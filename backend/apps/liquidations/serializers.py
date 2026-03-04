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


class UploadLiquidationSerializer(serializers.Serializer):
    file = serializers.FileField()
    period = serializers.RegexField(
        r"^\d{4}-\d{2}$",
        error_messages={"invalid": "Format: YYYY-MM"}
    )


class ManualMatchSerializer(serializers.Serializer):
    line_id = serializers.IntegerField()
    proforma_id = serializers.CharField()


class DisputeSerializer(serializers.Serializer):
    observations = serializers.CharField()
