from rest_framework import serializers
from .models import ClientOrder, ClientOrderLine

class ClientOrderLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientOrderLine
        fields = ['id', 'sku', 'qty', 'resolved_price', 'base_price', 'override_mode', 'is_formula_locked', 'manual_override_reason']
        read_only_fields = ['resolved_price', 'base_price', 'is_formula_locked']

class ClientOrderSerializer(serializers.ModelSerializer):
    lines = ClientOrderLineSerializer(many=True, required=False)

    class Meta:
        model = ClientOrder
        fields = ['id', 'client', 'brand', 'status', 'content_fingerprint', 'resolved_max_revisions', 'revision_count', 'lines', 'created_at', 'updated_at']
        read_only_fields = ['status', 'content_fingerprint', 'resolved_max_revisions', 'revision_count', 'created_at', 'updated_at']

    def create(self, validated_data):
        lines_data = validated_data.pop('lines', [])
        order = ClientOrder.objects.create(**validated_data)
        for line_data in lines_data:
            ClientOrderLine.objects.create(order=order, **line_data)
        return order
