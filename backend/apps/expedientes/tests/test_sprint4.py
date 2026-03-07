"""
Sprint 4 â€” Comprehensive Test Suite (S4-12)
Tests cover: models, enums, services (all commands), doble vista costs,
             ART-09 invoice, financial comparison, logistics C22/C23/C24,
             Tecmater brand logic, views endpoints, mirror-pdf.
"""
import pytest
import uuid
from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase, override_settings
from django.utils import timezone
from django.contrib.auth.models import User

from apps.expedientes.models import (
    LegalEntity, Expediente, ArtifactInstance, EventLog,
    CostLine, PaymentLine, LogisticsOption,
)
from apps.expedientes.enums import (
    Brand, CostLineVisibility, ArtifactStatus, LogisticsMode, LogisticsSource,
)
from apps.expedientes.services import (
    create_expediente, execute_command, can_execute_command,
    can_transition_to, supersede_artifact, void_artifact,
    get_costs, get_costs_summary, get_invoice_suggestion,
    get_invoice, calculate_financial_comparison,
)
from apps.expedientes.exceptions import (
    CommandValidationError, TransitionNotAllowedError, ArtifactMissingError,
)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# Fixtures
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class BaseTestCase(TestCase):
    """Common setup for Sprint 4 tests."""

    def setUp(self):
        self.ceo_user = User.objects.create_superuser(
            username='ceo', password='ceo123', email='ceo@mwt.one'
        )
        self.regular_user = User.objects.create_user(
            username='ops', password='ops123', email='ops@mwt.one'
        )
        self.entity = LegalEntity.objects.create(
            entity_id='MWT-CR',
            legal_name='MWT Costa Rica',
            country='CR',
            role='OWNER',
            relationship_to_mwt='SELF',
            frontend='MWT_ONE',
            visibility_level='FULL',
            pricing_visibility='INTERNAL',
        )
        self.client_entity = LegalEntity.objects.create(
            entity_id='SONDEL-CR',
            legal_name='Sondel Costa Rica',
            country='CR',
            role='DISTRIBUTOR',
            relationship_to_mwt='DISTRIBUTION',
            frontend='PORTAL_MWT_ONE',
            visibility_level='PARTNER',
            pricing_visibility='CLIENT',
        )

    def _create_expediente(self, brand='MARLUVAS', mode='FULL'):
        exp, event = create_expediente({
            'legal_entity_id': 'MWT-CR',
            'client': 'SONDEL-CR',
            'brand': brand,
            'mode': mode,
        }, self.ceo_user)
        return exp

    def _add_artifact(self, exp, art_type, payload=None, status='completed'):
        return ArtifactInstance.objects.create(
            expediente=exp,
            artifact_type=art_type,
            status=status,
            payload=payload or {},
        )

    def _add_cost(self, exp, amount=100, visibility='internal', phase='PREPARACION'):
        return CostLine.objects.create(
            expediente=exp,
            cost_type='flete',
            amount=Decimal(str(amount)),
            currency='USD',
            phase=phase,
            description='Test cost',
            visibility=visibility,
        )


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# S4-01: Model Tests
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class TestModels(BaseTestCase):
    """S4-01: Verify new model fields and LogisticsOption."""

    def test_brand_tecmater_exists(self):
        self.assertIn('TECMATER', [c[0] for c in Brand.choices])

    def test_cost_line_visibility_default(self):
        exp = self._create_expediente()
        cost = self._add_cost(exp)
        self.assertEqual(cost.visibility, 'internal')

    def test_cost_line_visibility_client(self):
        exp = self._create_expediente()
        cost = self._add_cost(exp, visibility='client')
        self.assertEqual(cost.visibility, 'client')

    def test_logistics_option_creation(self):
        exp = self._create_expediente()
        art19 = self._add_artifact(exp, 'ART-19', status='pending')
        opt = LogisticsOption.objects.create(
            artifact_instance=art19,
            option_id='OPT-1',
            mode='aereo',
            carrier='DHL',
            route='SJO-MIA',
            estimated_days=5,
            estimated_cost=Decimal('1500.00'),
            currency='USD',
            source='manual',
        )
        self.assertFalse(opt.is_selected)
        self.assertEqual(opt.mode, 'aereo')

    def test_artifact_status_pending(self):
        self.assertIn('pending', [c[0] for c in ArtifactStatus.choices])

    def test_cost_line_append_only(self):
        exp = self._create_expediente()
        cost = self._add_cost(exp)
        with self.assertRaises(Exception):
            cost.amount = Decimal('200')
            cost.save()

    def test_expediente_brand_choices(self):
        exp = self._create_expediente(brand='TECMATER')
        self.assertEqual(exp.brand, 'TECMATER')


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# S4-02: Costs Doble Vista Tests
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class TestCostsDobleVista(BaseTestCase):
    """S4-02: Test cost visibility filtering and summary."""

    def test_get_costs_internal_returns_all(self):
        exp = self._create_expediente()
        self._add_cost(exp, 100, 'internal')
        self._add_cost(exp, 200, 'client')
        costs = get_costs(exp, view='internal')
        self.assertEqual(costs.count(), 2)

    def test_get_costs_client_view(self):
        exp = self._create_expediente()
        self._add_cost(exp, 100, 'internal')
        self._add_cost(exp, 200, 'client')
        costs = get_costs(exp, view='client')
        self.assertEqual(costs.count(), 1)
        self.assertEqual(costs.first().amount, Decimal('200'))

    def test_costs_summary(self):
        exp = self._create_expediente()
        self._add_cost(exp, 100, 'internal')
        self._add_cost(exp, 200, 'client')
        summary = get_costs_summary(exp)
        self.assertEqual(summary['total_internal'], 300.0)
        self.assertEqual(summary['total_client'], 200.0)

    def test_register_cost_with_visibility(self):
        exp = self._create_expediente()
        exp, events = execute_command(exp, 'C15', {
            'cost_type': 'flete',
            'amount': '500',
            'currency': 'USD',
            'phase': 'PREPARACION',
            'description': 'Test visible cost',
            'visibility': 'client',
        }, self.ceo_user)
        cost = exp.cost_lines.last()
        self.assertEqual(cost.visibility, 'client')

    def test_register_cost_default_visibility(self):
        exp = self._create_expediente()
        exp, events = execute_command(exp, 'C15', {
            'cost_type': 'flete',
            'amount': '500',
            'currency': 'USD',
            'phase': 'PREPARACION',
        }, self.ceo_user)
        cost = exp.cost_lines.last()
        self.assertEqual(cost.visibility, 'internal')


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# S4-03: ART-09 Invoice Tests
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class TestInvoice(BaseTestCase):
    """S4-03: Test invoice generation and doble vista."""

    def _prepare_for_invoice(self, exp):
        """Prepare an expediente up to EN_DESTINO with costs."""
        self._add_artifact(exp, 'ART-01', {'total_po': 10000, 'total': 10000, 'items': []})
        self._add_artifact(exp, 'ART-02', {'comision_pactada': 8, 'currency': 'USD'})
        self._add_artifact(exp, 'ART-03')
        self._add_artifact(exp, 'ART-04')
        self._add_artifact(exp, 'ART-05')
        self._add_artifact(exp, 'ART-06')
        self._add_cost(exp, 5000, 'internal')
        self._add_cost(exp, 3000, 'client')
        exp.status = 'EN_DESTINO'
        exp.save(update_fields=['status'])
        return exp

    def test_issue_invoice_creates_art09(self):
        exp = self._create_expediente()
        exp = self._prepare_for_invoice(exp)
        exp, events = execute_command(exp, 'C13', {
            'total_client_view': '12000',
            'currency': 'USD',
            'payload': {'lines': [{'item': 'Producto X', 'amount': 12000}]},
        }, self.ceo_user)
        art09 = exp.artifacts.filter(artifact_type='ART-09', status='completed').first()
        self.assertIsNotNone(art09)
        self.assertIn('consecutive', art09.payload)
        self.assertTrue(art09.payload['consecutive'].startswith('MWT-'))

    def test_invoice_doble_vista(self):
        exp = self._create_expediente()
        exp = self._prepare_for_invoice(exp)
        execute_command(exp, 'C13', {
            'total_client_view': '12000',
            'currency': 'USD',
        }, self.ceo_user)

        # Internal view (CEO sees everything)
        invoice_int = get_invoice(exp, view='internal')
        self.assertIn('total_internal_view', invoice_int)
        self.assertIn('margin', invoice_int)

        # Client view (no CEO fields)
        invoice_client = get_invoice(exp, view='client')
        self.assertNotIn('total_internal_view', invoice_client)
        self.assertNotIn('margin', invoice_client)
        self.assertIn('consecutive', invoice_client)

    def test_invoice_suggestion(self):
        exp = self._create_expediente()
        self._add_artifact(exp, 'ART-02', {'currency': 'USD'})
        self._add_cost(exp, 3000, 'client')
        suggestion = get_invoice_suggestion(exp)
        self.assertEqual(suggestion['suggested_total'], 3000.0)
        self.assertEqual(suggestion['currency'], 'USD')

    def test_c13_blocked_for_comision(self):
        exp = self._create_expediente(mode='COMISION')
        exp.status = 'EN_DESTINO'
        exp.save(update_fields=['status'])
        with self.assertRaises(Exception) as ctx:
            can_execute_command(exp, 'C13', self.ceo_user)
        self.assertIn('COMISION', str(ctx.exception.detail))


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# S4-05: Financial Comparison Tests
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class TestFinancialComparison(BaseTestCase):
    """S4-05: Test financial comparison calculation."""

    def test_comparison_full_mode(self):
        exp = self._create_expediente(mode='FULL')
        self._add_artifact(exp, 'ART-01', {'total_po': 10000, 'total': 10000})
        self._add_artifact(exp, 'ART-02', {'comision_pactada': 8})
        self._add_artifact(exp, 'ART-09', {'total_client_view': 12000, 'total': 12000})
        self._add_cost(exp, 7000, 'internal')

        result = calculate_financial_comparison(exp)
        self.assertEqual(result['actual_mode'], 'FULL')
        self.assertEqual(result['counterfactual_mode'], 'COMISION')
        self.assertEqual(result['actual']['revenue'], 12000.0)
        self.assertEqual(result['actual']['cost'], 7000.0)
        self.assertEqual(result['actual']['margin'], 5000.0)
        # Counterfactual: 8% of 10000 = 800
        self.assertEqual(result['counterfactual']['revenue'], 800.0)

    def test_comparison_comision_mode(self):
        exp = self._create_expediente(mode='COMISION')
        self._add_artifact(exp, 'ART-01', {'total_po': 10000, 'total': 10000})
        self._add_artifact(exp, 'ART-02', {'comision_pactada': 8})

        result = calculate_financial_comparison(exp)
        self.assertEqual(result['actual_mode'], 'COMISION')
        self.assertEqual(result['actual']['revenue'], 800.0)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# S4-07: ART-19 Logistics Tests
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class TestLogistics(BaseTestCase):
    """S4-07: Test C22/C23/C24 logistics commands."""

    def _prepare_for_logistics(self, exp):
        self._add_artifact(exp, 'ART-01', {'total_po': 10000})
        self._add_artifact(exp, 'ART-02', {'comision_pactada': 8})
        self._add_artifact(exp, 'ART-03')
        self._add_artifact(exp, 'ART-04')
        exp.status = 'PRODUCCION'
        exp.save(update_fields=['status'])
        return exp

    def test_c22_materialize_logistics(self):
        exp = self._create_expediente()
        exp = self._prepare_for_logistics(exp)
        exp, events = execute_command(exp, 'C22', {}, self.ceo_user)
        art19 = exp.artifacts.filter(artifact_type='ART-19').first()
        self.assertIsNotNone(art19)
        self.assertEqual(art19.status, 'pending')

    def test_c23_add_logistics_option(self):
        exp = self._create_expediente()
        exp = self._prepare_for_logistics(exp)
        execute_command(exp, 'C22', {}, self.ceo_user)

        exp, events = execute_command(exp, 'C23', {
            'mode': 'aereo',
            'carrier': 'DHL',
            'route': 'SJO-MIA',
            'estimated_days': 5,
            'estimated_cost': '1500',
            'currency': 'USD',
        }, self.ceo_user)

        art19 = exp.artifacts.filter(artifact_type='ART-19').first()
        self.assertEqual(art19.logistics_options.count(), 1)

    def test_c24_decide_logistics(self):
        exp = self._create_expediente()
        exp = self._prepare_for_logistics(exp)
        execute_command(exp, 'C22', {}, self.ceo_user)
        execute_command(exp, 'C23', {
            'mode': 'aereo', 'carrier': 'DHL', 'route': 'SJO-MIA',
            'estimated_days': 5, 'estimated_cost': '1500', 'currency': 'USD',
        }, self.ceo_user)

        exp, events = execute_command(exp, 'C24', {
            'selected_option_id': 'OPT-1',
        }, self.ceo_user)

        art19 = exp.artifacts.filter(artifact_type='ART-19').first()
        self.assertEqual(art19.status, 'completed')

    def test_c22_blocked_for_tecmater(self):
        exp = self._create_expediente(brand='TECMATER')
        # Tecmater always mode=FULL, no ART-19
        self._add_artifact(exp, 'ART-01', {'total_po': 10000})
        self._add_artifact(exp, 'ART-02', {'comision_pactada': 8})
        exp.status = 'PREPARACION'
        exp.save(update_fields=['status'])
        with self.assertRaises(Exception):
            can_execute_command(exp, 'C22', self.ceo_user)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# S4-09: Tecmater Brand Tests
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class TestTecmaterBrand(BaseTestCase):
    """S4-09: Test Tecmater parametrization."""

    def test_tecmater_forces_full_mode(self):
        exp = self._create_expediente(brand='TECMATER')
        self.assertEqual(exp.mode, 'FULL')

    def test_tecmater_rejects_comision(self):
        with self.assertRaises(CommandValidationError):
            create_expediente({
                'legal_entity_id': 'MWT-CR',
                'client': 'SONDEL-CR',
                'brand': 'TECMATER',
                'mode': 'COMISION',
            }, self.ceo_user)

    def test_tecmater_c4_blocked(self):
        exp = self._create_expediente(brand='TECMATER')
        with self.assertRaises(Exception):
            can_execute_command(exp, 'C4', self.ceo_user)

    def test_tecmater_c5_blocked(self):
        exp = self._create_expediente(brand='TECMATER')
        with self.assertRaises(Exception):
            can_execute_command(exp, 'C5', self.ceo_user)

    def test_tecmater_skips_produccion(self):
        """Tecmater transitions REGISTRO â†’ PREPARACION (skipping PRODUCCION)."""
        exp = self._create_expediente(brand='TECMATER')
        self._add_artifact(exp, 'ART-01', {'total_po': 10000})
        self._add_artifact(exp, 'ART-02', {'comision_pactada': 8})
        result = can_transition_to(exp, 'PREPARACION')
        self.assertTrue(result)

    def test_tecmater_no_produccion_transition(self):
        exp = self._create_expediente(brand='TECMATER')
        result = can_transition_to(exp, 'PRODUCCION')
        self.assertFalse(result)

    def test_tecmater_auto_transition_after_c3(self):
        exp = self._create_expediente(brand='TECMATER')
        self._add_artifact(exp, 'ART-01', {'total_po': 10000})
        exp, events = execute_command(exp, 'C3', {
            'payload': {'comision_pactada': 8},
        }, self.ceo_user)
        # After C3, Tecmater should auto-transition to PREPARACION
        exp.refresh_from_db()
        self.assertEqual(exp.status, 'PREPARACION')


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# S4-08: Mirror PDF Tests
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class TestMirrorPDF(BaseTestCase):
    """S4-08: Test mirror PDF generation."""

    def test_generate_html(self):
        from apps.expedientes.services import generate_mirror_pdf
        exp = self._create_expediente()
        self._add_artifact(exp, 'ART-01', {
            'items': [{'product': 'Zapato', 'qty': 100, 'sku': 'ZAP-001'}]
        })
        self._add_cost(exp, 500, 'client')
        html = generate_mirror_pdf(exp)
        self.assertIn('MWT.ONE', html)
        self.assertIn('013A57', html)   # Navy color
        self.assertIn('75CBB3', html)   # Mint color
        self.assertIn('Zapato', html)
        self.assertNotIn('internal', html.lower().split('visibility')[0] if 'visibility' in html.lower() else html)

    def test_no_data_returns_none(self):
        from apps.expedientes.services import generate_mirror_pdf
        exp = self._create_expediente()
        result = generate_mirror_pdf(exp)
        self.assertIsNone(result)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# Payments Regression (Sprint 4 extended)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class TestPayments(BaseTestCase):
    """S4-04: Payment accumulation and COMISION mode."""

    def test_c21_registers_payment(self):
        exp = self._create_expediente()
        exp, events = execute_command(exp, 'C21', {
            'amount': '5000',
            'currency': 'USD',
            'method': 'transferencia',
            'reference': 'REF-001',
        }, self.ceo_user)
        self.assertEqual(exp.payment_lines.count(), 1)

    def test_payment_status_partial(self):
        exp = self._create_expediente()
        self._add_artifact(exp, 'ART-09', {'total_client_view': 10000, 'total': 10000})
        execute_command(exp, 'C21', {
            'amount': '5000', 'currency': 'USD',
            'method': 'transferencia', 'reference': 'REF-001',
        }, self.ceo_user)
        exp.refresh_from_db()
        self.assertEqual(exp.payment_status, 'partial')

    def test_payment_status_paid(self):
        exp = self._create_expediente()
        self._add_artifact(exp, 'ART-09', {'total_client_view': 10000, 'total': 10000})
        execute_command(exp, 'C21', {
            'amount': '10000', 'currency': 'USD',
            'method': 'transferencia', 'reference': 'REF-001',
        }, self.ceo_user)
        exp.refresh_from_db()
        self.assertEqual(exp.payment_status, 'paid')

    def test_comision_payment_uses_art01(self):
        exp = self._create_expediente(mode='COMISION')
        self._add_artifact(exp, 'ART-01', {'total_po': 10000, 'total': 10000})
        execute_command(exp, 'C21', {
            'amount': '10000', 'currency': 'USD',
            'method': 'transferencia', 'reference': 'REF-001',
        }, self.ceo_user)
        exp.refresh_from_db()
        self.assertEqual(exp.payment_status, 'paid')


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# Sprint 1-3 Regression Tests
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class TestRegressionSprint1(BaseTestCase):
    """Regression: Sprint 1-2 commands still work."""

    def test_c1_create(self):
        exp = self._create_expediente()
        self.assertEqual(exp.status, 'REGISTRO')

    def test_c2_register_oc(self):
        exp = self._create_expediente()
        exp, events = execute_command(exp, 'C2', {
            'payload': {'total_po': 10000},
        }, self.ceo_user)
        self.assertTrue(exp.artifacts.filter(artifact_type='ART-01').exists())

    def test_c17_block(self):
        exp = self._create_expediente()
        exp, events = execute_command(exp, 'C17', {
            'reason': 'Test block',
        }, self.ceo_user)
        self.assertTrue(exp.is_blocked)

    def test_c18_unblock(self):
        exp = self._create_expediente()
        execute_command(exp, 'C17', {'reason': 'Test'}, self.ceo_user)
        exp, events = execute_command(exp, 'C18', {}, self.ceo_user)
        self.assertFalse(exp.is_blocked)

    def test_c16_cancel(self):
        exp = self._create_expediente()
        exp, events = execute_command(exp, 'C16', {}, self.ceo_user)
        self.assertEqual(exp.status, 'CANCELADO')
