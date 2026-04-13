from rest_framework import serializers
from apps.expedientes.models import Expediente, ArtifactInstance, ExpedienteProductLine

class PortalProductLineSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    size = serializers.ReadOnlyField(source='size_display')
    
    class Meta:
        model = ExpedienteProductLine
        fields = ['product_name', 'size', 'quantity', 'unit_price']

class ExpedientePortalSerializer(serializers.ModelSerializer):
    brand_name = serializers.ReadOnlyField(source='brand.name')
    is_operated_by_mwt = serializers.SerializerMethodField()
    product_lines = PortalProductLineSerializer(many=True, read_only=True)
    
    class Meta:
        model = Expediente
        fields = [
            'expediente_id', 'brand', 'brand_name', 'status', 
            'created_at', 'updated_at', 'is_operated_by_mwt', 'product_lines',
            'purchase_order_number'
        ]

    def get_is_operated_by_mwt(self, obj):
        return obj.operado_por == 'MWT'

class ArtifactPortalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArtifactInstance
        fields = ['artifact_id', 'artifact_type', 'status', 'payload', 'created_at', 'updated_at']
