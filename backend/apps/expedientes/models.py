import uuid
from django.db import models
from django.core.exceptions import ValidationError

from apps.core.models import TimestampMixin, AppendOnlyModel
from .enums import (
    LegalEntityRole, LegalEntityRelationship, LegalEntityFrontend,
    LegalEntityVisibility, PricingVisibility, LegalEntityStatus,
    ExpedienteStatus, BlockedByType, DispatchMode, PaymentStatus,
    CreditClockStartRule, Brand, ArtifactStatus, AggregateType,
    RegisteredByType, CostLineVisibility, LogisticsMode, LogisticsSource,
)


# ──────────────────────────────────────────────────
# Item 3: LegalEntity + Expediente
# ──────────────────────────────────────────────────

class LegalEntity(TimestampMixin):
    """
    Ref: ENT_PLAT_LEGAL_ENTITY.B
    Represents a legal entity in the MWT ecosystem.
    """
    entity_id = models.CharField(max_length=50, unique=True,
                                 help_text="e.g. MWT-CR, SONDEL-CR")
    legal_name = models.CharField(max_length=255)
    country = models.CharField(max_length=3, help_text="ISO 3166-1 alpha-2/3")
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    role = models.CharField(max_length=20, choices=LegalEntityRole.choices)
    relationship_to_mwt = models.CharField(max_length=20,
                                           choices=LegalEntityRelationship.choices)
    frontend = models.CharField(max_length=20,
                                choices=LegalEntityFrontend.choices)
    visibility_level = models.CharField(max_length=20,
                                        choices=LegalEntityVisibility.choices)
    pricing_visibility = models.CharField(max_length=20,
                                          choices=PricingVisibility.choices)
    status = models.CharField(max_length=20,
                              choices=LegalEntityStatus.choices,
                              default=LegalEntityStatus.ONBOARDING)

    class Meta:
        verbose_name = 'Legal Entity'
        verbose_name_plural = 'Legal Entities'
        ordering = ['legal_name']

    def __str__(self):
        return f"{self.entity_id} — {self.legal_name}"


class Expediente(TimestampMixin):
    """
    Ref: ENT_OPS_STATE_MACHINE §A, §C, §D, §L
    Core business object: a trade/logistics dossier.
    """
    expediente_id = models.UUIDField(primary_key=True, default=uuid.uuid4,
                                     editable=False)
    legal_entity = models.ForeignKey(LegalEntity,
                                     on_delete=models.PROTECT,
                                     related_name='expedientes_emitidos',
                                     help_text="Entidad emisora")
    brand = models.ForeignKey('brands.Brand', on_delete=models.PROTECT, null=True, blank=True)
    destination = models.CharField(max_length=10, choices=[('CR', 'Costa Rica'), ('USA', 'United States')], default='CR')
    client = models.ForeignKey(LegalEntity,
                               on_delete=models.PROTECT,
                               related_name='expedientes_como_cliente',
                               help_text="Cliente")
    # --- Status ---
    status = models.CharField(max_length=20,
                              choices=ExpedienteStatus.choices,
                              default=ExpedienteStatus.REGISTRO)
    # --- Block fields (5) ---
    is_blocked = models.BooleanField(default=False)
    blocked_reason = models.TextField(blank=True, null=True)
    blocked_at = models.DateTimeField(blank=True, null=True)
    blocked_by_type = models.CharField(max_length=10,
                                       choices=BlockedByType.choices,
                                       blank=True, null=True)
    blocked_by_id = models.CharField(max_length=255, blank=True, null=True,
                                     help_text="user_id if CEO, rule_name if SYSTEM")
    # --- Modality fields ---
    mode = models.CharField(max_length=50, blank=True,
                            help_text="Modalidad operativa")
    freight_mode = models.CharField(max_length=50, blank=True)
    transport_mode = models.CharField(max_length=50, blank=True)
    dispatch_mode = models.CharField(max_length=10,
                                     choices=DispatchMode.choices,
                                     default=DispatchMode.MWT)
    price_basis = models.CharField(max_length=50, blank=True)
    # --- Credit clock ---
    credit_clock_start_rule = models.CharField(
        max_length=20,
        choices=CreditClockStartRule.choices,
        default=CreditClockStartRule.ON_CREATION)
    credit_clock_started_at = models.DateTimeField(
        blank=True, null=True, default=None,
        help_text='Timestamp when credit clock started (FIX-7)')
    # --- Payment fields (4) ---
    payment_status = models.CharField(max_length=10,
                                      choices=PaymentStatus.choices,
                                      default=PaymentStatus.PENDING)
    payment_registered_at = models.DateTimeField(blank=True, null=True)
    payment_registered_by_type = models.CharField(
        max_length=10,
        choices=BlockedByType.choices,
        blank=True, null=True)
    payment_registered_by_id = models.CharField(max_length=255,
                                                blank=True, null=True)
    # Sprint 5 S5-01: nodo_destino — FK to Node for transfer handoff
    nodo_destino = models.ForeignKey(
        'transfers.Node', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='expedientes_destino',
        help_text='Target node (triggers transfer suggestion on close)'
    )

    class Meta:
        verbose_name = 'Expediente'
        verbose_name_plural = 'Expedientes'
        ordering = ['-created_at']

    def __str__(self):
        return f"EXP-{str(self.expediente_id)[:8]}"


