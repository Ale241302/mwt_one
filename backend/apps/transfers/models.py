"""
Sprint 5 S5-01: Transfer model + state machine
Node (stub), Transfer (6-state machine), TransferLine
Ref: LOTE_SM_SPRINT5 Item 3
"""
import uuid
from datetime import date
from django.db import models
from django.core.exceptions import ValidationError
from apps.transfers.enums_exp import (
    NodeType, NodeStatus, LegalContext, TransferStatus, TransferLineCondition
)
from apps.core.models import LegalEntity, UUIDReferenceField
from datetime import date

def generate_transfer_id():
    today = date.today().strftime('%Y%m%d')
    count = Transfer.objects.filter(transfer_id__startswith=f'TRF-{today}').count()
    return f'TRF-{today}-{str(count + 1).zfill(3)}'

class Transfer(models.Model):
    transfer_id = models.CharField(
        max_length=30, unique=True, editable=False, default=generate_transfer_id
    )
    from_node_id = UUIDReferenceField(target_module='nodos')
    to_node_id = UUIDReferenceField(target_module='nodos')
    ownership_before_id = UUIDReferenceField(target_module='clientes', null=True, blank=True)
    ownership_after_id = UUIDReferenceField(target_module='clientes', null=True, blank=True)
    ownership_changes = models.BooleanField(default=False)
    legal_context = models.CharField(max_length=30, choices=LegalContext.choices)
    customs_required = models.BooleanField(default=False)
    pricing_context = models.JSONField(null=True, blank=True)
    source_expediente_id = UUIDReferenceField(
        target_module='expedientes',
        null=True, blank=True,
        help_text='Expediente de origen'
    )
    status = models.CharField(
        max_length=20, choices=TransferStatus.choices, default=TransferStatus.PLANNED
    )
    cancel_reason = models.TextField(blank=True)
    exception_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    dispatched_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)
    reconciled_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    @property
    def source_expediente(self):
        return self.resolve_ref('source_expediente_id')

    @property
    def ownership_before(self):
        return self.resolve_ref('ownership_before_id')

    @property
    def ownership_after(self):
        return self.resolve_ref('ownership_after_id')

    @property
    def from_node(self):
        # Nota: Transfer no hereda de BaseModel, así que usamos el registro manual o helper
        from apps.core.registry import ModuleRegistry
        service = ModuleRegistry.get_service_class('nodos')
        return service.get_entity(self.from_node_id) if service else None

    @property
    def to_node(self):
        from apps.core.registry import ModuleRegistry
        service = ModuleRegistry.get_service_class('nodos')
        return service.get_entity(self.to_node_id) if service else None

    def clean(self):
        if self.from_node_id == self.to_node_id:
            raise ValidationError('from_node and to_node must be different.')

    class Meta:
        db_table = 'transfers_transfer'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.transfer_id} [{self.status}]'

    def compute_ownership_fields(self):
        f_node = self.from_node
        t_node = self.to_node
        if f_node:
            # Asumimos que f_node.legal_entity_id es el UUID de la entidad legal
            self.ownership_before_id = f_node.legal_entity_id
        if t_node:
            self.ownership_after_id = t_node.legal_entity_id
        
        self.ownership_changes = (self.ownership_before_id != self.ownership_after_id)
        self.customs_required = self.legal_context in (
            LegalContext.NATIONALIZATION, LegalContext.REEXPORT
        )


class TransferLine(models.Model):
    transfer = models.ForeignKey(
        Transfer, on_delete=models.CASCADE, related_name='lines'
    )
    sku = models.CharField(max_length=200)
    quantity_dispatched = models.PositiveIntegerField()
    quantity_received = models.PositiveIntegerField(null=True, blank=True)
    condition = models.CharField(
        max_length=20, choices=TransferLineCondition.choices,
        null=True, blank=True,
    )

    @property
    def discrepancy(self):
        if self.quantity_received is None:
            return None
        return self.quantity_dispatched - self.quantity_received

    @property
    def has_discrepancy(self):
        d = self.discrepancy
        return d is not None and d != 0

    class Meta:
        db_table = 'transfers_transferline'
