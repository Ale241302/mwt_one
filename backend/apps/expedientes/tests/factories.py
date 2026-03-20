from django.contrib.auth import get_user_model
from apps.expedientes.models import Expediente, LegalEntity, ArtifactInstance
from apps.expedientes.enums_exp import DispatchMode, LegalEntityRole
from apps.expedientes.enums_artifacts import ArtifactStatusEnum

User = get_user_model()

def UserFactory(username='testuser', email='test@example.com', is_superuser=False):
    user = User.objects.filter(username=username).first()
    if user:
        return user
    user = User.objects.create(
        username=username,
        email=email,
        is_superuser=is_superuser,
        is_staff=is_superuser,
    )
    user.set_password('password123')
    user.save()
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
    from apps.brands.models import Brand
    
    brand_input = kwargs.pop('brand', 'MARLUVAS')
    if isinstance(brand_input, str):
        brand_slug = brand_input.lower()
        brand, _ = Brand.objects.get_or_create(
            slug=brand_slug,
            defaults={'name': brand_slug.upper()}
        )
    else:
        brand = brand_input

    le = LegalEntityFactory()
    defaults = {
        'legal_entity': le,
        'client': le,
        'brand': brand,
        'mode': 'IMPORT',
        'freight_mode': 'FCL',
        'dispatch_mode': DispatchMode.MWT,
        'status': 'REGISTRO',
        'payment_status': 'pending',
    }
    defaults.update(kwargs)
    return Expediente.objects.create(**defaults)

def ArtifactInstanceFactory(**kwargs):
    if 'expediente' not in kwargs:
        kwargs['expediente'] = ExpedienteFactory()
    defaults = {
        'artifact_type': 'ART-01',
        'status': ArtifactStatusEnum.DRAFT,
        'payload': {}
    }
    defaults.update(kwargs)
    return ArtifactInstance.objects.create(**defaults)

# Alias for backward compatibility if needed
create_user = UserFactory
create_legal_entity = LegalEntityFactory
create_expediente = ExpedienteFactory
