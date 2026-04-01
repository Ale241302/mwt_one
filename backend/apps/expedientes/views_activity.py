"""
S21 — Views del Activity Feed.

Endpoints:
  GET  /api/activity-feed/         → ActivityFeedListView
  GET  /api/activity-feed/count/   → ActivityFeedCountView
  POST /api/activity-feed/mark-seen/ → ActivityFeedMarkSeenView

REGLAS HARD:
  - Todos llaman get_visible_events(request.user) — NUNCA duplicar permisos inline.
  - count/ usa slice [:100] — NO .count() para evitar full-table scan.
  - mark-seen sin filtros, sin query params, avanza al max(id) del queryset base.
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
      ?expediente=<uuid>     → filtra por expediente (aggregate_id)
      ?proforma=<uuid>       → filtra por proforma FK
      ?event_type=<str>      → filtra por event_type exacto
      ?unread_only=true      → solo eventos id > last_seen_event_id del usuario
    """
    serializer_class = EventLogFeedSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ActivityFeedPagination

    def get_queryset(self):
        user = self.request.user
        qs = get_visible_events(user).order_by('-event_id')

        # Filtro por expediente
        expediente_id = self.request.query_params.get('expediente')
        if expediente_id:
            qs = qs.filter(aggregate_id=expediente_id)

        # Filtro por proforma
        proforma_id = self.request.query_params.get('proforma')
        if proforma_id:
            qs = qs.filter(proforma__artifact_id=proforma_id)

        # Filtro por event_type
        event_type = self.request.query_params.get('event_type')
        if event_type:
            qs = qs.filter(event_type=event_type)

        # Filtro unread_only
        unread_only = self.request.query_params.get('unread_only', '').lower()
        if unread_only in ('true', '1', 'yes'):
            state, _ = UserNotificationState.objects.get_or_create(user=user)
            qs = qs.filter(event_id__gt=state.last_seen_event_id)

        return qs


class ActivityFeedCountView(APIView):
    """
    GET /api/activity-feed/count/

    Retorna:
      { unread_count: int (cap 99), has_more: bool, last_seen_event_id: int }

    REGLA: usa slice [:100] en lugar de .count() para evitar full-table scan.
    El cap real es 99 — si hay 100 resultados se asume 'hay más de 99'.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        state, _ = UserNotificationState.objects.get_or_create(user=user)

        qs = get_visible_events(user).filter(event_id__gt=state.last_seen_event_id)
        # Slice real — NO .count()
        ids = list(qs.order_by('-event_id').values_list('event_id', flat=True)[:100])
        n = len(ids)

        return Response({
            'unread_count': min(n, 99),
            'has_more': n == 100,
            'last_seen_event_id': state.last_seen_event_id,
        })


class ActivityFeedMarkSeenView(APIView):
    """
    POST /api/activity-feed/mark-seen/

    Sin filtros, sin query params. Avanza last_seen_event_id al max(id)
    del queryset base del usuario (get_visible_events sin filtros).

    Retorna:
      { previous_last_seen: int, last_seen_event_id: int }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # Queryset base sin filtros adicionales — avanza al max GLOBAL visible
        base_qs = get_visible_events(user).order_by('-event_id')
        latest = base_qs.values_list('event_id', flat=True).first()

        state, _ = UserNotificationState.objects.get_or_create(user=user)
        previous = state.last_seen_event_id

        if latest and latest > state.last_seen_event_id:
            state.last_seen_event_id = latest
            state.save(update_fields=['last_seen_event_id', 'updated_at'])

        return Response({
            'previous_last_seen': previous,
            'last_seen_event_id': state.last_seen_event_id,
        })
