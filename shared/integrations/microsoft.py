"""
Connecteur Microsoft (Outlook/Office 365) utilisant Microsoft Graph API avec OAuth2.

Supporte:
- Outlook.com
- Office 365
- Exchange Online
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import base64

from msal import ConfidentialClientApplication, PublicClientApplication
import requests

from shared.integrations.base import BaseEmailConnector

logger = logging.getLogger(__name__)


class MicrosoftConnector(BaseEmailConnector):
    """
    Connecteur pour Microsoft Graph API avec OAuth2.

    Credentials format:
    {
        "token": str,                    # Access token
        "refresh_token": str,            # Refresh token
        "token_uri": str,                # Token endpoint
        "client_id": str,                # Azure AD application client ID
        "client_secret": str (optional), # Client secret (for confidential apps)
        "tenant_id": str,                # Tenant ID (default: 'common')
        "scopes": List[str],             # Authorized scopes
        "expiry": str (ISO format)       # Token expiry datetime
    }
    """

    SCOPES = [
        'https://graph.microsoft.com/Mail.Read',
        'https://graph.microsoft.com/Mail.ReadWrite'
    ]

    GRAPH_API_ENDPOINT = 'https://graph.microsoft.com/v1.0'

    def __init__(self, email_address: str, credentials: Dict[str, Any]):
        """
        Initialiser le connecteur Microsoft.

        Args:
            email_address: Adresse email Outlook/Office 365
            credentials: Dict avec token OAuth2 et refresh token
        """
        super().__init__(email_address, credentials)

        self.client_id = credentials.get('client_id')
        self.client_secret = credentials.get('client_secret')
        self.tenant_id = credentials.get('tenant_id', 'common')
        self.token = credentials.get('token')
        self.refresh_token = credentials.get('refresh_token')
        self.expiry = credentials.get('expiry')
        self.scopes = credentials.get('scopes', self.SCOPES)

        # Parse expiry if string
        if isinstance(self.expiry, str):
            try:
                self.expiry = datetime.fromisoformat(self.expiry)
            except:
                self.expiry = None

        self._session: Optional[requests.Session] = None

    def connect(self) -> None:
        """
        Établir la connexion à Microsoft Graph API.

        Raises:
            ConnectionError: Si la connexion échoue
        """
        try:
            self.logger.info(f"Connecting to Microsoft Graph API for {self.email_address}")

            # Refresh token if expired
            if self._is_token_expired():
                self._refresh_access_token()

            # Create session
            self._session = requests.Session()
            self._session.headers.update({
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            })

            # Test connection
            response = self._session.get(f'{self.GRAPH_API_ENDPOINT}/me')
            response.raise_for_status()

            self.logger.info("Microsoft Graph API connection successful")

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Microsoft Graph API error: {e}", exc_info=True)
            raise ConnectionError(f"Failed to connect to Microsoft Graph API: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}", exc_info=True)
            raise ConnectionError(f"Microsoft connection failed: {e}")

    def disconnect(self) -> None:
        """Fermer la connexion (cleanup)."""
        if self._session:
            self._session.close()
            self._session = None
        self.logger.debug("Microsoft connection closed")

    def fetch_emails(
        self,
        folder: str = "INBOX",
        limit: int = 50,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Récupérer les emails depuis Microsoft Graph API.

        Args:
            folder: Nom du dossier (INBOX, Sent, etc.)
            limit: Nombre max d'emails
            since: Date à partir de laquelle récupérer

        Returns:
            Liste de dicts avec les emails parsés
        """
        if not self._session:
            self.connect()

        try:
            # Map folder names
            folder_map = {
                'INBOX': 'inbox',
                'SENT': 'sentitems',
                'DRAFTS': 'drafts',
                'TRASH': 'deleteditems',
                'JUNK': 'junkemail'
            }
            graph_folder = folder_map.get(folder.upper(), folder.lower())

            # Build query
            endpoint = f'{self.GRAPH_API_ENDPOINT}/me/mailFolders/{graph_folder}/messages'

            # Query parameters
            params = {
                '$top': min(limit, 999),  # Max 999 per request
                '$orderby': 'receivedDateTime desc',
                '$select': 'id,subject,from,toRecipients,receivedDateTime,bodyPreview,hasAttachments,internetMessageId'
            }

            # Filter by date if provided
            if since:
                since_str = since.strftime('%Y-%m-%dT%H:%M:%SZ')
                params['$filter'] = f'receivedDateTime ge {since_str}'

            self.logger.info(f"Fetching emails from {graph_folder} with limit {limit}")

            # Make request
            response = self._session.get(endpoint, params=params)
            response.raise_for_status()

            data = response.json()
            messages = data.get('value', [])

            self.logger.info(f"Found {len(messages)} messages")

            # Parse each message
            emails = []
            for msg in messages:
                try:
                    email_data = self._parse_microsoft_message(msg)
                    if email_data:
                        emails.append(email_data)
                except Exception as e:
                    self.logger.error(f"Error parsing message {msg.get('id')}: {e}")

            self.logger.info(f"Successfully parsed {len(emails)} emails")
            return emails

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching emails: {e}", exc_info=True)
            raise ConnectionError(f"Failed to fetch emails: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}", exc_info=True)
            raise

    def move_email(self, message_id: str, destination_folder: str) -> bool:
        """
        Déplacer un email vers un autre dossier.

        Args:
            message_id: ID du message Microsoft Graph
            destination_folder: Nom du dossier de destination

        Returns:
            True si succès
        """
        if not self._session:
            self.connect()

        try:
            # Get destination folder ID
            folder_id = self._get_folder_id(destination_folder)
            if not folder_id:
                self.logger.error(f"Folder not found: {destination_folder}")
                return False

            # Move message
            endpoint = f'{self.GRAPH_API_ENDPOINT}/me/messages/{message_id}/move'
            payload = {'destinationId': folder_id}

            response = self._session.post(endpoint, json=payload)
            response.raise_for_status()

            self.logger.info(f"Moved message {message_id} to {destination_folder}")
            return True

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error moving message: {e}")
            return False

    def delete_email(self, message_id: str, permanent: bool = False) -> bool:
        """
        Supprimer un email.

        Args:
            message_id: ID du message Microsoft Graph
            permanent: Si True, suppression définitive. Sinon, déplace vers Deleted Items.

        Returns:
            True si succès
        """
        if not self._session:
            self.connect()

        try:
            endpoint = f'{self.GRAPH_API_ENDPOINT}/me/messages/{message_id}'

            if permanent:
                # Hard delete
                response = self._session.delete(endpoint)
            else:
                # Soft delete (move to trash)
                trash_id = self._get_folder_id('deleteditems')
                if trash_id:
                    move_endpoint = f'{endpoint}/move'
                    response = self._session.post(move_endpoint, json={'destinationId': trash_id})
                else:
                    # Fallback to hard delete if trash not found
                    response = self._session.delete(endpoint)

            response.raise_for_status()

            action = "permanently deleted" if permanent else "moved to trash"
            self.logger.info(f"Message {message_id} {action}")
            return True

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error deleting message: {e}")
            return False

    def _parse_microsoft_message(self, message: Dict) -> Optional[Dict[str, Any]]:
        """
        Parser un message Microsoft Graph en format standard.

        Args:
            message: Message Microsoft Graph API format

        Returns:
            Dict formaté selon BaseEmailConnector
        """
        try:
            # Extract basic info
            message_id = message.get('internetMessageId', message.get('id', ''))
            subject = message.get('subject', 'No Subject')

            # Extract sender
            from_field = message.get('from', {})
            sender_obj = from_field.get('emailAddress', {})
            sender = f"{sender_obj.get('name', '')} <{sender_obj.get('address', 'unknown')}>"

            # Parse date
            date_str = message.get('receivedDateTime')
            if date_str:
                try:
                    # Microsoft returns ISO 8601 format
                    date_received = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                except:
                    date_received = datetime.utcnow()
            else:
                date_received = datetime.utcnow()

            # Body preview
            body_preview = message.get('bodyPreview', '')

            # Attachments
            has_attachments = message.get('hasAttachments', False)

            return {
                "message_id": message_id,
                "microsoft_id": message.get('id'),  # Keep Graph ID for operations
                "subject": subject,
                "sender": sender,
                "date_received": date_received,
                "body": body_preview[:2000] if body_preview else "",
                "has_attachments": has_attachments,
                "attachment_count": 0,  # Would need separate API call to get exact count
                "attachments": []
            }

        except Exception as e:
            self.logger.error(f"Error parsing message: {e}", exc_info=True)
            return None

    def _is_token_expired(self) -> bool:
        """
        Vérifier si le token est expiré.

        Returns:
            True si expiré ou expiration dans moins de 5 minutes
        """
        if not self.expiry:
            return True

        # Consider expired if less than 5 minutes remaining
        buffer = timedelta(minutes=5)
        return datetime.utcnow() >= (self.expiry - buffer)

    def _refresh_access_token(self) -> None:
        """
        Refresh le token d'accès avec le refresh token.

        Raises:
            ConnectionError: Si le refresh échoue
        """
        if not self.refresh_token:
            raise ConnectionError("No refresh token available")

        try:
            self.logger.info("Refreshing access token...")

            authority = f"https://login.microsoftonline.com/{self.tenant_id}"

            if self.client_secret:
                # Confidential client (with secret)
                app = ConfidentialClientApplication(
                    self.client_id,
                    authority=authority,
                    client_credential=self.client_secret
                )
            else:
                # Public client (no secret)
                app = PublicClientApplication(
                    self.client_id,
                    authority=authority
                )

            # Acquire token by refresh token
            result = app.acquire_token_by_refresh_token(
                self.refresh_token,
                scopes=self.scopes
            )

            if 'access_token' in result:
                self.token = result['access_token']
                self.refresh_token = result.get('refresh_token', self.refresh_token)

                # Calculate expiry
                expires_in = result.get('expires_in', 3600)
                self.expiry = datetime.utcnow() + timedelta(seconds=expires_in)

                self.logger.info("Token refreshed successfully")
            else:
                error = result.get('error_description', 'Unknown error')
                raise ConnectionError(f"Token refresh failed: {error}")

        except Exception as e:
            self.logger.error(f"Error refreshing token: {e}", exc_info=True)
            raise ConnectionError(f"Failed to refresh token: {e}")

    def _get_folder_id(self, folder_name: str) -> Optional[str]:
        """
        Obtenir l'ID d'un dossier par son nom.

        Args:
            folder_name: Nom du dossier (case-insensitive)

        Returns:
            Folder ID ou None si not found
        """
        try:
            # Well-known folder names
            well_known = {
                'inbox': 'inbox',
                'deleteditems': 'deleteditems',
                'drafts': 'drafts',
                'sentitems': 'sentitems',
                'junkemail': 'junkemail'
            }

            folder_lower = folder_name.lower()
            if folder_lower in well_known:
                return well_known[folder_lower]

            # Search in mailFolders
            endpoint = f'{self.GRAPH_API_ENDPOINT}/me/mailFolders'
            params = {'$filter': f"displayName eq '{folder_name}'"}

            response = self._session.get(endpoint, params=params)
            response.raise_for_status()

            data = response.json()
            folders = data.get('value', [])

            if folders:
                return folders[0]['id']

            return None

        except Exception as e:
            self.logger.error(f"Error getting folder ID: {e}")
            return None

    def get_refreshed_credentials(self) -> Optional[Dict[str, Any]]:
        """
        Récupérer les credentials actuels (pour mise à jour en DB si refresh).

        Returns:
            Dict avec credentials ou None
        """
        if not self.token:
            return None

        return {
            'token': self.token,
            'refresh_token': self.refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'tenant_id': self.tenant_id,
            'scopes': self.scopes,
            'expiry': self.expiry.isoformat() if self.expiry else None
        }
