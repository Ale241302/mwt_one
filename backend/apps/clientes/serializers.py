from rest_framework import serializers
from apps.clientes.models import Cliente


class ClienteSerializer(serializers.ModelSerializer):
    legal_entity_name = serializers.SerializerMethodField()
    active_expedientes = serializers.IntegerField(read_only=True)

    class Meta:
        model = Cliente
        fields = [
            'id', 'name', 'contact_name', 'email', 'phone', 'country',
            'legal_entity', 'legal_entity_name', 'credit_approved',
            'active_expedientes', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'legal_entity_name', 'active_expedientes']

    def get_legal_entity_name(self, obj):
        return obj.legal_entity.legal_name if obj.legal_entity else None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['active_expedientes'] = instance.active_expedientes
        return data
