import uuid
from django.utils import timezone
from django.db import transaction
from apps.transfers.models import Transfer
from apps.transfers.enums import TransferStatus
from apps.expedientes.models import ArtifactInstance
from apps.expedientes.enums import ArtifactStatus
from apps.transfers.services import _create_transfer_event

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
