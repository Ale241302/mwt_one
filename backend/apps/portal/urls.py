from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PortalExpedienteViewSet, CatalogView, PortalContactsView, PortalPreferencesView
from .views_client_portal import ClientPortalViewSet
from .views_vendor import VendorCatalogView

router = DefaultRouter()
router.register(r'expedientes', PortalExpedienteViewSet, basename='portal-expedientes-v1')
router.register(r'cliente/expedientes', ClientPortalViewSet, basename='portal-cliente-expedientes')

urlpatterns = [
    path('', include(router.urls)),
    path('catalog/', CatalogView.as_view(), name='portal-catalog'),
    path('vendedor/catalog/', VendorCatalogView.as_view(), name='portal-vendor-catalog'),
    path('contacts/', PortalContactsView.as_view(), name='portal-contacts'),
    path('me/preferences/', PortalPreferencesView.as_view(), name='portal-preferences'),
]
