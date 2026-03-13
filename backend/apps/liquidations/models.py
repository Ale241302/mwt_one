"""
Sprint 5 S5-03: ART-10 Liquidation models
Ref: LOTE_SM_SPRINT5 Item 1
"""
from django.conf import settings
from django.db import models
from apps.liquidations.enums import (
    LiquidationStatus, LiquidationLineConcept, MatchStatus
)
from apps.expedientes.models import Expediente, ArtifactInstance


def generate_liquidation_id(period: str):
    """Auto-genera LIQ-YYYY-MM-NNN"""
    count = Liquidation.objects.filter(period=period).count()
    return f"LIQ-{period}-{str(count + 1).zfill(3)}"


class Liquidation(models.Model):
    """
    ART-10 – Artefacto CROSS (transversal). No tiene FK a expediente.
    Relaciona con expedientes INDIRECTAMENTE a través de LiquidationLine.
    """
    liquidation_id = models.CharField(max_length=30, unique=True, editable=False)
    period = models.CharField(max_length=7)  # formato YYYY-MM
    brand = models.CharField(max_length=50, default="marluvas")
    source_file = models.FileField(upload_to="liquidations/uploads/", null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=LiquidationStatus.choices,
        default=LiquidationStatus.PENDING
    )
    error_log = models.TextField(blank=True)
    total_lines = models.PositiveIntegerField(default=0)
    total_commission_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reconciled_at = models.DateTimeField(null=True, blank=True, default=None)
    reconciled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True, default=None,
        related_name="reconciled_liquidations",
    )
    observations = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.liquidation_id:
            self.liquidation_id = generate_liquidation_id(self.period)
        super().save(*args, **kwargs)

    class Meta:
        db_table = "liquidations_liquidation"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.liquidation_id} [{self.status}]"


class LiquidationLine(models.Model):
    """Línea individual del Excel de Marluvas."""
    liquidation = models.ForeignKey(
        Liquidation, on_delete=models.CASCADE, related_name="lines"
    )
    marluvas_reference = models.CharField(max_length=200)
    concept = models.CharField(
        max_length=20, choices=LiquidationLineConcept.choices
    )
    client_payment_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, default=None)
    commission_pct_reported = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True, default=None
    )
    commission_amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    is_partial_payment = models.BooleanField(default=False)
    matched_proforma = models.ForeignKey(
        ArtifactInstance,
        on_delete=models.SET_NULL,
        null=True, blank=True, default=None,
        related_name="liquidation_matches",
        limit_choices_to={"artifact_type": "ART-02"},
    )
    matched_expediente = models.ForeignKey(
        Expediente,
        on_delete=models.SET_NULL,
        null=True, blank=True, default=None,
        related_name="liquidation_matches",
    )
    commission_pct_expected = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True, default=None
    )
    match_status = models.CharField(
        max_length=20, choices=MatchStatus.choices, default=MatchStatus.UNMATCHED
    )
    observation = models.TextField(blank=True)

    class Meta:
        db_table = "liquidations_liquidationline"
