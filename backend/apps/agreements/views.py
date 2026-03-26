from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from .models import CreditOverride, CreditPolicy, CreditExposure
from .serializers import CreditOverrideSerializer

class CreditOverrideViewSet(viewsets.ModelViewSet):
    queryset = CreditOverride.objects.all()
    serializer_class = CreditOverrideSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            # Must be CEO
            class IsCEO(permissions.BasePermission):
                def has_permission(self, request, view):
                    # Fallback to is_superuser if role field is not properly populated
                    return request.user.is_authenticated and (getattr(request.user, 'role', '') == 'CEO' or request.user.is_superuser)
            return [IsCEO()]
        return super().get_permissions()

    @action(detail=False, methods=['get'], url_path='credit-status')
    def credit_status(self, request):
        """S16-01E: Reporte de Saldo de Crédito."""
        # Assume one global policy or filter by brand/client if needed
        # For now, let's take the latest active policy
        policy = CreditPolicy.objects.filter(status='active').order_by('-valid_daterange').first()
        
        if not policy:
            return Response({"error": "No active credit policy found"}, status=status.HTTP_404_NOT_FOUND)

        total_limit = policy.max_amount
        
        # Reserved: Sum of reserved_amount in CreditExposure for active expedientes
        # Exposure is updated by C1...C14
        total_reserved = CreditExposure.objects.aggregate(total=Sum('reserved_amount'))['total'] or 0
        
        total_available = total_limit - total_reserved
        
        overrides_active = CreditOverride.objects.count()

        return Response({
            "total_limit": float(total_limit),
            "total_reserved": float(total_reserved),
            "total_available": float(total_available),
            "overrides_active": overrides_active,
            "policy_id": str(policy.pk)
        })