# ──────────────────────────────────────────────────
# Item 4A: ArtifactInstance + EventLog
# ──────────────────────────────────────────────────

class ArtifactInstance(TimestampMixin):
    """
    Ref: ENT_OPS_STATE_MACHINE §G, §I
    Generic business artifact linked to an Expediente.
    """
    artifact_id = models.UUIDField(primary_key=True, default=uuid.uuid4,
                                   editable=False)
    expediente = models.ForeignKey(Expediente,
                                   on_delete=models.CASCADE,
                                   related_name='artifacts')
    artifact_type = models.CharField(max_length=20,
                                     help_text="ART-01 to ART-19")
    status = models.CharField(max_length=20,
                              choices=ArtifactStatus.choices,
                              default=ArtifactStatus.DRAFT)
    payload = models.JSONField(default=dict)
    supersedes = models.ForeignKey('self', on_delete=models.SET_NULL,
                                   blank=True, null=True,
                                   related_name='superseded_by_set')
    superseded_by = models.ForeignKey('self', on_delete=models.SET_NULL,
                                      blank=True, null=True,
                                      related_name='supersedes_set')

    class Meta:
        verbose_name = 'Artifact Instance'
        verbose_name_plural = 'Artifact Instances'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.artifact_type} — {self.get_status_display()}"


class EventLog(models.Model):
    """
    Ref: ENT_OPS_STATE_MACHINE §K — Outbox pattern.
    Exactly 10 fields as per spec.
    """
    event_id = models.UUIDField(primary_key=True, default=uuid.uuid4,
                                editable=False)
    event_type = models.CharField(max_length=100,
                                  help_text='e.g. "expediente.state_changed"')
    aggregate_type = models.CharField(max_length=20,
                                      choices=AggregateType.choices)
    aggregate_id = models.UUIDField()
    payload = models.JSONField(default=dict)
    occurred_at = models.DateTimeField()
    emitted_by = models.CharField(max_length=100,
                                  help_text='e.g. "C5:RegisterSAPConfirmation"')
    processed_at = models.DateTimeField(blank=True, null=True,
                                        help_text="null until dispatcher consumes")
    retry_count = models.IntegerField(default=0)
    correlation_id = models.UUIDField()

    class Meta:
        verbose_name = 'Event Log'
        verbose_name_plural = 'Event Logs'
        ordering = ['-occurred_at']
        indexes = [
            models.Index(fields=['aggregate_type', 'aggregate_id'],
                         name='idx_eventlog_aggregate'),
            models.Index(fields=['processed_at'],
                         name='idx_eventlog_processed'),
            models.Index(fields=['correlation_id'],
                         name='idx_eventlog_correlation'),
        ]

    def __str__(self):
        return f"{self.event_type} @ {self.occurred_at}"


