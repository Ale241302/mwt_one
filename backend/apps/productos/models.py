from django.db import models
from apps.core.models import TimestampMixin

class Producto(TimestampMixin):
    name = models.CharField(max_length=255)
    sku_base = models.CharField(max_length=50, unique=True, help_text="SKU base del producto")
    brand = models.ForeignKey('brands.Brand', on_delete=models.PROTECT, related_name='productos')
    category = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'productos_producto'
        ordering = ['name']
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'

    def __str__(self):
        return f"{self.name} ({self.sku_base})"
