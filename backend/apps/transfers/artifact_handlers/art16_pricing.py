import uuid
from django.utils import timezone
from django.db import transaction
from apps.transfers.models import Transfer
from apps.transfers.enums_exp import TransferStatus
from apps.expedientes.models import ArtifactInstance
from apps.expedientes.enums_artifacts import ArtifactStatusEnum


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
            status=ArtifactStatusEnum.COMPLETED,
            payload={
                "transfer_id": transfer.transfer_id,
                **payload
            }
        )
        from apps.transfers.services import _create_transfer_event
        _create_transfer_event(
            transfer, "transfer.artifact_created", "C39:CreatePricingApproval",
            payload={"artifact_type": "ART-16", "artifact_id": str(artifact.artifact_id)}
        )
    return artifact
