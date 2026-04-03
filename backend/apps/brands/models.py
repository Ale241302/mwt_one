import uuid
from django.db import models
from apps.core.models import TimestampMixin

class BrandType(models.TextChoices):
    OWN = 'own', 'Own'
    CLIENT = 'client', 'Client'

class Brand(TimestampMixin):
    slug = models.CharField(max_length=50, unique=True, primary_key=True)
    name = models.CharField(max_length=255)
    brand_type = models.CharField(max_length=20, choices=BrandType.choices, default=BrandType.CLIENT)
    is_active = models.BooleanField(default=True)
    # S22-04: Alerta de margen mínimo. Solo activa si tiene valor (nullable).
    min_margin_alert_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Porcentaje mínimo de margen. Si el CPA cacheado cae por debajo, se genera una alerta.',
    )

    def __str__(self):
        return self.name

class DestinationChoices(models.TextChoices):
    CR = 'CR', 'Costa Rica'
    USA = 'USA', 'United States'
    ALL = 'ALL', 'All destinations'

class BrandArtifactRule(TimestampMixin):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='artifact_rules')
    artifact_type = models.CharField(max_length=20)
    destination = models.CharField(max_length=10, choices=DestinationChoices.choices, default=DestinationChoices.ALL)
    is_required = models.BooleanField(default=True)

    class Meta:
        unique_together = ('brand', 'artifact_type', 'destination')

    def __str__(self):
        return f"{self.brand.slug} - {self.artifact_type} ({self.destination})"

class ArchProfile(models.TextChoices):
    LOW = 'LOW', 'Low'
    MED = 'MED', 'Medium'
    HGH = 'HGH', 'High'

class BrandSKU(TimestampMixin):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='skus')
    product_key = models.CharField(max_length=3)
    arch = models.CharField(max_length=3, choices=ArchProfile.choices)
    size = models.CharField(max_length=10)
    sku_code = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.sku_code

class BrandConfigVersion(TimestampMixin):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='config_versions')
    version = models.CharField(max_length=20) # semver
    default_currency = models.CharField(max_length=3, default='USD')
    default_mode = models.CharField(max_length=20, default='CIF')
    allowed_operation_modes = models.JSONField(default=list)
    dispatch_modes = models.JSONField(default=list)
    has_sap = models.BooleanField(default=False)
    has_production = models.BooleanField(default=True)
    max_order_revisions = models.IntegerField(default=3)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Draft'), ('active', 'Active'), ('superseded', 'Superseded'), ('archived', 'Archived')
    ], default='draft')

    def __str__(self):
        return f"{self.brand.slug} Config {self.version}"

class CatalogVersion(TimestampMixin):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='catalogs')
    version = models.CharField(max_length=20)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, default='draft')

    def __str__(self):
        return f"{self.brand.slug} Catalog {self.version}"
