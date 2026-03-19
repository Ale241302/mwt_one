from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from apps.expedientes.models import Expediente
from apps.users.models import UserRole
from .serializers import ExpedientePortalSerializer

class PortalExpedienteViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ExpedientePortalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        # Determine brand from user role
        brand_slug = None
        if user.role == UserRole.CLIENT_MARLUVAS:
            brand_slug = 'marluvas'
        elif user.role == UserRole.CLIENT_TECMATER:
            brand_slug = 'tecmater'
            
        if user.role == UserRole.CEO or user.role == UserRole.INTERNAL:
            return Expediente.objects.all()
            
        if brand_slug:
            return Expediente.objects.filter(brand_id=brand_slug)
            
        return Expediente.objects.none()

    @action(detail=True, methods=['get'])
    def artifacts(self, request, pk=None):
        expediente = self.get_object()
        from apps.expedientes.models import ArtifactInstance
        from .serializers import ArtifactPortalSerializer
        
        artifacts = ArtifactInstance.objects.filter(expediente=expediente)
        serializer = ArtifactPortalSerializer(artifacts, many=True)
        return Response(serializer.data)
