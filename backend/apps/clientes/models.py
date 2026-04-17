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

class ClientUltimateParent(models.Model):
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class ClientGroup(models.Model):
    parent = models.ForeignKey(ClientUltimateParent, on_delete=models.SET_NULL, null=True, blank=True, related_name='groups')
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class ClientSubsidiary(models.Model):
    group = models.ForeignKey(ClientGroup, on_delete=models.CASCADE, related_name='subsidiaries')
    alias = models.CharField(max_length=8)
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=100)
    legal_entity = models.ForeignKey(LegalEntity, on_delete=models.SET_NULL, null=True, blank=True, related_name='subsidiaries')

    # S16-03: Legal Entity details for Billing
    legal_name = models.CharField(max_length=255, blank=True, null=True)
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    email_billing = models.EmailField(blank=True, null=True)

    # S17-12: Days of grace after due date before collections email is triggered
    payment_grace_days = models.IntegerField(
        default=15,
        help_text="Días de gracia post-vencimiento antes de email cobranza."
    )

    # S26-02: Email de contacto para notificaciones transaccionales
    contact_email = models.EmailField(
        null=True, blank=True,
        help_text="Email de contacto para notificaciones. Si null, se salta notificación."
    )
    # S26-02: Idioma preferido para templates email
    preferred_language = models.CharField(
        max_length=5,
        null=True, blank=True,
        help_text="Idioma preferido (ISO 639-1). Default: es si null."
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

from apps.core.models import LegalEntity, UUIDReferenceField

class ClientBrandExternalCode(models.Model):
    subsidiary = models.ForeignKey(ClientSubsidiary, on_delete=models.CASCADE, related_name='external_codes')
    brand_id = UUIDReferenceField(target_module='brands', db_index=True)
    sap_code = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('subsidiary', 'brand_id')

    def __str__(self):
        return f"{self.sap_code} ({self.subsidiary.alias} - {self.brand.slug})"
