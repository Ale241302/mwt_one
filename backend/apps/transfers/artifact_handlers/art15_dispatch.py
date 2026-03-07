import uuid
from django.utils import timezone
from django.db import transaction
from apps.transfers.models import Transfer
from apps.transfers.enums import TransferStatus
from apps.expedientes.models import ArtifactInstance
from apps.expedientes.enums import ArtifactStatus


def create_dispatch_artifact(transfer: Transfer, payload: dict, user) -> ArtifactInstance:
    """
    C37 â€” Create ART-15 (Dispatch).
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
        
        from apps.transfers.services import _create_transfer_event
        _create_transfer_event(
            transfer, "transfer.dispatched_art15", "C37:CreateDispatch",
            payload={"artifact_type": "ART-15"}
        )
    return artifact
