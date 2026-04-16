"""
Sprint 3-4 — UI Serializers
S20-06: ExpedienteBundleSerializer ahora incluye artifact_policy calculada dinámicamente.
FIX-2026-03-31: get_product_lines envuelto en try/except para no romper el bundle.
FIX-2026-04-08: get_expediente ahora expone 'id' (alias de expediente_id) para que
                page.tsx pueda usar expediente.id en ArtifactModal (C21, C15, etc.)
FIX-2026-04-08b: get_credit_snapshot computa credit_snapshot desde pagos (S25-05)
                 y lo expone como campo top-level del bundle.
                 CostLineSummarySerializer usa visible_to_client (bool) en lugar de
                 visibility (str) para que el toggle Vista Cliente funcione.
"""
import datetime
from decimal import Decimal
from rest_framework import serializers


class UIExpedienteListSerializer(serializers.Serializer):
    id = serializers.UUIDField(source='expediente_id', read_only=True)
    custom_ref = serializers.SerializerMethodField()
    status = serializers.CharField(read_only=True)
    brand_name = serializers.SerializerMethodField()
    brand = serializers.SerializerMethodField()
    client_name = serializers.CharField(source='client.legal_name', read_only=True, default='')

    # Annotated fields
    credit_days_elapsed = serializers.IntegerField(read_only=True, default=0)
    credit_band = serializers.CharField(read_only=True, default='MINT')
    total_cost = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True, default=Decimal('0.00'))
    artifact_count = serializers.IntegerField(read_only=True, default=0)
    last_event_at = serializers.DateTimeField(read_only=True, default=None)

    is_blocked = serializers.BooleanField(read_only=True)
    block_reason = serializers.CharField(source='blocked_reason', read_only=True, default='')

    # Extended fields for dashboard view
    purchase_order_number = serializers.CharField(read_only=True, allow_null=True, default=None)
    payment_status = serializers.CharField(read_only=True, default='PENDING')
    proforma_client_number = serializers.CharField(read_only=True, allow_null=True, default=None)
    shipment_date = serializers.DateField(read_only=True, allow_null=True, default=None)
    total_value = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    credit_limit_client = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True, allow_null=True, default=None)
    credit_exposure = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True, allow_null=True, default=None)

    def get_custom_ref(self, obj):
        # Usa purchase_order_number si existe, sino genera ref UUID
        if getattr(obj, 'purchase_order_number', None):
            return obj.purchase_order_number
        return f"OC-{str(obj.expediente_id)[:8].upper()}"

    def get_brand_name(self, obj):
        """FIX: brand es ForeignKey a Brand, no CharField con get_brand_display."""
        try:
            if obj.brand:
                return obj.brand.name
        except Exception:
            pass
        return ''

    def get_brand(self, obj):
        """FIX: retorna el name normalizado del brand FK."""
        try:
            if obj.brand:
                return obj.brand.name
        except Exception:
            pass
        return ''

    def get_total_value(self, obj):
        """Calcula el valor total de líneas de producto."""
        try:
            total = sum(
                (line.unit_price or Decimal('0')) * (line.quantity or 0)
                for line in obj.product_lines.all()
            )
            return float(total)
        except Exception:
            return 0.0

    def get_product_count(self, obj):
        """Cuenta líneas de producto distintas."""
        try:
            return obj.product_lines.count()
        except Exception:
            return 0


class EventLogSummarySerializer(serializers.Serializer):
    id = serializers.UUIDField(source='event_id')
    event_type = serializers.CharField()
    occurred_at = serializers.DateTimeField()
    emitted_by = serializers.CharField()
    payload = serializers.JSONField()


class ArtifactSummarySerializer(serializers.Serializer):
    id = serializers.UUIDField(source='artifact_id')
    artifact_type = serializers.CharField()
    status = serializers.CharField()
    status_display = serializers.CharField(source='get_status_display')
    created_at = serializers.DateTimeField()
    payload = serializers.JSONField()
    parent_proforma_id = serializers.UUIDField(allow_null=True, required=False)


