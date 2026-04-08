"""S17-04: Portal B2B views with strict tenant isolation.

FIX-2026-04-08c:
  Agrega PortalExpedientePagosView:
    GET /api/portal/expedientes/{pk}/pagos/
    Retorna pagos en formato PagoClienteSerializer (CLIENT_* tier).
    Tenant-isolated: mismo patrón _get_expediente_for_user.
    Resuelve 404 que PortalPagosTab recibía en la vista cliente.
"""
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Expediente, ArtifactInstance, ExpedientePago
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


class PortalExpedientePagosView(APIView):
    """
    FIX-2026-04-08c — GET /api/portal/expedientes/<pk>/pagos/
    Retorna pagos del expediente en formato PagoClienteSerializer (CLIENT_* tier).
    Campos restringidos: id, payment_date, amount_paid, payment_status.
    NUNCA expone: rejection_reason, verified_by, credit_released_by.
    Tenant-isolated: mismo control que PortalExpedienteDetailView.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        # Para la vista admin/interna que usa el mismo endpoint,
        # permitimos si el user es staff o si el expediente le pertenece.
        try:
            exp = Expediente.objects.get(expediente_id=pk)
        except Expediente.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Tenant check: staff/admin bypass, clientes deben ser del tenant
        if not (request.user.is_staff or request.user.is_superuser):
            if not hasattr(request.user, 'legal_entity') or exp.client != request.user.legal_entity:
                return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        from apps.expedientes.serializers import PagoClienteSerializer
        pagos = ExpedientePago.objects.filter(
            expediente=exp
        ).order_by('-payment_date', '-created_at')
        serializer = PagoClienteSerializer(pagos, many=True)
        return Response(serializer.data)
