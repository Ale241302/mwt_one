"""
Sprint 3-4 – UI Serializers
"""
import datetime
from decimal import Decimal
from rest_framework import serializers


class UIExpedienteListSerializer(serializers.Serializer):
    id = serializers.UUIDField(source='expediente_id', read_only=True)

    # Frontend ExpedienteCard expects 'ref', not 'custom_ref'
    ref = serializers.SerializerMethodField()

    status = serializers.CharField(read_only=True)
    brand_name = serializers.CharField(source='get_brand_display', read_only=True, default='')
    brand = serializers.CharField(read_only=True)

    # Frontend ExpedienteCard expects 'client', not 'client_name'
    client = serializers.CharField(source='client.legal_name', read_only=True, default='')

    # Annotated fields
    credit_days_elapsed = serializers.IntegerField(read_only=True, default=0)
    credit_band = serializers.CharField(read_only=True, default='MINT')
    total_cost = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True, default=Decimal('0.00'))

    # Frontend ExpedienteCard expects 'artifacts_total' and 'artifacts_done'
    artifacts_total = serializers.IntegerField(source='artifact_count', read_only=True, default=0)
    artifacts_done = serializers.SerializerMethodField()

    last_event_at = serializers.DateTimeField(read_only=True, default=None)

    is_blocked = serializers.BooleanField(read_only=True)
    block_reason = serializers.CharField(source='blocked_reason', read_only=True, default='')

    # pending_action: derived from available_actions if present, else None
    pending_action = serializers.SerializerMethodField()

    def get_ref(self, obj):
        return f"EXP-{str(obj.expediente_id)[:8]}"

    def get_artifacts_done(self, obj):
        """Count completed artifacts. Uses prefetched queryset when available."""
        try:
            return obj.artifacts.filter(status='completed').count()
        except Exception:
            return 0

    def get_pending_action(self, obj):
        """Return first available action label if any, else None."""
        actions = getattr(obj, '_available_actions', None)
        if actions:
            first = actions[0]
            if isinstance(first, dict):
                return first.get('label') or first.get('command')
            return str(first)
        return None


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


class PaymentLineSummarySerializer(serializers.Serializer):
    payment_line_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField()
    method = serializers.CharField()
    reference = serializers.CharField()
    created_at = serializers.DateTimeField()


class DocumentSummarySerializer(serializers.Serializer):
    name = serializers.CharField()
    type = serializers.CharField()
    date = serializers.DateTimeField()
    download_url = serializers.CharField()


class ExpedienteBundleSerializer(serializers.Serializer):
    """
    Complete bundle for Expediente Detail page <200ms
    Now receives an Expediente model instance directly.
    """
    expediente = serializers.SerializerMethodField()
    events = serializers.SerializerMethodField()
    artifacts = serializers.SerializerMethodField()
    costs = serializers.SerializerMethodField()
    payments = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    available_actions = serializers.SerializerMethodField()
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

    def get_events(self, obj):
        events = getattr(obj, '_events', [])
        return EventLogSummarySerializer(events, many=True).data

    def get_artifacts(self, obj):
        return ArtifactSummarySerializer(obj.artifacts.all(), many=True).data

    def get_costs(self, obj):
        return CostLineSummarySerializer(obj.cost_lines.all(), many=True).data

    def get_payments(self, obj):
        return PaymentLineSummarySerializer(obj.payment_lines.all(), many=True).data

    def get_available_actions(self, obj):
        return getattr(obj, '_available_actions', [])

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
