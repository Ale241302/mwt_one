"""
S10-04b — C22 IssueCommissionInvoice handler.
Persists ART-19 artifact and emits CommissionInvoiceIssued event.
"""
from django.db import transaction
from expedientes.domain.commands.c22_issue_commission_invoice import (
    IssueCommissionInvoice,
    CommissionInvoiceIssued,
)
from expedientes.models import Expediente, Artifact, DomainEvent
import uuid
from datetime import datetime, UTC


class IssueCommissionInvoiceHandler:
    def handle(self, cmd: IssueCommissionInvoice) -> CommissionInvoiceIssued:
        with transaction.atomic():
            exp = Expediente.objects.select_for_update().get(pk=cmd.expediente_id)

            # Guard: must not be cancelled or closed
            if exp.status in ("CANCELADO", "CERRADO"):
                raise ValueError(
                    f"Cannot issue commission invoice on expediente in status {exp.status}."
                )

            # Guard: no duplicate active commission invoice
            existing = Artifact.objects.filter(
                expediente=exp,
                artifact_type="ART-19",
                status="completed",
            ).exists()
            if existing:
                raise ValueError("A commission invoice (ART-19) already exists for this expediente.")

            # Create artifact
            artifact = Artifact.objects.create(
                artifact_id=str(uuid.uuid4()),
                expediente=exp,
                artifact_type="ART-19",
                status="completed",
                payload={
                    "invoice_number": cmd.invoice_number,
                    "commission_amount": cmd.commission_amount,
                    "commission_pct": cmd.commission_pct,
                    "notes": cmd.notes,
                },
                created_at=cmd.issued_at,
            )

            # Emit domain event
            event = CommissionInvoiceIssued(
                expediente_id=str(exp.pk),
                invoice_number=cmd.invoice_number,
                commission_amount=cmd.commission_amount,
                commission_pct=cmd.commission_pct,
                notes=cmd.notes,
                occurred_at=cmd.issued_at,
            )
            DomainEvent.objects.create(
                event_type="CommissionInvoiceIssued",
                expediente=exp,
                payload={
                    "event_id": event.event_id,
                    "invoice_number": event.invoice_number,
                    "commission_amount": event.commission_amount,
                    "commission_pct": event.commission_pct,
                    "notes": event.notes,
                },
                occurred_at=datetime.now(UTC),
                emitted_by="system",
            )

        return event
