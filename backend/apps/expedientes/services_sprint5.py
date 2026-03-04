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
