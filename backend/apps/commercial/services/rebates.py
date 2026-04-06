"""
S23-05 — Resolvers de Rebates.

Resolvers con cascada por scope: subsidiary → client → brand.
NUNCA usar .first() sin order_by.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class RebateResult:
    """Resultado de resolución de un programa de rebate."""
    assignment_id: str
    program_id: str
    program_name: str
    rebate_type: str
    rebate_value: Decimal
    calculation_base: Optional[str]
    threshold_type: str
    # Threshold efectivo (custom del assignment si existe, si no el del programa)
    effective_threshold_amount: Optional[Decimal]
    effective_threshold_units: Optional[int]
    period_type: str
    valid_from: object
    valid_to: Optional[object]
    scope_level: str  # 'subsidiary' | 'client' | 'brand'


def resolve_rebate_assignment(
    brand_slug: str,
    client_id: Optional[int] = None,
    subsidiary_id: Optional[int] = None,
) -> Optional[RebateResult]:
    """
    S23-05: Resuelve el programa de rebate activo para un cliente/subsidiary
    usando cascada: subsidiary → client → brand.

    Retorna None si no hay ningún programa activo aplicable.
    """
    from apps.commercial.models import RebateAssignment

    # --- Nivel subsidiary ---
    if subsidiary_id is not None:
        assignment = (
            RebateAssignment.objects
            .select_related('rebate_program')
            .filter(
                is_active=True,
                subsidiary_id=subsidiary_id,
                rebate_program__brand_id=brand_slug,
                rebate_program__is_active=True,
            )
            .order_by('-created_at')
            .first()
        )
        if assignment:
            return _build_rebate_result(assignment, 'subsidiary')

    # --- Nivel client ---
    if client_id is not None:
        assignment = (
            RebateAssignment.objects
            .select_related('rebate_program')
            .filter(
                is_active=True,
                client_id=client_id,
                rebate_program__brand_id=brand_slug,
                rebate_program__is_active=True,
            )
            .order_by('-created_at')
            .first()
        )
        if assignment:
            return _build_rebate_result(assignment, 'client')

    # --- Nivel brand (sin cliente específico) ---
    assignment = (
        RebateAssignment.objects
        .select_related('rebate_program')
        .filter(
            is_active=True,
            client__isnull=True,
            subsidiary__isnull=True,
            rebate_program__brand_id=brand_slug,
            rebate_program__is_active=True,
        )
        .order_by('-created_at')
        .first()
    )
    if assignment:
        return _build_rebate_result(assignment, 'brand')

    return None


def _build_rebate_result(assignment, scope_level: str) -> RebateResult:
    """
    Construye un RebateResult desde un RebateAssignment.
    Usa threshold custom del assignment si existe; si no, el del programa.
    """
    program = assignment.rebate_program

    effective_threshold_amount = (
        assignment.custom_threshold_amount
        if assignment.custom_threshold_amount is not None
        else program.threshold_amount
    )
    effective_threshold_units = (
        assignment.custom_threshold_units
        if assignment.custom_threshold_units is not None
        else program.threshold_units
    )

    return RebateResult(
        assignment_id=str(assignment.id),
        program_id=str(program.id),
        program_name=program.name,
        rebate_type=program.rebate_type,
        rebate_value=program.rebate_value,
        calculation_base=program.calculation_base,
        threshold_type=program.threshold_type,
        effective_threshold_amount=effective_threshold_amount,
        effective_threshold_units=effective_threshold_units,
        period_type=program.period_type,
        valid_from=program.valid_from,
        valid_to=program.valid_to,
        scope_level=scope_level,
    )
