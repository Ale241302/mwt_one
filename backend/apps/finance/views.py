"""
Refactor de Payment Status Machine de expedientes/views/payment_status.py
Ahora opera sobre finance.Payment y usa ModuleRegistry para resolver el expediente.
"""
import uuid
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.registry import ModuleRegistry
from apps.expedientes.permissions import IsCEO
# Logica de negocio movida a services si es posible, pero mantenemos compatibilidad por ahora

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def list_pagos(request, exp_id):
    """
    GET /api/expedientes/{exp_id}/pagos/ -> Listado distribuido
    POST /api/expedientes/{exp_id}/pagos/ -> Crear pago en finance app
    """
    expediente_model = ModuleRegistry.get_model('expedientes', 'Expediente')
    try:
        expediente = expediente_model.objects.get(expediente_id=exp_id)
    except Exception:
        return Response({'error': 'Expediente no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    from .models import Payment
    if request.method == 'POST':
        amount = request.data.get('amount')
        payment_date = request.data.get('payment_date')

        if not amount or not payment_date:
            return Response({'error': 'amount and payment_date are required.'}, status=status.HTTP_400_BAD_REQUEST)

        pago = Payment.objects.create(
            expediente_id=exp_id,
            amount_paid=Decimal(str(amount)),
            payment_date=payment_date,
            metodo_pago='TRANSFERENCIA',
            tipo_pago='PARCIAL',
            status='pending',
            rejection_reason=request.data.get('notes', ''),
        )

        # Emitir evento vía ModuleRegistry o EventLog legacy
        event_model = ModuleRegistry.get_model('expedientes', 'EventLog')
        if event_model:
            event_model.objects.create(
                event_type='payment.created',
                aggregate_type='EXPEDIENTE',
                aggregate_id=exp_id,
                action_source='register_payment_ui',
                user=request.user,
                occurred_at=timezone.now(),
                emitted_by='ui',
                correlation_id=uuid.uuid4(),
                payload={'pago_id': str(pago.pk), 'amount': str(amount)},
            )

        from apps.expedientes.serializers import PagoSerializer
        return Response(PagoSerializer(pago).data, status=status.HTTP_201_CREATED)

    pagos = Payment.objects.filter(expediente_id=exp_id).order_by('-payment_date', '-created_at')
    from apps.expedientes.serializers import PagoSerializer
    serializer = PagoSerializer(pagos, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsCEO])
def verify_payment(request, exp_id, pago_id):
    from .models import Payment
    with transaction.atomic():
        try:
            pago = Payment.objects.select_for_update().get(pk=pago_id, expediente_id=exp_id)
        except Payment.DoesNotExist:
            return Response({'error': 'Pago no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if pago.status != 'pending':
            return Response({'error': f'Status conflict: {pago.status}'}, status=status.HTTP_409_CONFLICT)

        pago.status = 'verified'
        pago.verified_at = timezone.now()
        pago.verified_by_id = str(request.user.id)
        pago.save()

        # Auditoría
        event_model = ModuleRegistry.get_model('expedientes', 'EventLog')
        if event_model:
            event_model.objects.create(
                event_type='payment.verified', aggregate_type='EXPEDIENTE', aggregate_id=exp_id,
                action_source='verify_payment', user=request.user, payload={'pago_id': str(pago.pk)}
            )
    return Response({'status': 'verified', 'pago_id': str(pago.pk)})

@api_view(['POST'])
@permission_classes([IsCEO])
def reject_payment(request, exp_id, pago_id):
    from .models import Payment
    reason = request.data.get('reason', '').strip()
    if not reason:
        return Response({'error': 'reason is required.'}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        try:
            pago = Payment.objects.select_for_update().get(pk=pago_id, expediente_id=exp_id)
        except Payment.DoesNotExist:
            return Response({'error': 'Pago no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        previous_status = pago.status
        pago.status = 'rejected'
        pago.rejection_reason = reason
        pago.save()

        event_model = ModuleRegistry.get_model('expedientes', 'EventLog')
        if event_model:
            event_model.objects.create(
                event_type='payment.rejected', aggregate_type='EXPEDIENTE', aggregate_id=exp_id,
                action_source='reject_payment', user=request.user, 
                payload={'pago_id': str(pago.pk), 'previous_status': previous_status, 'reason': reason}
            )
            
        # Recalcular crédito vía servicio de expedientes si es posible
        from apps.expedientes.services.credit import recalculate_expediente_credit
        expediente_model = ModuleRegistry.get_model('expedientes', 'Expediente')
        exp = expediente_model.objects.filter(expediente_id=exp_id).first()
        if exp:
            recalculate_expediente_credit(exp)

    return Response({'status': 'rejected', 'pago_id': str(pago.pk)})

@api_view(['POST'])
@permission_classes([IsCEO])
def release_credit(request, exp_id, pago_id):
    from .models import Payment
    with transaction.atomic():
        try:
            pago = Payment.objects.select_for_update().get(pk=pago_id, expediente_id=exp_id)
        except Payment.DoesNotExist:
            return Response({'error': 'Pago no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        pago.status = 'credit_released'
        pago.save()

        from apps.expedientes.services.credit import recalculate_expediente_credit
        expediente_model = ModuleRegistry.get_model('expedientes', 'Expediente')
        exp = expediente_model.objects.filter(expediente_id=exp_id).first()
        if exp:
            recalculate_expediente_credit(exp)

    return Response({'status': 'credit_released', 'pago_id': str(pago.pk)})

@api_view(['POST'])
@permission_classes([IsCEO])
def release_all_verified(request, exp_id):
    from .models import Payment
    with transaction.atomic():
        pagos = Payment.objects.filter(expediente_id=exp_id, status='verified').select_for_update()
        count = pagos.count()
        pagos.update(status='credit_released')

        if count > 0:
            from apps.expedientes.services.credit import recalculate_expediente_credit
            expediente_model = ModuleRegistry.get_model('expedientes', 'Expediente')
            exp = expediente_model.objects.filter(expediente_id=exp_id).first()
            if exp:
                recalculate_expediente_credit(exp)

    return Response({'released': count})
