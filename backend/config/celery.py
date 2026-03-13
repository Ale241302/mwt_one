import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    # Sprint 2 tasks (preservadas)
    'evaluar-relojes-diario': {
        'task': 'apps.expedientes.tasks.evaluar_relojes_credito',
        'schedule': crontab(hour=2, minute=0),
    },
    'dispatch-events-5min': {
        'task': 'apps.expedientes.tasks.process_pending_events',
        'schedule': crontab(minute='*/5'),
    },
    # Sprint 8 S8-06: purga de ConversationLog expirados
    'purge-expired-logs-diario': {
        'task': 'apps.knowledge.tasks.purge_expired_logs',
        'schedule': crontab(hour=3, minute=0),
    },
}
