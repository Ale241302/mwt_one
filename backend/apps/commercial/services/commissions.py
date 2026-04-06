"""
S23-05 — Resolver de CommissionRule.

Resuelve la regla de comisión activa para un scope dado.
NUNCA usar .first() sin order_by.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class CommissionRuleResult:
    """Resultado de resolución de una regla de comisión."""
    rule_id: str
    rule_type: str
    rule_value: Decimal
    commission_base: Optional[str]
    scope_level: str   # 'subsidiary' | 'client' | 'brand'
    product_key: Optional[str]


def resolve_commission_rule(
    brand_slug: Optional[str] = None,
    client_id: Optional[int] = None,
    subsidiary_id: Optional[int] = None,
    product_key: Optional[str] = None,
) -> Optional[CommissionRuleResult]:
    """
    S23-05: Resuelve la regla de comisión activa.

    Cascada de resolución por scope:
      1. subsidiary + product_key (si ambos provistos)
      2. subsidiary default
      3. client + product_key
      4. client default
      5. brand + product_key
      6. brand default

    Retorna None si no existe ninguna regla aplicable.
    """
    from apps.commercial.models import CommissionRule

    def _query(filters: dict) -> Optional[CommissionRule]:
        return (
            CommissionRule.objects
            .filter(is_active=True, **filters)
            .order_by('-created_at')
            .first()
        )

    # --- Scope: subsidiary ---
    if subsidiary_id is not None:
        # Con product_key
        if product_key:
            rule = _query({'subsidiary_id': subsidiary_id, 'product_key': product_key})
            if rule:
                return _build_commission_result(rule, 'subsidiary')
        # Default
        rule = _query({'subsidiary_id': subsidiary_id, 'product_key__isnull': True})
        if rule:
            return _build_commission_result(rule, 'subsidiary')

    # --- Scope: client ---
    if client_id is not None:
        if product_key:
            rule = _query({'client_id': client_id, 'product_key': product_key})
            if rule:
                return _build_commission_result(rule, 'client')
        rule = _query({'client_id': client_id, 'product_key__isnull': True})
        if rule:
            return _build_commission_result(rule, 'client')

    # --- Scope: brand ---
    if brand_slug is not None:
        if product_key:
            rule = _query({'brand_id': brand_slug, 'product_key': product_key})
            if rule:
                return _build_commission_result(rule, 'brand')
        rule = _query({'brand_id': brand_slug, 'product_key__isnull': True})
        if rule:
            return _build_commission_result(rule, 'brand')

    return None


def _build_commission_result(rule, scope_level: str) -> CommissionRuleResult:
    return CommissionRuleResult(
        rule_id=str(rule.id),
        rule_type=rule.rule_type,
        rule_value=rule.rule_value,
        commission_base=rule.commission_base,
        scope_level=scope_level,
        product_key=rule.product_key,
    )
