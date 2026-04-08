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
    S25-08: Includes restricted credit coverage and public deferred price.
    """
    payment_coverage = serializers.SerializerMethodField(read_only=True)
    coverage_pct = serializers.SerializerMethodField(read_only=True)
    deferred_total_price = serializers.SerializerMethodField(read_only=True)
    parent_expediente = serializers.SerializerMethodField(read_only=True)

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
            # S25 restricted fields
            'payment_coverage', 'coverage_pct',
            'deferred_total_price', 'parent_expediente',
        ]

    def get_payment_coverage(self, obj):
        from apps.expedientes.services.credit import compute_coverage
        from decimal import Decimal
        total_released = sum(p.amount_paid for p in obj.pagos.filter(payment_status='credit_released') if p.amount_paid) or Decimal('0.00')
        total_value = getattr(obj, 'total_value', None) or sum((l.unit_price * l.quantity) for l in obj.product_lines.all())
        coverage, _ = compute_coverage(total_released, total_value)
        return coverage

    def get_coverage_pct(self, obj):
        from apps.expedientes.services.credit import compute_coverage
        from decimal import Decimal
        total_released = sum(p.amount_paid for p in obj.pagos.filter(payment_status='credit_released') if p.amount_paid) or Decimal('0.00')
        total_value = getattr(obj, 'total_value', None) or sum((l.unit_price * l.quantity) for l in obj.product_lines.all())
        _, pct = compute_coverage(total_released, total_value)
        return pct

    def get_deferred_total_price(self, obj):
        if obj.deferred_visible:
            return obj.deferred_total_price
        return None

    def get_parent_expediente(self, obj):
        if obj.parent_expediente:
            return str(obj.parent_expediente)
        return None
