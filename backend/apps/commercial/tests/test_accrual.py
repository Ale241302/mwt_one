"""
T5 — calculate_rebate_accrual(): lógica, idempotencia, ValueError y concurrencia.
"""
from decimal import Decimal
from datetime import date
from django.db import IntegrityError
from django.test import TestCase, TransactionTestCase
import threading

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
from apps.commercial.services.rebates import calculate_rebate_accrual


def make_brand(slug='brand-t5'):
    from apps.brands.models import Brand
    return Brand.objects.get_or_create(slug=slug, defaults={'name': f'Brand {slug}'})[0]


def make_client():
    from apps.clientes.models import Cliente
    return Cliente.objects.get_or_create(
        nombre='Cliente T5', defaults={'email': 'cliente-t5@test.com'}
    )[0]


def make_program(brand, calculation_base='invoiced', threshold_type=ThresholdType.AMOUNT,
                 threshold_amount=Decimal('500.00'), rebate_type=RebateType.PERCENTAGE,
                 rebate_value=Decimal('10.0000')):
    return RebateProgram.objects.create(
        brand=brand,
        name='Accrual Program',
        period_type=PeriodType.QUARTERLY,
        valid_from=date(2026, 1, 1),
        rebate_type=rebate_type,
        rebate_value=rebate_value,
        calculation_base=calculation_base,
        threshold_type=threshold_type,
        threshold_amount=threshold_amount if threshold_type == ThresholdType.AMOUNT else None,
        threshold_units=100 if threshold_type == ThresholdType.UNITS else None,
    )


def make_ledger(assignment, status=LedgerStatus.ACCRUING):
    return RebateLedger.objects.create(
        rebate_assignment=assignment,
        period_start=date(2026, 1, 1),
        period_end=date(2026, 3, 31),
        status=status,
    )


SAMPLE_LINES = [
    {'product_key': 'SKU-001', 'quantity': 10, 'unit_price': Decimal('100.00'), 'base_list_price': Decimal('120.00')},
    {'product_key': 'SKU-002', 'quantity': 5,  'unit_price': Decimal('200.00'), 'base_list_price': Decimal('240.00')},
]


class T5AccrualTest(TestCase):

    def setUp(self):
        self.brand = make_brand()
        self.client = make_client()
        self.program = make_program(self.brand, calculation_base='invoiced')
        self.assignment = RebateAssignment.objects.create(
            rebate_program=self.program,
            client=self.client,
        )
        self.ledger = make_ledger(self.assignment)

    def test_T5a_accrual_invoiced(self):
        """
        qualifying_amount = 10*100 + 5*200 = 2000.00
        accrued_amount = 2000 * 10% = 200.0000
        threshold 500 → met
        """
        result = calculate_rebate_accrual(
            ledger_id=str(self.ledger.pk),
            proforma_id='PF-001',
            proforma_lines=SAMPLE_LINES,
            proforma_date=date(2026, 1, 15),
        )
        self.assertEqual(result.qualifying_amount, Decimal('2000.00'))
        self.assertEqual(result.accrued_amount, Decimal('200.0000'))
        self.assertEqual(result.qualifying_units, 15)
        self.assertTrue(result.threshold_met)
        self.assertFalse(result.was_idempotent)

        self.ledger.refresh_from_db()
        self.assertEqual(self.ledger.qualifying_amount, Decimal('2000.00'))
        self.assertEqual(self.ledger.accrued_amount, Decimal('200.0000'))
        self.assertTrue(self.ledger.threshold_met)

    def test_T5b_accrual_list_price(self):
        """
        qualifying_amount = 10*120 + 5*240 = 2400.00
        accrued_amount = 2400 * 10% = 240.0000
        """
        self.program.calculation_base = 'list_price'
        self.program.save()

        result = calculate_rebate_accrual(
            ledger_id=str(self.ledger.pk),
            proforma_id='PF-002',
            proforma_lines=SAMPLE_LINES,
            proforma_date=date(2026, 1, 15),
        )
        self.assertEqual(result.qualifying_amount, Decimal('2400.00'))
        self.assertEqual(result.accrued_amount, Decimal('240.0000'))

    def test_T5c_idempotence_same_proforma_returns_existing(self):
        calculate_rebate_accrual(
            ledger_id=str(self.ledger.pk),
            proforma_id='PF-IDEM',
            proforma_lines=SAMPLE_LINES,
            proforma_date=date(2026, 1, 15),
        )
        result2 = calculate_rebate_accrual(
            ledger_id=str(self.ledger.pk),
            proforma_id='PF-IDEM',
            proforma_lines=SAMPLE_LINES,
            proforma_date=date(2026, 1, 15),
        )
        self.assertTrue(result2.was_idempotent)
        # Ledger debe tener solo 1 entry
        self.assertEqual(
            RebateAccrualEntry.objects.filter(ledger=self.ledger).count(), 1
        )

    def test_T5d_calculation_base_none_raises_value_error(self):
        self.program.calculation_base = None
        self.program.save(update_fields=['calculation_base'])

        with self.assertRaises(ValueError) as ctx:
            calculate_rebate_accrual(
                ledger_id=str(self.ledger.pk),
                proforma_id='PF-ERR',
                proforma_lines=SAMPLE_LINES,
                proforma_date=date(2026, 1, 15),
            )
        self.assertIn('DEC-S23-01', str(ctx.exception))

    def test_T5e_ledger_not_accruing_raises_value_error(self):
        ledger_pr = make_ledger(self.assignment, status=LedgerStatus.PENDING_REVIEW)
        ledger_pr.pk = None
        ledger_pr.status = LedgerStatus.PENDING_REVIEW
        ledger_pr.period_start = date(2026, 4, 1)
        ledger_pr.period_end = date(2026, 6, 30)
        ledger_pr.save()

        with self.assertRaises(ValueError) as ctx:
            calculate_rebate_accrual(
                ledger_id=str(ledger_pr.pk),
                proforma_id='PF-STATUS',
                proforma_lines=SAMPLE_LINES,
                proforma_date=date(2026, 4, 10),
            )
        self.assertIn('accruing', str(ctx.exception))

    def test_T5_threshold_not_met_when_below(self):
        """
        qualifying_amount = 100.00 (below 500 threshold) → threshold_met=False
        """
        small_lines = [
            {'product_key': 'SKU-001', 'quantity': 1, 'unit_price': Decimal('100.00'), 'base_list_price': Decimal('120.00')},
        ]
        result = calculate_rebate_accrual(
            ledger_id=str(self.ledger.pk),
            proforma_id='PF-SMALL',
            proforma_lines=small_lines,
            proforma_date=date(2026, 1, 15),
        )
        self.assertFalse(result.threshold_met)

    def test_T5_qualified_product_keys_filter(self):
        """
        Solo SKU-001 califica → 10*100 = 1000.00
        """
        result = calculate_rebate_accrual(
            ledger_id=str(self.ledger.pk),
            proforma_id='PF-FILTER',
            proforma_lines=SAMPLE_LINES,
            proforma_date=date(2026, 1, 15),
            qualified_product_keys=['SKU-001'],
        )
        self.assertEqual(result.qualifying_amount, Decimal('1000.00'))
        self.assertEqual(result.qualifying_units, 10)

    def test_T5_fixed_amount_rebate(self):
        """
        fixed_amount: accrued = units * rebate_value = 15 * 2 = 30.0000
        """
        program2 = make_program(
            self.brand,
            rebate_type=RebateType.FIXED_AMOUNT,
            rebate_value=Decimal('2.0000'),
            threshold_type=ThresholdType.NONE,
        )
        assignment2 = RebateAssignment.objects.create(
            rebate_program=program2,
            client=self.client,
            is_active=False,  # no conflicto con el activo
        )
        ledger2 = RebateLedger.objects.create(
            rebate_assignment=assignment2,
            period_start=date(2026, 1, 1),
            period_end=date(2026, 3, 31),
            status=LedgerStatus.ACCRUING,
        )
        result = calculate_rebate_accrual(
            ledger_id=str(ledger2.pk),
            proforma_id='PF-FIXED',
            proforma_lines=SAMPLE_LINES,
            proforma_date=date(2026, 1, 15),
        )
        self.assertEqual(result.accrued_amount, Decimal('30.0000'))


