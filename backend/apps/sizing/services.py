# Sprint 18 - T0.1 Paso 4: validate_entry_completeness
from django.core.exceptions import ValidationError


def validate_entry_completeness(entry):
    system_dims = set(entry.system.dimensions.values_list('id', flat=True))
    entry_dims = set(entry.dimension_values.values_list('dimension_id', flat=True))
    missing = system_dims - entry_dims
    if missing:
        from apps.sizing.models import SizeDimension
        codes = SizeDimension.objects.filter(id__in=missing).values_list('code', flat=True)
        raise ValidationError(f"Entry '{entry.label}' le faltan dimensiones: {list(codes)}")
