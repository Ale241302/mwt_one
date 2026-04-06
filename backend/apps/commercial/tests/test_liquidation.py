from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.commercial.models import (
    RebateProgram, RebateAssignment, RebateLedger
)
from apps.commercial.tasks import liquidate_rebates
from apps.commercial.services.rebates import approve_rebate_liquidation
from apps.eventlog.models import EventLog
from apps.brands.models import Brand
from apps.clients.models import Client, Subsidiary

User = get_user_model()


class TestLiquidationT6(TestCase):
    """T6: liquidate_rebates() task — threshold-gated move to pending_review"""

    def setUp(self):
        self.brand = Brand.objects.create(name="BrandLiq")
        self.client = Client.objects.create(name="ClientLiq", brand=self.brand)
        self.program = RebateProgram.objects.create(
            brand=self.brand,
            name="Liq Program",
            period_type="quarterly",
            valid_from=date(2026, 1, 1),
            valid_to=date(2026, 3, 31),
            rebate_type="percentage",
            rebate_value=Decimal("5.00"),
            threshold_type="amount",
            threshold_amount=Decimal("3000.00"),
            calculation_base="invoiced",
        )
        self.assignment = RebateAssignment.objects.create(
            rebate_program=self.program, client=self.client
        )

    def test_t6_threshold_met_moves_to_pending_review(self):
        ledger = RebateLedger.objects.create(
            rebate_assignment=self.assignment,
            period_start=date(2026, 1, 1),
            period_end=date(2026, 3, 31),
            status="accruing",
            accrued_amount=Decimal("200.00"),
            qualifying_amount=Decimal("4000.00"),  # > threshold
        )
        liquidate_rebates()
        ledger.refresh_from_db()
        self.assertEqual(ledger.status, "pending_review")

    def test_t6_threshold_not_met_stays_accruing(self):
        ledger = RebateLedger.objects.create(
            rebate_assignment=self.assignment,
            period_start=date(2026, 1, 1),
            period_end=date(2026, 3, 31),
            status="accruing",
            accrued_amount=Decimal("50.00"),
            qualifying_amount=Decimal("1000.00"),  # < threshold
        )
        liquidate_rebates()
        ledger.refresh_from_db()
        self.assertEqual(ledger.status, "accruing")


class TestLiquidationT7(TestCase):
    """T7: approve_rebate_liquidation()"""

    def setUp(self):
        self.brand = Brand.objects.create(name="BrandApprove")
        self.client = Client.objects.create(name="ClientApprove", brand=self.brand)
        self.ceo = User.objects.create_user(username="ceo", password="pass", role="CEO")
        self.program = RebateProgram.objects.create(
            brand=self.brand,
            name="Approve Program",
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
            status="pending_review",
            accrued_amount=Decimal("500.00"),
            qualifying_amount=Decimal("10000.00"),
        )

    def test_t7_approval_sets_liquidated(self):
        result = approve_rebate_liquidation(
            ledger=self.ledger,
            approved_by=self.ceo,
            liquidation_type="credit_note",
        )
        self.ledger.refresh_from_db()
        self.assertEqual(self.ledger.status, "liquidated")
        self.assertIsNotNone(self.ledger.liquidated_at)
        self.assertEqual(self.ledger.liquidated_by, self.ceo)

    def test_t7_approval_creates_event_log(self):
        approve_rebate_liquidation(
            ledger=self.ledger,
            approved_by=self.ceo,
            liquidation_type="credit_note",
        )
        log = EventLog.objects.filter(event_type="rebate.liquidated").first()
        self.assertIsNotNone(log)

    def test_t7_wrong_status_raises_value_error(self):
        self.ledger.status = "accruing"
        self.ledger.save()
        with self.assertRaises(ValueError):
            approve_rebate_liquidation(
                ledger=self.ledger,
                approved_by=self.ceo,
                liquidation_type="credit_note",
            )

    def test_t7_invalid_liquidation_type_raises_value_error(self):
        with self.assertRaises(ValueError):
            approve_rebate_liquidation(
                ledger=self.ledger,
                approved_by=self.ceo,
                liquidation_type="invalid_type",
            )
