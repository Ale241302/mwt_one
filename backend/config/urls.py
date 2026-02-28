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
    path('api/core/', include('apps.core.urls', namespace='core')),
]
