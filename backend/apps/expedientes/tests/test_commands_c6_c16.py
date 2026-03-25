import pytest
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from apps.expedientes.models import Expediente, ArtifactInstance
from apps.expedientes.enums_exp import ExpedienteStatus, CreditClockStartRule, PaymentStatus
from apps.expedientes.services import execute_command
@pytest.fixture
def ceo_user():
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_superuser(username='ceo', password='password', email='ceo@mwt.one')

@pytest.fixture
def brand(db):
    from apps.brands.models import Brand
    return Brand.objects.create(name="Marluvas", slug="MAR")

@pytest.fixture
def legal_entity(db):
    from apps.core.models import LegalEntity
    return LegalEntity.objects.create(legal_name="Client A", entity_id="MWT-A")

@pytest.fixture
def active_expediente(brand, legal_entity, ceo_user):
    return Expediente.objects.create(
        brand=brand,
        legal_entity=legal_entity,
        client=legal_entity,
        status=ExpedienteStatus.REGISTRO,
        credit_clock_start_rule=CreditClockStartRule.ON_SHIPMENT
    )

@pytest.mark.django_db
class TestCommandsC6C16:

    def test_c6_requires_art02_art03(self, active_expediente, ceo_user):
        active_expediente.status = ExpedienteStatus.PRODUCCION
        active_expediente.save()
        
        with pytest.raises(Exception, match="C6 requires both ART-02 and ART-03"):
            execute_command(active_expediente, 'C6', {}, ceo_user)

    def test_c11_starts_credit_clock_on_shipment(self, active_expediente, ceo_user):
        active_expediente.status = ExpedienteStatus.PREPARACION
        active_expediente.credit_clock_start_rule = CreditClockStartRule.ON_SHIPMENT
        active_expediente.save()
        
        # Add required artifacts for C11
        ArtifactInstance.objects.create(expediente=active_expediente, artifact_type='ART-02', status='completed')
        ArtifactInstance.objects.create(expediente=active_expediente, artifact_type='ART-03', status='completed')
        ArtifactInstance.objects.create(expediente=active_expediente, artifact_type='ART-06', status='completed')
        ArtifactInstance.objects.create(expediente=active_expediente, artifact_type='ART-07', status='completed')

        execute_command(active_expediente, 'C11', {}, ceo_user)
        active_expediente.refresh_from_db()
        
        assert active_expediente.status == ExpedienteStatus.TRANSITO
        assert active_expediente.credit_clock_started_at is not None

    def test_check_credit_clocks_management_command(self, active_expediente):
        from django.core.management import call_command
        
        # Set clock to 80 days ago
        active_expediente.credit_clock_started_at = timezone.now() - timedelta(days=80)
        active_expediente.status = ExpedienteStatus.TRANSITO
        active_expediente.save()
        
        call_command('check_credit_clocks')
        active_expediente.refresh_from_db()
        assert active_expediente.credit_warning == True
        assert active_expediente.is_blocked == False

        # Set clock to 95 days ago
        active_expediente.credit_clock_started_at = timezone.now() - timedelta(days=95)
        active_expediente.save()
        
        call_command('check_credit_clocks')
        active_expediente.refresh_from_db()
        assert active_expediente.is_blocked == True
        assert active_expediente.credit_blocked == True

    def test_c16_cancel_as_ceo(self, active_expediente, ceo_user):
        execute_command(active_expediente, 'C16', {}, ceo_user)
        active_expediente.refresh_from_db()
        assert active_expediente.status == ExpedienteStatus.CANCELADO
