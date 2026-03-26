from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from apps.users.models import MWTUser, UserRole
from apps.brands.models import Brand
from apps.productos.models import ProductMaster
from apps.orders.models import ClientOrder, ClientOrderItem

class Phase1OrdersTests(APITestCase):
    def setUp(self):
        self.brand = Brand.objects.create(name="Test Brand", slug="test-brand", code="TB")
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
        self.client.force_authenticate(user=self.user)
        self.list_url = reverse('orders:clientorder-list')

    def test_9_create_order(self):
        """Test #9: Create ClientOrder."""
        data = {
            "client_subsidiary_id": self.user.id,
            "currency": "USD"
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_10_create_order_missing_fields(self):
        """Test #10: Missing client_subsidiary_id."""
        response = self.client.post(self.list_url, {"currency": "USD"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_11_create_order_with_items(self):
        """Test #11: Create ClientOrder with ClientOrderItem."""
        order = ClientOrder.objects.create(client_subsidiary_id=self.user.id, currency="USD")
        item = ClientOrderItem.objects.create(order=order, product=self.product, price=10.0, quantity=2)
        self.assertEqual(item.get_subtotal(), 20.0)

    def test_12_cancel_order(self):
        """Test #12: Transition ClientOrder to CANCELLED."""
        order = ClientOrder.objects.create(client_subsidiary_id=self.user.id, currency="USD")
        url = reverse('orders:clientorder-detail', args=[order.id])
        response = self.client.patch(url, {"status": "cancelled"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.status, "cancelled")

    def test_13_confirm_order(self):
        """Test #13: Transition ClientOrder to CONFIRMED."""
        order = ClientOrder.objects.create(client_subsidiary_id=self.user.id, currency="USD", status="submitted")
        url = reverse('orders:clientorder-detail', args=[order.id])
        response = self.client.patch(url, {"status": "confirmed"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.status, "confirmed")

    def test_14_order_billing_total(self):
        """Test #14: Order total calculation."""
        order = ClientOrder.objects.create(client_subsidiary_id=self.user.id, currency="USD")
        ClientOrderItem.objects.create(order=order, product=self.product, price=10.0, quantity=2)
        ClientOrderItem.objects.create(order=order, product=self.product, price=15.0, quantity=1)
        order.total_amount = sum(item.get_subtotal() for item in order.items.all())
        order.save()
        self.assertEqual(order.total_amount, 35.0)

    def test_15_list_orders(self):
        """Test #15: List orders."""
        ClientOrder.objects.create(client_subsidiary_id=self.user.id, currency="USD")
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_16_retrieve_order(self):
        """Test #16: Retrieve order."""
        order = ClientOrder.objects.create(client_subsidiary_id=self.user.id, currency="USD")
        url = reverse('orders:clientorder-detail', args=[order.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_17_create_order_api_success(self):
        """Test #17: Create full order via API."""
        data = {
            "client_subsidiary_id": self.user.id,
            "currency": "USD",
            "status": "draft"
        }
        res = self.client.post(self.list_url, data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ClientOrder.objects.count(), 1)

    def test_18_delete_order(self):
        """Test #18: Delete order."""
        order = ClientOrder.objects.create(client_subsidiary_id=self.user.id, currency="USD")
        url = reverse('orders:clientorder-detail', args=[order.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
