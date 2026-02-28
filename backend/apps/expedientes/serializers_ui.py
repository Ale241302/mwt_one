import datetime
from decimal import Decimal
from rest_framework import serializers

class UIExpedienteListSerializer(serializers.Serializer):
    id = serializers.UUIDField(source='expediente_id', read_only=True)
    custom_ref = serializers.SerializerMethodField()
    status = serializers.CharField(read_only=True)
    brand_name = serializers.CharField(source='get_brand_display', read_only=True, default='')
    client_name = serializers.CharField(source='client.legal_name', read_only=True, default='')
    
    # Annotated fields
    credit_days_elapsed = serializers.IntegerField(read_only=True, default=0)
    credit_band = serializers.CharField(read_only=True, default='MINT')
    total_cost = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True, default=Decimal('0.00'))
    artifact_count = serializers.IntegerField(read_only=True, default=0)
    last_event_at = serializers.DateTimeField(read_only=True, default=None)
    
    is_blocked = serializers.BooleanField(read_only=True)
    block_reason = serializers.CharField(source='blocked_reason', read_only=True, default='')

    def get_custom_ref(self, obj):
        return f"EXP-{str(obj.expediente_id)[:8]}"


class EventLogSummarySerializer(serializers.Serializer):
    id = serializers.UUIDField(source='event_id')
    event_type = serializers.CharField()
    occurred_at = serializers.DateTimeField()
    emitted_by = serializers.CharField()
    payload = serializers.JSONField()


class ArtifactSummarySerializer(serializers.Serializer):
    id = serializers.UUIDField(source='artifact_id')
    artifact_type = serializers.CharField()
    status = serializers.CharField()
    status_display = serializers.CharField(source='get_status_display')
    created_at = serializers.DateTimeField()
    payload = serializers.JSONField()


class CostLineSummarySerializer(serializers.Serializer):
    id = serializers.UUIDField(source='cost_line_id')
    cost_type = serializers.CharField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField()
    phase = serializers.CharField()
    description = serializers.CharField()
    created_at = serializers.DateTimeField()


class DocumentSummarySerializer(serializers.Serializer):
    # Documents might be mapped from artifacts with file URLs. We define a placeholder for minimal shape
    name = serializers.CharField()
    type = serializers.CharField()
    date = serializers.DateTimeField()
    download_url = serializers.CharField()


class ExpedienteBundleSerializer(serializers.Serializer):
    """
    Complete bundle for Expediente Detail page <200ms
    """
    expediente = serializers.SerializerMethodField()
    events = EventLogSummarySerializer(many=True)
    artifacts = ArtifactSummarySerializer(many=True)
    costs = CostLineSummarySerializer(source='cost_lines', many=True)
    documents = serializers.SerializerMethodField()
    available_actions = serializers.ListField(child=serializers.DictField())

    def get_expediente(self, obj):
        # We can reuse the list serializer for the core fields and append more
        data = UIExpedienteListSerializer(obj).data
        data.update({
            'mode': obj.mode,
            'freight_mode': obj.freight_mode,
            'transport_mode': obj.transport_mode,
            'dispatch_mode': obj.dispatch_mode,
            'payment_status': obj.payment_status,
        })
        return data

    def get_documents(self, obj):
        docs = []
        for art in obj.artifacts.all():
            if art.status == 'COMPLETED' and 'file_url' in art.payload: # Simplified stub
                docs.append({
                    'name': art.payload.get('filename', f"Documento_{art.artifact_type}"),
                    'type': art.artifact_type,
                    'date': art.created_at,
                    'download_url': f"/api/documents/{art.artifact_id}/download/"
                })
        return docs