class CostLineSummarySerializer(serializers.Serializer):
    """
    FIX-2026-04-08b: visible_to_client ahora es bool (antes 'visibility' str).
    CostTable.tsx filtra por visible_to_client para el toggle Vista Cliente.
    """
    id = serializers.UUIDField(source='cost_line_id')
    cost_type = serializers.CharField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField()
    phase = serializers.CharField()
    description = serializers.CharField()
    visible_to_client = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField()

    def get_visible_to_client(self, obj):
        """Unifica campo 'visibility' (str) con bool esperado por el frontend."""
        vis = getattr(obj, 'visibility', None)
        if isinstance(vis, bool):
            return vis
        if isinstance(vis, str):
            return vis.lower() in ('public', 'client', 'true', '1', 'visible')
        return False


class LogisticsOptionSerializer(serializers.Serializer):
    """Sprint 4 S4-07"""
    id = serializers.UUIDField(source='logistics_option_id')
    option_id = serializers.CharField()
    mode = serializers.CharField()
    carrier = serializers.CharField()
    route = serializers.CharField()
    estimated_days = serializers.IntegerField()
    estimated_cost = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField()
    valid_until = serializers.DateField(allow_null=True)
    source = serializers.CharField()
    is_selected = serializers.BooleanField()


class PaymentLineSummarySerializer(serializers.Serializer):
    """
    FIX-2026-04-08b: expone payment_status y campos S25-01 para que
    PagosSection y CreditBar puedan consumir los pagos del bundle.
    """
    payment_line_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField()
    method = serializers.CharField()
    reference = serializers.CharField()
    created_at = serializers.DateTimeField()
    # S25-01 campos del ciclo de vida del pago
    payment_status = serializers.CharField(default='pending')
    verified_at = serializers.DateTimeField(allow_null=True, required=False)
    verified_by = serializers.CharField(allow_null=True, required=False)
    credit_released_at = serializers.DateTimeField(allow_null=True, required=False)
    credit_released_by = serializers.CharField(allow_null=True, required=False)
    rejection_reason = serializers.CharField(allow_null=True, required=False)


class DocumentSummarySerializer(serializers.Serializer):
    name = serializers.CharField()
    type = serializers.CharField()
    date = serializers.DateTimeField()
    download_url = serializers.CharField()


