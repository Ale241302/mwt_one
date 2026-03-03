"""
Sprint 3-4 — UI Serializers
"""
import datetime
from decimal import Decimal
from rest_framework import serializers


class UIExpedienteListSerializer(serializers.Serializer):
    id = serializers.UUIDField(source='expediente_id', read_only=True)
    custom_ref = serializers.SerializerMethodField()
    status = serializers.CharField(read_only=True)
    brand_name = serializers.CharField(source='get_brand_display', read_only=True, default='')
    brand = serializers.CharField(read_only=True)
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
    visibility = serializers.CharField()   # Sprint 4 S4-02
    created_at = serializers.DateTimeField()


class LogisticsOptionSerializer(serializers.Serializer):
    """Sprint 4 S4-07"""
    id = serializers.UUIDField(source='logistics_option_id')
    option_id = serializers.CharField()
    mode = serializers.CharField()
    carrier = serializers.CharField()
    route = serializers.CharField()
    estimated_days = serializers.IntegerField()
    estimated_cost = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField()
    valid_until = serializers.DateField(allow_null=True)
    source = serializers.CharField()
    is_selected = serializers.BooleanField()


class DocumentSummarySerializer(serializers.Serializer):
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
    available_actions = serializers.JSONField()
    credit_clock = serializers.SerializerMethodField()

    def get_expediente(self, obj):
        data = UIExpedienteListSerializer(obj).data
        data.update({
            'mode': obj.mode,
            'freight_mode': obj.freight_mode,
            'transport_mode': obj.transport_mode,
            'dispatch_mode': obj.dispatch_mode,
            'payment_status': obj.payment_status,
            'price_basis': obj.price_basis,
            'legal_entity_id': str(obj.legal_entity_id),
            'client_id': str(obj.client_id) if obj.client_id else None,
        })
        return data

    def get_credit_clock(self, obj):
        return {
            'days': getattr(obj, 'credit_days_elapsed', 0),
            'band': getattr(obj, 'credit_band', 'MINT'),
            'started_at': obj.credit_clock_started_at,
            'is_ignored': obj.status in ['CERRADO', 'CANCELADO']
        }

    def get_documents(self, obj):
        docs = []
        for art in obj.artifacts.all():
            if art.status == 'completed' and 'file_url' in art.payload:
                docs.append({
                    'id': str(art.artifact_id),
                    'name': art.payload.get('filename', f"Documento_{art.artifact_type}"),
                    'type': art.artifact_type,
                    'date': art.created_at,
                    'download_url': f"/api/documents/{art.artifact_id}/download/"
                })
        return docs
