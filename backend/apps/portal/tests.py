from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from apps.users.models import MWTUser, UserRole
from apps.expedientes.models import Expediente, LegalEntity
from apps.brands.models import Brand

class PortalTests(APITestCase):
    def setUp(self):
        # Create Brands
        self.brand_marluvas = Brand.objects.create(name='Marluvas', slug='marluvas')
        self.brand_tecmater = Brand.objects.create(name='Tecmater', slug='tecmater')
        
        # Create LegalEntities
        self.le_mwt = LegalEntity.objects.create(
            entity_id='MWT-CR', 
            legal_name='MWT', 
            role='OWNER', 
            relationship_to_mwt='SELF',
            frontend='MWT_ONE',
            visibility_level='FULL',
            pricing_visibility='INTERNAL',
            country='CR'
        )
        self.le_client = LegalEntity.objects.create(
            entity_id='CL-001', 
            legal_name='Test Client',
            role='DISTRIBUTOR',
            relationship_to_mwt='DISTRIBUTION',
            frontend='PORTAL_MWT_ONE',
            visibility_level='PARTNER',
            pricing_visibility='CLIENT',
            country='CR'
        )

        # Create Users
        self.user_marluvas = MWTUser.objects.create_user(
            username='user_marluvas', 
            password='password123', 
            role=UserRole.CLIENT_MARLUVAS
        )
        self.user_tecmater = MWTUser.objects.create_user(
            username='user_tecmater', 
            password='password123', 
            role=UserRole.CLIENT_TECMATER
        )

        # Create Expedientes
        self.exp_marluvas = Expediente.objects.create(
            legal_entity=self.le_mwt,
            client=self.le_client,
            brand=self.brand_marluvas
        )
        self.exp_tecmater = Expediente.objects.create(
            legal_entity=self.le_mwt,
            client=self.le_client,
            brand=self.brand_tecmater
        )

        self.url = reverse('portal-expedientes-v1-list')

    def test_marluvas_user_only_sees_marluvas_expedientes(self):
        self.client.force_authenticate(user=self.user_marluvas)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Results should only contain exp_marluvas
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['brand'], 'marluvas')

    def test_tecmater_user_only_sees_tecmater_expedientes(self):
        self.client.force_authenticate(user=self.user_tecmater)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['brand'], 'tecmater')
