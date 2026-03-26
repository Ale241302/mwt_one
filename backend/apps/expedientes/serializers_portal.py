"""S17-04: Portal serializers — CEO-ONLY and internal fields excluded."""
from rest_framework import serializers
from .models import Expediente

# Fields that must NEVER be exposed through the portal
_CEO_ONLY_FIELDS = {
    'fob_unit', 'margin_pct', 'commission_pct',
    'landed_cost', 'dai_amount',
}

_INTERNAL_PREFIXES = ('internal_', 'ceo_')


def _is_safe_field(field_name: str) -> bool:
    """Returns True if the field is safe to expose through the portal."""
    if field_name in _CEO_ONLY_FIELDS:
        return False
    for prefix in _INTERNAL_PREFIXES:
        if field_name.startswith(prefix):
            return False
    return True


class PortalExpedienteListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for portal list endpoint."""

    class Meta:
        model = Expediente
        fields = [
            'expediente_id',
            'status',
            'destination',
            'created_at',
            'updated_at',
            'payment_status',
            'is_blocked',
        ]


class PortalExpedienteDetailSerializer(serializers.ModelSerializer):
    """
    Detail serializer for portal — explicitly excludes CEO-ONLY fields.
    Any field added to Expediente with 'internal_' or 'ceo_' prefix
    is automatically excluded by the _is_safe_field guard.
    """

    class Meta:
        model = Expediente
        # Explicitly safe fields only — NO fob_unit, margin_pct, commission_pct, etc.
        fields = [
            'expediente_id',
            'destination',
            'status',
            'is_blocked',
            'blocked_reason',
            'mode',
            'freight_mode',
            'transport_mode',
            'dispatch_mode',
            'payment_status',
            'payment_registered_at',
            'created_at',
            'updated_at',
        ]
