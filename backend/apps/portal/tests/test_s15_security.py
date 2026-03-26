from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()

class S15SecurityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='test_ceo', password='password123')

    def test_unauthenticated_freeze_access_denied(self):
        url = reverse('api-cliente-credit-freeze', kwargs={'pk': 1})
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_ceo_freeze_access_granted(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('api-cliente-credit-freeze', kwargs={'pk': 1})
        resp = self.client.post(url)
        # Because the endpoints return mock successes, it should be 200 or 201
        self.assertIn(resp.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])

    def test_unauthenticated_preferences_access_denied(self):
        url = reverse('api-portal-preferences')
        resp = self.client.patch(url, {'darkMode': True}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_preferences_access_granted(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('api-portal-preferences')
        resp = self.client.patch(url, {'darkMode': True}, format='json')
        self.assertIn(resp.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
