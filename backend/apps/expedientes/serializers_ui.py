"""
Sprint 3-4 — UI Serializers
S20-06: ExpedienteBundleSerializer ahora incluye artifact_policy calculada dinámicamente.
FIX-2026-03-31: get_product_lines envuelto en try/except para no romper el bundle.
"""
import datetime
from decimal import Decimal
from rest_framework import serializers


class UIExpedienteListSerializer(serializers.Serializer):
    id = serializers.UUIDField(source='expediente_id', read_only=True)
    custom_ref = serializers.SerializerMethodField()
    status = serializers.CharField(read_only=True)
    brand_name = serializers.SerializerMethodField()
    brand = serializers.SerializerMethodField()
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

    def get_brand_name(self, obj):
        """FIX: brand es ForeignKey a Brand, no CharField con get_brand_display."""
        try:
            if obj.brand:
                return obj.brand.name
        except Exception:
            pass
        return ''

    def get_brand(self, obj):
        """FIX: retorna el name normalizado del brand FK."""
        try:
            if obj.brand:
                return obj.brand.name
        except Exception:
            pass
        return ''


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
    parent_proforma_id = serializers.UUIDField(allow_null=True, required=False)


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
    Complete bundle for Expediente Detail page <200ms.
    S20-06: agrega artifact_policy calculada dinámicamente por brand + proformas.
    FIX-2026-03-31: get_product_lines protegido con try/except.
    """
    expediente = serializers.SerializerMethodField()
    events = serializers.SerializerMethodField()
    artifacts = serializers.SerializerMethodField()
    costs = serializers.SerializerMethodField()
    payments = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    available_actions = serializers.SerializerMethodField()
    credit_clock = serializers.SerializerMethodField()
    # S20-06: policy de artefactos calculada dinámicamente
    artifact_policy = serializers.SerializerMethodField()
    product_lines = serializers.SerializerMethodField()

    def get_expediente(self, obj):
        """
        S25-08: Unifies with BundleSerializer to include credit snapshot,
        deferred pricing, and genealogy fields in the UI detail bundle.
        """
        from .serializers import BundleSerializer
        # Base with S25 fields
        data = BundleSerializer(obj).data
        
        # Merge UI-specific metadata
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

    def get_product_lines(self, obj):
        """
        FIX-2026-03-31: Protegido con try/except para no romper el bundle
        si ProductLineSerializer falla (import circular u otro error).
        """
        try:
            from apps.expedientes.serializers import ProductLineSerializer
            return ProductLineSerializer(obj.product_lines.all(), many=True).data
        except Exception:
            # Fallback: retorna lista vacía para no romper el bundle
            return []

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

    def get_artifact_policy(self, obj):
        """
        S20-06: Retorna la política de artefactos resuelta dinámicamente.
        - Sin proformas completadas → solo estado REGISTRO
        - Con proformas → policy completa por estado mergeada por mode
        - Siempre JSON-serializable (listas ordenadas, nunca sets)
        """
        from apps.expedientes.services.artifact_policy import resolve_artifact_policy
        try:
            return resolve_artifact_policy(obj)
        except Exception:
            # Nunca romper el bundle por un fallo en la policy
            return {'REGISTRO': {'required': ['ART-01'], 'optional': [], 'gate_for_advance': ['ART-01']}}
