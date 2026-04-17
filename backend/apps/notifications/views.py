"""
S26: Views para sistema de notificaciones.
H1: Templates CRUD + test-send + restore (CEO-only)
H2: Historial endpoints (NotificationLog + CollectionEmailLog)
H3: Send proforma — dedup 1h
"""
import uuid
import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import NotificationTemplate, NotificationLog, CollectionEmailLog
from .permissions import IsCEO
from .serializers import (
    NotificationTemplateSerializer,
    NotificationTemplateWriteSerializer,
    NotificationLogSerializer,
    CollectionEmailLogSerializer,
    TestSendSerializer,
    SendProformaSerializer,
)

logger = logging.getLogger(__name__)


# =============================================================================
# H1: Templates CRUD + restore + test-send
# =============================================================================

class NotificationTemplateViewSet(viewsets.ModelViewSet):
    """
    CEO-only. CRUD completo de templates.
    DELETE = desactivar (is_active=False), no borrar.
    /restore/ = reactivar.
    /test-send/ = email de prueba a CEO_EMAIL.
    """
    permission_classes = [IsCEO]
    serializer_class = NotificationTemplateSerializer

    def get_queryset(self):
        # Inactivos visibles en lista (grayed en frontend)
        return NotificationTemplate.objects.all().order_by('template_key', 'language')

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return NotificationTemplateWriteSerializer
        return NotificationTemplateSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """DELETE = desactivar. No borra el template."""
        instance = self.get_object()
        instance.is_active = False
        # Nota: instance.save() bypasses ImmutableManager (si se aplicara en el futuro)
        # NotificationTemplate no es inmutable por ahora, así que esto es seguro.
        instance.save(update_fields=['is_active'])
        return Response({'detail': 'Template desactivado.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='restore')
    def restore(self, request, pk=None):
        """POST /restore/ — Reactivar template desactivado."""
        instance = self.get_object()
        instance.is_active = True
        instance.save(update_fields=['is_active'])
        return Response({'detail': 'Template reactivado.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='test-send')
    def test_send(self, request, pk=None):
        """
        POST /test-send/ — Email de prueba a CEO_EMAIL.
        Requiere: { "sample_expediente_id": "uuid" }
        """
        serializer = TestSendSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        template = self.get_object()
        sample_expediente_id = serializer.validated_data['sample_expediente_id']

        try:
            from apps.expedientes.models import Expediente
            expediente = Expediente.objects.get(pk=sample_expediente_id)
        except Expediente.DoesNotExist:
            return Response({'detail': 'Expediente no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        ceo_email = getattr(settings, 'CEO_EMAIL', '') or None
        if not ceo_email:
            return Response({'detail': 'CEO_EMAIL no configurado.'}, status=status.HTTP_400_BAD_REQUEST)

        from apps.notifications.tasks import send_notification
        send_notification.delay(
            template_key=template.template_key,
            expediente_id=str(expediente.pk),
            event_log_id=None,
            trigger_action_source='test_send',
            _correlation_id=str(uuid.uuid4()),
            _recipient=ceo_email,
        )
        return Response({'detail': 'Email de prueba encolado.'}, status=status.HTTP_200_OK)


# =============================================================================
# H2: Historial endpoints
# =============================================================================

class NotificationLogListView(APIView):
    """
    GET /api/notifications/log/
    CEO-only. Filtros: expediente, status, date_from, date_to.
    Paginación 25/page.
    """
    permission_classes = [IsCEO]

    def get(self, request):
        qs = NotificationLog.objects.all().order_by('-created_at')

        expediente_id = request.query_params.get('expediente')
        if expediente_id:
            qs = qs.filter(expediente_id=expediente_id)

        log_status = request.query_params.get('status')
        if log_status:
            qs = qs.filter(status=log_status)

        date_from = request.query_params.get('date_from')
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)

        date_to = request.query_params.get('date_to')
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)

        # Paginación simple
        page = int(request.query_params.get('page', 1))
        page_size = 25
        offset = (page - 1) * page_size
        total = qs.count()
        qs = qs[offset:offset + page_size]

        serializer = NotificationLogSerializer(qs, many=True)
        return Response({
            'count': total,
            'page': page,
            'page_size': page_size,
            'results': serializer.data,
        })


class CollectionEmailLogListView(APIView):
    """
    GET /api/notifications/collections/
    CEO-only. Filtros: expediente, date_from, date_to.
    Paginación 25/page.
    """
    permission_classes = [IsCEO]

    def get(self, request):
        qs = CollectionEmailLog.objects.all().order_by('-created_at')

        expediente_id = request.query_params.get('expediente')
        if expediente_id:
            qs = qs.filter(expediente_id=expediente_id)

        date_from = request.query_params.get('date_from')
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)

        date_to = request.query_params.get('date_to')
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)

        log_status = request.query_params.get('status')
        if log_status:
            qs = qs.filter(status=log_status)

        page = int(request.query_params.get('page', 1))
        page_size = 25
        offset = (page - 1) * page_size
        total = qs.count()
        qs = qs[offset:offset + page_size]

        serializer = CollectionEmailLogSerializer(qs, many=True)
        return Response({
            'count': total,
            'page': page,
            'page_size': page_size,
            'results': serializer.data,
        })


# =============================================================================
# H3: Send proforma — dedup 1h
# =============================================================================

class SendProformaView(APIView):
    """
    POST /api/notifications/send-proforma/
    CEO-only. Envía proforma por email.
    template_key='proforma.sent'. Dedup 1h →  409 si ya se envió.
    """
    permission_classes = [IsCEO]

    def post(self, request):
        serializer = SendProformaSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        proforma_id = serializer.validated_data['proforma_id']
        recipient_override = serializer.validated_data.get('recipient_email_override')

        from apps.core.registry import ModuleRegistry
        artifact_model = ModuleRegistry.get_model('expedientes', 'ArtifactInstance')
        if not artifact_model:
             return Response({'detail': 'Modelo ArtifactInstance no disponible.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            proforma = artifact_model.objects.select_related('expediente').get(pk=proforma_id)
        except artifact_model.DoesNotExist:
            return Response({'detail': 'Proforma no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        expediente = proforma.expediente

        # Dedup: 409 si ya se envió en la última hora
        one_hour_ago = timezone.now() - timedelta(hours=1)
        already_sent = NotificationLog.objects.filter(
            template_key='proforma.sent',
            proforma=proforma,
            status='sent',
            completed_at__gte=one_hour_ago,
        ).exists()
        if already_sent:
            return Response(
                {'detail': 'Proforma ya enviada en la última hora.'},
                status=status.HTTP_409_CONFLICT
            )

        # Resolver destinatario
        if recipient_override:
            recipient = recipient_override
        else:
            from apps.notifications.services import resolve_notification_recipient
            recipient = resolve_notification_recipient(expediente, str(proforma_id))

        if not recipient:
            return Response(
                {'detail': 'No se pudo resolver el destinatario.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from apps.notifications.tasks import send_notification
        correlation_id = str(uuid.uuid4())
        send_notification.delay(
            template_key='proforma.sent',
            expediente_id=str(expediente.pk),
            proforma_id=str(proforma_id),
            event_log_id=None,
            trigger_action_source='send_proforma_manual',
            _correlation_id=correlation_id,
            _recipient=recipient,
        )
        return Response({'detail': 'Proforma encolada para envío.', 'correlation_id': correlation_id},
                        status=status.HTTP_200_OK)
