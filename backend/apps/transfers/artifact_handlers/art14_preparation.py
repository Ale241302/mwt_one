import uuid
from django.utils import timezone
from django.db import transaction
from apps.transfers.models import Transfer
from apps.transfers.enums import TransferStatus
from apps.expedientes.models import ArtifactInstance
from apps.expedientes.enums import ArtifactStatus
from apps.transfers.services import _create_transfer_event

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
