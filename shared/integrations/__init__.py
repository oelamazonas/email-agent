"""
Email integrations/connectors pour différents providers.

Ce module contient les connecteurs pour les différents services email:
- BaseEmailConnector: Interface abstraite pour tous les connecteurs
- ImapConnector: IMAP générique (Gmail via app password, Outlook, etc.)
- GmailConnector: Gmail API avec OAuth2 (accès complet, recommandé)
- MicrosoftConnector: Microsoft Graph API avec OAuth2 (Outlook/Office 365)

Usage:
    from shared.integrations import ImapConnector, GmailConnector, MicrosoftConnector

    # IMAP
    imap_connector = ImapConnector(email, credentials)

    # Gmail
    gmail_connector = GmailConnector(email, credentials)

    # Microsoft
    microsoft_connector = MicrosoftConnector(email, credentials)
"""
from .base import BaseEmailConnector
from .imap import ImapConnector
from .gmail import GmailConnector
from .microsoft import MicrosoftConnector

__all__ = ["BaseEmailConnector", "ImapConnector", "GmailConnector", "MicrosoftConnector"]
