"""
DEPRECATED: Les connecteurs ont été déplacés vers shared/integrations/

Ce module existe pour la rétrocompatibilité.
Utilisez plutôt: from shared.integrations import ImapConnector, GmailConnector
"""
import warnings

# Redirection vers le nouveau module
from shared.integrations import BaseEmailConnector, ImapConnector, GmailConnector

warnings.warn(
    "worker.connectors is deprecated. Use 'from shared.integrations import ...' instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = ["BaseEmailConnector", "ImapConnector", "GmailConnector"]
