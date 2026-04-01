# S20-11 — Endpoints Sprint 20: crear proforma + change mode
# POST /api/expedientes/{id}/proformas/
# PATCH /api/expedientes/{id}/proforma/{pf_id}/change-mode/

from __future__ import annotations

import uuid

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.expedientes.models import ArtifactInstance, EventLog, Expediente
from apps.expedientes.enums_exp import AggregateType
from apps.expedientes.services.artifact_policy import BRAND_ALLOWED_MODES
from apps.expedientes.services.proforma_mode import change_proforma_mode

VALID_MODES = ('mode_b', 'mode_c', 'default')


class ProformaCreateView(APIView):
    """
    POST /api/expedientes/{id}/proformas/

    Payload: {
        proforma_number: str,
        mode: str,
        operated_by: str,
        line_ids: list[int] | null  (opcional)
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        data = request.data

        # ── Validación rápida de mode ANTES del lock ──────────────────────────
        mode = data.get('mode', '')
        if mode not in VALID_MODES:
            return Response(
                {'error': f"Modo inválido: '{mode}'. Válidos: {VALID_MODES}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── Validación estricta de line_ids ANTES del lock ────────────────────
        raw_line_ids = data.get('line_ids', None)
        if raw_line_ids is None:
            line_ids = []
        elif not isinstance(raw_line_ids, list):
            return Response(
                {'error': 'line_ids debe ser una lista o null'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            for item in raw_line_ids:
                if isinstance(item, bool):
                    return Response(
                        {'error': 'line_ids no acepta booleanos'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if not isinstance(item, int):
                    return Response(
                        {'error': 'line_ids solo acepta enteros'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            line_ids = list(set(raw_line_ids))

        with transaction.atomic():
            # ── select_for_update en expediente (gate de status) ─────────────
            try:
                expediente = (
                    Expediente.objects
                    .select_for_update(of=('self',))
                    .get(pk=pk)
                )
            except Expediente.DoesNotExist:
                return Response({'error': 'Expediente no encontrado'}, status=status.HTTP_404_NOT_FOUND)

            # Gate: solo en REGISTRO
            if expediente.status != 'REGISTRO':
                return Response(
                    {'error': f"Solo se pueden crear proformas en estado REGISTRO. Estado actual: {expediente.status}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validar mode por brand
            brand_slug = ''
            try:
                brand_slug = expediente.brand.slug
            except Exception:
                pass

            if not brand_slug or brand_slug not in BRAND_ALLOWED_MODES:
                return Response(
                    {'error': f"Brand '{brand_slug}' no soportada en BRAND_ALLOWED_MODES."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            allowed = BRAND_ALLOWED_MODES[brand_slug]
            if mode not in allowed:
                return Response(
                    {'error': f"Modo '{mode}' no permitido para brand '{brand_slug}'. Permitidos: {list(allowed)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # ── Crear ArtifactInstance ART-02 ─────────────────────────────────
            proforma = ArtifactInstance.objects.create(
                expediente=expediente,
                artifact_type='ART-02',
                status='COMPLETED',
                payload={
                    'proforma_number': data.get('proforma_number', ''),
                    'mode': mode,
                    'operated_by': data.get('operated_by', ''),
                },
            )

            # ── NEW: Create lines from product catalog (new_lines) ────────────
            new_lines_data = data.get('new_lines', [])
            if new_lines_data:
                from apps.expedientes.models import ExpedienteProductLine
                from apps.productos.models import ProductMaster, Producto
                
                for line_data in new_lines_data:
                    raw_product_id = line_data.get('product_id')
                    quantity = int(line_data.get('quantity', 1))
                    unit_price = float(line_data.get('unit_price', 0))
                    
                    target_product_master = None
                    
                    # 1. Try direct lookup in ProductMaster
                    try:
                        target_product_master = ProductMaster.objects.get(pk=raw_product_id)
                    except (ProductMaster.DoesNotExist, ValueError, TypeError):
                        # 2. Try lookup in Producto and then find Master by sku_base
                        try:
                            producto_obj = Producto.objects.get(pk=raw_product_id)
                            target_product_master = ProductMaster.objects.filter(sku_base=producto_obj.sku_base).first()
                            
                            # 3. If no Master exists for this SKU, create one on the fly to satisfy FK
                            if not target_product_master:
                                target_product_master = ProductMaster.objects.create(
                                    sku_base=producto_obj.sku_base,
                                    name=producto_obj.name,
                                    brand=producto_obj.brand,
                                    category=producto_obj.category,
                                    description=producto_obj.description
                                )
                        except (Producto.DoesNotExist, ValueError, TypeError):
                            # Fallback if both fail (unlikely given frontend source)
                            continue

                    if target_product_master:
                        ExpedienteProductLine.objects.create(
                            expediente=expediente,
                            product=target_product_master,
                            quantity=quantity,
                            unit_price=unit_price,
                            proforma=proforma,
                            price_source='manual'
                        )

            # ── Asignar líneas con validación ─────────────────────────────────
            assigned_count = 0
            if line_ids:
                from apps.expedientes.models import ExpedienteProductLine

                lines_qs = (
                    ExpedienteProductLine.objects
                    .select_for_update(of=('self',))
                    .filter(id__in=line_ids, expediente=expediente)
                )
                found_ids = set(lines_qs.values_list('id', flat=True))
                missing = set(line_ids) - found_ids
                if missing:
                    transaction.set_rollback(True)
                    return Response(
                        {'error': f'line_ids no encontrados en este expediente: {sorted(missing)}'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                already_assigned = list(
                    lines_qs.exclude(proforma__isnull=True).values_list('id', flat=True)
                )
                if already_assigned:
                    transaction.set_rollback(True)
                    return Response(
                        {'error': f'Líneas ya asignadas a otra proforma: {sorted(already_assigned)}'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                assigned_count = lines_qs.update(proforma=proforma)

            # ── EventLog ──────────────────────────────────────────────────────
            EventLog.objects.create(
                event_type='proforma.created',
                aggregate_type=AggregateType.EXPEDIENTE,
                aggregate_id=expediente.expediente_id,
                payload={
                    'proforma_id': str(proforma.artifact_id),
                    'mode': mode,
                    'assigned_count': assigned_count,
                    'new_lines_count': len(new_lines_data),
                },
                occurred_at=timezone.now(),
                emitted_by='S20-11:ProformaCreateView',
                correlation_id=uuid.uuid4(),
            )

        return Response(
            {
                'proforma_id': str(proforma.artifact_id),
                'mode': mode,
                'assigned_count': assigned_count,
            },
            status=status.HTTP_201_CREATED,
        )


class ProformaModeChangeView(APIView):
    """
    PATCH /api/expedientes/{id}/proforma/{pf_id}/change-mode/

    Payload: { new_mode: str, confirm_void: bool }
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk, pf_id):
        try:
            proforma = ArtifactInstance.objects.select_related(
                'expediente__brand'
            ).get(
                pk=pf_id,
                expediente__pk=pk,
                artifact_type='ART-02',
            )
        except ArtifactInstance.DoesNotExist:
            return Response({'error': 'Proforma no encontrada'}, status=status.HTTP_404_NOT_FOUND)

        new_mode = request.data.get('new_mode', '')
        confirm_void = bool(request.data.get('confirm_void', False))

        try:
            result = change_proforma_mode(
                proforma=proforma,
                new_mode=new_mode,
                confirm_void=confirm_void,
                user=request.user,
            )
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(result, status=status.HTTP_200_OK)
