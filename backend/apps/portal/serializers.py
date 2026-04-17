from rest_framework import serializers

class PortalProductLineSerializer(serializers.ModelSerializer):
    product_name = serializers.SerializerMethodField()
    size = serializers.ReadOnlyField(source='size_display')
    
    class Meta:
        from apps.expedientes.models import ExpedienteProductLine
        model = ExpedienteProductLine
        fields = ['product_name', 'size', 'quantity', 'unit_price']

    def get_product_name(self, obj):
        prod = obj.product
        return prod.product_name if prod else "N/A"

class ExpedientePortalSerializer(serializers.ModelSerializer):
    brand_name = serializers.SerializerMethodField()
    is_operated_by_mwt = serializers.SerializerMethodField()
    product_lines = PortalProductLineSerializer(many=True, read_only=True)
    
    class Meta:
        from apps.expedientes.models import Expediente
        model = Expediente
        fields = [
            'expediente_id', 'brand_id', 'brand_name', 'status', 
            'created_at', 'updated_at', 'is_operated_by_mwt', 'product_lines',
            'purchase_order_number'
        ]

    def get_brand_name(self, obj):
        brand = obj.brand
        return brand.name if brand else "N/A"

    def get_is_operated_by_mwt(self, obj):
        return obj.operado_por == 'MWT'

class ArtifactPortalSerializer(serializers.ModelSerializer):
    class Meta:
        from apps.expedientes.models import ArtifactInstance
        model = ArtifactInstance
        fields = ['artifact_id', 'artifact_type', 'status', 'payload', 'created_at', 'updated_at']
