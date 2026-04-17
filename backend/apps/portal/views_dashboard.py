from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.users.models import UserRole
from apps.dashboard.models import DashboardKPI
from django.utils import timezone
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

class CEODashboardAjaxView(APIView):
    """S32: Polling endpoint para realtime stats del CEO dashboard (Opción A)"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if request.user.role != UserRole.CEO:
            return Response({"error": "Forbidden"}, status=403)
            
        def get_metric(name, default=0):
            kpi = DashboardKPI.objects.filter(metric_name=name).first()
            return kpi.metric_value if kpi else default

        return Response({
            "action_needed_count": int(get_metric('action_needed_count')),
            "pending_proformas_count": int(get_metric('pending_proformas_count')),
            "pipeline_count": int(get_metric('pipeline_count')),
            "latest_activity": [] # Se obtendría de un servicio de historial dedicado
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
        
        def get_metric(name, default=0):
            kpi = DashboardKPI.objects.filter(metric_name=name).first()
            return kpi.metric_value if kpi else default

        context['pipeline_count'] = int(get_metric('pipeline_count'))
        context['pending_proformas_count'] = int(get_metric('pending_proformas_count'))
        context['action_needed_count'] = int(get_metric('action_needed_count'))
        context['pending_collections_sum'] = get_metric('pending_collections_sum')
        
        # S21: Activity Feed Connect (Placeholder - Debería venir de apps.historial)
        context['activity_feed'] = [] 
        
        return context
