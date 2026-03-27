from django.db import models
from apps.core.models import TimestampMixin

class PriceList(TimestampMixin):
    brand = models.ForeignKey('brands.Brand', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    currency = models.CharField(max_length=3, default='USD')
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_to = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'pricing_pricelist'

class PriceListItem(TimestampMixin):
    price_list = models.ForeignKey(PriceList, related_name='items', on_delete=models.CASCADE)
    sku = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=12, decimal_places=4)
    moq_per_size = models.PositiveIntegerField(null=True, blank=True, help_text='MOQ por talla individual (Agent-A H4)')

    class Meta:
        db_table = 'pricing_pricelistitem'
        unique_together = ('price_list', 'sku')
