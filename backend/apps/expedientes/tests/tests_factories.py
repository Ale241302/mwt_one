from django.contrib.auth import get_user_model
from apps.expedientes.models import Expediente, LegalEntity
from apps.expedientes.enums import DispatchMode, LegalEntityRole

User = get_user_model()

def create_user(username='testuser', email='test@example.com', is_superuser=False):
    user, _ = User.objects.get_or_create(username=username, defaults={
        'email': email,
        'is_superuser': is_superuser
    })
    return user

def create_legal_entity(entity_id='CL123'):
    le, _ = LegalEntity.objects.get_or_create(
        entity_id=entity_id,
        defaults={
            'legal_name': 'Test Client',
            'country': 'US',
            'role': LegalEntityRole.DISTRIBUTOR
        }
    )
    return le

def create_expediente(**kwargs):
    le = create_legal_entity()
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
