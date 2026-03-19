from django.db import models


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


class ExpedienteStatus(models.TextChoices):
    REGISTRO    = 'REGISTRO',    'Registro'
    PRODUCCION  = 'PRODUCCION',  'Producci\u00f3n'
    PREPARACION = 'PREPARACION', 'Preparaci\u00f3n'
    DESPACHO    = 'DESPACHO',    'Despacho'
    TRANSITO    = 'TRANSITO',    'Tr\u00e1nsito'
    EN_DESTINO  = 'EN_DESTINO',  'En Destino'
    CERRADO     = 'CERRADO',     'Cerrado'
    CANCELADO   = 'CANCELADO',   'Cancelado'



class BlockedByType(models.TextChoices):
    CEO    = 'CEO',    'CEO'
    SYSTEM = 'SYSTEM', 'System'


class DispatchMode(models.TextChoices):
    MWT    = 'MWT',    'MWT'
    CLIENT = 'CLIENT', 'Client'


class PaymentStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    PARTIAL = 'PARTIAL', 'Partial'
    PAID    = 'PAID',    'Paid'


class CreditClockStartRule(models.TextChoices):
    ON_CREATION = 'ON_CREATION', 'On Creation'
    ON_SHIPMENT = 'ON_SHIPMENT', 'On Shipment'


class Brand(models.TextChoices):
    MARLUVAS = 'MARLUVAS', 'Marluvas'


class ArtifactStatus(models.TextChoices):
    DRAFT      = 'DRAFT',      'Draft'
    COMPLETED  = 'COMPLETED',  'Completed'
    SUPERSEDED = 'SUPERSEDED', 'Superseded'
    VOID       = 'VOID',       'Void'


class AggregateType(models.TextChoices):
    EXPEDIENTE = 'EXPEDIENTE', 'Expediente'
    TRANSFER   = 'TRANSFER',   'Transfer'
    NODE       = 'NODE',       'Node'
    ARTIFACT   = 'ARTIFACT',   'Artifact'


class RegisteredByType(models.TextChoices):
    CEO    = 'CEO',    'CEO'
    SYSTEM = 'SYSTEM', 'System'


class CostLineVisibility(models.TextChoices):
    INTERNAL = 'INTERNAL', 'Internal'
    CLIENT   = 'CLIENT',   'Client'


class LogisticsMode(models.TextChoices):
    AIR    = 'AIR',    'Air'
    SEA    = 'SEA',    'Sea'
    LAND   = 'LAND',   'Land'
    MULTIMODAL = 'MULTIMODAL', 'Multimodal'


class LogisticsSource(models.TextChoices):
    MANUAL = 'MANUAL', 'Manual'
    AUTO   = 'AUTO',   'Auto'


class CostCategory(models.TextChoices):
    LANDED_COST    = 'LANDED_COST',    'Landed Cost'
    TAX_CREDIT     = 'TAX_CREDIT',     'Tax Credit (IVA)'
    RECOVERABLE    = 'RECOVERABLE',    'Recoverable'
    NON_DEDUCTIBLE = 'NON_DEDUCTIBLE', 'Non-Deductible'


class CostBehavior(models.TextChoices):
    FIXED_PER_OPERATION = 'FIXED_PER_OPERATION', 'Fixed per Operation'
    VARIABLE_PER_UNIT   = 'VARIABLE_PER_UNIT',   'Variable per Unit'
    VARIABLE_PER_WEIGHT = 'VARIABLE_PER_WEIGHT', 'Variable per Weight'
    SEMI_VARIABLE       = 'SEMI_VARIABLE',       'Semi-variable'


class AforoType(models.TextChoices):
    VERDE    = 'VERDE',    'Verde (Levante Inmediato)'
    AMARILLO = 'AMARILLO', 'Amarillo (Revisi\u00f3n Documental)'
    ROJO     = 'ROJO',     'Rojo (Revisi\u00f3n F\u00edsica)'
