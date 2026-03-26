import pytest
from django.utils import timezone
from datetime import timedelta
from apps.expedientes.models import Expediente
from apps.expedientes.enums_exp import ExpedienteStatus, CreditClockStartRule
from apps.agreements.models import BrandClientAgreement, PartyType
from apps.expedientes.services import execute_command
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture
def ceo_user():
    return User.objects.create_superuser(username='ceo3', password='password', email='ceo3@mwt.one')

@pytest.fixture
def brand(db):
    from apps.brands.models import Brand
    return Brand.objects.create(name="Marluvas", code="MAR3")

@pytest.fixture
def legal_entity(db):
    from apps.core.models import LegalEntity
    return LegalEntity.objects.create(name="Client B", tax_id="456")

@pytest.fixture
def agreement(brand, legal_entity):
    from django.contrib.postgres.fields import DateTimeRangeField
    from psycopg2.extras import DateTimeTZRange
    
    # Active agreement with defaults
    return BrandClientAgreement.objects.create(
        brand=brand,
        party_type=PartyType.SUBSIDIARY,
        party_id=legal_entity.pk,
        status='active',
        valid_daterange=DateTimeTZRange(timezone.now() - timedelta(days=1), timezone.now() + timedelta(days=365)),
        standard_cost=Decimal('50.00'),
        commission=Decimal('5.00')
    )

from decimal import Decimal

@pytest.mark.django_db
class TestCommercialDefaults:

    def test_c2_applies_commission_in_comision_mode(self, brand, legal_entity, ceo_user, agreement):
        exp = Expediente.objects.create(
            brand=brand, legal_entity=legal_entity, client=legal_entity,
            status=ExpedienteStatus.REGISTRO, mode='COMISION'
        )
        
        payload = {'items': [{'sku': 'SKU1', 'qty': 10}]}
        # We need ProductMaster for C2 validation
        from apps.productos.models import ProductMaster
        ProductMaster.objects.create(sku='SKU1', brand=brand, name='Product 1')

        execute_command(exp, 'C2', payload, ceo_user)
        
        artifact = exp.artifacts.filter(artifact_type='ART-02').first()
        assert artifact.payload['items'][0]['commission'] == 5.0

    def test_c2_applies_standard_cost_in_import_mode(self, brand, legal_entity, ceo_user, agreement):
        exp = Expediente.objects.create(
            brand=brand, legal_entity=legal_entity, client=legal_entity,
            status=ExpedienteStatus.REGISTRO, mode='IMPORT'
        )
        
        payload = {'items': [{'sku': 'SKU2', 'qty': 10}]}
        from apps.productos.models import ProductMaster
        ProductMaster.objects.create(sku='SKU2', brand=brand, name='Product 2')

        execute_command(exp, 'C2', payload, ceo_user)
        
        artifact = exp.artifacts.filter(artifact_type='ART-02').first()
        assert artifact.payload['items'][0]['standard_cost'] == 50.0
