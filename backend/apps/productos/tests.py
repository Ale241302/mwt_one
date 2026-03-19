from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from apps.users.models import MWTUser, UserRole
from .models import Producto

class ProductoTests(APITestCase):
    def setUp(self):
        self.ceo = MWTUser.objects.create_user(
            username='ceo_test', 
            password='password123', 
            role=UserRole.CEO
        )
        self.client = MWTUser.objects.create_user(
            username='client_test', 
            password='password123', 
            role=UserRole.CLIENT_MARLUVAS
        )
        self.url = reverse('producto-list')

    def test_create_producto_as_ceo(self):
        self.client_test = self.client # Shadowing DRF client
        self.client.force_authenticate(user=self.ceo)
        data = {
            'sku': 'SKU001',
            'name': 'Test Product',
            'category': 'Calzado',
            'is_active': True
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Producto.objects.count(), 1)

    def test_create_producto_as_client_forbidden(self):
        self.client.force_authenticate(user=self.client)
        data = {
            'sku': 'SKU002',
            'name': 'Test Product 2',
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
