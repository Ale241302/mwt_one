from django.db import models
from django.core.exceptions import ValidationError


class TimestampMixin(models.Model):
    """Mixin that adds created_at and updated_at fields to any model."""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AppendOnlyModel(TimestampMixin):
    """
    Base model for ledger-like records (CostLine, PaymentLine).
    Prevents updates and deletes to maintain immutable audit trail.
    """

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError(
                f"{self.__class__.__name__} records are append-only and cannot be updated."
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(
            f"{self.__class__.__name__} records are append-only and cannot be deleted."
        )


class LegalEntityRole(models.TextChoices):
    OWNER          = 'OWNER',          'Owner'
    DISTRIBUTOR    = 'DISTRIBUTOR',    'Distributor'
    SUBDISTRIBUTOR = 'SUBDISTRIBUTOR', 'Sub-distributor'
    THREEPL        = 'THREEPL',        '3PL'
    FACTORY        = 'FACTORY',        'Factory'


class LegalEntityRelationship(models.TextChoices):
    SELF         = 'SELF',         'Self'
    FRANCHISE    = 'FRANCHISE',    'Franchise'
    DISTRIBUTION = 'DISTRIBUTION', 'Distribution'
    SERVICE      = 'SERVICE',      'Service'


class LegalEntityFrontend(models.TextChoices):
    MWT_ONE        = 'MWT_ONE',        'MWT.ONE'
    PORTAL_MWT_ONE = 'PORTAL_MWT_ONE', 'Portal MWT.ONE'
    EXTERNAL       = 'EXTERNAL',       'External'


class LegalEntityVisibility(models.TextChoices):
    FULL    = 'FULL',    'Full'
    PARTNER = 'PARTNER', 'Partner'
    LIMITED = 'LIMITED', 'Limited'


class PricingVisibility(models.TextChoices):
    INTERNAL = 'INTERNAL', 'Internal'
    CLIENT   = 'CLIENT',   'Client'
    NONE     = 'NONE',     'None'


class LegalEntityStatus(models.TextChoices):
    ACTIVE     = 'ACTIVE',     'Active'
    ONBOARDING = 'ONBOARDING', 'Onboarding'
    INACTIVE   = 'INACTIVE',   'Inactive'


class LegalEntity(TimestampMixin):
    entity_id           = models.CharField(max_length=50, unique=True, help_text='e.g. MWT-CR, SONDEL-CR')
    legal_name          = models.CharField(max_length=255)
    country             = models.CharField(max_length=3, help_text='ISO 3166-1 alpha-2/3')
    tax_id              = models.CharField(max_length=50, blank=True, null=True)
    role                = models.CharField(max_length=20, choices=LegalEntityRole.choices)
    relationship_to_mwt = models.CharField(max_length=20, choices=LegalEntityRelationship.choices)
    frontend            = models.CharField(max_length=20, choices=LegalEntityFrontend.choices)
    visibility_level    = models.CharField(max_length=20, choices=LegalEntityVisibility.choices)
    pricing_visibility  = models.CharField(max_length=20, choices=PricingVisibility.choices)
    status              = models.CharField(max_length=20, choices=LegalEntityStatus.choices, default=LegalEntityStatus.ONBOARDING)

    class Meta:
        verbose_name = 'Legal Entity'
        verbose_name_plural = 'Legal Entities'
        ordering = ['legal_name']

    def __str__(self):
        return f'{self.entity_id} \u2013 {self.legal_name}'
