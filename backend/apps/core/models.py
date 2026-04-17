from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid


class TimestampMixin(models.Model):
    """Mixin that adds created_at and updated_at fields to any model."""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def resolve_ref(self, field_name):
        """Helper para resolver una referencia UUID a su objeto real."""
        field = self._meta.get_field(field_name)
        if isinstance(field, UUIDReferenceField):
            val = getattr(self, field_name)
            return field.resolve(val)
        return None


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


class BaseModel(models.Model):
    """Modelo base para TODOS los módulos del sistema distribuido."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        abstract = True
    
    def soft_delete(self):
        """Borrado lógico de la entidad."""
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_active', 'deleted_at'])



class UUIDReferenceField(models.UUIDField):
    """Campo que almacena UUID de otra entidad SIN ForeignKey."""
    def __init__(self, target_module=None, target_model=None, *args, **kwargs):
        self.target_module = target_module
        self.target_model = target_model
        kwargs['editable'] = kwargs.get('editable', True)
        kwargs['null'] = kwargs.get('null', True)
        kwargs['blank'] = kwargs.get('blank', True)
        super().__init__(*args, **kwargs)

    def resolve(self, value):
        """Resuelve el valor UUID usando el ModuleRegistry."""
        if not value or not self.target_module:
            return None
        
        from apps.core.registry import ModuleRegistry
        service_class = ModuleRegistry.get_service_class(self.target_module)
        if service_class and hasattr(service_class, 'get_entity'):
            return service_class.get_entity(value)
        return None
