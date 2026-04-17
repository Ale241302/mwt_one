from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.expedientes.models import Expediente, ArtifactInstance
from apps.core.registry import ModuleRegistry
from apps.expedientes.enums_exp import ExpedienteStatus, ArtifactType
from apps.users.models import UserRole
from apps.portal.serializers import ExpedientePortalSerializer

class ClientPortalViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Extends simple Portal to handle historical data, 
    due balances, and S3 signed URLs for artifacts.
    """
    serializer_class = ExpedientePortalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        if "client" not in user.role:
            return Expediente.objects.none()
            
        brand_slug = None
        if user.role == UserRole.CLIENT_MARLUVAS:
            brand_slug = 'marluvas'
        elif user.role == UserRole.CLIENT_TECMATER:
            brand_slug = 'tecmater'
            
        qs = Expediente.objects.all()
        if brand_slug:
            qs = qs.filter(brand_id=brand_slug)
            
        # Optional filter for 'historical' parameter
        historical = self.request.query_params.get('historical', 'false').lower() == 'true'
        if historical:
            return qs.filter(status__in=[ExpedienteStatus.CERRADO, ExpedienteStatus.CANCELADO])
        else:
            return qs.exclude(status__in=[ExpedienteStatus.CERRADO, ExpedienteStatus.CANCELADO])

    @action(detail=False, methods=['get'])
    def financials(self, request):
        qs = self.get_queryset()
        exp_ids = list(qs.values_list('expediente_id', flat=True))
        
        payment_model = ModuleRegistry.get_model('finance', 'Payment')
        if not payment_model:
            return Response({"error": "Finance module unavailable"}, status=503)

        pagos = payment_model.objects.filter(expediente_id__in=exp_ids)
        total_due = sum([p.amount_paid for p in pagos if p.status in ['pending', 'partial']])
        # S25/S26 Verified/Released
        total_credited = sum([p.amount_paid for p in pagos if p.status in ['verified', 'credit_released']])
        
        return Response({
            "total_due_balance": total_due,
            "total_cleared_balance": total_credited,
            "active_orders": qs.count()
        })
        
    @action(detail=True, methods=['get'])
    def download_proforma(self, request, pk=None):
        expediente = self.get_object()
        proforma = ArtifactInstance.objects.filter(
            expediente=expediente, 
            artifact_type=ArtifactType.PROFORMA,
            payload__is_valid=True
        ).last()
        
        if not proforma:
            return Response({"error": "No proforma available"}, status=status.HTTP_404_NOT_FOUND)
            
        # S24 mocked S3 Signed URL generation from payload
        file_url = proforma.payload.get('file_url', '')
        signed_url = f"{file_url}?AuthToken=S24TokenSigned"
        return Response({"download_url": signed_url})
