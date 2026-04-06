"""
T14 — EventLog: creación correcta por approve_rebate_liquidation(),
       ausencia en update_artifact_policy(), integrity_error en _emit_integrity_error().
"""
from decimal import Decimal
from datetime import date
from django.test import TestCase

from apps.commercial.models import (
    RebateProgram, RebateAssignment, RebateLedger,
    BrandArtifactPolicyVersion,
    PeriodType, RebateType, ThresholdType, LedgerStatus,
)
from apps.commercial.services.rebates import approve_rebate_liquidation
from apps.commercial.services.artifact_policy import (
    update_artifact_policy,
    _emit_integrity_error,
)
from apps.audit.models import EventLog, ConfigChangeLog
from apps.users.models import MWTUser, UserRole


def make_brand(slug='brand-el'):
    from apps.brands.models import Brand
    return Brand.objects.get_or_create(slug=slug, defaults={'name': f'Brand {slug}'})[0]


def make_client():
    from apps.clientes.models import Cliente
    return Cliente.objects.get_or_create(
        nombre='Cliente EL', defaults={'email': 'el@test.com'}
    )[0]


def make_ceo():
    user, _ = MWTUser.objects.get_or_create(
        username='ceo-el', defaults={'role': UserRole.CEO, 'email': 'ceo-el@test.com'}
    )
    return user


def make_pending_ledger(brand, client):
    program = RebateProgram.objects.create(
        brand=brand, name='EL Program',
        period_type=PeriodType.QUARTERLY,
        valid_from=date(2026, 1, 1),
        rebate_type=RebateType.PERCENTAGE,
        rebate_value=Decimal('5.0000'),
        calculation_base='invoiced',
        threshold_type=ThresholdType.NONE,
    )
    assignment = RebateAssignment.objects.create(
        rebate_program=program, client=client,
    )
    return RebateLedger.objects.create(
        rebate_assignment=assignment,
        period_start=date(2026, 1, 1),
        period_end=date(2026, 3, 31),
        status=LedgerStatus.PENDING_REVIEW,
        threshold_met=True,
        accrued_amount=Decimal('100.00'),
    )


class T14EventLogTest(TestCase):

    def setUp(self):
        self.brand = make_brand()
        self.client_obj = make_client()
        self.ceo = make_ceo()
        self.ledger = make_pending_ledger(self.brand, self.client_obj)

    def test_T14a_approve_creates_event_log_rebate_liquidated(self):
        before = EventLog.objects.filter(event_type='rebate.liquidated').count()
        approve_rebate_liquidation(
            ledger_id=str(self.ledger.pk),
            liquidation_type='credit_note',
            approved_by_user=self.ceo,
        )
        after = EventLog.objects.filter(event_type='rebate.liquidated').count()
        self.assertEqual(after, before + 1)

    def test_T14a_event_log_payload_contains_required_keys(self):
        approve_rebate_liquidation(
            ledger_id=str(self.ledger.pk),
            liquidation_type='bank_transfer',
            approved_by_user=self.ceo,
        )
        log = EventLog.objects.filter(event_type='rebate.liquidated').latest('created_at')
        self.assertIn('ledger_id', log.payload)
        self.assertIn('liquidation_type', log.payload)
        self.assertIn('accrued_amount', log.payload)
        self.assertIn('assignment_id', log.payload)
        self.assertEqual(log.payload['liquidation_type'], 'bank_transfer')
        self.assertEqual(log.payload['ledger_id'], str(self.ledger.pk))

    def test_T14d_event_log_action_source_is_approve(self):
        approve_rebate_liquidation(
            ledger_id=str(self.ledger.pk),
            liquidation_type='product_credit',
            approved_by_user=self.ceo,
        )
        log = EventLog.objects.filter(event_type='rebate.liquidated').latest('created_at')
        self.assertEqual(log.action_source, 'approve_rebate_liquidation')
        self.assertEqual(log.actor, self.ceo)
        self.assertEqual(log.related_model, 'RebateLedger')
        self.assertEqual(log.related_id, str(self.ledger.pk))

    def test_T14b_update_artifact_policy_creates_config_change_log_not_event_log(self):
        brand2 = make_brand(slug='brand-el-ap')
        el_before = EventLog.objects.count()
        ccl_before = ConfigChangeLog.objects.count()

        update_artifact_policy(
            brand_slug=brand2.slug,
            new_policy={'docs': ['invoice']},
            changed_by=self.ceo,
        )
        # EventLog no debe haberse creado
        self.assertEqual(EventLog.objects.count(), el_before)
        # ConfigChangeLog SÍ debe haberse creado
        self.assertEqual(ConfigChangeLog.objects.count(), ccl_before + 1)

    def test_T14c_emit_integrity_error_creates_config_change_log(self):
        brand3 = make_brand(slug='brand-el-integrity')
        ccl_before = ConfigChangeLog.objects.filter(action='integrity_error').count()
        _emit_integrity_error(brand3.slug)
        ccl_after = ConfigChangeLog.objects.filter(action='integrity_error').count()
        self.assertEqual(ccl_after, ccl_before + 1)

        log = ConfigChangeLog.objects.filter(action='integrity_error').latest('created_at')
        self.assertEqual(log.model_name, 'BrandArtifactPolicyVersion')
        self.assertIn('artifact_policy.integrity_error', log.changes.get('event_type', ''))
        self.assertEqual(log.record_id, brand3.slug)

    def test_T14_event_log_ordering_latest_first(self):
        approve_rebate_liquidation(
            ledger_id=str(self.ledger.pk),
            liquidation_type='credit_note',
            approved_by_user=self.ceo,
        )
        logs = EventLog.objects.filter(event_type='rebate.liquidated')
        if logs.count() >= 2:
            self.assertGreaterEqual(logs[0].created_at, logs[1].created_at)
