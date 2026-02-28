"""
Sprint 1 — API Endpoints (views.py)
18 APIViews, 1 per command. No ViewSet.
Ref: LOTE_SM_SPRINT1 Items 3-6, FIX-1 (response format), FIX-8 (block bypass)
"""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.expedientes.models import Expediente, EventLog
from apps.expedientes.serializers import (
    ExpedienteSerializer, EventLogSerializer, ArtifactInstanceSerializer,
    ExpedienteCreateSerializer, ArtifactPayloadSerializer,
    RegisterCostSerializer, RegisterPaymentSerializer,
    SupersedeArtifactSerializer,
)
from apps.expedientes.services import (
    create_expediente, execute_command, supersede_artifact, void_artifact
)
from apps.expedientes.permissions import IsCEO, EnsureNotBlocked


# ══════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════

def _command_response(expediente, events, http_status):
    """Standard response format (FIX-1): {"expediente": {...}, "events": [...]}"""
    return Response(
        {
            'expediente': ExpedienteSerializer(expediente).data,
            'events': EventLogSerializer(events, many=True).data,
        },
        status=http_status,
    )


def _get_expediente(pk):
    """Fetch expediente or 404."""
    try:
        return Expediente.objects.get(pk=pk)
    except Expediente.DoesNotExist:
        from rest_framework.exceptions import NotFound
        raise NotFound(f'Expediente {pk} not found.')


# ══════════════════════════════════════════════════
# LIST & BUNDLE (Sprint 3)
# ══════════════════════════════════════════════════

from apps.expedientes.services import get_available_commands, COMMAND_SPEC
from apps.expedientes.serializers_ui import UIExpedienteListSerializer, ExpedienteBundleSerializer
from django.utils import timezone

from rest_framework.pagination import PageNumberPagination

class ExpedientePagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100

class ListExpedientesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Expediente.objects.select_related('client').prefetch_related(
            'artifacts', 'cost_lines'
        ).all()

        # Filtros
        status_param = request.query_params.get('status')
        brand_param  = request.query_params.get('brand_name')
        client_param = request.query_params.get('client_name__icontains')
        is_blocked   = request.query_params.get('is_blocked')
        ordering     = request.query_params.get('ordering', '-created_at')

        if status_param:
            qs = qs.filter(status=status_param)
        if brand_param:
            qs = qs.filter(brand=brand_param)
        if client_param:
            qs = qs.filter(client__legal_name__icontains=client_param)
        if is_blocked == 'true':
            qs = qs.filter(is_blocked=True)

        # Ordenamiento seguro
        ALLOWED_ORDERINGS = {
            'created_at', '-created_at',
            'credit_days_elapsed', '-credit_days_elapsed',
            'total_cost', '-total_cost',
            'last_event_at', '-last_event_at',
            'status', '-status',
        }
        if ordering not in ALLOWED_ORDERINGS:
            ordering = '-created_at'
        # Nota: credit_days_elapsed, total_cost, last_event_at son calculados, usamos DB fallback
        db_ordering = ordering if ordering.lstrip('-') in ('created_at', 'status') else '-created_at'
        qs = qs.order_by(db_ordering)

        now = timezone.now()
        exp_list = list(qs)
        exp_ids  = [e.pk for e in exp_list]

        events_by_exp = {}
        if exp_ids:
            from apps.expedientes.enums import AggregateType
            for ev in EventLog.objects.filter(
                aggregate_id__in=exp_ids,
                aggregate_type=AggregateType.EXPEDIENTE
            ).order_by('occurred_at'):
                events_by_exp.setdefault(ev.aggregate_id, []).append(ev)

        for exp in exp_list:
            exp.total_cost    = sum(c.amount for c in exp.cost_lines.all())
            exp.artifact_count = exp.artifacts.count()
            evs = events_by_exp.get(exp.pk, [])
            exp.last_event_at = evs[-1].occurred_at if evs else None

            if exp.credit_clock_started_at:
                days = (now - exp.credit_clock_started_at).days
                exp.credit_days_elapsed = days
                if days >= 75:
                    exp.credit_band = 'CORAL'
                elif days >= 60:
                    exp.credit_band = 'AMBER'
                else:
                    exp.credit_band = 'MINT'
            else:
                exp.credit_days_elapsed = 0
                exp.credit_band = 'MINT'

        # Paginación — retorna {count, next, previous, results}
        paginator = ExpedientePagination()
        page = paginator.paginate_queryset(exp_list, request)
        data = UIExpedienteListSerializer(page, many=True).data
        return paginator.get_paginated_response(data)

class ExpedienteBundleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        exp = _get_expediente(pk)
        
        now = timezone.now()
        exp.total_cost = sum(c.amount for c in exp.cost_lines.all())
        exp.artifact_count = exp.artifacts.count()
        
        from apps.expedientes.models import EventLog
        from apps.expedientes.enums import AggregateType
        
        exp_events = list(EventLog.objects.filter(
            aggregate_id=exp.pk, 
            aggregate_type=AggregateType.EXPEDIENTE
        ).order_by('occurred_at'))
        
        exp.events = exp_events
        exp.last_event_at = exp_events[-1].occurred_at if exp_events else None
        
        if exp.credit_clock_started_at:
            days = (now - exp.credit_clock_started_at).days
            exp.credit_days_elapsed = days
            if days >= 75:
                exp.credit_band = 'CORAL'
            elif days >= 60:
                exp.credit_band = 'AMBER'
            else:
                exp.credit_band = 'MINT'
        else:
            exp.credit_days_elapsed = 0
            exp.credit_band = 'MINT'
        
        available_cmds = get_available_commands(exp, request.user)
        exp.available_actions = [
            {'command': c, 'name': COMMAND_SPEC[c]['name']} for c in available_cmds
        ]
        
        data = ExpedienteBundleSerializer(exp).data
        return Response(data)


# ══════════════════════════════════════════════════
# C1: CreateExpediente  (POST /api/expedientes/)
# ══════════════════════════════════════════════════

class CreateExpedienteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = ExpedienteCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        expediente, event = create_expediente(ser.validated_data, request.user)
        return _command_response(expediente, [event], status.HTTP_201_CREATED)


# ══════════════════════════════════════════════════
# C2: RegisterOC  (POST /api/expedientes/{pk}/register-oc/)
# ══════════════════════════════════════════════════

class RegisterOCView(APIView):
    permission_classes = [IsAuthenticated, EnsureNotBlocked]

    def post(self, request, pk):
        exp = _get_expediente(pk)
        self.check_object_permissions(request, exp)
        ser = ArtifactPayloadSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        exp, events = execute_command(exp, 'C2', ser.validated_data, request.user)
        return _command_response(exp, events, status.HTTP_201_CREATED)


# ══════════════════════════════════════════════════
# C3: RegisterProforma  (POST /api/expedientes/{pk}/register-proforma/)
# ══════════════════════════════════════════════════

class RegisterProformaView(APIView):
    permission_classes = [IsAuthenticated, EnsureNotBlocked]

    def post(self, request, pk):
        exp = _get_expediente(pk)
        self.check_object_permissions(request, exp)
        ser = ArtifactPayloadSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        exp, events = execute_command(exp, 'C3', ser.validated_data, request.user)
        return _command_response(exp, events, status.HTTP_201_CREATED)


# ══════════════════════════════════════════════════
# C4: DecideMode  (POST /api/expedientes/{pk}/decide-mode/) — CEO only
# ══════════════════════════════════════════════════

class DecideModeView(APIView):
    permission_classes = [IsAuthenticated, IsCEO, EnsureNotBlocked]

    def post(self, request, pk):
        exp = _get_expediente(pk)
        self.check_object_permissions(request, exp)
        ser = ArtifactPayloadSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        exp, events = execute_command(exp, 'C4', ser.validated_data, request.user)
        return _command_response(exp, events, status.HTTP_201_CREATED)


# ══════════════════════════════════════════════════
# C5: ConfirmSAP  (POST /api/expedientes/{pk}/confirm-sap/)
# Auto-transition → PRODUCCION, 2 events (FIX-5)
# ══════════════════════════════════════════════════

class ConfirmSAPView(APIView):
    permission_classes = [IsAuthenticated, EnsureNotBlocked]

    def post(self, request, pk):
        exp = _get_expediente(pk)
        self.check_object_permissions(request, exp)
        ser = ArtifactPayloadSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        exp, events = execute_command(exp, 'C5', ser.validated_data, request.user)
        return _command_response(exp, events, status.HTTP_201_CREATED)


# ══════════════════════════════════════════════════
# C6: ConfirmProduction  (POST /api/expedientes/{pk}/confirm-production/)
# ══════════════════════════════════════════════════

class ConfirmProductionView(APIView):
    permission_classes = [IsAuthenticated, EnsureNotBlocked]

    def post(self, request, pk):
        exp = _get_expediente(pk)
        self.check_object_permissions(request, exp)
        exp, events = execute_command(exp, 'C6', {}, request.user)
        return _command_response(exp, events, status.HTTP_200_OK)


