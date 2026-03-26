from django.db import models


class LiquidationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    IN_REVIEW = "in_review", "In Review"
    RECONCILED = "reconciled", "Reconciled"
    DISPUTED = "disputed", "Disputed"


class LiquidationLineConcept(models.TextChoices):
    COMISION = "comision", "Comisión"
    PREMIO = "premio", "Premio"
    AJUSTE = "ajuste", "Ajuste"
    OTRO = "otro", "Otro"


class MatchStatus(models.TextChoices):
    MATCHED = "matched", "Matched"
    DISCREPANCY = "discrepancy", "Discrepancy"
    UNMATCHED = "unmatched", "Unmatched"
    NO_MATCH_NEEDED = "no_match_needed", "No Match Needed"
