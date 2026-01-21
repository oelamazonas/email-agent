"""
Email actions module for Email Agent AI.

This module handles executing actions on emails based on classification results,
including moving to folders, deleting, applying labels, and bulk operations.
"""
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db_context
from api.models import (
    Email, EmailAccount, EmailCategory, ProcessingStatus,
    ProcessingLog, AccountType
)
from worker.rules import rules_parser
from shared.integrations import ImapConnector, GmailConnector, MicrosoftConnector
from shared.security import decrypt_credentials

logger = logging.getLogger(__name__)


class EmailActionError(Exception):
    """Base exception for email action errors."""
    pass


class ConnectorNotFoundError(EmailActionError):
    """Connector could not be created."""
    pass


async def _get_connector_for_account(account: EmailAccount):
    """
    Create appropriate connector for an email account.

    Args:
        account: EmailAccount model instance

    Returns:
        Connector instance (ImapConnector, GmailConnector, or MicrosoftConnector)

    Raises:
        ConnectorNotFoundError: If connector cannot be created
    """
    try:
        credentials = decrypt_credentials(account.encrypted_credentials)

        if account.account_type == AccountType.IMAP:
            return ImapConnector(
                email_address=account.email_address,
                credentials=credentials
            )
        elif account.account_type == AccountType.GMAIL:
            return GmailConnector(
                email_address=account.email_address,
                credentials=credentials
            )
        elif account.account_type == AccountType.OUTLOOK:
            return MicrosoftConnector(
                email_address=account.email_address,
                credentials=credentials
            )
        else:
            raise ConnectorNotFoundError(f"Unsupported account type: {account.account_type}")

    except Exception as e:
        logger.error(f"Error creating connector for account {account.id}: {e}", exc_info=True)
        raise ConnectorNotFoundError(f"Failed to create connector: {e}")


