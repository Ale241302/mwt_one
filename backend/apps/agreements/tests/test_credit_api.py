import pytest
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from apps.agreements.models import CreditPolicy, CreditExposure
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def ceo_user(db):
    return User.objects.create_superuser(username='ceo4', password='password', email='ceo4@mwt.one')

@pytest.mark.django_db
class TestCreditAPI:

    def test_credit_status_endpoint(self, api_client, ceo_user):
        from psycopg2.extras import DateTimeTZRange
        # Create a policy
        policy = CreditPolicy.objects.create(
            name="Global Policy",
            max_amount=Decimal('1000000.00'),
            status='active',
            valid_daterange=DateTimeTZRange(timezone.now() - timedelta(days=1), timezone.now() + timedelta(days=365))
        )
        
        # Create some exposure
        from apps.brands.models import Brand
        brand = Brand.objects.create(name="B1", code="B1")
        from apps.core.models import LegalEntity
        client = LegalEntity.objects.create(name="C1", tax_id="T1")
        
        CreditExposure.objects.create(
            brand=brand, client=client,
            reserved_amount=Decimal('150000.00'),
            current_exposure=Decimal('0.00')
        )

        api_client.force_authenticate(user=ceo_user)
        response = api_client.get('/api/agreements/credit-status/')
        
        assert response.status_code == 200
        data = response.json()
        assert data['total_limit'] == 1000000.0
        assert data['total_reserved'] == 150000.0
        assert data['total_available'] == 850000.0
