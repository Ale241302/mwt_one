"""
Vista Orden de Compra (OC) — API endpoints.

GET  /api/ui/expedientes/{pk}/oc/           → Bundle completo de la OC
POST /api/ui/expedientes/{pk}/oc/proformas/ → Crear OCProforma
DEL  /api/ui/expedientes/{pk}/oc/proformas/{proforma_id}/ → Eliminar OCProforma

SECURITY:
  - CEO/INTERNAL → acceso total
  - Cliente → solo puede ver/crear proformas en sus propios expedientes
"""
from __future__ import annotations

from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from apps.expedientes.models import (
    Expediente, EventLog, OCProforma, ExpedientePago, FactoryOrder,
)


def _is_admin(user) -> bool:
    return user.is_superuser or getattr(user, 'role', '') == 'INTERNAL'


def _get_expediente_for_user(pk, user):
    """
    Retorna el Expediente si el usuario tiene acceso, o None si no.
    CEO/INTERNAL → cualquier expediente.
    Cliente → solo los suyos (client_id == legal_entity_id).
    """
    try:
        exp = (
            Expediente.objects
            .select_related('client', 'brand')
            .prefetch_related(
                'product_lines__product',
                'factory_orders',
                'oc_proformas',
                'pagos',
            )
            .get(pk=pk)
        )
    except Expediente.DoesNotExist:
        return None

    if not _is_admin(user):
        user_entity = getattr(user, 'legal_entity_id', None)
        if not user_entity or str(exp.client_id) != str(user_entity):
            return None

    return exp


# ─────────────────────────────────────────────────────────────────────────────

