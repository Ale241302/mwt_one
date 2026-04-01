"""
S21 — Views del Activity Feed.

Endpoints:
  GET  /api/activity-feed/         → ActivityFeedListView
  GET  /api/activity-feed/count/   → ActivityFeedCountView
  POST /api/activity-feed/mark-seen/ → ActivityFeedMarkSeenView

REGLAS HARD:
  - Todos llaman get_visible_events(request.user) — NUNCA duplicar permisos inline.
  - count/ usa slice materializado, NO .count() sobre un queryset con slice.
  - mark-seen actualiza last_seen_at al occurred_at del evento más reciente.
  - payload NO se serializa.
"""
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from apps.expedientes.models import EventLog, UserNotificationState
from apps.expedientes.serializers_activity import EventLogFeedSerializer
from apps.expedientes.services.activity_permissions import get_visible_events


class ActivityFeedPagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = 'page_size'
    max_page_size = 100


class ActivityFeedListView(ListAPIView):
    """
    GET /api/activity-feed/

    Filtros opcionales (query params):
      ?expediente=<uuid>     → filtra por expediente FK
      ?proforma=<uuid>       → filtra por proforma FK
      ?event_type=<str>      → filtra por event_type exacto
      ?unread_only=true      → solo eventos occurred_at > last_seen_at del usuario
    """
    serializer_class = EventLogFeedSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ActivityFeedPagination

    def get_queryset(self):
        user = self.request.user
        # BUG-FIX 1: NO hacer slice aquí — DRF necesita llamar .count() y
        # .filter() sobre este queryset para la paginación. Un slice evaluado
        # ya no soporta esas operaciones.
        qs = get_visible_events(user).order_by('-occurred_at')

        # Filtro por expediente
        expediente_id = self.request.query_params.get('expediente')
        if expediente_id:
            qs = qs.filter(expediente_id=expediente_id)

        # Filtro por proforma
        proforma_id = self.request.query_params.get('proforma')
        if proforma_id:
            qs = qs.filter(proforma_id=proforma_id)

        # Filtro por event_type
        event_type = self.request.query_params.get('event_type')
        if event_type:
            qs = qs.filter(event_type=event_type)

        # Filtro unread_only
        unread_only = self.request.query_params.get('unread_only', '').lower()
        if unread_only in ('true', '1', 'yes'):
            state, _ = UserNotificationState.objects.get_or_create(user=user)
            if state.last_seen_at:
                qs = qs.filter(occurred_at__gt=state.last_seen_at)
            # Si last_seen_at es NULL todo es unread → no aplicar filtro adicional

        return qs


class ActivityFeedCountView(APIView):
    """
    GET /api/activity-feed/count/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        state, _ = UserNotificationState.objects.get_or_create(user=user)

        qs = get_visible_events(user)
        if state.last_seen_at:
            qs = qs.filter(occurred_at__gt=state.last_seen_at)

        # BUG-FIX 2: Un queryset con slice (qs[:100]) no soporta .count() en Django
        # → materializar la lista con len() para evitar TypeError.
        ids = list(qs.order_by('-occurred_at').values_list('event_id', flat=True)[:100])
        count = len(ids)
        has_more = count >= 100
        display_count = 99 if has_more else count

        return Response({
            'unread_count': display_count,
            'has_more': has_more,
            'last_seen_at': state.last_seen_at,
        })


class ActivityFeedMarkSeenView(APIView):
    """
    POST /api/activity-feed/mark-seen/
    Actualiza last_seen_at al timestamp del evento más reciente visible.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        base_qs = get_visible_events(user).order_by('-occurred_at')
        latest_event = base_qs.first()

        state, _ = UserNotificationState.objects.get_or_create(user=user)
        previous = state.last_seen_at

        if latest_event:
            state.last_seen_at = latest_event.occurred_at
            state.save(update_fields=['last_seen_at', 'updated_at'])

        return Response({
            'previous_last_seen': previous,
            'last_seen_at': state.last_seen_at,
        })
