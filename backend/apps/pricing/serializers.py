# Sprint 22 - S22-08: Serializers para Bulk Assignment y pricing resolve
from rest_framework import serializers
from apps.pricing.models import ClientProductAssignment


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
