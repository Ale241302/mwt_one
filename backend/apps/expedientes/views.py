"""
Sprint 1-4 – Views (views.py)
Ref: LOTE_SM_SPRINT1 Items 5-7, Sprint 3 UI, Sprint 4 S4-02/03/05/07/08
"""
import io
from decimal import Decimal

from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from apps.expedientes.models import (
    Expediente, ArtifactInstance, CostLine, PaymentLine, EventLog, LogisticsOption,
)
from apps.expedientes.services import (
    create_expediente, can_execute_command, execute_command,
    supersede_artifact, void_artifact, get_available_commands,
    get_costs, get_costs_summary, get_invoice_suggestion, get_invoice,
    calculate_financial_comparison, generate_mirror_pdf,
    register_compensation, get_logistics_suggestions, add_shipment_update,
    get_handoff_suggestion, get_liquidation_payment_suggestion,
)
from apps.expedientes.serializers_ui import (
    UIExpedienteListSerializer, ExpedienteBundleSerializer,
    CostLineSummarySerializer, ArtifactSummarySerializer,
)


# ─── Permissions ──────────────────────────────────────────────────

class IsCEO(IsAuthenticated):
    """CEO = superuser."""
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_superuser


class EnsureNotBlocked(IsAuthenticated):
    """Skip if command has bypass_block."""
    pass


# ─── Helpers ────────────────────────────────────────────────────────────

def _get_expediente(pk):
    try:
        return Expediente.objects.get(pk=pk)
    except Expediente.DoesNotExist:
        return None


def _command_response(expediente, events, status_code=200):
    return Response({
        'expediente_id': str(expediente.expediente_id),
        'status': expediente.status,
        'payment_status': expediente.payment_status,
        'is_blocked': expediente.is_blocked,
        'events': [
            {'event_id': str(e.event_id), 'event_type': e.event_type}
            for e in events
        ]
    }, status=status_code)


# ═══════════════════════════════════════════════════════════════════
# SPRINT 1 COMMANDS (C1-C21)
# ═══════════════════════════════════════════════════════════════════

class CreateExpedienteView(APIView):
    """C1: POST /api/expedientes/create/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        exp = create_expediente(request.data, request.user)
        return _command_response(exp, [], status_code=201)


class CommandDispatchView(APIView):
    """
    Sprint 12: Single entry point for all 22+ commands.
    URL pattern should provide 'cmd_id' via lookup or kwarg.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, cmd_id=None):
        # 1. Get command ID from URL kwarg or payload
        # If not in URL (fallback), look in payload 'command' field
        cmd_id = cmd_id or request.data.get('command')
        if not cmd_id:
            return Response({'detail': 'Command ID is required.'}, status=400)

        # 2. Get expediente
        exp = _get_expediente(pk)
        if not exp:
            return Response({'detail': 'Expediente not found.'}, status=404)

        # 3. Execute
        try:
            exp, events = execute_command(exp, cmd_id, request.data, request.user)
            return _command_response(exp, events)
        except PermissionError as e:
            return Response({'detail': str(e)}, status=403)
        except Exception as e:
            # We filter some internal exceptions if needed, but for now:
            return Response({'detail': str(e)}, status=400)

# The individual views (RegisterOCView, etc.) are now removed or deprecated.
# To maintain URL compatibility, we will point existing URLs to this view.


# ═══════════════════════════════════════════════════════════════════
# SPRINT 2 COMMANDS (C19, C20)
# ═══════════════════════════════════════════════════════════════════

class SupersedeArtifactView(APIView):
    """C19: POST /api/expedientes/<pk>/supersede-artifact/"""
    permission_classes = [IsCEO]

    def post(self, request, pk):
        exp = _get_expediente(pk)
        if not exp:
            return Response({'detail': 'Not found.'}, status=404)
        artifact_id = request.data.get('artifact_id')
        new_payload = request.data.get('payload', {})
        exp, new_art, event = supersede_artifact(artifact_id, new_payload, request.user)
        return _command_response(exp, [event])


class VoidArtifactView(APIView):
    """C20: POST /api/expedientes/<pk>/void-artifact/"""
    permission_classes = [IsCEO]

    def post(self, request, pk):
        exp = _get_expediente(pk)
        if not exp:
            return Response({'detail': 'Not found.'}, status=404)
        artifact_id = request.data.get('artifact_id')
        exp, art, event = void_artifact(artifact_id, request.user)
        return _command_response(exp, [event])


