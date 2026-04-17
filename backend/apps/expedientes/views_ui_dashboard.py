"""
ExpedientesStatsView — GET /api/ui/expedientes/stats/

Retorna conteos KPI para el dashboard de control logístico:
  - count_produccion       → status=PRODUCCION
  - count_despacho_transito → status IN (DESPACHO, TRANSITO)
  - count_en_destino       → status=EN_DESTINO
  - total_active           → todo excepto CERRADO/CANCELADO

SECURITY: CEO/INTERNAL → todos los expedientes.
          Cliente       → solo sus propios (filtrado por legal_entity).
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Q
from decimal import Decimal

from apps.core.registry import ModuleRegistry
from apps.expedientes.models import Expediente


class ExpedientesStatsView(APIView):
    """GET /api/ui/expedientes/stats/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Base queryset (active = not closed/cancelled)
        qs = Expediente.objects.all()

        # ── SECURITY filtrado por rol ──────────────────────────────────────
        is_admin = request.user.is_superuser or getattr(request.user, 'role', '') == 'INTERNAL'
        if not is_admin:
            user_entity = getattr(request.user, 'legal_entity_id', None)
            if user_entity:
                qs = qs.filter(client_id=user_entity)
            else:
                qs = qs.none()
        # ──────────────────────────────────────────────────────────────────

        active_qs = qs.exclude(status__in=['CERRADO', 'CANCELADO'])

        count_produccion = active_qs.filter(status='PRODUCCION').count()
        count_preparacion = active_qs.filter(status='PREPARACION').count()
        count_despacho_transito = active_qs.filter(
            status__in=['DESPACHO', 'TRANSITO']
        ).count()
        count_en_destino = active_qs.filter(status='EN_DESTINO').count()
        total_active = active_qs.count()

        # Credit stats (solo para admin)
        credit_data = {}
        if is_admin:
            total_limit = qs.aggregate(
                total=Sum('credit_limit_client')
            )['total'] or Decimal('0')
            total_exposure = qs.aggregate(
                total=Sum('credit_exposure')
            )['total'] or Decimal('0')
            credit_data = {
                'total_credit_limit': float(total_limit),
                'total_credit_used': float(total_exposure),
            }
        else:
            # Para cliente: muestra su propio crédito disponible/utilizado
            first = qs.first()
            if first:
                limit = first.credit_limit_client or Decimal('0')
                exposure = first.credit_exposure or Decimal('0')
                credit_data = {
                    'total_credit_limit': float(limit),
                    'total_credit_used': float(exposure),
                }
            else:
                credit_data = {
                    'total_credit_limit': 0.0,
                    'total_credit_used': 0.0,
                }

        # Pagos realizados (últimos 5 del queryset filtrado via finance app)
        recent_payments = []
        try:
            payment_model = ModuleRegistry.get_model('finance', 'Payment')
            if payment_model:
                exp_ids = qs.values_list('expediente_id', flat=True)
                pagos = payment_model.objects.filter(
                    expediente_id__in=exp_ids,
                    status='credit_released'
                ).order_by('-payment_date')[:5]

                for p in pagos:
                    # Resolvemos la referencia al expediente
                    exp = p.resolve_ref('expediente_id')
                    recent_payments.append({
                        'order_ref': exp.purchase_order_number if exp else f"ID-{str(p.expediente_id)[:8]}",
                        'sap_id': exp.proforma_client_number if exp else "N/A",
                        'paid_amount': float(p.amount_paid),
                        'payment_date': p.payment_date.strftime('%d/%m/%Y') if p.payment_date else None,
                        'method': p.metodo_pago,
                    })
        except Exception:
            pass

        return Response({
            'kpi': {
                'count_produccion': count_produccion,
                'count_preparacion': count_preparacion,
                'count_despacho_transito': count_despacho_transito,
                'count_en_destino': count_en_destino,
                'total_active': total_active,
            },
            'credit': credit_data,
            'recent_payments': recent_payments,
            'is_admin': is_admin,
        })
