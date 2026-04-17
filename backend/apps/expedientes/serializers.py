# Sprint 18 - T1.1: Serializers para expedientes
# S20-06: BundleSerializer ahora incluye artifact_policy calculada dinámicamente
from decimal import Decimal
from rest_framework import serializers
from apps.core.registry import ModuleRegistry
from .models import (
    Expediente, ExpedienteProductLine, FactoryOrder, EventLog,
)

class ProductLineSerializer(serializers.ModelSerializer):
    size_display = serializers.SerializerMethodField(read_only=True)
    product_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ExpedienteProductLine
        fields = [
            'id', 'expediente', 'product_id', 'product_name',
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

    def get_product_name(self, obj):
        prod = obj.product
        return prod.product_name if prod else "N/A"

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
        payment_model = ModuleRegistry.get_model('finance', 'Payment')
        model = payment_model
        fields = [
            'id', 'expediente_id', 'tipo_pago', 'metodo_pago',
            'payment_date', 'amount_paid', 'additional_info',
            'url_comprobante', 'status', 'created_at',
            'verified_at', 'verified_by', 'verified_by_display',
            'credit_released_at', 'credit_released_by', 'credit_released_by_display',
            'rejection_reason',
        ]
        read_only_fields = [
            'expediente_id', 'created_at', 'status',
            'verified_at', 'verified_by', 'verified_by_display',
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
    """S25-08: CLIENT_* tier — campos restringidos."""
    class Meta:
        payment_model = ModuleRegistry.get_model('finance', 'Payment')
        model = payment_model
        fields = ['id', 'payment_date', 'amount_paid', 'status']
        read_only_fields = fields

class BundleSerializer(serializers.ModelSerializer):
    """S25-08: CEO / AGENT_* tier."""
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
            'expediente_id', 'status', 'brand_id', 'client_id',
            'credit_released', 'credit_exposure',
            'purchase_order_number', 'factory_order_number',
            'incoterms', 'created_at', 'updated_at',
            'artifact_policy',
            'payment_coverage', 'coverage_pct',
            'total_pending', 'total_rejected',
            'deferred_total_price', 'deferred_visible',
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
        if hasattr(self, '_coverage_cache') and getattr(self, '_coverage_cache_id', None) == obj.pk:
            return self._coverage_cache
        
        from .services.credit import compute_coverage
        payment_model = ModuleRegistry.get_model('finance', 'Payment')
        total_released = Decimal('0.00')
        if payment_model:
            total_released = sum(
                p.amount_paid for p in payment_model.objects.filter(
                    expediente_id=obj.expediente_id, status='credit_released'
                )
            ) or Decimal('0.00')
        
        total_lines = sum(
            (line.unit_price or Decimal('0.00')) * (line.quantity or 0)
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
        payment_model = ModuleRegistry.get_model('finance', 'Payment')
        if not payment_model: return Decimal('0.00')
        return sum(
            p.amount_paid for p in payment_model.objects.filter(
                expediente_id=obj.expediente_id, status__in=['pending', 'verified']
            )
        ) or Decimal('0.00')

    def get_total_rejected(self, obj):
        payment_model = ModuleRegistry.get_model('finance', 'Payment')
        if not payment_model: return Decimal('0.00')
        return sum(
            p.amount_paid for p in payment_model.objects.filter(
                expediente_id=obj.expediente_id, status='rejected'
            )
        ) or Decimal('0.00')

    def get_parent_expediente(self, obj):
        parent = obj.parent_expediente
        if parent:
            return {'id': str(parent.expediente_id), 'number': str(parent)}
        return None

    def get_child_expedientes(self, obj):
        return [
            {'id': str(c.expediente_id), 'number': str(c)}
            for c in obj.child_expedientes.all()
        ]

class BundlePortalSerializer(serializers.ModelSerializer):
    """S25-08: CLIENT_* tier."""
    payment_coverage = serializers.SerializerMethodField(read_only=True)
    coverage_pct = serializers.SerializerMethodField(read_only=True)
    deferred_total_price = serializers.SerializerMethodField(read_only=True)
    parent_expediente = serializers.SerializerMethodField(read_only=True)
    pagos = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Expediente
        fields = [
            'expediente_id', 'status', 'brand_id', 'incoterms',
            'payment_coverage', 'coverage_pct',
            'deferred_total_price', 'parent_expediente',
            'pagos',
        ]
        read_only_fields = fields

    def get_pagos(self, obj):
        payment_model = ModuleRegistry.get_model('finance', 'Payment')
        if not payment_model: return []
        pagos = payment_model.objects.filter(expediente_id=obj.expediente_id)
        return PagoClienteSerializer(pagos, many=True).data

    def get_payment_coverage(self, obj):
        from .services.credit import compute_coverage
        payment_model = ModuleRegistry.get_model('finance', 'Payment')
        total_released = Decimal('0.00')
        if payment_model:
            total_released = sum(
                p.amount_paid for p in payment_model.objects.filter(
                    expediente_id=obj.expediente_id, status='credit_released'
                )
            ) or Decimal('0.00')
        total_lines = sum((l.unit_price * l.quantity) for l in obj.product_lines.all()) or Decimal('0.00')
        expediente_total = getattr(obj, 'total_value', None) or total_lines
        coverage, _ = compute_coverage(total_released, expediente_total)
        return coverage

    def get_coverage_pct(self, obj):
        from .services.credit import compute_coverage
        payment_model = ModuleRegistry.get_model('finance', 'Payment')
        total_released = Decimal('0.00')
        if payment_model:
            total_released = sum(
                p.amount_paid for p in payment_model.objects.filter(
                    expediente_id=obj.expediente_id, status='credit_released'
                )
            ) or Decimal('0.00')
        total_lines = sum((l.unit_price * l.quantity) for l in obj.product_lines.all()) or Decimal('0.00')
        expediente_total = getattr(obj, 'total_value', None) or total_lines
        _, pct = compute_coverage(total_released, expediente_total)
        return pct

    def get_deferred_total_price(self, obj):
        return obj.deferred_total_price if obj.deferred_visible else None

    def get_parent_expediente(self, obj):
        return str(obj.parent_expediente) if obj.parent_expediente else None

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