# ═══════════════════════════════════════════════════════════════════
# SPRINT 3: List + Bundle
# ═══════════════════════════════════════════════════════════════════

class ListExpedientesView(APIView):
    """GET /api/ui/expedientes/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.db.models import Sum, Count, Max
        from datetime import timedelta
        from django.utils import timezone

        qs = Expediente.objects.select_related('client').all()

        # Filtering
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        brand_filter = request.query_params.get('brand')
        if brand_filter:
            qs = qs.filter(brand=brand_filter)

        client_filter = request.query_params.get('client')
        if client_filter:
            qs = qs.filter(client_id=client_filter)

        search = request.query_params.get('search')
        if search:
            qs = qs.filter(client__legal_name__icontains=search)

        # Annotate
        qs = qs.annotate(
            total_cost=Sum('cost_lines__amount'),
            artifact_count=Count('artifacts'),
            last_event_at=Max('artifacts__created_at'),
        )

        for exp in qs:
            exp.credit_days_elapsed = 0
            exp.credit_band = 'MINT'
            if exp.credit_clock_started_at:
                delta = (timezone.now() - exp.credit_clock_started_at).days
                exp.credit_days_elapsed = delta
                if delta > 90:
                    exp.credit_band = 'RED'
                elif delta > 60:
                    exp.credit_band = 'AMBER'

        from core.pagination import StandardPagination
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = UIExpedienteListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class ExpedienteBundleView(APIView):
    """GET /api/ui/expedientes/<pk>/"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        from django.db.models import Sum, Count, Max
        from django.utils import timezone

        try:
            exp = Expediente.objects.select_related('client').prefetch_related(
                'artifacts', 'cost_lines', 'payment_lines'
            ).get(pk=pk)
        except Expediente.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)

        exp.total_cost = exp.cost_lines.aggregate(total=Sum('amount'))['total'] or 0
        exp.artifact_count = exp.artifacts.count()
        exp.last_event_at = exp.artifacts.aggregate(max_date=Max('created_at'))['max_date']

        if exp.credit_clock_started_at:
            delta = (timezone.now() - exp.credit_clock_started_at).days
            exp.credit_days_elapsed = delta
            exp.credit_band = 'RED' if delta > 90 else ('AMBER' if delta > 60 else 'MINT')
        else:
            exp.credit_days_elapsed = 0
            exp.credit_band = 'MINT'

        events = EventLog.objects.filter(
            aggregate_id=exp.expediente_id,
            aggregate_type='expediente'
        ).order_by('-occurred_at')[:20]

        available_actions = get_available_commands(exp, request.user)

        exp._events = events
        exp._available_actions = available_actions

        serializer = ExpedienteBundleSerializer(exp)
        result = serializer.data
        result['available_actions'] = available_actions
        result['events'] = [
            {'id': str(e.event_id), 'event_type': e.event_type,
             'occurred_at': e.occurred_at, 'emitted_by': e.emitted_by,
             'payload': e.payload}
            for e in events
        ]
        # S21: Expose is_admin so frontend can show the Admin Panel
        result['is_admin'] = request.user.is_superuser

        return Response(result)


class DocumentDownloadView(APIView):
    """GET /api/ui/expedientes/documents/<artifact_id>/download/"""
    permission_classes = [IsAuthenticated]

    def get(self, request, artifact_id):
        try:
            art = ArtifactInstance.objects.get(pk=artifact_id)
        except ArtifactInstance.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)

        file_url = art.payload.get('file_url')
        if not file_url:
            return Response({'detail': 'No file associated.'}, status=404)

        return Response({
            'download_url': file_url,
            'filename': art.payload.get('filename', f'{art.artifact_type}.pdf')
        })


# ═══════════════════════════════════════════════════════════════════
# SPRINT 4 NEW ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

# ── S4-02: Costs Doble Vista ──

