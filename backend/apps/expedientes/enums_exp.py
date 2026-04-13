from django.db.models import TextChoices





class LegalEntityRole(TextChoices):
    OWNER          = 'OWNER',          'Owner'
    DISTRIBUTOR    = 'DISTRIBUTOR',    'Distributor'
    SUBDISTRIBUTOR = 'SUBDISTRIBUTOR', 'Sub-distributor'
    THREEPL        = 'THREEPL',        '3PL'
    FACTORY        = 'FACTORY',        'Factory'


class LegalEntityRelationship(TextChoices):
    SELF         = 'SELF',         'Self'
    FRANCHISE    = 'FRANCHISE',    'Franchise'
    DISTRIBUTION = 'DISTRIBUTION', 'Distribution'
    SERVICE      = 'SERVICE',      'Service'


class LegalEntityFrontend(TextChoices):
    MWT_ONE        = 'MWT_ONE',        'MWT.ONE'
    PORTAL_MWT_ONE = 'PORTAL_MWT_ONE', 'Portal MWT.ONE'
    EXTERNAL       = 'EXTERNAL',       'External'


class LegalEntityVisibility(TextChoices):
    FULL    = 'FULL',    'Full'
    PARTNER = 'PARTNER', 'Partner'
    LIMITED = 'LIMITED', 'Limited'


class PricingVisibility(TextChoices):
    INTERNAL = 'INTERNAL', 'Internal'
    CLIENT   = 'CLIENT',   'Client'
    NONE     = 'NONE',     'None'


class LegalEntityStatus(TextChoices):
    ACTIVE     = 'ACTIVE',     'Active'
    ONBOARDING = 'ONBOARDING', 'Onboarding'
    INACTIVE   = 'INACTIVE',   'Inactive'


class ExpedienteStatus(TextChoices):
    REGISTRO    = 'REGISTRO',    'Registro'
    PRODUCCION  = 'PRODUCCION',  'Producci\u00f3n'
    PREPARACION = 'PREPARACION', 'Preparaci\u00f3n'
    DESPACHO    = 'DESPACHO',    'Despacho'
    TRANSITO    = 'TRANSITO',    'Tr\u00e1nsito'
    EN_DESTINO  = 'EN_DESTINO',  'En Destino'
    CERRADO     = 'CERRADO',     'Cerrado'
    CANCELADO   = 'CANCELADO',   'Cancelado'



class BlockedByType(TextChoices):
    CEO    = 'CEO',    'CEO'
    SYSTEM = 'SYSTEM', 'System'


class DispatchMode(TextChoices):
    MWT    = 'MWT',    'MWT'
    CLIENT = 'CLIENT', 'Client'


class PaymentStatus(TextChoices):
    PENDING = 'PENDING', 'Pending'
    PARTIAL = 'PARTIAL', 'Partial'
    PAID    = 'PAID',    'Paid'


class CreditClockStartRule(TextChoices):
    ON_CREATION = 'ON_CREATION', 'On Creation'
    ON_SHIPMENT = 'ON_SHIPMENT', 'On Shipment'


class Brand(TextChoices):
    MARLUVAS = 'MARLUVAS', 'Marluvas'


class AggregateType(TextChoices):
    EXPEDIENTE = 'EXPEDIENTE', 'Expediente'
    TRANSFER   = 'TRANSFER',   'Transfer'
    NODE       = 'NODE',       'Node'
    ARTIFACT   = 'ARTIFACT',   'Artifact'


class RegisteredByType(TextChoices):
    CEO    = 'CEO',    'CEO'
    SYSTEM = 'SYSTEM', 'System'


class CostLineVisibility(TextChoices):
    INTERNAL = 'INTERNAL', 'Internal'
    CLIENT   = 'CLIENT',   'Client'


class LogisticsMode(TextChoices):
    AIR    = 'AIR',    'Air'
    SEA    = 'SEA',    'Sea'
    LAND   = 'LAND',   'Land'
    MULTIMODAL = 'MULTIMODAL', 'Multimodal'


class LogisticsSource(TextChoices):
    MANUAL = 'MANUAL', 'Manual'
    AUTO   = 'AUTO',   'Auto'


class CostCategory(TextChoices):
    LANDED_COST    = 'landed_cost',    'Landed Cost'
    TAX_CREDIT     = 'tax_credit',     'Tax Credit (recuperable)'
    RECOVERABLE    = 'recoverable',    'Recoverable (otro)'
    NON_DEDUCTIBLE = 'non_deductible', 'Non-Deductible'


class CostBehavior(TextChoices):
    FIXED_PER_OPERATION = 'fixed_per_operation', 'Fixed per Operation'
    VARIABLE_PER_UNIT   = 'variable_per_unit',   'Variable per Unit'
    VARIABLE_PER_WEIGHT = 'variable_per_weight', 'Variable per Weight'
    SEMI_VARIABLE       = 'semi_variable',       'Semi-Variable'


class AforoType(TextChoices):
    VERDE    = 'verde',    'Verde (Levante Inmediato)'
    AMARILLO = 'amarillo', 'Amarillo (Revisión Documental)'
    ROJO     = 'rojo',     'Rojo (Revisión Física)'


class ArtifactType(TextChoices):
    PROFORMA = 'ART-02', 'Proforma'
    CERTIFICATE_OF_ORIGIN = 'ART-03', 'Certificado de Origen'
    DUE_EXPORT_BR = 'ART-05', 'DU-E Exportación Brasil'
