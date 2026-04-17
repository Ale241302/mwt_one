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
