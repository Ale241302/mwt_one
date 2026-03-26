"""
S10-04b — Tests for C22 IssueCommissionInvoice.
"""
import pytest
from django.test import TestCase
from expedientes.models import Expediente, Artifact, DomainEvent
from expedientes.domain.commands.c22_issue_commission_invoice import IssueCommissionInvoice
from expedientes.application.handlers.c22_handler import IssueCommissionInvoiceHandler
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


def make_expediente(status="EN_PROCESO"):
    return Expediente.objects.create(
        expediente_id=str(uuid.uuid4()),
        status=status,
        payment_status="PENDIENTE",
        is_blocked=False,
    )


class IssueCommissionInvoiceHandlerTest(TestCase):
    def test_creates_art19_artifact(self):
        exp = make_expediente()
        cmd = IssueCommissionInvoice(
            expediente_id=str(exp.pk),
            invoice_number="CINV-001",
            commission_amount=500.00,
            commission_pct=5.0,
        )
        handler = IssueCommissionInvoiceHandler()
        event = handler.handle(cmd)

        art = Artifact.objects.get(expediente=exp, artifact_type="ART-19")
        assert art.status == "completed"
        assert art.payload["invoice_number"] == "CINV-001"
        assert art.payload["commission_amount"] == 500.00
        assert event.invoice_number == "CINV-001"

    def test_emits_domain_event(self):
        exp = make_expediente()
        cmd = IssueCommissionInvoice(
            expediente_id=str(exp.pk),
            invoice_number="CINV-002",
            commission_amount=250.0,
        )
        IssueCommissionInvoiceHandler().handle(cmd)
        ev = DomainEvent.objects.filter(expediente=exp, event_type="CommissionInvoiceIssued").first()
        assert ev is not None
        assert ev.payload["invoice_number"] == "CINV-002"

    def test_raises_on_duplicate(self):
        exp = make_expediente()
        cmd = IssueCommissionInvoice(
            expediente_id=str(exp.pk),
            invoice_number="CINV-003",
            commission_amount=100.0,
        )
        handler = IssueCommissionInvoiceHandler()
        handler.handle(cmd)
        with pytest.raises(ValueError, match="already exists"):
            handler.handle(cmd)

    def test_raises_on_cancelled_expediente(self):
        exp = make_expediente(status="CANCELADO")
        cmd = IssueCommissionInvoice(
            expediente_id=str(exp.pk),
            invoice_number="CINV-004",
            commission_amount=100.0,
        )
        with pytest.raises(ValueError, match="CANCELADO"):
            IssueCommissionInvoiceHandler().handle(cmd)

    def test_raises_on_closed_expediente(self):
        exp = make_expediente(status="CERRADO")
        cmd = IssueCommissionInvoice(
            expediente_id=str(exp.pk),
            invoice_number="CINV-005",
            commission_amount=100.0,
        )
        with pytest.raises(ValueError, match="CERRADO"):
            IssueCommissionInvoiceHandler().handle(cmd)
