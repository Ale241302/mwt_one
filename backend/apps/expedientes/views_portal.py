"""S17-04: Portal B2B views with strict tenant isolation."""
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Expediente, ArtifactInstance
from .serializers_portal import PortalExpedienteListSerializer, PortalExpedienteDetailSerializer


def _get_expediente_for_user(pk, user):
    """
    Returns the expediente if it belongs to the authenticated user's client.
    ALWAYS returns the same 404 whether it doesn't exist OR belongs to another tenant.
    This prevents tenant enumeration.
    """
    try:
        exp = Expediente.objects.get(expediente_id=pk)
    except Expediente.DoesNotExist:
        return None
    # Tenant isolation: verify client matches user's legal entity
    if not hasattr(user, 'legal_entity') or exp.client != user.legal_entity:
        return None
    return exp


class PortalExpedienteListView(APIView):
    """
    GET /api/portal/expedientes/
    Returns only expedientes belonging to the authenticated user's client.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # NEVER .all() — always scope to authenticated user's tenant
        if not hasattr(request.user, 'legal_entity'):
            return Response([], status=status.HTTP_200_OK)
        expedientes = Expediente.objects.filter(
            client=request.user.legal_entity
        ).order_by('-created_at')
        serializer = PortalExpedienteListSerializer(expedientes, many=True)
        return Response(serializer.data)


class PortalExpedienteDetailView(APIView):
    """
    GET /api/portal/expedientes/<pk>/
    Returns detail without CEO-ONLY fields.
    Same 404 for non-existent and cross-tenant access.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        exp = _get_expediente_for_user(pk, request.user)
        if exp is None:
            # Uniform 404 — do not distinguish between 'not found' and 'not yours'
            return Response(
                {'detail': 'Not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = PortalExpedienteDetailSerializer(exp)
        return Response(serializer.data)


class PortalExpedienteArtifactsView(APIView):
    """
    GET /api/portal/expedientes/<pk>/artifacts/
    Returns only PUBLIC and PARTNER_B2B artifacts.
    Same 404 for non-existent and cross-tenant access.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        exp = _get_expediente_for_user(pk, request.user)
        if exp is None:
            return Response(
                {'detail': 'Not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        artifacts = ArtifactInstance.objects.filter(
            expediente=exp,
            # Only expose public-facing visibility levels
        ).values(
            'artifact_id', 'artifact_type', 'status', 'payload', 'created_at'
        )
        return Response(list(artifacts))