class T5fConcurrentAccrualTest(TransactionTestCase):
    """T5-f — select_for_update previene race condition en accrual concurrente."""

    def setUp(self):
        from apps.brands.models import Brand
        from apps.clientes.models import Cliente
        self.brand = Brand.objects.get_or_create(slug='brand-concurrent', defaults={'name': 'Concurrent'})[0]
        self.client = Cliente.objects.get_or_create(
            nombre='Cliente Concurrent', defaults={'email': 'concurrent@test.com'}
        )[0]
        self.program = RebateProgram.objects.create(
            brand=self.brand,
            name='Concurrent Prog',
            period_type=PeriodType.QUARTERLY,
            valid_from=date(2026, 1, 1),
            rebate_type=RebateType.PERCENTAGE,
            rebate_value=Decimal('5.0000'),
            calculation_base='invoiced',
            threshold_type=ThresholdType.NONE,
        )
        self.assignment = RebateAssignment.objects.create(
            rebate_program=self.program,
            client=self.client,
        )
        self.ledger = RebateLedger.objects.create(
            rebate_assignment=self.assignment,
            period_start=date(2026, 1, 1),
            period_end=date(2026, 3, 31),
            status=LedgerStatus.ACCRUING,
        )

    def test_T5f_concurrent_same_proforma_only_one_entry(self):
        lines = [
            {'product_key': 'SKU-X', 'quantity': 10, 'unit_price': Decimal('50.00'), 'base_list_price': Decimal('60.00')},
        ]
        errors = []

        def run_accrual():
            try:
                calculate_rebate_accrual(
                    ledger_id=str(self.ledger.pk),
                    proforma_id='PF-CONCURRENT',
                    proforma_lines=lines,
                    proforma_date=date(2026, 1, 20),
                )
            except Exception as e:
                errors.append(e)

        t1 = threading.Thread(target=run_accrual)
        t2 = threading.Thread(target=run_accrual)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # Solo debe haber 1 entry — la segunda fue idempotente o fue bloqueada
        count = RebateAccrualEntry.objects.filter(
            ledger=self.ledger, proforma_id='PF-CONCURRENT'
        ).count()
        self.assertEqual(count, 1)
