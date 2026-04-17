from django.db import models
from apps.core.models import TimestampMixin

from apps.core.models import TimestampMixin, UUIDReferenceField

class Product(TimestampMixin):
    sku_base = models.CharField(max_length=50, unique=True, help_text="SKU base del producto")
    brand_id = UUIDReferenceField(target_module='brands', db_index=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    hs_code = models.CharField(max_length=50, blank=True)
    weight_kg = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    cbm = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    moq = models.IntegerField(default=1)
    country_eligibility = models.JSONField(default=list)
    channel_eligibility = models.JSONField(default=list)
    uom = models.CharField(max_length=20, default='PAIR')
    country_of_origin = models.CharField(max_length=3, blank=True)
    lead_time_days = models.IntegerField(default=60)

    class Meta:
        db_table = 'productos_product'
        ordering = ['sku_base']
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'

    def __str__(self):
        return f"{self.name} ({self.sku_base})"

class ProductVariant(TimestampMixin):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    variant_sku = models.CharField(max_length=100, unique=True)
    attributes = models.JSONField(default=dict)
    barcode = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'productos_productvariant'

    def __str__(self):
        return self.variant_sku

# Alias de compatibilidad para evitar roturas inmediatas en otros módulos
ProductMaster = Product
Producto = Product
