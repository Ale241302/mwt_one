"""
Sprint 5 S5-02: Transfer domain services C30-C35
Ref: LOTE_SM_SPRINT5 Item 3B
"""
import uuid
from django.utils import timezone
from django.db import transaction

from apps.transfers.models import Transfer, TransferLine, Node
from apps.transfers.enums import TransferStatus, LegalContext
from apps.expedientes.models import EventLog, ArtifactInstance
from apps.expedientes.enums import ArtifactStatus


def _create_transfer_event(transfer, event_type, emitted_by, payload=None):
    """Create EventLog for transfer domain."""
    return EventLog.objects.create(
        event_type=event_type,
        aggregate_type='transfer',
        aggregate_id=uuid.UUID(int=0),  # placeholder — transfers use char id
        payload={
            'transfer_id': transfer.transfer_id,
            **(payload or {}),
        },
        occurred_at=timezone.now(),
        emitted_by=emitted_by,
        correlation_id=uuid.uuid4(),
    )


def create_transfer(data: dict, user) -> Transfer:
    """
    C30 CreateTransfer — estado inicial: planned.
    Calcula ownership_before/after y customs_required automáticamente.
    """
    from_node = Node.objects.get(pk=data["from_node"])
    to_node = Node.objects.get(pk=data["to_node"])

    with transaction.atomic():
        transfer = Transfer(
            from_node=from_node,
            to_node=to_node,
            legal_context=data["legal_context"],
            pricing_context=data.get("pricing_context"),
            source_expediente_id=data.get("source_expediente"),
        )
        transfer.compute_ownership_fields()
        transfer.full_clean()
        transfer.save()

        for item in data.get("items", []):
            TransferLine.objects.create(
                transfer=transfer,
                sku=item["sku"],
                quantity_dispatched=item["quantity"],
            )

        _create_transfer_event(
            transfer, "transfer.created", "C30:CreateTransfer",
        )
    return transfer


def approve_transfer(transfer: Transfer, user) -> Transfer:
    """C31 — planned → approved. CEO only."""
    if transfer.status != TransferStatus.PLANNED:
        raise ValueError("Transfer must be in planned status to approve.")
        
    # ART-16 rule: if ownership changes, we need pricing approval before approval
    if transfer.ownership_changes and transfer.source_expediente:
        art_16s = ArtifactInstance.objects.filter(
            expediente=transfer.source_expediente, 
            artifact_type="ART-16", 
            status=ArtifactStatus.COMPLETED
        )
        art_16_exists = any(a.payload.get("transfer_id") == transfer.transfer_id for a in art_16s)
        if not art_16_exists:
            raise ValueError("Transfer with ownership_changes=True requires ART-16 (Pricing Approval) before approval (C31).")
            
    with transaction.atomic():
        transfer.status = TransferStatus.APPROVED
        transfer.approved_at = timezone.now()
        transfer.save(update_fields=["status", "approved_at", "updated_at"])
        _create_transfer_event(
            transfer, "transfer.approved", "C31:ApproveTransfer",
        )
    return transfer


def dispatch_transfer(transfer: Transfer, user) -> Transfer:
    """
    C32 — approved → in_transit.
    Regla puente Sprint 5: CEO confirma manualmente (ART-15 no existe aún).
    """
    if transfer.status != TransferStatus.APPROVED:
        raise ValueError("Transfer must be approved to dispatch.")
    with transaction.atomic():
        transfer.status = TransferStatus.IN_TRANSIT
        transfer.dispatched_at = timezone.now()
        transfer.save(update_fields=["status", "dispatched_at", "updated_at"])
        _create_transfer_event(
            transfer, "transfer.dispatched", "C32:DispatchTransfer",
            payload={"bridge_rule": "manual_ceo_confirmation_no_art15"},
        )
    return transfer


