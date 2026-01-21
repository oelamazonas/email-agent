"""
Celery worker pour tâches asynchrones
"""
from celery import Celery
from celery.schedules import crontab
from shared.config import settings
import logging

logger = logging.getLogger(__name__)

# Configuration Celery
celery_app = Celery(
    "email_agent_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        'worker.tasks.email_sync',
        'worker.tasks.email_classification',
        'worker.tasks.classification',
        'worker.tasks.maintenance'
    ]
)

# Configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max par tâche
    worker_max_tasks_per_child=100,
    broker_connection_retry_on_startup=True,
)

# Configuration du scheduler (Celery Beat)
celery_app.conf.beat_schedule = {
    # Synchroniser les emails toutes les X minutes
    'sync-all-accounts': {
        'task': 'worker.tasks.email_sync.sync_all_accounts',
        'schedule': crontab(minute=f'*/{settings.EMAIL_POLL_INTERVAL}'),
    },
    # Classifier les emails en attente toutes les 10 minutes
    'classify-pending-emails': {
        'task': 'worker.tasks.email_classification.classify_pending_emails',
        'schedule': crontab(minute='*/10'),
        'kwargs': {'limit': 100}
    },
    # Nettoyer les emails en quarantaine tous les jours à 2h du matin
    'cleanup-quarantine': {
        'task': 'worker.tasks.maintenance.cleanup_quarantine',
        'schedule': crontab(hour=2, minute=0),
    },
    # Générer les statistiques quotidiennes
    'daily-stats': {
        'task': 'worker.tasks.maintenance.generate_daily_stats',
        'schedule': crontab(hour=1, minute=0),
    },
}


@celery_app.task(bind=True)
def debug_task(self):
    """Tâche de test pour vérifier que Celery fonctionne"""
    logger.info(f'Request: {self.request!r}')
    return {
        'status': 'ok',
        'task_id': self.request.id,
        'message': 'Celery is working!'
    }
