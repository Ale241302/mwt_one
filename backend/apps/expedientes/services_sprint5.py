"""
Sprint 5 S5-05/07/08: Additional expediente services
- S5-05: ART-12 Nota Compensación (C29)
- S5-07: ART-19 RouteHistoricalStats auto-suggest
- S5-08: ART-19 Tracking Links + Updates Feed (C36)
"""
import uuid
from decimal import Decimal
from django.db import transaction
from django.db.models import Count, Avg
from django.utils import timezone

from apps.expedientes.models import (
    Expediente, ArtifactInstance, EventLog, LogisticsOption,
)


# ──────────────────────────────────────────────
# S5-05: C29 RegisterCompensation (ART-12 Nota Compensación)
# ──────────────────────────────────────────────

def register_compensation(expediente: Expediente, payload: dict, user) -> ArtifactInstance:
    """
    C29 RegisterCompensation — CEO-only.
    Crea ArtifactInstance type ART-12.
    Voidable via C20 (VoidArtifact ya existente).
    """
    if not user.is_superuser:
        raise PermissionError("Only CEO can register compensation notes.")

    with transaction.atomic():
        artifact = ArtifactInstance.objects.create(
            expediente=expediente,
            artifact_type="ART-12",
            payload={
                "amount": str(payload.get("amount", 0)),
                "currency": payload.get("currency", "USD"),
                "reason": payload.get("reason", ""),
                "beneficiary": payload.get("beneficiary", ""),
                "reference": payload.get("reference", ""),
                "notes": payload.get("notes", ""),
            },
            status="completed",
        )

        EventLog.objects.create(
            event_type="compensation.registered",
            aggregate_type="expediente",
            aggregate_id=expediente.expediente_id,
            payload={
                "artifact_id": str(artifact.artifact_id),
                "amount": str(payload.get("amount", 0)),
            },
            occurred_at=timezone.now(),
            emitted_by="C29:RegisterCompensation",
            correlation_id=uuid.uuid4(),
        )

    return artifact


# ──────────────────────────────────────────────
# S5-07: Logistics Route Historical Stats
# ──────────────────────────────────────────────

def get_logistics_suggestions(expediente: Expediente) -> dict:
    """
    GET /api/expedientes/{id}/logistics-suggestions/
    Requiere >=5 expedientes cerrados con ART-19 completada.
    Retorna sugerencias rankeadas por frecuencia, costo promedio, y días.
    """
    # Filtrar expedientes cerrados con al menos un LogisticsOption seleccionado
    closed_expedientes = Expediente.objects.filter(status="CERRADO")
    selected_options = LogisticsOption.objects.filter(
        artifact_instance__expediente__in=closed_expedientes,
        is_selected=True,
    )

    if selected_options.count() < 5:
        return {
            "suggestions": [],
            "message": "Insufficient historical data (minimum 5 completed routes required).",
            "count": selected_options.count(),
        }

    # Agrupar por carrier + mode + route
    stats = (
        selected_options
        .values("carrier", "mode", "route")
        .annotate(
            frequency=Count("id"),
            avg_cost=Avg("estimated_cost"),
            avg_days=Avg("estimated_days"),
        )
        .order_by("-frequency", "avg_cost", "avg_days")
    )

    suggestions = [
        {
            "carrier": s["carrier"],
            "mode": s["mode"],
            "route": s["route"],
            "frequency": s["frequency"],
            "avg_cost": str(s["avg_cost"]) if s["avg_cost"] else None,
            "avg_days": float(s["avg_days"]) if s["avg_days"] else None,
        }
        for s in stats[:10]  # top 10
    ]

    return {
        "suggestions": suggestions,
        "message": f"Based on {selected_options.count()} historical routes.",
        "count": len(suggestions),
    }


# ──────────────────────────────────────────────
# S5-08: C36 AddShipmentUpdate (manual tracking updates)
# ──────────────────────────────────────────────

def add_shipment_update(expediente: Expediente, payload: dict, user) -> ArtifactInstance:
    """
    C36 AddShipmentUpdate — manual tracking update.
    Appends update entry to ART-05 payload.updates array.
    If ART-05 doesn't exist, creates one with the update.
    """
    art05 = ArtifactInstance.objects.filter(
        expediente=expediente,
        artifact_type="ART-05",
        status="completed",
    ).order_by("-created_at").first()

    update_entry = {
        "timestamp": timezone.now().isoformat(),
        "status": payload.get("status", ""),
        "location": payload.get("location", ""),
        "notes": payload.get("notes", ""),
        "source": "manual",
    }

    with transaction.atomic():
        if art05:
            # Append update to existing payload
            current_payload = art05.payload or {}
            updates = current_payload.get("updates", [])
            updates.append(update_entry)
            current_payload["updates"] = updates

            # Also update tracking_url if provided
            if payload.get("tracking_url"):
                current_payload["tracking_url"] = payload["tracking_url"]

            art05.payload = current_payload
            art05.save(update_fields=["payload"])
        else:
            # Create new ART-05 with tracking data
            art05 = ArtifactInstance.objects.create(
                expediente=expediente,
                artifact_type="ART-05",
                payload={
                    "tracking_url": payload.get("tracking_url", ""),
                    "updates": [update_entry],
                },
                status="completed",
            )

        EventLog.objects.create(
            event_type="shipment.update_added",
            aggregate_type="expediente",
            aggregate_id=expediente.expediente_id,
            payload={
                "artifact_id": str(art05.artifact_id),
                "update": update_entry,
            },
            occurred_at=timezone.now(),
            emitted_by="C36:AddShipmentUpdate",
            correlation_id=uuid.uuid4(),
        )

    return art05


