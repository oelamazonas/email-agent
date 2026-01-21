"""
Email actions module.

Handles execution of actions on emails based on classification results.
"""
from worker.actions.email_actions import (
    apply_classification_action,
    bulk_move_emails,
    apply_label,
    bulk_classify_pending_emails,
    EmailActionError,
    ConnectorNotFoundError
)

__all__ = [
    'apply_classification_action',
    'bulk_move_emails',
    'apply_label',
    'bulk_classify_pending_emails',
    'EmailActionError',
    'ConnectorNotFoundError'
]
