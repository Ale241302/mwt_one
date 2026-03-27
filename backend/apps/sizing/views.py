from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import SizeSystem
from .serializers import SizeSystemSerializer


class SizeSystemViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet de solo lectura para SizeSystems. Usado por el frontend."""
    queryset = SizeSystem.objects.filter(is_active=True).prefetch_related(
        'dimensions', 'entries__equivalences'
    )
    serializer_class = SizeSystemSerializer
    permission_classes = [permissions.IsAuthenticated]
