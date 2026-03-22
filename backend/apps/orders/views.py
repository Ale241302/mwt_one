from rest_framework import viewsets
from .models import ClientOrder
from .serializers import ClientOrderSerializer

class ClientOrderViewSet(viewsets.ModelViewSet):
    queryset = ClientOrder.objects.all()
    serializer_class = ClientOrderSerializer

    def get_queryset(self):
        # Filtering for portal context or brand context
        user = self.request.user
        qs = super().get_queryset()
        if not user.is_superuser:
            # S14: Example scoping - for now returning all or filter by user's client if applicable
            pass
        return qs
