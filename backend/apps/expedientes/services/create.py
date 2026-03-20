from django.db import transaction
from apps.expedientes.models import Expediente, LegalEntity, ArtifactInstance
from apps.expedientes.enums_exp import ExpedienteStatus
from apps.expedientes.enums_artifacts import ArtifactStatusEnum
from apps.brands.models import Brand
from .constants import COMMAND_SPEC

def handle_c1(user, payload):
    with transaction.atomic():
        entity_id = payload.get('entity_id')
        le, _ = LegalEntity.objects.get_or_create(entity_id=entity_id)
        
        brand_slug = payload.get('brand', 'marluvas').lower()
        brand, _ = Brand.objects.get_or_create(
            slug=brand_slug, 
            defaults={'name': brand_slug.upper()}
        )
        
        exp = Expediente.objects.create(
            external_id=payload.get('external_id'),
            legal_entity=le,
            client=le,
            brand=brand,
            status=ExpedienteStatus.REGISTRO,
            mode=payload.get('mode', 'IMPORT'),
            freight_mode=payload.get('freight_mode', 'FCL')
        )
        
        # Create initial artifact
        ArtifactInstance.objects.create(
            expediente=exp,
            artifact_type='ART-01',
            status=ArtifactStatusEnum.COMPLETED,
            payload=payload
        )
        return exp
