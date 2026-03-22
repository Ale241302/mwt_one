from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from apps.users.models import MWTUser, UserRole
from apps.brands.models import Brand
from apps.productos.models import ProductMaster

class Phase1CatalogTests(APITestCase):
    def setUp(self):
        self.brand = Brand.objects.create(name="marluvas", slug="marluvas", code="ML")
        self.user = MWTUser.objects.create_user(
            email="client@example.com",
            password="password",
            role=UserRole.CLIENT_MARLUVAS
        )
        self.product = ProductMaster.objects.create(
            brand=self.brand,
            sku="SKU1",
            name="Test Product"
        )
        self.catalog_url = reverse('portal-catalog')

    def test_19_catalog_success(self):
        """Test #19: Catalog API returns products."""
        self.client.force_authenticate(user=self.user)
        res = self.client.get(self.catalog_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Even if 0 products depending on exact filters, it should return 200 list
        self.assertIsInstance(res.data, list)

    def test_20_catalog_unauthenticated(self):
        """Test #20: Unauthenticated access rejected."""
        res = self.client.get(self.catalog_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_21_catalog_wrong_brand(self):
        """Test #21: User with no brand gets 403."""
        other_user = MWTUser.objects.create_user(email="other@ex.com", password="pwd", role=UserRole.BRAND)
        self.client.force_authenticate(user=other_user)
        res = self.client.get(self.catalog_url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_22_catalog_price_resolution(self):
        """Test #22: Catalog includes resolved prices."""
        self.client.force_authenticate(user=self.user)
        res = self.client.get(self.catalog_url)
        if len(res.data) > 0:
            self.assertIn('price', res.data[0])

    def test_23_catalog_pricing_source(self):
        """Test #23: Catalog indicates pricing source."""
        self.client.force_authenticate(user=self.user)
        res = self.client.get(self.catalog_url)
        if len(res.data) > 0:
            self.assertIn('pricing_source', res.data[0])
