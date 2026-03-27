# Sprint 18 - T1.7: Actualizar C1 con campos nuevos (brand_sku, incoterms, purchase_order_number)
# Backward compatible: si no vienen los campos nuevos, C1 funciona igual.
from django.db import transaction


def handle_c1_s18_extensions(expediente, product_lines_data, user, **kwargs):
    """
    Extension de C1 para Sprint 18.
    Acepta product_lines con brand_sku opcional + auto-resolucion de precio.
    Acepta incoterms y purchase_order_number opcionales.
    """
    from apps.expedientes.models import ExpedienteProductLine
    from apps.pricing.services import resolve_client_price
    from django.utils import timezone

    incoterms = kwargs.get('incoterms')
    purchase_order_number = kwargs.get('purchase_order_number')

    if incoterms and not expediente.incoterms:
        expediente.incoterms = incoterms
        expediente.save(update_fields=['incoterms'])

    if purchase_order_number and not expediente.purchase_order_number:
        expediente.purchase_order_number = purchase_order_number
        expediente.save(update_fields=['purchase_order_number'])

    with transaction.atomic():
        for line_data in product_lines_data:
            brand_sku_id = line_data.pop('brand_sku', None)
            product = line_data['product']
            line = ExpedienteProductLine.objects.filter(
                expediente=expediente, product=product
            ).first()

            if line and brand_sku_id:
                try:
                    from apps.brands.models import BrandSKU
                    brand_sku = BrandSKU.objects.get(pk=brand_sku_id)
                    line.brand_sku = brand_sku

                    # Auto-resolver precio via chain-of-responsibility
                    result = resolve_client_price(
                        product=product,
                        client=expediente.client,
                        brand=expediente.brand,
                        date=timezone.now().date(),
                    )
                    if result:
                        line.pricelist_used = result.get('pricelist')
                        line.base_price = result.get('price')
                        if result.get('pricelist'):
                            line.price_source = 'pricelist'

                    line.save(update_fields=['brand_sku', 'pricelist_used', 'base_price', 'price_source'])
                except Exception:
                    pass
