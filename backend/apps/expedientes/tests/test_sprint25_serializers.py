from decimal import Decimal
from django.test import TestCase
from apps.expedientes.models import Expediente, ExpedientePago, ExpedienteProductLine
from apps.expedientes.serializers import BundleSerializer, BundlePortalSerializer

class TestS25Serializers(TestCase):
    def setUp(self):
        self.exp = Expediente.objects.create(
            status='PRODUCCION',
            brand='MWT',
            deferred_total_price=Decimal('1500.00'),
            deferred_visible=True
        )
        self.p1 = ExpedientePago.objects.create(
            expediente=self.exp,
            payment_status='credit_released',
            amount_paid=Decimal('500.00')
        )
        self.p2 = ExpedientePago.objects.create(
            expediente=self.exp,
            payment_status='pending',
            amount_paid=Decimal('200.00')
        )
        self.p3 = ExpedientePago.objects.create(
            expediente=self.exp,
            payment_status='rejected',
            amount_paid=Decimal('100.00')
        )
        # Add a product line to have total_value
        ExpedienteProductLine.objects.create(
            expediente=self.exp,
            unit_price=Decimal('1000.00'),
            quantity=1
        )

    def test_bundle_serializer_ceo_fields(self):
        serializer = BundleSerializer(self.exp)
        data = serializer.data
        self.assertEqual(data['payment_coverage'], 'partial')
        self.assertEqual(Decimal(data['coverage_pct']), Decimal('50.00'))
        self.assertEqual(Decimal(data['total_pending']), Decimal('200.00'))
        self.assertEqual(Decimal(data['total_rejected']), Decimal('100.00'))
        self.assertEqual(Decimal(data['deferred_total_price']), Decimal('1500.00'))
        self.assertTrue(data['deferred_visible'])
        self.assertIn('parent_expediente', data)
        self.assertIn('child_expedientes', data)

    def test_bundle_portal_serializer_restricted_fields(self):
        # Test visible deferred price
        serializer = BundlePortalSerializer(self.exp)
        data = serializer.data
        self.assertEqual(data['payment_coverage'], 'partial')
        self.assertEqual(Decimal(data['coverage_pct']), Decimal('50.00'))
        self.assertEqual(Decimal(data['deferred_total_price']), Decimal('1500.00'))
        
        # Verify restricted fields are NOT present
        self.assertNotIn('total_pending', data)
        self.assertNotIn('total_rejected', data)
        self.assertNotIn('deferred_visible', data)
        self.assertNotIn('credit_exposure', data)

    def test_bundle_portal_serializer_deferred_masked(self):
        self.exp.deferred_visible = False
        self.exp.save()
        serializer = BundlePortalSerializer(self.exp)
        data = serializer.data
        self.assertIsNone(data['deferred_total_price'])
