"""
Sprint 1-4 — Views (views.py)
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
)
from apps.expedientes.serializers_ui import (
    UIExpedienteListSerializer, ExpedienteBundleSerializer,
    CostLineSummarySerializer, ArtifactSummarySerializer,
)


# ─── Permissions ──────────────────────────────────

class IsCEO(IsAuthenticated):
    """CEO = superuser."""
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_superuser


class EnsureNotBlocked(IsAuthenticated):
    """Skip if command has bypass_block."""
    pass


# ─── Helpers ──────────────────────────────────────

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


# ═══════════════════════════════════════════════════
# SPRINT 1 COMMANDS (C1-C21)
# ═══════════════════════════════════════════════════

class CreateExpedienteView(APIView):
    """C1: POST /api/expedientes/create/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        exp, event = create_expediente(request.data, request.user)
        return _command_response(exp, [event], status_code=201)


class CommandView(APIView):
    """Generic POST for C2-C18."""
    permission_classes = [IsAuthenticated]
    command_name = None

    def post(self, request, pk):
        exp = _get_expediente(pk)
        if not exp:
            return Response({'detail': 'Not found.'}, status=404)
        exp, events = execute_command(exp, self.command_name, request.data, request.user)
        return _command_response(exp, events)


# Individual command views
class RegisterOCView(CommandView):
    command_name = 'C2'

class RegisterProformaView(CommandView):
    command_name = 'C3'

class DecideModeView(CommandView):
    permission_classes = [IsCEO]
    command_name = 'C4'

class ConfirmSAPView(CommandView):
    command_name = 'C5'

class ConfirmProductionView(CommandView):
    command_name = 'C6'

class RegisterShipmentView(CommandView):
    command_name = 'C7'

class RegisterFreightQuoteView(CommandView):
    command_name = 'C8'

class RegisterCustomsView(CommandView):
    command_name = 'C9'

class ApproveDispatchView(CommandView):
    command_name = 'C10'

class ConfirmDepartureView(CommandView):
    command_name = 'C11'

class ConfirmArrivalView(CommandView):
    command_name = 'C12'

class IssueInvoiceView(CommandView):
    command_name = 'C13'

class CloseExpedienteView(CommandView):
    command_name = 'C14'

class RegisterCostView(CommandView):
    command_name = 'C15'

class CancelExpedienteView(CommandView):
    permission_classes = [IsCEO]
    command_name = 'C16'

class BlockExpedienteView(CommandView):
    command_name = 'C17'

class UnblockExpedienteView(CommandView):
    permission_classes = [IsCEO]
    command_name = 'C18'

class RegisterPaymentView(CommandView):
    command_name = 'C21'


# ═══════════════════════════════════════════════════
# SPRINT 2 COMMANDS (C19, C20)
# ═══════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════
# SPRINT 3: List + Bundle
# ═══════════════════════════════════════════════════

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

        serializer = UIExpedienteListSerializer(qs, many=True)
        return Response(serializer.data)


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

        # Attach extra context as attributes so the serializer can access them
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


# ═══════════════════════════════════════════════════
# SPRINT 4 NEW ENDPOINTS
# ═══════════════════════════════════════════════════

# ── S4-02: Costs Doble Vista ──

