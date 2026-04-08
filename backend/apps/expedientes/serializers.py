# Sprint 18 - T1.1: Serializers para expedientes
# S20-06: BundleSerializer ahora incluye artifact_policy calculada dinámicamente
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
    # S20-06: policy de artefactos calculada dinámicamente según brand y proformas del expediente
    artifact_policy = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Expediente
        fields = [
            'expediente_id', 'status', 'brand', 'client',
            'credit_released', 'credit_exposure',
            'purchase_order_number', 'factory_order_number',
            'incoterms', 'created_at', 'updated_at',
            'artifact_policy',  # S20-06
        ]
        read_only_fields = ['credit_released', 'credit_exposure', 'expediente_id', 'artifact_policy']

    def get_artifact_policy(self, obj):
        """
        Retorna la política de artefactos resuelta dinámicamente.
        - Sin proformas completadas → solo estado REGISTRO
        - Con proformas → policy completa por estado, mergeada por mode
        """
        from apps.expedientes.services.artifact_policy import resolve_artifact_policy
        return resolve_artifact_policy(obj)


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
