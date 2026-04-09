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
    # Sprint 23 S23-07: liquidacion trimestral de rebates
    # Corre el dia 1 de enero, abril, julio y octubre a las 06:00
    'liquidate-rebates-trimestral': {
        'task': 'apps.commercial.tasks.liquidate_rebates',
        'schedule': crontab(hour=6, minute=0, day_of_month=1, month_of_year='1,4,7,10'),
    },
    # Sprint 26 S26-08: cobranza diaria 8:00 AM Costa Rica (14:00 UTC)
    'check-overdue-payments': {
        'task': 'apps.notifications.tasks.check_overdue_payments',
        'schedule': crontab(hour=14, minute=0),
    },
}
