"""
S23-05 — Resolvers de Rebates (Fase 0).
S23-06 — calculate_rebate_accrual()
S23-07 — liquidate_rebates() helper
S23-07b — approve_rebate_liquidation()
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.utils import timezone

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dataclasses de resultado (Fase 0 — se mantienen)
# ---------------------------------------------------------------------------

@dataclass
class RebateResult:
    assignment_id: str
    program_id: str
    program_name: str
    rebate_type: str
    rebate_value: Decimal
    calculation_base: Optional[str]
    threshold_type: str
    effective_threshold_amount: Optional[Decimal]
    effective_threshold_units: Optional[int]
    period_type: str
    valid_from: object
    valid_to: Optional[object]
    scope_level: str  # 'subsidiary' | 'client' | 'brand'


@dataclass
class AccrualResult:
    ledger_id: str
    proforma_id: str
    qualifying_amount: Decimal
    qualifying_units: int
    accrued_amount: Decimal
    threshold_met: bool
    was_idempotent: bool  # True si la entry ya existia


# ---------------------------------------------------------------------------
# S23-05 — Resolvers (Fase 0 — sin cambios)
# ---------------------------------------------------------------------------

def resolve_rebate_assignment(
    brand_slug: str,
    client_id: Optional[int] = None,
    subsidiary_id: Optional[int] = None,
) -> Optional[RebateResult]:
    from apps.commercial.models import RebateAssignment

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


# ---------------------------------------------------------------------------
# S23-06 — calculate_rebate_accrual()
# ---------------------------------------------------------------------------

def calculate_rebate_accrual(
    *,
    ledger_id: str,
    proforma_id: str,
    proforma_lines: list[dict],
    proforma_date: date,
    qualified_product_keys: Optional[list[str]] = None,
) -> AccrualResult:
    """
    S23-06: Calcula y registra el accrual de rebate al cerrar una proforma.

    - Todo dentro de transaction.atomic() + select_for_update() en el ledger.
    - Idempotente: si ya existe la entry (unique_together ledger+proforma_id),
      retorna el resultado existente sin modificar el ledger.
    - Recalcula totales con aggregate() desde entries — NUNCA F() incremental.

    proforma_lines: lista de dicts con claves:
        product_key (str), quantity (int), unit_price (Decimal), base_list_price (Decimal)
    qualified_product_keys: si None, todas las lineas califican.
    """
    from apps.commercial.models import (
        RebateAccrualEntry,
        RebateLedger,
        LedgerStatus,
        CalculationBase,
    )

    with transaction.atomic():
        # Lock del ledger — critico para concurrencia
        try:
            ledger = (
                RebateLedger.objects
                .select_for_update()
                .select_related('rebate_assignment__rebate_program')
                .get(id=ledger_id)
            )
        except RebateLedger.DoesNotExist:
            raise ValueError(f"RebateLedger {ledger_id} no existe.")

        if ledger.status not in (LedgerStatus.ACCRUING,):
            raise ValueError(
                f"No se puede accruar en ledger con status '{ledger.status}'. "
                f"Solo se permite en status 'accruing'."
            )

        program = ledger.rebate_assignment.rebate_program

        # Filtrar lineas calificables
        if qualified_product_keys is not None:
            lines = [
                l for l in proforma_lines
                if l['product_key'] in qualified_product_keys
            ]
        else:
            lines = proforma_lines

        # Calcular montos
        qualifying_amount = _calculate_qualifying_amount(lines, program.calculation_base)
        qualifying_units = _calculate_qualifying_units(lines)

        # Calcular rebate accrued
        accrued_amount = _calculate_accrued_amount(
            qualifying_amount=qualifying_amount,
            qualifying_units=qualifying_units,
            rebate_type=program.rebate_type,
            rebate_value=program.rebate_value,
        )

        # Intentar crear la entry — idempotencia via IntegrityError
        try:
            RebateAccrualEntry.objects.create(
                ledger=ledger,
                proforma_id=proforma_id,
                qualifying_amount=qualifying_amount,
                qualifying_units=qualifying_units,
                accrued_amount=accrued_amount,
                proforma_date=proforma_date,
            )
            was_idempotent = False
        except IntegrityError:
            existing = RebateAccrualEntry.objects.get(
                ledger=ledger,
                proforma_id=proforma_id,
            )
            return AccrualResult(
                ledger_id=str(ledger.id),
                proforma_id=proforma_id,
                qualifying_amount=existing.qualifying_amount,
                qualifying_units=existing.qualifying_units,
                accrued_amount=existing.accrued_amount,
                threshold_met=ledger.threshold_met,
                was_idempotent=True,
            )

        # Recalcular totales del ledger con aggregate() desde entries
        totals = RebateAccrualEntry.objects.filter(ledger=ledger).aggregate(
            total_qualifying_amount=Sum('qualifying_amount'),
            total_qualifying_units=Sum('qualifying_units'),
            total_accrued_amount=Sum('accrued_amount'),
        )

        ledger.qualifying_amount = totals['total_qualifying_amount'] or Decimal('0')
        ledger.qualifying_units = totals['total_qualifying_units'] or 0
        ledger.accrued_amount = totals['total_accrued_amount'] or Decimal('0')

        # Evaluar threshold
        ledger.threshold_met = _evaluate_threshold(
            ledger=ledger,
            program=program,
        )

        ledger.save(update_fields=[
            'qualifying_amount',
            'qualifying_units',
            'accrued_amount',
            'threshold_met',
            'updated_at',
        ])

    return AccrualResult(
        ledger_id=str(ledger.id),
        proforma_id=proforma_id,
        qualifying_amount=qualifying_amount,
        qualifying_units=qualifying_units,
        accrued_amount=accrued_amount,
        threshold_met=ledger.threshold_met,
        was_idempotent=was_idempotent,
    )


def _calculate_qualifying_amount(lines: list[dict], calculation_base: Optional[str]) -> Decimal:
    """
    S23-06: Calcula el monto calificable segun calculation_base.
    - 'invoiced'   -> usar unit_price de cada linea
    - 'list_price' -> usar base_list_price de cada linea
    - NULL         -> ValueError (DEC-S23-01 pendiente)
    """
    if calculation_base is None:
        raise ValueError(
            "calculation_base es NULL — DEC-S23-01 pendiente. "
            "No se puede calcular qualifying_amount sin esta decision."
        )

    total = Decimal('0')
    for line in lines:
        qty = Decimal(str(line['quantity']))
        if calculation_base == 'invoiced':
            price = Decimal(str(line['unit_price']))
        elif calculation_base == 'list_price':
            price = Decimal(str(line['base_list_price']))
        else:
            raise ValueError(f"calculation_base invalido: '{calculation_base}'")
        total += qty * price

    return total


def _calculate_qualifying_units(lines: list[dict]) -> int:
    """S23-06: Suma simple de quantity en lineas calificables."""
    return sum(int(line['quantity']) for line in lines)


def _calculate_accrued_amount(
    *,
    qualifying_amount: Decimal,
    qualifying_units: int,
    rebate_type: str,
    rebate_value: Decimal,
) -> Decimal:
    if rebate_type == 'percentage':
        return (qualifying_amount * rebate_value / Decimal('100')).quantize(Decimal('0.0001'))
    elif rebate_type == 'fixed_amount':
        return (Decimal(str(qualifying_units)) * rebate_value).quantize(Decimal('0.0001'))
    else:
        raise ValueError(f"rebate_type invalido: '{rebate_type}'")


def _evaluate_threshold(*, ledger, program) -> bool:
    """Evalua si se alcanzo el threshold usando valores efectivos del assignment."""
    assignment = ledger.rebate_assignment

    threshold_type = program.threshold_type
    if threshold_type == 'none':
        return True

    if threshold_type == 'amount':
        effective = (
            assignment.custom_threshold_amount
            if assignment.custom_threshold_amount is not None
            else program.threshold_amount
        )
        if effective is None:
            return False
        return ledger.qualifying_amount >= effective

    if threshold_type == 'units':
        effective = (
            assignment.custom_threshold_units
            if assignment.custom_threshold_units is not None
            else program.threshold_units
        )
        if effective is None:
            return False
        return ledger.qualifying_units >= effective

    return False


# ---------------------------------------------------------------------------
# S23-07b — approve_rebate_liquidation()
# ---------------------------------------------------------------------------

VALID_LIQUIDATION_TYPES = ('credit_note', 'bank_transfer', 'product_credit')


def approve_rebate_liquidation(
    *,
    ledger_id: str,
    liquidation_type: str,
    approved_by_user,
) -> None:
    """
    S23-07b: Aprueba la liquidacion de un ledger en status 'pending_review'.

    - Valida status == 'pending_review' y liquidation_type valido.
    - Setea liquidated_at y liquidated_by.
    - Genera EventLog(event_type='rebate.liquidated') — NO ConfigChangeLog.
    """
    from apps.commercial.models import RebateLedger, LedgerStatus
    from apps.audit.models import EventLog

    if liquidation_type not in VALID_LIQUIDATION_TYPES:
        raise ValueError(
            f"liquidation_type '{liquidation_type}' no es valido. "
            f"Opciones: {VALID_LIQUIDATION_TYPES}"
        )

    with transaction.atomic():
        try:
            ledger = (
                RebateLedger.objects
                .select_for_update()
                .get(id=ledger_id)
            )
        except RebateLedger.DoesNotExist:
            raise ValueError(f"RebateLedger {ledger_id} no existe.")

        if ledger.status != LedgerStatus.PENDING_REVIEW:
            raise ValueError(
                f"Solo se puede aprobar un ledger en 'pending_review'. "
                f"Estado actual: '{ledger.status}'."
            )

        ledger.status = LedgerStatus.LIQUIDATED
        ledger.liquidation_type = liquidation_type
        ledger.liquidated_at = timezone.now()
        ledger.liquidated_by = approved_by_user
        ledger.save(update_fields=[
            'status',
            'liquidation_type',
            'liquidated_at',
            'liquidated_by',
            'updated_at',
        ])

        EventLog.objects.create(
            event_type='rebate.liquidated',
            action_source='approve_rebate_liquidation',
            actor=approved_by_user,
            payload={
                'ledger_id': str(ledger.id),
                'liquidation_type': liquidation_type,
                'accrued_amount': str(ledger.accrued_amount),
                'assignment_id': str(ledger.rebate_assignment_id),
            },
            related_model='RebateLedger',
            related_id=str(ledger.id),
        )
