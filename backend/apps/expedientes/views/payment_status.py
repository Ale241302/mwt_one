"""
S25-03 / S25-04 — Payment Status Machine: verify, reject, release credit endpoints.
Permisos: CEO only (IsCEO).
Locking: transaction.atomic() + select_for_update() en Expediente + ExpedientePago.

FIX-2026-04-08c:
  - Agrega list_pagos() GET — listado de pagos de un expediente.
    Usa PagoSerializer (CEO/AGENT tier). Requiere IsAuthenticated.
    Resuelve bug: PagosSection llamaba este endpoint que no existía.
"""
from decimal import Decimal
import uuid
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.expedientes.models import Expediente, ExpedientePago, EventLog
from apps.expedientes.permissions import IsCEO
from apps.expedientes.services.credit import recalculate_expediente_credit


def _get_expediente_and_pago(exp_id, pago_id):
    """Lock-free lookup; locking is done inside atomic blocks."""
    try:
        expediente = Expediente.objects.get(expediente_id=exp_id)
    except Expediente.DoesNotExist:
        return None, None, Response(
            {'error': 'Expediente no encontrado.'},
            status=status.HTTP_404_NOT_FOUND,
        )
    try:
        pago = ExpedientePago.objects.get(pk=pago_id, expediente=expediente)
    except ExpedientePago.DoesNotExist:
        return None, None, Response(
            {'error': 'Pago no encontrado.'},
            status=status.HTTP_404_NOT_FOUND,
        )
    return expediente, pago, None


