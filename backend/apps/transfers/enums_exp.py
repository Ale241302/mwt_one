from django.db import models


class NodeType(models.TextChoices):
    FISCAL = "fiscal", "Fiscal"
    OWNED_WAREHOUSE = "owned_warehouse", "Owned Warehouse"
    FBA = "fba", "FBA"
    THIRD_PARTY = "third_party", "Third Party"
    FACTORY = "factory", "Factory"


class NodeStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"


class LegalContext(models.TextChoices):
    INTERNAL = "internal", "Internal"
    NATIONALIZATION = "nationalization", "Nationalization"
    REEXPORT = "reexport", "Reexport"
    DISTRIBUTION = "distribution", "Distribution"
    CONSIGNMENT = "consignment", "Consignment"


class TransferStatus(models.TextChoices):
    PLANNED = "planned", "Planned"
    APPROVED = "approved", "Approved"
    IN_TRANSIT = "in_transit", "In Transit"
    RECEIVED = "received", "Received"
    RECONCILED = "reconciled", "Reconciled"
    CANCELLED = "cancelled", "Cancelled"


class TransferLineCondition(models.TextChoices):
    GOOD = "good", "Good"
    DAMAGED = "damaged", "Damaged"
    PARTIAL = "partial", "Partial"
