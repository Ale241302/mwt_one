"""
Sprint 5 + Sprint 9 -- Liquidations views
"""
import io
import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.liquidations.models import Liquidation, LiquidationLine
from apps.liquidations.parsers import parse_marluvas_liquidation
from apps.liquidations.serializers import (
    LiquidationListSerializer,
    LiquidationDetailSerializer,
    LiquidationLineSerializer,
    ManualMatchSerializer,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# S9-P01 -- Preview: parsea Excel sin persistir
# POST /api/liquidations/preview/
# ---------------------------------------------------------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def preview_liquidation_view(request):
    """
    Recibe archivo Excel (.xlsx / .xls) via multipart/form-data (campo: archivo_excel).
    Devuelve lista de filas parseadas para la tabla comparativa del frontend.
    No persiste nada en base de datos.
    """
    archivo = request.FILES.get("archivo_excel")
    if not archivo:
        return Response(
            {"detail": "El campo 'archivo_excel' es requerido."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    ext = archivo.name.rsplit(".", 1)[-1].lower() if "." in archivo.name else ""
    if ext not in ("xlsx", "xls"):
        return Response(
            {"detail": "Solo se aceptan archivos .xlsx o .xls."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        import openpyxl

        wb = openpyxl.load_workbook(io.BytesIO(archivo.read()), data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))

        if not rows:
            return Response([], status=status.HTTP_200_OK)

        headers = [
            str(h).strip() if h is not None else f"col_{i}"
            for i, h in enumerate(rows[0])
        ]
        result = []
        for row in rows[1:]:
            if all(v is None for v in row):
                continue
            result.append(
                {k: (str(v) if v is not None else "") for k, v in zip(headers, row)}
            )

        logger.info("preview_liquidation_view: %d filas leidas de %s", len(result), archivo.name)
        return Response(result, status=status.HTTP_200_OK)

    except Exception as exc:
        logger.exception("preview_liquidation_view: error procesando archivo")
        return Response(
            {"detail": f"Error al parsear el archivo: {str(exc)}"},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


# ---------------------------------------------------------------------------
# Existing views (Sprint 5)
# ---------------------------------------------------------------------------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_liquidations_view(request):
    qs = Liquidation.objects.all().order_by("-created_at")
    return Response(LiquidationListSerializer(qs, many=True).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upload_liquidation_view(request):
    data = request.data
    lines_data = parse_marluvas_liquidation(data)

    liq = Liquidation.objects.create(
        source=data.get("source", "MARLUVAS"),
        currency=data.get("currency", "USD"),
        reference=data.get("reference", ""),
        raw_payload=data,
    )
    for line in lines_data:
        LiquidationLine.objects.create(liquidation=liq, **line)

    return Response(LiquidationDetailSerializer(liq).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_liquidation_view(request, liquidation_id):
    try:
        liq = Liquidation.objects.get(pk=liquidation_id)
    except Liquidation.DoesNotExist:
        return Response({"detail": "No encontrado."}, status=status.HTTP_404_NOT_FOUND)
    return Response(LiquidationDetailSerializer(liq).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_liquidation_lines_view(request, liquidation_id):
    lines = LiquidationLine.objects.filter(liquidation_id=liquidation_id).order_by("id")
    return Response(LiquidationLineSerializer(lines, many=True).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def manual_match_line_view(request, liquidation_id):
    serializer = ManualMatchSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        line = LiquidationLine.objects.get(
            liquidation_id=liquidation_id,
            pk=serializer.validated_data["line_id"],
        )
    except LiquidationLine.DoesNotExist:
        return Response({"detail": "Linea no encontrada."}, status=status.HTTP_404_NOT_FOUND)

    line.match_status = "matched"
    line.matched_expediente_id = serializer.validated_data.get("proforma_id")
    line.save(update_fields=["match_status", "matched_expediente_id"])
    return Response(LiquidationLineSerializer(line).data)