class CostsListView(APIView):
    """GET /api/expedientes/<pk>/costs/?view=internal|client"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        exp = _get_expediente(pk)
        if not exp:
            return Response({'detail': 'Not found.'}, status=404)

        view_param = request.query_params.get('view', 'internal')

        if view_param == 'internal' and not request.user.is_superuser:
            view_param = 'client'

        costs = get_costs(exp, view=view_param)
        serializer = CostLineSummarySerializer(costs, many=True)
        return Response({
            'view': view_param,
            'count': costs.count(),
            'costs': serializer.data,
        })


class CostsSummaryView(APIView):
    """GET /api/expedientes/<pk>/costs/summary/  [CEO-ONLY]"""
    permission_classes = [IsCEO]

    def get(self, request, pk):
        exp = _get_expediente(pk)
        if not exp:
            return Response({'detail': 'Not found.'}, status=404)

        summary = get_costs_summary(exp)
        return Response(summary)


# ── S4-03: ART-09 Invoice ──

class InvoiceSuggestionView(APIView):
    """GET /api/expedientes/<pk>/invoice-suggestion/"""
    permission_classes = [IsCEO]

    def get(self, request, pk):
        exp = _get_expediente(pk)
        if not exp:
            return Response({'detail': 'Not found.'}, status=404)
        suggestion = get_invoice_suggestion(exp)
        return Response(suggestion)


class InvoiceView(APIView):
    """GET /api/expedientes/<pk>/invoice/?view=internal|client"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        exp = _get_expediente(pk)
        if not exp:
            return Response({'detail': 'Not found.'}, status=404)

        view_param = request.query_params.get('view', 'internal')
        if view_param == 'internal' and not request.user.is_superuser:
            view_param = 'client'

        invoice_data = get_invoice(exp, view=view_param)
        if not invoice_data:
            return Response({'detail': 'No invoice found (ART-09).'}, status=404)
        return Response({
            'view': view_param,
            'invoice': invoice_data,
        })


# ── S4-05: Financial Comparison ──

class FinancialComparisonView(APIView):
    """GET /api/expedientes/<pk>/financial-comparison/  [CEO-ONLY]"""
    permission_classes = [IsCEO]

    def get(self, request, pk):
        exp = _get_expediente(pk)
        if not exp:
            return Response({'detail': 'Not found.'}, status=404)
        comparison = calculate_financial_comparison(exp)
        return Response(comparison)


# Individual command views (deprecated in favor of CommandDispatchView)
# URL configuration will now map these directly to CommandDispatchView(cmd_id='...')


# ── S4-08: Mirror PDF ──

