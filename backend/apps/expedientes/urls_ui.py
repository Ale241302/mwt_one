"""
Sprint 3-4 – UI URL Configuration for /api/ui/expedientes/
S20-07: Agrega endpoint POST para crear proformas (ART-02)

FIX-2026-03-31: Se ELIMINÓ la ruta 'dashboard/financial/' de aquí.
Ahora vive en config/urls.py como /api/ui/dashboard/financial/
para que el frontend la encuentre en la URL correcta.
"""
from django.urls import path
from apps.expedientes.views import (
    ListExpedientesView,
    ExpedienteBundleView,
    DocumentDownloadView,
    LegalEntitiesListView,
)
from apps.expedientes.views_s20 import ProformaCreateView

app_name = 'expedientes-ui'

urlpatterns = [
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
