from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from unittest.mock import patch
from apps.expedientes.tests.factories import create_user, create_expediente, create_legal_entity
from apps.expedientes.enums import ExpedienteStatus, DispatchMode, PaymentStatus
from apps.expedientes.models import Expediente, ArtifactInstance, EventLog

class CommandAPITests(APITestCase):
    def setUp(self):
        self.user = create_user(username='normal')
        self.client.force_authenticate(user=self.user)
        self.le = create_legal_entity(entity_id='CL999')
        self.exp = create_expediente(client=self.le)

    # ──────────────────────────────────────────────────
    # Tests Básicos & C1
    # ──────────────────────────────────────────────────
    def test_c1_create_expediente(self):
        url = reverse('expedientes:create')
        data = {
            'brand': 'NewBrand',
            'legal_entity_id': 'CL999',
            'client': 'CL999',
            'mode': 'IMPORT',
            'freight_mode': 'FCL',
            'dispatch_mode': DispatchMode.MWT,
        }
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['expediente']['brand'], 'NewBrand')
        self.assertEqual(len(res.data['events']), 1)
        self.assertIsNotNone(res.data['expediente']['credit_clock_started_at'])

    def test_c1_on_shipment_rule(self):
        url = reverse('expedientes:create')
        data = {
            'brand': 'OnShipmentBrand',
            'legal_entity_id': 'CL999',
            'client': 'CL999',
            'credit_clock_start_rule': 'on_shipment',
        }
        res = self.client.post(url, data)
        self.assertIsNone(res.data['expediente']['credit_clock_started_at'])
        
    def test_c1_invalid_entity(self):
        url = reverse('expedientes:create')
        data = {'legal_entity_id': 'INVALID', 'client': 'CLIENT'}
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # ──────────────────────────────────────────────────
    # REGISTRO
    # ──────────────────────────────────────────────────
    def test_c2_register_oc(self):
        url = reverse('expedientes:register-oc', kwargs={'pk': self.exp.pk})
        res = self.client.post(url, {'payload': {}})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(ArtifactInstance.objects.filter(artifact_type='OC').exists())

    def test_c3_register_proforma(self):
        url = reverse('expedientes:register-proforma', kwargs={'pk': self.exp.pk})
        res = self.client.post(url, {'payload': {}})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_c4_decide_mode_requires_ceo(self):
        url = reverse('expedientes:decide-mode', kwargs={'pk': self.exp.pk})
        res = self.client.post(url, {'payload': {}})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        
        ceo = create_user(username='ceo', is_superuser=True)
        self.client.force_authenticate(user=ceo)
        res = self.client.post(url, {'payload': {}})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_c5_confirm_sap_transitions_and_events(self):
        self.exp.status = ExpedienteStatus.REGISTRO
        self.exp.save()
        url = reverse('expedientes:confirm-sap', kwargs={'pk': self.exp.pk})
        res = self.client.post(url, {'payload': {}})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # Verify 2 events returned (Transition + Command)
        self.assertEqual(len(res.data['events']), 2)
        self.exp.refresh_from_db()
        self.assertEqual(self.exp.status, ExpedienteStatus.PRODUCCION)

    # ──────────────────────────────────────────────────
    # PRODUCCION + PREPARACION
    # ──────────────────────────────────────────────────
    def test_c6_confirm_production(self):
        self.exp.status = ExpedienteStatus.PRODUCCION
        self.exp.save()
        url = reverse('expedientes:confirm-production', kwargs={'pk': self.exp.pk})
        res = self.client.post(url, {})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_c7_register_shipment_starts_clock(self):
        self.exp.status = ExpedienteStatus.PRODUCCION
        self.exp.credit_clock_start_rule = 'on_shipment'
        self.exp.credit_clock_started_at = None
        self.exp.save()
        url = reverse('expedientes:register-shipment', kwargs={'pk': self.exp.pk})
        res = self.client.post(url, {'payload': {}})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.exp.refresh_from_db()
        self.assertIsNotNone(self.exp.credit_clock_started_at)

    def test_c8_register_freight_quote(self):
        self.exp.status = ExpedienteStatus.PRODUCCION
        self.exp.save()
        url = reverse('expedientes:register-freight-quote', kwargs={'pk': self.exp.pk})
        res = self.client.post(url, {'payload': {}})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_c9_register_customs_only_mwt(self):
        self.exp.status = ExpedienteStatus.PREPARACION
        self.exp.dispatch_mode = DispatchMode.CLIENT
        self.exp.save()
        url = reverse('expedientes:register-customs', kwargs={'pk': self.exp.pk})
        res = self.client.post(url, {'payload': {}})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        
        self.exp.dispatch_mode = DispatchMode.MWT
        self.exp.save()
        res = self.client.post(url, {'payload': {}})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_c10_approve_dispatch_transitions(self):
        self.exp.status = ExpedienteStatus.PREPARACION
        self.exp.dispatch_mode = DispatchMode.MWT
        self.exp.save()
        url = reverse('expedientes:approve-dispatch', kwargs={'pk': self.exp.pk})
        res = self.client.post(url, {'payload': {}})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(res.data['events']), 2)
        self.exp.refresh_from_db()
        self.assertEqual(self.exp.status, ExpedienteStatus.DESPACHO)

    # ──────────────────────────────────────────────────
    # DESPACHO → CERRADO
    # ──────────────────────────────────────────────────
    def test_c11_confirm_departure(self):
        self.exp.status = ExpedienteStatus.DESPACHO
        self.exp.save()
        url = reverse('expedientes:confirm-departure', kwargs={'pk': self.exp.pk})
        res = self.client.post(url, {})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_c12_confirm_arrival(self):
        self.exp.status = ExpedienteStatus.DESPACHO
        self.exp.save()
        url = reverse('expedientes:confirm-arrival', kwargs={'pk': self.exp.pk})
        res = self.client.post(url, {})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_c13_issue_invoice(self):
        self.exp.status = ExpedienteStatus.DESPACHO
        self.exp.save()
        url = reverse('expedientes:issue-invoice', kwargs={'pk': self.exp.pk})
        res = self.client.post(url, {'payload': {}})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_c14_close_fails_if_unpaid(self):
        self.exp.status = ExpedienteStatus.DESPACHO
        self.exp.payment_status = PaymentStatus.PENDING
        self.exp.save()
        url = reverse('expedientes:close', kwargs={'pk': self.exp.pk})
        res = self.client.post(url, {})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_c14_close_success(self):
        self.exp.status = ExpedienteStatus.DESPACHO
        self.exp.payment_status = PaymentStatus.PAID
        self.exp.save()
        url = reverse('expedientes:close', kwargs={'pk': self.exp.pk})
        res = self.client.post(url, {})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.exp.refresh_from_db()
        self.assertEqual(self.exp.status, ExpedienteStatus.CERRADO)

    # ──────────────────────────────────────────────────
    # COSTOS Y PAGOS
    # ──────────────────────────────────────────────────
    def test_c15_register_cost(self):
        url = reverse('expedientes:register-cost', kwargs={'pk': self.exp.pk})
        res = self.client.post(url, {'cost_type': 'FREIGHT', 'amount': '1500.00', 'currency': 'USD', 'phase': 'PREP'})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_c21_register_payment(self):
        url = reverse('expedientes:register-payment', kwargs={'pk': self.exp.pk})
        res = self.client.post(url, {'amount': '1500.00', 'currency': 'USD', 'method': 'TRANSFER', 'reference': 'REF123'})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.exp.refresh_from_db()
        self.assertEqual(self.exp.payment_status, PaymentStatus.PARTIAL)

    # ──────────────────────────────────────────────────
    # BLOQUEOS Y CANCELACION
    # ──────────────────────────────────────────────────
    def test_c16_cancel_requires_ceo(self):
        url = reverse('expedientes:cancel', kwargs={'pk': self.exp.pk})
        res = self.client.post(url, {})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        
        ceo = create_user(username='ceo', is_superuser=True)
        self.client.force_authenticate(user=ceo)
        res = self.client.post(url, {})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.exp.refresh_from_db()
        self.assertEqual(self.exp.status, ExpedienteStatus.CANCELADO)

    def test_c17_block(self):
        url = reverse('expedientes:block', kwargs={'pk': self.exp.pk})
        res = self.client.post(url, {'reason': 'test'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.exp.refresh_from_db()
        self.assertTrue(self.exp.is_blocked)

    def test_c18_unblock_requires_ceo(self):
        self.exp.is_blocked = True
        self.exp.save()
        url = reverse('expedientes:unblock', kwargs={'pk': self.exp.pk})
        res = self.client.post(url, {})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        
        ceo = create_user(username='ceo', is_superuser=True)
        self.client.force_authenticate(user=ceo)
        res = self.client.post(url, {})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    # ──────────────────────────────────────────────────
    # PRUEBAS DE ATOMICIDAD (Monkeypatch)
    # ──────────────────────────────────────────────────
    @patch('apps.expedientes.services.ArtifactInstance.objects.create')
    def test_atomicity_c2_exception_rolls_back(self, mock_create):
        # Simulate a DB failure halfway through the execution
        mock_create.side_effect = Exception("Simulated DB Failure")
        url = reverse('expedientes:register-oc', kwargs={'pk': self.exp.pk})
        
        initial_events = EventLog.objects.count()
        with self.assertRaises(Exception):
            self.client.post(url, {'payload': {}})
            
        # Ensure no events were saved due to transaction rollback
        self.assertEqual(EventLog.objects.count(), initial_events)
        
    @patch('apps.expedientes.services.Expediente.save')
    def test_atomicity_c5_transition_rollback(self, mock_save):
        mock_save.side_effect = Exception("Simulated Save Failure")
        self.exp.status = ExpedienteStatus.REGISTRO
        self.exp.save()
        url = reverse('expedientes:confirm-sap', kwargs={'pk': self.exp.pk})
        
        initial_events = EventLog.objects.count()
        with self.assertRaises(Exception):
            self.client.post(url, {'payload': {}})
            
        self.assertEqual(EventLog.objects.count(), initial_events)
        
    @patch('apps.expedientes.services.EventLog.objects.create')
    def test_atomicity_event_failure_rolls_back_expediente(self, mock_event_create):
        mock_event_create.side_effect = Exception("Event Save Failure")
        url = reverse('expedientes:register-oc', kwargs={'pk': self.exp.pk})
        
        with self.assertRaises(Exception):
            self.client.post(url, {'payload': {}})
            
        # The artifact should not have been created because the event creation failed
        self.assertEqual(ArtifactInstance.objects.count(), 0)

