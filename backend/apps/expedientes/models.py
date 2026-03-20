import uuid
from django.db import models
from django.core.exceptions import ValidationError

from apps.core.models import TimestampMixin, AppendOnlyModel, LegalEntity
from .enums_artifacts import ArtifactStatusEnum
from .enums_exp import (
    ExpedienteStatus, BlockedByType, DispatchMode, PaymentStatus,
    CreditClockStartRule, AggregateType,
    RegisteredByType, CostLineVisibility, LogisticsMode, LogisticsSource,
    CostCategory, CostBehavior, AforoType,
)


class Expediente(TimestampMixin):
    expediente_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    legal_entity = models.ForeignKey(LegalEntity, on_delete=models.PROTECT, related_name='expedientes_emitidos', help_text='Entidad emisora')
    brand = models.ForeignKey('brands.Brand', on_delete=models.PROTECT, null=True, blank=True)
    destination = models.CharField(max_length=10, choices=[('CR', 'Costa Rica'), ('USA', 'United States')], default='CR')
    client = models.ForeignKey(LegalEntity, on_delete=models.PROTECT, related_name='expedientes_como_cliente', help_text='Cliente')
    status = models.CharField(max_length=20, choices=ExpedienteStatus.choices, default=ExpedienteStatus.REGISTRO)
    is_blocked = models.BooleanField(default=False)
    blocked_reason = models.TextField(blank=True, null=True)
    blocked_at = models.DateTimeField(blank=True, null=True)
    blocked_by_type = models.CharField(max_length=10, choices=BlockedByType.choices, blank=True, null=True)
    blocked_by_id = models.CharField(max_length=255, blank=True, null=True, help_text='user_id if CEO, rule_name if SYSTEM')
    mode = models.CharField(max_length=50, blank=True, help_text='Modalidad operativa')
    freight_mode = models.CharField(max_length=50, blank=True)
    transport_mode = models.CharField(max_length=50, blank=True)
    dispatch_mode = models.CharField(max_length=10, choices=DispatchMode.choices, default=DispatchMode.MWT)
    price_basis = models.CharField(max_length=50, blank=True)
    credit_clock_start_rule = models.CharField(max_length=20, choices=CreditClockStartRule.choices, default=CreditClockStartRule.ON_CREATION)
    credit_clock_started_at = models.DateTimeField(blank=True, null=True, help_text='Timestamp when credit clock started (FIX-7)')
    payment_status = models.CharField(max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    payment_registered_at = models.DateTimeField(blank=True, null=True)
    payment_registered_by_type = models.CharField(max_length=10, choices=BlockedByType.choices, blank=True, null=True)
    payment_registered_by_id = models.CharField(max_length=255, blank=True, null=True)
    nodo_destino = models.ForeignKey(
        'transfers.Node',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='expedientes_destino',
        help_text='Target node (triggers transfer suggestion on close)'
    )
    external_fiscal_refs = models.JSONField(
        default=dict, blank=True,
        help_text='DANFE, DU-E, etc. (H5)'
    )
    aforo_type = models.CharField(
        max_length=10, choices=AforoType.choices,
        blank=True, null=True, help_text='H9'
    )
    aforo_date = models.DateField(blank=True, null=True, help_text='H9')

    class Meta:
        verbose_name = 'Expediente'
        verbose_name_plural = 'Expedientes'
        ordering = ['-created_at']

    def __str__(self):
        return f'EXP-{str(self.expediente_id)[:8]}'


class ArtifactInstance(TimestampMixin):
    artifact_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    expediente = models.ForeignKey(Expediente, on_delete=models.CASCADE, related_name='artifacts')
    artifact_type = models.CharField(max_length=20, help_text='ART-01 to ART-19')
    status = models.CharField(max_length=20, choices=ArtifactStatusEnum.choices(), default=ArtifactStatusEnum.DRAFT)
    payload = models.JSONField(default=dict)
    supersedes = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name='superseded_by_set',
    )
    superseded_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name='supersedes_set',
    )

    class Meta:
        verbose_name = 'Artifact Instance'
        verbose_name_plural = 'Artifact Instances'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.artifact_type} \u2013 {self.get_status_display()}'