# ─────────────── FIX-2026-04-08c: LIST PAGOS ───────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_pagos(request, exp_id):
    """
    GET /api/expedientes/{exp_id}/pagos/
    Retorna todos los pagos del expediente en formato PagoSerializer (CEO/AGENT tier).
    Acceso: cualquier usuario autenticado con acceso al expediente.
    """
    try:
        expediente = Expediente.objects.get(expediente_id=exp_id)
    except Expediente.DoesNotExist:
        return Response({'error': 'Expediente no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    from apps.expedientes.serializers import PagoSerializer
    pagos = ExpedientePago.objects.filter(expediente=expediente).order_by('-payment_date', '-created_at')
    serializer = PagoSerializer(pagos, many=True)
    return Response(serializer.data)


# ─────────────── S25-03: VERIFY ───────────────
@api_view(['POST'])
@permission_classes([IsCEO])
def verify_payment(request, exp_id, pago_id):
    """
    pending → verified.
    Locking: Expediente + ExpedientePago con select_for_update().
    No libera crédito automáticamente (paso separado, S25-04).
    """
    with transaction.atomic():
        try:
            expediente = Expediente.objects.select_for_update().get(expediente_id=exp_id)
        except Expediente.DoesNotExist:
            return Response({'error': 'Expediente no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        try:
            pago = ExpedientePago.objects.select_for_update().get(pk=pago_id, expediente=expediente)
        except ExpedientePago.DoesNotExist:
            return Response({'error': 'Pago no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if pago.payment_status != 'pending':
            return Response(
                {'error': f'Cannot verify payment in status {pago.payment_status}. Expected: pending.'},
                status=status.HTTP_409_CONFLICT,
            )

        pago.payment_status = 'verified'
        pago.verified_at = timezone.now()
        pago.verified_by = request.user
        pago.save(update_fields=['payment_status', 'verified_at', 'verified_by'])

        EventLog.objects.create(
            event_type='payment.verified',
            aggregate_type='EXPEDIENTE',
            aggregate_id=expediente.expediente_id,
            expediente=expediente,
            action_source='verify_payment',
            user=request.user,
            occurred_at=timezone.now(),
            emitted_by='verify_payment',
            correlation_id=uuid.uuid4(),
            payload={
                'pago_id': str(pago.pk),
                'amount': str(pago.amount_paid),
            },
        )
        # No recalcula crédito aquí — el crédito solo se libera en release_credit()
    return Response({'status': 'verified', 'pago_id': str(pago.pk)})


# ─────────────── S25-03: REJECT ───────────────
@api_view(['POST'])
@permission_classes([IsCEO])
def reject_payment(request, exp_id, pago_id):
    """
    pending → rejected  o  verified → rejected.
    Requiere body: { reason: string }.
    Recalcula crédito (este pago ya no cuenta).
    """
    reason = request.data.get('reason', '').strip()
    if not reason:
        return Response({'error': 'reason is required.'}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        try:
            expediente = Expediente.objects.select_for_update().get(expediente_id=exp_id)
        except Expediente.DoesNotExist:
            return Response({'error': 'Expediente no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        try:
            pago = ExpedientePago.objects.select_for_update().get(pk=pago_id, expediente=expediente)
        except ExpedientePago.DoesNotExist:
            return Response({'error': 'Pago no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if pago.payment_status not in ('pending', 'verified'):
            return Response(
                {'error': f'Cannot reject payment in status {pago.payment_status}. Expected: pending or verified.'},
                status=status.HTTP_409_CONFLICT,
            )

        previous_status = pago.payment_status
        pago.payment_status = 'rejected'
        pago.rejection_reason = reason
        pago.save(update_fields=['payment_status', 'rejection_reason'])

        EventLog.objects.create(
            event_type='payment.rejected',
            aggregate_type='EXPEDIENTE',
            aggregate_id=expediente.expediente_id,
            expediente=expediente,
            action_source='reject_payment',
            user=request.user,
            occurred_at=timezone.now(),
            emitted_by='reject_payment',
            correlation_id=uuid.uuid4(),
            previous_status=previous_status,
            new_status='rejected',
            payload={
                'pago_id': str(pago.pk),
                'amount': str(pago.amount_paid),
                'previous_status': previous_status,
                'reason': reason,
            },
        )
        recalculate_expediente_credit(expediente)

    return Response({'status': 'rejected', 'pago_id': str(pago.pk)})


# ─────────────── S25-04: RELEASE CREDIT (individual) ───────────────
@api_view(['POST'])
@permission_classes([IsCEO])
def release_credit(request, exp_id, pago_id):
    """
    verified → credit_released.
    Trigger: recalculate_expediente_credit().
    """
    with transaction.atomic():
        try:
            expediente = Expediente.objects.select_for_update().get(expediente_id=exp_id)
        except Expediente.DoesNotExist:
            return Response({'error': 'Expediente no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        try:
            pago = ExpedientePago.objects.select_for_update().get(pk=pago_id, expediente=expediente)
        except ExpedientePago.DoesNotExist:
            return Response({'error': 'Pago no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if pago.payment_status != 'verified':
            return Response(
                {'error': f'Cannot release credit for payment in status {pago.payment_status}. Expected: verified.'},
                status=status.HTTP_409_CONFLICT,
            )

        pago.payment_status = 'credit_released'
        pago.credit_released_at = timezone.now()
        pago.credit_released_by = request.user
        pago.save(update_fields=['payment_status', 'credit_released_at', 'credit_released_by'])

        EventLog.objects.create(
            event_type='payment.credit_released',
            aggregate_type='EXPEDIENTE',
            aggregate_id=expediente.expediente_id,
            expediente=expediente,
            action_source='release_credit',
            user=request.user,
            occurred_at=timezone.now(),
            emitted_by='release_credit',
            correlation_id=uuid.uuid4(),
            payload={
                'pago_id': str(pago.pk),
                'amount': str(pago.amount_paid),
                'bulk': False,
            },
        )
        recalculate_expediente_credit(expediente)

    return Response({'status': 'credit_released', 'pago_id': str(pago.pk)})


# ─────────────── S25-04: RELEASE ALL VERIFIED (bulk) ───────────────
@api_view(['POST'])
@permission_classes([IsCEO])
def release_all_verified(request, exp_id):
    """
    Bulk release: libera crédito de TODOS los pagos 'verified' del expediente.
    Pagos pending/rejected se ignoran silenciosamente.
    Recálculo: UNA sola vez post-bulk.
    Idempotente: llamar dos veces → segunda retorna released=0.
    EventLog: 1 por pago (payload.bulk=true). NO existe payment.bulk_credit_released.

    Response: { released: N, already_released: N }
    """
    with transaction.atomic():
        try:
            expediente = Expediente.objects.select_for_update().get(expediente_id=exp_id)
        except Expediente.DoesNotExist:
            return Response({'error': 'Expediente no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        # Conjunto base: verified + credit_released. pending/rejected se ignoran.
        pagos = (
            ExpedientePago.objects
            .select_for_update()
            .filter(expediente=expediente, payment_status__in=['verified', 'credit_released'])
        )

        released = 0
        already_released = 0
        now = timezone.now()

        for pago in pagos:
            if pago.payment_status == 'credit_released':
                already_released += 1
            elif pago.payment_status == 'verified':
                pago.payment_status = 'credit_released'
                pago.credit_released_at = now
                pago.credit_released_by = request.user
                pago.save(update_fields=['payment_status', 'credit_released_at', 'credit_released_by'])

                # 1 EventLog por pago con payload.bulk=true (fix M1 v1.2)
                EventLog.objects.create(
                    event_type='payment.credit_released',
                    aggregate_type='EXPEDIENTE',
                    aggregate_id=expediente.expediente_id,
                    expediente=expediente,
                    action_source='release_credit',
                    user=request.user,
                    occurred_at=now,
                    emitted_by='release_all_verified',
                    correlation_id=uuid.uuid4(),
                    payload={
                        'pago_id': str(pago.pk),
                        'amount': str(pago.amount_paid),
                        'bulk': True,
                    },
                )
                released += 1

        # Recálculo UNA vez post-bulk (fix N2 R6)
        if released > 0:
            recalculate_expediente_credit(expediente)

    return Response({'released': released, 'already_released': already_released})
