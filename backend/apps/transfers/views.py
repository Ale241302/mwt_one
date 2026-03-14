"""
Sprint 5 S5-02: Transfer views C30-C35 + reads
Sprint 6: C36-C39 artifact views
S9-11 fix: list_transfers_view — select_related completo + try/except para evitar 500
"""
import logging

from django.db import OperationalError, ProgrammingError
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from apps.transfers.models import Transfer
from apps.transfers.services import (
    create_transfer, approve_transfer, dispatch_transfer,
    receive_transfer, reconcile_transfer, cancel_transfer,
    create_preparation_artifact, create_dispatch_artifact, create_reception_artifact,
    create_pricing_approval_artifact
)
from apps.transfers.serializers import (
    CreateTransferSerializer, TransferListSerializer, TransferDetailSerializer,
    ReceiveTransferSerializer, ReconcileTransferSerializer, CancelTransferSerializer,
    CreatePreparationArtifactSerializer, CreateDispatchArtifactSerializer,
    CreateReceptionArtifactSerializer, CreatePricingApprovalArtifactSerializer
)

logger = logging.getLogger(__name__)


# C30 — POST /api/transfers/create/
@api_view(["POST"])
@permission_classes([IsAdminUser])
def create_transfer_view(request):
    ser = CreateTransferSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    transfer = create_transfer(ser.validated_data, request.user)
    return Response(
        TransferDetailSerializer(transfer).data, status=status.HTTP_201_CREATED
    )


# C31 — POST /api/transfers/{id}/approve/
@api_view(["POST"])
@permission_classes([IsAdminUser])
def approve_transfer_view(request, transfer_id):
    transfer = Transfer.objects.get(transfer_id=transfer_id)
    transfer = approve_transfer(transfer, request.user)
    return Response(TransferDetailSerializer(transfer).data)


# C32 — POST /api/transfers/{id}/dispatch/
@api_view(["POST"])
@permission_classes([IsAdminUser])
def dispatch_transfer_view(request, transfer_id):
    transfer = Transfer.objects.get(transfer_id=transfer_id)
    transfer = dispatch_transfer(transfer, request.user)
    return Response(TransferDetailSerializer(transfer).data)


# C33 — POST /api/transfers/{id}/receive/
@api_view(["POST"])
@permission_classes([IsAdminUser])
def receive_transfer_view(request, transfer_id):
    transfer = Transfer.objects.get(transfer_id=transfer_id)
    ser = ReceiveTransferSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    transfer = receive_transfer(transfer, ser.validated_data["lines"], request.user)
    return Response(TransferDetailSerializer(transfer).data)


# C34 — POST /api/transfers/{id}/reconcile/
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reconcile_transfer_view(request, transfer_id):
    transfer = Transfer.objects.get(transfer_id=transfer_id)
    ser = ReconcileTransferSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    transfer = reconcile_transfer(
        transfer, request.user, ser.validated_data.get("exception_reason")
    )
    return Response(TransferDetailSerializer(transfer).data)


# C35 — POST /api/transfers/{id}/cancel/
@api_view(["POST"])
@permission_classes([IsAdminUser])
def cancel_transfer_view(request, transfer_id):
    transfer = Transfer.objects.get(transfer_id=transfer_id)
    ser = CancelTransferSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    transfer = cancel_transfer(transfer, request.user, ser.validated_data["reason"])
    return Response(TransferDetailSerializer(transfer).data)


# C36 — POST /api/transfers/{id}/complete-reception/
@api_view(["POST"])
@permission_classes([IsAdminUser])
def create_reception_artifact_view(request, transfer_id):
    transfer = Transfer.objects.get(transfer_id=transfer_id)
    ser = CreateReceptionArtifactSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    create_reception_artifact(
        transfer,
        ser.validated_data["lines"],
        ser.validated_data.get("payload", {}),
        request.user
    )
    transfer.refresh_from_db()
    return Response(TransferDetailSerializer(transfer).data)


# C37 — POST /api/transfers/{id}/complete-preparation/
@api_view(["POST"])
@permission_classes([IsAdminUser])
def create_preparation_artifact_view(request, transfer_id):
    transfer = Transfer.objects.get(transfer_id=transfer_id)
    ser = CreatePreparationArtifactSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    create_preparation_artifact(transfer, ser.validated_data.get("payload", {}), request.user)
    transfer.refresh_from_db()
    return Response(TransferDetailSerializer(transfer).data)


# C38 — POST /api/transfers/{id}/complete-dispatch/
@api_view(["POST"])
@permission_classes([IsAdminUser])
def create_dispatch_artifact_view(request, transfer_id):
    transfer = Transfer.objects.get(transfer_id=transfer_id)
    ser = CreateDispatchArtifactSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    create_dispatch_artifact(transfer, ser.validated_data.get("payload", {}), request.user)
    transfer.refresh_from_db()
    return Response(TransferDetailSerializer(transfer).data)


# C39 — POST /api/transfers/{id}/approve-pricing/
@api_view(["POST"])
@permission_classes([IsAdminUser])
def create_pricing_approval_artifact_view(request, transfer_id):
    transfer = Transfer.objects.get(transfer_id=transfer_id)
    ser = CreatePricingApprovalArtifactSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    create_pricing_approval_artifact(transfer, ser.validated_data.get("payload", {}), request.user)
    transfer.refresh_from_db()
    return Response(TransferDetailSerializer(transfer).data)


# GET /api/transfers/  (S9-11 fix)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def list_transfers_view(request):
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
        # Tabla no existe todavía — migración pendiente
        logger.warning("[S9-11] transfers_transfer tabla no disponible: %s", exc)
        return Response({"count": 0, "next": None, "previous": None, "results": []})
    except Exception as exc:
        logger.exception("[S9-11] Error inesperado en list_transfers_view: %s", exc)
        return Response(
            {"detail": "Error interno al listar transfers."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# GET /api/transfers/{id}/
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_transfer_view(request, transfer_id):
    transfer = Transfer.objects.prefetch_related("lines").select_related(
        "from_node", "to_node", "ownership_before", "ownership_after"
    ).get(transfer_id=transfer_id)
    return Response(TransferDetailSerializer(transfer).data)
