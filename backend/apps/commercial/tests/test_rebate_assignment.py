import pytest
from django.db import IntegrityError
from django.test import TestCase
from apps.commercial.models import RebateProgram, RebateAssignment
from apps.commercial.services.rebates import resolve_rebate_assignment
from apps.brands.models import Brand
from apps.clients.models import Client, Subsidiary
from decimal import Decimal
from datetime import date


class TestRebateAssignmentT3(TestCase):
    """T3: Crear asignación y verificar cascada resolve_rebate_assignment()"""

    def setUp(self):
        self.brand = Brand.objects.create(name="BrandA")
        self.client = Client.objects.create(name="ClientA", brand=self.brand)
        self.subsidiary = Subsidiary.objects.create(name="SubA", client=self.client)
        self.program = RebateProgram.objects.create(
            brand=self.brand,
            name="Program A",
            period_type="quarterly",
            valid_from=date(2026, 1, 1),
            valid_to=date(2026, 3, 31),
            rebate_type="percentage",
            rebate_value=Decimal("5.00"),
            threshold_type="none",
        )

    def test_assignment_to_client(self):
        assignment = RebateAssignment.objects.create(
            rebate_program=self.program,
            client=self.client,
        )
        self.assertEqual(assignment.client, self.client)
        self.assertIsNone(assignment.subsidiary)

    def test_assignment_to_subsidiary(self):
        assignment = RebateAssignment.objects.create(
            rebate_program=self.program,
            subsidiary=self.subsidiary,
        )
        self.assertEqual(assignment.subsidiary, self.subsidiary)
        self.assertIsNone(assignment.client)

    def test_resolve_cascades_subsidiary_over_client(self):
        # Client-level assignment
        RebateAssignment.objects.create(rebate_program=self.program, client=self.client)
        # Subsidiary-level assignment (higher priority)
        sub_assignment = RebateAssignment.objects.create(
            rebate_program=self.program, subsidiary=self.subsidiary
        )
        result = resolve_rebate_assignment(
            program=self.program, subsidiary=self.subsidiary, client=self.client
        )
        self.assertEqual(result, sub_assignment)

    def test_resolve_falls_back_to_client(self):
        client_assignment = RebateAssignment.objects.create(
            rebate_program=self.program, client=self.client
        )
        result = resolve_rebate_assignment(
            program=self.program, subsidiary=self.subsidiary, client=self.client
        )
        self.assertEqual(result, client_assignment)


class TestRebateAssignmentT4(TestCase):
    """T4: UniqueConstraints y CheckConstraints en RebateAssignment"""

    def setUp(self):
        self.brand = Brand.objects.create(name="BrandB")
        self.client = Client.objects.create(name="ClientB", brand=self.brand)
        self.subsidiary = Subsidiary.objects.create(name="SubB", client=self.client)
        self.program = RebateProgram.objects.create(
            brand=self.brand,
            name="Program B",
            period_type="quarterly",
            valid_from=date(2026, 1, 1),
            valid_to=date(2026, 3, 31),
            rebate_type="percentage",
            rebate_value=Decimal("5.00"),
            threshold_type="none",
        )

    def test_t4a_duplicate_active_program_client_raises(self):
        RebateAssignment.objects.create(
            rebate_program=self.program, client=self.client, is_active=True
        )
        with self.assertRaises(IntegrityError):
            RebateAssignment.objects.create(
                rebate_program=self.program, client=self.client, is_active=True
            )

    def test_t4b_both_null_raises(self):
        with self.assertRaises(IntegrityError):
            RebateAssignment.objects.create(
                rebate_program=self.program,
                client=None,
                subsidiary=None,
            )

    def test_t4c_both_client_and_subsidiary_raises(self):
        with self.assertRaises(IntegrityError):
            RebateAssignment.objects.create(
                rebate_program=self.program,
                client=self.client,
                subsidiary=self.subsidiary,
            )
