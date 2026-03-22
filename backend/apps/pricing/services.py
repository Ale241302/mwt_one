from apps.pricing.models import PriceList, PriceListItem
from apps.agreements.models import BrandClientPriceAgreement
from django.utils import timezone

def resolve_client_price(brand_id, party_type, party_id, sku, mode, currency, date=None):
    if date is None:
        date = timezone.now()

    # 1. Consultar BrandClientPriceAgreement (Override)
    agreement = BrandClientPriceAgreement.objects.filter(
        brand_id=brand_id,
        party_type=party_type,
        party_id=party_id,
        sku=sku,
        mode=mode,
        currency=currency,
        status='active',
        valid_daterange__contains=date
    ).first()

    if agreement:
        return {
            'price': agreement.override_price,
            'source': 'agreement',
            'agreement_id': agreement.id
        }

    # 2. Consultar PriceList Base
    price_list_item = PriceListItem.objects.filter(
        price_list__brand_id=brand_id,
        price_list__currency=currency,
        price_list__is_active=True,
        sku=sku
    ).filter(
        price_list__valid_from__lte=date,
        price_list__valid_to__gte=date
    ).first()

    if price_list_item:
        return {
            'price': price_list_item.price,
            'source': 'pricelist',
            'pricelist_id': price_list_item.price_list.id
        }
    
    return None
