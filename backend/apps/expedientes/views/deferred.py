"""
S25-06 — PATCH deferred-price endpoint.
Permisos: CEO only.
Locking: transaction.atomic() + select_for_update() en Expediente.

Invariante (fix M1 R6 v1.6):
  Payload contradictorio (deferred_total_price=null + deferred_visible=true en MISMA llamada) → 400 duro.
  Orden de evaluación:
    1. Validar contradicción → 400 duro.
    2. Si price=null → auto-corregir visible=false.
    3. Si visible=true con precio null existente → 400.
"""
import uuid
from decimal import Decimal, InvalidOperation
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.expedientes.models import Expediente, EventLog
from apps.expedientes.permissions import IsCEO

# Sentinel para distinguir "campo no enviado" de "campo enviado como null"
_MISSING = object()


@api_view(['PATCH'])
@permission_classes([IsCEO])
def patch_deferred_price(request, exp_id):
    """
    PATCH /api/expedientes/{exp_id}/deferred-price/
    Payload (todos opcionales):
      { deferred_total_price: Decimal|null, deferred_visible: bool }

    Semántica:
      null  = "limpiar precio" (vuelve a no definido)
      0.00  = valor válido y distinto de null
    """
    with transaction.atomic():
        try:
            expediente = Expediente.objects.select_for_update().get(expediente_id=exp_id)
        except Expediente.DoesNotExist:
            return Response({'error': 'Expediente no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        raw_data = request.data

        # Leer con sentinel para distinguir ausencia de null explícito
        price_val = raw_data.get('deferred_total_price', _MISSING)
        visible_val = raw_data.get('deferred_visible', _MISSING)

        # ── Validar precio >= 0 si se provee valor numérico ──
        if price_val is not _MISSING and price_val is not None:
            try:
                price_decimal = Decimal(str(price_val))
            except (InvalidOperation, TypeError, ValueError):
                return Response(
                    {'error': 'deferred_total_price must be a valid decimal.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if price_decimal < 0:
                return Response(
                    {'error': 'deferred_total_price must be >= 0.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            price_decimal = price_val  # None o _MISSING

        # ── PASO 1: payload contradictorio → error duro (fix M1 R6) ──
        # null + visible=true en misma llamada = error duro, NO auto-corrección.
        if (
            price_val is not _MISSING
            and price_val is None
            and visible_val is True
        ):
            return Response(
                {'error': 'Cannot set deferred_visible=True and deferred_total_price=null in the same request.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        update_fields = []

        # ── PASO 2: si price=null → auto-corregir visible=false ──
        if price_val is not _MISSING and price_val is None:
            expediente.deferred_total_price = None
            expediente.deferred_visible = False
            update_fields.extend(['deferred_total_price', 'deferred_visible'])

        elif price_val is not _MISSING:
            # Precio numérico válido
            expediente.deferred_total_price = price_decimal
            update_fields.append('deferred_total_price')

        # ── PASO 3: procesar visible si no fue ya seteado en paso 2 ──
        if visible_val is not _MISSING and 'deferred_visible' not in update_fields:
            # Determinar precio efectivo (puede venir del payload o del estado actual)
            if price_val is not _MISSING and price_val is not None:
                effective_price = price_decimal
            else:
                effective_price = expediente.deferred_total_price

            if visible_val is True and effective_price is None:
                return Response(
                    {'error': 'Cannot set deferred_visible=True when deferred_total_price is null.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            expediente.deferred_visible = bool(visible_val)
            update_fields.append('deferred_visible')

        if not update_fields:
            return Response(
                {'error': 'No fields to update. Send deferred_total_price and/or deferred_visible.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        expediente.save(update_fields=update_fields)

        EventLog.objects.create(
            event_type='expediente.deferred_price_updated',
            aggregate_type='EXPEDIENTE',
            aggregate_id=expediente.expediente_id,
            expediente=expediente,
            action_source='patch_deferred',
            user=request.user,
            occurred_at=timezone.now(),
            emitted_by='patch_deferred_price',
            correlation_id=uuid.uuid4(),
            payload={
                f: str(getattr(expediente, f))
                for f in update_fields
            },
        )

    return Response({
        'status': 'updated',
        'fields': update_fields,
        'deferred_total_price': str(expediente.deferred_total_price) if expediente.deferred_total_price is not None else None,
        'deferred_visible': expediente.deferred_visible,
    })
