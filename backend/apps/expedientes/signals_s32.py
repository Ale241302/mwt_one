from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from apps.expedientes.models import Expediente
import logging

logger = logging.getLogger(__name__)

@receiver(pre_save, sender=Expediente)
def capture_old_status(sender, instance, **kwargs):
    if instance.pk:
        old_instance = Expediente.objects.get(pk=instance.pk)
        instance._old_status = old_instance.status
    else:
        instance._old_status = None

@receiver(post_save, sender=Expediente)
def trigger_state_change_notifications(sender, instance, created, **kwargs):
    """
    S32: Automatización de Notificaciones
    """
    old_status = getattr(instance, '_old_status', None)
    
    if old_status and old_status != instance.status:
        try:
            from apps.expedientes.tasks import send_notification_task
            template_key = f"expediente.status.{str(instance.status).lower()}"
            
            # Fire and forget asynchronous celery hook
            send_notification_task.delay(
                expediente_id=str(instance.expediente_id),
                template_key=template_key
            )
            logger.info(f"Triggered template {template_key} for Expediente {instance.expediente_id}")
            
        except Exception as e:
            logger.error(f"Failed to trigger state notification for Expediente {instance.expediente_id}: {e}")
