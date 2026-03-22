from django.db import models
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import RangeOperators, DateTimeRangeField
from apps.core.models import TimestampMixin

class CommercialFilterMixin(models.Model):
    mode = models.CharField(max_length=20, blank=True, null=True)
    channel = models.CharField(max_length=50, blank=True, null=True)
    currency = models.CharField(max_length=3, blank=True, null=True)
    incoterm = models.CharField(max_length=10, blank=True, null=True)
    class Meta:
        abstract = True

class PartyType(models.TextChoices):
    GROUP = 'group', 'Group'
    SUBSIDIARY = 'subsidiary', 'Subsidiary'

class BrandClientAgreement(TimestampMixin, CommercialFilterMixin):
    brand = models.ForeignKey('brands.Brand', on_delete=models.CASCADE)
    party_type = models.CharField(max_length=20, choices=PartyType.choices)
    party_id = models.IntegerField()  # ID of Group or Subsidiary
    version = models.CharField(max_length=20)
    max_order_revisions = models.IntegerField(null=True, blank=True)
    
    valid_daterange = DateTimeRangeField(null=True, blank=True)
    status = models.CharField(max_length=20, default='draft')

    class Meta:
        db_table = 'agreements_brandclientagreement'
        constraints = [
            ExclusionConstraint(
                name='exclude_overlapping_agreements',
                expressions=[
                    ('brand', '='),
                    ('party_type', '='),
                    ('party_id', '='),
                    ('valid_daterange', RangeOperators.OVERLAPS),
                ],
                condition=models.Q(status='active'),
            )
        ]

class BrandClientPriceAgreement(TimestampMixin):
    brand = models.ForeignKey('brands.Brand', on_delete=models.CASCADE)
    party_type = models.CharField(max_length=20, choices=PartyType.choices)
    party_id = models.IntegerField()
    sku = models.CharField(max_length=50)
    mode = models.CharField(max_length=20)
    currency = models.CharField(max_length=3)
    override_price = models.DecimalField(max_digits=12, decimal_places=4)
    valid_daterange = DateTimeRangeField(null=True, blank=True)
    status = models.CharField(max_length=20, default='draft')

    class Meta:
        db_table = 'agreements_brandclientpriceagreement'
        constraints = [
            ExclusionConstraint(
                name='exclude_overlapping_price_agreements',
                expressions=[
                    ('brand', '='),
                    ('party_type', '='),
                    ('party_id', '='),
                    ('sku', '='),
                    ('mode', '='),
                    ('currency', '='),
                    ('valid_daterange', RangeOperators.OVERLAPS),
                ],
                condition=models.Q(status='active'),
            )
        ]

class BrandSupplierAgreement(TimestampMixin):
    brand = models.ForeignKey('brands.Brand', on_delete=models.CASCADE)
    supplier_id = models.IntegerField()
    version = models.CharField(max_length=20)
    valid_daterange = DateTimeRangeField(null=True, blank=True)
    status = models.CharField(max_length=20, default='draft')
    
    class Meta:
        db_table = 'agreements_brandsupplieragreement'

class AssortmentPolicy(TimestampMixin):
    brand = models.ForeignKey('brands.Brand', on_delete=models.CASCADE)
    party_type = models.CharField(max_length=20, choices=PartyType.choices)
    party_id = models.IntegerField()
    channel = models.CharField(max_length=50)
    include_rules = models.JSONField(default=list)
    exclude_rules = models.JSONField(default=list)
    valid_daterange = DateTimeRangeField(null=True, blank=True)
    status = models.CharField(max_length=20, default='draft')

    class Meta:
        db_table = 'agreements_assortmentpolicy'
        constraints = [
            ExclusionConstraint(
                name='exclude_overlapping_assortment',
                expressions=[
                    ('brand', '='),
                    ('party_type', '='),
                    ('party_id', '='),
                    ('channel', '='),
                    ('valid_daterange', RangeOperators.OVERLAPS),
                ],
                condition=models.Q(status='active'),
            )
        ]