class OCBundleView(APIView):
    """
    GET /api/ui/expedientes/{pk}/oc/

    Retorna el bundle completo para la vista Orden de Compra:
    - metadata del expediente (OC)
    - product_lines (tabla de detalle de productos)
    - factory_orders (Envíos SAP Asociados)
    - oc_proformas (Proformas Asociadas)
    - financials (total OC, pagos, crédito restante)
    - event_log (historial)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        exp = _get_expediente_for_user(pk, request.user)
        if exp is None:
            return Response({'detail': 'No encontrado o sin acceso.'}, status=404)

        is_admin_user = _is_admin(request.user)

        # ── Metadata OC ──
        oc_ref = (
            exp.purchase_order_number
            or f"OC-{str(exp.expediente_id)[:8].upper()}"
        )

        # ── Product lines ──
        product_lines = []
        for i, line in enumerate(exp.product_lines.all(), start=1):
            sap_ref = None
            try:
                fo = exp.factory_orders.first()
                if fo:
                    sap_ref = fo.order_number
            except Exception:
                pass

            product_lines.append({
                'id': line.id,
                'sku': getattr(getattr(line, 'product', None), 'sku_base', None) or f"SKU-{i:03d}",
                'product_name': getattr(getattr(line, 'product', None), 'name', '') or '—',
                'quantity_oc': line.quantity or 0,
                'price_oc': float(line.unit_price or 0),
                'quantity_real': line.quantity_modified or line.quantity or 0,
                'price_real': float(line.unit_price_modified or line.unit_price or 0),
                'sap_ref': sap_ref,
            })

        # ── Factory Orders (SAP Asociados) ──
        sap_entries = []
        for i, fo in enumerate(exp.factory_orders.all(), start=1):
            sap_entries.append({
                'id': fo.id,
                'sap_id': fo.order_number or f"SAP-{i:03d}",
                'status': exp.status,
                'shipping_method': exp.shipping_method or '—',
                'expediente_id': str(exp.expediente_id),
                'url': f"/expedientes/{str(exp.expediente_id)}",
            })

        # ── OCProformas ──
        oc_proformas = []
        for pf in exp.oc_proformas.all():
            oc_proformas.append({
                'id': pf.id,
                'proforma_number': pf.proforma_number,
                'file_url': pf.file_url,
                'filename': pf.filename or pf.proforma_number,
                'file_type': pf.file_type,
                'notes': pf.notes,
                'created_at': pf.created_at,
                'created_by': getattr(pf.created_by, 'username', None),
            })

        # ── Financials ──
        total_oc = sum(
            (line.unit_price or Decimal('0')) * (line.quantity or 0)
            for line in exp.product_lines.all()
        )
        total_paid = sum(
            p.amount_paid or Decimal('0')
            for p in exp.pagos.filter(payment_status='credit_released')
        )
        remaining = total_oc - total_paid

        # ── Progreso general ──
        PROGRESS_MAP = {
            'REGISTRO': 5, 'PRODUCCION': 30, 'PREPARACION': 50,
            'DESPACHO': 65, 'TRANSITO': 80, 'EN_DESTINO': 95, 'CERRADO': 100,
        }
        progress_pct = PROGRESS_MAP.get(exp.status, 0)

        # ── Event log (últimos 10) ──
        events = []
        try:
            logs = EventLog.objects.filter(
                aggregate_id=exp.expediente_id,
                aggregate_type='expediente',
            ).order_by('-occurred_at')[:10]
            for ev in logs:
                events.append({
                    'id': str(ev.event_id),
                    'event_type': ev.event_type,
                    'occurred_at': ev.occurred_at,
                    'emitted_by': ev.emitted_by,
                    'payload': ev.payload if is_admin_user else {},
                })
        except Exception:
            pass

        return Response({
            'expediente_id': str(exp.expediente_id),
            'oc_ref': oc_ref,
            'client_name': exp.client.legal_name if exp.client else '—',
            'brand_name': exp.brand.name if exp.brand else '—',
            'status': exp.status,
            'payment_status': exp.payment_status,
            'progress_pct': progress_pct,
            'is_admin': is_admin_user,
            'incoterms': exp.incoterms or '—',
            'product_lines': product_lines,
            'sap_entries': sap_entries,
            'oc_proformas': oc_proformas,
            'financials': {
                'total_oc': float(total_oc),
                'total_paid': float(total_paid),
                'remaining_credit': float(remaining),
                'currency': 'USD',
            },
            'events': events,
        })


# ─────────────────────────────────────────────────────────────────────────────

class OCProformaCreateView(APIView):
    """
    POST /api/ui/expedientes/{pk}/oc/proformas/

    Payload:
    {
        "proforma_number": "PF-12345",
        "file_url": "https://drive.google.com/...",
        "filename": "proforma.pdf",
        "file_type": "pdf",
        "notes": "..."
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        exp = _get_expediente_for_user(pk, request.user)
        if exp is None:
            return Response({'detail': 'No encontrado o sin acceso.'}, status=404)

        proforma_number = request.data.get('proforma_number', '').strip()
        if not proforma_number:
            return Response({'detail': 'El campo proforma_number es requerido.'}, status=400)

        file_url = request.data.get('file_url', '').strip() or None
        filename = request.data.get('filename', '').strip() or None
        file_type = request.data.get('file_type', '').strip() or None
        notes = request.data.get('notes', '').strip() or None

        # Auto-detectar tipo por extensión si no viene
        if file_url and not file_type:
            lower = file_url.lower()
            if lower.endswith('.pdf'):
                file_type = 'pdf'
            elif lower.endswith('.xlsx') or lower.endswith('.xls'):
                file_type = 'xlsx'
            else:
                file_type = 'other'

        pf = OCProforma.objects.create(
            expediente=exp,
            proforma_number=proforma_number,
            file_url=file_url,
            filename=filename,
            file_type=file_type,
            notes=notes,
            created_by=request.user,
        )

        return Response({
            'id': pf.id,
            'proforma_number': pf.proforma_number,
            'file_url': pf.file_url,
            'filename': pf.filename,
            'file_type': pf.file_type,
            'created_at': pf.created_at,
        }, status=status.HTTP_201_CREATED)


class OCProformaDeleteView(APIView):
    """
    DELETE /api/ui/expedientes/{pk}/oc/proformas/{proforma_id}/
    Solo admin puede eliminar.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk, proforma_id):
        if not _is_admin(request.user):
            return Response({'detail': 'Solo administradores pueden eliminar proformas.'}, status=403)

        try:
            pf = OCProforma.objects.get(id=proforma_id, expediente_id=pk)
        except OCProforma.DoesNotExist:
            return Response({'detail': 'Proforma no encontrada.'}, status=404)

        pf.delete()
        return Response({'detail': 'Proforma eliminada.'}, status=204)
