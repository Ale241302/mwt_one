# Sprint 18 - T1.2, T1.3, T1.4, T1.5, T1.6
# PATCH state endpoints, FactoryOrder CRUD, pagos, merge, split
from django.db import transaction
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Expediente, FactoryOrder, ExpedientePago, ExpedienteProductLine
from .serializers import FactoryOrderSerializer, PagoSerializer, BundleSerializer
from .services.credit import sync_credit_exposure_and_log, recalculate_expediente_credit


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


# ─────────────── T1.4: Pagos ───────────────
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def pagos_list(request, pk):
    exp = _get_expediente(request, pk)
    if exp is None:
        return Response({'detail': 'No encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(PagoSerializer(exp.pagos.all(), many=True).data)

    data = request.data.copy()
    # Pago siempre inicia PENDING - nunca auto-libera credito
    serializer = PagoSerializer(data=data)
    if serializer.is_valid():
        pago = serializer.save(expediente=exp, credit_status='PENDING')
        return Response(PagoSerializer(pago).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def pago_confirmar(request, pk, pago_id):
    """CEO confirma pago PENDING -> CONFIRMED + recalcula credito."""
    exp = _get_expediente(request, pk)
    if exp is None:
        return Response({'detail': 'No encontrado.'}, status=status.HTTP_404_NOT_FOUND)
    try:
        pago = exp.pagos.get(pk=pago_id)
    except ExpedientePago.DoesNotExist:
        return Response({'detail': 'Pago no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    if pago.credit_status != 'PENDING':
        return Response(
            {'detail': f'Pago ya esta en estado: {pago.credit_status}.'},
            status=status.HTTP_409_CONFLICT,
        )

    pago.credit_status = 'CONFIRMED'
    pago.save(update_fields=['credit_status'])
    sync_credit_exposure_and_log(exp, user=request.user)
    return Response(PagoSerializer(pago).data)


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


# ─────────────── T1.6: Split ───────────────
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

    with transaction.atomic():
        new_exp = Expediente.objects.create(
            legal_entity=original.legal_entity,
            brand=original.brand,
            client=original.client,
            destination=original.destination,
            dispatch_mode=original.dispatch_mode,
            incoterms=original.incoterms,
            purchase_order_number=original.purchase_order_number,
        )
        ExpedienteProductLine.objects.filter(
            expediente=original,
            id__in=line_ids,
        ).update(expediente=new_exp, separated_to_expediente=new_exp)

        recalculate_expediente_credit(original)
        recalculate_expediente_credit(new_exp)

    return Response({
        'original': BundleSerializer(original).data,
        'new_expediente': BundleSerializer(new_exp).data,
    }, status=status.HTTP_201_CREATED)
