"""
Root URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from core.views_logger import FrontendLoggerView
# S25 FIX: import desde views_financial para evitar conflicto views/ vs views.py
from apps.expedientes.views_financial import FinancialDashboardView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/expedientes/', include('apps.expedientes.urls', namespace='expedientes')),
    path('api/expedientes/', include('apps.expedientes.urls_sprint18')),   # Sprint 18
    path('api/sizing/', include('apps.sizing.urls', namespace='sizing')),         # Sprint 18
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
    path('api/users/', include('apps.users.urls')),
    path('api/agreements/', include('apps.agreements.urls')),
    # Inventario
    path('api/inventario/', include('apps.inventario.urls')),
    # Sprint 23: Commercial layer (rebates, commissions, artifact policy)
    path('api/commercial/', include('apps.commercial.urls')),
    # Spectacular
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api/logs/', include(([
        path('', FrontendLoggerView.as_view()),
    ], 'logs'))),
    # FIX: Dashboard endpoints directamente en /api/ui/dashboard/
    path('api/ui/dashboard/financial/', FinancialDashboardView.as_view(), name='ui-dashboard-financial'),
    path('api/ui/dashboard/', FinancialDashboardView.as_view(), name='ui-dashboard'),
    
    # S28: CEO Dashboard Landing Page
    path('api/portal/ceo-dashboard/', __import__('apps.portal.views_dashboard').portal.views_dashboard.CEODashboardView.as_view(), name='ceo-dashboard'),
    path('api/portal/ceo-dashboard/ajax/', __import__('apps.portal.views_dashboard').portal.views_dashboard.CEODashboardAjaxView.as_view(), name='ceo-dashboard-ajax'),
    
    # S21: Activity Feed endpoints
    path('api/', include('apps.expedientes.urls_activity')),
    # S22: Pricing endpoints
    path('api/pricing/', include('apps.pricing.urls')),
    # S26: Notifications
    path('api/notifications/', include('apps.notifications.urls')),
]
