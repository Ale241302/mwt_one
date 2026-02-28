"""
Sprint 1 — Read + Write Serializers
Ref: LOTE_SM_SPRINT1 Items 1A + 1B
"""
from rest_framework import serializers
from apps.expedientes.models import (
    Expediente, ArtifactInstance, EventLog, CostLine, PaymentLine,
)


# ──────────────────────────────────────────────────
# READ SERIALIZERS (Item 1A)
# ──────────────────────────────────────────────────

class EventLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventLog
        fields = [
            'event_id', 'event_type', 'aggregate_type', 'aggregate_id',
            'payload', 'occurred_at', 'emitted_by',
            'processed_at', 'retry_count', 'correlation_id',
        ]
        read_only_fields = fields


class ArtifactInstanceSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ArtifactInstance
        fields = [
            'artifact_id', 'artifact_type', 'status', 'status_display',
            'payload', 'supersedes', 'superseded_by',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields


class CostLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = CostLine
        fields = [
            'cost_line_id', 'cost_type', 'amount', 'currency',
            'phase', 'description', 'created_at', 'updated_at',
        ]
        read_only_fields = fields


class PaymentLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentLine
        fields = [
            'payment_line_id', 'amount', 'currency', 'method',
            'reference', 'registered_at', 'registered_by_type',
            'registered_by_id', 'created_at', 'updated_at',
        ]
        read_only_fields = fields


class ExpedienteSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_status_display = serializers.CharField(
        source='get_payment_status_display', read_only=True)
    legal_entity_name = serializers.CharField(
        source='legal_entity.legal_name', read_only=True, default=None)

    class Meta:
        model = Expediente
        fields = [
            'expediente_id', 'legal_entity', 'legal_entity_name',
            'brand', 'client', 'status', 'status_display',
            'is_blocked', 'blocked_reason', 'blocked_at',
            'blocked_by_type', 'blocked_by_id',
            'mode', 'freight_mode', 'transport_mode',
            'dispatch_mode', 'price_basis',
            'credit_clock_start_rule', 'credit_clock_started_at',
            'payment_status', 'payment_status_display',
            'payment_registered_at',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields


# ──────────────────────────────────────────────────
# WRITE SERIALIZERS (Item 1B)
# ──────────────────────────────────────────────────

class ExpedienteCreateSerializer(serializers.Serializer):
    """C1: CreateExpediente — inputs."""
    legal_entity_id = serializers.CharField(max_length=50, required=True)
    brand = serializers.CharField(max_length=200)
    client = serializers.CharField(max_length=50, required=True)
    mode = serializers.CharField(max_length=50, required=False, default='')
    freight_mode = serializers.CharField(max_length=50, required=False, default='')
    transport_mode = serializers.CharField(max_length=50, required=False, default='')
    dispatch_mode = serializers.ChoiceField(
        choices=['MWT', 'CLIENT'], default='MWT')
    price_basis = serializers.CharField(max_length=50, required=False, default='')
    credit_clock_start_rule = serializers.ChoiceField(
        choices=['on_creation', 'on_shipment'], required=False, default='on_creation')


class ArtifactPayloadSerializer(serializers.Serializer):
    """Generic serializer for commands C2-C10 that create artifacts.
    Payload is a JSON object — validation is intentionally lenient in MVP."""
    payload = serializers.DictField(required=False, default=dict)


class RegisterCostSerializer(serializers.Serializer):
    """C15: RegisterCost — inputs."""
    cost_type = serializers.CharField(max_length=50)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField(max_length=3)
    phase = serializers.CharField(max_length=50)
    description = serializers.CharField(required=False, default='', allow_blank=True)


class RegisterPaymentSerializer(serializers.Serializer):
    """C21: RegisterPayment — inputs."""
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField(max_length=3)
    method = serializers.CharField(max_length=50)
    reference = serializers.CharField(max_length=100)

