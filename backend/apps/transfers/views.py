"""
Sprint 5 + Sprint 9 — Transfers views
<<<<<<< HEAD
"""
import logging

=======
S9-11 fix: list_transfers_view — select_related completo + try/except para evitar 500
"""
import logging

from django.db import OperationalError, ProgrammingError
>>>>>>> origin/fix/s9-transfers-500
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
<<<<<<< HEAD
# Resuelve la ambigüedad /api/nodes/ vs /api/nodos/ — la URL canonica es /api/transfers/nodes/
=======
>>>>>>> origin/fix/s9-transfers-500
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
<<<<<<< HEAD
# Existing Transfer views (Sprint 5)
=======
# GET /api/transfers/  (S9-11 fix)
>>>>>>> origin/fix/s9-transfers-500
# ---------------------------------------------------------------------------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_transfers_view(request):
<<<<<<< HEAD
    qs = Transfer.objects.select_related("from_node", "to_node").order_by("-created_at")
    return Response(TransferListSerializer(qs, many=True).data)


=======
    """
    S9-11: select_related ampliado para evitar N+1 y errores de FK no resuelta.
    try/except OperationalError | ProgrammingError para devolver 200 vacío
    si la migración aún no se ha ejecutado en el contenedor.
    """
    try:
        qs = (
            Transfer.objects
            .select_related(
                "from_node",
                "to_node",
                "ownership_before",
                "ownership_after",
                "source_expediente",
            )
            .order_by("-created_at")
        )
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(
            TransferListSerializer(page, many=True).data
        )
    except (OperationalError, ProgrammingError) as exc:
        logger.warning("[S9-11] transfers_transfer tabla no disponible: %s", exc)
        return Response({"count": 0, "next": None, "previous": None, "results": []})
    except Exception as exc:
        logger.exception("[S9-11] Error inesperado en list_transfers_view: %s", exc)
        return Response(
            {"detail": "Error interno al listar transfers."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ---------------------------------------------------------------------------
# GET /api/transfers/{id}/
# ---------------------------------------------------------------------------
>>>>>>> origin/fix/s9-transfers-500
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_transfer_view(request, transfer_id):
    try:
<<<<<<< HEAD
        t = Transfer.objects.select_related("from_node", "to_node").prefetch_related("lines").get(
            transfer_id=transfer_id
        )
=======
        t = Transfer.objects.select_related(
            "from_node", "to_node", "ownership_before", "ownership_after"
        ).prefetch_related("lines").get(transfer_id=transfer_id)
>>>>>>> origin/fix/s9-transfers-500
    except Transfer.DoesNotExist:
        return Response({"detail": "Transfer no encontrado."}, status=status.HTTP_404_NOT_FOUND)
    return Response(TransferDetailSerializer(t).data)


<<<<<<< HEAD
=======
# ---------------------------------------------------------------------------
# POST /api/transfers/create/
# ---------------------------------------------------------------------------
>>>>>>> origin/fix/s9-transfers-500
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


<<<<<<< HEAD
=======
# ---------------------------------------------------------------------------
# POST /api/transfers/{id}/approve/
# ---------------------------------------------------------------------------
>>>>>>> origin/fix/s9-transfers-500
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


<<<<<<< HEAD
=======
# ---------------------------------------------------------------------------
# POST /api/transfers/{id}/dispatch/
# ---------------------------------------------------------------------------
>>>>>>> origin/fix/s9-transfers-500
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


<<<<<<< HEAD
=======
# ---------------------------------------------------------------------------
# POST /api/transfers/{id}/receive/
# ---------------------------------------------------------------------------
>>>>>>> origin/fix/s9-transfers-500
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


<<<<<<< HEAD
=======
# ---------------------------------------------------------------------------
# POST /api/transfers/{id}/reconcile/
# ---------------------------------------------------------------------------
>>>>>>> origin/fix/s9-transfers-500
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


<<<<<<< HEAD
=======
# ---------------------------------------------------------------------------
# POST /api/transfers/{id}/cancel/
# ---------------------------------------------------------------------------
>>>>>>> origin/fix/s9-transfers-500
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


<<<<<<< HEAD
=======
# ---------------------------------------------------------------------------
# POST /api/transfers/{id}/complete-reception/
# ---------------------------------------------------------------------------
>>>>>>> origin/fix/s9-transfers-500
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


<<<<<<< HEAD
=======
# ---------------------------------------------------------------------------
# POST /api/transfers/{id}/complete-preparation/
# ---------------------------------------------------------------------------
>>>>>>> origin/fix/s9-transfers-500
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


<<<<<<< HEAD
=======
# ---------------------------------------------------------------------------
# POST /api/transfers/{id}/complete-dispatch/
# ---------------------------------------------------------------------------
>>>>>>> origin/fix/s9-transfers-500
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


<<<<<<< HEAD
=======
# ---------------------------------------------------------------------------
# POST /api/transfers/{id}/approve-pricing/
# ---------------------------------------------------------------------------
>>>>>>> origin/fix/s9-transfers-500
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
