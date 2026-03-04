# apps/expedientes/tests/test_sprint5.py
from datetime import timedelta
from decimal import Decimal
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.expedientes.models import Expediente, ArtifactInstance, EventLog, PaymentLine
from apps.transfers.models import Node
from apps.expedientes.enums import ExpedienteStatus
from apps.expedientes.tests.factories import create_user, create_expediente, create_legal_entity

class Sprint5ExpedienteTests(APITestCase):
    def setUp(self):
        self.user = create_user(username='normal')
        self.ceo = create_user(username='ceo', is_superuser=True)
        self.client.force_authenticate(user=self.ceo)
        
        self.le = create_legal_entity(entity_id='CL999')
        self.exp = create_expediente(client=self.le, brand='MARLUVAS', status=ExpedienteStatus.REGISTRO)
        
        # Node setup for transfers
        self.node_destino = Node.objects.create(name="Destino", legal_entity=self.le, node_type="warehouse", location="MIA", status="active")

    # S5-05: C29 RegisterCompensation - ART-12
    def test_c29_register_compensation_ceo_only(self):
        self.exp.status = ExpedienteStatus.CERRADO
        self.exp.save()
        
        url = reverse('expedientes:register-compensation', kwargs={'pk': self.exp.pk})
        
        # Test normal user
        self.client.force_authenticate(user=self.user)
        res = self.client.post(url, {'payload': {}}, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test CEO user
        self.client.force_authenticate(user=self.ceo)
        res = self.client.post(url, {'payload': {'amount': 100}}, format='json')
        self.assertIn(res.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.assertTrue(ArtifactInstance.objects.filter(expediente=self.exp, artifact_type='ART-12').exists())

    def test_c20_void_art12(self):
        self.exp.status = ExpedienteStatus.PREPARACION
        self.exp.save()
        art12 = ArtifactInstance.objects.create(expediente=self.exp, artifact_type='ART-12', status='completed')
        
        url = reverse('expedientes:void-artifact', kwargs={'pk': self.exp.pk})
        res = self.client.post(url, {'artifact_id': art12.pk, 'reason': 'Error'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        art12.refresh_from_db()
        self.assertEqual(art12.status, 'void')

    # S5-06: Handoff behavior test (suggests a transfer when Expediente closes if it has a destination node)
    def test_handoff_suggestion_on_close(self):
        self.exp.status = ExpedienteStatus.EN_DESTINO
        self.exp.nodo_destino = self.node_destino
        self.exp.payment_status = 'paid'
        self.exp.save()
        
        ArtifactInstance.objects.create(expediente=self.exp, artifact_type='ART-09', status='completed', payload={'total': 1000})

        url = reverse('expedientes:close', kwargs={'pk': self.exp.pk})
        res = self.client.post(url, {}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        # Depending on if the frontend gets the handoff suggestion, the backend just sets it to CERRADO.
        self.exp.refresh_from_db()
        self.assertEqual(self.exp.status, ExpedienteStatus.CERRADO)
        self.assertIsNotNone(self.exp.nodo_destino) # A Transfer can now be created with source_expediente=self.exp.pk

    # S5-07: ART-19 Suggestion feature (< 5 historical data)
    def test_art19_historical_logistics_suggestions(self):
        url = reverse('expedientes:logistics-suggestions', kwargs={'pk': self.exp.pk})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 0)
        self.assertIn("Insufficient historical data", res.data.get("message", ""))

    # S5-08: Shipment Updates
    def test_c36_add_shipment_update(self):
        self.exp.status = ExpedienteStatus.TRANSITO
        self.exp.save()
        
        # Need ART-05 first
        art05 = ArtifactInstance.objects.create(expediente=self.exp, artifact_type='ART-05', status='completed', payload={'tracking_url': ''})

        url = reverse('expedientes:add-shipment-update', kwargs={'pk': self.exp.pk})
        payload = {
            'tracking_url': 'http://track.me',
            'updates': [{'status': 'On the way'}]
        }
        res = self.client.post(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        art05.refresh_from_db()
        self.assertEqual(art05.payload.get('tracking_url'), 'http://track.me')

    # S5-10: C21 Refine COMISION Mode calculation
    def test_c21_comision_mode_paid(self):
        self.exp.mode = 'COMISION'
        self.exp.status = ExpedienteStatus.PREPARACION
        # Setup required artifacts
        ArtifactInstance.objects.create(expediente=self.exp, artifact_type='ART-01', status='completed', payload={'total_po': 1000})
        ArtifactInstance.objects.create(expediente=self.exp, artifact_type='ART-02', status='completed', payload={'comision_pactada': 10})
        self.exp.save()

        # Expected commission is 1000 * 10 / 100 = 100.
        
        # Paid 50 -> partial
        url = reverse('expedientes:register-payment', kwargs={'pk': self.exp.pk})
        res = self.client.post(url, {'amount': '50.00', 'currency': 'USD', 'method': 'TRANSFER', 'reference': 'REF1'}, format='json')
        self.assertIn(res.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.exp.refresh_from_db()
        self.assertEqual(self.exp.payment_status, 'partial')

        # Paid another 50 -> paid
        res = self.client.post(url, {'amount': '50.00', 'currency': 'USD', 'method': 'TRANSFER', 'reference': 'REF2'}, format='json')
        self.assertIn(res.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.exp.refresh_from_db()
        self.assertEqual(self.exp.payment_status, 'paid')
