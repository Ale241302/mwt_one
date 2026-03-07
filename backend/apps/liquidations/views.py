"""
Sprint 5 S5-03: Liquidation views C25-C28 + reads
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from apps.liquidations.models import Liquidation
from apps.liquidations.services import (
    upload_liquidation, manual_match_line,
    reconcile_liquidation, dispute_liquidation,
)
from apps.liquidations.serializers import (
    UploadLiquidationSerializer, LiquidationListSerializer,
    LiquidationDetailSerializer, LiquidationLineSerializer,
    ManualMatchSerializer, DisputeSerializer,
)


# C25 â€” POST /api/liquidations/upload/
@api_view(["POST"])
@permission_classes([IsAdminUser])
def upload_liquidation_view(request):
    ser = UploadLiquidationSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    liquidation = upload_liquidation(
        data=request.data,
        file=ser.validated_data.get("file"),
        period=ser.validated_data["period"],
        user=request.user,
    )
    return Response(
        LiquidationDetailSerializer(liquidation).data,
        status=status.HTTP_201_CREATED,
    )


# C26 â€” POST /api/liquidations/{id}/match-line/
@api_view(["POST"])
@permission_classes([IsAdminUser])
def manual_match_line_view(request, liquidation_id):
    liquidation = Liquidation.objects.get(liquidation_id=liquidation_id)
    ser = ManualMatchSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    line = manual_match_line(
        liquidation,
        ser.validated_data["line_id"],
        ser.validated_data["proforma_id"],
        request.user,
    )
    return Response(LiquidationLineSerializer(line).data)


# C27 â€” POST /api/liquidations/{id}/reconcile/
@api_view(["POST"])
@permission_classes([IsAdminUser])
def reconcile_liquidation_view(request, liquidation_id):
    liquidation = Liquidation.objects.get(liquidation_id=liquidation_id)
    liquidation = reconcile_liquidation(liquidation, request.user)
    return Response(LiquidationDetailSerializer(liquidation).data)


# C28 â€” POST /api/liquidations/{id}/dispute/
@api_view(["POST"])
@permission_classes([IsAdminUser])
def dispute_liquidation_view(request, liquidation_id):
    liquidation = Liquidation.objects.get(liquidation_id=liquidation_id)
    ser = DisputeSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    liquidation = dispute_liquidation(
        liquidation,
        ser.validated_data["observations"],
        request.user,
    )
    return Response(LiquidationDetailSerializer(liquidation).data)


# GET /api/liquidations/
@api_view(["GET"])
@permission_classes([IsAdminUser])
def list_liquidations_view(request):
    qs = Liquidation.objects.order_by("-created_at")
    paginator = PageNumberPagination()
    page = paginator.paginate_queryset(qs, request)
    return paginator.get_paginated_response(
        LiquidationListSerializer(page, many=True).data
    )


# GET /api/liquidations/{id}/
@api_view(["GET"])
@permission_classes([IsAdminUser])
def get_liquidation_view(request, liquidation_id):
    liquidation = Liquidation.objects.prefetch_related("lines").get(
        liquidation_id=liquidation_id
    )
    return Response(LiquidationDetailSerializer(liquidation).data)


# GET /api/liquidations/{id}/lines/
@api_view(["GET"])
@permission_classes([IsAdminUser])
def get_liquidation_lines_view(request, liquidation_id):
    liquidation = Liquidation.objects.get(liquidation_id=liquidation_id)
    lines = liquidation.lines.select_related(
        "matched_proforma", "matched_expediente"
    )
    return Response(LiquidationLineSerializer(lines, many=True).data)
