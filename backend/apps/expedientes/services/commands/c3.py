from apps.expedientes.exceptions import CommandValidationError
from apps.agreements.models import BrandClientAgreement, PartyType
from django.utils import timezone

import logging
logger = logging.getLogger(__name__)

def handle_c3(expediente, payload, env=None):
    """
    Registrar Orden de Compra (ART-01).
    S21: Maneja tanto payloads simples (oc_number) como complejos (items con defaults).
    """
    logger.info(f"Executing C3 for Expediente {expediente.expediente_id}. Payload: {payload}")
    
    # Soporte para campos de ArtifactModal
    oc_number = payload.get('oc_number')
    notes = payload.get('notes')
    
    items = payload.get('items', [])
    
    agreement = BrandClientAgreement.objects.filter(
        brand=expediente.brand,
        party_type=PartyType.SUBSIDIARY,
        party_id=expediente.client.pk,
        status='active',
        valid_daterange__contains=timezone.now()
    ).first()

    processed_count = 0
    if items:
        for item in items:
            if agreement:
                if expediente.mode == 'COMISION' and 'commission' not in item:
                    item['commission'] = float(agreement.commission)
                elif expediente.mode == 'IMPORT' and 'standard_cost' not in item:
                    item['standard_cost'] = float(agreement.standard_cost)
            processed_count += 1

    return {
        "message": "Purchase Order registered",
        "oc_number": oc_number,
        "items_processed": processed_count,
        "applied_agreement": agreement.pk if agreement else None
    }