# ──────────────────────────────────────────────
# S5-06: Handoff Expediente → Transfer suggestion
# ──────────────────────────────────────────────

def get_handoff_suggestion(expediente: Expediente) -> dict:
    """
    S5-06: Returns transfer suggestion data if expediente is CERRADO
    and has nodo_destino assigned. CEO uses this to create transfer via C30.
    """
    if expediente.status != 'CERRADO':
        return {"has_suggestion": False, "reason": "Expediente not closed"}

    if not expediente.nodo_destino:
        return {"has_suggestion": False, "reason": "No destination node assigned"}

    # Build suggestion payload for C30 CreateTransfer
    nodo = expediente.nodo_destino
    items = []
    # Gather SKU-like info from ART-01 payload if available
    art01 = ArtifactInstance.objects.filter(
        expediente=expediente, artifact_type='ART-01', status='completed'
    ).order_by('-created_at').first()

    if art01 and art01.payload:
        # Try to extract items from OC payload
        oc_items = art01.payload.get('items', [])
        for item in oc_items:
            items.append({
                "sku": item.get("sku", item.get("description", "N/A")),
                "quantity": item.get("quantity", 1),
            })

    if not items:
        items = [{"sku": f"EXP-{str(expediente.expediente_id)[:8]}", "quantity": 1}]

    return {
        "has_suggestion": True,
        "message": f"Producto entregado a {nodo.name}. ¿Crear transfer?",
        "transfer_data": {
            "from_node": str(nodo.node_id),
            "source_expediente": str(expediente.expediente_id),
            "items": items,
        },
        "node": {
            "node_id": str(nodo.node_id),
            "name": nodo.name,
            "node_type": nodo.node_type,
            "location": nodo.location,
        },
    }


# ──────────────────────────────────────────────
# S5-10: Liquidation → Payment suggestion for COMISION mode
# ──────────────────────────────────────────────

def get_liquidation_payment_suggestion(expediente: Expediente) -> dict:
    """
    S5-10: When ART-10 liquidation is reconciled and has lines matched
    to proformas of this expediente, suggest registering payment via C21
    with method='liquidacion_marluvas'.
    """
    from apps.liquidations.models import LiquidationLine
    from apps.liquidations.enums_exp import LiquidationStatus, MatchStatus

    if expediente.mode != 'COMISION':
        return {"has_suggestion": False, "reason": "Only applicable for COMISION mode"}

    # Find matched liquidation lines for this expediente's proformas
    matched_lines = LiquidationLine.objects.filter(
        matched_expediente=expediente,
        liquidation__status=LiquidationStatus.RECONCILED,
        match_status=MatchStatus.MATCHED,
    ).select_related('liquidation')

    if not matched_lines.exists():
        return {"has_suggestion": False, "reason": "No reconciled liquidation lines for this expediente"}

    # Calculate expected commission
    art01 = ArtifactInstance.objects.filter(
        expediente=expediente, artifact_type='ART-01', status='completed'
    ).order_by('-created_at').first()
    art02 = ArtifactInstance.objects.filter(
        expediente=expediente, artifact_type='ART-02', status='completed'
    ).order_by('-created_at').first()

    total_po = Decimal('0')
    if art01 and 'total_po' in art01.payload:
        total_po = Decimal(str(art01.payload['total_po']))
    elif art01 and 'total' in art01.payload:
        total_po = Decimal(str(art01.payload['total']))

    comision_pactada = Decimal('0')
    if art02 and 'comision_pactada' in art02.payload:
        comision_pactada = Decimal(str(art02.payload['comision_pactada']))

    expected_commission = (total_po * comision_pactada) / Decimal('100')

    # Sum already paid
    from django.db.models import Sum as DjangoSum
    total_paid = expediente.payment_lines.aggregate(
        total=DjangoSum('amount')
    )['total'] or Decimal('0')

    remaining = expected_commission - total_paid

    suggestions = []
    for line in matched_lines:
        suggestions.append({
            "liquidation_id": line.liquidation.liquidation_id,
            "period": line.liquidation.period,
            "commission_amount": str(line.commission_amount),
            "marluvas_reference": line.marluvas_reference,
            "c21_data": {
                "amount": str(line.commission_amount),
                "currency": line.currency or "USD",
                "method": "liquidacion_marluvas",
                "reference": line.liquidation.liquidation_id,
            },
        })

    return {
        "has_suggestion": True,
        "expected_commission": str(expected_commission),
        "total_paid": str(total_paid),
        "remaining": str(remaining),
        "is_partial": total_paid > Decimal('0') and total_paid < expected_commission,
        "payment_status": expediente.payment_status,
        "suggestions": suggestions,
    }
