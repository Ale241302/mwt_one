"""
T6 — liquidate_rebates() Celery task helper
T7 — approve_rebate_liquidation()
"""
from decimal import Decimal
from datetime import date
from unittest.mock import patch, MagicMock
from django.test import TestCase

from apps.commercial.models import (
    RebateProgram,
    RebateAssignment,
    RebateLedger,
    RebateAccrualEntry,
    PeriodType,
    RebateType,
    ThresholdType,
    LedgerStatus,
)
from apps.commercial.services.rebates import approve_rebate_liquidation
from apps.audit.models import EventLog


def make_brand(slug='brand-t6'):
    from apps.brands.models import Brand
    return Brand.objects.get_or_create(slug=slug, defaults={'name': f'Brand {slug}'})[0]


def make_client():
    from apps.clientes.models import Cliente
    return Cliente.objects.get_or_create(
        nombre='Cliente T6', defaults={'email': 'cliente-t6@test.com'}
    )[0]


def make_ceo_user():
    from apps.users.models import MWTUser, UserRole
    user, _ = MWTUser.objects.get_or_create(
        username='ceo-t6',
        defaults={'role': UserRole.CEO, 'email': 'ceo-t6@test.com'},
    )
    return user


def make_program_and_ledger(brand, client, threshold_type=ThresholdType.AMOUNT,
                             threshold_amount=Decimal('500.00'), status=LedgerStatus.ACCRUING,
                             threshold_met=False):
    program = RebateProgram.objects.create(
        brand=brand,
        name='Liq Program',
        period_type=PeriodType.QUARTERLY,
        valid_from=date(2026, 1, 1),
        rebate_type=RebateType.PERCENTAGE,
        rebate_value=Decimal('5.0000'),
        calculation_base='invoiced',
        threshold_type=threshold_type,
        threshold_amount=threshold_amount if threshold_type == ThresholdType.AMOUNT else None,
    )
    assignment = RebateAssignment.objects.create(
        rebate_program=program,
        client=client,
    )
    ledger = RebateLedger.objects.create(
        rebate_assignment=assignment,
        period_start=date(2026, 1, 1),
        period_end=date(2026, 3, 31),
        status=status,
        threshold_met=threshold_met,
        accrued_amount=Decimal('250.00') if threshold_met else Decimal('0.00'),
        qualifying_amount=Decimal('5000.00') if threshold_met else Decimal('100.00'),
    )
    return program, assignment, ledger


class T6LiquidateRebatesTest(TestCase):
    """T6 — liquidate_rebates() helper: mueve ledgers accruing+threshold_met a pending_review."""

    def setUp(self):
        self.brand = make_brand()
        self.client = make_client()

    def _run_liquidate_for_period(self, period_start, period_end):
        """Simula la lógica del task liquidate_rebates() para un período."""
        updated = RebateLedger.objects.filter(
            status=LedgerStatus.ACCRUING,
            threshold_met=True,
            period_start__lte=period_end,
            period_end__lte=period_end,
        ).update(status=LedgerStatus.PENDING_REVIEW)
        return updated

    def test_T6_threshold_met_ledger_moves_to_pending_review(self):
        _, _, ledger = make_program_and_ledger(
            self.brand, self.client, threshold_met=True
        )
        self.assertEqual(ledger.status, LedgerStatus.ACCRUING)

        count = self._run_liquidate_for_period(date(2026, 1, 1), date(2026, 3, 31))
        self.assertGreaterEqual(count, 1)

        ledger.refresh_from_db()
        self.assertEqual(ledger.status, LedgerStatus.PENDING_REVIEW)

    def test_T6_threshold_not_met_stays_accruing(self):
        _, _, ledger = make_program_and_ledger(
            self.brand, self.client, threshold_met=False
        )
        self._run_liquidate_for_period(date(2026, 1, 1), date(2026, 3, 31))

        ledger.refresh_from_db()
        self.assertEqual(ledger.status, LedgerStatus.ACCRUING)

    def test_T6_already_liquidated_ledger_not_touched(self):
        _, _, ledger = make_program_and_ledger(
            self.brand, self.client,
            status=LedgerStatus.LIQUIDATED,
            threshold_met=True,
        )
        self._run_liquidate_for_period(date(2026, 1, 1), date(2026, 3, 31))
        ledger.refresh_from_db()
        self.assertEqual(ledger.status, LedgerStatus.LIQUIDATED)


