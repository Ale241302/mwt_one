# apps/expedientes/tests/test_sprint5.py
"""
S5-11: Comprehensive Sprint 5 tests
Covers: S5-05 (C29 ART-12), S5-06 (Handoff), S5-07 (ART-19 suggestions),
        S5-08 (C36 Shipment Updates), S5-10 (C21 modo B refinado)
"""
from datetime import timedelta
from decimal import Decimal
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.expedientes.models import (
    Expediente, ArtifactInstance, EventLog, PaymentLine, LegalEntity,
)
from apps.transfers.models import Node
from apps.expedientes.enums import ExpedienteStatus, DispatchMode
from apps.expedientes.tests.factories import create_user, create_expediente, create_legal_entity


class S5_05_CompensationTests(APITestCase):
    """S5-05: C29 RegisterCompensation - ART-12"""

    def setUp(self):
        self.user = create_user(username='normal_comp')
        self.ceo = create_user(username='ceo_comp', is_superuser=True)
        self.client.force_authenticate(user=self.ceo)
        self.le = create_legal_entity(entity_id='CL_COMP')
        self.exp = create_expediente(client=self.le, brand='MARLUVAS', status=ExpedienteStatus.CERRADO)

    def test_c29_creates_art12(self):
        url = reverse('expedientes:register-compensation', kwargs={'pk': self.exp.pk})
        res = self.client.post(url, {'payload': {'amount': 150, 'reason': 'Quality issue'}}, format='json')
        self.assertIn(res.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.assertTrue(ArtifactInstance.objects.filter(
            expediente=self.exp, artifact_type='ART-12'
        ).exists())

    def test_c29_ceo_only(self):
        url = reverse('expedientes:register-compensation', kwargs={'pk': self.exp.pk})
        self.client.force_authenticate(user=self.user)
        res = self.client.post(url, {'payload': {'amount': 50}}, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_c20_void_art12(self):
        self.exp.status = ExpedienteStatus.PREPARACION
        self.exp.save()
        art12 = ArtifactInstance.objects.create(
            expediente=self.exp, artifact_type='ART-12', status='completed'
        )
        url = reverse('expedientes:void-artifact', kwargs={'pk': self.exp.pk})
        res = self.client.post(url, {'artifact_id': art12.pk, 'reason': 'Error'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        art12.refresh_from_db()
        self.assertEqual(art12.status, 'void')


class S5_06_HandoffTests(APITestCase):
    """S5-06: Handoff Expediente â†’ Transfer suggestion"""

    def setUp(self):
        self.ceo = create_user(username='ceo_handoff', is_superuser=True)
        self.user = create_user(username='normal_handoff')
        self.client.force_authenticate(user=self.ceo)
        self.le = create_legal_entity(entity_id='CL_HO')
        self.exp = create_expediente(client=self.le, brand='MARLUVAS', status=ExpedienteStatus.EN_DESTINO)
        self.node_destino = Node.objects.create(
            name="Destino Warehouse", legal_entity=self.le,
            node_type="warehouse", location="MIA"
        )

    def test_close_with_nodo_destino_returns_suggestion(self):
        """When expediente closes and has nodo_destino, the handoff endpoint returns a suggestion."""
        self.exp.nodo_destino = self.node_destino
        self.exp.payment_status = 'paid'
        self.exp.status = ExpedienteStatus.CERRADO
        self.exp.save()
        ArtifactInstance.objects.create(
            expediente=self.exp, artifact_type='ART-09', status='completed',
            payload={'total': 1000}
        )

        url = reverse('expedientes:handoff-suggestion', kwargs={'pk': self.exp.pk})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['has_suggestion'])
        self.assertIn('transfer_data', res.data)
        self.assertEqual(res.data['node']['name'], 'Destino Warehouse')

    def test_handoff_no_suggestion_without_nodo(self):
        """When no nodo_destino, returns no suggestion."""
        self.exp.status = ExpedienteStatus.CERRADO
        self.exp.nodo_destino = None
        self.exp.save()

        url = reverse('expedientes:handoff-suggestion', kwargs={'pk': self.exp.pk})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(res.data['has_suggestion'])
        self.assertEqual(res.data['reason'], 'No destination node assigned')

    def test_handoff_no_suggestion_when_not_closed(self):
        """When expediente is not CERRADO, returns no suggestion."""
        self.exp.nodo_destino = self.node_destino
        self.exp.status = ExpedienteStatus.PREPARACION
        self.exp.save()

        url = reverse('expedientes:handoff-suggestion', kwargs={'pk': self.exp.pk})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(res.data['has_suggestion'])

    def test_handoff_includes_items_from_art01(self):
        """When ART-01 has items, they appear in the transfer suggestion."""
        self.exp.nodo_destino = self.node_destino
        self.exp.status = ExpedienteStatus.CERRADO
        self.exp.save()
        ArtifactInstance.objects.create(
            expediente=self.exp, artifact_type='ART-01', status='completed',
            payload={'items': [
                {'sku': 'BOOT-001', 'quantity': 100},
                {'sku': 'BOOT-002', 'quantity': 50},
            ]}
        )

        url = reverse('expedientes:handoff-suggestion', kwargs={'pk': self.exp.pk})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['has_suggestion'])
        items = res.data['transfer_data']['items']
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]['sku'], 'BOOT-001')

    def test_handoff_ceo_only(self):
        self.exp.status = ExpedienteStatus.CERRADO
        self.exp.nodo_destino = self.node_destino
        self.exp.save()

        self.client.force_authenticate(user=self.user)
        url = reverse('expedientes:handoff-suggestion', kwargs={'pk': self.exp.pk})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class S5_07_LogisticsSuggestionsTests(APITestCase):
    """S5-07: ART-19 Historical logistics suggestions"""

    def setUp(self):
        self.ceo = create_user(username='ceo_log', is_superuser=True)
        self.client.force_authenticate(user=self.ceo)
        self.le = create_legal_entity(entity_id='CL_LOG')
        self.exp = create_expediente(client=self.le, brand='MARLUVAS')

    def test_suggestions_empty_when_insufficient_data(self):
        url = reverse('expedientes:logistics-suggestions', kwargs={'pk': self.exp.pk})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 0)
        self.assertIn("Insufficient historical data", res.data.get("message", ""))


