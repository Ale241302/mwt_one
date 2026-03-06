"""
Sprint 5 S5-03/04: Liquidation domain services C25-C28
Ref: LOTE_SM_SPRINT5 Item 1
"""
import uuid
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from django.db import transaction

from apps.liquidations.models import Liquidation, LiquidationLine
from apps.liquidations.enums import (
    LiquidationStatus, MatchStatus, LiquidationLineConcept
)
from apps.liquidations.parsers import parse_marluvas_liquidation
from apps.expedientes.models import ArtifactInstance, EventLog

# Tolerancias configurables (con defaults)
AMOUNT_TOLERANCE_PCT = getattr(settings, "LIQUIDATION_AMOUNT_TOLERANCE_PCT", Decimal("0.01"))
AMOUNT_TOLERANCE_ABS = getattr(settings, "LIQUIDATION_AMOUNT_TOLERANCE_ABS", Decimal("5.00"))
COMMISSION_TOLERANCE_PP = getattr(settings, "LIQUIDATION_COMMISSION_TOLERANCE_PP", Decimal("0.5"))


def _create_liquidation_event(liquidation, event_type, emitted_by, payload=None):
    """Create EventLog for liquidation domain."""
    return EventLog.objects.create(
        event_type=event_type,
        aggregate_type='liquidation',
        aggregate_id=uuid.UUID(int=0),
        payload={
            'liquidation_id': liquidation.liquidation_id,
            **(payload or {}),
        },
        occurred_at=timezone.now(),
        emitted_by=emitted_by,
        correlation_id=uuid.uuid4(),
    )


def upload_liquidation(data: dict, file, period: str, user) -> Liquidation:
    """
    C25 UploadLiquidation.
    1. Valida formato período y que no haya liquidación reconciled para ese período.
    2. Crea Liquidation, guarda archivo SIEMPRE.
    3. Intenta parsear JSON.
    4. Intenta auto-match por marluvas_reference contra ART-02 consecutivos.
    5. Emite evento liquidation.received.
    """
    if Liquidation.objects.filter(
        period=period, status=LiquidationStatus.RECONCILED
    ).exists():
        raise ValueError(
            f"A reconciled liquidation already exists for period {period}."
        )

    with transaction.atomic():
        liquidation = Liquidation(period=period)
        liquidation.source_file = file

        # Intentar parsear
        try:
            lines_data = parse_marluvas_liquidation(data)
            error_msg = ""
        except Exception as e:
            lines_data = []
            error_msg = str(e)
            
        liquidation.error_log = error_msg
        liquidation.save()

        # Insertar líneas y correr auto-match
        for line_data in lines_data:
            line = LiquidationLine(liquidation=liquidation, **line_data)
            _auto_match_line(line)
            line.save()

        # Actualizar totales
        liquidation.total_lines = len(lines_data)
        liquidation.save(update_fields=["total_lines"])

        _create_liquidation_event(
            liquidation, "liquidation.received", "C25:UploadLiquidation",
            payload={"period": period},
        )
    return liquidation


def _auto_match_line(line: LiquidationLine):
    """
    Auto-match por consecutivo de proforma vs marluvas_reference.
    Premiaciones → no_match_needed automático.
    """
    if line.concept == LiquidationLineConcept.PREMIO:
        line.match_status = MatchStatus.NO_MATCH_NEEDED
        return

    matches = ArtifactInstance.objects.filter(
        artifact_type="ART-02",
        payload__consecutive__iexact=line.marluvas_reference
    )

    if matches.count() == 1:
        proforma = matches.first()
        line.matched_proforma = proforma
        line.matched_expediente = proforma.expediente
        commission_pct = proforma.payload.get("comision_pactada")
        if commission_pct:
            line.commission_pct_expected = Decimal(str(commission_pct))
        line.match_status = _evaluate_tolerance(line)
    else:
        line.match_status = MatchStatus.UNMATCHED


def _evaluate_tolerance(line: LiquidationLine) -> str:
    """Evalúa tolerancias de monto y % comisión."""
    if not line.matched_proforma:
        return MatchStatus.UNMATCHED

    proforma_amount = Decimal(
        str(line.matched_proforma.payload.get("total_amount", 0))
    )
    tolerance = max(proforma_amount * AMOUNT_TOLERANCE_PCT, AMOUNT_TOLERANCE_ABS)
    if abs(line.client_payment_amount - proforma_amount) > tolerance:
        return MatchStatus.DISCREPANCY

    if line.commission_pct_reported and line.commission_pct_expected:
        diff = abs(line.commission_pct_reported - line.commission_pct_expected)
        if diff > COMMISSION_TOLERANCE_PP:
            return MatchStatus.DISCREPANCY

    return MatchStatus.MATCHED


def manual_match_line(liquidation: Liquidation, line_id: int, proforma_id, user):
    """C26 ManualMatchLine — CEO resuelve líneas unmatched."""
    if liquidation.status not in (
        LiquidationStatus.PENDING, LiquidationStatus.IN_REVIEW
    ):
        raise ValueError(
            "Liquidation must be pending or in_review to match lines."
        )

    line = liquidation.lines.get(pk=line_id, match_status=MatchStatus.UNMATCHED)
    proforma = ArtifactInstance.objects.get(pk=proforma_id, artifact_type="ART-02")

    line.matched_proforma = proforma
    line.matched_expediente = proforma.expediente
    commission_pct = proforma.payload.get("comision_pactada")
    if commission_pct:
        line.commission_pct_expected = Decimal(str(commission_pct))
    line.match_status = _evaluate_tolerance(line)
    line.save()
    return line


def reconcile_liquidation(liquidation: Liquidation, user) -> Liquidation:
    """
    C27 ReconcileLiquidation.
    Precondición: todas las líneas concept=comision tienen
    match_status ∈ {matched, no_match_needed}.
    """
    if liquidation.status not in (
        LiquidationStatus.PENDING, LiquidationStatus.IN_REVIEW
    ):
        raise ValueError(
            "Liquidation must be pending or in_review to reconcile."
        )

    blocking_lines = liquidation.lines.filter(
        concept=LiquidationLineConcept.COMISION,
        match_status__in=[MatchStatus.UNMATCHED, MatchStatus.DISCREPANCY]
    )
    if blocking_lines.exists():
        raise ValueError(
            f"{blocking_lines.count()} commission lines are unmatched or have "
            f"discrepancies. Resolve all lines before reconciling."
        )

    with transaction.atomic():
        total = sum(l.commission_amount for l in liquidation.lines.all())
        liquidation.total_commission_amount = total
        liquidation.status = LiquidationStatus.RECONCILED
        liquidation.reconciled_at = timezone.now()
        liquidation.reconciled_by = user
        liquidation.save()

        _create_liquidation_event(
            liquidation, "liquidation.reconciled", "C27:ReconcileLiquidation",
            payload={"total_commission_amount": str(total)},
        )
    return liquidation


def dispute_liquidation(
    liquidation: Liquidation, observations: str, user
) -> Liquidation:
    """C28 DisputeLiquidation."""
    if liquidation.status not in (
        LiquidationStatus.PENDING, LiquidationStatus.IN_REVIEW
    ):
        raise ValueError(
            "Liquidation must be pending or in_review to dispute."
        )

    with transaction.atomic():
        liquidation.status = LiquidationStatus.DISPUTED
        liquidation.observations = observations
        liquidation.save(
            update_fields=["status", "observations", "updated_at"]
        )

        _create_liquidation_event(
            liquidation, "liquidation.disputed", "C28:DisputeLiquidation",
            payload={"observations": observations},
        )
    return liquidation
