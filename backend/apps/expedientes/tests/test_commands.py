from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from apps.expedientes.tests.factories import create_user, create_expediente, create_legal_entity
from apps.expedientes.enums import ExpedienteStatus, DispatchMode
from apps.expedientes.models import Expediente

class CommandAPITests(APITestCase):
    def setUp(self):
        self.user = create_user()
        self.client.force_authenticate(user=self.user)
        self.exp = create_expediente()

    def test_c1_create_expediente(self):
        url = reverse('expedientes:create')
        le = create_legal_entity(entity_id='CL999')
        data = {
            'brand': 'NewBrand',
            'legal_entity_id': 'CL999',
            'client': 'CL999',
            'mode': 'IMPORT',
            'freight_mode': 'FCL',
            'dispatch_mode': DispatchMode.MWT,
        }
        res = self.client.post(url, data)
        print("C1 Creation result:", res.data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['expediente']['brand'], 'NewBrand')
        self.assertEqual(len(res.data['events']), 1)

    def test_c2_register_oc(self):
        url = reverse('expedientes:register-oc', kwargs={'pk': self.exp.pk})
        data = {
            'file_url': 'http://example.com/oc.pdf',
            'file_name': 'oc.pdf'
        }
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_c16_cancel_requires_ceo(self):
        url = reverse('expedientes:cancel', kwargs={'pk': self.exp.pk})
        res = self.client.post(url, {})
        # Should be 403 because user is not CEO
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test with CEO
        ceo = create_user(username='ceo', is_superuser=True)
        self.client.force_authenticate(user=ceo)
        res = self.client.post(url, {})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.exp.refresh_from_db()
        self.assertEqual(self.exp.status, ExpedienteStatus.CANCELADO)
