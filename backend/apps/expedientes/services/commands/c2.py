from apps.expedientes.exceptions import CommandValidationError
from apps.productos.models import Product
from apps.agreements.models import BrandClientAgreement, PartyType
from django.utils import timezone

def handle_c2(expediente, payload, env=None):
    """Registrar Proforma (ART-02) with commercial defaults (S16-04)."""
    items = payload.get('items', [])
    
    # S16-04: Lookup commercial defaults
    agreement = BrandClientAgreement.objects.filter(
        brand=expediente.brand,
        party_type=PartyType.SUBSIDIARY, # Or based on client.type if available
        party_id=expediente.client.pk,
        status='active',
        valid_daterange__contains=timezone.now()
    ).first()

    for item in items:
        sku = item.get('sku')
        if not sku:
            raise CommandValidationError("SKU is required in proforma items")
        
        if expediente.brand:
            product = Product.objects.filter(sku_base=sku, brand_id=expediente.brand_id).first()
            if not product:
                raise CommandValidationError(f"SKU {sku} not found in Product catalog for this brand")

        # Apply defaults if missing in payload
        if agreement:
            if expediente.mode == 'COMISION' and 'commission' not in item:
                item['commission'] = float(agreement.commission)
            elif expediente.mode == 'IMPORT' and 'standard_cost' not in item:
                item['standard_cost'] = float(agreement.standard_cost)

    return {"message": "Proforma registered with defaults applied", "item_count": len(items)}
