"""
S21 — Serializer del Activity Feed.

REGLA: payload NO se incluye jamas — son datos internos.
REGLA: user_display NUNCA expone email. Cadena: full_name → role → 'Usuario' → 'Sistema'.
"""
from rest_framework import serializers
from apps.expedientes.models import EventLog


class EventLogFeedSerializer(serializers.ModelSerializer):
    expediente_number = serializers.SerializerMethodField()
    proforma_number = serializers.SerializerMethodField()
    user_display = serializers.SerializerMethodField()

    class Meta:
        model = EventLog
        fields = [
            'event_id',
            'event_type',
            'action_source',
            'previous_status',
            'new_status',
            'aggregate_id',       # expediente_id equivalent (UUID)
            'expediente_number',
            'proforma_id',
            'proforma_number',
            'user_id',
            'user_display',
            'occurred_at',
        ]
        # payload JAMAS se serializa (datos internos)

    def get_expediente_number(self, obj):
        if obj.expediente:
            # Soporte para expediente_number si existe el campo, si no usa PK truncado
            number = getattr(obj.expediente, 'expediente_number', None)
            if number:
                return str(number)
            return f'EXP-{str(obj.expediente.expediente_id)[:8]}'
        return ''

    def get_proforma_number(self, obj):
        if obj.proforma and obj.proforma.payload:
            return obj.proforma.payload.get('proforma_number', '')
        return ''

    def get_user_display(self, obj):
        """full_name → role → 'Usuario' → 'Sistema'. NUNCA email."""
        if not obj.user:
            return 'Sistema'
        name = obj.user.get_full_name()
        if name and name.strip():
            return name.strip()
        role = getattr(obj.user, 'role', None)
        if role:
            return role
        return 'Usuario'
