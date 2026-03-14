"""
Sprint 5 + Sprint 9 — Transfers views
"""
import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.transfers.models import Transfer, Node
from apps.transfers.serializers import (
    TransferListSerializer,
    TransferDetailSerializer,
    CreateTransferSerializer,
    ReceiveTransferSerializer,
    ReconcileTransferSerializer,
    CancelTransferSerializer,
    CreatePreparationArtifactSerializer,
    CreateDispatchArtifactSerializer,
    CreateReceptionArtifactSerializer,
    CreatePricingApprovalArtifactSerializer,
    NodeSerializer,
)
from apps.transfers.services import (
    create_transfer,
    approve_transfer,
    dispatch_transfer,
    receive_transfer,
    reconcile_transfer,
    cancel_transfer,
    create_preparation_artifact,
    create_dispatch_artifact,
    create_reception_artifact,
    create_pricing_approval_artifact,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# S9-P02 — Nodes list: GET /api/transfers/nodes/
# Resuelve la ambigüedad /api/nodes/ vs /api/nodos/ — la URL canonica es /api/transfers/nodes/
# ---------------------------------------------------------------------------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_nodes_view(request):
    """
    Devuelve todos los nodos activos ordenados por nombre.
    URL canónica: GET /api/transfers/nodes/
    """
    qs = Node.objects.select_related("legal_entity").filter(
        status="active"
    ).order_by("name")
    return Response(NodeSerializer(qs, many=True).data)


# ---------------------------------------------------------------------------
# Existing Transfer views (Sprint 5)
# ---------------------------------------------------------------------------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_transfers_view(request):
    qs = Transfer.objects.select_related("from_node", "to_node").order_by("-created_at")
    return Response(TransferListSerializer(qs, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_transfer_view(request, transfer_id):
    try:
        t = Transfer.objects.select_related("from_node", "to_node").prefetch_related("lines").get(
            transfer_id=transfer_id
        )
    except Transfer.DoesNotExist:
        return Response({"detail": "Transfer no encontrado."}, status=status.HTTP_404_NOT_FOUND)
    return Response(TransferDetailSerializer(t).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_transfer_view(request):
    s = CreateTransferSerializer(data=request.data)
    if not s.is_valid():
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        transfer = create_transfer(s.validated_data, request.user)
    except Exception as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    return Response(TransferDetailSerializer(transfer).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def approve_transfer_view(request, transfer_id):
    try:
        t = Transfer.objects.get(transfer_id=transfer_id)
        transfer = approve_transfer(t, request.user)
    except Transfer.DoesNotExist:
        return Response({"detail": "Transfer no encontrado."}, status=status.HTTP_404_NOT_FOUND)
    except (ValueError, PermissionError) as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    return Response(TransferDetailSerializer(transfer).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def dispatch_transfer_view(request, transfer_id):
    try:
        t = Transfer.objects.get(transfer_id=transfer_id)
        transfer = dispatch_transfer(t, request.user)
    except Transfer.DoesNotExist:
        return Response({"detail": "Transfer no encontrado."}, status=status.HTTP_404_NOT_FOUND)
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    return Response(TransferDetailSerializer(transfer).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def receive_transfer_view(request, transfer_id):
    s = ReceiveTransferSerializer(data=request.data)
    if not s.is_valid():
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        t = Transfer.objects.get(transfer_id=transfer_id)
        transfer = receive_transfer(t, s.validated_data["lines"], request.user)
    except Transfer.DoesNotExist:
        return Response({"detail": "Transfer no encontrado."}, status=status.HTTP_404_NOT_FOUND)
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    return Response(TransferDetailSerializer(transfer).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reconcile_transfer_view(request, transfer_id):
    s = ReconcileTransferSerializer(data=request.data)
    if not s.is_valid():
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        t = Transfer.objects.get(transfer_id=transfer_id)
        transfer = reconcile_transfer(
            t, request.user, s.validated_data.get("exception_reason")
        )
    except Transfer.DoesNotExist:
        return Response({"detail": "Transfer no encontrado."}, status=status.HTTP_404_NOT_FOUND)
    except (ValueError, PermissionError) as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    return Response(TransferDetailSerializer(transfer).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cancel_transfer_view(request, transfer_id):
    s = CancelTransferSerializer(data=request.data)
    if not s.is_valid():
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        t = Transfer.objects.get(transfer_id=transfer_id)
        transfer = cancel_transfer(t, request.user, s.validated_data["reason"])
    except Transfer.DoesNotExist:
        return Response({"detail": "Transfer no encontrado."}, status=status.HTTP_404_NOT_FOUND)
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    return Response(TransferDetailSerializer(transfer).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_reception_artifact_view(request, transfer_id):
    s = CreateReceptionArtifactSerializer(data=request.data)
    if not s.is_valid():
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        t = Transfer.objects.get(transfer_id=transfer_id)
        artifact = create_reception_artifact(
            t, s.validated_data["lines"], s.validated_data.get("payload", {}), request.user
        )
    except Transfer.DoesNotExist:
        return Response({"detail": "Transfer no encontrado."}, status=status.HTTP_404_NOT_FOUND)
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"artifact_id": str(artifact.pk)}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_preparation_artifact_view(request, transfer_id):
    s = CreatePreparationArtifactSerializer(data=request.data)
    if not s.is_valid():
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        t = Transfer.objects.get(transfer_id=transfer_id)
        artifact = create_preparation_artifact(
            t, s.validated_data.get("payload", {}), request.user
        )
    except Transfer.DoesNotExist:
        return Response({"detail": "Transfer no encontrado."}, status=status.HTTP_404_NOT_FOUND)
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"artifact_id": str(artifact.pk)}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_dispatch_artifact_view(request, transfer_id):
    s = CreateDispatchArtifactSerializer(data=request.data)
    if not s.is_valid():
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        t = Transfer.objects.get(transfer_id=transfer_id)
        artifact = create_dispatch_artifact(
            t, s.validated_data.get("payload", {}), request.user
        )
    except Transfer.DoesNotExist:
        return Response({"detail": "Transfer no encontrado."}, status=status.HTTP_404_NOT_FOUND)
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"artifact_id": str(artifact.pk)}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_pricing_approval_artifact_view(request, transfer_id):
    s = CreatePricingApprovalArtifactSerializer(data=request.data)
    if not s.is_valid():
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        t = Transfer.objects.get(transfer_id=transfer_id)
        artifact = create_pricing_approval_artifact(
            t, s.validated_data.get("payload", {}), request.user
        )
    except Transfer.DoesNotExist:
        return Response({"detail": "Transfer no encontrado."}, status=status.HTTP_404_NOT_FOUND)
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"artifact_id": str(artifact.pk)}, status=status.HTTP_201_CREATED)
