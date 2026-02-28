import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def superuser(db):
    user = User.objects.create_superuser('ceo', 'ceo@mwt.com', 'password')
    return user
