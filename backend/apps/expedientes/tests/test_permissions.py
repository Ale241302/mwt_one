import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from rest_framework import status
from apps.expedientes.tests.factories import create_user, create_expediente

@pytest.mark.django_db
class TestPermissions:
    def test_ensure_not_blocked_blocks_normal_commands(self):
        client = APIClient()
        user = create_user()
        client.force_authenticate(user=user)
        exp = create_expediente()
        exp.is_blocked = True
        exp.save()

        # Regular command C2 is blocked
        url = reverse('expedientes:register-oc', kwargs={'pk': exp.pk})
        res = client.post(url, {'payload': {}})
        assert res.status_code == status.HTTP_403_FORBIDDEN
        assert 'El expediente está bloqueado' in res.data['detail']

    def test_is_ceo_bypasses_blocked_for_certain_commands(self):
        client = APIClient()
        ceo = create_user(is_superuser=True)
        client.force_authenticate(user=ceo)
        exp = create_expediente()
        exp.is_blocked = True
        exp.save()

        # Cancellation bypasses blocked (but needs CEO)
        url = reverse('expedientes:cancel', kwargs={'pk': exp.pk})
        res = client.post(url, {})
        assert res.status_code == status.HTTP_200_OK

        # Unblock naturally bypasses blocked (needs CEO)
        url = reverse('expedientes:unblock', kwargs={'pk': exp.pk})
        res = client.post(url, {})
        assert res.status_code == status.HTTP_200_OK

    def test_normal_user_may_block_expediente(self):
        client = APIClient()
        user = create_user()
        client.force_authenticate(user=user)
        exp = create_expediente()
        
        # Any authenticated user can block (C17)
        url = reverse('expedientes:block', kwargs={'pk': exp.pk})
        res = client.post(url, {'reason': 'spam'})
        assert res.status_code == status.HTTP_200_OK
