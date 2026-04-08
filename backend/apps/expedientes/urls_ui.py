"""
Sprint 3-4 – UI URL Configuration for /api/ui/expedientes/
S20-07: Agrega endpoint POST para crear proformas (ART-02)

FIX-2026-03-31: 'dashboard/financial/' fue movida a config/urls.py
  como /api/ui/dashboard/financial/ para que el frontend la encuentre.

FIX-2026-04-08d: El frontend (/dashboard/financial) llama a
  /api/ui/expedientes/dashboard/financial/ (con prefijo expedientes/).
  Se agrega alias aquí que apunta al mismo FinancialDashboardView.
  Ambas rutas quedan activas:
    /api/ui/dashboard/financial/            <- original en config/urls.py
    /api/ui/expedientes/dashboard/financial/ <- alias nuevo (esta)
"""
from django.urls import path
from apps.expedientes.views import (
    ListExpedientesView,
    ExpedienteBundleView,
    DocumentDownloadView,
    LegalEntitiesListView,
)
from apps.expedientes.views_s20 import ProformaCreateView
from apps.expedientes.views_financial import FinancialDashboardView

app_name = 'expedientes-ui'

urlpatterns = [
    # FIX-2026-04-08d: alias /api/ui/expedientes/dashboard/financial/
    # El frontend lo llama con este prefijo desde la página /dashboard/financial.
    path('dashboard/financial/', FinancialDashboardView.as_view(), name='dashboard-financial'),

    # Sprint 3: List and Detail (Bundle)
    path('', ListExpedientesView.as_view(), name='list'),
    path('<uuid:pk>/', ExpedienteBundleView.as_view(), name='bundle'),

    # S20-07: Crear proforma (ART-02) para un expediente
    path('<uuid:pk>/artifacts/proforma/', ProformaCreateView.as_view(), name='proforma-create'),

    # Download endpoint
    path('documents/<uuid:artifact_id>/download/', DocumentDownloadView.as_view(), name='document-download'),

    # Legal Entities para formularios UI (e.g. Nuevo Expediente)
    path('legal-entities/', LegalEntitiesListView.as_view(), name='legal-entities'),
]
