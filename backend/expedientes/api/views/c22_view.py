"""
S10-04b — POST /expedientes/{id}/issue-commission-invoice/
HTTP endpoint for C22 command.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from expedientes.models import Expediente
from expedientes.domain.commands.c22_issue_commission_invoice import IssueCommissionInvoice
from expedientes.application.handlers.c22_handler import IssueCommissionInvoiceHandler


class IssueCommissionInvoiceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, expediente_id):
        exp = get_object_or_404(Expediente, pk=expediente_id)

        invoice_number = request.data.get("invoice_number", "")
        if not invoice_number:
            return Response(
                {"invoice_number": "Este campo es requerido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        commission_amount = request.data.get("commission_amount")
        if commission_amount is None:
            return Response(
                {"commission_amount": "Este campo es requerido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            commission_amount = float(commission_amount)
        except (TypeError, ValueError):
            return Response(
                {"commission_amount": "Debe ser un número."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        commission_pct = float(request.data.get("commission_pct", 0.0))
        notes = request.data.get("notes", "")

        cmd = IssueCommissionInvoice(
            expediente_id=str(exp.pk),
            invoice_number=invoice_number,
            commission_amount=commission_amount,
            commission_pct=commission_pct,
            notes=notes,
        )
        try:
            handler = IssueCommissionInvoiceHandler()
            event = handler.handle(cmd)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        return Response(
            {
                "event_id": event.event_id,
                "invoice_number": event.invoice_number,
                "commission_amount": event.commission_amount,
                "commission_pct": event.commission_pct,
                "message": "Factura de comisión emitida correctamente.",
            },
            status=status.HTTP_201_CREATED,
        )