def receive_transfer(transfer: Transfer, lines_data: list, user) -> Transfer:
    """
    C33 — in_transit → received.
    lines_data = [{sku, quantity_received, condition}, ...]
    """
    if transfer.status != TransferStatus.IN_TRANSIT:
        raise ValueError("Transfer must be in_transit to receive.")
    with transaction.atomic():
        for line_data in lines_data:
            line = transfer.lines.filter(sku=line_data["sku"]).first()
            if line:
                line.quantity_received = line_data["quantity_received"]
                line.condition = line_data.get("condition")
                line.save(update_fields=["quantity_received", "condition"])

        transfer.status = TransferStatus.RECEIVED
        transfer.received_at = timezone.now()
        transfer.save(update_fields=["status", "received_at", "updated_at"])
        _create_transfer_event(
            transfer, "transfer.received", "C33:ReceiveTransfer",
            payload={"bridge_rule": "manual_ceo_confirmation_no_art13"},
        )
    return transfer


def reconcile_transfer(transfer: Transfer, user, exception_reason: str = None) -> Transfer:
    """
    C34 — received → reconciled.
    Si hay discrepancias: SOLO CEO puede reconciliar + exception_reason obligatorio.
    """
    if transfer.status != TransferStatus.RECEIVED:
        raise ValueError("Transfer must be received to reconcile.")

    lines = transfer.lines.all()
    has_discrepancy = any(line.has_discrepancy for line in lines)

    if has_discrepancy:
        if not user.is_superuser:
            raise PermissionError("Only CEO can reconcile transfers with discrepancies.")
        if not exception_reason:
            raise ValueError("exception_reason is required when there are discrepancies.")
        transfer.exception_reason = exception_reason

    with transaction.atomic():
        transfer.status = TransferStatus.RECONCILED
        transfer.reconciled_at = timezone.now()
        transfer.save(update_fields=[
            "status", "reconciled_at", "exception_reason", "updated_at"
        ])
        _create_transfer_event(
            transfer, "transfer.reconciled", "C34:ReconcileTransfer",
            payload={
                "has_discrepancy": has_discrepancy,
                "exception_reason": exception_reason,
            },
        )
    return transfer


def cancel_transfer(transfer: Transfer, user, reason: str) -> Transfer:
    """C35 — any → cancelled. CEO only. Solo desde planned o approved."""
    if transfer.status not in (TransferStatus.PLANNED, TransferStatus.APPROVED):
        raise ValueError("Transfer can only be cancelled from planned or approved status.")
    with transaction.atomic():
        transfer.status = TransferStatus.CANCELLED
        transfer.cancel_reason = reason
        transfer.cancelled_at = timezone.now()
        transfer.save(update_fields=[
            "status", "cancel_reason", "cancelled_at", "updated_at"
        ])
        _create_transfer_event(
            transfer, "transfer.cancelled", "C35:CancelTransfer",
            payload={"reason": reason},
        )
    return transfer


def create_preparation_artifact(transfer: Transfer, payload: dict, user) -> ArtifactInstance:
    """
    C36 — Create ART-14 (Preparation).
    Pre-condition: status == APPROVED.
    Generates ART-14.
    """
    if transfer.status != TransferStatus.APPROVED:
        raise ValueError("Transfer must be approved to prepare (ART-14).")

    with transaction.atomic():
        artifact = ArtifactInstance.objects.create(
            expediente=transfer.source_expediente,  # Allow NULL if model permits, though it's typically required
            artifact_type="ART-14",
            status=ArtifactStatus.COMPLETED,
            payload={
                "transfer_id": transfer.transfer_id,
                **payload
            }
        )
        _create_transfer_event(
            transfer, "transfer.artifact_created", "C36:CreatePreparation",
            payload={"artifact_type": "ART-14", "artifact_id": str(artifact.artifact_id)}
        )
    return artifact


