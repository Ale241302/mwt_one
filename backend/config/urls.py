"""
Root URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from core.views_logger import FrontendLoggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/expedientes/', include('apps.expedientes.urls', namespace='expedientes')),
    path('api/ui/', include('apps.core.urls_ui', namespace='core-ui')),
    path('api/ui/expedientes/', include('apps.expedientes.urls_ui', namespace='expedientes-ui')),
    path('api/core/', include('apps.core.urls', namespace='core')),
    # Sprint 5
    path('api/transfers/', include('apps.transfers.urls', namespace='transfers')),
    path('api/ui/transfers/', include('apps.transfers.urls_ui', namespace='transfers-ui')),
    path('api/liquidations/', include('apps.liquidations.urls', namespace='liquidations')),
    path('api/brands/', include('apps.brands.urls')),
    path('api/qr/', include('apps.qr.urls')),
    # Clientes
    path('api/clientes/', include('apps.clientes.urls')),
    path('api/productos/', include('apps.productos.urls')),
    path('api/knowledge/', include('apps.knowledge.urls')),
    path('api/suppliers/', include('apps.suppliers.urls')),
    # Sprint 8: Users & Auth
    path('api/portal/', include('apps.portal.urls')),
    path('api/agreements/', include('apps.agreements.urls')),
    # Inventario
    path('api/inventario/', include('apps.inventario.urls')),
    # Spectacular
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api/logs/', include(([
        path('', FrontendLoggerView.as_view()),
    ], 'logs'))),
]