class ExpedienteBundleSerializer(serializers.Serializer):
    """
    Complete bundle for Expediente Detail page <200ms.
    S20-06: agrega artifact_policy calculada dinámicamente por brand + proformas.
    FIX-2026-03-31: get_product_lines protegido con try/except.
    FIX-2026-04-08: get_expediente expone 'id' como alias de expediente_id.
    FIX-2026-04-08b: credit_snapshot como campo top-level del bundle (Bug CreditBar $0).
    """
    expediente = serializers.SerializerMethodField()
    events = serializers.SerializerMethodField()
    artifacts = serializers.SerializerMethodField()
    costs = serializers.SerializerMethodField()
    payments = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    available_actions = serializers.SerializerMethodField()
    credit_clock = serializers.SerializerMethodField()
    # S20-06: policy de artefactos calculada dinámicamente
    artifact_policy = serializers.SerializerMethodField()
    product_lines = serializers.SerializerMethodField()
    # FIX-2026-04-08b: credit_snapshot top-level (antes solo era campo del serializer S25)
    credit_snapshot = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()

    def get_expediente(self, obj):
        """
        S25-08: Unifies with BundleSerializer to include credit snapshot,
        deferred pricing, and genealogy fields in the UI detail bundle.
        FIX-2026-04-08: Agrega 'id' como alias de expediente_id.
        """
        from .serializers import BundleSerializer
        data = BundleSerializer(obj).data

        # FIX: asegura que 'id' siempre esté presente como string UUID
        data['id'] = str(obj.expediente_id)

        # Merge UI-specific metadata
        data.update({
            'mode': obj.mode,
            'freight_mode': obj.freight_mode,
            'transport_mode': obj.transport_mode,
            'dispatch_mode': obj.dispatch_mode,
            'payment_status': obj.payment_status,
            'price_basis': obj.price_basis,
            'legal_entity_id': str(obj.legal_entity_id),
            'client_id': str(obj.client_id) if obj.client_id else None,
        })
        return data

    def get_events(self, obj):
        events = getattr(obj, '_events', [])
        return EventLogSummarySerializer(events, many=True).data

    def get_artifacts(self, obj):
        return ArtifactSummarySerializer(obj.artifacts.all(), many=True).data

    def get_product_lines(self, obj):
        """
        FIX-2026-03-31: Protegido con try/except para no romper el bundle.
        """
        try:
            from apps.expedientes.serializers import ProductLineSerializer
            return ProductLineSerializer(obj.product_lines.all(), many=True).data
        except Exception:
            return []

    def get_costs(self, obj):
        return CostLineSummarySerializer(obj.cost_lines.all(), many=True).data

    def get_payments(self, obj):
        return PaymentLineSummarySerializer(obj.payment_lines.all(), many=True).data

    def get_available_actions(self, obj):
        return getattr(obj, '_available_actions', [])

    def get_credit_clock(self, obj):
        return {
            'days': getattr(obj, 'credit_days_elapsed', 0),
            'band': getattr(obj, 'credit_band', 'MINT'),
            'started_at': obj.credit_clock_started_at,
            'is_ignored': obj.status in ['CERRADO', 'CANCELADO']
        }

    def get_documents(self, obj):
        docs = []
        for art in obj.artifacts.all():
            if art.status == 'completed' and 'file_url' in art.payload:
                docs.append({
                    'id': str(art.artifact_id),
                    'name': art.payload.get('filename', f"Documento_{art.artifact_type}"),
                    'type': art.artifact_type,
                    'date': art.created_at,
                    'download_url': f"/api/documents/{art.artifact_id}/download/"
                })
        return docs

    def get_artifact_policy(self, obj):
        """
        S20-06: Retorna la política de artefactos resuelta dinámicamente.
        """
        from apps.expedientes.services.artifact_policy import resolve_artifact_policy
        try:
            return resolve_artifact_policy(obj)
        except Exception:
            return {'REGISTRO': {'required': ['ART-01'], 'optional': [], 'gate_for_advance': ['ART-01']}}

    def get_credit_snapshot(self, obj):
        """
        FIX-2026-04-08b: Computa credit_snapshot directamente desde pagos.
        Antes nunca llegaba al frontend — la CreditBar siempre mostraba $0.

        Usa compute_coverage() de services/credit.py (SSOT S25-05):
        solo pagos con payment_status='credit_released' cuentan para total_released.
        """
        try:
            from decimal import Decimal
            from apps.expedientes.services.credit import compute_coverage

            # Solo pagos credit_released cuentan (S25-05)
            total_released = sum(
                p.amount_paid or Decimal('0.00')
                for p in obj.pagos.filter(payment_status='credit_released')
            ) or Decimal('0.00')

            total_pending = sum(
                p.amount_paid or Decimal('0.00')
                for p in obj.pagos.filter(payment_status__in=['pending', 'verified'])
            ) or Decimal('0.00')

            total_rejected = sum(
                p.amount_paid or Decimal('0.00')
                for p in obj.pagos.filter(payment_status='rejected')
            ) or Decimal('0.00')

            # total del expediente: sum de líneas de producto (SSOT)
            total_lines = sum(
                (line.unit_price or Decimal('0.00')) * (line.quantity or 0)
                for line in obj.product_lines.all()
            ) or Decimal('0.00')

            # total_value logic matches services/credit.py
            expediente_total = getattr(obj, 'total_value', None) or total_lines

            payment_coverage, coverage_pct = compute_coverage(total_released, expediente_total)

            credit_released = getattr(obj, 'credit_released', False)

            return {
                'payment_coverage': payment_coverage,
                'coverage_pct': float(coverage_pct),
                'total_released': float(total_released),
                'total_pending': float(total_pending),
                'total_rejected': float(total_rejected),
                'expediente_total': float(expediente_total),
                'credit_released': credit_released,
            }
        except Exception as e:
            # Nunca romper el bundle
            return {
                'payment_coverage': 'none',
                'coverage_pct': 0.0,
                'total_released': 0.0,
                'total_pending': 0.0,
                'total_rejected': 0.0,
                'expediente_total': 0.0,
                'credit_released': False,
                '_error': str(e),
            }

    def get_is_admin(self, obj):
        """Expone is_admin desde el contexto del request (superuser)."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return request.user.is_superuser
        return getattr(obj, '_is_admin', False)
