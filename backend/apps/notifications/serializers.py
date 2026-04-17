"""
S26: Serializers para el sistema de notificaciones.
"""
from rest_framework import serializers
from .models import NotificationTemplate, NotificationLog, CollectionEmailLog


class NotificationTemplateSerializer(serializers.ModelSerializer):
    brand_name = serializers.SerializerMethodField()

    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'name', 'template_key', 'subject_template', 'body_template',
            'is_active', 'brand_id', 'brand_name', 'language',
            'created_at', 'updated_at', 'created_by',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']

    def get_brand_name(self, obj):
        return obj.brand.name if obj.brand else 'Default'


class NotificationTemplateWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = ['name', 'template_key', 'subject_template', 'body_template',
                  'is_active', 'brand_id', 'language']


class NotificationLogSerializer(serializers.ModelSerializer):
    expediente_code = serializers.SerializerMethodField()

    class Meta:
        model = NotificationLog
        fields = [
            'id', 'correlation_id', 'template', 'template_key',
            'event_log_id', 'expediente_id', 'expediente_code',
            'recipient_email', 'subject', 'body_preview',
            'created_at', 'completed_at', 'status', 'error',
            'trigger_action_source', 'attempt_count',
        ]

    def get_expediente_code(self, obj):
        if obj.expediente:
            return str(obj.expediente.expediente_id)[:8].upper()
        return None


class CollectionEmailLogSerializer(serializers.ModelSerializer):
    expediente_code = serializers.SerializerMethodField()

    class Meta:
        model = CollectionEmailLog
        fields = [
            'id', 'expediente_id', 'expediente_code', 'proforma_id', 'payment_id',
            'created_at', 'grace_days_used', 'amount_overdue',
            'recipient_email', 'status', 'completed_at', 'error',
        ]

    def get_expediente_code(self, obj):
        return str(obj.expediente.expediente_id)[:8].upper() if obj.expediente else None


class TestSendSerializer(serializers.Serializer):
    sample_expediente_id = serializers.UUIDField(required=True)


class SendProformaSerializer(serializers.Serializer):
    proforma_id = serializers.UUIDField(required=True)
    recipient_email_override = serializers.EmailField(required=False, allow_blank=True)
