from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.brands.models import Brand
from apps.clients.models import Client, Subsidiary

User = get_user_model()


class TestAccessControlT13(TestCase):
    """T13: 403 cross-access and role-based endpoint protection"""

    def setUp(self):
        self.client_api = APIClient()
        self.brand = Brand.objects.create(name="BrandAC")
        self.client_marluvas = Client.objects.create(name="MARLUVAS", brand=self.brand)
        self.client_tecmater = Client.objects.create(name="TECMATER", brand=self.brand)
        self.sub_marluvas = Subsidiary.objects.create(name="SubM", client=self.client_marluvas)
        self.sub_tecmater = Subsidiary.objects.create(name="SubT", client=self.client_tecmater)

        self.user_marluvas = User.objects.create_user(
            username="client_m", password="pass", role="CLIENT_USER",
            subsidiary=self.sub_marluvas
        )
        self.user_tecmater = User.objects.create_user(
            username="client_t", password="pass", role="CLIENT_USER",
            subsidiary=self.sub_tecmater
        )
        self.user_internal = User.objects.create_user(
            username="agent", password="pass", role="AGENT_INTERNAL"
        )
        self.user_ceo = User.objects.create_user(
            username="ceo", password="pass", role="CEO"
        )

    def test_t13a_client_marluvas_cannot_see_tecmater_data(self):
        self.client_api.force_authenticate(user=self.user_marluvas)
        response = self.client_api.get(
            f"/api/commercial/portal/rebates/?subsidiary_id={self.sub_tecmater.pk}"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_t13b_internal_agent_cannot_access_commissions_endpoint(self):
        self.client_api.force_authenticate(user=self.user_internal)
        response = self.client_api.get("/api/commercial/commissions/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_t13c_ceo_can_access_all_endpoints(self):
        self.client_api.force_authenticate(user=self.user_ceo)
        endpoints = [
            "/api/commercial/rebates/",
            "/api/commercial/commissions/",
            "/api/commercial/artifact-policy/",
        ]
        for endpoint in endpoints:
            response = self.client_api.get(endpoint)
            self.assertIn(
                response.status_code,
                [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT],
                f"CEO should access {endpoint}"
            )

    def test_t13d_anonymous_gets_401(self):
        self.client_api.force_authenticate(user=None)
        endpoints = [
            "/api/commercial/rebates/",
            "/api/commercial/commissions/",
            "/api/commercial/artifact-policy/",
        ]
        for endpoint in endpoints:
            response = self.client_api.get(endpoint)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_t13e_client_cannot_see_internal_ledgers(self):
        self.client_api.force_authenticate(user=self.user_marluvas)
        response = self.client_api.get("/api/commercial/ledgers/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
