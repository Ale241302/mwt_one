from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from apps.core.models import TimestampMixin


# -------------------------------------------------------------------
# Modelos existentes (S14) - NO MODIFICAR
# -------------------------------------------------------------------

from apps.core.models import TimestampMixin, UUIDReferenceField

class PriceList(TimestampMixin):
    brand_id = UUIDReferenceField(target_module='brands', db_index=True)
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


# -------------------------------------------------------------------
# S22-01: PriceListVersion + PriceListGradeItem
# -------------------------------------------------------------------

class DeactivationReason(models.TextChoices):
    MANUAL = 'manual', _('Manual')
    PRICE_DECREASE = 'price_decrease', _('Price Decrease')
    SUPERSEDED = 'superseded', _('Superseded')


class PriceListVersion(TimestampMixin):
    """
    Versión de pricelist por brand. N versiones pueden estar activas
    simultáneamente (norma S22 Sección 2.1).
    """
    brand_id = UUIDReferenceField(
        target_module='brands',
        db_index=True,
    )
    version_label = models.CharField(max_length=100)
    # NO file_url - usar storage_key
    storage_key = models.CharField(max_length=500, blank=True, default='')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='uploaded_pricelists',
    )
    is_active = models.BooleanField(default=False)
    activated_at = models.DateTimeField(null=True, blank=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    deactivation_reason = models.CharField(
        max_length=20,
        choices=DeactivationReason.choices,
        null=True, blank=True,
    )
    notes = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'pricing_pricelistversion'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.brand_id} v {self.version_label} ({'active' if self.is_active else 'inactive'})"


class PriceListGradeItem(TimestampMixin):
    """
    Item de pricelist con estructura real Marluvas:
    precio + Grade (rango de tallas) + size_multipliers JSON.
    """
    pricelist_version = models.ForeignKey(
        PriceListVersion,
        on_delete=models.CASCADE,
        related_name='grade_items',
    )
    reference_code = models.CharField(max_length=100)
    brand_sku = models.ForeignKey(
        'brands.BrandSKU',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='pricelist_grade_items',
    )
    # Metadata Marluvas
    tip_type = models.CharField(max_length=50, blank=True, default='')
    insole_type = models.CharField(max_length=50, blank=True, default='')
    ncm = models.CharField(max_length=20, blank=True, default='')
    ca_number = models.CharField(max_length=50, blank=True, default='')
    factory_code = models.CharField(max_length=50, blank=True, default='')
    factory_center = models.CharField(max_length=50, blank=True, default='')
    # Precio y Grade
    unit_price_usd = models.DecimalField(max_digits=12, decimal_places=4)
    grade_label = models.CharField(max_length=50, blank=True, default='')
    # Dict talla → multiplicador MOQ (ej. {33: 1, 41:  2, ...})
    size_multipliers = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'pricing_pricelistgradeitem'
        unique_together = ('pricelist_version', 'reference_code')

    def __str__(self):
        return f"{self.reference_code} ({self.grade_label})"

    @property
    def moq_total(self):
        """Suma de todos los multiplicadores del grade."""
        if not self.size_multipliers:
            return 0
        return sum(self.size_multipliers.values())

    @property
    def available_sizes(self):
        """Lista de tallas disponibles en el grade."""
        if not self.size_multipliers:
            return []
        return list(self.size_multipliers.keys())


# -------------------------------------------------------------------
# S22-02: ClientProductAssignment (CPA)
# -------------------------------------------------------------------

class ClientProductAssignment(TimestampMixin):
    """
    Asignación permanente de un producto a un cliente con precio cacheado.
    Paso 0 del waterfall de resolución de precio.
    Sin valid_from/valid_to en MVP - solo is_active toggle.
    """
    client_subsidiary = models.ForeignKey(
        'clientes.ClientSubsidiary',
        on_delete=models.CASCADE,
        related_name='product_assignments',
    )
    brand_sku = models.ForeignKey(
        'brands.BrandSKU',
        on_delete=models.PROTECT,
        related_name='client_assignments',
    )
    cached_client_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    cached_base_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    cached_pricelist_version = models.ForeignKey(
        PriceListVersion,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='assignments_cached',
    )
    cached_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._old_price = self.cached_client_price

    class Meta:
        db_table = 'pricing_clientproductassignment'
        unique_together = ('client_subsidiary', 'brand_sku')

    def __str__(self):
        return f"CPA {self.client_subsidiary_id} - {self.brand_sku_id}"


# -------------------------------------------------------------------
# S22-03: EarlyPaymentPolicy + EarlyPaymentTier
# -------------------------------------------------------------------

class EarlyPaymentPolicy(TimestampMixin):
    """
    Política de descuento por pronto pago por cliente x brand.
    Mutable por excepción explícita a S14-C5.
    Cambios se registran en ConfigChangeLog vía signal post_save.
    """
    client_subsidiary = models.ForeignKey(
        'clientes.ClientSubsidiary',
        on_delete=models.CASCADE,
        related_name='early_payment_policies_client',
    )
    brand_id = UUIDReferenceField(
        target_module='brands',
        db_index=True,
    )
    base_payment_days = models.PositiveIntegerField(default=90)
    base_commission_pct = models.DecimalField(max_digits=5, decimal_places=2, default='10.00')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'pricing_earlypaymentpolicy'
        unique_together = ('client_subsidiary', 'brand_id')

    def __str__(self):
        return f"EarlyPaymentPolicy {self.client_subsidiary_id} - {self.brand_id}"


class EarlyPaymentTier(TimestampMixin):
    """
    Tramos de descuento por pronto pago.
    Ejemplo: 60d → -1%, 30d → -1.75%, 8d → -2.75%
    """
    policy = models.ForeignKey(
        EarlyPaymentPolicy,
        on_delete=models.CASCADE,
        related_name='tiers',
    )
    payment_days = models.PositiveIntegerField(help_text='Pago en X días o menos')
    discount_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text='Valor positivo - se aplica como descuento. Ej. 1.75 = -1.75%',
    )

    class Meta:
        db_table = 'pricing_earlypaymenttier'
        unique_together = ('policy', 'payment_days')
        ordering = ['-payment_days']

    def __str__(self):
        return f"{self.payment_days}d → -{self.discount_pct}%"