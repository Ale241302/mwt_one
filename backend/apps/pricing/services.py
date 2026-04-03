# Sprint 18 - T1.10: Chain-of-responsibility para resolve_client_price
# Sprint 22 - S22-05/06/07: Waterfall v2 + activate_pricelist + validate_moq
from decimal import Decimal
from django.db.models import Q, Min
from django.utils import timezone


# -------------------------------------------------------------------
# Helpers internos
# -------------------------------------------------------------------

def _resolve_grade_constraints(brand_sku_id):
    """
    Retorna los grade constraints del BrandSKU desde versiones activas.
    Siempre viene del Grade activo independientemente de la fuente del precio.
    Returns dict con: grade_moq, size_multipliers, grade_pricelist_version
    o None si no hay grade activo.
    """
    try:
        from apps.pricing.models import PriceListGradeItem
        grade = (
            PriceListGradeItem.objects
            .filter(
                brand_sku_id=brand_sku_id,
                pricelist_version__is_active=True,
            )
            .select_related('pricelist_version')
            .order_by('-pricelist_version__activated_at')
            .first()
        )
        if grade:
            return {
                'grade_moq': grade.moq_total,
                'size_multipliers': grade.size_multipliers,
                'grade_pricelist_version': grade.pricelist_version_id,
            }
    except Exception:
        pass
    return None


def _apply_early_payment(base_price, client_subsidiary_id, brand_id, payment_days):
    """
    Aplica descuento de pronto pago si hay EarlyPaymentPolicy activa.
    Busca el tier con payment_days >= payment_days solicitado (mayor descuento).
    Returns (final_price, discount_pct_applied)
    """
    if not payment_days:
        return base_price, Decimal('0')
    try:
        from apps.pricing.models import EarlyPaymentTier
        tier = (
            EarlyPaymentTier.objects
            .filter(
                policy__client_subsidiary_id=client_subsidiary_id,
                policy__brand_id=brand_id,
                policy__is_active=True,
                payment_days__gte=payment_days,
            )
            .order_by('payment_days')  # el menor >= dias solicitados
            .first()
        )
        if tier:
            discount = Decimal(str(tier.discount_pct)) / Decimal('100')
            final_price = base_price * (1 - discount)
            return final_price.quantize(Decimal('0.0001')), tier.discount_pct
    except Exception:
        pass
    return base_price, Decimal('0')


# -------------------------------------------------------------------
# resolve_client_price v2 — waterfall de 5 pasos
# Backward compatible: llamada sin nuevos params = comportamiento v1
# -------------------------------------------------------------------

