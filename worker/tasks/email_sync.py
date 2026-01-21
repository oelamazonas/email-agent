"""
Tâches Celery pour la synchronisation des emails
"""
from celery import shared_task
import logging
import asyncio
import json
from sqlalchemy import select
from datetime import datetime
from typing import Optional, Dict, Any

from api.database import get_db_context
from api.models import EmailAccount, Email, AccountType, ProcessingStatus
from shared.security import decrypt_password
from shared.integrations import ImapConnector, GmailConnector, MicrosoftConnector

logger = logging.getLogger(__name__)

async def _get_active_accounts_ids():
    async with get_db_context() as db:
        query = select(EmailAccount.id).where(
            EmailAccount.is_active == True,
            EmailAccount.sync_enabled == True
        )
        result = await db.execute(query)
        return result.scalars().all()

async def _get_account_details(account_id: int):
    async with get_db_context() as db:
        query = select(EmailAccount).where(EmailAccount.id == account_id)
        result = await db.execute(query)
        account = result.scalar_one_or_none()
        if not account:
            return None
            
        return {
            "id": account.id,
            "type": account.account_type,
            "email": account.email_address,
            "encrypted_credentials": account.encrypted_credentials,
            "last_sync": account.last_sync
        }

async def _save_emails(account_id: int, emails_data: list):
    """
    Sauvegarder les emails en base de données.

    Args:
        account_id: ID du compte email
        emails_data: Liste de dicts avec les données des emails

    Returns:
        Nombre d'emails sauvegardés
    """
    if not emails_data:
        return 0

    count = 0
    async with get_db_context() as db:
        for data in emails_data:
            # Vérifier si l'email existe déjà
            existing = await db.execute(
                select(Email).where(
                    Email.account_id == account_id,
                    Email.message_id == data["message_id"]
                )
            )
            if existing.scalar_one_or_none():
                continue

            # Créer l'email
            email = Email(
                account_id=account_id,
                message_id=data["message_id"],
                subject=data["subject"],
                sender=data["sender"],
                date_received=data["date_received"],
                body_preview=data["body"][:500] if data["body"] else "",
                has_attachments=data["has_attachments"],
                attachment_count=data["attachment_count"],
                status=ProcessingStatus.PENDING
            )
            db.add(email)
            count += 1

        # Update account last_sync et clear error
        account = await db.get(EmailAccount, account_id)
        if account:
            account.last_sync = datetime.utcnow()
            account.total_emails_processed = (account.total_emails_processed or 0) + count
            account.last_error = None  # Clear error on successful sync

        await db.commit()
    return count


async def _update_account_error(account_id: int, error_message: str) -> None:
    """
    Enregistrer une erreur de synchronisation dans le compte.

    Args:
        account_id: ID du compte
        error_message: Message d'erreur
    """
    try:
        async with get_db_context() as db:
            account = await db.get(EmailAccount, account_id)
            if account:
                account.last_error = error_message
                await db.commit()
    except Exception as e:
        logger.error(f"Failed to update account error: {e}")

@shared_task(name='worker.tasks.email_sync.sync_all_accounts')
def sync_all_accounts():
    """
    Synchroniser tous les comptes email actifs
    """
    logger.info("Starting sync for all email accounts")
    
    try:
        account_ids = asyncio.run(_get_active_accounts_ids())
        logger.info(f"Found {len(account_ids)} accounts to sync")
        
        for account_id in account_ids:
            sync_account.delay(account_id)
            
        return {
            'status': 'completed',
            'accounts_triggered': len(account_ids)
        }
    except Exception as e:
        logger.error(f"Error in sync_all_accounts: {e}")
        return {'status': 'error', 'error': str(e)}


