"""
Tâches Celery pour la maintenance
"""
from celery import shared_task
import logging
import asyncio
from datetime import datetime, timedelta

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


@shared_task(name='worker.tasks.maintenance.cleanup_quarantine')
def cleanup_quarantine():
    """
    Nettoyer les emails en quarantaine (supprimés mais pas encore purgés)
    Exécuté quotidiennement
    """
    logger.info("Starting quarantine cleanup")

    from api.database import get_db_context
    from api.models import Email
    from sqlalchemy import select, and_
    from shared.config import settings

    async def _cleanup():
        async with get_db_context() as db:
            # 1. Récupérer les emails deleted_at > QUARANTINE_DAYS
            cutoff_date = datetime.utcnow() - timedelta(days=settings.QUARANTINE_DAYS)

            query = select(Email).where(
                and_(
                    Email.is_deleted == True,
                    Email.deleted_at < cutoff_date
                )
            )

            result = await db.execute(query)
            emails_to_delete = result.scalars().all()

            count = len(emails_to_delete)

            if count > 0:
                # 2. Les supprimer définitivement de la DB
                for email in emails_to_delete:
                    await db.delete(email)

                await db.commit()
                logger.info(f"Deleted {count} emails from quarantine")
            else:
                logger.info("No emails to delete from quarantine")

            return count

    try:
        # 3. Logger le nombre d'emails supprimés
        emails_deleted = run_async(_cleanup())

        logger.info(f"Quarantine cleanup completed: {emails_deleted} emails deleted")
        return {
            'emails_deleted': emails_deleted,
            'status': 'completed'
        }
    except Exception as e:
        logger.error(f"Quarantine cleanup failed: {e}", exc_info=True)
        return {
            'emails_deleted': 0,
            'status': 'error',
            'error': str(e)
        }


@shared_task(name='worker.tasks.maintenance.generate_daily_stats')
def generate_daily_stats():
    """
    Générer les statistiques quotidiennes
    Exécuté chaque jour à 1h du matin
    """
    logger.info("Generating daily statistics")

    from api.database import get_db_context
    from api.models import Email, EmailCategory, ProcessingStatus
    from sqlalchemy import select, func, and_

    async def _generate_stats():
        async with get_db_context() as db:
            stats = {
                'date': datetime.utcnow().date().isoformat(),
                'categories': {},
                'processing_stats': {},
                'totals': {}
            }

            # 1. Compter les emails par catégorie (dernières 24h)
            yesterday = datetime.utcnow() - timedelta(days=1)

            for category in EmailCategory:
                query = select(func.count(Email.id)).where(
                    and_(
                        Email.category == category,
                        Email.created_at >= yesterday
                    )
                )
                result = await db.execute(query)
                count = result.scalar()
                stats['categories'][category.value] = count

            # 2. Calculer les temps de traitement moyens
            query = select(
                func.avg(Email.processing_time_ms),
                func.min(Email.processing_time_ms),
                func.max(Email.processing_time_ms)
            ).where(
                and_(
                    Email.processing_time_ms.isnot(None),
                    Email.created_at >= yesterday
                )
            )
            result = await db.execute(query)
            avg_time, min_time, max_time = result.first()

            stats['processing_stats'] = {
                'avg_time_ms': int(avg_time) if avg_time else 0,
                'min_time_ms': int(min_time) if min_time else 0,
                'max_time_ms': int(max_time) if max_time else 0
            }

            # 3. Compter les emails par statut
            for status in ProcessingStatus:
                query = select(func.count(Email.id)).where(
                    and_(
                        Email.status == status,
                        Email.created_at >= yesterday
                    )
                )
                result = await db.execute(query)
                count = result.scalar()
                stats['totals'][status.value] = count

            # Total d'emails traités
            query = select(func.count(Email.id)).where(Email.created_at >= yesterday)
            result = await db.execute(query)
            stats['totals']['total_emails'] = result.scalar()

            logger.info(f"Daily stats: {stats}")
            return stats

    try:
        stats = run_async(_generate_stats())

        logger.info(f"Daily stats generated successfully")
        return {
            'date': stats['date'],
            'status': 'completed',
            'stats': stats
        }
    except Exception as e:
        logger.error(f"Failed to generate daily stats: {e}", exc_info=True)
        return {
            'date': datetime.utcnow().date().isoformat(),
            'status': 'error',
            'error': str(e)
        }


@shared_task(name='worker.tasks.maintenance.optimize_database')
def optimize_database():
    """
    Optimiser la base de données (VACUUM, ANALYZE)
    Exécuté hebdomadairement
    """
    logger.info("Starting database optimization")

    from api.database import get_db_context
    from sqlalchemy import text

    async def _optimize():
        results = []

        async with get_db_context() as db:
            # Liste des tables principales à optimiser
            tables = [
                'emails',
                'email_accounts',
                'email_attachments',
                'processing_logs',
                'users'
            ]

            # 1. VACUUM ANALYZE sur les tables principales
            for table in tables:
                try:
                    logger.info(f"Running VACUUM ANALYZE on {table}")

                    # Note: VACUUM cannot run inside a transaction block
                    # We need to commit and use autocommit
                    await db.commit()

                    # Execute VACUUM ANALYZE (PostgreSQL specific)
                    await db.execute(text(f"VACUUM ANALYZE {table}"))

                    results.append({
                        'table': table,
                        'operation': 'VACUUM ANALYZE',
                        'status': 'success'
                    })

                    logger.info(f"VACUUM ANALYZE completed for {table}")

                except Exception as e:
                    logger.error(f"Failed to optimize {table}: {e}")
                    results.append({
                        'table': table,
                        'operation': 'VACUUM ANALYZE',
                        'status': 'error',
                        'error': str(e)
                    })

            # 2. Réindexer les index principaux si nécessaire
            # PostgreSQL auto-gère généralement les index, mais on peut forcer REINDEX si besoin
            try:
                logger.info("Checking index health")

                # Query pour vérifier la santé des index
                query = text("""
                    SELECT schemaname, tablename, indexname
                    FROM pg_indexes
                    WHERE schemaname = 'public'
                    ORDER BY tablename, indexname
                """)

                result = await db.execute(query)
                indexes = result.fetchall()

                logger.info(f"Found {len(indexes)} indexes in public schema")

            except Exception as e:
                logger.error(f"Failed to check indexes: {e}")

            return results

    try:
        results = run_async(_optimize())

        success_count = sum(1 for r in results if r.get('status') == 'success')
        error_count = sum(1 for r in results if r.get('status') == 'error')

        logger.info(f"Database optimization completed: {success_count} success, {error_count} errors")

        return {
            'status': 'completed',
            'tables_optimized': success_count,
            'errors': error_count,
            'details': results
        }

    except Exception as e:
        logger.error(f"Database optimization failed: {e}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e)
        }
