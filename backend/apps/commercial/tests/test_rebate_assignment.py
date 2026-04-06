"""
T3 — RebateAssignment: creación + cascada resolve_rebate_assignment()
T4 — RebateAssignment: CheckConstraints y UniqueConstraints
"""
import pytest
from decimal import Decimal
from datetime import date
from django.db import IntegrityError
from django.test import TestCase

from apps.commercial.models import (
    RebateProgram,
    RebateAssignment,
    RebateLedger,
    PeriodType,
    RebateType,
    ThresholdType,
    LedgerStatus,
)
from apps.commercial.services.rebates import resolve_rebate_assignment


def make_brand(slug='brand-t3'):
    from apps.brands.models import Brand
    return Brand.objects.get_or_create(slug=slug, defaults={'name': f'Brand {slug}'})[0]


def make_client():
    from apps.clientes.models import Cliente
    return Cliente.objects.get_or_create(
        nombre='Cliente Test T3',
        defaults={'email': 'test-t3@test.com'},
    )[0]


def make_subsidiary(client):
    from apps.clientes.models import ClientSubsidiary
    return ClientSubsidiary.objects.get_or_create(
        client=client,
        name='Subsidiary T3',
        defaults={},
    )[0]


def make_program(brand, name='Prog T3', threshold_type=ThresholdType.AMOUNT, threshold_amount=Decimal('1000.00')):
    return RebateProgram.objects.create(
        brand=brand,
        name=name,
        period_type=PeriodType.QUARTERLY,
        valid_from=date(2026, 1, 1),
        rebate_type=RebateType.PERCENTAGE,
        rebate_value=Decimal('5.0000'),
        calculation_base='invoiced',
        threshold_type=threshold_type,
        threshold_amount=threshold_amount if threshold_type == ThresholdType.AMOUNT else None,
    )


class T3RebateAssignmentCascadeTest(TestCase):
    """T3 — Cascada resolve_rebate_assignment(): subsidiary > client > brand."""

    def setUp(self):
        self.brand = make_brand()
        self.client = make_client()
        self.subsidiary = make_subsidiary(self.client)
        self.program = make_program(self.brand)

    def test_resolve_returns_none_when_no_assignments(self):
        result = resolve_rebate_assignment(
            brand_slug=self.brand.slug,
            client_id=self.client.pk,
            subsidiary_id=self.subsidiary.pk,
        )
        self.assertIsNone(result)

    def test_resolve_subsidiary_level(self):
        RebateAssignment.objects.create(
            rebate_program=self.program,
            subsidiary=self.subsidiary,
        )
        result = resolve_rebate_assignment(
            brand_slug=self.brand.slug,
            client_id=self.client.pk,
            subsidiary_id=self.subsidiary.pk,
        )
        self.assertIsNotNone(result)
        self.assertEqual(result.scope_level, 'subsidiary')
        self.assertEqual(result.program_id, str(self.program.pk))

    def test_resolve_client_level_when_no_subsidiary(self):
        RebateAssignment.objects.create(
            rebate_program=self.program,
            client=self.client,
        )
        result = resolve_rebate_assignment(
            brand_slug=self.brand.slug,
            client_id=self.client.pk,
            subsidiary_id=self.subsidiary.pk,
        )
        # subsidiary no tiene assignment, debe caer a client
        self.assertIsNotNone(result)
        self.assertEqual(result.scope_level, 'client')

    def test_resolve_subsidiary_takes_priority_over_client(self):
        RebateAssignment.objects.create(
            rebate_program=self.program,
            client=self.client,
        )
        program2 = make_program(self.brand, name='Prog Sub')
        RebateAssignment.objects.create(
            rebate_program=program2,
            subsidiary=self.subsidiary,
        )
        result = resolve_rebate_assignment(
            brand_slug=self.brand.slug,
            client_id=self.client.pk,
            subsidiary_id=self.subsidiary.pk,
        )
        self.assertEqual(result.scope_level, 'subsidiary')
        self.assertEqual(result.program_id, str(program2.pk))

    def test_resolve_custom_threshold_overrides_program_threshold(self):
        assignment = RebateAssignment.objects.create(
            rebate_program=self.program,
            subsidiary=self.subsidiary,
            custom_threshold_amount=Decimal('500.00'),
        )
        result = resolve_rebate_assignment(
            brand_slug=self.brand.slug,
            subsidiary_id=self.subsidiary.pk,
        )
        self.assertEqual(result.effective_threshold_amount, Decimal('500.00'))

    def test_resolve_uses_program_threshold_when_no_custom(self):
        RebateAssignment.objects.create(
            rebate_program=self.program,
            subsidiary=self.subsidiary,
        )
        result = resolve_rebate_assignment(
            brand_slug=self.brand.slug,
            subsidiary_id=self.subsidiary.pk,
        )
        self.assertEqual(result.effective_threshold_amount, Decimal('1000.00'))

    def test_resolve_inactive_assignment_ignored(self):
        RebateAssignment.objects.create(
            rebate_program=self.program,
            subsidiary=self.subsidiary,
            is_active=False,
        )
        result = resolve_rebate_assignment(
            brand_slug=self.brand.slug,
            subsidiary_id=self.subsidiary.pk,
        )
        self.assertIsNone(result)


class T4RebateAssignmentConstraintsTest(TestCase):
    """T4 — CheckConstraints y UniqueConstraints de RebateAssignment."""

    def setUp(self):
        self.brand = make_brand(slug='brand-t4')
        self.client = make_client()
        self.subsidiary = make_subsidiary(self.client)
        self.program = make_program(self.brand, name='Prog T4')

    def test_T4a_duplicate_active_program_client_raises(self):
        RebateAssignment.objects.create(
            rebate_program=self.program,
            client=self.client,
            is_active=True,
        )
        with self.assertRaises(IntegrityError):
            RebateAssignment.objects.create(
                rebate_program=self.program,
                client=self.client,
                is_active=True,
            )

    def test_T4a_inactive_duplicate_allowed(self):
        RebateAssignment.objects.create(
            rebate_program=self.program,
            client=self.client,
            is_active=False,
        )
        # Segundo inactivo no viola constraint
        a2 = RebateAssignment.objects.create(
            rebate_program=self.program,
            client=self.client,
            is_active=False,
        )
        self.assertIsNotNone(a2.pk)

    def test_T4b_one_level_only_both_null_raises(self):
        with self.assertRaises(IntegrityError):
            RebateAssignment.objects.create(
                rebate_program=self.program,
                client=None,
                subsidiary=None,
            )

    def test_T4c_both_client_and_subsidiary_raises(self):
        with self.assertRaises(IntegrityError):
            RebateAssignment.objects.create(
                rebate_program=self.program,
                client=self.client,
                subsidiary=self.subsidiary,
            )

    def test_T4a_duplicate_active_program_subsidiary_raises(self):
        RebateAssignment.objects.create(
            rebate_program=self.program,
            subsidiary=self.subsidiary,
            is_active=True,
        )
        with self.assertRaises(IntegrityError):
            RebateAssignment.objects.create(
                rebate_program=self.program,
                subsidiary=self.subsidiary,
                is_active=True,
            )