# ──────────────────────────────────────────────────
# Item 4B: CostLine + PaymentLine (AppendOnly)
# ──────────────────────────────────────────────────

class CostLine(AppendOnlyModel):
    """
    Ref: ENT_OPS_STATE_MACHINE §F2 C15
    Append-only cost record for an Expediente.
    Sprint 4: Added visibility field for doble vista.
    """
    cost_line_id = models.UUIDField(primary_key=True, default=uuid.uuid4,
                                    editable=False)
    expediente = models.ForeignKey(Expediente,
                                   on_delete=models.PROTECT,
                                   related_name='cost_lines',
                                   null=True, blank=True)
    # Sprint 5 S5-01: nullable FK for transfer cost lines (XOR with expediente)
    transfer = models.ForeignKey(
        'transfers.Transfer', on_delete=models.PROTECT,
        null=True, blank=True, related_name='cost_lines',
        help_text='XOR with expediente — use one or the other'
    )
    cost_type = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, help_text="ISO 4217")
    phase = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    # Sprint 4 S4-01: Doble vista
    visibility = models.CharField(
        max_length=10,
        choices=CostLineVisibility.choices,
        default=CostLineVisibility.INTERNAL,
        help_text="internal=CEO-only, client=visible to client"
    )

    class Meta:
        verbose_name = 'Cost Line'
        verbose_name_plural = 'Cost Lines'
        ordering = ['-created_at']

    def __str__(self):
        return f"Cost {self.cost_type}: {self.amount} {self.currency}"


class PaymentLine(AppendOnlyModel):
    """
    Ref: ENT_OPS_STATE_MACHINE §L1
    Append-only payment record for an Expediente.
    """
    payment_line_id = models.UUIDField(primary_key=True, default=uuid.uuid4,
                                       editable=False)
    expediente = models.ForeignKey(Expediente,
                                   on_delete=models.PROTECT,
                                   related_name='payment_lines')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, help_text="ISO 4217")
    method = models.CharField(max_length=50,
                              help_text="transferencia, cheque, otro")
    reference = models.CharField(max_length=100,
                                 help_text="Número de comprobante")
    registered_at = models.DateTimeField()
    registered_by_type = models.CharField(max_length=10,
                                          choices=RegisteredByType.choices)
    registered_by_id = models.CharField(max_length=255)

    class Meta:
        verbose_name = 'Payment Line'
        verbose_name_plural = 'Payment Lines'
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment {self.method}: {self.amount} {self.currency}"


# ──────────────────────────────────────────────────
# Sprint 4 S4-07: LogisticsOption (for ART-19)
# ──────────────────────────────────────────────────

class LogisticsOption(TimestampMixin):
    """
    Ref: ENT_PLAT_ARTEFACTOS.F2
    Logistics option for ART-19 Decisión Logística.
    """
    logistics_option_id = models.UUIDField(primary_key=True, default=uuid.uuid4,
                                           editable=False)
    artifact_instance = models.ForeignKey(ArtifactInstance,
                                          on_delete=models.CASCADE,
                                          related_name='logistics_options')
    option_id = models.CharField(max_length=50)
    mode = models.CharField(max_length=20, choices=LogisticsMode.choices)
    carrier = models.CharField(max_length=100)
    route = models.CharField(max_length=200)
    estimated_days = models.IntegerField()
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, help_text="ISO 4217")
    valid_until = models.DateField(null=True, blank=True)
    source = models.CharField(max_length=20, choices=LogisticsSource.choices,
                              default=LogisticsSource.MANUAL)
    is_selected = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Logistics Option'
        verbose_name_plural = 'Logistics Options'
        ordering = ['-created_at']

    def __str__(self):
        return f"Option {self.option_id}: {self.mode} via {self.carrier}"
