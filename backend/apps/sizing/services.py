from django.core.exceptions import ValidationError


def validate_entry_completeness(entry):
    """Valida que una SizeEntry tenga valores para TODAS las dimensiones de su sistema."""
    system_dims = set(entry.system.dimensions.values_list('id', flat=True))
    entry_dims = set(entry.dimension_values.values_list('dimension_id', flat=True))
    missing = system_dims - entry_dims
    if missing:
        from apps.sizing.models import SizeDimension
        codes = list(
            SizeDimension.objects.filter(id__in=missing).values_list('code', flat=True)
        )
        raise ValidationError(
            f"Entry '{entry.label}' le faltan dimensiones: {codes}"
        )