class CostsListView(APIView):
    """GET /api/expedientes/<pk>/costs/?view=internal|client"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        exp = _get_expediente(pk)
        if not exp:
            return Response({'detail': 'Not found.'}, status=404)

        view_param = request.query_params.get('view', 'internal')

        # Client view is always available; internal only for CEO
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


# ── S4-07: ART-19 Logistics ──

class MaterializeLogisticsView(CommandView):
    """C22: POST /api/expedientes/<pk>/materialize-logistics/"""
    command_name = 'C22'


class AddLogisticsOptionView(CommandView):
    """C23: POST /api/expedientes/<pk>/add-logistics-option/"""
    permission_classes = [IsCEO]
    command_name = 'C23'


class DecideLogisticsView(CommandView):
    """C24: POST /api/expedientes/<pk>/decide-logistics/"""
    permission_classes = [IsCEO]
    command_name = 'C24'


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
            # weasyprint not installed, return HTML as fallback
            return HttpResponse(html_content, content_type='text/html')


# ═══════════════════════════════════════════════════
# SPRINT 4 S4-11: Dashboard Financial Endpoints
# ═══════════════════════════════════════════════════

class FinancialDashboardView(APIView):
    """GET /api/ui/dashboard/financial/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.db.models import Sum, Count

        # Financial cards data
        active_expedientes = Expediente.objects.exclude(
            status__in=['CERRADO', 'CANCELADO']
        )

        # Total active costs
        total_cost = CostLine.objects.filter(
            expediente__in=active_expedientes
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        # Total invoiced (from ART-09)
        invoiced_artifacts = ArtifactInstance.objects.filter(
            artifact_type='ART-09',
            status='completed',
            expediente__in=active_expedientes,
        )
        total_invoiced = Decimal('0')
        for art in invoiced_artifacts:
            total_invoiced += Decimal(str(art.payload.get('total_client_view', 0)))

        # Total payments
        total_paid = PaymentLine.objects.filter(
            expediente__in=active_expedientes
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        # Receivables & Margin
        total_receivables = total_invoiced - total_paid
        margin = total_invoiced - total_cost

        # Count
        active_count = active_expedientes.count()

        # Brand breakdown — include total_invoiced per brand
        brands_qs = active_expedientes.values('brand').annotate(
            count=Count('expediente_id'),
            total_cost=Sum('cost_lines__amount'),
        )
        brand_breakdown = []
        for b in brands_qs:
            # Calculate invoiced per brand
            brand_invoiced = Decimal('0')
            brand_arts = ArtifactInstance.objects.filter(
                artifact_type='ART-09',
                status='completed',
                expediente__brand=b['brand'],
                expediente__in=active_expedientes,
            )
            for art in brand_arts:
                brand_invoiced += Decimal(str(art.payload.get('total_client_view', 0)))
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


# ══════════════════════════════════════════════════
# Sprint 5 Views
# ══════════════════════════════════════════════════

class RegisterCompensationView(APIView):
    """S5-05 C29 — POST /api/expedientes/{pk}/register-compensation/
    CEO-only. Creates ART-12 Nota Compensación."""
    permission_classes = [IsCEO]

    def post(self, request, pk):
        from apps.expedientes.services_sprint5 import register_compensation
        exp = Expediente.objects.get(pk=pk)
        artifact = register_compensation(exp, request.data, request.user)
        return Response({
            'artifact_id': str(artifact.artifact_id),
            'artifact_type': artifact.artifact_type,
            'payload': artifact.payload,
        }, status=status.HTTP_201_CREATED)


class LogisticsSuggestionsView(APIView):
    """S5-07 — GET /api/expedientes/{pk}/logistics-suggestions/
    CEO-only. Returns ranked suggestions from historical data."""
    permission_classes = [IsCEO]

    def get(self, request, pk):
        from apps.expedientes.services_sprint5 import get_logistics_suggestions
        exp = Expediente.objects.get(pk=pk)
        return Response(get_logistics_suggestions(exp))


class AddShipmentUpdateView(APIView):
    """S5-08 C36 — POST /api/expedientes/{pk}/add-shipment-update/
    Manual tracking update appended to ART-05."""
    permission_classes = [IsCEO]

    def post(self, request, pk):
        from apps.expedientes.services_sprint5 import add_shipment_update
        exp = Expediente.objects.get(pk=pk)
        artifact = add_shipment_update(exp, request.data, request.user)
        return Response({
            'artifact_id': str(artifact.artifact_id),
            'payload': artifact.payload,
        })


class HandoffSuggestionView(APIView):
    """S5-06 — GET /api/expedientes/{pk}/handoff-suggestion/
    Returns transfer suggestion when expediente is closed with nodo_destino."""
    permission_classes = [IsCEO]

    def get(self, request, pk):
        from apps.expedientes.services_sprint5 import get_handoff_suggestion
        exp = Expediente.objects.get(pk=pk)
        return Response(get_handoff_suggestion(exp))


class LiquidationPaymentSuggestionView(APIView):
    """S5-10 — GET /api/expedientes/{pk}/liquidation-payment-suggestion/
    Suggests C21 payments from reconciled ART-10 lines for COMISION mode."""
    permission_classes = [IsCEO]

    def get(self, request, pk):
        from apps.expedientes.services_sprint5 import get_liquidation_payment_suggestion
        exp = Expediente.objects.get(pk=pk)
        return Response(get_liquidation_payment_suggestion(exp))