def create_dispatch_artifact(transfer: Transfer, payload: dict, user) -> ArtifactInstance:
    """
    C37 — Create ART-15 (Dispatch).
    Pre-condition: ART-14 exists for this transfer.
    Changes status to IN_TRANSIT.
    """
    if transfer.status != TransferStatus.APPROVED:
        raise ValueError("Transfer must be approved to dispatch (ART-15).")
        
    # Validation: needs ART-14
    if transfer.source_expediente:
        # Check if ART-14 exists in source_expediente payloads linking to this transfer
        art_14s = ArtifactInstance.objects.filter(
            expediente=transfer.source_expediente, 
            artifact_type="ART-14", 
            status=ArtifactStatus.COMPLETED
        )
        # Verify it's actually for this transfer
        art_14_exists = any(a.payload.get("transfer_id") == transfer.transfer_id for a in art_14s)
        if not art_14_exists:
            raise ValueError("Transfer requires ART-14 (Preparation) before ART-15 (Dispatch).")

    with transaction.atomic():
        artifact = ArtifactInstance.objects.create(
            expediente=transfer.source_expediente,
            artifact_type="ART-15",
            status=ArtifactStatus.COMPLETED,
            payload={
                "transfer_id": transfer.transfer_id,
                **payload
            }
        )
        
        transfer.status = TransferStatus.IN_TRANSIT
        transfer.dispatched_at = timezone.now()
        transfer.save(update_fields=["status", "dispatched_at", "updated_at"])
        
        _create_transfer_event(
            transfer, "transfer.dispatched_art15", "C37:CreateDispatch",
            payload={"artifact_type": "ART-15"}
        )
    return artifact


def create_reception_artifact(transfer: Transfer, lines_data: list, payload: dict, user) -> ArtifactInstance:
    """
    C38 — Create ART-13 (Reception).
    Pre-condition: status == IN_TRANSIT.
    Changes status to RECEIVED. Updates TransferLines.
    """
    if transfer.status != TransferStatus.IN_TRANSIT:
        raise ValueError("Transfer must be in transit to receive (ART-13).")

    with transaction.atomic():
        for line_data in lines_data:
            line = transfer.lines.filter(sku=line_data["sku"]).first()
            if line:
                line.quantity_received = line_data.get("quantity_received", 0)
                line.condition = line_data.get("condition")
                line.save(update_fields=["quantity_received", "condition"])

        artifact = ArtifactInstance.objects.create(
            expediente=transfer.source_expediente,
            artifact_type="ART-13",
            status=ArtifactStatus.COMPLETED,
            payload={
                "transfer_id": transfer.transfer_id,
                "lines_data": lines_data,
                **payload
            }
        )

        transfer.status = TransferStatus.RECEIVED
        transfer.received_at = timezone.now()
        transfer.save(update_fields=["status", "received_at", "updated_at"])
        
        _create_transfer_event(
            transfer, "transfer.received_art13", "C38:CreateReception",
            payload={"artifact_type": "ART-13"}
        )
    return artifact


def create_pricing_approval_artifact(transfer: Transfer, payload: dict, user) -> ArtifactInstance:
    """
    C39 — Create ART-16 (Pricing Approval).
    Pre-condition: ownership_changes == True AND status == PLANNED.
    Generates ART-16. Required before C31.
    """
    if not transfer.ownership_changes:
        raise ValueError("Transfer without ownership changes does not require pricing approval (ART-16).")
    
    if transfer.status != TransferStatus.PLANNED:
        raise ValueError("Pricing approval (ART-16) must be given while transfer is in PLANNED status.")

    with transaction.atomic():
        artifact = ArtifactInstance.objects.create(
            expediente=transfer.source_expediente,
            artifact_type="ART-16",
            status=ArtifactStatus.COMPLETED,
            payload={
                "transfer_id": transfer.transfer_id,
                **payload
            }
        )
        _create_transfer_event(
            transfer, "transfer.artifact_created", "C39:CreatePricingApproval",
            payload={"artifact_type": "ART-16", "artifact_id": str(artifact.artifact_id)}
        )
    return artifact

