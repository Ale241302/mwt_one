from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework_simplejwt.tokens import RefreshToken
from apps.expedientes.models import Expediente
from django.db.models import Sum
from apps.expedientes.enums_exp import ExpedienteStatus
from apps.core.serializers import UserSerializer, LegalEntitySerializer
from apps.core.models import LegalEntity


@method_decorator(csrf_exempt, name='dispatch')
class HealthView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response({"status": "healthy", "timestamp": timezone.now()}, status=status.HTTP_200_OK)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            refresh = RefreshToken.for_user(user)
            csrf_token = get_token(request)
            return Response({
                'detail': 'Login successful.',
                'user': UserSerializer(user).data,
                'csrfToken': csrf_token,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }, status=status.HTTP_200_OK)
        return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({'detail': 'Logout successful.'}, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
class MeView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        get_token(request)
        if not request.user.is_authenticated:
            return Response({"detail": "Not authenticated"}, status=status.HTTP_403_FORBIDDEN)
        return Response({'user': UserSerializer(request.user).data})


# GET /api/core/legal-entities/
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_legal_entities(request):
    qs = LegalEntity.objects.order_by('legal_name')
    paginator = PageNumberPagination()
    paginator.page_size = 200
    page = paginator.paginate_queryset(qs, request)
    return paginator.get_paginated_response(LegalEntitySerializer(page, many=True).data)


class DashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from apps.expedientes.models import CostLine
        from apps.expedientes.serializers_ui import UIExpedienteListSerializer
        from django.utils import timezone

        active_qs = Expediente.objects.exclude(
            status__in=[ExpedienteStatus.CERRADO, ExpedienteStatus.CANCELADO]
        ).select_related('client').prefetch_related('artifacts', 'cost_lines')

        active_list = list(active_qs)

        exp_ids = [e.pk for e in active_list]
        events_by_exp = {}
        if exp_ids:
            from apps.expedientes.models import EventLog
            from apps.expedientes.enums_exp import AggregateType
            all_events = EventLog.objects.filter(
                aggregate_id__in=exp_ids,
                aggregate_type=AggregateType.EXPEDIENTE
            ).order_by('occurred_at')
            for ev in all_events:
                events_by_exp.setdefault(ev.aggregate_id, []).append(ev)

        now = timezone.now()
        alerts_list_data = []
        top_risk_data = []

        for exp in active_list:
            exp.total_cost = sum(c.amount for c in exp.cost_lines.all())
            exp.artifact_count = exp.artifacts.count()

            exp_events = events_by_exp.get(exp.pk, [])
            exp.last_event_at = exp_events[-1].occurred_at if exp_events else None

            if exp.credit_clock_started_at:
                days = (now - exp.credit_clock_started_at).days
                exp.credit_days_elapsed = days
                if days <= 15:
                    exp.credit_band = 'OK'
                elif days <= 30:
                    exp.credit_band = 'WARNING'
                    alerts_list_data.append(exp)
                else:
                    exp.credit_band = 'CRITICAL'
                    alerts_list_data.append(exp)
                    top_risk_data.append(exp)
            else:
                exp.credit_days_elapsed = 0
                exp.credit_band = 'MINT'

            if exp.is_blocked and exp not in alerts_list_data:
                alerts_list_data.append(exp)

        top_risk_data.sort(key=lambda x: x.credit_days_elapsed, reverse=True)
        top_risk_data = top_risk_data[:5]

        blocked_qs = [exp for exp in active_list if exp.is_blocked]

        active_count = len(active_list)
        alert_count = len(alerts_list_data)
        blocked_count = len(blocked_qs)

        total_cost = CostLine.objects.aggregate(total=Sum('amount'))['total'] or 0

        by_status_dict = {}
        for exp in active_list:
            by_status_dict[exp.status] = by_status_dict.get(exp.status, 0) + 1
        
        by_status = [{"status": k, "count": v} for k, v in by_status_dict.items()]

        next_actions = [
            {
                "id": str(e.expediente_id),
                "ref_number": f"EXP-{str(e.expediente_id)[:8]}",
                "client": e.client.legal_name if e.client else 'N/A',
                "action": f"Revisar ({e.status})",
                "urgency": "high" if getattr(e, 'credit_band', '') == "CRITICAL" else "medium"
            } for e in top_risk_data
        ]
        if not next_actions:
            next_actions = [
                {
                    "id": str(e.expediente_id),
                    "ref_number": f"EXP-{str(e.expediente_id)[:8]}",
                    "client": e.client.legal_name if e.client else 'N/A',
                    "action": f"Avanzar ({e.status})",
                    "urgency": "normal"
                } for e in active_list[:3]
            ]
        else:
            next_actions = next_actions[:3]

        return Response({
            'active_count': active_count,
            'alert_count': alert_count,
            'blocked_count': blocked_count,
            'total_cost': total_cost,
            'top_risk': UIExpedienteListSerializer(top_risk_data, many=True).data,
            'blocked_list': UIExpedienteListSerializer(blocked_qs, many=True).data,
            'alerts_list': UIExpedienteListSerializer(alerts_list_data, many=True).data,
            'by_status': by_status,
            'next_actions': next_actions,
        })
