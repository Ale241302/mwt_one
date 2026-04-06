"""
S23-05 — resolve_commission_rule() (Fase 0)
S23-08 — resolve_commission()
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class CommissionRuleResult:
    rule_id: str
    rule_type: str
    rule_value: Decimal
    commission_base: Optional[str]
    product_key: Optional[str]
    scope_level: str  # 'subsidiary' | 'client' | 'brand'


@dataclass
class CommissionResult:
    rule_id: str
    commission_base: str
    base_amount: Decimal
    commission_amount: Decimal
    scope_level: str


# ---------------------------------------------------------------------------
# S23-05 — resolve_commission_rule() (Fase 0 — sin cambios)
# ---------------------------------------------------------------------------

def resolve_commission_rule(
    brand_slug: str,
    product_key: Optional[str] = None,
    client_id: Optional[int] = None,
    subsidiary_id: Optional[int] = None,
) -> Optional[CommissionRuleResult]:
    """
    S23-05: Resuelve la regla de comision con cascada:
    subsidiary+product -> subsidiary default -> client+product -> client default
    -> brand+product -> brand default -> None
    """
    from apps.commercial.models import CommissionRule

    def _query(filters: dict):
        return (
            CommissionRule.objects
            .filter(is_active=True, **filters)
            .order_by('-created_at')
            .first()
        )

    # --- Nivel subsidiary ---
    if subsidiary_id is not None:
        if product_key:
            rule = _query({'subsidiary_id': subsidiary_id, 'product_key': product_key})
            if rule:
                return _build_commission_result(rule, 'subsidiary')
        rule = _query({'subsidiary_id': subsidiary_id, 'product_key__isnull': True})
        if rule:
            return _build_commission_result(rule, 'subsidiary')

    # --- Nivel client ---
    if client_id is not None:
        if product_key:
            rule = _query({'client_id': client_id, 'product_key': product_key})
            if rule:
                return _build_commission_result(rule, 'client')
        rule = _query({'client_id': client_id, 'product_key__isnull': True})
        if rule:
            return _build_commission_result(rule, 'client')

    # --- Nivel brand ---
    if product_key:
        rule = _query({
            'brand_id': brand_slug,
            'product_key': product_key,
            'client__isnull': True,
            'subsidiary__isnull': True,
        })
        if rule:
            return _build_commission_result(rule, 'brand')

    rule = _query({
        'brand_id': brand_slug,
        'product_key__isnull': True,
        'client__isnull': True,
        'subsidiary__isnull': True,
    })
    if rule:
        return _build_commission_result(rule, 'brand')

    return None


def _build_commission_result(rule, scope_level: str) -> CommissionRuleResult:
    return CommissionRuleResult(
        rule_id=str(rule.id),
        rule_type=rule.rule_type,
        rule_value=rule.rule_value,
        commission_base=rule.commission_base,
        product_key=rule.product_key,
        scope_level=scope_level,
    )


# ---------------------------------------------------------------------------
# S23-08 — resolve_commission()
# ---------------------------------------------------------------------------

def resolve_commission(
    *,
    brand_slug: str,
    sale_price: Decimal,
    product_key: Optional[str] = None,
    client_id: Optional[int] = None,
    subsidiary_id: Optional[int] = None,
    cost_price: Optional[Decimal] = None,
) -> Optional[CommissionResult]:
    """
    S23-08: Calcula la comision para un agente dado una factory_order/linea.

    - commission_base 'sale_price': usa sale_price como base.
    - commission_base 'gross_margin': usa (sale_price - cost_price) como base.
      cost_price es OBLIGATORIO si commission_base='gross_margin'.
    - ValueError si commission_base es NULL en regla tipo 'percentage'.
    - Retorna None si no hay regla aplicable.
    """
    rule_result = resolve_commission_rule(
        brand_slug=brand_slug,
        product_key=product_key,
        client_id=client_id,
        subsidiary_id=subsidiary_id,
    )

    if rule_result is None:
        return None

    # Validar commission_base si es tipo percentage
    if rule_result.rule_type == 'percentage' and rule_result.commission_base is None:
        raise ValueError(
            f"commission_base es NULL en CommissionRule {rule_result.rule_id} "
            f"(type=percentage) — DEC-S23-03 pendiente. "
            f"No se puede calcular la comision sin esta decision."
        )

    commission_base = rule_result.commission_base

    if commission_base == 'sale_price':
        base_amount = Decimal(str(sale_price))

    elif commission_base == 'gross_margin':
        if cost_price is None:
            raise ValueError(
                "cost_price es obligatorio cuando commission_base='gross_margin'. "
                "Proporciona el costo unitario del producto."
            )
        base_amount = Decimal(str(sale_price)) - Decimal(str(cost_price))
        if base_amount < Decimal('0'):
            base_amount = Decimal('0')

    elif rule_result.rule_type == 'fixed_amount':
        base_amount = Decimal('1')

    else:
        raise ValueError(
            f"commission_base invalido: '{commission_base}' en regla {rule_result.rule_id}."
        )

    if rule_result.rule_type == 'percentage':
        commission_amount = (
            base_amount * rule_result.rule_value / Decimal('100')
        ).quantize(Decimal('0.0001'))
    elif rule_result.rule_type == 'fixed_amount':
        commission_amount = rule_result.rule_value.quantize(Decimal('0.0001'))
    else:
        raise ValueError(f"rule_type invalido: '{rule_result.rule_type}'")

    return CommissionResult(
        rule_id=rule_result.rule_id,
        commission_base=commission_base or 'fixed_amount',
        base_amount=base_amount,
        commission_amount=commission_amount,
        scope_level=rule_result.scope_level,
    )
