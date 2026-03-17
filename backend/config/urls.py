"""
Root URL Configuration
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/expedientes/', include('apps.expedientes.urls', namespace='expedientes')),
    path('api/ui/', include('apps.core.urls_ui', namespace='core-ui')),
    path('api/ui/expedientes/', include('apps.expedientes.urls_ui', namespace='expedientes-ui')),
    path('api/core/', include('apps.core.urls', namespace='core')),
    # Sprint 5
    path('api/transfers/', include('apps.transfers.urls', namespace='transfers')),
    path('api/ui/transfers/', include('apps.transfers.urls_ui', namespace='transfers-ui')),  # fixed: uses own urls_ui
    path('api/liquidations/', include('apps.liquidations.urls', namespace='liquidations')),
    path('api/brands/', include('apps.brands.urls')),
    path('api/qr/', include('apps.qr.urls')),
    # Clientes
    path('api/clientes/', include('apps.clientes.urls')),
]