# ══════════════════════════════════════════════════
# C7: RegisterShipment  (POST /api/expedientes/{pk}/register-shipment/)
# FIX-3: credit_clock persist if rule=on_shipment
# ══════════════════════════════════════════════════

class RegisterShipmentView(APIView):
    permission_classes = [IsAuthenticated, EnsureNotBlocked]

    def post(self, request, pk):
        exp = _get_expediente(pk)
        self.check_object_permissions(request, exp)
        ser = ArtifactPayloadSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        exp, events = execute_command(exp, 'C7', ser.validated_data, request.user)
        return _command_response(exp, events, status.HTTP_201_CREATED)


# ══════════════════════════════════════════════════
# C8: RegisterFreightQuote  (POST /api/expedientes/{pk}/register-freight-quote/)
# ══════════════════════════════════════════════════

class RegisterFreightQuoteView(APIView):
    permission_classes = [IsAuthenticated, EnsureNotBlocked]

    def post(self, request, pk):
        exp = _get_expediente(pk)
        self.check_object_permissions(request, exp)
        ser = ArtifactPayloadSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        exp, events = execute_command(exp, 'C8', ser.validated_data, request.user)
        return _command_response(exp, events, status.HTTP_201_CREATED)


# ══════════════════════════════════════════════════
# C9: RegisterCustoms  (POST /api/expedientes/{pk}/register-customs/)
# Requires dispatch_mode=mwt
# ══════════════════════════════════════════════════

class RegisterCustomsView(APIView):
    permission_classes = [IsAuthenticated, EnsureNotBlocked]

    def post(self, request, pk):
        exp = _get_expediente(pk)
        self.check_object_permissions(request, exp)
        ser = ArtifactPayloadSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        exp, events = execute_command(exp, 'C9', ser.validated_data, request.user)
        return _command_response(exp, events, status.HTTP_201_CREATED)


# ══════════════════════════════════════════════════
# C10: ApproveDispatch  (POST /api/expedientes/{pk}/approve-dispatch/)
# Auto-transition → DESPACHO, 2 events (FIX-5)
# ══════════════════════════════════════════════════

class ApproveDispatchView(APIView):
    permission_classes = [IsAuthenticated, EnsureNotBlocked]

    def post(self, request, pk):
        exp = _get_expediente(pk)
        self.check_object_permissions(request, exp)
        ser = ArtifactPayloadSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        exp, events = execute_command(exp, 'C10', ser.validated_data, request.user)
        return _command_response(exp, events, status.HTTP_201_CREATED)


# ══════════════════════════════════════════════════
# C11: ConfirmDeparture  (POST /api/expedientes/{pk}/confirm-departure/)
# ══════════════════════════════════════════════════

class ConfirmDepartureView(APIView):
    permission_classes = [IsAuthenticated, EnsureNotBlocked]

    def post(self, request, pk):
        exp = _get_expediente(pk)
        self.check_object_permissions(request, exp)
        exp, events = execute_command(exp, 'C11', {}, request.user)
        return _command_response(exp, events, status.HTTP_200_OK)


# ══════════════════════════════════════════════════
# C12: ConfirmArrival  (POST /api/expedientes/{pk}/confirm-arrival/)
# ══════════════════════════════════════════════════

class ConfirmArrivalView(APIView):
    permission_classes = [IsAuthenticated, EnsureNotBlocked]

    def post(self, request, pk):
        exp = _get_expediente(pk)
        self.check_object_permissions(request, exp)
        exp, events = execute_command(exp, 'C12', {}, request.user)
        return _command_response(exp, events, status.HTTP_200_OK)


# ══════════════════════════════════════════════════
# C13: IssueInvoice  (POST /api/expedientes/{pk}/issue-invoice/)
# ══════════════════════════════════════════════════

class IssueInvoiceView(APIView):
    permission_classes = [IsAuthenticated, EnsureNotBlocked]

    def post(self, request, pk):
        exp = _get_expediente(pk)
        self.check_object_permissions(request, exp)
        ser = ArtifactPayloadSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        exp, events = execute_command(exp, 'C13', ser.validated_data, request.user)
        return _command_response(exp, events, status.HTTP_201_CREATED)


# ══════════════════════════════════════════════════
# C14: CloseExpediente  (POST /api/expedientes/{pk}/close/)
# ══════════════════════════════════════════════════

