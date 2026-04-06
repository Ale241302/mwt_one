"""
T1 — RebateProgram: creación válida y __str__
T2 — RebateProgram: CheckConstraints (7 constraints del modelo)
"""
import pytest
from decimal import Decimal
from datetime import date
from django.db import IntegrityError
from django.test import TestCase

from apps.commercial.models import (
    RebateProgram,
    RebateProgramProduct,
    PeriodType,
    RebateType,
    ThresholdType,
)


def make_brand():
    from apps.brands.models import Brand
    return Brand.objects.get_or_create(slug='brand-test', defaults={'name': 'Brand Test'})[0]


class T1RebateProgramCreationTest(TestCase):
    """T1 — Crear RebateProgram válido, verificar campos y __str__."""

    def setUp(self):
        self.brand = make_brand()

    def test_create_valid_program_percentage(self):
        prog = RebateProgram.objects.create(
            brand=self.brand,
            name='Q1 2026 Rebate',
            period_type=PeriodType.QUARTERLY,
            valid_from=date(2026, 1, 1),
            valid_to=date(2026, 3, 31),
            rebate_type=RebateType.PERCENTAGE,
            rebate_value=Decimal('5.0000'),
            calculation_base='invoiced',
            threshold_type=ThresholdType.AMOUNT,
            threshold_amount=Decimal('10000.00'),
        )
        self.assertEqual(prog.period_type, PeriodType.QUARTERLY)
        self.assertEqual(prog.rebate_type, RebateType.PERCENTAGE)
        self.assertEqual(prog.threshold_type, ThresholdType.AMOUNT)
        self.assertTrue(prog.is_active)
        self.assertIn('Q1 2026 Rebate', str(prog))

    def test_create_valid_program_fixed_amount_no_threshold(self):
        prog = RebateProgram.objects.create(
            brand=self.brand,
            name='Fixed Rebate',
            period_type=PeriodType.ANNUAL,
            valid_from=date(2026, 1, 1),
            rebate_type=RebateType.FIXED_AMOUNT,
            rebate_value=Decimal('100.0000'),
            threshold_type=ThresholdType.NONE,
        )
        self.assertIsNone(prog.valid_to)
        self.assertIsNone(prog.threshold_amount)
        self.assertIsNone(prog.threshold_units)

    def test_create_program_units_threshold(self):
        prog = RebateProgram.objects.create(
            brand=self.brand,
            name='Units Rebate',
            period_type=PeriodType.MONTHLY,
            valid_from=date(2026, 1, 1),
            rebate_type=RebateType.PERCENTAGE,
            rebate_value=Decimal('3.0000'),
            threshold_type=ThresholdType.UNITS,
            threshold_units=500,
        )
        self.assertEqual(prog.threshold_units, 500)
        self.assertIsNone(prog.threshold_amount)

    def test_rebate_program_product_unique_together(self):
        prog = RebateProgram.objects.create(
            brand=self.brand,
            name='Product Prog',
            period_type=PeriodType.QUARTERLY,
            valid_from=date(2026, 1, 1),
            rebate_type=RebateType.PERCENTAGE,
            rebate_value=Decimal('2.0000'),
            threshold_type=ThresholdType.NONE,
        )
        RebateProgramProduct.objects.create(rebate_program=prog, product_key='SKU-001')
        with self.assertRaises(IntegrityError):
            RebateProgramProduct.objects.create(rebate_program=prog, product_key='SKU-001')


class T2RebateProgramConstraintsTest(TestCase):
    """T2 — CheckConstraints del modelo RebateProgram."""

    def setUp(self):
        self.brand = make_brand()
        self.base_kwargs = dict(
            brand=self.brand,
            name='Test',
            period_type=PeriodType.QUARTERLY,
            valid_from=date(2026, 1, 1),
            rebate_type=RebateType.PERCENTAGE,
            rebate_value=Decimal('5.0000'),
            threshold_type=ThresholdType.NONE,
        )

    def test_T2a_valid_to_gte_valid_from_ok(self):
        prog = RebateProgram(**self.base_kwargs)
        prog.valid_to = date(2026, 3, 31)
        prog.save()
        self.assertIsNotNone(prog.pk)

    def test_T2b_valid_to_lt_valid_from_raises(self):
        kwargs = {**self.base_kwargs, 'valid_to': date(2025, 12, 31)}
        with self.assertRaises(IntegrityError):
            RebateProgram.objects.create(**kwargs)

    def test_T2c_threshold_type_amount_with_threshold_units_raises(self):
        kwargs = {
            **self.base_kwargs,
            'threshold_type': ThresholdType.AMOUNT,
            'threshold_amount': Decimal('5000.00'),
            'threshold_units': 100,  # debe ser NULL cuando type=amount
        }
        with self.assertRaises(IntegrityError):
            RebateProgram.objects.create(**kwargs)

    def test_T2d_threshold_type_none_with_threshold_amount_raises(self):
        kwargs = {
            **self.base_kwargs,
            'threshold_type': ThresholdType.NONE,
            'threshold_amount': Decimal('5000.00'),  # debe ser NULL cuando type=none
        }
        with self.assertRaises(IntegrityError):
            RebateProgram.objects.create(**kwargs)

    def test_T2d_threshold_type_none_with_threshold_units_raises(self):
        kwargs = {
            **self.base_kwargs,
            'threshold_type': ThresholdType.NONE,
            'threshold_units': 100,  # debe ser NULL cuando type=none
        }
        with self.assertRaises(IntegrityError):
            RebateProgram.objects.create(**kwargs)

    def test_T2e_rebate_value_zero_raises(self):
        kwargs = {**self.base_kwargs, 'rebate_value': Decimal('0.0000')}
        with self.assertRaises(IntegrityError):
            RebateProgram.objects.create(**kwargs)

    def test_T2e_rebate_value_negative_raises(self):
        kwargs = {**self.base_kwargs, 'rebate_value': Decimal('-1.0000')}
        with self.assertRaises(IntegrityError):
            RebateProgram.objects.create(**kwargs)

    def test_T2_threshold_type_units_with_threshold_amount_raises(self):
        kwargs = {
            **self.base_kwargs,
            'threshold_type': ThresholdType.UNITS,
            'threshold_units': 100,
            'threshold_amount': Decimal('5000.00'),  # debe ser NULL cuando type=units
        }
        with self.assertRaises(IntegrityError):
            RebateProgram.objects.create(**kwargs)