class EventLog(models.Model):
    event_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=100, help_text='e.g. "expediente.state_changed"')
    aggregate_type = models.CharField(max_length=20, choices=AggregateType.choices)
    aggregate_id = models.UUIDField()
    payload = models.JSONField(default=dict)
    occurred_at = models.DateTimeField()
    emitted_by = models.CharField(max_length=100, help_text='e.g. "C5:RegisterSAPConfirmation"')
    processed_at = models.DateTimeField(blank=True, null=True, help_text='null until dispatcher consumes')
    retry_count = models.IntegerField(default=0)
    correlation_id = models.UUIDField()

    class Meta:
        verbose_name = 'Event Log'
        verbose_name_plural = 'Event Logs'
        ordering = ['-occurred_at']
        indexes = [
            models.Index(fields=['aggregate_type', 'aggregate_id'], name='idx_eventlog_aggregate'),
            models.Index(fields=['processed_at'], name='idx_eventlog_processed'),
            models.Index(fields=['correlation_id'], name='idx_eventlog_correlation'),
        ]

    def __str__(self):
        return f'{self.event_type} @ {self.occurred_at}'


class CostLine(AppendOnlyModel):
    cost_line_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    expediente = models.ForeignKey(
        Expediente,
        on_delete=models.PROTECT,
        related_name='cost_lines',
        null=True, blank=True,
    )
    transfer = models.ForeignKey(
        'transfers.Transfer',
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='cost_lines',
        help_text='XOR with expediente \u2013 use one or the other'
    )
    cost_type = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, help_text='ISO 4217')
    phase = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    visibility = models.CharField(
        max_length=10,
        choices=CostLineVisibility.choices,
        default=CostLineVisibility.INTERNAL,
        help_text='internal=CEO-only, client=visible to client'
    )
    category = models.CharField(
        max_length=20, choices=CostCategory.choices,
        default=CostCategory.LANDED_COST, help_text='H2'
    )
    behavior = models.CharField(
        max_length=20, choices=CostBehavior.choices,
        default=CostBehavior.VARIABLE_PER_UNIT, help_text='H3'
    )
    exchange_rate = models.DecimalField(
        max_digits=12, decimal_places=4,
        blank=True, null=True, help_text='H8'
    )
    amount_base_currency = models.DecimalField(
        max_digits=12, decimal_places=2,
        blank=True, null=True, help_text='H8 (USD)'
    )
    base_currency = models.CharField(
        max_length=3, default='USD', help_text='H8'
    )

    class Meta:
        verbose_name = 'Cost Line'
        verbose_name_plural = 'Cost Lines'
        ordering = ['-created_at']

    def __str__(self):
        return f'Cost {self.cost_type}: {self.amount} {self.currency}'


class PaymentLine(AppendOnlyModel):
    payment_line_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    expediente = models.ForeignKey(Expediente, on_delete=models.PROTECT, related_name='payment_lines')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, help_text='ISO 4217')
    method = models.CharField(max_length=50, help_text='transferencia, cheque, otro')
    reference = models.CharField(max_length=100, help_text='N\u00famero de comprobante')
    registered_at = models.DateTimeField()
    registered_by_type = models.CharField(max_length=10, choices=RegisteredByType.choices)
    registered_by_id = models.CharField(max_length=255)

    class Meta:
        verbose_name = 'Payment Line'
        verbose_name_plural = 'Payment Lines'
        ordering = ['-created_at']

    def __str__(self):
        return f'Payment {self.method}: {self.amount} {self.currency}'


class LogisticsOption(TimestampMixin):
    logistics_option_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    artifact_instance = models.ForeignKey(ArtifactInstance, on_delete=models.CASCADE, related_name='logistics_options')
    option_id = models.CharField(max_length=50)
    mode = models.CharField(max_length=20, choices=LogisticsMode.choices)
    carrier = models.CharField(max_length=100)
    route = models.CharField(max_length=200)
    estimated_days = models.IntegerField()
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, help_text='ISO 4217')
    valid_until = models.DateField(null=True, blank=True)
    source = models.CharField(max_length=20, choices=LogisticsSource.choices, default=LogisticsSource.MANUAL)
    is_selected = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Logistics Option'
        verbose_name_plural = 'Logistics Options'
        ordering = ['-created_at']

    def __str__(self):
        return f'Option {self.option_id}: {self.mode} via {self.carrier}'
