# Sprint 22 - S22-08: Serializers para Bulk Assignment y pricing resolve
from rest_framework import serializers




class BulkAssignmentSerializer(serializers.Serializer):
    """
    S22-08: Serializer para bulk create de ClientProductAssignments.
    Recibe product_key y lista de client_subsidiary_ids.
    """
    product_key = serializers.CharField(
        help_text='product_key del BrandSKU (ej: MARLUVAS-REF-001)'
    )
    client_subsidiary_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        help_text='Lista de IDs de ClientSubsidiary a asignar',
    )


class PricingPortalSerializer(serializers.Serializer):
    """
    S22-18: Solo expone price y moq — NUNCA source, base_price,
    discount, size_multipliers ni grade_pricelist_version por portal.
    """
    price = serializers.DecimalField(max_digits=12, decimal_places=4, allow_null=True)
    grade_moq = serializers.IntegerField(allow_null=True)


class PricingInternalSerializer(serializers.Serializer):
    """
    Serializer completo para uso interno (backoffice, Brand Console).
    Expone todos los campos del dict de resolve_client_price.
    """
    price = serializers.DecimalField(max_digits=12, decimal_places=4, allow_null=True)
    source = serializers.CharField(allow_null=True)
    pricelist_version = serializers.IntegerField(allow_null=True)
    discount_applied = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    base_price = serializers.DecimalField(max_digits=12, decimal_places=4, allow_null=True)
    grade_moq = serializers.IntegerField(allow_null=True)
    size_multipliers = serializers.DictField(allow_null=True)
    grade_pricelist_version = serializers.IntegerField(allow_null=True)


class PriceListGradeItemSerializer(serializers.ModelSerializer):
    """S22-01: Serializer para items de la pricelist (GradeItems)."""
    class Meta:
        from apps.pricing.models import PriceListGradeItem
        model = PriceListGradeItem
        fields = [
            'id', 'brand_sku', 'reference_code', 'unit_price_usd', 
            'grade_label', 'size_multipliers', 'moq_total'
        ]


class PriceListVersionSerializer(serializers.ModelSerializer):
    """S22-01: Serializer para versiones de pricelist."""
    items_count = serializers.IntegerField(read_only=True)
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)

    class Meta:
        from apps.pricing.models import PriceListVersion
        model = PriceListVersion
        fields = [
            'id', 'version_label', 'is_active', 'created_at', 
            'activated_at', 'notes', 'items_count', 'uploaded_by_name'
        ]


class EarlyPaymentTierSerializer(serializers.ModelSerializer):
    """S22-03: Serializer para tramos de pronto pago."""
    class Meta:
        from apps.pricing.models import EarlyPaymentTier
        model = EarlyPaymentTier
        fields = ['id', 'payment_days', 'discount_pct']


class EarlyPaymentPolicySerializer(serializers.ModelSerializer):
    """S22-03: Serializer para políticas de pronto pago."""
    tiers = EarlyPaymentTierSerializer(many=True, read_only=True)
    client_subsidiary_name = serializers.CharField(source='client_subsidiary.name', read_only=True)

    class Meta:
        from apps.pricing.models import EarlyPaymentPolicy
        model = EarlyPaymentPolicy
        fields = [
            'id', 'client_subsidiary', 'client_subsidiary_name', 
            'base_payment_days', 'base_commission_pct', 'is_active', 'tiers'
        ]


class ClientProductAssignmentSerializer(serializers.ModelSerializer):
    """S22-02: Serializer para assignments."""
    client_subsidiary_name = serializers.CharField(source='client_subsidiary.name', read_only=True)
    brand_sku_code = serializers.CharField(source='brand_sku.sku_code', read_only=True)
    brand_sku_description = serializers.SerializerMethodField()

    def get_brand_sku_description(self, obj):
        return f"Ref: {obj.brand_sku.product_key}"
    is_stale = serializers.BooleanField(read_only=True)

    class Meta:
        from apps.pricing.models import ClientProductAssignment
        model = ClientProductAssignment
        fields = [
            'id', 'client_subsidiary', 'client_subsidiary_name', 
            'brand_sku', 'brand_sku_code', 'brand_sku_description',
            'cached_client_price', 'cached_base_price', 'cached_at', 
            'is_active', 'is_stale'
        ]
