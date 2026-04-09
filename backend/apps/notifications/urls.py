"""
S26: URLs para el sistema de notificaciones.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NotificationTemplateViewSet,
    NotificationLogListView,
    CollectionEmailLogListView,
    SendProformaView,
)

router = DefaultRouter()
router.register(r'templates', NotificationTemplateViewSet, basename='notification-template')

urlpatterns = [
    path('', include(router.urls)),
    path('log/', NotificationLogListView.as_view(), name='notification-log-list'),
    path('collections/', CollectionEmailLogListView.as_view(), name='collection-log-list'),
    path('send-proforma/', SendProformaView.as_view(), name='send-proforma'),
]
