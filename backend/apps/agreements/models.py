import uuid
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

    # S16-04: Pricing Defaults
    standard_cost = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    commission = models.DecimalField(max_digits=12, decimal_places=4, default=0)

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
    reserved_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        db_table = 'agreements_creditexposure'

    @classmethod
    def calculate(cls, brand, subject_type, subject_id):
        policy = CreditPolicy.objects.filter(
            brand=brand, 
            subject_type=subject_type, 
            subject_id=subject_id,
            status='active'
        ).first()
        if not policy:
            return None
        exposure, _ = cls.objects.get_or_create(policy=policy)
        return exposure

    def reserve(self, amount):
        if self.current_exposure + self.reserved_amount + amount > self.policy.max_amount:
            return False, "Exceeds credit limit"
        self.reserved_amount += amount
        self.save()
        return True, "Credit reserved"

    def release(self, amount):
        """S16-03: Releases reserved credit."""
        self.reserved_amount = max(0, self.reserved_amount - amount)
        self.save()
        return True, f"Released {amount}"

    def is_clock_expired(self, expediente):
        """S16-02: Logic to determine if 90-day clock is expired."""
        if not expediente.credit_clock_started_at:
            return False
        from django.utils import timezone
        delta = timezone.now() - expediente.credit_clock_started_at
        return delta.days >= 90

class CreditClockRule(TimestampMixin):
    """S16-01: Rule to determine when the credit clock starts for a brand/mode."""
    brand = models.ForeignKey('brands.Brand', on_delete=models.CASCADE, related_name='credit_clock_rules')
    freight_mode = models.CharField(max_length=20) # e.g. SEA, AIR, LAND
    start_event = models.CharField(max_length=20, choices=[
        ('on_departure', 'On Departure (China)'),
        ('on_arrival', 'On Arrival (Destination)'),
        ('on_invoice', 'On Invoice'),
        ('on_arrival_mwt', 'On Arrival (MWT)')
    ])

    class Meta:
        db_table = 'agreements_creditclockrule'
        unique_together = ('brand', 'freight_mode')

class CreditOverride(TimestampMixin):
    """S16-01B: CEO authorization to bypass credit block per command."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    expediente = models.ForeignKey(
        'expedientes.Expediente', on_delete=models.CASCADE,
        related_name='credit_overrides'
    )
    brand = models.ForeignKey('brands.Brand', on_delete=models.PROTECT, null=True, blank=True)
    command_code = models.CharField(
        max_length=10,
        help_text='Command authorized: C1, C6, C8, C9, C14'
    )
    amount_over_limit = models.DecimalField(
        max_digits=14, decimal_places=2,
        help_text='Amount exceeding credit limit at time of authorization'
    )
    authorized_by = models.ForeignKey(
        'users.MWTUser', on_delete=models.PROTECT,
        help_text='Must be CEO (is_superuser=True)'
    )
    reason = models.TextField(help_text='Minimum 10 characters')
    authorized_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'agreements_creditoverride'
        unique_together = ('expediente', 'command_code')

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
