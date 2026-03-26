from rest_framework import serializers
from .models import InventoryEntry

class InventoryEntrySerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    product_sku = serializers.ReadOnlyField(source='product.sku_base')
    node_name = serializers.ReadOnlyField(source='node.name')

    class Meta:
        model = InventoryEntry
        fields = [
            'id', 'product', 'product_name', 'product_sku',
            'node', 'node_name', 'quantity', 'reserved',
            'lot_number', 'received_at', 'created_at', 'updated_at'
        ]