class CloseExpedienteView(APIView):
    permission_classes = [IsAuthenticated, EnsureNotBlocked]

    def post(self, request, pk):
        exp = _get_expediente(pk)
        self.check_object_permissions(request, exp)
        exp, events = execute_command(exp, 'C14', {}, request.user)
        return _command_response(exp, events, status.HTTP_200_OK)


# ══════════════════════════════════════════════════
# C15: RegisterCost  (POST /api/expedientes/{pk}/register-cost/)
# ══════════════════════════════════════════════════

class RegisterCostView(APIView):
    permission_classes = [IsAuthenticated, EnsureNotBlocked]

    def post(self, request, pk):
        exp = _get_expediente(pk)
        self.check_object_permissions(request, exp)
        ser = RegisterCostSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        exp, events = execute_command(exp, 'C15', ser.validated_data, request.user)
        return _command_response(exp, events, status.HTTP_201_CREATED)


# ══════════════════════════════════════════════════
# C16: CancelExpediente  (POST /api/expedientes/{pk}/cancel/)
# CEO only. NO EnsureNotBlocked (FIX-8).
# ══════════════════════════════════════════════════

class CancelExpedienteView(APIView):
    permission_classes = [IsAuthenticated, IsCEO]     # NO EnsureNotBlocked FIX-8

    def post(self, request, pk):
        exp = _get_expediente(pk)
        self.check_object_permissions(request, exp)
        exp, events = execute_command(exp, 'C16', {}, request.user)
        return _command_response(exp, events, status.HTTP_200_OK)


# ══════════════════════════════════════════════════
# C17: BlockExpediente  (POST /api/expedientes/{pk}/block/)
# NO EnsureNotBlocked (FIX-8). Precondition: is_blocked=false.
# ══════════════════════════════════════════════════

class BlockExpedienteView(APIView):
    permission_classes = [IsAuthenticated]             # NO EnsureNotBlocked FIX-8

    def post(self, request, pk):
        exp = _get_expediente(pk)
        self.check_object_permissions(request, exp)
        data = {'reason': request.data.get('reason', '')}
        exp, events = execute_command(exp, 'C17', data, request.user)
        return _command_response(exp, events, status.HTTP_200_OK)


# ══════════════════════════════════════════════════
# C18: UnblockExpediente  (POST /api/expedientes/{pk}/unblock/)
# CEO only. NO EnsureNotBlocked (FIX-8).
# ══════════════════════════════════════════════════

class UnblockExpedienteView(APIView):
    permission_classes = [IsAuthenticated, IsCEO]     # NO EnsureNotBlocked FIX-8

    def post(self, request, pk):
        exp = _get_expediente(pk)
        self.check_object_permissions(request, exp)
        exp, events = execute_command(exp, 'C18', {}, request.user)
        return _command_response(exp, events, status.HTTP_200_OK)


# ══════════════════════════════════════════════════
# C21: RegisterPayment  (POST /api/expedientes/{pk}/register-payment/)
# ══════════════════════════════════════════════════

class RegisterPaymentView(APIView):
    permission_classes = [IsAuthenticated, EnsureNotBlocked]

    def post(self, request, pk):
        exp = _get_expediente(pk)
        self.check_object_permissions(request, exp)
        ser = RegisterPaymentSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        exp, events = execute_command(exp, 'C21', ser.validated_data, request.user)
        return _command_response(exp, events, status.HTTP_201_CREATED)


# ══════════════════════════════════════════════════
# C19 & C20: Artifact Correction
# ══════════════════════════════════════════════════

class SupersedeArtifactView(APIView):
    permission_classes = [IsAuthenticated, IsCEO]

    def post(self, request, pk, artifact_id):
        exp = _get_expediente(pk)
        self.check_object_permissions(request, exp)
        ser = SupersedeArtifactSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        exp, new_art, event = supersede_artifact(artifact_id, ser.validated_data['payload'], request.user)
        return Response(
            {
                'expediente': ExpedienteSerializer(exp).data,
                'artifact': ArtifactInstanceSerializer(new_art).data,
                'events': EventLogSerializer([event], many=True).data
            },
            status=status.HTTP_201_CREATED
        )


class VoidArtifactView(APIView):
    permission_classes = [IsAuthenticated, IsCEO]

    def post(self, request, pk, artifact_id):
        exp = _get_expediente(pk)
        self.check_object_permissions(request, exp)
        exp, voided_art, event = void_artifact(artifact_id, request.user)
        return Response(
            {
                'expediente': ExpedienteSerializer(exp).data,
                'artifact': ArtifactInstanceSerializer(voided_art).data,
                'events': EventLogSerializer([event], many=True).data
            },
            status=status.HTTP_200_OK
        )

