"""
Celery tasks for email classification and action execution.
"""
from celery import shared_task
import logging
import asyncio
from typing import Optional

from worker.actions import bulk_classify_pending_emails

logger = logging.getLogger(__name__)


def run_async(coro):
    """
    Helper to run async code safely in Celery worker context.
    Celery workers already have an event loop, so we can't use asyncio.run().
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@shared_task(name='worker.tasks.email_classification.classify_pending_emails')
def classify_pending_emails(limit: int = 100):
    """
    Classify all pending emails and apply actions.

    This task:
    1. Fetches pending emails from database
    2. Classifies using rules first, then LLM if needed
    3. Applies appropriate actions (move, delete, etc.)
    4. Updates database

    Args:
        limit: Maximum number of emails to process

    Returns:
        Dict with processing results
    """
    logger.info(f"Starting classification task (limit: {limit})")

    try:
        result = run_async(bulk_classify_pending_emails(limit=limit))

        logger.info(f"Classification task completed: {result}")
        return result

    except Exception as e:
        logger.error(f"Classification task failed: {e}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e)
        }


@shared_task(name='worker.tasks.email_classification.classify_single_email')
def classify_single_email(email_id: int):
    """
    Classify a single email and apply actions.

    Args:
        email_id: Email ID to classify

    Returns:
        Dict with classification result
    """
    logger.info(f"Classifying email {email_id}")

    try:
        from api.database import get_db_context
        from api.models import Email, ProcessingStatus
        from worker.classifiers.ollama_classifier import classifier
        from worker.rules import rules_parser
        from worker.actions import apply_classification_action
        from sqlalchemy import select

        async def _classify():
            async with get_db_context() as db:
                # Get email
                email = await db.get(Email, email_id)
                if not email:
                    return {
                        'status': 'error',
                        'error': f'Email {email_id} not found'
                    }

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
                    # Rule matched
                    category = rule.category
                    confidence = 95
                    reason = f"Matched rule: {rule.name}"
                    rule_name = rule.name
                else:
                    # Use LLM
                    result = await classifier.classify_email(
                        subject=email.subject,
                        sender=email.sender,
                        body_preview=email.body_preview or "",
                        has_attachments=email.has_attachments
                    )

                    category = result['category']
                    confidence = result['confidence']
                    reason = result['reason']
                    rule_name = None

                # Update email
                email.category = category
                email.classification_confidence = confidence
                email.classification_reason = reason
                email.status = ProcessingStatus.PROCESSING

                await db.commit()

                # Apply actions
                action_result = await apply_classification_action(
                    email_id=email_id,
                    category=category,
                    confidence=confidence,
                    rule_matched=rule_name
                )

                return {
                    'status': 'success',
                    'email_id': email_id,
                    'category': category.value,
                    'confidence': confidence,
                    'reason': reason,
                    'rule_matched': rule_name,
                    'actions': action_result
                }

        result = run_async(_classify())
        logger.info(f"Email {email_id} classification completed: {result}")
        return result

    except Exception as e:
        logger.error(f"Error classifying email {email_id}: {e}", exc_info=True)
        return {
            'status': 'error',
            'email_id': email_id,
            'error': str(e)
        }
