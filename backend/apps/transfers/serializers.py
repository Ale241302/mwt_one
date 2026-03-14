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
    """
    FIX S9-11: from_node / to_node eran FK -> el serializador anterior intentaba
    serializar el objeto Node como string -> KeyError / 500.
    Ahora se exponen como campos planos seguros con source explicito.
    """
    from_node_id   = serializers.UUIDField(source="from_node_id",    read_only=True)
    to_node_id     = serializers.UUIDField(source="to_node_id",      read_only=True)
    from_node_name = serializers.CharField(source="from_node.name",  read_only=True)
    to_node_name   = serializers.CharField(source="to_node.name",    read_only=True)

    class Meta:
        model = Transfer
        fields = [
            "transfer_id", "status", "legal_context",
            "ownership_changes", "customs_required", "created_at",
            "from_node_id", "from_node_name",
            "to_node_id",   "to_node_name",
        ]


class TransferDetailSerializer(serializers.ModelSerializer):
    lines     = TransferLineSerializer(many=True, read_only=True)
    from_node = NodeSerializer(read_only=True)
    to_node   = NodeSerializer(read_only=True)

    class Meta:
        model = Transfer
        fields = "__all__"


class CreateTransferSerializer(serializers.Serializer):
    from_node         = serializers.UUIDField()
    to_node           = serializers.UUIDField()
    legal_context     = serializers.ChoiceField(
        choices=["internal", "nationalization", "reexport", "distribution", "consignment"]
    )
    items             = serializers.ListField(child=serializers.DictField())
    source_expediente = serializers.CharField(required=False, allow_null=True)
    pricing_context   = serializers.JSONField(required=False, allow_null=True)


class ReceiveTransferSerializer(serializers.Serializer):
    lines = serializers.ListField(child=serializers.DictField())


class ReconcileTransferSerializer(serializers.Serializer):
    exception_reason = serializers.CharField(required=False, allow_blank=True)


class CancelTransferSerializer(serializers.Serializer):
    reason = serializers.CharField()


class CreatePreparationArtifactSerializer(serializers.Serializer):
    payload = serializers.DictField(required=False, default=dict)


class CreateDispatchArtifactSerializer(serializers.Serializer):
    payload = serializers.DictField(required=False, default=dict)


class CreateReceptionArtifactSerializer(serializers.Serializer):
    lines   = serializers.ListField(child=serializers.DictField())
    payload = serializers.DictField(required=False, default=dict)


class CreatePricingApprovalArtifactSerializer(serializers.Serializer):
    payload = serializers.DictField(required=False, default=dict)