async def _log_action(
    db: AsyncSession,
    email_id: int,
    action: str,
    success: bool,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an action execution to database.

    Args:
        db: Database session
        email_id: Email ID
        action: Action name (e.g., "move_email", "delete_email")
        success: Whether action succeeded
        details: Additional details about the action
    """
    try:
        log = ProcessingLog(
            email_id=email_id,
            level="INFO" if success else "ERROR",
            message=f"Action '{action}' {'succeeded' if success else 'failed'}",
            details=details or {},
            component="email_actions"
        )
        db.add(log)
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to log action: {e}", exc_info=True)


async def apply_classification_action(
    email_id: int,
    category: EmailCategory,
    confidence: int,
    rule_matched: Optional[str] = None
) -> Dict[str, Any]:
    """
    Apply appropriate action based on email classification.

    This function:
    1. Checks if a rule was matched and applies its action
    2. Otherwise, applies default actions based on category
    3. Logs all actions taken
    4. Updates email status in database

    Args:
        email_id: Email ID to process
        category: Classification category
        confidence: Classification confidence (0-100)
        rule_matched: Optional name of matched rule

    Returns:
        Dict with action results: {
            'status': 'success'|'error',
            'actions_taken': List[str],
            'error': Optional[str]
        }
    """
    actions_taken = []
    start_time = datetime.utcnow()

    try:
        async with get_db_context() as db:
            # Get email and account
            email = await db.get(Email, email_id)
            if not email:
                return {
                    'status': 'error',
                    'error': f'Email {email_id} not found'
                }

            account = await db.get(EmailAccount, email.account_id)
            if not account:
                return {
                    'status': 'error',
                    'error': f'Account {email.account_id} not found'
                }

            # Build email data for rule matching
            email_data = {
                'subject': email.subject,
                'sender': email.sender,
                'body_preview': email.body_preview,
                'has_attachments': email.has_attachments,
                'attachment_names': []  # TODO: Load from attachments table if needed
            }

            # Find matching rule
            rule = rules_parser.find_matching_rule(email_data)

            # Determine actions based on rule or defaults
            target_folder = None
            should_delete = False

            if rule:
                logger.info(f"Email {email_id} matched rule: {rule.name}")
                target_folder = rule.folder
                should_delete = rule.auto_delete
                actions_taken.append(f"matched_rule:{rule.name}")
            else:
                # Default actions based on category
                target_folder = _get_default_folder_for_category(category)
                should_delete = (category == EmailCategory.SPAM)

            # Execute actions
            connector = None
            try:
                connector = await _get_connector_for_account(account)
                connector.connect()

                # Move to folder if specified
                if target_folder and not should_delete:
                    success = connector.move_email(email.message_id, target_folder)
                    if success:
                        email.archived_folder = target_folder
                        actions_taken.append(f"moved_to:{target_folder}")
                        await _log_action(db, email_id, "move_email", True, {
                            'folder': target_folder,
                            'category': category.value
                        })
                    else:
                        logger.warning(f"Failed to move email {email_id} to {target_folder}")
                        await _log_action(db, email_id, "move_email", False, {
                            'folder': target_folder
                        })

                # Delete if specified
                if should_delete:
                    success = connector.delete_email(email.message_id, permanent=False)
                    if success:
                        email.is_deleted = True
                        email.deleted_at = datetime.utcnow()
                        actions_taken.append("deleted")
                        await _log_action(db, email_id, "delete_email", True, {
                            'permanent': False
                        })
                    else:
                        logger.warning(f"Failed to delete email {email_id}")
                        await _log_action(db, email_id, "delete_email", False)

            finally:
                if connector:
                    connector.disconnect()

            # Update email status
            email.status = ProcessingStatus.CLASSIFIED
            email.processed_at = datetime.utcnow()
            email.processing_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            await db.commit()

            logger.info(f"Email {email_id} actions completed: {actions_taken}")

            return {
                'status': 'success',
                'actions_taken': actions_taken,
                'category': category.value,
                'confidence': confidence
            }

    except Exception as e:
        logger.error(f"Error applying actions to email {email_id}: {e}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e),
            'actions_taken': actions_taken
        }


def _get_default_folder_for_category(category: EmailCategory) -> Optional[str]:
    """
    Get default folder name for a category.

    Args:
        category: EmailCategory

    Returns:
        Folder name or None
    """
    folder_mapping = {
        EmailCategory.INVOICE: "Finance/Invoices",
        EmailCategory.RECEIPT: "Finance/Receipts",
        EmailCategory.DOCUMENT: "Documents",
        EmailCategory.NEWSLETTER: "Newsletters",
        EmailCategory.PROMOTION: "Promotions",
        EmailCategory.SOCIAL: "Social",
        EmailCategory.NOTIFICATION: "Notifications",
        # Professional and Personal stay in inbox
        EmailCategory.PROFESSIONAL: None,
        EmailCategory.PERSONAL: None,
        EmailCategory.SPAM: None,  # Will be deleted instead
        EmailCategory.UNKNOWN: None,
    }
    return folder_mapping.get(category)


async def bulk_move_emails(
    email_ids: List[int],
    folder: str
) -> Dict[str, Any]:
    """
    Move multiple emails to a folder in batch.

    Handles errors per email and continues processing.
    Updates database in a transaction.

    Args:
        email_ids: List of email IDs to move
        folder: Destination folder name

    Returns:
        Dict with results: {
            'status': 'success'|'partial'|'error',
            'succeeded': List[int],  # Email IDs
            'failed': List[Dict],     # {'email_id': int, 'error': str}
            'total': int
        }
    """
    succeeded = []
    failed = []

    logger.info(f"Bulk moving {len(email_ids)} emails to folder: {folder}")

    try:
        async with get_db_context() as db:
            for email_id in email_ids:
                try:
                    # Get email and account
                    email = await db.get(Email, email_id)
                    if not email:
                        failed.append({'email_id': email_id, 'error': 'Email not found'})
                        continue

                    account = await db.get(EmailAccount, email.account_id)
                    if not account:
                        failed.append({'email_id': email_id, 'error': 'Account not found'})
                        continue

                    # Create connector and move
                    connector = None
                    try:
                        connector = await _get_connector_for_account(account)
                        connector.connect()

                        success = connector.move_email(email.message_id, folder)

                        if success:
                            # Update email in DB
                            email.archived_folder = folder
                            email.status = ProcessingStatus.ARCHIVED
                            succeeded.append(email_id)

                            await _log_action(db, email_id, "bulk_move", True, {
                                'folder': folder
                            })
                        else:
                            failed.append({'email_id': email_id, 'error': 'Move operation failed'})
                            await _log_action(db, email_id, "bulk_move", False, {
                                'folder': folder
                            })

                    finally:
                        if connector:
                            connector.disconnect()

                except Exception as e:
                    logger.error(f"Error moving email {email_id}: {e}", exc_info=True)
                    failed.append({'email_id': email_id, 'error': str(e)})

            # Commit all changes
            await db.commit()

        # Determine overall status
        if not failed:
            status = 'success'
        elif succeeded:
            status = 'partial'
        else:
            status = 'error'

        logger.info(f"Bulk move completed: {len(succeeded)} succeeded, {len(failed)} failed")

        return {
            'status': status,
            'succeeded': succeeded,
            'failed': failed,
            'total': len(email_ids)
        }

    except Exception as e:
        logger.error(f"Bulk move operation failed: {e}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e),
            'succeeded': succeeded,
            'failed': failed,
            'total': len(email_ids)
        }


async def apply_label(
    email_id: int,
    label: str
) -> Dict[str, Any]:
    """
    Apply a Gmail label to an email.

    Note: This only works for Gmail accounts. For other account types,
    this function will return an error.

    Args:
        email_id: Email ID
        label: Label name to apply

    Returns:
        Dict with result: {
            'status': 'success'|'error',
            'error': Optional[str]
        }
    """
    logger.info(f"Applying label '{label}' to email {email_id}")

    try:
        async with get_db_context() as db:
            # Get email and account
            email = await db.get(Email, email_id)
            if not email:
                return {
                    'status': 'error',
                    'error': f'Email {email_id} not found'
                }

            account = await db.get(EmailAccount, email.account_id)
            if not account:
                return {
                    'status': 'error',
                    'error': f'Account {email.account_id} not found'
                }

            # Check if account is Gmail
            if account.account_type != AccountType.GMAIL:
                return {
                    'status': 'error',
                    'error': f'Labels are only supported for Gmail accounts (account type: {account.account_type.value})'
                }

            # Create Gmail connector
            connector = None
            try:
                connector = await _get_connector_for_account(account)
                connector.connect()

                # Apply label using Gmail API
                # Note: GmailConnector should implement apply_label method
                if hasattr(connector, 'apply_label'):
                    success = connector.apply_label(email.message_id, label)

                    if success:
                        await _log_action(db, email_id, "apply_label", True, {
                            'label': label
                        })
                        await db.commit()

                        return {
                            'status': 'success',
                            'label': label
                        }
                    else:
                        return {
                            'status': 'error',
                            'error': 'Failed to apply label'
                        }
                else:
                    return {
                        'status': 'error',
                        'error': 'Gmail connector does not support label operations'
                    }

            finally:
                if connector:
                    connector.disconnect()

    except Exception as e:
        logger.error(f"Error applying label to email {email_id}: {e}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e)
        }


async def bulk_classify_pending_emails(limit: int = 100) -> Dict[str, Any]:
    """
    Classify all pending emails in batch.

    This function:
    1. Fetches pending emails from database
    2. Classifies each using rules first, then LLM if needed
    3. Applies appropriate actions
    4. Updates database

    Args:
        limit: Maximum number of emails to process

    Returns:
        Dict with results: {
            'status': 'success',
            'processed': int,
            'classified': int,
            'errors': int
        }
    """
    logger.info(f"Starting bulk classification of pending emails (limit: {limit})")

    processed = 0
    classified = 0
    errors = 0

    try:
        async with get_db_context() as db:
            # Get pending emails
            query = select(Email).where(
                Email.status == ProcessingStatus.PENDING
            ).limit(limit)

            result = await db.execute(query)
            emails = result.scalars().all()

            logger.info(f"Found {len(emails)} pending emails to classify")

            # Import classifier
            from worker.classifiers.ollama_classifier import classifier

            for email in emails:
                try:
                    processed += 1

                    # Build email data
                    email_data = {
                        'subject': email.subject,
                        'sender': email.sender,
                        'body_preview': email.body_preview,
                        'has_attachments': email.has_attachments,
                        'attachment_names': []
                    }

                    # Try rules first
                    rule = rules_parser.find_matching_rule(email_data)

                    if rule:
                        # Rule matched - use rule category
                        category = rule.category
                        confidence = 95  # High confidence for rule-based
                        reason = f"Matched rule: {rule.name}"

                    else:
                        # No rule - use LLM classification
                        result = await classifier.classify_email(
                            subject=email.subject,
                            sender=email.sender,
                            body_preview=email.body_preview or "",
                            has_attachments=email.has_attachments
                        )

                        category = result['category']
                        confidence = result['confidence']
                        reason = result['reason']

                    # Update email classification
                    email.category = category
                    email.classification_confidence = confidence
                    email.classification_reason = reason
                    email.status = ProcessingStatus.PROCESSING

                    await db.commit()

                    # Apply actions (in background to avoid blocking)
                    await apply_classification_action(
                        email_id=email.id,
                        category=category,
                        confidence=confidence,
                        rule_matched=rule.name if rule else None
                    )

                    classified += 1

                except Exception as e:
                    logger.error(f"Error classifying email {email.id}: {e}", exc_info=True)
                    errors += 1

                    # Mark as error
                    email.status = ProcessingStatus.ERROR
                    await db.commit()

        logger.info(f"Bulk classification completed: {classified}/{processed} classified, {errors} errors")

        return {
            'status': 'success',
            'processed': processed,
            'classified': classified,
            'errors': errors
        }

    except Exception as e:
        logger.error(f"Bulk classification failed: {e}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e),
            'processed': processed,
            'classified': classified,
            'errors': errors
        }
