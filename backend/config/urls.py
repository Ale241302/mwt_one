"""
Sprint 1 — Root URL Configuration (Item 7)
18 command endpoints under /api/expedientes/
Ref: LOTE_SM_SPRINT1 Item 7, PLB_SPRINT1_PROMPTS FIX-4

NOTE: /api/ui/* endpoints belong to Sprint 3. Do NOT register here.
NOTE: DashboardView belongs to Sprint 3. Do NOT import here.
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
    path('api/liquidations/', include('apps.liquidations.urls', namespace='liquidations')),
    path('api/brands/', include('apps.brands.urls')),
    path('api/qr/', include('apps.qr.urls')),
]
