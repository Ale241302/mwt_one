import pytest
from rest_framework.test import APIClient
from .factories import create_user, create_expediente

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user(db):
    user = create_user(username='apiuser', email='apiuser@example.com')
    user.set_password('apipass123')
    user.save()
    return user

@pytest.mark.django_db
class TestSprint3API:
    def test_login_success(self, api_client, user):
        response = api_client.post('/api/core/auth/login/', {'username': 'apiuser', 'password': 'apipass123'})
        assert response.status_code == 200
        assert 'user' in response.data
        assert response.data['user']['username'] == 'apiuser'

    def test_login_failure(self, api_client, user):
        response = api_client.post('/api/core/auth/login/', {'username': 'apiuser', 'password': 'wrongpassword'})
        assert response.status_code == 401

    def test_logout(self, api_client, user):
        api_client.force_authenticate(user=user)
        response = api_client.post('/api/core/auth/logout/')
        assert response.status_code == 200

    def test_dashboard_stats(self, api_client, user):
        api_client.force_authenticate(user=user)
        create_expediente(status='REGISTRO')
        create_expediente(status='TRANSITO')
        
        response = api_client.get('/api/ui/dashboard/')
        assert response.status_code == 200
        data = response.data
        assert 'active_count' in data
        assert 'alert_count' in data
        assert 'blocked_count' in data
        assert 'total_cost' in data

    def test_expedientes_list(self, api_client, user):
        api_client.force_authenticate(user=user)
        create_expediente(status='REGISTRO', brand='SKECHERS')
        create_expediente(status='TRANSITO', brand='ON')
        
        response = api_client.get('/api/expedientes/')
        assert response.status_code == 200
        assert 'results' in response.data
        assert isinstance(response.data['results'], list)
        assert len(response.data['results']) >= 2
        
        # Test filtering
        response_filtered = api_client.get('/api/expedientes/?status=REGISTRO')
        assert response_filtered.status_code == 200
        assert all(exp['status'] == 'REGISTRO' for exp in response_filtered.data['results'])

    def test_expediente_detail_bundle(self, api_client, user):
        api_client.force_authenticate(user=user)
        exp = create_expediente(status='REGISTRO')
        
        response = api_client.get(f'/api/expedientes/{exp.expediente_id}/bundle/')
        assert response.status_code == 200
        assert 'expediente' in response.data
        assert 'events' in response.data
        assert 'artifacts' in response.data
        assert 'available_actions' in response.data
        
        exp_data = response.data['expediente']
        assert exp_data['id'] == str(exp.expediente_id)
        assert exp_data['status'] == 'REGISTRO'