def resolve_client_price(
    product,
    client,
    brand,
    date=None,
    # Nuevos params v2 (todos opcionales para backward compat)
    brand_sku_id=None,
    client_subsidiary_id=None,
    payment_days=None,
    skip_cache=False,
):
    """
    Waterfall de resolución de precio v2.

    Paso 0: CPA cached_client_price   (skip si skip_cache=True)
    Paso 1: BCPA override
    Paso 2A: PriceListGradeItem        (MIN de versiones activas)
    Paso 2B: PriceListItem S14         (valid_from/valid_to, SIN is_active)
    Paso 3: Manual (product base_price)
    Post:  Descuento pronto pago si hay EarlyPaymentPolicy activa

    Returns dict completo:
      price, source, pricelist_version, discount_applied,
      base_price, grade_moq, size_multipliers, grade_pricelist_version

    NOTA: grade_moq, size_multipliers y grade_pricelist_version
    NUNCA deben exponerse por portal (usar PricingPortalSerializer).
    """

    # --- Paso 0: CPA cache ---
    if brand_sku_id and client_subsidiary_id and not skip_cache:
        try:
            from apps.pricing.models import ClientProductAssignment
            cpa = ClientProductAssignment.objects.filter(
                brand_sku_id=brand_sku_id,
                client_subsidiary_id=client_subsidiary_id,
                is_active=True,
                cached_client_price__isnull=False,
            ).first()
            if cpa:
                grade_info = _resolve_grade_constraints(brand_sku_id) or {}
                return {
                    'price': cpa.cached_client_price,
                    'source': 'assignment',
                    'pricelist_version': cpa.cached_pricelist_version_id,
                    'discount_applied': Decimal('0'),
                    'base_price': cpa.cached_base_price,
                    'grade_moq': grade_info.get('grade_moq'),
                    'size_multipliers': grade_info.get('size_multipliers'),
                    'grade_pricelist_version': grade_info.get('grade_pricelist_version'),
                }
        except Exception:
            pass

    # --- Paso 1: BCPA (Brand-Client Price Agreement) override ---
    # Usa la cadena original de S18 para brand_client_pricelist
    result_s18 = None
    try:
        result_s18 = resolve_from_brand_client_pricelist(product, client, brand, date)
    except Exception:
        pass
    if result_s18:
        grade_info = _resolve_grade_constraints(brand_sku_id) or {} if brand_sku_id else {}
        price = result_s18['price']
        final_price, discount = _apply_early_payment(
            price, client_subsidiary_id, getattr(brand, 'id', None), payment_days
        ) if client_subsidiary_id and brand else (price, Decimal('0'))
        return {
            'price': final_price,
            'source': 'agreement',
            'pricelist_version': None,
            'discount_applied': discount,
            'base_price': price,
            'grade_moq': grade_info.get('grade_moq'),
            'size_multipliers': grade_info.get('size_multipliers'),
            'grade_pricelist_version': grade_info.get('grade_pricelist_version'),
        }

    # --- Paso 2A: PriceListGradeItem — MIN de versiones activas ---
    if brand_sku_id:
        try:
            from apps.pricing.models import PriceListGradeItem
            grade_item = (
                PriceListGradeItem.objects
                .filter(
                    brand_sku_id=brand_sku_id,
                    pricelist_version__is_active=True,
                )
                .order_by('unit_price_usd')
                .select_related('pricelist_version')
                .first()
            )
            if grade_item:
                price = grade_item.unit_price_usd
                brand_id = getattr(brand, 'id', None)
                final_price, discount = _apply_early_payment(
                    price, client_subsidiary_id, brand_id, payment_days
                ) if client_subsidiary_id and brand_id else (price, Decimal('0'))
                return {
                    'price': final_price,
                    'source': 'pricelist_grade',
                    'pricelist_version': grade_item.pricelist_version_id,
                    'discount_applied': discount,
                    'base_price': price,
                    'grade_moq': grade_item.moq_total,
                    'size_multipliers': grade_item.size_multipliers,
                    'grade_pricelist_version': grade_item.pricelist_version_id,
                }
        except Exception:
            pass

    # --- Paso 2B: PriceListItem S14 legacy (valid_from/valid_to, sin is_active) ---
    try:
        from apps.pricing.models import PriceList, PriceListItem
        today = date or timezone.now().date()
        legacy_pls = PriceList.objects.filter(
            Q(valid_from__lte=today),
            Q(valid_to__isnull=True) | Q(valid_to__gte=today),
            brand=brand,
            # NO filtrar por is_active — solo por vigencia de fechas (norma S22)
        ).order_by('-valid_from')
        for pl in legacy_pls:
            item = PriceListItem.objects.filter(
                price_list=pl, sku=getattr(product, 'sku', str(product))
            ).first()
            if item:
                price = item.price
                brand_id = getattr(brand, 'id', None)
                final_price, discount = _apply_early_payment(
                    price, client_subsidiary_id, brand_id, payment_days
                ) if client_subsidiary_id and brand_id else (price, Decimal('0'))
                return {
                    'price': final_price,
                    'source': 'pricelist_legacy',
                    'pricelist_version': None,
                    'discount_applied': discount,
                    'base_price': price,
                    'grade_moq': None,
                    'size_multipliers': None,
                    'grade_pricelist_version': None,
                }
    except Exception:
        pass

    # --- Paso 3: Manual — precio base del producto ---
    try:
        if hasattr(product, 'base_price') and product.base_price is not None:
            price = product.base_price
            brand_id = getattr(brand, 'id', None)
            final_price, discount = _apply_early_payment(
                price, client_subsidiary_id, brand_id, payment_days
            ) if client_subsidiary_id and brand_id else (price, Decimal('0'))
            return {
                'price': final_price,
                'source': 'manual',
                'pricelist_version': None,
                'discount_applied': discount,
                'base_price': price,
                'grade_moq': None,
                'size_multipliers': None,
                'grade_pricelist_version': None,
            }
    except Exception:
        pass

    return None


# -------------------------------------------------------------------
# S18 legacy resolvers — se mantienen para backward compat
# -------------------------------------------------------------------

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
                price_list=pl, sku=getattr(product, 'sku', str(product))
            ).first()
            if item:
                return {'price': item.price, 'pricelist': pl, 'source': 'brand_client_pricelist'}
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
                price_list=pl, sku=getattr(product, 'sku', str(product))
            ).first()
            if item:
                return {'price': item.price, 'pricelist': pl, 'source': 'brand_default_pricelist'}
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


# -------------------------------------------------------------------
# S22-06: activate_pricelist()
# -------------------------------------------------------------------

