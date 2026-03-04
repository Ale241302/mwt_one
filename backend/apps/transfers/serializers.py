from rest_framework import serializers
from apps.transfers.models import Transfer, TransferLine, Node


class NodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Node
        fields = ["node_id", "name", "node_type", "location", "status"]


class TransferLineSerializer(serializers.ModelSerializer):
    discrepancy = serializers.ReadOnlyField()
    has_discrepancy = serializers.ReadOnlyField()

    class Meta:
        model = TransferLine
        fields = [
            "id", "sku", "quantity_dispatched", "quantity_received",
            "discrepancy", "has_discrepancy", "condition"
        ]


class TransferListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transfer
        fields = [
            "transfer_id", "status", "legal_context", "ownership_changes",
            "customs_required", "created_at", "from_node", "to_node"
        ]


class TransferDetailSerializer(serializers.ModelSerializer):
    lines = TransferLineSerializer(many=True, read_only=True)
    from_node = NodeSerializer(read_only=True)
    to_node = NodeSerializer(read_only=True)

    class Meta:
        model = Transfer
        fields = "__all__"


class CreateTransferSerializer(serializers.Serializer):
    from_node = serializers.UUIDField()
    to_node = serializers.UUIDField()
    legal_context = serializers.ChoiceField(
        choices=["internal", "nationalization", "reexport", "distribution", "consignment"]
    )
    items = serializers.ListField(child=serializers.DictField())
    source_expediente = serializers.CharField(required=False, allow_null=True)
    pricing_context = serializers.JSONField(required=False, allow_null=True)


class ReceiveTransferSerializer(serializers.Serializer):
    lines = serializers.ListField(child=serializers.DictField())


class ReconcileTransferSerializer(serializers.Serializer):
    exception_reason = serializers.CharField(required=False, allow_blank=True)


class CancelTransferSerializer(serializers.Serializer):
    reason = serializers.CharField()
