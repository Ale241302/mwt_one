from rest_framework import viewsets
from .models import InventoryEntry
from .serializers import InventoryEntrySerializer

class InventoryEntryViewSet(viewsets.ModelViewSet):
    queryset = InventoryEntry.objects.all()
    serializer_serializer = InventoryEntrySerializer
    serializer_class = InventoryEntrySerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        node_id = self.request.query_params.get('node')
        product_id = self.request.query_params.get('product')

        if node_id:
            queryset = queryset.filter(node_id=node_id)
        if product_id:
            queryset = queryset.filter(product_id=product_id)
            
        return queryset
