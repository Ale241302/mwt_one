"""
Sprint 5 S5-02: Transfer views C30-C35 + reads
Sprint 6: C36-C39 artifact views
Sprint 9: Node CRUD views
Sprint 10 S10-02a: Transfer Edit (PUT/PATCH) + Delete (DELETE)
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.core.exceptions import ValidationError as DjangoValidationError

from apps.transfers.models import Transfer
from apps.nodos.models import Node
from apps.core.models import LegalEntity
from apps.transfers.services import (
    TransferService,
    create_preparation_artifact, create_dispatch_artifact, create_reception_artifact,
    create_pricing_approval_artifact
)
from apps.transfers.serializers import (
    CreateTransferSerializer, TransferListSerializer, TransferDetailSerializer,
    ReceiveTransferSerializer, ReconcileTransferSerializer, CancelTransferSerializer,
    CreatePreparationArtifactSerializer, CreateDispatchArtifactSerializer,
    CreateReceptionArtifactSerializer, CreatePricingApprovalArtifactSerializer,
    NodeSerializer, NodeCreateSerializer
)


# ─── NODE CRUD ────────────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_nodes_view(request):
    qs = Node.objects.all().order_by("name")
    paginator = PageNumberPagination()
    paginator.page_size = 100
    page = paginator.paginate_queryset(qs, request)
    return paginator.get_paginated_response(NodeSerializer(page, many=True).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_node_view(request):
    ser = NodeCreateSerializer(data=request.data)
    if not ser.is_valid():
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

    d = ser.validated_data
    entity_id = d.get("legal_entity", "").strip()

    if entity_id:
        try:
            legal_entity = LegalEntity.objects.get(entity_id=entity_id)
        except LegalEntity.DoesNotExist:
            return Response(
                {"legal_entity": f"No existe LegalEntity con entity_id='{entity_id}'"},
                status=status.HTTP_400_BAD_REQUEST
            )
    else:
        legal_entity = LegalEntity.objects.first()
        if not legal_entity:
            return Response(
                {"legal_entity": "No hay LegalEntities registradas. Crea una primero."},
                status=status.HTTP_400_BAD_REQUEST
            )

    node = Node.objects.create(
        name=d["name"],
        node_type=d["node_type"],
        location=d.get("location", ""),
        status=d.get("status", "active"),
        legal_entity=legal_entity,
    )
    return Response(NodeSerializer(node).data, status=status.HTTP_201_CREATED)


@api_view(["PUT", "PATCH"])
@permission_classes([IsAuthenticated])
def update_node_view(request, node_id):
    try:
        node = Node.objects.get(node_id=node_id)
    except Node.DoesNotExist:
        return Response({"detail": "Node no encontrado."}, status=status.HTTP_404_NOT_FOUND)

    ser = NodeCreateSerializer(data=request.data, partial=True)
    if not ser.is_valid():
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

    d = ser.validated_data
    entity_id = d.get("legal_entity", "").strip() if "legal_entity" in d else ""
    if entity_id:
        try:
            node.legal_entity = LegalEntity.objects.get(entity_id=entity_id)
        except LegalEntity.DoesNotExist:
            return Response(
                {"legal_entity": f"No existe LegalEntity con entity_id='{entity_id}'"},
                status=status.HTTP_400_BAD_REQUEST
            )

    for field in ["name", "node_type", "location", "status"]:
        if field in d:
            setattr(node, field, d[field])
    node.save()
    return Response(NodeSerializer(node).data)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_node_view(request, node_id):
    try:
        node = Node.objects.get(node_id=node_id)
    except Node.DoesNotExist:
        return Response({"detail": "Node no encontrado."}, status=status.HTTP_404_NOT_FOUND)
    node.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ─── TRANSFER CRUD ────────────────────────────────────────────────────────────

# C30 — POST /api/transfers/create/
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_transfer_view(request):
    ser = CreateTransferSerializer(data=request.data)
    if not ser.is_valid():
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        transfer = TransferService.create_transfer(ser.validated_data, request.user)
        return Response(
            TransferDetailSerializer(transfer).data, status=status.HTTP_201_CREATED
        )
    except Node.DoesNotExist:
        return Response(
            {"detail": "Node no encontrado. Verifica los UUIDs de from_node y to_node."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except DjangoValidationError as e:
        return Response(
            {"detail": e.messages if hasattr(e, "messages") else str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except ValueError as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# S10-02a — PUT/PATCH /api/transfers/{id}/edit/
@api_view(["PUT", "PATCH"])
@permission_classes([IsAdminUser])
def update_transfer_view(request, transfer_id):
    """S10-02a: Edit a transfer (only planned/approved status)."""
    try:
        transfer = Transfer.objects.get(transfer_id=transfer_id)
    except Transfer.DoesNotExist:
        return Response({"detail": "Transfer no encontrado."}, status=status.HTTP_404_NOT_FOUND)

    EDITABLE_STATUSES = ["planned", "approved"]
    if transfer.status not in EDITABLE_STATUSES:
        return Response(
            {"detail": f"Solo se pueden editar transfers en estado: {', '.join(EDITABLE_STATUSES)}. Estado actual: {transfer.status}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    data = request.data
    if "from_node" in data:
        try:
            transfer.from_node = Node.objects.get(node_id=data["from_node"])
        except Node.DoesNotExist:
            return Response({"detail": "from_node no encontrado."}, status=status.HTTP_400_BAD_REQUEST)
    if "to_node" in data:
        try:
            transfer.to_node = Node.objects.get(node_id=data["to_node"])
        except Node.DoesNotExist:
            return Response({"detail": "to_node no encontrado."}, status=status.HTTP_400_BAD_REQUEST)
    if "legal_context" in data:
        transfer.legal_context = data["legal_context"]
    if "ownership_changes" in data:
        transfer.ownership_changes = bool(data["ownership_changes"])
    if "customs_required" in data:
        transfer.customs_required = bool(data["customs_required"])
    if "notes" in data:
        transfer.notes = data.get("notes", "")

    transfer.save()
    return Response(TransferDetailSerializer(transfer).data)


# S10-02a — DELETE /api/transfers/{id}/delete/
@api_view(["DELETE"])
@permission_classes([IsAdminUser])
def delete_transfer_view(request, transfer_id):
    """S10-02a: Delete a transfer (only planned status)."""
    try:
        transfer = Transfer.objects.get(transfer_id=transfer_id)
    except Transfer.DoesNotExist:
        return Response({"detail": "Transfer no encontrado."}, status=status.HTTP_404_NOT_FOUND)

    if transfer.status != "planned":
        return Response(
            {"detail": f"Solo se pueden eliminar transfers en estado 'planned'. Estado actual: {transfer.status}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    transfer.delete()
    return Response({"detail": "Transfer eliminado."}, status=status.HTTP_200_OK)


# C31 — POST /api/transfers/{id}/approve/
@api_view(["POST"])
@permission_classes([IsAdminUser])
def approve_transfer_view(request, transfer_id):
    transfer = Transfer.objects.get(transfer_id=transfer_id)
    transfer = TransferService.approve_transfer(transfer, request.user)
    return Response(TransferDetailSerializer(transfer).data)


# C32 — POST /api/transfers/{id}/dispatch/
@api_view(["POST"])
@permission_classes([IsAdminUser])
def dispatch_transfer_view(request, transfer_id):
    transfer = Transfer.objects.get(transfer_id=transfer_id)
    transfer = TransferService.dispatch_transfer(transfer, request.user)
    return Response(TransferDetailSerializer(transfer).data)


# C33 — POST /api/transfers/{id}/receive/
@api_view(["POST"])
@permission_classes([IsAdminUser])
def receive_transfer_view(request, transfer_id):
    transfer = Transfer.objects.get(transfer_id=transfer_id)
    ser = ReceiveTransferSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    transfer = TransferService.receive_transfer(transfer, ser.validated_data["lines"], request.user)
    return Response(TransferDetailSerializer(transfer).data)


# C34 — POST /api/transfers/{id}/reconcile/
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reconcile_transfer_view(request, transfer_id):
    transfer = Transfer.objects.get(transfer_id=transfer_id)
    ser = ReconcileTransferSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    transfer = TransferService.reconcile_transfer(
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
    transfer = TransferService.cancel_transfer(transfer, request.user, ser.validated_data["reason"])
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


# GET /api/transfers/ (CEO-ONLY)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def list_transfers_view(request):
    qs = Transfer.objects.select_related("from_node", "to_node").order_by("-created_at")
    paginator = PageNumberPagination()
    page = paginator.paginate_queryset(qs, request)
    return paginator.get_paginated_response(
        TransferListSerializer(page, many=True).data
    )


# GET /api/transfers/{id}/
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_transfer_view(request, transfer_id):
    try:
        transfer = Transfer.objects.prefetch_related("lines").select_related(
            "from_node", "to_node",
            "from_node__legal_entity", "to_node__legal_entity"
        ).get(transfer_id=transfer_id)
    except Transfer.DoesNotExist:
        return Response({"detail": "Transfer no encontrado."}, status=status.HTTP_404_NOT_FOUND)
    return Response(TransferDetailSerializer(transfer).data)
