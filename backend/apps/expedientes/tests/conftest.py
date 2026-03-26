import pytest
from rest_framework.test import APIClient

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def superuser(db):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create(
        username='ceo',
        email='ceo@mwt.com',
        is_superuser=True,
        is_staff=True
    )
    user.set_password('password')
    user.save()
    return user
