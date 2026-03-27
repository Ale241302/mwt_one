# Sprint 18 - T0.1: Motor dimensional de tallas
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class SizeSystem(models.Model):
    CATEGORY_CHOICES = [
        ('FOOTWEAR', 'Footwear'),
        ('SHIRT', 'Shirt'),
        ('PANTS', 'Pants'),
        ('GLOVES', 'Gloves'),
        ('GENERIC', 'Generic'),
    ]
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
    system = models.ForeignKey(SizeSystem, on_delete=models.CASCADE, related_name='dimensions')
    code = models.CharField(max_length=30)
    display_name = models.CharField(max_length=60)
    unit = models.CharField(max_length=20, blank=True, default='')
    display_order = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ['system', 'display_order', 'code']
        unique_together = [('system', 'code')]

    def __str__(self):
        return f'{self.system.code} / {self.code}'


class SizeEntry(models.Model):
    system = models.ForeignKey(SizeSystem, on_delete=models.CASCADE, related_name='entries')
    label = models.CharField(max_length=20, help_text="Etiqueta visible, ej: 'S1', '42'")
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['system', 'display_order', 'label']
        unique_together = [('system', 'label')]

    def __str__(self):
        return f'{self.system.code} / {self.label}'


class SizeEntryValue(models.Model):
    entry = models.ForeignKey(SizeEntry, on_delete=models.CASCADE, related_name='dimension_values')
    dimension = models.ForeignKey(SizeDimension, on_delete=models.CASCADE, related_name='entry_values')
    value = models.CharField(max_length=30)

    class Meta:
        unique_together = [('entry', 'dimension')]

    def clean(self):
        if self.dimension.system_id != self.entry.system_id:
            raise ValidationError(
                'La dimension pertenece a un sistema distinto al de la entrada de talla.'
            )

    def __str__(self):
        return f'{self.entry} [{self.dimension.code}={self.value}]'


class SizeEquivalence(models.Model):
    entry = models.ForeignKey(SizeEntry, on_delete=models.CASCADE, related_name='equivalences')
    standard_system = models.CharField(
        max_length=30,
        help_text="Codigo libre del sistema estandar, ej: 'EU', 'US_MEN', 'CM'"
    )
    value = models.CharField(max_length=30)
    display_order = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ['entry', 'display_order', 'standard_system']
        unique_together = [('entry', 'standard_system', 'value')]

    def __str__(self):
        return f'{self.entry} {self.standard_system}={self.value}'


class BrandSizeSystemAssignment(models.Model):
    brand = models.ForeignKey(
        'brands.Brand', on_delete=models.CASCADE,
        related_name='size_system_assignments'
    )
    size_system = models.ForeignKey(
        SizeSystem, on_delete=models.CASCADE,
        related_name='brand_assignments'
    )
    is_default = models.BooleanField(default=False)
    assigned_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['brand', '-is_default', 'size_system__code']
        unique_together = [('brand', 'size_system')]

    def __str__(self):
        return f'{self.brand} ↔ {self.size_system}'
