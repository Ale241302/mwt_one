from django.db import models
from apps.core.models import TimestampMixin

class ClientOrder(TimestampMixin):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('revision_requested', 'Revision Requested'),
        ('converted', 'Converted'),
        ('rejected', 'Rejected')
    ]
    
    RESOLUTION_LEVEL_CHOICES = [
        ('subsidiary', 'Subsidiary'),
        ('group', 'Group'),
        ('brand_default', 'Brand Default')
    ]

    client = models.ForeignKey('clientes.Cliente', on_delete=models.CASCADE)
    brand = models.ForeignKey('brands.Brand', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    content_fingerprint = models.CharField(max_length=64, blank=True, null=True)
    
    resolved_agreement = models.ForeignKey('agreements.BrandClientAgreement', null=True, blank=True, on_delete=models.SET_NULL)
    agreement_resolution_level = models.CharField(max_length=20, choices=RESOLUTION_LEVEL_CHOICES, blank=True, null=True)
    
    resolved_max_revisions = models.IntegerField(default=0)
    revision_count = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'orders_clientorder'


class ClientOrderLine(models.Model):
    OVERRIDE_CHOICES = [
        ('none', 'None'),
        ('base_override', 'Base Override'),
        ('final_override_manual', 'Final Override Manual')
    ]

    order = models.ForeignKey(ClientOrder, on_delete=models.CASCADE, related_name='lines')
    sku = models.CharField(max_length=50)
    qty = models.IntegerField()
    
    resolved_price = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    base_price = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    commission_applied = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    price_index_applied = models.DecimalField(max_digits=8, decimal_places=6, default=1)
    
    override_mode = models.CharField(max_length=30, choices=OVERRIDE_CHOICES, default='none')
    is_formula_locked = models.BooleanField(default=False)
    manual_override_reason = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'orders_clientorderline'


class ClientOrderSnapshot(TimestampMixin):
    order = models.OneToOneField(ClientOrder, on_delete=models.CASCADE, related_name='snapshot')
    payload_hash = models.CharField(max_length=64)
    payload_canonical_version = models.IntegerField(default=1)
    ceo_override_diff = models.JSONField(default=dict)

    class Meta:
        db_table = 'orders_clientordersnapshot'
