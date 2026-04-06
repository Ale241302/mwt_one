"""
S23-10/11/12 — Serializers DRF para la capa comercial.

Convenciones:
- RebateProgramInternalSerializer: todos los campos (uso interno).
- RebateLedgerInternalSerializer: todos los campos + entries_count annotado.
- RebateProgressPortalSerializer: SOLO los campos permitidos al cliente
  (program_name, period, threshold_type, progress_percentage, threshold_met).
  NUNCA incluir rebate_value, accrued_rebate, ni umbrales absolutos.
- CommissionRuleSerializer: todos los campos (solo CEO).
- BrandArtifactPolicyVersionSerializer: todos los campos (CEO + AGENT).
"""
from decimal import Decimal

from rest_framework import serializers

from apps.commercial.models import (
    BrandArtifactPolicyVersion,
    CommissionRule,
    RebateAccrualEntry,
    RebateAssignment,
    RebateLedger,
    RebateProgram,
    RebateProgramProduct,
)


# ---------------------------------------------------------------------------
# S23-10 — Rebates (uso interno: CEO + AGENT)
# ---------------------------------------------------------------------------

class RebateProgramProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = RebateProgramProduct
        fields = '__all__'


class RebateProgramInternalSerializer(serializers.ModelSerializer):
    """
    S23-10: Serializer completo de RebateProgram para uso interno.
    Incluye los productos del programa como nested read-only.
    """
    product_inclusions = RebateProgramProductSerializer(many=True, read_only=True)

    class Meta:
        model = RebateProgram
        fields = '__all__'


class RebateAccrualEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = RebateAccrualEntry
        fields = '__all__'


class RebateLedgerInternalSerializer(serializers.ModelSerializer):
    """
    S23-10: Serializer completo de RebateLedger para uso interno.
    entries_count se inyecta desde el queryset anotado en la view.
    """
    entries_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = RebateLedger
        fields = '__all__'


class RebateAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RebateAssignment
        fields = '__all__'


# ---------------------------------------------------------------------------
# S23-10 — Portal de clientes (IsClientUser)
# ---------------------------------------------------------------------------

class RebateProgressPortalSerializer(serializers.ModelSerializer):
    """
    S23-10: Vista de progreso de rebate para el portal del cliente.

    CAMPO RESTRINGIDO — SOLO expone:
      program_name, period_start, period_end, threshold_type,
      progress_percentage, threshold_met.

    NUNCA incluir: rebate_value, accrued_amount, qualifying_amount,
    threshold_amount, threshold_units, ni datos de comisiones.
    """
    program_name = serializers.SerializerMethodField()
    period = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = RebateLedger
        fields = [
            'id',
            'program_name',
            'period',
            'threshold_type',
            'progress_percentage',
            'threshold_met',
        ]

    def get_program_name(self, obj) -> str:
        try:
            return obj.rebate_assignment.rebate_program.name
        except Exception:
            return ''

    def get_period(self, obj) -> dict:
        return {
            'start': obj.period_start.isoformat() if obj.period_start else None,
            'end': obj.period_end.isoformat() if obj.period_end else None,
        }

    def get_progress_percentage(self, obj) -> float:
        """
        Calcula el porcentaje de progreso hacia el threshold sin exponer
        los valores absolutos:
        - threshold_type=amount: qualifying_amount / threshold_amount * 100
        - threshold_type=units:  qualifying_units  / threshold_units  * 100
        - threshold_type=none:   siempre 100.0
        Retorna valor entre 0.0 y 100.0 (no supera 100).
        """
        try:
            assignment = obj.rebate_assignment
            program = assignment.rebate_program
            threshold_type = program.threshold_type

            if threshold_type == 'none':
                return 100.0

            if threshold_type == 'amount':
                effective = (
                    assignment.custom_threshold_amount
                    if assignment.custom_threshold_amount is not None
                    else program.threshold_amount
                )
                if not effective or effective == 0:
                    return 0.0
                pct = float(obj.qualifying_amount / effective * 100)
                return min(round(pct, 2), 100.0)

            if threshold_type == 'units':
                effective = (
                    assignment.custom_threshold_units
                    if assignment.custom_threshold_units is not None
                    else program.threshold_units
                )
                if not effective or effective == 0:
                    return 0.0
                pct = float(obj.qualifying_units / effective * 100)
                return min(round(pct, 2), 100.0)

        except Exception:
            pass
        return 0.0


# ---------------------------------------------------------------------------
# S23-11 — Comisiones (solo CEO)
# ---------------------------------------------------------------------------

class CommissionRuleSerializer(serializers.ModelSerializer):
    """
    S23-11: Serializer completo de CommissionRule.
    Solo accesible por CEO — nunca AGENT, nunca CLIENT.
    """
    class Meta:
        model = CommissionRule
        fields = '__all__'


# ---------------------------------------------------------------------------
# S23-12 — ArtifactPolicy (CEO + AGENT)
# ---------------------------------------------------------------------------

class BrandArtifactPolicyVersionSerializer(serializers.ModelSerializer):
    """
    S23-12: Serializer completo de BrandArtifactPolicyVersion.
    Accesible por CEO y agentes internos.
    """
    class Meta:
        model = BrandArtifactPolicyVersion
        fields = '__all__'
