import pytest
from django.db import IntegrityError
from django.test import TestCase
from apps.commercial.models import RebateProgram
from apps.brands.models import Brand
import uuid
from decimal import Decimal
from datetime import date


class TestRebateProgramT1(TestCase):
    """T1: Crear RebateProgram válido, verificar campos y __str__"""

    def setUp(self):
        self.brand = Brand.objects.create(name="TestBrand")

    def test_create_valid_rebate_program(self):
        program = RebateProgram.objects.create(
            brand=self.brand,
            name="Q1 2026 Rebate",
            period_type="quarterly",
            valid_from=date(2026, 1, 1),
            valid_to=date(2026, 3, 31),
            rebate_type="percentage",
            rebate_value=Decimal("5.00"),
            threshold_type="none",
        )
        self.assertIsNotNone(program.pk)
        self.assertEqual(program.brand, self.brand)
        self.assertEqual(program.name, "Q1 2026 Rebate")
        self.assertEqual(program.period_type, "quarterly")
        self.assertEqual(program.rebate_type, "percentage")
        self.assertEqual(program.rebate_value, Decimal("5.00"))
        self.assertEqual(program.threshold_type, "none")
        self.assertIn("Q1 2026 Rebate", str(program))


class TestRebateProgramT2(TestCase):
    """T2: CheckConstraints"""

    def setUp(self):
        self.brand = Brand.objects.create(name="TestBrand2")

    def _base_kwargs(self, **overrides):
        base = dict(
            brand=self.brand,
            name="Program",
            period_type="quarterly",
            valid_from=date(2026, 1, 1),
            valid_to=date(2026, 3, 31),
            rebate_type="percentage",
            rebate_value=Decimal("5.00"),
            threshold_type="none",
        )
        base.update(overrides)
        return base

    def test_t2a_valid_to_gte_valid_from(self):
        # Valid case: valid_to == valid_from
        program = RebateProgram.objects.create(**self._base_kwargs(valid_from=date(2026, 1, 1), valid_to=date(2026, 1, 1)))
        self.assertIsNotNone(program.pk)

    def test_t2b_valid_to_lt_valid_from_raises_integrity_error(self):
        with self.assertRaises(IntegrityError):
            RebateProgram.objects.create(**self._base_kwargs(
                valid_from=date(2026, 3, 31),
                valid_to=date(2026, 1, 1),
            ))

    def test_t2c_threshold_amount_with_threshold_units_raises(self):
        with self.assertRaises(IntegrityError):
            RebateProgram.objects.create(**self._base_kwargs(
                threshold_type="amount",
                threshold_amount=Decimal("1000.00"),
                threshold_units=100,  # must be null when type=amount
            ))

    def test_t2d_threshold_none_with_threshold_amount_raises(self):
        with self.assertRaises(IntegrityError):
            RebateProgram.objects.create(**self._base_kwargs(
                threshold_type="none",
                threshold_amount=Decimal("500.00"),
            ))

    def test_t2e_rebate_value_zero_raises(self):
        with self.assertRaises(IntegrityError):
            RebateProgram.objects.create(**self._base_kwargs(
                rebate_value=Decimal("0.00"),
            ))
