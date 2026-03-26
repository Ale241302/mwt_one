from rest_framework import serializers
from apps.liquidations.models import Liquidation, LiquidationLine


class LiquidationLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = LiquidationLine
        fields = "__all__"


class LiquidationListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Liquidation
        fields = [
            "liquidation_id", "period", "brand", "status",
            "total_lines", "total_commission_amount", "created_at"
        ]


class LiquidationDetailSerializer(serializers.ModelSerializer):
    lines = LiquidationLineSerializer(many=True, read_only=True)

    class Meta:
        model = Liquidation
        fields = "__all__"


class CommissionLineInputSerializer(serializers.Serializer):
    client = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    fatura = serializers.CharField()
    base   = serializers.DecimalField(max_digits=15, decimal_places=2)
    rate   = serializers.DecimalField(max_digits=5, decimal_places=2)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)

class PremioInputSerializer(serializers.Serializer):
    label    = serializers.CharField(default="Premio de Vendas", required=False)
    amount   = serializers.DecimalField(max_digits=15, decimal_places=2)
    ptax     = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    ptaxDate = serializers.CharField(required=False, allow_null=True, allow_blank=True)

class UploadLiquidationSerializer(serializers.Serializer):
    file = serializers.FileField(required=False, allow_null=True)
    period = serializers.RegexField(
        r"^\d{4}-\d{2}$",
        error_messages={"invalid": "Format: YYYY-MM"}
    )
    currency = serializers.CharField(default="USD", required=False)
    commissions = CommissionLineInputSerializer(many=True, required=False)
    premio = PremioInputSerializer(required=False, allow_null=True)


class ManualMatchSerializer(serializers.Serializer):
    line_id = serializers.IntegerField()
    proforma_id = serializers.CharField()


class DisputeSerializer(serializers.Serializer):
    observations = serializers.CharField()
