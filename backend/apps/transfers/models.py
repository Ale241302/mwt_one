"""
Sprint 5 S5-01: Transfer model + state machine
Node (stub), Transfer (6-state machine), TransferLine
Ref: LOTE_SM_SPRINT5 Item 3
"""
import uuid
from datetime import date
from django.db import models
from django.core.exceptions import ValidationError
from apps.transfers.enums import (
    NodeType, NodeStatus, LegalContext, TransferStatus, TransferLineCondition
)
from apps.expedientes.models import LegalEntity, Expediente


def generate_transfer_id():
    """Auto-genera TRF-YYYYMMDD-XXX"""
    today = date.today().strftime("%Y%m%d")
    count = Transfer.objects.filter(transfer_id__startswith=f"TRF-{today}").count()
    return f"TRF-{today}-{str(count + 1).zfill(3)}"


class Node(models.Model):
    """
    STUB mínimo. Detalles completos en ENT_OPS_NODOS (Sprint 6+).
    Nodo físico o fiscal donde reside inventario.
    """
    node_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    legal_entity = models.ForeignKey(
        LegalEntity, on_delete=models.PROTECT, related_name="nodes"
    )
    node_type = models.CharField(max_length=30, choices=NodeType.choices)
    location = models.CharField(max_length=500, blank=True)
    status = models.CharField(
        max_length=20, choices=NodeStatus.choices, default=NodeStatus.ACTIVE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "transfers_node"
        verbose_name = "Node"

    def __str__(self):
        return f"{self.name} ({self.node_type})"


class Transfer(models.Model):
    """
    Entidad estructural con state machine propia (6 estados).
    NO es ArtifactInstance. Cimiento para Sprint 6 Rana Walk.

    State machine:
      planned → approved → in_transit → received → reconciled
      any → cancelled (CEO only, desde planned o approved)
    """
    transfer_id = models.CharField(
        max_length=30, unique=True, editable=False, default=generate_transfer_id
    )
    from_node = models.ForeignKey(
        Node, on_delete=models.PROTECT, related_name="transfers_from"
    )
    to_node = models.ForeignKey(
        Node, on_delete=models.PROTECT, related_name="transfers_to"
    )
    ownership_before = models.ForeignKey(
        LegalEntity, on_delete=models.PROTECT,
        related_name="transfers_ownership_before",
        null=True, blank=True,
    )
    ownership_after = models.ForeignKey(
        LegalEntity, on_delete=models.PROTECT,
        related_name="transfers_ownership_after",
        null=True, blank=True,
    )
    ownership_changes = models.BooleanField(default=False)
    legal_context = models.CharField(max_length=30, choices=LegalContext.choices)
    customs_required = models.BooleanField(default=False)
    pricing_context = models.JSONField(null=True, blank=True)
    source_expediente = models.ForeignKey(
        Expediente, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="transfers"
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

    def clean(self):
        if self.from_node_id == self.to_node_id:
            raise ValidationError("from_node and to_node must be different.")

    class Meta:
        db_table = "transfers_transfer"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.transfer_id} [{self.status}]"

    def compute_ownership_fields(self):
        """
        Calcula ownership_before/after desde Node.legal_entity.
        customs_required = True si legal_context in {nationalization, reexport}.
        """
        self.ownership_before = self.from_node.legal_entity
        self.ownership_after = self.to_node.legal_entity
        self.ownership_changes = (self.ownership_before_id != self.ownership_after_id)
        self.customs_required = self.legal_context in (
            LegalContext.NATIONALIZATION, LegalContext.REEXPORT
        )


class TransferLine(models.Model):
    """
    Línea de producto dentro de un Transfer.
    discrepancy = quantity_dispatched - quantity_received (computed).
    """
    transfer = models.ForeignKey(
        Transfer, on_delete=models.CASCADE, related_name="lines"
    )
    sku = models.CharField(max_length=200)
    quantity_dispatched = models.PositiveIntegerField()
    quantity_received = models.PositiveIntegerField(null=True, blank=True)
    condition = models.CharField(
        max_length=20, choices=TransferLineCondition.choices, null=True, blank=True
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
        db_table = "transfers_transferline"
