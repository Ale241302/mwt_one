from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.users.models import UserRole
from apps.expedientes.models import Expediente, EventLog, ArtifactInstance, ExpedientePago
from django.utils import timezone
from datetime import timedelta
from apps.expedientes.enums_exp import ExpedienteStatus, ArtifactType, AggregateType
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

class CEODashboardAjaxView(APIView):
    """S32: Polling endpoint para realtime stats del CEO dashboard (Opción A)"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if request.user.role != UserRole.CEO:
            return Response({"error": "Forbidden"}, status=403)
            
        now = timezone.now()
        three_days_ago = now - timedelta(days=3)
        
        active_expedientes = Expediente.objects.exclude(
            status__in=[ExpedienteStatus.CERRADO, ExpedienteStatus.CANCELADO]
        )
        exp_ids = list(active_expedientes.values_list('expediente_id', flat=True))
        
        # Action needed count
        events = EventLog.objects.filter(
            aggregate_id__in=exp_ids,
            aggregate_type=AggregateType.EXPEDIENTE
        ).order_by('aggregate_id', '-occurred_at').distinct('aggregate_id')
        stale_exp_ids = [e.aggregate_id for e in events if e.occurred_at <= three_days_ago]
        
        pending_proformas_count = ArtifactInstance.objects.filter(
            expediente_id__in=exp_ids,
            artifact_type=ArtifactType.PROFORMA,
            payload__is_valid=True
        ).count()
        
        recent_activities = EventLog.objects.filter(
            aggregate_type=AggregateType.EXPEDIENTE
        ).order_by('-occurred_at')[:5]
        
        return Response({
            "action_needed_count": len(stale_exp_ids),
            "pending_proformas_count": pending_proformas_count,
            "pipeline_count": active_expedientes.count(),
            "latest_activity": [{"id": str(a.id), "event": str(a.event_type), "time": a.occurred_at} for a in recent_activities]
        })



class CEODashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'portal/ceo_dashboard.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != UserRole.CEO:
            # Add simple role protection, usually should use custom mixing.
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("CEO area only.")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        three_days_ago = now - timedelta(days=3)
        seven_days_from_now = now + timedelta(days=7)
        seven_days_ago = now - timedelta(days=7)

        active_expedientes = Expediente.objects.exclude(
            status__in=[ExpedienteStatus.CERRADO, ExpedienteStatus.CANCELADO]
        ).select_related('client', 'brand')

        # 1. Expedientes que necesitan acción (no movidos > 3 días)
        exp_ids = list(active_expedientes.values_list('expediente_id', flat=True))
        
        # Get latest event per expediente
        events = EventLog.objects.filter(
            aggregate_id__in=exp_ids,
            aggregate_type=AggregateType.EXPEDIENTE
        ).order_by('aggregate_id', '-occurred_at').distinct('aggregate_id')
        
        stale_exp_ids = [e.aggregate_id for e in events if e.occurred_at <= three_days_ago]
        
        # 2. Proformas pendientes de enviar
        pending_proformas_exp_ids = ArtifactInstance.objects.filter(
            expediente_id__in=exp_ids,
            artifact_type=ArtifactType.PROFORMA,
            payload__is_valid=True
        ).values_list('expediente_id', flat=True)
        
        # 3. Cobros que vencen esta semana (integrado con PaymentStatusMachine S25)
        # Using ExpedientePago limits to 7 days
        payments_due_exp_ids = ExpedientePago.objects.filter(
            expediente_id__in=exp_ids,
            status__in=['pending', 'partial'],
            payment_date__range=[seven_days_ago, seven_days_from_now]
        ).values_list('expediente_id', flat=True)

        action_needed_ids = set(stale_exp_ids) | set(pending_proformas_exp_ids) | set(payments_due_exp_ids)
        
        context['action_needed_expedientes'] = active_expedientes.filter(expediente_id__in=action_needed_ids)
        
        context['pending_proformas'] = ArtifactInstance.objects.filter(
            expediente_id__in=exp_ids,
            artifact_type=ArtifactType.PROFORMA,
            payload__is_valid=True
        ).select_related('expediente', 'expediente__client')

        context['due_payments'] = ExpedientePago.objects.filter(
            expediente_id__in=exp_ids,
            status__in=['pending', 'partial'],
            payment_date__range=[seven_days_ago, seven_days_from_now]
        ).select_related('expediente', 'expediente__client')
        
        # Pipeline Data
        context['pipeline'] = active_expedientes
        
        # S21: Activity Feed Connect
        # Get latest 10 events across all expedientes
        recent_activity = EventLog.objects.filter(
            aggregate_type=AggregateType.EXPEDIENTE
        ).select_related('user').order_by('-occurred_at')[:10]
        context['activity_feed'] = recent_activity

        return context