class CreditPolicy(TimestampMixin):
    scope_type = models.CharField(max_length=50)
    subject_type = models.CharField(max_length=50)
    subject_id = models.IntegerField()
    brand = models.ForeignKey('brands.Brand', on_delete=models.CASCADE)
    currency = models.CharField(max_length=3)
    max_amount = models.DecimalField(max_digits=14, decimal_places=2)
    valid_daterange = DateTimeRangeField(null=True, blank=True)
    status = models.CharField(max_length=20, default='draft')

    class Meta:
        db_table = 'agreements_creditpolicy'
        constraints = [
            ExclusionConstraint(
                name='exclude_overlapping_credit',
                expressions=[
                    ('scope_type', '='),
                    ('subject_type', '='),
                    ('subject_id', '='),
                    ('brand', '='),
                    ('currency', '='),
                    ('valid_daterange', RangeOperators.OVERLAPS),
                ],
                condition=models.Q(status='active'),
            )
        ]

class CreditExposure(TimestampMixin):
    policy = models.ForeignKey(CreditPolicy, on_delete=models.CASCADE, related_name='exposures')
    current_exposure = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    
    class Meta:
        db_table = 'agreements_creditexposure'

class PaymentTermPricingVersion(TimestampMixin):
    SCOPE_CHOICES = [('agreement', 'Agreement'), ('brand_default', 'Brand Default')]
    brand = models.ForeignKey('brands.Brand', on_delete=models.CASCADE)
    scope_type = models.CharField(max_length=20, choices=SCOPE_CHOICES)
    agreement = models.ForeignKey(BrandClientAgreement, null=True, blank=True, on_delete=models.CASCADE)
    version = models.CharField(max_length=20)
    valid_daterange = DateTimeRangeField(null=True, blank=True)
    status = models.CharField(max_length=20, default='draft')

    class Meta:
        db_table = 'agreements_paymenttermpricingversion'
        constraints = [
            ExclusionConstraint(
                name='exclude_overlapping_paymentterm',
                expressions=[
                    ('brand', '='),
                    ('scope_type', '='),
                    ('agreement', '='), # This works even with nulls if properly configured, but Postgres handles nulls distinctively.
                    ('valid_daterange', RangeOperators.OVERLAPS),
                ],
                condition=models.Q(status='active'),
            )
        ]

class PaymentTermPricingTerm(models.Model):
    pricing_version = models.ForeignKey(PaymentTermPricingVersion, on_delete=models.CASCADE, related_name='terms')
    payment_days = models.IntegerField()
    price_index = models.DecimalField(max_digits=8, decimal_places=6)
    label = models.CharField(max_length=50)

    class Meta:
        db_table = 'agreements_paymenttermpricingterm'
        unique_together = ('pricing_version', 'payment_days')


class BrandWorkflowPolicy(TimestampMixin):
    brand = models.ForeignKey('brands.Brand', on_delete=models.CASCADE, related_name='workflow_policies')
    valid_daterange = DateTimeRangeField(null=True, blank=True)
    status = models.CharField(max_length=20, default='draft')

    class Meta:
        db_table = 'agreements_brandworkflowpolicy'
        constraints = [
            ExclusionConstraint(
                name='exclude_overlapping_workflow_policy',
                expressions=[
                    ('brand', '='),
                    ('valid_daterange', RangeOperators.OVERLAPS),
                ],
                condition=models.Q(status='active'),
            )
        ]

class StatePolicy(models.Model):
    policy = models.ForeignKey(BrandWorkflowPolicy, on_delete=models.CASCADE, related_name='state_policies')
    state = models.CharField(max_length=50)

    class Meta:
        db_table = 'agreements_statepolicy'
        unique_together = ('policy', 'state')

class CommandPolicy(models.Model):
    policy = models.ForeignKey(BrandWorkflowPolicy, on_delete=models.CASCADE, related_name='command_policies')
    command = models.CharField(max_length=50)

    class Meta:
        db_table = 'agreements_commandpolicy'
        unique_together = ('policy', 'command')

class ArtifactRequirement(models.Model):
    policy = models.ForeignKey(BrandWorkflowPolicy, on_delete=models.CASCADE, related_name='artifact_requirements')
    artifact_type = models.CharField(max_length=50)
    is_required = models.BooleanField(default=True)

    class Meta:
        db_table = 'agreements_artifactrequirement'
        unique_together = ('policy', 'artifact_type')

class TransitionPolicy(models.Model):
    policy = models.ForeignKey(BrandWorkflowPolicy, on_delete=models.CASCADE, related_name='transition_policies')
    from_state = models.CharField(max_length=50)
    to_state = models.CharField(max_length=50)
    command = models.CharField(max_length=50)
    conditions = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'agreements_transitionpolicy'
        unique_together = ('policy', 'from_state', 'to_state', 'command')