class MirrorPDFView(APIView):
    """GET /api/expedientes/<pk>/mirror-pdf/"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        exp = _get_expediente(pk)
        if not exp:
            return Response({'detail': 'Not found.'}, status=404)

        html_content = generate_mirror_pdf(exp)
        if not html_content:
            return Response({'detail': 'No client-facing data available.'}, status=404)

        try:
            from weasyprint import HTML
            pdf_bytes = HTML(string=html_content).write_pdf()
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = (
                f'inline; filename="MWT_Expediente_{str(exp.expediente_id)[:8]}.pdf"'
            )
            return response
        except ImportError:
            return HttpResponse(html_content, content_type='text/html')


# ═══════════════════════════════════════════════════════════════════
# SPRINT 4 S4-11: Dashboard Financial Endpoints
# ═══════════════════════════════════════════════════════════════════

def _safe_decimal(value):
    try:
        if value is None:
            return Decimal('0')
        # Clean potential commas or formatting
        clean_val = str(value).replace(',', '').strip()
        if not clean_val or clean_val.lower() == 'none':
            return Decimal('0')
        return Decimal(clean_val)
    except:
        return Decimal('0')

class FinancialDashboardView(APIView):
    """GET /api/ui/dashboard/financial/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.db.models import Sum, Count

        active_expedientes = Expediente.objects.exclude(
            status__in=['CERRADO', 'CANCELADO']
        )

        total_cost = CostLine.objects.filter(
            expediente__in=active_expedientes
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        invoiced_artifacts = ArtifactInstance.objects.filter(
            artifact_type='ART-09',
            status='completed',
            expediente__in=active_expedientes,
        )
        total_invoiced = Decimal('0')
        for art in invoiced_artifacts:
            total_invoiced += _safe_decimal(art.payload.get('total_client_view'))

        total_paid = PaymentLine.objects.filter(
            expediente__in=active_expedientes
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        total_receivables = total_invoiced - total_paid
        margin = total_invoiced - total_cost
        active_count = active_expedientes.count()

        brands_qs = active_expedientes.values('brand').annotate(
            count=Count('expediente_id'),
            total_cost=Sum('cost_lines__amount'),
        )
        brand_breakdown = []
        for b in brands_qs:
            brand_invoiced = Decimal('0')
            brand_arts = ArtifactInstance.objects.filter(
                artifact_type='ART-09',
                status='completed',
                expediente__brand=b['brand'],
                expediente__in=active_expedientes,
            )
            for art in brand_arts:
                brand_invoiced += _safe_decimal(art.payload.get('total_client_view'))
            brand_breakdown.append({
                'brand': b['brand'] or 'Sin marca',
                'count': b['count'],
                'total_cost': float(b['total_cost'] or 0),
                'total_invoiced': float(brand_invoiced),
            })

        return Response({
            'cards': {
                'active_count': active_count,
                'total_cost': float(total_cost),
                'total_invoiced': float(total_invoiced),
                'total_paid': float(total_paid),
                'total_receivables': float(total_receivables),
                'margin': float(margin),
                'currency': 'USD',
            },
            'brand_breakdown': brand_breakdown,
        })


# ═══════════════════════════════════════════════════════════════════
# UI: Legal Entities (para formularios frontend)
# ═══════════════════════════════════════════════════════════════════

class LegalEntitiesListView(APIView):
    """GET /api/ui/expedientes/legal-entities/?role=CLIENT|OPERATOR|ALL
    Devuelve la lista de LegalEntity para poblar selects en el frontend.
    Sin filtro de status para no excluir registros en onboarding.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.expedientes.models import LegalEntity

        role = request.query_params.get('role')
        qs = LegalEntity.objects.all().order_by('legal_name')

        if role and role != 'ALL':
            qs = qs.filter(role=role)

        data = [
            {
                'entity_id': e.entity_id,
                'legal_name': e.legal_name,
                'country': e.country,
                'role': e.role,
            }
            for e in qs
        ]
        return Response(data)


# ═══════════════════════════════════════════════════════════════════
# FINANCIAL SUMMARY — GET /api/expedientes/<pk>/financial-summary/
# Usado por CostsSection en el frontend del detalle de expediente
# ═══════════════════════════════════════════════════════════════════

class FinancialSummaryView(APIView):
    """GET /api/expedientes/<pk>/financial-summary/
    Retorna costos + pagos + resumen financiero del expediente.
    Accesible para usuarios autenticados (CEO ve todo, otros solo vista cliente).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        from django.db.models import Sum
        exp = _get_expediente(pk)
        if not exp:
            return Response({'detail': 'Not found.'}, status=404)

        is_ceo = request.user.is_superuser

        # Costos
        costs_qs = exp.cost_lines.all() if is_ceo else exp.cost_lines.filter(visibility='client')
        costs_data = [
            {
                'cost_id': str(c.pk),
                'cost_type': c.cost_type,
                'amount': float(c.amount),
                'currency': c.currency,
                'phase': c.phase,
                'description': c.description,
                'visibility': c.visibility,
            }
            for c in costs_qs
        ]

        total_costs = costs_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0')

        # Pagos
        payments_qs = exp.payment_lines.all()
        payments_data = [
            {
                'payment_id': str(p.pk),
                'amount': float(p.amount),
                'currency': p.currency,
                'method': p.method,
                'reference': p.reference,
                'registered_at': p.registered_at,
            }
            for p in payments_qs
        ]
        total_paid = payments_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0')

        # Factura ART-09
        invoice = None
        art09 = exp.artifacts.filter(artifact_type='ART-09', status='completed').order_by('-created_at').first()
        if art09:
            payload = dict(art09.payload)
            if not is_ceo:
                for field in ('total_internal_view', 'margin', 'margin_pct'):
                    payload.pop(field, None)
            invoice = payload

        total_invoiced = Decimal('0')
        if art09:
            total_invoiced = Decimal(str(art09.payload.get('total_client_view', 0)))

        balance = total_invoiced - total_paid

        return Response({
            'costs': costs_data,
            'payments': payments_data,
            'invoice': invoice,
            'summary': {
                'total_costs': float(total_costs),
                'total_invoiced': float(total_invoiced),
                'total_paid': float(total_paid),
                'balance_pending': float(balance),
                'payment_status': exp.payment_status,
                'currency': 'USD',
            },
        })


# ═══════════════════════════════════════════════════════════════════
# DOCUMENTS LIST — GET /api/expedientes/<pk>/documents/
# Usado por DocumentMirrorPanel en el frontend del detalle de expediente
# ═══════════════════════════════════════════════════════════════════

class DocumentsListView(APIView):
    """GET /api/expedientes/<pk>/documents/
    Lista todos los artefactos con file_url en el payload.
    Sirve como panel de documentos descargables en el frontend.
    """
    permission_classes = [IsAuthenticated]

    # Tipos de artefacto que pueden tener documento adjunto
    DOCUMENT_ARTIFACT_TYPES = [
        'ART-01', 'ART-02', 'ART-03', 'ART-04',
        'ART-05', 'ART-06', 'ART-07', 'ART-08',
        'ART-09', 'ART-10', 'ART-12', 'ART-19',
    ]

    ARTIFACT_LABELS = {
        'ART-01': 'Orden de Compra',
        'ART-02': 'Proforma',
        'ART-03': 'Decisión Modal',
        'ART-04': 'SAP Confirmado',
        'ART-05': 'Embarque',
        'ART-06': 'Cotización Flete',
        'ART-07': 'Despacho Aprobado',
        'ART-08': 'Despacho Aduanal',
        'ART-09': 'Factura MWT',
        'ART-10': 'BL Registrado',
        'ART-12': 'Nota Compensación',
        'ART-19': 'Decisión Logística',
    }

    def get(self, request, pk):
        exp = _get_expediente(pk)
        if not exp:
            return Response({'detail': 'Not found.'}, status=404)

        artifacts = exp.artifacts.filter(
            artifact_type__in=self.DOCUMENT_ARTIFACT_TYPES,
            status__in=['completed', 'pending'],
        ).order_by('artifact_type', '-created_at')

        documents = []
        for art in artifacts:
            file_url = art.payload.get('file_url')
            documents.append({
                'artifact_id': str(art.artifact_id),
                'artifact_type': art.artifact_type,
                'label': self.ARTIFACT_LABELS.get(art.artifact_type, art.artifact_type),
                'status': art.status,
                'has_file': bool(file_url),
                'file_url': file_url or None,
                'filename': art.payload.get('filename', f'{art.artifact_type}.pdf'),
                'created_at': art.created_at,
            })

        return Response({
            'count': len(documents),
            'documents': documents,
        })


# ═══════════════════════════════════════════════════════════════════
# Sprint 5 Views
# ═══════════════════════════════════════════════════════════════════

class LogisticsSuggestionsView(APIView):
    """S5-07 – GET /api/expedientes/{pk}/logistics-suggestions/
    CEO-only. Returns ranked suggestions from historical data."""
    permission_classes = [IsCEO]

    def get(self, request, pk):
        from apps.expedientes.services import get_logistics_suggestions
        exp = _get_expediente(pk)
        if not exp:
            return Response({'detail': 'Not found.'}, status=404)
        return Response(get_logistics_suggestions(exp))


class HandoffSuggestionView(APIView):
    """S5-06 – GET /api/expedientes/{pk}/handoff-suggestion/"""
    permission_classes = [IsCEO]

    def get(self, request, pk):
        from apps.expedientes.services import get_handoff_suggestion
        exp = _get_expediente(pk)
        if not exp:
            return Response({'detail': 'Not found.'}, status=404)
        return Response(get_handoff_suggestion(exp))


class LiquidationPaymentSuggestionView(APIView):
    """S5-10 – GET /api/expedientes/{pk}/liquidation-payment-suggestion/"""
    permission_classes = [IsCEO]

    def get(self, request, pk):
        from apps.expedientes.services import get_liquidation_payment_suggestion
        exp = _get_expediente(pk)
        if not exp:
            return Response({'detail': 'Not found.'}, status=404)
        return Response(get_liquidation_payment_suggestion(exp))


class CEOOverrideView(APIView):
    """S14-15: POST /api/expedientes/{pk}/ceo-override/"""
    permission_classes = [IsCEO]

    def post(self, request, pk):
        exp = _get_expediente(pk)
        if not exp:
            return Response({'detail': 'Not found.'}, status=404)
        
        target_state = request.data.get('target_state')
        reason = request.data.get('reason')
        if not target_state or not reason:
            return Response({'detail': 'target_state and reason are required'}, status=400)
            
        old_state = exp.status
        exp.status = target_state
        exp.save(update_fields=['status'])
        
        EventLog.objects.create(
            aggregate_id=exp.expediente_id,
            aggregate_type='expediente',
            event_type='CEO_OVERRIDE',
            emitted_by=request.user.email,
            payload={'old_state': old_state, 'new_state': target_state, 'reason': reason}
        )
        return Response({'detail': 'Override successful', 'new_state': exp.status})
