import pytest
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

@pytest.mark.django_db
class TestAuthAPI:
    def setup_method(self):
        self.client = APIClient()
        self.user_data = {
            'username': 'testuser',
            'password': 'testpassword123',
            'email': 'test@example.com'
        }
        self.user = User.objects.create_user(**self.user_data)
        self.login_url = reverse('core:login')
        self.logout_url = reverse('core:logout')
        self.me_url = reverse('core:me')

    def test_login_success(self):
        """test_login_success() → POST /api/auth/login/ → 200 + session + user info"""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'testpassword123'
        })
        assert response.status_code == status.HTTP_200_OK
        assert 'user' in response.data
        assert response.data['user']['username'] == 'testuser'
        # Check if session cookie is set
        assert 'sessionid' in response.cookies

    def test_login_fail_wrong_password(self):
        """test_login_fail_wrong_password() → POST /api/auth/login/ → 401"""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_clears_session(self):
        """test_logout_clears_session() → POST /api/auth/logout/ → 200 + sesión limpia"""
        self.client.login(username='testuser', password='testpassword123')
        response = self.client.post(self.logout_url)
        assert response.status_code == status.HTTP_200_OK
        
        # Check if session is cleared
        me_response = self.client.get(self.me_url)
        assert me_response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_me_authenticated(self):
        """test_me_authenticated() → GET /api/auth/me/ → 200 + user info"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.me_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['user']['username'] == 'testuser'

    def test_me_unauthenticated_has_csrf(self):
        """test_me_unauthenticated_has_csrf()→ GET /api/auth/me/ → 401/403 PERO csrftoken cookie SIEMPRE presente (S3-D06)"""
        response = self.client.get(self.me_url)
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        assert 'csrftoken' in response.cookies
