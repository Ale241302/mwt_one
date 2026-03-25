from apps.expedientes.exceptions import CommandValidationError
from apps.agreements.models import BrandClientAgreement, PartyType
from django.utils import timezone

def handle_c3(expediente, payload):
    """Registrar Orden de Compra (ART-03) with commercial defaults (S16-04)."""
    items = payload.get('items', [])
    
    agreement = BrandClientAgreement.objects.filter(
        brand=expediente.brand,
        party_type=PartyType.SUBSIDIARY,
        party_id=expediente.client.pk,
        status='active',
        valid_daterange__contains=timezone.now()
    ).first()

    for item in items:
        if agreement:
            if expediente.mode == 'COMISION' and 'commission' not in item:
                item['commission'] = float(agreement.commission)
            elif expediente.mode == 'IMPORT' and 'standard_cost' not in item:
                item['standard_cost'] = float(agreement.standard_cost)

    return {"message": "Purchase Order registered with defaults applied", "item_count": len(items)}
