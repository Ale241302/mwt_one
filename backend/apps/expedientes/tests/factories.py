from django.contrib.auth import get_user_model
from apps.expedientes.models import Expediente, LegalEntity, ArtifactInstance
from apps.expedientes.enums import DispatchMode, LegalEntityRole, ArtifactStatus

User = get_user_model()

def UserFactory(username='testuser', email='test@example.com', is_superuser=False):
    user, _ = User.objects.get_or_create(username=username, defaults={
        'email': email,
        'is_superuser': is_superuser
    })
    return user

def LegalEntityFactory(entity_id='CL123'):
    le, _ = LegalEntity.objects.get_or_create(
        entity_id=entity_id,
        defaults={
            'legal_name': 'Test Client',
            'country': 'US',
            'role': LegalEntityRole.DISTRIBUTOR
        }
    )
    return le

def ExpedienteFactory(**kwargs):
    le = LegalEntityFactory()
    defaults = {
        'legal_entity': le,
        'client': le,
        'brand': 'MARLUVAS',
        'mode': 'IMPORT',
        'freight_mode': 'FCL',
        'dispatch_mode': DispatchMode.MWT,
    }
    defaults.update(kwargs)
    return Expediente.objects.create(**defaults)

def ArtifactInstanceFactory(**kwargs):
    if 'expediente' not in kwargs:
        kwargs['expediente'] = ExpedienteFactory()
    defaults = {
        'artifact_type': 'ART-01',
        'status': ArtifactStatus.DRAFT,
        'payload': {}
    }
    defaults.update(kwargs)
    return ArtifactInstance.objects.create(**defaults)

# Alias for backward compatibility if needed
create_user = UserFactory
create_legal_entity = LegalEntityFactory
create_expediente = ExpedienteFactory