class S5_08_ShipmentUpdateTests(APITestCase):
    """S5-08: C36 AddShipmentUpdate"""

    def setUp(self):
        self.ceo = create_user(username='ceo_ship', is_superuser=True)
        self.client.force_authenticate(user=self.ceo)
        self.le = create_legal_entity(entity_id='CL_SHIP')
        self.exp = create_expediente(
            client=self.le, brand='MARLUVAS',
            status=ExpedienteStatus.TRANSITO
        )
        self.art05 = ArtifactInstance.objects.create(
            expediente=self.exp, artifact_type='ART-05',
            status='completed', payload={'tracking_url': ''}
        )

    def test_c36_adds_tracking_info(self):
        url = reverse('expedientes:add-shipment-update', kwargs={'pk': self.exp.pk})
        payload = {
            'tracking_url': 'http://track.me/ABC',
            'updates': [{'status': 'Departed port'}]
        }
        res = self.client.post(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.art05.refresh_from_db()
        self.assertEqual(self.art05.payload.get('tracking_url'), 'http://track.me/ABC')

    def test_c36_multiple_updates_accumulate(self):
        url = reverse('expedientes:add-shipment-update', kwargs={'pk': self.exp.pk})

        self.client.post(url, {
            'tracking_url': 'http://track.me/1',
            'updates': [{'status': 'In transit'}]
        }, format='json')

        self.client.post(url, {
            'tracking_url': 'http://track.me/1',
            'updates': [{'status': 'Arrived at customs'}]
        }, format='json')

        self.art05.refresh_from_db()
        updates = self.art05.payload.get('updates', [])
        self.assertGreaterEqual(len(updates), 2)


class S5_10_C21_ComisionModeTests(APITestCase):
    """S5-10: Refine C21 modo B â€” COMISION mode payment calculation"""

    def setUp(self):
        self.ceo = create_user(username='ceo_c21', is_superuser=True)
        self.client.force_authenticate(user=self.ceo)
        self.le = create_legal_entity(entity_id='CL_C21')
        self.exp = create_expediente(
            client=self.le, brand='MARLUVAS',
            mode='COMISION', status=ExpedienteStatus.PREPARACION
        )
        # ART-01: total_po = 1000
        ArtifactInstance.objects.create(
            expediente=self.exp, artifact_type='ART-01',
            status='completed', payload={'total_po': 1000}
        )
        # ART-02: comision_pactada = 10%  â†’ expected commission = 100
        ArtifactInstance.objects.create(
            expediente=self.exp, artifact_type='ART-02',
            status='completed', payload={'comision_pactada': 10}
        )

    def test_c21_partial_then_paid(self):
        """Partial payment then full payment updates status correctly."""
        url = reverse('expedientes:register-payment', kwargs={'pk': self.exp.pk})

        # Pay 50 â†’ partial
        res = self.client.post(url, {
            'amount': '50.00', 'currency': 'USD',
            'method': 'TRANSFER', 'reference': 'REF1'
        }, format='json')
        self.assertIn(res.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.exp.refresh_from_db()
        self.assertEqual(self.exp.payment_status, 'partial')

        # Pay 50 more â†’ paid (total 100 = expected commission)
        res = self.client.post(url, {
            'amount': '50.00', 'currency': 'USD',
            'method': 'TRANSFER', 'reference': 'REF2'
        }, format='json')
        self.assertIn(res.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.exp.refresh_from_db()
        self.assertEqual(self.exp.payment_status, 'paid')

    def test_c21_liquidacion_marluvas_method(self):
        """C21 accepts 'liquidacion_marluvas' as payment method."""
        url = reverse('expedientes:register-payment', kwargs={'pk': self.exp.pk})
        res = self.client.post(url, {
            'amount': '100.00', 'currency': 'USD',
            'method': 'liquidacion_marluvas',
            'reference': 'LIQ-2024-01-001'
        }, format='json')
        self.assertIn(res.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.exp.refresh_from_db()
        self.assertEqual(self.exp.payment_status, 'paid')

        # Verify PaymentLine stored with correct method
        pl = PaymentLine.objects.filter(expediente=self.exp).last()
        self.assertEqual(pl.method, 'liquidacion_marluvas')

    def test_c21_import_mode_uses_total_po(self):
        """For IMPORT mode, reference_total is total_po not commission."""
        exp_import = create_expediente(
            client=self.le, brand='MARLUVAS',
            mode='IMPORT', status=ExpedienteStatus.PREPARACION
        )
        ArtifactInstance.objects.create(
            expediente=exp_import, artifact_type='ART-01',
            status='completed', payload={'total_po': 500}
        )

        url = reverse('expedientes:register-payment', kwargs={'pk': exp_import.pk})
        res = self.client.post(url, {
            'amount': '250.00', 'currency': 'USD',
            'method': 'TRANSFER', 'reference': 'IMP-1'
        }, format='json')
        self.assertIn(res.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        exp_import.refresh_from_db()
        self.assertEqual(exp_import.payment_status, 'partial')

    def test_liquidation_payment_suggestion_endpoint(self):
        """S5-10: GET returns suggestion data for COMISION expediente."""
        url = reverse('expedientes:liquidation-payment-suggestion', kwargs={'pk': self.exp.pk})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # No reconciled liquidation lines yet
        self.assertFalse(res.data['has_suggestion'])

    def test_liquidation_payment_suggestion_not_comision(self):
        """Only applies to COMISION mode."""
        exp_import = create_expediente(
            client=self.le, brand='MARLUVAS',
            mode='IMPORT', status=ExpedienteStatus.PREPARACION
        )
        url = reverse('expedientes:liquidation-payment-suggestion', kwargs={'pk': exp_import.pk})
        self.client.force_authenticate(user=self.ceo)
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(res.data['has_suggestion'])
        self.assertIn('Only applicable for COMISION', res.data['reason'])

    def test_c21_overpayment_still_paid(self):
        """When total paid exceeds expected commission, status should be 'paid'."""
        url = reverse('expedientes:register-payment', kwargs={'pk': self.exp.pk})
        res = self.client.post(url, {
            'amount': '200.00', 'currency': 'USD',
            'method': 'TRANSFER', 'reference': 'OVER1'
        }, format='json')
        self.assertIn(res.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.exp.refresh_from_db()
        self.assertEqual(self.exp.payment_status, 'paid')
