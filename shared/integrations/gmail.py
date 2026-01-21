"""
Connecteur Gmail utilisant Gmail API avec OAuth2
"""
import base64
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from email.utils import parsedate_to_datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from shared.integrations.base import BaseEmailConnector

logger = logging.getLogger(__name__)


class GmailConnector(BaseEmailConnector):
    """
    Connecteur pour Gmail API avec OAuth2.

    Credentials format:
    {
        "token": str,              # Access token
        "refresh_token": str,      # Refresh token
        "token_uri": str,          # OAuth2 token endpoint
        "client_id": str,          # Google OAuth2 client ID
        "client_secret": str,      # Google OAuth2 client secret
        "scopes": List[str],       # Scopes autorisés
        "expiry": str (ISO format) # Token expiry
    }
    """

    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.modify'
    ]

    def __init__(self, email_address: str, credentials: Dict[str, Any]):
        """
        Initialiser le connecteur Gmail.

        Args:
            email_address: Adresse Gmail
            credentials: Dict avec token OAuth2 et refresh token
        """
        super().__init__(email_address, credentials)
        self.service = None
        self._creds: Optional[Credentials] = None

    def _build_credentials(self) -> Credentials:
        """
        Construire l'objet Credentials depuis le dict.

        Returns:
            Credentials Google OAuth2
        """
        creds_data = {
            'token': self.credentials.get('token'),
            'refresh_token': self.credentials.get('refresh_token'),
            'token_uri': self.credentials.get('token_uri', 'https://oauth2.googleapis.com/token'),
            'client_id': self.credentials.get('client_id'),
            'client_secret': self.credentials.get('client_secret'),
            'scopes': self.credentials.get('scopes', self.SCOPES)
        }

        # Parse expiry si présent
        if 'expiry' in self.credentials and self.credentials['expiry']:
            if isinstance(self.credentials['expiry'], str):
                creds_data['expiry'] = datetime.fromisoformat(self.credentials['expiry'])
            else:
                creds_data['expiry'] = self.credentials['expiry']

        return Credentials(**creds_data)

    def _refresh_token_if_needed(self) -> Dict[str, Any]:
        """
        Refresh le token si expiré.

        Returns:
            Dict avec les nouveaux credentials si refresh, sinon None
        """
        if not self._creds:
            return None

        if self._creds.expired and self._creds.refresh_token:
            self.logger.info("Access token expired, refreshing...")
            try:
                self._creds.refresh(Request())
                self.logger.info("Token refreshed successfully")

                # Retourner les nouvelles credentials pour mise à jour en DB
                return {
                    'token': self._creds.token,
                    'refresh_token': self._creds.refresh_token,
                    'expiry': self._creds.expiry.isoformat() if self._creds.expiry else None,
                    'token_uri': self._creds.token_uri,
                    'client_id': self._creds.client_id,
                    'client_secret': self._creds.client_secret,
                    'scopes': self._creds.scopes
                }
            except Exception as e:
                self.logger.error(f"Token refresh failed: {e}", exc_info=True)
                raise ConnectionError(f"Failed to refresh OAuth2 token: {e}")

        return None

    def connect(self) -> None:
        """
        Établir la connexion à Gmail API.

        Raises:
            ConnectionError: Si connexion échoue
        """
        try:
            self.logger.info(f"Connecting to Gmail API for {self.email_address}")

            # Build credentials
            self._creds = self._build_credentials()

            # Refresh si nécessaire
            self._refresh_token_if_needed()

            # Build service
            self.service = build('gmail', 'v1', credentials=self._creds)

            # Test connection
            self.service.users().getProfile(userId='me').execute()

            self.logger.info("Gmail API connection successful")

        except HttpError as e:
            self.logger.error(f"Gmail API HTTP error: {e}", exc_info=True)
            raise ConnectionError(f"Gmail API error: {e}")
        except Exception as e:
            self.logger.error(f"Failed to connect to Gmail API: {e}", exc_info=True)
            raise ConnectionError(f"Gmail connection failed: {e}")

    def disconnect(self) -> None:
        """Fermer la connexion (cleanup)."""
        self.service = None
        self._creds = None
        self.logger.debug("Gmail connection closed")

    def fetch_emails(
        self,
        folder: str = "INBOX",
        limit: int = 50,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Récupérer les emails depuis Gmail.

        Args:
            folder: Label Gmail (INBOX, SENT, etc.)
            limit: Nombre max d'emails
            since: Date à partir de laquelle récupérer

        Returns:
            Liste de dicts avec les emails parsés
        """
        if not self.service:
            self.connect()

        try:
            # Construire la query
            query_parts = [f"label:{folder}"]
            if since:
                date_str = since.strftime('%Y/%m/%d')
                query_parts.append(f"after:{date_str}")

            query = ' '.join(query_parts)

            self.logger.info(f"Fetching emails with query: {query}")

            # List messages
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=limit
            ).execute()

            messages = results.get('messages', [])

            if not messages:
                self.logger.info("No messages found")
                return []

            self.logger.info(f"Found {len(messages)} messages, fetching details...")

            # Fetch details en batch
            emails = []
            for msg in messages:
                try:
                    email_data = self._fetch_message_details(msg['id'])
                    if email_data:
                        emails.append(email_data)
                except Exception as e:
                    self.logger.error(f"Error parsing message {msg['id']}: {e}")

            self.logger.info(f"Successfully parsed {len(emails)} emails")
            return emails

        except HttpError as e:
            self.logger.error(f"Gmail API error fetching emails: {e}", exc_info=True)
            raise
        except Exception as e:
            self.logger.error(f"Error fetching emails: {e}", exc_info=True)
            raise

    def _fetch_message_details(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupérer les détails d'un message Gmail.

        Args:
            message_id: ID du message Gmail

        Returns:
            Dict avec les données parsées ou None si erreur
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()

            return self._parse_gmail_message(message)

        except HttpError as e:
            self.logger.error(f"Error fetching message {message_id}: {e}")
            return None

    def _parse_gmail_message(self, message: Dict) -> Dict[str, Any]:
        """
        Parser un message Gmail en format standard.

        Args:
            message: Message Gmail API format

        Returns:
            Dict formaté selon BaseEmailConnector
        """
        headers = {h['name']: h['value'] for h in message['payload']['headers']}

        # Extract basic info
        subject = headers.get('Subject', 'No Subject')
        sender = headers.get('From', 'Unknown')
        message_id = headers.get('Message-ID', message['id'])

        # Parse date
        date_str = headers.get('Date')
        if date_str:
            try:
                date_received = parsedate_to_datetime(date_str)
            except Exception:
                date_received = datetime.utcnow()
        else:
            # Fallback to internalDate
            timestamp_ms = int(message.get('internalDate', 0))
            date_received = datetime.fromtimestamp(timestamp_ms / 1000)

        # Extract body
        body = self._extract_body(message['payload'])

        # Check attachments
        attachments = self._extract_attachments_info(message['payload'])

        return {
            "message_id": message_id,
            "gmail_id": message['id'],  # Garder l'ID Gmail pour les opérations
            "subject": subject,
            "sender": sender,
            "date_received": date_received,
            "body": body[:2000] if body else "",
            "has_attachments": len(attachments) > 0,
            "attachment_count": len(attachments),
            "attachments": attachments
        }

    def _extract_body(self, payload: Dict) -> str:
        """
        Extraire le corps du message.

        Args:
            payload: Payload du message Gmail

        Returns:
            Body text
        """
        body = ""

        # Si c'est une partie simple
        if 'body' in payload and 'data' in payload['body']:
            body_data = payload['body']['data']
            body = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='replace')
            return body

        # Si c'est multipart, parcourir les parties
        if 'parts' in payload:
            for part in payload['parts']:
                mime_type = part.get('mimeType', '')

                # Récursif pour nested parts
                if 'parts' in part:
                    body += self._extract_body(part)
                elif mime_type == 'text/plain':
                    if 'data' in part['body']:
                        part_data = part['body']['data']
                        decoded = base64.urlsafe_b64decode(part_data).decode('utf-8', errors='replace')
                        body += decoded
                elif mime_type == 'text/html' and not body:
                    # Fallback to HTML si pas de text/plain
                    if 'data' in part['body']:
                        part_data = part['body']['data']
                        body = base64.urlsafe_b64decode(part_data).decode('utf-8', errors='replace')

        return body

    def _extract_attachments_info(self, payload: Dict) -> List[Dict[str, Any]]:
        """
        Extraire les infos des pièces jointes.

        Args:
            payload: Payload du message

        Returns:
            Liste de dicts avec infos attachments
        """
        attachments = []

        if 'parts' in payload:
            for part in payload['parts']:
                # Récursif
                if 'parts' in part:
                    attachments.extend(self._extract_attachments_info(part))
                elif part.get('filename'):
                    attachments.append({
                        'filename': part['filename'],
                        'content_type': part.get('mimeType', 'application/octet-stream'),
                        'size': part['body'].get('size', 0)
                    })

        return attachments

    def move_email(self, message_id: str, destination_folder: str) -> bool:
        """
        Déplacer un email (ajouter/retirer labels).

        Args:
            message_id: Gmail message ID
            destination_folder: Label de destination

        Returns:
            True si succès
        """
        if not self.service:
            self.connect()

        try:
            # Gmail utilise des labels, pas des folders
            # "Déplacer" = retirer INBOX et ajouter le label destination

            body = {
                'addLabelIds': [destination_folder],
                'removeLabelIds': ['INBOX']
            }

            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body=body
            ).execute()

            self.logger.info(f"Moved message {message_id} to {destination_folder}")
            return True

        except HttpError as e:
            self.logger.error(f"Error moving message {message_id}: {e}")
            return False

    def delete_email(self, message_id: str, permanent: bool = False) -> bool:
        """
        Supprimer un email.

        Args:
            message_id: Gmail message ID
            permanent: Si True, suppression définitive. Sinon, déplace vers TRASH.

        Returns:
            True si succès
        """
        if not self.service:
            self.connect()

        try:
            if permanent:
                self.service.users().messages().delete(
                    userId='me',
                    id=message_id
                ).execute()
                self.logger.info(f"Permanently deleted message {message_id}")
            else:
                self.service.users().messages().trash(
                    userId='me',
                    id=message_id
                ).execute()
                self.logger.info(f"Moved message {message_id} to trash")

            return True

        except HttpError as e:
            self.logger.error(f"Error deleting message {message_id}: {e}")
            return False

    def get_refreshed_credentials(self) -> Optional[Dict[str, Any]]:
        """
        Récupérer les credentials actuels (pour mise à jour en DB si refresh).

        Returns:
            Dict avec credentials ou None
        """
        if not self._creds:
            return None

        return {
            'token': self._creds.token,
            'refresh_token': self._creds.refresh_token,
            'expiry': self._creds.expiry.isoformat() if self._creds.expiry else None,
            'token_uri': self._creds.token_uri,
            'client_id': self._creds.client_id,
            'client_secret': self._creds.client_secret,
            'scopes': self._creds.scopes
        }
