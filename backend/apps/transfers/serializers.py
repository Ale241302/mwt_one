from rest_framework import serializers
from apps.transfers.models import Transfer, TransferLine
from apps.nodos.models import Node
from apps.core.models import LegalEntity


class NodeSerializer(serializers.ModelSerializer):
    legal_entity_name = serializers.CharField(source='legal_entity.legal_name', read_only=True)
    legal_entity_id = serializers.CharField(source='legal_entity.entity_id', read_only=True)

    class Meta:
        model = Node
        fields = ["node_id", "name", "node_type", "location", "status", "legal_entity_name", "legal_entity_id"]


class NodeCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    node_type = serializers.ChoiceField(choices=[
        "fiscal", "owned_warehouse", "fba", "third_party", "factory"
    ])
    location = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")
    status = serializers.ChoiceField(
        choices=["active", "inactive"], required=False, default="active"
    )
    legal_entity = serializers.CharField(
        help_text="entity_id of LegalEntity (e.g. MWT-CR)",
        required=False, allow_blank=True, default=""
    )


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


class CreatePreparationArtifactSerializer(serializers.Serializer):
    payload = serializers.DictField(required=False, default=dict)


class CreateDispatchArtifactSerializer(serializers.Serializer):
    payload = serializers.DictField(required=False, default=dict)


class CreateReceptionArtifactSerializer(serializers.Serializer):
    lines = serializers.ListField(child=serializers.DictField())
    payload = serializers.DictField(required=False, default=dict)


class CreatePricingApprovalArtifactSerializer(serializers.Serializer):
    payload = serializers.DictField(required=False, default=dict)
