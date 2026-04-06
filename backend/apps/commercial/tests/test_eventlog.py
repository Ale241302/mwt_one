from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.commercial.models import RebateProgram, RebateAssignment, RebateLedger, BrandArtifactPolicyVersion
from apps.commercial.services.rebates import approve_rebate_liquidation
from apps.commercial.services.artifact_policy import update_artifact_policy
from apps.eventlog.models import EventLog
from apps.changelog.models import ConfigChangeLog
from apps.brands.models import Brand
from apps.clients.models import Client

User = get_user_model()


class TestEventLogT14(TestCase):
    """T14: EventLog and ConfigChangeLog emission correctness"""

    def setUp(self):
        self.brand = Brand.objects.create(name="BrandEL")
        self.client = Client.objects.create(name="ClientEL", brand=self.brand)
        self.ceo = User.objects.create_user(username="ceo_el", password="pass", role="CEO")
        self.program = RebateProgram.objects.create(
            brand=self.brand,
            name="EL Program",
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

    def test_t14a_approve_creates_event_log_with_correct_payload(self):
        approve_rebate_liquidation(
            ledger=self.ledger,
            approved_by=self.ceo,
            liquidation_type="credit_note",
        )
        log = EventLog.objects.filter(event_type="rebate.liquidated").first()
        self.assertIsNotNone(log)
        self.assertIn("ledger_id", log.payload)
        self.assertIn("liquidation_type", log.payload)

    def test_t14b_update_artifact_policy_creates_config_change_log_not_event_log(self):
        BrandArtifactPolicyVersion.objects.create(
            brand=self.brand, version=1,
            artifact_policy={"rule": "old"},
            is_active=True,
        )
        initial_event_count = EventLog.objects.count()
        update_artifact_policy(
            brand=self.brand,
            new_policy={"rule": "new"},
            changed_by_description="test update",
        )
        # EventLog count must NOT increase
        self.assertEqual(EventLog.objects.count(), initial_event_count)
        # ConfigChangeLog must be created
        log = ConfigChangeLog.objects.filter(action="update_artifact_policy").first()
        self.assertIsNotNone(log)

    def test_t14c_integrity_error_creates_config_change_log(self):
        from apps.commercial.services.artifact_policy import _emit_integrity_error
        _emit_integrity_error(brand=self.brand)
        log = EventLog.objects.filter(event_type="artifact_policy.integrity_error").first()
        self.assertIsNotNone(log)

    def test_t14d_event_log_has_correct_action_source(self):
        approve_rebate_liquidation(
            ledger=self.ledger,
            approved_by=self.ceo,
            liquidation_type="credit_note",
        )
        log = EventLog.objects.filter(event_type="rebate.liquidated").first()
        self.assertEqual(log.action_source, "approve_rebate_liquidation")