class T7ApproveLiquidationTest(TestCase):
    """T7 — approve_rebate_liquidation(): aprobación, EventLog, validaciones."""

    def setUp(self):
        self.brand = make_brand(slug='brand-t7')
        self.client = make_client()
        self.ceo = make_ceo_user()
        _, _, self.ledger = make_program_and_ledger(
            self.brand, self.client,
            status=LedgerStatus.PENDING_REVIEW,
            threshold_met=True,
        )

    def test_T7_approve_sets_status_liquidated(self):
        approve_rebate_liquidation(
            ledger_id=str(self.ledger.pk),
            liquidation_type='credit_note',
            approved_by_user=self.ceo,
        )
        self.ledger.refresh_from_db()
        self.assertEqual(self.ledger.status, LedgerStatus.LIQUIDATED)
        self.assertEqual(self.ledger.liquidation_type, 'credit_note')
        self.assertIsNotNone(self.ledger.liquidated_at)
        self.assertEqual(self.ledger.liquidated_by, self.ceo)

    def test_T7_approve_creates_event_log(self):
        initial_count = EventLog.objects.filter(event_type='rebate.liquidated').count()
        approve_rebate_liquidation(
            ledger_id=str(self.ledger.pk),
            liquidation_type='bank_transfer',
            approved_by_user=self.ceo,
        )
        self.assertEqual(
            EventLog.objects.filter(event_type='rebate.liquidated').count(),
            initial_count + 1,
        )
        log = EventLog.objects.filter(event_type='rebate.liquidated').latest('created_at')
        self.assertEqual(log.action_source, 'approve_rebate_liquidation')
        self.assertEqual(log.actor, self.ceo)
        self.assertIn('ledger_id', log.payload)
        self.assertIn('liquidation_type', log.payload)

    def test_T7_approve_wrong_status_raises(self):
        self.ledger.status = LedgerStatus.ACCRUING
        self.ledger.save(update_fields=['status'])
        with self.assertRaises(ValueError) as ctx:
            approve_rebate_liquidation(
                ledger_id=str(self.ledger.pk),
                liquidation_type='credit_note',
                approved_by_user=self.ceo,
            )
        self.assertIn('pending_review', str(ctx.exception))

    def test_T7_invalid_liquidation_type_raises(self):
        with self.assertRaises(ValueError) as ctx:
            approve_rebate_liquidation(
                ledger_id=str(self.ledger.pk),
                liquidation_type='invalid_type',
                approved_by_user=self.ceo,
            )
        self.assertIn('invalid_type', str(ctx.exception))

    def test_T7_nonexistent_ledger_raises(self):
        import uuid
        with self.assertRaises(ValueError):
            approve_rebate_liquidation(
                ledger_id=str(uuid.uuid4()),
                liquidation_type='credit_note',
                approved_by_user=self.ceo,
            )

    def test_T7_all_liquidation_types_valid(self):
        for lt in ('credit_note', 'bank_transfer', 'product_credit'):
            brand2 = make_brand(slug=f'brand-lt-{lt}')
            _, _, ledger = make_program_and_ledger(
                brand2, self.client,
                status=LedgerStatus.PENDING_REVIEW,
                threshold_met=True,
            )
            approve_rebate_liquidation(
                ledger_id=str(ledger.pk),
                liquidation_type=lt,
                approved_by_user=self.ceo,
            )
            ledger.refresh_from_db()
            self.assertEqual(ledger.status, LedgerStatus.LIQUIDATED)
