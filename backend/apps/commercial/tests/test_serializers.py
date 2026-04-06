from decimal import Decimal
from datetime import date
from django.test import TestCase
from apps.commercial.models import RebateProgram, RebateAssignment, RebateLedger
from apps.commercial.serializers import (
    RebateProgressPortalSerializer,
    RebateLedgerInternalSerializer,
    RebateProgramInternalSerializer,
)
from apps.brands.models import Brand
from apps.clients.models import Client, Subsidiary


class TestSerializersT12(TestCase):
    """T12: Serializer field-level security"""

    PORTAL_ALLOWED = {
        "program_name", "period", "threshold_type", "progress_percentage", "threshold_met"
    }
    PORTAL_FORBIDDEN = {
        "rebate_value", "accrued_amount", "threshold_amount", "threshold_units"
    }

    def setUp(self):
        self.brand = Brand.objects.create(name="BrandSer")
        self.client = Client.objects.create(name="ClientSer", brand=self.brand)
        self.program = RebateProgram.objects.create(
            brand=self.brand,
            name="Ser Program",
            period_type="quarterly",
            valid_from=date(2026, 1, 1),
            valid_to=date(2026, 3, 31),
            rebate_type="percentage",
            rebate_value=Decimal("5.00"),
            threshold_type="none",
            calculation_base="invoiced",
        )
        self.assignment = RebateAssignment.objects.create(
            rebate_program=self.program, client=self.client
        )
        self.ledger = RebateLedger.objects.create(
            rebate_assignment=self.assignment,
            period_start=date(2026, 1, 1),
            period_end=date(2026, 3, 31),
            status="accruing",
            accrued_amount=Decimal("250.00"),
            qualifying_amount=Decimal("5000.00"),
        )

    def test_t12a_portal_serializer_excludes_forbidden_fields(self):
        serializer = RebateProgressPortalSerializer(self.ledger)
        data = serializer.data
        for field in self.PORTAL_FORBIDDEN:
            self.assertNotIn(field, data, f"Field '{field}' must NOT appear in portal serializer")

    def test_t12b_portal_serializer_has_exactly_allowed_fields(self):
        serializer = RebateProgressPortalSerializer(self.ledger)
        self.assertEqual(set(serializer.data.keys()), self.PORTAL_ALLOWED)

    def test_t12c_internal_ledger_serializer_includes_accrued_amount(self):
        serializer = RebateLedgerInternalSerializer(self.ledger)
        self.assertIn("accrued_amount", serializer.data)

    def test_t12d_internal_program_serializer_includes_sensitive_fields(self):
        serializer = RebateProgramInternalSerializer(self.program)
        for field in ["rebate_value", "calculation_base", "threshold_amount"]:
            self.assertIn(field, serializer.data, f"Internal serializer must include '{field}'")
