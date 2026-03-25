from rest_framework import serializers
from apps.clientes.models import Cliente, ClientSubsidiary


class ClientSubsidiarySerializer(serializers.ModelSerializer):
    """S16-03: Serializer for Subsidiary with tax_id masking."""
    class Meta:
        model = ClientSubsidiary
        fields = [
            'id', 'alias', 'name', 'country', 'legal_name',
            'tax_id', 'address', 'email_billing', 'is_active'
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        if request and request.user:
            is_ceo = getattr(request.user, 'role', '') == 'CEO' or request.user.is_superuser
            if not is_ceo and data.get('tax_id'):
                # Mask tax_id: keep first 3 and last 2, others as '*'
                val = data['tax_id']
                if len(val) > 5:
                    data['tax_id'] = f"{val[:3]}{'*' * (len(val)-5)}{val[-2:]}"
                else:
                    data['tax_id'] = '*' * len(val)
        return data


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
