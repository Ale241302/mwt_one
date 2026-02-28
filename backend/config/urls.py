from django.contrib import admin
from django.urls import path, include
from apps.expedientes.views import ListExpedientesView, ExpedienteBundleView
from apps.core.views import DashboardView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/expedientes/', include('apps.expedientes.urls', namespace='expedientes')),
    path('api/core/', include('apps.core.urls', namespace='core')),
    
    # UI Endpoints (Sprint 3)
    path('api/ui/expedientes/', ListExpedientesView.as_view(), name='ui-expedientes-list'),
    path('api/ui/expedientes/<uuid:pk>/', ExpedienteBundleView.as_view(), name='ui-expedientes-detail'),
    path('api/ui/dashboard/', DashboardView.as_view(), name='ui-dashboard'),
]
