import uuid
from django.db import models
from apps.core.models import BaseModel, UUIDReferenceField

class RebateProgram(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    brand_id = UUIDReferenceField(target_module='brands', db_index=True)
    name = models.CharField(max_length=255)
    period_type = models.CharField(max_length=20, choices=[
        ('quarterly', 'Quarterly'), ('annual', 'Annual')
    ])
    valid_from = models.DateField()
    valid_to = models.DateField(null=True, blank=True)
    rebate_type = models.CharField(max_length=20, choices=[
        ('percentage', 'Percentage'), ('fixed_amount', 'Fixed Amount')
    ])
    rebate_value = models.DecimalField(max_digits=10, decimal_places=4)
    calculation_base = models.CharField(max_length=20, null=True, blank=True,
        choices=[('invoiced', 'Invoiced'), ('list_price', 'List Price')])  # DEC-S23-01
    threshold_type = models.CharField(max_length=20, choices=[
        ('amount', 'Amount'), ('units', 'Units'), ('none', 'None')
    ])
    threshold_value = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(valid_to__isnull=True) | models.Q(valid_to__gte=models.F('valid_from')),
                name='rebate_valid_to_gte_valid_from'
            ),
            models.CheckConstraint(
                check=~models.Q(threshold_type__in=['amount', 'units']) | models.Q(threshold_value__isnull=False),
                name='rebate_threshold_value_required'
            ),
            models.CheckConstraint(
                check=~models.Q(threshold_type='none') | models.Q(threshold_value__isnull=True),
                name='rebate_threshold_value_null_when_none'
            ),
            models.CheckConstraint(
                check=models.Q(rebate_value__gt=0),
                name='rebate_value_positive'
            ),
            models.CheckConstraint(
                check=~models.Q(rebate_type='percentage') | models.Q(rebate_value__lte=100),
                name='rebate_percentage_max_100'
            ),
            models.CheckConstraint(
                check=~models.Q(rebate_type='fixed_amount') | models.Q(calculation_base__isnull=True),
                name='rebate_fixed_no_calc_base'
            ),
        ]

class RebateProgramProduct(BaseModel):
    rebate_program = models.ForeignKey(RebateProgram, on_delete=models.CASCADE, related_name='products')
    product_key = models.CharField(max_length=100)

    class Meta:
        unique_together = [['rebate_program', 'product_key']]

class RebateAssignment(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rebate_program = models.ForeignKey(RebateProgram, on_delete=models.PROTECT)
    client_id = UUIDReferenceField(target_module='clientes', null=True, blank=True)
    subsidiary_id = UUIDReferenceField(target_module='clientes', null=True, blank=True)
    custom_threshold_value = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(client_id__isnull=False, subsidiary_id__isnull=True) |
                    models.Q(client_id__isnull=True, subsidiary_id__isnull=False)
                ),
                name='rebate_assignment_one_level_only'
            ),
            models.UniqueConstraint(
                fields=['rebate_program', 'client_id'],
                condition=models.Q(is_active=True, client_id__isnull=False),
                name='rebate_assignment_unique_active_client'
            ),
            models.UniqueConstraint(
                fields=['rebate_program', 'subsidiary_id'],
                condition=models.Q(is_active=True, subsidiary_id__isnull=False),
                name='rebate_assignment_unique_active_subsidiary'
            )
        ]

