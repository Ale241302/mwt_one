# Sprint 18 - T1.2, T1.3, T1.4, T1.5, T1.6
# PATCH state endpoints, FactoryOrder CRUD, merge, split
from django.db import transaction
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.utils import timezone
from .models import Expediente, FactoryOrder, ExpedienteProductLine
from .serializers import FactoryOrderSerializer, BundleSerializer, PagoSerializer
from .services.credit import recalculate_expediente_credit
from apps.core.registry import ModuleRegistry


# ─────────────── HELPER ───────────────
def _get_expediente(request, pk):
    """Tenant isolation: nunca .all()"""
    try:
        return Expediente.objects.for_user(request.user).get(pk=pk)
    except AttributeError:
        # fallback si for_user no existe aun
        return Expediente.objects.get(pk=pk)
    except Expediente.DoesNotExist:
        return None


def _sync_factory_order_number(expediente):
    principal = expediente.factory_orders.order_by('id').first()
    expediente.factory_order_number = (
        principal.order_number if principal else None
    )
    expediente.save(update_fields=['factory_order_number'])


# ─────────────── T1.2: PATCH por estado ───────────────
def _patch_state_endpoint(request, pk, required_status, allowed_fields):
    exp = _get_expediente(request, pk)
    if exp is None:
        return Response({'detail': 'No encontrado.'}, status=status.HTTP_404_NOT_FOUND)
    if exp.status != required_status:
        return Response(
            {'detail': f'Estado requerido: {required_status}. Actual: {exp.status}.'},
            status=status.HTTP_409_CONFLICT,
        )
    for field in allowed_fields:
        if field in request.data:
            setattr(exp, field, request.data[field])
    exp.save()
    return Response(BundleSerializer(exp).data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def patch_confirmado(request, pk):
    return _patch_state_endpoint(request, pk, 'CONFIRMADO', [
        'purchase_order_number', 'proforma_client_number', 'proforma_mwt_number',
        'credit_days_client', 'credit_days_mwt',
    ])


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def patch_preparacion(request, pk):
    return _patch_state_endpoint(request, pk, 'PREPARACION', [
        'shipping_method', 'cargo_manager', 'shipping_value',
        'payment_mode_shipping', 'url_list_empaque', 'url_cotizacion_envio',
    ])


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def patch_produccion(request, pk):
    return _patch_state_endpoint(request, pk, 'PRODUCCION', [
        'factory_order_number', 'fabrication_start_date', 'fabrication_end_date',
        'url_proforma_cliente', 'url_proforma_muito_work',
    ])


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def patch_despacho(request, pk):
    return _patch_state_endpoint(request, pk, 'DESPACHO', [
        'airline_or_shipping_company', 'awb_bl_number', 'shipment_date',
        'invoice_client_number', 'invoice_mwt_number', 'dispatch_additional_info',
        'url_certificado_origen', 'url_factura_cliente', 'url_awb_bl', 'tracking_url',
    ])


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def patch_transito(request, pk):
    return _patch_state_endpoint(request, pk, 'TRANSITO', [
        'intermediate_airport_or_port', 'transit_arrival_date',
        'url_packing_list_detallado',
    ])


# ─────────────── T1.3: FactoryOrder CRUD ───────────────
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def factory_orders_list(request, pk):
    exp = _get_expediente(request, pk)
    if exp is None:
        return Response({'detail': 'No encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        qs = exp.factory_orders.all().order_by('id')
        return Response(FactoryOrderSerializer(qs, many=True).data)

    # POST
    data = request.data.copy()
    if not data.get('order_number'):
        seq = exp.factory_orders.count() + 1
        exp_code = getattr(exp, 'code', str(exp.expediente_id)[:8])
        data['order_number'] = f'FO-{exp_code}-{seq:03d}'

    serializer = FactoryOrderSerializer(data=data)
    if serializer.is_valid():
        fo = serializer.save(expediente=exp)
        _sync_factory_order_number(exp)
        return Response(FactoryOrderSerializer(fo).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def factory_orders_detail(request, pk, fo_id):
    exp = _get_expediente(request, pk)
    if exp is None:
        return Response({'detail': 'No encontrado.'}, status=status.HTTP_404_NOT_FOUND)
    try:
        fo = exp.factory_orders.get(pk=fo_id)
    except FactoryOrder.DoesNotExist:
        return Response({'detail': 'FactoryOrder no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'DELETE':
        fo.delete()
        _sync_factory_order_number(exp)
        return Response(status=status.HTTP_204_NO_CONTENT)

    # PATCH
    serializer = FactoryOrderSerializer(fo, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        _sync_factory_order_number(exp)
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─────────────── T1.5: Merge ───────────────
PRE_PRODUCTION_STATUSES = {'REGISTRO', 'PI_SOLICITADA', 'CONFIRMADO'}


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def merge_expedientes(request, pk):
    master = _get_expediente(request, pk)
    if master is None:
        return Response({'detail': 'Master no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    follower_ids = request.data.get('follower_ids', [])
    if not follower_ids:
        return Response({'detail': 'follower_ids requerido.'}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        all_ids = sorted([master.expediente_id] + list(follower_ids))
        expedientes = list(
            Expediente.objects.select_for_update().filter(
                expediente_id__in=all_ids
            ).order_by('expediente_id')
        )

        for exp in expedientes:
            if exp.status not in PRE_PRODUCTION_STATUSES:
                return Response(
                    {'detail': f'Expediente {exp.expediente_id} esta en estado {exp.status}. Solo REGISTRO, PI_SOLICITADA o CONFIRMADO.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        followers = [e for e in expedientes if e.expediente_id != master.expediente_id]
        for follower in followers:
            ExpedienteProductLine.objects.filter(expediente=follower).update(expediente=master)
            follower.status = 'CANCELADO'
            follower.master_expediente = master
            follower.save(update_fields=['status', 'master_expediente'])

        recalculate_expediente_credit(master)

    return Response(BundleSerializer(master).data)


# ─────────────── T1.6: Split (S25-07 extended) ───────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def split_expediente(request, pk):
    original = _get_expediente(request, pk)
    if original is None:
        return Response({'detail': 'No encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    line_ids = request.data.get('product_line_ids', [])
    if not line_ids:
        return Response({'detail': 'product_line_ids requerido.'}, status=status.HTTP_400_BAD_REQUEST)

    total_lines = original.product_lines.count()
    if len(line_ids) >= total_lines:
        return Response(
            {'detail': 'No se puede separar todas las lineas.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    invert_parent = bool(request.data.get('invert_parent', False))

    if invert_parent and original.parent_expediente_id is not None:
        return Response(
            {
                'error': (
                    'Cannot invert parent on an expediente that is already a child.'
                )
            },
            status=status.HTTP_409_CONFLICT,
        )

    with transaction.atomic():
        original_locked = Expediente.objects.select_for_update().get(
            expediente_id=original.expediente_id
        )

        new_exp = Expediente.objects.create(
            legal_entity=original_locked.legal_entity,
            brand_id=original_locked.brand_id,
            client_id=original_locked.client_id,
            destination=original_locked.destination,
            dispatch_mode=original_locked.dispatch_mode,
            incoterms=original_locked.incoterms,
            purchase_order_number=original_locked.purchase_order_number,
        )

        moved_lines = list(
            ExpedienteProductLine.objects.filter(
                expediente=original_locked,
                id__in=line_ids,
            )
        )
        ExpedienteProductLine.objects.filter(
            expediente=original_locked,
            id__in=line_ids,
        ).update(expediente=new_exp, separated_to_expediente=new_exp)

        if invert_parent:
            original_locked.parent_expediente = new_exp
            original_locked.is_inverted_child = True
            original_locked.save(update_fields=['parent_expediente', 'is_inverted_child'])
            parent_id = str(new_exp.expediente_id)
            child_id = str(original_locked.expediente_id)
        else:
            new_exp.parent_expediente = original_locked
            new_exp.save(update_fields=['parent_expediente'])
            parent_id = str(original_locked.expediente_id)
            child_id = str(new_exp.expediente_id)

        # EventLog 
        import uuid as _uuid
        from django.utils import timezone as _tz
        from apps.expedientes.models import EventLog
        now = _tz.now()
        moved_line_ids = [str(l.id) for l in moved_lines]

        for exp, role in [(original_locked, 'original'), (new_exp, 'new')]:
            EventLog.objects.create(
                event_type='expediente.split',
                aggregate_type='EXPEDIENTE',
                aggregate_id=exp.expediente_id,
                expediente=exp,
                action_source='separate_products',
                user=request.user,
                occurred_at=now,
                emitted_by='split_expediente',
                correlation_id=_uuid.uuid4(),
                payload={
                    'parent_id': parent_id,
                    'child_id': child_id,
                    'inverted': invert_parent,
                    'role': role,
                    'lines_moved': moved_line_ids,
                },
            )

        recalculate_expediente_credit(original_locked)
        recalculate_expediente_credit(new_exp)

    return Response({
        'original': BundleSerializer(original_locked).data,
        'new_expediente': BundleSerializer(new_exp).data,
    }, status=status.HTTP_201_CREATED)
# ─────────────── T1.4: Pagos ───────────────
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def pagos_list(request, pk):
    exp = _get_expediente(request, pk)
    if exp is None:
        return Response({'detail': 'No encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    payment_model = ModuleRegistry.get_model('finance', 'Payment')
    if not payment_model:
        return Response({'detail': 'Servicio de finanzas no disponible.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    if request.method == 'GET':
        qs = payment_model.objects.filter(expediente_id=exp.expediente_id).order_by('-created_at')
        return Response(PagoSerializer(qs, many=True).data)

    # POST - Registrar pago desde Expediente
    serializer = PagoSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(expediente_id=exp.expediente_id)
        # Recalcular crédito si es necesario
        recalculate_expediente_credit(exp)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pago_confirmar(request, pk, pago_id):
    exp = _get_expediente(request, pk)
    if exp is None:
        return Response({'detail': 'No encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    payment_model = ModuleRegistry.get_model('finance', 'Payment')
    if not payment_model:
        return Response({'detail': 'Servicio de finanzas no disponible.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    try:
        pago = payment_model.objects.get(pk=pago_id, expediente_id=exp.expediente_id)
    except payment_model.DoesNotExist:
        return Response({'detail': 'Pago no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    action = request.data.get('action', 'verify') # 'verify' or 'release_credit'
    
    with transaction.atomic():
        if action == 'verify':
            pago.status = 'verified'
            pago.verified_by = request.user
            pago.verified_at = timezone.now()
        elif action == 'release_credit':
            pago.status = 'credit_released'
            pago.credit_released_by = request.user
            pago.credit_released_at = timezone.now()
        
        pago.save()
        recalculate_expediente_credit(exp)

    return Response(PagoSerializer(pago).data)
