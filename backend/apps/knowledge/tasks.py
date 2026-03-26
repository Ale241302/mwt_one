"""Sprint 8 S8-06: Task Celery para purgar ConversationLog expirados.
Se registra en app.conf.beat_schedule en celery.py.
"""
from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task(name='apps.knowledge.tasks.purge_expired_logs')
def purge_expired_logs():
    """Purga logs con retain_until < hoy. Ejecuta diariamente a las 3am."""
    from apps.knowledge.models import ConversationLog
    today = timezone.now().date()
    qs = ConversationLog.objects.filter(retain_until__lt=today)
    count, _ = qs.delete()
    logger.info('purge_expired_logs: eliminados %d registros', count)
    return {'deleted': count}