def _get_connector(account: Dict[str, Any]):
    """
    Créer le connecteur approprié selon le type de compte.

    Args:
        account: Dict avec les détails du compte

    Returns:
        Instance du connecteur approprié

    Raises:
        ValueError: Si le type de compte n'est pas supporté
    """
    account_type = account['type']
    email = account['email']
    encrypted_creds = account['encrypted_credentials']

    if account_type == AccountType.IMAP:
        # Déchiffrer les credentials IMAP
        try:
            from shared.security import decrypt_credentials
            credentials = decrypt_credentials(encrypted_creds)
        except Exception as e:
            logger.error(f"Error decrypting IMAP credentials: {e}")
            raise ValueError(f"Failed to decrypt credentials: {e}")

        # Si les credentials ne sont pas dans le format dict (ancien format)
        if not isinstance(credentials, dict):
            # Fallback: c'est juste un mot de passe
            logger.warning(f"Legacy password format detected for account {email}")

            # Déterminer le host depuis l'email
            if "@gmail.com" in email:
                host = "imap.gmail.com"
            elif "@outlook.com" in email or "@hotmail.com" in email:
                host = "outlook.office365.com"
            else:
                host = "imap.gmail.com"  # Fallback

            credentials = {
                "type": "imap",
                "imap_server": host,
                "imap_port": 993,
                "username": email,
                "password": credentials if isinstance(credentials, str) else decrypt_password(encrypted_creds),
                "use_ssl": True
            }

        return ImapConnector(
            email_address=email,
            credentials=credentials
        )

    elif account_type == AccountType.GMAIL:
        # Déchiffrer les credentials OAuth2
        try:
            from shared.security import decrypt_credentials
            credentials = decrypt_credentials(encrypted_creds)
        except Exception as e:
            logger.error(f"Error decrypting Gmail credentials: {e}")
            raise ValueError(f"Failed to decrypt Gmail credentials: {e}")

        return GmailConnector(
            email_address=email,
            credentials=credentials
        )

    elif account_type == AccountType.OUTLOOK:
        # Déchiffrer les credentials OAuth2
        try:
            from shared.security import decrypt_credentials
            credentials = decrypt_credentials(encrypted_creds)
        except Exception as e:
            logger.error(f"Error decrypting Microsoft credentials: {e}")
            raise ValueError(f"Failed to decrypt Microsoft credentials: {e}")

        return MicrosoftConnector(
            email_address=email,
            credentials=credentials
        )

    else:
        raise ValueError(f"Unsupported account type: {account_type}")


async def _update_credentials_if_refreshed(account_id: int, connector) -> None:
    """
    Mettre à jour les credentials en DB si le token a été refresh.

    Args:
        account_id: ID du compte
        connector: Instance du connecteur (avec méthode get_refreshed_credentials)
    """
    if hasattr(connector, 'get_refreshed_credentials'):
        new_creds = connector.get_refreshed_credentials()
        if new_creds:
            logger.info(f"Updating refreshed credentials for account {account_id}")

            from shared.security import encrypt_credentials
            encrypted = encrypt_credentials(new_creds)

            async with get_db_context() as db:
                account = await db.get(EmailAccount, account_id)
                if account:
                    account.encrypted_credentials = encrypted
                    await db.commit()
                    logger.info("Credentials updated successfully")


@shared_task(name='worker.tasks.email_sync.sync_account')
def sync_account(account_id: int):
    """
    Synchroniser un compte email spécifique.

    Supporte IMAP, Gmail API, et Outlook (à venir).
    """
    logger.info(f"Syncing account {account_id}")

    try:
        # 1. Récupérer les détails du compte
        account = asyncio.run(_get_account_details(account_id))
        if not account:
            logger.error(f"Account {account_id} not found")
            return {'status': 'error', 'message': 'Account not found'}

        # 2. Créer le connecteur approprié
        try:
            connector = _get_connector(account)
        except ValueError as e:
            logger.error(f"Failed to create connector for account {account_id}: {e}")
            return {'status': 'error', 'message': str(e)}
        except NotImplementedError as e:
            logger.warning(f"Account type not yet supported: {e}")
            return {'status': 'skipped', 'message': str(e)}

        # 3. Fetch emails
        emails = connector.fetch_emails(limit=50, since=account['last_sync'])
        logger.info(f"Fetched {len(emails)} emails for account {account_id}")

        # 4. Sauvegarder les emails en DB
        saved_count = asyncio.run(_save_emails(account_id, emails))

        # 5. Mettre à jour les credentials si refresh (OAuth2)
        asyncio.run(_update_credentials_if_refreshed(account_id, connector))

        # 6. Cleanup
        connector.disconnect()

        # 7. Trigger classification for new emails if any
        if saved_count > 0:
            logger.info(f"Triggering classification for {saved_count} new emails")
            from worker.tasks.email_classification import classify_pending_emails
            classify_pending_emails.delay(limit=saved_count)

        logger.info(f"Account {account_id} sync completed. Saved {saved_count} new emails.")
        return {
            'account_id': account_id,
            'new_emails': saved_count,
            'fetched': len(emails),
            'status': 'completed'
        }

    except Exception as e:
        logger.error(f"Error syncing account {account_id}: {e}", exc_info=True)

        # Enregistrer l'erreur dans la DB
        asyncio.run(_update_account_error(account_id, str(e)))

        return {'status': 'error', 'error': str(e)}
