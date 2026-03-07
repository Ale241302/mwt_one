"""
Sprint 3-4 â€” UI URL Configuration for /api/ui/expedientes/
"""
from django.urls import path
from apps.expedientes.views import (
    ListExpedientesView,
    ExpedienteBundleView,
    DocumentDownloadView,
    FinancialDashboardView,
)

app_name = 'expedientes-ui'

urlpatterns = [
    # Sprint 3: List and Detail (Bundle)
    path('', ListExpedientesView.as_view(), name='list'),
    path('<uuid:pk>/', ExpedienteBundleView.as_view(), name='bundle'),

    # Download endpoint
    path('documents/<uuid:artifact_id>/download/', DocumentDownloadView.as_view(), name='document-download'),

    # Sprint 4 S4-11: Financial Dashboard
    path('dashboard/financial/', FinancialDashboardView.as_view(), name='financial-dashboard'),
]
