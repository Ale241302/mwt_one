from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Supplier, SupplierContact, SupplierPerformanceKPI
from apps.agreements.models import BrandSupplierAgreement
from .serializers import (
    SupplierSerializer, SupplierContactSerializer, 
    SupplierPerformanceKPISerializer, BrandSupplierAgreementSerializer
)


class SupplierViewSet(viewsets.ModelViewSet):
    """
    S16-P1: ViewSet for Suppliers with 11 actions.
    """
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    filterset_fields = ['country', 'is_active']
    search_fields = ['name', 'tax_id']

    def get_queryset(self):
        qs = super().get_queryset()
        brand_id = self.request.query_params.get('brand')
        if brand_id:
            # Filter suppliers that have agreements with this brand
            supplier_ids = BrandSupplierAgreement.objects.filter(
                brand_id=brand_id, status='active'
            ).values_list('supplier_id', flat=True)
            qs = qs.filter(id__in=supplier_ids)
        return qs

    # 1-5: list, retrieve, create, update, destroy are provided by ModelViewSet

    @action(detail=True, methods=['get'])
    def contacts(self, request, pk=None):
        """Action 6: Get supplier contacts."""
        supplier = self.get_object()
        contacts = supplier.contacts.all()
        serializer = SupplierContactSerializer(contacts, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def performance(self, request, pk=None):
        """Action 7: Get supplier performance KPIs."""
        supplier = self.get_object()
        kpis = supplier.performance_kpis.all().order_by('-year', '-month')
        serializer = SupplierPerformanceKPISerializer(kpis, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def catalog(self, request, pk=None):
        """Action 8: Get supplier product catalog."""
        # Current schema doesn't have a direct Product-Supplier link yet beyond agreements.
        # Returning empty as per requirement "Empty state si count === 0".
        return Response({
            "count": 0,
            "results": []
        })

    @action(detail=True, methods=['get'])
    def agreements(self, request, pk=None):
        """Action 9: Get supplier agreements."""
        supplier = self.get_object()
        agreements = BrandSupplierAgreement.objects.filter(supplier_id=supplier.id)
        serializer = BrandSupplierAgreementSerializer(agreements, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def compliance(self, request, pk=None):
        """Action 10: Get compliance status (Simulated)."""
        return Response({
            "supplier_id": pk,
            "status": "COMPLIANT",
            "score": 100,
            "pending_documents": []
        })

    @action(detail=True, methods=['post'])
    def register_kpi(self, request, pk=None):
        """Action 12: Register a new performance KPI period."""
        supplier = self.get_object()
        data = request.data.copy()
        data['supplier'] = supplier.id
        
        # Simple calculation for overall_rating if not provided
        if 'overall_rating' not in data:
            weights = {'on_time_delivery_score': 0.4, 'quality_score': 0.4, 'cost_score': 0.2}
            try:
                score = (
                    float(data.get('on_time_delivery_score', 0)) * weights['on_time_delivery_score'] +
                    float(data.get('quality_score', 0)) * weights['quality_score'] +
                    float(data.get('cost_score', 0)) * weights['cost_score']
                )
                data['overall_rating'] = round(float(score), 2)
            except (ValueError, TypeError):
                data['overall_rating'] = 0

        serializer = SupplierPerformanceKPISerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def audit(self, request, pk=None):
        """Action 11: Get audit logs (Simulated)."""
        return Response({
            "supplier_id": pk,
            "audit_logs": [
                {"timestamp": "2026-03-20", "action": "LOGIN", "user": "admin"},
                {"timestamp": "2026-03-15", "action": "KPI_UPDATE", "user": "system"}
            ]
        })
