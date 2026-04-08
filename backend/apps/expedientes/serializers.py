# Sprint 18 - T1.1: Serializers para expedientes
# S20-06: BundleSerializer ahora incluye artifact_policy calculada dinámicamente
from decimal import Decimal
from rest_framework import serializers
from .models import (
    Expediente, ExpedienteProductLine, FactoryOrder,
    ExpedientePago, EventLog,
)


class ProductLineSerializer(serializers.ModelSerializer):
    size_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ExpedienteProductLine
        fields = [
            'id', 'expediente', 'product',
            'brand_sku', 'size_display',
            'quantity', 'unit_price', 'price_source',
            'pricelist_used', 'base_price',
            'quantity_modified', 'unit_price_modified', 'modification_reason',
            'factory_order', 'created_at', 'updated_at', 'proforma',
        ]
        read_only_fields = ['size_display', 'pricelist_used', 'base_price']

    def get_size_display(self, obj):
        if obj.brand_sku and hasattr(obj.brand_sku, 'size') and obj.brand_sku.size:
            return obj.brand_sku.size
        return '\u2014'


class FactoryOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = FactoryOrder
        fields = [
            'id', 'expediente', 'order_number',
            'proforma_client_number', 'proforma_mwt_number',
            'purchase_number', 'url_proforma_client', 'url_proforma_mwt',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['expediente', 'created_at', 'updated_at']


class PagoSerializer(serializers.ModelSerializer):
    """S25-08: CEO / AGENT_* tier — incluye campos completos del payment status machine."""
    verified_by_display = serializers.SerializerMethodField(read_only=True)
    credit_released_by_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ExpedientePago
        fields = [
            'id', 'expediente', 'tipo_pago', 'metodo_pago',
            'payment_date', 'amount_paid', 'additional_info',
            'url_comprobante', 'credit_status', 'created_at',
            # S25-01 nuevos
            'payment_status',
            'verified_at', 'verified_by', 'verified_by_display',
            'credit_released_at', 'credit_released_by', 'credit_released_by_display',
            'rejection_reason',
        ]
        read_only_fields = [
            'credit_status', 'expediente', 'created_at',
            'payment_status', 'verified_at', 'verified_by', 'verified_by_display',
            'credit_released_at', 'credit_released_by', 'credit_released_by_display',
        ]

    def get_verified_by_display(self, obj):
        if obj.verified_by:
            return getattr(obj.verified_by, 'get_full_name', lambda: str(obj.verified_by))() or str(obj.verified_by)
        return None

    def get_credit_released_by_display(self, obj):
        if obj.credit_released_by:
            return getattr(obj.credit_released_by, 'get_full_name', lambda: str(obj.credit_released_by))() or str(obj.credit_released_by)
        return None


class PagoClienteSerializer(serializers.ModelSerializer):
    """
    S25-08: CLIENT_* tier — campos restringidos.
    NUNCA incluye: rejection_reason, verified_by, credit_released_by.
    El badge 'rejected' es informativo (cliente sabe, no ve motivo interno).
    """
    class Meta:
        model = ExpedientePago
        fields = [
            'id', 'payment_date', 'amount_paid', 'payment_status',
        ]
        read_only_fields = fields


class BundleSerializer(serializers.ModelSerializer):
    """
    S25-08: CEO / AGENT_* tier.
    Incluye snapshot de credito extendido, deferred pricing y genealogía.
    """
    artifact_policy = serializers.SerializerMethodField(read_only=True)
    payment_coverage = serializers.SerializerMethodField(read_only=True)
    coverage_pct = serializers.SerializerMethodField(read_only=True)
    total_pending = serializers.SerializerMethodField(read_only=True)
    total_rejected = serializers.SerializerMethodField(read_only=True)
    parent_expediente = serializers.SerializerMethodField(read_only=True)
    child_expedientes = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Expediente
        fields = [
            'expediente_id', 'status', 'brand', 'client',
            'credit_released', 'credit_exposure',
            'purchase_order_number', 'factory_order_number',
            'incoterms', 'created_at', 'updated_at',
            'artifact_policy',
            # S25 - Crédito
            'payment_coverage', 'coverage_pct',
            'total_pending', 'total_rejected',
            # S25 - Deferred
            'deferred_total_price', 'deferred_visible',
            # S25 - Genealogy
            'parent_expediente', 'child_expedientes', 'is_inverted_child',
        ]
        read_only_fields = [
            'credit_released', 'credit_exposure', 'expediente_id', 
            'artifact_policy', 'is_inverted_child'
        ]

    def get_artifact_policy(self, obj):
        from apps.expedientes.services.artifact_policy import resolve_artifact_policy
        return resolve_artifact_policy(obj)

    def _get_coverage_data(self, obj):
        """Helper to avoid redundant calculations."""
        if hasattr(self, '_coverage_cache') and getattr(self, '_coverage_cache_id', None) == obj.pk:
            return self._coverage_cache
        
        from .services.credit import compute_coverage
        total_released = sum(
            p.amount_paid for p in obj.pagos.filter(payment_status='credit_released')
            if p.amount_paid
        ) or Decimal('0.00')
        
        # total_value logic matches services/credit.py
        total_lines = sum(
            (line.unit_price * line.quantity)
            for line in obj.product_lines.all()
        ) or Decimal('0.00')
        expediente_total = getattr(obj, 'total_value', None) or total_lines
        
        res = compute_coverage(total_released, expediente_total)
        self._coverage_cache = res
        self._coverage_cache_id = obj.pk
        return res

    def get_payment_coverage(self, obj):
        return self._get_coverage_data(obj)[0]

    def get_coverage_pct(self, obj):
        return self._get_coverage_data(obj)[1]

    def get_total_pending(self, obj):
        return sum(
            p.amount_paid for p in obj.pagos.filter(payment_status__in=['pending', 'verified'])
            if p.amount_paid
        ) or Decimal('0.00')

    def get_total_rejected(self, obj):
        return sum(
            p.amount_paid for p in obj.pagos.filter(payment_status='rejected')
            if p.amount_paid
        ) or Decimal('0.00')

    def get_parent_expediente(self, obj):
        if obj.parent_expediente:
            return {
                'id': str(obj.parent_expediente.expediente_id),
                'number': str(obj.parent_expediente)
            }
        return None

    def get_child_expedientes(self, obj):
        return [
            {'id': str(c.expediente_id), 'number': str(c)}
            for c in obj.child_expedientes.all()
        ]


class BundlePortalSerializer(serializers.ModelSerializer):
    """
    S25-08: CLIENT_* tier.
    Tiering rules (fix M2 R3):
    - NO montos financieros internos ($ pending/rejected, exposure).
    - SOLO payment_coverage + coverage_pct.
    - Deferred price solo si deferred_visible=True.
    - Pagos restringidos (PagoClienteSerializer).
    """
    payment_coverage = serializers.SerializerMethodField(read_only=True)
    coverage_pct = serializers.SerializerMethodField(read_only=True)
    deferred_total_price = serializers.SerializerMethodField(read_only=True)
    parent_expediente = serializers.SerializerMethodField(read_only=True)
    pagos = PagoClienteSerializer(many=True, read_only=True)

    class Meta:
        model = Expediente
        fields = [
            'expediente_id', 'status', 'brand', 'incoterms',
            'payment_coverage', 'coverage_pct',
            'deferred_total_price', 'parent_expediente',
            'pagos',
        ]
        read_only_fields = fields

    def get_payment_coverage(self, obj):
        from .services.credit import compute_coverage
        total_released = sum(
            p.amount_paid for p in obj.pagos.filter(payment_status='credit_released')
            if p.amount_paid
        ) or Decimal('0.00')
        total_lines = sum((l.unit_price * l.quantity) for l in obj.product_lines.all()) or Decimal('0.00')
        expediente_total = getattr(obj, 'total_value', None) or total_lines
        coverage, _ = compute_coverage(total_released, expediente_total)
        return coverage

    def get_coverage_pct(self, obj):
        from .services.credit import compute_coverage
        total_released = sum(
            p.amount_paid for p in obj.pagos.filter(payment_status='credit_released')
            if p.amount_paid
        ) or Decimal('0.00')
        total_lines = sum((l.unit_price * l.quantity) for l in obj.product_lines.all()) or Decimal('0.00')
        expediente_total = getattr(obj, 'total_value', None) or total_lines
        _, pct = compute_coverage(total_released, expediente_total)
        return pct

    def get_deferred_total_price(self, obj):
        if obj.deferred_visible:
            return obj.deferred_total_price
        return None

    def get_parent_expediente(self, obj):
        if obj.parent_expediente:
            return str(obj.parent_expediente)
        return None


class SizeSystemSerializer(serializers.Serializer):
    """Read-only nested serializer para SizeSystem desde frontend."""
    id = serializers.IntegerField(read_only=True)
    code = serializers.CharField(read_only=True)
    category = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    entries = serializers.SerializerMethodField(read_only=True)

    def get_entries(self, obj):
        from apps.sizing.models import SizeEntry
        entries = obj.entries.filter(is_active=True).order_by('display_order')
        return [
            {
                'id': e.id,
                'label': e.label,
                'display_order': e.display_order,
                'equivalences': list(
                    e.equivalences.values('standard_system', 'value', 'is_primary')
                ),
            }
            for e in entries
        ]
