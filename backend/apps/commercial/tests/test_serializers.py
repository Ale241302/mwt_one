"""
T12 — Seguridad de serializers: campos expuestos vs. campos sensibles.
"""
from decimal import Decimal
from datetime import date
from django.test import TestCase

from apps.commercial.serializers import (
    RebateProgramInternalSerializer,
    RebateLedgerInternalSerializer,
    RebateProgressPortalSerializer,
)
from apps.commercial.models import (
    RebateProgram,
    RebateAssignment,
    RebateLedger,
    PeriodType,
    RebateType,
    ThresholdType,
    LedgerStatus,
)


def make_brand(slug='brand-ser'):
    from apps.brands.models import Brand
    return Brand.objects.get_or_create(slug=slug, defaults={'name': f'Brand {slug}'})[0]


def make_client():
    from apps.clientes.models import Cliente
    return Cliente.objects.get_or_create(
        nombre='Cliente Ser', defaults={'email': 'ser@test.com'}
    )[0]


class T12SerializerSecurityTest(TestCase):
    """T12 — RebateProgressPortalSerializer no expone campos sensibles."""

    PORTAL_FORBIDDEN_FIELDS = {
        'rebate_value',
        'accrued_amount',
        'accrued_rebate',
        'threshold_amount',
        'threshold_units',
        'calculation_base',
        'qualifying_amount',
    }

    PORTAL_ALLOWED_FIELDS = {
        'program_name',
        'period',
        'threshold_type',
        'progress_percentage',
        'threshold_met',
    }

    def setUp(self):
        self.brand = make_brand()
        self.client = make_client()
        self.program = RebateProgram.objects.create(
            brand=self.brand,
            name='Portal Program',
            period_type=PeriodType.QUARTERLY,
            valid_from=date(2026, 1, 1),
            valid_to=date(2026, 3, 31),
            rebate_type=RebateType.PERCENTAGE,
            rebate_value=Decimal('5.0000'),
            calculation_base='invoiced',
            threshold_type=ThresholdType.AMOUNT,
            threshold_amount=Decimal('5000.00'),
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
            qualifying_amount=Decimal('2500.00'),
            accrued_amount=Decimal('125.00'),
        )

    def test_T12a_portal_serializer_excludes_forbidden_fields(self):
        serializer = RebateProgressPortalSerializer(self.ledger)
        data = serializer.data
        for forbidden_field in self.PORTAL_FORBIDDEN_FIELDS:
            self.assertNotIn(
                forbidden_field, data,
                msg=f"Portal serializer expone campo sensible: '{forbidden_field}'"
            )

    def test_T12b_portal_serializer_includes_allowed_fields(self):
        serializer = RebateProgressPortalSerializer(self.ledger)
        data = serializer.data
        for allowed_field in self.PORTAL_ALLOWED_FIELDS:
            self.assertIn(
                allowed_field, data,
                msg=f"Portal serializer no incluye campo requerido: '{allowed_field}'"
            )

    def test_T12b_portal_serializer_only_allowed_fields(self):
        serializer = RebateProgressPortalSerializer(self.ledger)
        data_keys = set(serializer.data.keys())
        unexpected = data_keys - self.PORTAL_ALLOWED_FIELDS
        self.assertEqual(
            unexpected, set(),
            msg=f"Portal serializer contiene campos no permitidos: {unexpected}"
        )

    def test_T12c_ledger_internal_serializer_includes_accrued_amount(self):
        serializer = RebateLedgerInternalSerializer(self.ledger)
        data = serializer.data
        self.assertIn('accrued_amount', data)
        self.assertIn('qualifying_amount', data)
        self.assertIn('status', data)

    def test_T12d_program_internal_serializer_includes_sensitive_fields(self):
        serializer = RebateProgramInternalSerializer(self.program)
        data = serializer.data
        self.assertIn('rebate_value', data)
        self.assertIn('calculation_base', data)
        self.assertIn('threshold_amount', data)
        self.assertIn('threshold_units', data)
        self.assertIn('period_type', data)
        self.assertIn('valid_from', data)

    def test_T12_progress_percentage_between_0_and_100(self):
        serializer = RebateProgressPortalSerializer(self.ledger)
        data = serializer.data
        pct = float(data['progress_percentage'])
        self.assertGreaterEqual(pct, 0.0)
        self.assertLessEqual(pct, 100.0)

    def test_T12_threshold_met_is_bool(self):
        serializer = RebateProgressPortalSerializer(self.ledger)
        data = serializer.data
        self.assertIsInstance(data['threshold_met'], bool)
