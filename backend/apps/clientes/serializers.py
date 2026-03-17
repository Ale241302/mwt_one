from rest_framework import serializers
from apps.clientes.models import Cliente


class ClienteSerializer(serializers.ModelSerializer):
    legal_entity_name = serializers.SerializerMethodField()
    active_expedientes = serializers.SerializerMethodField()

    class Meta:
        model = Cliente
        fields = [
            'id', 'name', 'contact_name', 'email', 'phone', 'country',
            'legal_entity', 'legal_entity_name', 'credit_approved',
            'active_expedientes', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_legal_entity_name(self, obj):
        try:
            return obj.legal_entity.legal_name if obj.legal_entity_id else None
        except Exception:
            return None

    def get_active_expedientes(self, obj):
        return 0
