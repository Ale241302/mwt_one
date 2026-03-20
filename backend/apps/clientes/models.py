from django.db import models
from apps.core.models import LegalEntity


class Cliente(models.Model):
    name = models.CharField(max_length=255)
    contact_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    legal_entity = models.ForeignKey(
        LegalEntity,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='clientes',
    )
    credit_approved = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clientes_cliente'
        ordering = ['name']
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    def __str__(self):
        return self.name

    @property
    def legal_entity_name(self):
        return self.legal_entity.legal_name if self.legal_entity else None

    @property
    def active_expedientes(self):
        from apps.expedientes.models import Expediente
        from apps.expedientes.enums_exp import ExpedienteStatus
        try:
            return Expediente.objects.filter(
                client__name=self.name
            ).exclude(
                status__in=[ExpedienteStatus.CERRADO, ExpedienteStatus.CANCELADO]
            ).count()
        except Exception:
            return 0
