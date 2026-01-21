"""
Base connector abstraction pour tous les email providers
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BaseEmailConnector(ABC):
    """
    Classe abstraite pour les connecteurs email.

    Tous les connecteurs (IMAP, Gmail, Outlook) doivent implémenter cette interface.
    """

    def __init__(self, email_address: str, credentials: Dict[str, Any]):
        """
        Initialiser le connecteur.

        Args:
            email_address: Adresse email du compte
            credentials: Dictionnaire de credentials (format varie par provider)
        """
        self.email_address = email_address
        self.credentials = credentials
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def connect(self) -> None:
        """
        Établir la connexion au service email.

        Raises:
            ConnectionError: Si la connexion échoue
            AuthenticationError: Si l'authentification échoue
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Fermer la connexion proprement."""
        pass

    @abstractmethod
    def fetch_emails(
        self,
        folder: str = "INBOX",
        limit: int = 50,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Récupérer les emails depuis le serveur.

        Args:
            folder: Dossier à scanner (INBOX par défaut)
            limit: Nombre max d'emails à récupérer
            since: Date à partir de laquelle récupérer (None = tous)

        Returns:
            Liste de dictionnaires avec structure:
            {
                "message_id": str,
                "subject": str,
                "sender": str,
                "date_received": datetime,
                "body": str,
                "has_attachments": bool,
                "attachment_count": int,
                "attachments": List[Dict]
            }
        """
        pass

    @abstractmethod
    def move_email(self, message_id: str, destination_folder: str) -> bool:
        """
        Déplacer un email vers un dossier.

        Args:
            message_id: ID unique du message
            destination_folder: Nom du dossier de destination

        Returns:
            True si succès, False sinon
        """
        pass

    @abstractmethod
    def delete_email(self, message_id: str, permanent: bool = False) -> bool:
        """
        Supprimer un email.

        Args:
            message_id: ID unique du message
            permanent: Si True, suppression permanente. Sinon, déplace vers Trash.

        Returns:
            True si succès, False sinon
        """
        pass

    def test_connection(self) -> Dict[str, Any]:
        """
        Tester la connexion au service.

        Returns:
            Dict avec status et détails:
            {"success": bool, "message": str, "details": dict}
        """
        try:
            self.connect()
            self.disconnect()
            return {
                "success": True,
                "message": "Connection successful",
                "details": {"email": self.email_address}
            }
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}",
                "details": {"error_type": type(e).__name__}
            }
