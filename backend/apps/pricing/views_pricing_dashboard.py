from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.pricing.models import ClientProductAssignment
from apps.users.models import UserRole
from django.utils import timezone
from datetime import timedelta

class PricingDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role not in [UserRole.CEO, UserRole.INTERNAL, UserRole.VENDOR]:
            return Response({"error": "Unauthorized"}, status=403)
            
        assignments = ClientProductAssignment.objects.all().select_related('brand_sku__brand', 'client_subsidiary')
        
        # S31 Identify stale prices (>90 days without update)
        ninety_days_ago = timezone.now() - timedelta(days=90)
        
        data = []
        for assign in assignments:
            # Assuming simple-history is used, or a generic updated_at field
            last_updated = assign.updated_at
            is_stale = last_updated <= ninety_days_ago
            
            data.append({
                "assignment_id": assign.id,
                "brand": assign.brand_sku.brand.name if assign.brand_sku and assign.brand_sku.brand else None,
                "client": assign.client_subsidiary.legal_name if assign.client_subsidiary else None,
                "sku": assign.brand_sku.sku if assign.brand_sku else None,
                "price": float(assign.cached_client_price) if assign.cached_client_price else 0.0,
                "last_updated": last_updated,
                "is_stale": is_stale,
                "requires_review": is_stale
            })
            
        return Response({
            "stale_count": sum(1 for d in data if d["is_stale"]),
            "items": data
        })