class RebateLedger(BaseModel):
    STATUS_CHOICES = [
        ('accruing', 'Accruing'),
        ('pending_review', 'Pending Review'),
        ('liquidated', 'Liquidated'),
        ('cancelled', 'Cancelled'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rebate_assignment = models.ForeignKey(RebateAssignment, on_delete=models.PROTECT)
    period_start = models.DateField()
    period_end = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='accruing')
    accrued_rebate = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    liquidation_type = models.CharField(max_length=30, null=True, blank=True)  # DEC-S23-02
    liquidated_at = models.DateTimeField(null=True, blank=True)
    liquidated_by = models.ForeignKey('users.MWTUser', null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        unique_together = [['rebate_assignment', 'period_start', 'period_end']]

class RebateAccrualEntry(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ledger = models.ForeignKey(
        RebateLedger,
        on_delete=models.PROTECT,
        related_name='entries'
    )
    factory_order_id = UUIDReferenceField(
        target_module='expedientes',
        null=True, blank=True,
        help_text='ID de la Factory Order legada o relacionada'
    )
    qualifying_amount = models.DecimalField(max_digits=14, decimal_places=4)
    qualifying_units = models.DecimalField(max_digits=14, decimal_places=4)
    rebate_amount = models.DecimalField(max_digits=14, decimal_places=4)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['ledger', 'factory_order_id']]

class CommissionRule(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    brand_id = UUIDReferenceField(target_module='brands', null=True, blank=True, db_index=True)
    client_id = UUIDReferenceField(target_module='clientes', null=True, blank=True)
    subsidiary_id = UUIDReferenceField(target_module='clientes', null=True, blank=True)
    product_key = models.CharField(max_length=100, null=True, blank=True)
    commission_type = models.CharField(max_length=20, choices=[
        ('percentage', 'Percentage'), ('fixed_amount', 'Fixed Amount')
    ])
    commission_value = models.DecimalField(max_digits=10, decimal_places=4)
    commission_base = models.CharField(max_length=20, null=True, blank=True,
        choices=[('sale_price', 'Sale Price'), ('gross_margin', 'Gross Margin')])  # DEC-S23-03
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    (models.Q(brand_id__isnull=False) & models.Q(client_id__isnull=True) & models.Q(subsidiary_id__isnull=True)) |
                    (models.Q(brand_id__isnull=True) & models.Q(client_id__isnull=False) & models.Q(subsidiary_id__isnull=True)) |
                    (models.Q(brand_id__isnull=True) & models.Q(client_id__isnull=True) & models.Q(subsidiary_id__isnull=False))
                ),
                name='commission_one_level_only'
            ),
            models.UniqueConstraint(
                fields=['brand_id'],
                condition=models.Q(is_active=True, product_key__isnull=True, client_id__isnull=True, subsidiary_id__isnull=True),
                name='unique_active_brand_default_commission'
            ),
            models.UniqueConstraint(
                fields=['brand_id', 'product_key'],
                condition=models.Q(is_active=True, client_id__isnull=True, subsidiary_id__isnull=True, product_key__isnull=False),
                name='unique_active_brand_product_commission'
            ),
            models.UniqueConstraint(
                fields=['client_id'],
                condition=models.Q(is_active=True, product_key__isnull=True, brand_id__isnull=True, subsidiary_id__isnull=True),
                name='unique_active_client_default_commission'
            ),
            models.UniqueConstraint(
                fields=['client_id', 'product_key'],
                condition=models.Q(is_active=True, brand_id__isnull=True, subsidiary_id__isnull=True, product_key__isnull=False),
                name='unique_active_client_product_commission'
            ),
            models.UniqueConstraint(
                fields=['subsidiary_id'],
                condition=models.Q(is_active=True, product_key__isnull=True, brand_id__isnull=True, client_id__isnull=True),
                name='unique_active_subsidiary_default_commission'
            ),
            models.UniqueConstraint(
                fields=['subsidiary_id', 'product_key'],
                condition=models.Q(is_active=True, brand_id__isnull=True, client_id__isnull=True, product_key__isnull=False),
                name='unique_active_subsidiary_product_commission'
            ),
        ]

class BrandArtifactPolicyVersion(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    brand_id = UUIDReferenceField(target_module='brands', db_index=True)
    version = models.PositiveIntegerField()
    artifact_policy = models.JSONField()
    is_active = models.BooleanField(default=True)
    superseded_by = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL, related_name='supersedes'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('users.MWTUser', null=True, on_delete=models.SET_NULL)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['brand_id'],
                condition=models.Q(is_active=True),
                name='brand_artifact_policy_one_active_per_brand'
            ),
            models.UniqueConstraint(
                fields=['brand_id', 'version'],
                name='brand_artifact_policy_unique_version'
            ),
        ]
