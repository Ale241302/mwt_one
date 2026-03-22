from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PortalExpedienteViewSet, CatalogView

router = DefaultRouter()
router.register(r'expedientes', PortalExpedienteViewSet, basename='portal-expedientes-v1')

urlpatterns = [
    path('', include(router.urls)),
    path('catalog/', CatalogView.as_view(), name='portal-catalog'),
]
