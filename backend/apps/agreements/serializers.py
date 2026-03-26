from rest_framework import serializers
from .models import CreditOverride


class CreditOverrideSerializer(serializers.ModelSerializer):
    """S16-01B: Serializer for CEO credit override per command.

    Fields align with the updated CreditOverride model that uses
    FK+command_code unique_together instead of OneToOneField.
    """
    class Meta:
        model = CreditOverride
        fields = [
            'id',
            'expediente',
            'brand',
            'command_code',
            'amount_over_limit',
            'authorized_by',
            'reason',
            'authorized_at',
        ]
        read_only_fields = ['id', 'authorized_at']

    def validate_reason(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError("reason debe tener mínimo 10 caracteres.")
        return value
