from django.db import models


from apps.core.models import BaseModel, UUIDReferenceField

class Supplier(BaseModel):
    name = models.CharField(max_length=255)
    tax_id = models.CharField(max_length=100, unique=True)
    country = models.CharField(max_length=100)
    address = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    legal_entity_id = UUIDReferenceField(
        target_module='core', 
        target_model='LegalEntity',
        db_index=True,
        null=True, blank=True
    )

    @property
    def legal_entity(self):
        return self.resolve_ref('legal_entity_id')

    def __str__(self):
        return f"{self.name} ({self.tax_id})"


class SupplierContact(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='contacts')
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True, null=True)
    role = models.CharField(max_length=100, blank=True, null=True)
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.supplier.name})"


class SupplierPerformanceKPI(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='performance_kpis')
    year = models.IntegerField()
    month = models.IntegerField()
    on_time_delivery_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    quality_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    cost_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    overall_rating = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    comments = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('supplier', 'year', 'month')

    def __str__(self):
        return f"KPI {self.supplier.name} - {self.year}/{self.month}"
