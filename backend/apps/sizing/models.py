from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


CATEGORY_CHOICES = [
    ('FOOTWEAR', 'Footwear'),
    ('SHIRT', 'Shirt'),
    ('PANTS', 'Pants'),
    ('GLOVES', 'Gloves'),
    ('GENERIC', 'Generic'),
]


class SizeSystem(models.Model):
    """Sistema de tallas de plataforma. Sin FK a Brand (la asignacion va en BrandSizeSystemAssignment)."""
    code = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='GENERIC')
    description = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f'{self.code} ({self.category})'


class SizeDimension(models.Model):
    """N dimensiones por sistema (ej: EU, US_MEN, CM)."""
    system = models.ForeignKey(
        SizeSystem, on_delete=models.CASCADE, related_name='dimensions'
    )
    code = models.CharField(max_length=30)
    display_name = models.CharField(max_length=60)
    unit = models.CharField(max_length=20, blank=True, default='')
    display_order = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False)

    class Meta:
        unique_together = [('system', 'code')]
        ordering = ['system', 'display_order', 'code']

    def __str__(self):
        return f'{self.system.code} / {self.code}'


class SizeEntry(models.Model):
    """Una talla individual dentro de un sistema."""
    system = models.ForeignKey(
        SizeSystem, on_delete=models.CASCADE, related_name='entries'
    )
    label = models.CharField(max_length=20, help_text="Etiqueta visible, ej: 'S1', '42'")
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [('system', 'label')]
        ordering = ['system', 'display_order', 'label']

    def __str__(self):
        return f'{self.system.code} / {self.label}'


class SizeEntryValue(models.Model):
    """Valor de una dimension especifica para una talla."""
    entry = models.ForeignKey(
        SizeEntry, on_delete=models.CASCADE, related_name='dimension_values'
    )
    dimension = models.ForeignKey(
        SizeDimension, on_delete=models.CASCADE, related_name='entry_values'
    )
    value = models.CharField(max_length=30)

    class Meta:
        unique_together = [('entry', 'dimension')]

    def clean(self):
        if self.dimension_id and self.entry_id:
            if self.dimension.system_id != self.entry.system_id:
                raise ValidationError(
                    'La dimension y la entry deben pertenecer al mismo SizeSystem.'
                )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.entry} | {self.dimension.code}: {self.value}'


class SizeEquivalence(models.Model):
    """Mapeo 1:N de una SizeEntry a un sistema estandar externo."""
    entry = models.ForeignKey(
        SizeEntry, on_delete=models.CASCADE, related_name='equivalences'
    )
    standard_system = models.CharField(
        max_length=30,
        help_text="Codigo libre del sistema estandar, ej: 'EU', 'US_MEN', 'CM'"
    )
    value = models.CharField(max_length=30)
    display_order = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False)

    class Meta:
        unique_together = [('entry', 'standard_system', 'value')]
        ordering = ['entry', 'display_order', 'standard_system']

    def __str__(self):
        return f'{self.entry} -> {self.standard_system}: {self.value}'


class BrandSizeSystemAssignment(models.Model):
    """Asignacion M:N entre Brand y SizeSystem."""
    brand = models.ForeignKey(
        'brands.Brand', on_delete=models.CASCADE, related_name='size_system_assignments'
    )
    size_system = models.ForeignKey(
        SizeSystem, on_delete=models.CASCADE, related_name='brand_assignments'
    )
    is_default = models.BooleanField(default=False)
    assigned_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True, default='')

    class Meta:
        unique_together = [('brand', 'size_system')]
        ordering = ['brand', '-is_default', 'size_system__code']

    def __str__(self):
        return f'{self.brand} <-> {self.size_system.code}'
