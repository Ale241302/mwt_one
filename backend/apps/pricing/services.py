# Sprint 18 - T1.10: Chain-of-responsibility para resolve_client_price
# Refactorizacion del resolver de precios a cadena de responsabilidad.
from django.db.models import Q
from django.utils import timezone


def resolve_from_brand_client_pricelist(product, client, brand, date):
    """Nivel 1: lista de precios especifica por brand + client."""
    try:
        from apps.pricing.models import PriceList, PriceListItem
        today = date or timezone.now().date()
        pricelists = PriceList.objects.filter(
            Q(valid_from__lte=today),
            Q(valid_to__isnull=True) | Q(valid_to__gte=today),
            brand=brand,
            client=client,
            is_active=True,
        ).order_by('-valid_from')
        for pl in pricelists:
            item = PriceListItem.objects.filter(
                pricelist=pl, product=product
            ).first()
            if item:
                return {'price': item.unit_price, 'pricelist': pl, 'source': 'brand_client_pricelist'}
    except Exception:
        pass
    return None


def resolve_from_brand_default_pricelist(product, client, brand, date):
    """Nivel 2: lista de precios por defecto del brand (sin client especifico)."""
    try:
        from apps.pricing.models import PriceList, PriceListItem
        today = date or timezone.now().date()
        pricelists = PriceList.objects.filter(
            Q(valid_from__lte=today),
            Q(valid_to__isnull=True) | Q(valid_to__gte=today),
            brand=brand,
            client__isnull=True,
            is_active=True,
        ).order_by('-valid_from')
        for pl in pricelists:
            item = PriceListItem.objects.filter(
                pricelist=pl, product=product
            ).first()
            if item:
                return {'price': item.unit_price, 'pricelist': pl, 'source': 'brand_default_pricelist'}
    except Exception:
        pass
    return None


def resolve_from_product_master_base_price(product, client, brand, date):
    """Nivel 3 (fallback): precio base del ProductMaster."""
    try:
        if hasattr(product, 'base_price') and product.base_price is not None:
            return {'price': product.base_price, 'pricelist': None, 'source': 'product_master_base_price'}
    except Exception:
        pass
    return None


PRICE_RESOLVERS = [
    resolve_from_brand_client_pricelist,
    resolve_from_brand_default_pricelist,
    resolve_from_product_master_base_price,
]


def resolve_client_price(product, client, brand, date=None):
    """
    Chain-of-responsibility: intenta cada resolver en orden.
    Retorna el primer resultado no-None, o None si ninguno resuelve.
    """
    for resolver in PRICE_RESOLVERS:
        result = resolver(product, client, brand, date)
        if result is not None:
            return result
    return None
