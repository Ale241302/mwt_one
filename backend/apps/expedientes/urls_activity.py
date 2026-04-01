"""
S21 — URLs del Activity Feed.

Incluir en el urls.py principal con:
    from apps.expedientes.urls_activity import urlpatterns as activity_urls
    urlpatterns += activity_urls

O via include():
    path('api/', include('apps.expedientes.urls_activity')),
"""
from django.urls import path
from apps.expedientes.views_activity import (
    ActivityFeedListView,
    ActivityFeedCountView,
    ActivityFeedMarkSeenView,
)

urlpatterns = [
    # GET /api/activity-feed/
    path('activity-feed/', ActivityFeedListView.as_view(), name='activity-feed-list'),
    # GET /api/activity-feed/count/
    path('activity-feed/count/', ActivityFeedCountView.as_view(), name='activity-feed-count'),
    # POST /api/activity-feed/mark-seen/
    path('activity-feed/mark-seen/', ActivityFeedMarkSeenView.as_view(), name='activity-feed-mark-seen'),
]