def activate_pricelist(version_id, force=False, activated_by=None):
    """
    Activa una PriceListVersion.

    Lógica de extinción:
    - Una versión previa se extingue SOLO si para TODOS sus SKUs solapados
      la nueva versión tiene precio <=.
    - Si al menos 1 SKU previo es más barato → la versión previa vive.
    - force=True extingue todo sin evaluar.
    - EventLog obligatorio al completar.

    Returns: dict con versiones_extinguidas, skus_solapados
    """
    from apps.pricing.models import PriceListVersion, PriceListGradeItem, DeactivationReason
    from django.utils import timezone

    new_version = PriceListVersion.objects.get(pk=version_id)
    brand_id = new_version.brand_id

    # SKUs de la nueva versión
    new_items = {
        item.reference_code: item.unit_price_usd
        for item in PriceListGradeItem.objects.filter(pricelist_version=new_version)
    }

    # Versiones activas del mismo brand (excluyendo la nueva)
    active_versions = PriceListVersion.objects.filter(
        brand_id=brand_id,
        is_active=True,
    ).exclude(pk=version_id)

    extinguished = []
    kept_alive = []

    for old_version in active_versions:
        if force:
            old_version.is_active = False
            old_version.deactivated_at = timezone.now()
            old_version.deactivation_reason = DeactivationReason.SUPERSEDED
            old_version.save(update_fields=['is_active', 'deactivated_at', 'deactivation_reason'])
            extinguished.append(old_version.pk)
            continue

        # Evaluar solapamiento
        old_items = {
            item.reference_code: item.unit_price_usd
            for item in PriceListGradeItem.objects.filter(pricelist_version=old_version)
        }
        overlapping_codes = set(old_items.keys()) & set(new_items.keys())

        if not overlapping_codes:
            # Sin solapamiento — la versión vieja sobrevive
            kept_alive.append(old_version.pk)
            continue

        # Verificar si la nueva tiene precio <= para TODOS los solapados
        new_is_cheaper_or_equal_everywhere = all(
            new_items[code] <= old_items[code]
            for code in overlapping_codes
        )

        if new_is_cheaper_or_equal_everywhere:
            old_version.is_active = False
            old_version.deactivated_at = timezone.now()
            old_version.deactivation_reason = DeactivationReason.PRICE_DECREASE
            old_version.save(update_fields=['is_active', 'deactivated_at', 'deactivation_reason'])
            extinguished.append(old_version.pk)
        else:
            kept_alive.append(old_version.pk)

    # Activar la nueva versión
    new_version.is_active = True
    new_version.activated_at = timezone.now()
    new_version.save(update_fields=['is_active', 'activated_at'])

    # EventLog
    try:
        from apps.audit.models import EventLog
        EventLog.objects.create(
            event_type='pricelist_activated',
            description=(
                f"PriceListVersion {version_id} activada para brand {brand_id}. "
                f"Extinguidas: {extinguished}. Sobrevivientes: {kept_alive}."
            ),
            created_by_id=activated_by,
        )
    except Exception:
        pass

    # Disparar recálculo Celery (S22-09)
    try:
        from apps.pricing.tasks import recalculate_assignments_for_brand
        recalculate_assignments_for_brand.delay(brand_id)
    except Exception:
        pass

    return {
        'version_id': version_id,
        'extinguished': extinguished,
        'kept_alive': kept_alive,
        'new_items_count': len(new_items),
    }


# -------------------------------------------------------------------
# S22-07: validate_moq()
# -------------------------------------------------------------------

def validate_moq(brand_sku_id, client_subsidiary_id, quantities_by_size):
    """
    Valida MOQ usando size_multipliers del Grade activo.
    El MOQ es independiente de la fuente del precio.

    quantities_by_size: dict {talla: cantidad} ej. {'33': 2, '34': 1}

    Returns dict:
      valid: bool
      warnings: list de {size, qty, min_qty, message}
      errors: list de {message}
      grade_moq: int (MOQ total del grade)
      total_qty: int
    """
    warnings = []
    errors = []

    grade_info = _resolve_grade_constraints(brand_sku_id)

    if not grade_info or not grade_info.get('size_multipliers'):
        # Sin grade activo — no se puede validar MOQ, se deja pasar
        return {
            'valid': True,
            'warnings': [],
            'errors': [],
            'grade_moq': None,
            'total_qty': sum(quantities_by_size.values()) if quantities_by_size else 0,
        }

    size_multipliers = grade_info['size_multipliers']
    grade_moq = grade_info['grade_moq']
    total_qty = 0

    for size, qty in quantities_by_size.items():
        size_str = str(size)
        qty = int(qty)
        total_qty += qty

        min_qty = size_multipliers.get(size_str) or size_multipliers.get(size)
        if min_qty is not None and qty > 0 and qty < int(min_qty):
            warnings.append({
                'size': size_str,
                'qty': qty,
                'min_qty': int(min_qty),
                'message': f"Talla {size_str}: cantidad {qty} es menor al mínimo por talla ({min_qty})",
            })

    # ERROR si suma total < grade_moq — bloquea confirmación C5
    if grade_moq and total_qty < grade_moq:
        errors.append({
            'message': (
                f"Cantidad total ({total_qty}) es menor al MOQ del grade ({grade_moq}). "
                "No se puede confirmar el pedido."
            ),
        })

    return {
        'valid': len(errors) == 0,
        'warnings': warnings,
        'errors': errors,
        'grade_moq': grade_moq,
        'total_qty': total_qty,
    }
