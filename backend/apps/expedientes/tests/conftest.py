import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def superuser(db):
    user = User.objects.create(
        username='ceo',
        email='ceo@mwt.com',
        is_superuser=True,
        is_staff=True
    )
    user.set_password('password')
    user.save()
    return user
