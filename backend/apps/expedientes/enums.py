from django.db import models


# --- LegalEntity enums ---

class LegalEntityRole(models.TextChoices):
    OWNER = 'OWNER', 'Owner'
    DISTRIBUTOR = 'DISTRIBUTOR', 'Distributor'
    SUBDISTRIBUTOR = 'SUBDISTRIBUTOR', 'Sub-distributor'
    THREEPL = 'THREEPL', '3PL'
    FACTORY = 'FACTORY', 'Factory'


class LegalEntityRelationship(models.TextChoices):
    SELF = 'SELF', 'Self'
    FRANCHISE = 'FRANCHISE', 'Franchise'
    DISTRIBUTION = 'DISTRIBUTION', 'Distribution'
    SERVICE = 'SERVICE', 'Service'


class LegalEntityFrontend(models.TextChoices):
    MWT_ONE = 'MWT_ONE', 'MWT.ONE'
    PORTAL_MWT_ONE = 'PORTAL_MWT_ONE', 'Portal MWT.ONE'
    EXTERNAL = 'EXTERNAL', 'External'


class LegalEntityVisibility(models.TextChoices):
    FULL = 'FULL', 'Full'
    PARTNER = 'PARTNER', 'Partner'
    LIMITED = 'LIMITED', 'Limited'


class PricingVisibility(models.TextChoices):
    INTERNAL = 'INTERNAL', 'Internal'
    CLIENT = 'CLIENT', 'Client'
    NONE = 'NONE', 'None'


class LegalEntityStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Active'
    ONBOARDING = 'ONBOARDING', 'Onboarding'
    INACTIVE = 'INACTIVE', 'Inactive'


# --- Expediente enums ---

class ExpedienteStatus(models.TextChoices):
    REGISTRO = 'REGISTRO', 'Registro'
    PRODUCCION = 'PRODUCCION', 'Producción'
    PREPARACION = 'PREPARACION', 'Preparación'
    DESPACHO = 'DESPACHO', 'Despacho'
    TRANSITO = 'TRANSITO', 'Tránsito'
    EN_DESTINO = 'EN_DESTINO', 'En Destino'
    CERRADO = 'CERRADO', 'Cerrado'
    CANCELADO = 'CANCELADO', 'Cancelado'


class BlockedByType(models.TextChoices):
    CEO = 'CEO', 'CEO'
    SYSTEM = 'SYSTEM', 'System'


class DispatchMode(models.TextChoices):
    MWT = 'MWT', 'MWT'
    CLIENT = 'CLIENT', 'Client'


class PaymentStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    PARTIAL = 'PARTIAL', 'Partial'
    PAID = 'PAID', 'Paid'


class CreditClockStartRule(models.TextChoices):
    ON_CREATION = 'ON_CREATION', 'On Creation'
    ON_SHIPMENT = 'ON_SHIPMENT', 'On Shipment'


class Brand(models.TextChoices):
    MARLUVAS = 'MARLUVAS', 'Marluvas'


# --- ArtifactInstance enums ---

class ArtifactStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    COMPLETED = 'COMPLETED', 'Completed'
    SUPERSEDED = 'SUPERSEDED', 'Superseded'
    VOID = 'VOID', 'Void'


# --- EventLog enums ---

class AggregateType(models.TextChoices):
    EXPEDIENTE = 'EXPEDIENTE', 'Expediente'
    TRANSFER = 'TRANSFER', 'Transfer'
    NODE = 'NODE', 'Node'
    ARTIFACT = 'ARTIFACT', 'Artifact'


# --- PaymentLine enums ---

class RegisteredByType(models.TextChoices):
    CEO = 'CEO', 'CEO'
    SYSTEM = 'SYSTEM', 'System'
