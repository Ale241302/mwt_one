"""Sprint 8 S8-06: Signal post_save en Expediente con transaction.on_commit().
Actualiza retain_until cuando status=CERRADO.
D-10: on_commit() obligatorio para evitar condición de carrera con signals Transfer Sprint 5.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction


@receiver(post_save, sender='expedientes.Expediente')
def update_retention_on_close(sender, instance, **kwargs):
    if instance.status == 'CERRADO':
        def _update():
            from apps.knowledge.models import ConversationLog
            from apps.knowledge.utils import calculate_retention
            logs = ConversationLog.objects.filter(expediente_ref=instance)
            new_retain = calculate_retention(expediente=instance)
            logs.update(retain_until=new_retain)
        transaction.on_commit(_update)
