"""
Connecteur IMAP pour récupérer les emails.

Supporte IMAP générique, Gmail (via app password), Outlook, etc.
"""
"""
Connecteur IMAP pour récupérer les emails.

Supporte IMAP générique, Gmail (via app password), Outlook, etc.
"""
from imapclient import IMAPClient
from imapclient.exceptions import LoginError, IMAPClientError
from email import message_from_bytes
from email.header import decode_header, make_header
from email.utils import parsedate_to_datetime
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any

from shared.integrations.base import BaseEmailConnector

logger = logging.getLogger(__name__)


class ImapConnector(BaseEmailConnector):
    """
    Connecteur IMAP générique.

    Credentials format:
    {
        "type": "imap",
        "imap_server": str,    # Hostname (e.g., "imap.gmail.com")
        "imap_port": int,      # Port (default: 993)
        "username": str,       # Username (often same as email)
        "password": str,       # Password or app password
        "use_ssl": bool        # Use SSL/TLS (default: True)
    }
    """

    def __init__(self, email_address: str, credentials: Dict[str, Any]):
        """
        Initialiser le connecteur IMAP.

        Args:
            email_address: Adresse email du compte
            credentials: Dict avec config IMAP et mot de passe
        """
        super().__init__(email_address, credentials)

        # Extract IMAP configuration
        self.host = credentials.get('imap_server', 'imap.gmail.com')
        self.port = credentials.get('imap_port', 993)
        self.username = credentials.get('username', email_address)
        self.password = credentials.get('password', '')
        self.use_ssl = credentials.get('use_ssl', True)

        self.client: Optional[IMAPClient] = None

    def connect(self) -> None:
        """
        Établir la connexion IMAP.

        Raises:
            LoginError: Si l'authentification échoue
            ConnectionError: Si la connexion au serveur échoue
        """
        try:
            self.logger.info(f"Connecting to IMAP server {self.host}:{self.port} for {self.email_address}")

            self.client = IMAPClient(
                self.host,
                port=self.port,
                ssl=self.use_ssl,
                use_uid=True
            )

            self.client.login(self.username, self.password)
            self.logger.info("IMAP login successful")

        except LoginError as e:
            self.logger.error(f"Login failed for {self.email_address}: {e}")
            raise ConnectionError(f"IMAP authentication failed: {e}")
        except Exception as e:
            self.logger.error(f"IMAP connection failed: {e}", exc_info=True)
            raise ConnectionError(f"Failed to connect to IMAP server: {e}")

    def disconnect(self) -> None:
        """Fermer la connexion IMAP proprement."""
        if self.client:
            try:
                self.client.logout()
                self.logger.debug("IMAP connection closed")
            except Exception as e:
                self.logger.warning(f"Error during logout: {e}")
            finally:
                self.client = None

    def fetch_emails(
        self,
        folder: str = "INBOX",
        limit: int = 50,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Récupérer les emails depuis un dossier IMAP.

        Args:
            folder: Nom du dossier IMAP (INBOX, SENT, etc.)
            limit: Nombre max d'emails à récupérer
            since: Date à partir de laquelle récupérer

        Returns:
            Liste de dicts avec les emails parsés

        Raises:
            ConnectionError: Si la connexion échoue
        """
        if not self.client:
            self.connect()

        try:
            # Sélectionner le dossier
            select_info = self.client.select_folder(folder)
            self.logger.debug(f"Selected folder {folder}: {select_info}")

            # Construire les critères de recherche
            criteria = ['NOT', 'DELETED']
            if since:
                date_str = since.date().strftime("%d-%b-%Y")
                criteria.append('SINCE')
                criteria.append(date_str)

            # Rechercher les messages
            messages = self.client.search(criteria)

            if not messages:
                self.logger.info(f"No messages found in {folder}")
                return []

            # Limiter et trier (plus récents en premier)
            messages = sorted(messages, reverse=True)[:limit]

            self.logger.info(f"Fetching {len(messages)} emails from {folder}")

            # Fetch message data
            response = self.client.fetch(messages, ['BODY.PEEK[]', 'FLAGS', 'INTERNALDATE'])

            # Parse each message
            results = []
            for msg_id, data in response.items():
                try:
                    email_data = self._parse_email(msg_id, data)
                    if email_data:
                        results.append(email_data)
                except Exception as e:
                    self.logger.error(f"Error parsing message {msg_id}: {e}")

            self.logger.info(f"Successfully parsed {len(results)} emails")
            return results

        except IMAPClientError as e:
            self.logger.error(f"IMAP error fetching emails: {e}", exc_info=True)
            raise ConnectionError(f"Failed to fetch emails: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error fetching emails: {e}", exc_info=True)
            raise

    def move_email(self, message_id: str, destination_folder: str) -> bool:
        """
        Déplacer un email vers un autre dossier.

        Args:
            message_id: UID du message IMAP (converti en int)
            destination_folder: Nom du dossier de destination

        Returns:
            True si succès, False sinon
        """
        if not self.client:
            self.connect()

        try:
            # Convert message_id to UID (int)
            uid = int(message_id) if isinstance(message_id, str) else message_id

            # IMAP COPY then DELETE pattern
            self.client.copy([uid], destination_folder)
            self.client.delete_messages([uid])
            self.client.expunge()

            self.logger.info(f"Moved message {uid} to {destination_folder}")
            return True

        except ValueError as e:
            self.logger.error(f"Invalid message ID format: {message_id}")
            return False
        except IMAPClientError as e:
            self.logger.error(f"IMAP error moving message {message_id}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error moving message {message_id}: {e}", exc_info=True)
            return False

    def delete_email(self, message_id: str, permanent: bool = False) -> bool:
        """
        Supprimer un email.

        Args:
            message_id: UID du message IMAP
            permanent: Si True, suppression définitive (expunge).
                      Si False, marque comme \\Deleted seulement.

        Returns:
            True si succès, False sinon
        """
        if not self.client:
            self.connect()

        try:
            # Convert message_id to UID
            uid = int(message_id) if isinstance(message_id, str) else message_id

            # Mark as deleted
            self.client.delete_messages([uid])

            # Expunge si suppression permanente
            if permanent:
                self.client.expunge()
                self.logger.info(f"Permanently deleted message {uid}")
            else:
                self.logger.info(f"Marked message {uid} as deleted")

            return True

        except ValueError as e:
            self.logger.error(f"Invalid message ID format: {message_id}")
            return False
        except IMAPClientError as e:
            self.logger.error(f"IMAP error deleting message {message_id}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error deleting message {message_id}: {e}", exc_info=True)
            return False

    def _parse_email(self, msg_id: int, data: Dict) -> Optional[Dict[str, Any]]:
        """
        Parser un email IMAP en format standard.

        Args:
            msg_id: UID du message
            data: Données brutes IMAP

        Returns:
            Dict formaté selon BaseEmailConnector ou None si erreur
        """
        try:
            raw_email = data[b'BODY[]']
            msg = message_from_bytes(raw_email)

            # Extract headers
            subject = str(make_header(decode_header(msg.get('Subject', 'No Subject'))))
            sender = str(make_header(decode_header(msg.get('From', 'Unknown'))))
            message_id = msg.get('Message-ID', '').strip() or f"imap-{msg_id}"

            # Parse date
            date_str = msg.get('Date')
            if date_str:
                try:
                    date_received = parsedate_to_datetime(date_str)
                except Exception:
                    date_received = datetime.utcnow()
            else:
                # Fallback to INTERNALDATE
                internal_date = data.get(b'INTERNALDATE')
                date_received = internal_date if internal_date else datetime.utcnow()

            # Extract body and attachments
            body, attachments = self._extract_body_and_attachments(msg)

            return {
                "message_id": message_id,
                "imap_uid": msg_id,  # Keep IMAP UID for operations
                "subject": subject,
                "sender": sender,
                "date_received": date_received,
                "body": body[:2000] if body else "",
                "has_attachments": len(attachments) > 0,
                "attachment_count": len(attachments),
                "attachments": attachments
            }

        except Exception as e:
            self.logger.error(f"Error parsing email {msg_id}: {e}", exc_info=True)
            return None

    def _extract_body_and_attachments(self, msg) -> tuple[str, List[Dict[str, Any]]]:
        """
        Extraire le corps et les pièces jointes d'un message.

        Args:
            msg: Message email parsé

        Returns:
            Tuple (body: str, attachments: List[Dict])
        """
        body = ""
        html_body = None
        attachments = []

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                # Check for attachments
                if "attachment" in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        # Decode filename if needed
                        try:
                            filename = str(make_header(decode_header(filename)))
                        except:
                            pass

                        attachments.append({
                            "filename": filename,
                            "content_type": content_type,
                            "size": len(part.get_payload(decode=True) or b"")
                        })
                    continue

                # Extract body content
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        decoded = payload.decode(charset, errors='replace')

                        if content_type == "text/plain":
                            body += decoded
                        elif content_type == "text/html" and not body:
                            # Fallback to HTML if no plain text
                            html_body = decoded
                except Exception as e:
                    self.logger.warning(f"Error decoding part: {e}")
        else:
            # Single part message
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset() or 'utf-8'
                    body = payload.decode(charset, errors='replace')
            except Exception as e:
                self.logger.warning(f"Error decoding message body: {e}")
                body = str(msg.get_payload())

        # Use HTML as fallback if no plain text
        if not body and html_body:
            body = html_body

        return body, attachments


# Backward compatibility: support old constructor signature
class ImapConnectorLegacy(ImapConnector):
    """
    Legacy IMAP connector pour compatibilité avec l'ancien code.

    DEPRECATED: Utiliser ImapConnector avec credentials dict à la place.
    """

    def __init__(self, host: str, email_address: str, password: str, ssl: bool = True, port: int = 993):
        """
        Ancienne signature du constructeur.

        Args:
            host: Serveur IMAP
            email_address: Adresse email
            password: Mot de passe
            ssl: Utiliser SSL
            port: Port IMAP
        """
        credentials = {
            "type": "imap",
            "imap_server": host,
            "imap_port": port,
            "username": email_address,
            "password": password,
            "use_ssl": ssl
        }
        super().__init__(email_address, credentials)
        logger.warning("ImapConnectorLegacy is deprecated. Use ImapConnector with credentials dict.")
