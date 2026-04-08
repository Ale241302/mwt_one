# views/__init__.py
# ===========================================================================
# S25 FIX: Este subpaquete (views/) shadowa al archivo views.py en Python.
# Para que todos los imports existentes sigan funcionando sin modificar
# ningun otro archivo, se carga views.py directamente por path de archivo
# usando importlib.util y se re-exportan todas sus clases publicas.
# ===========================================================================
import importlib.util
import sys
import os

_views_py_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'views.py')
_spec = importlib.util.spec_from_file_location(
    'apps.expedientes._views_legacy',
    _views_py_path,
)
_views_legacy = importlib.util.module_from_spec(_spec)
sys.modules['apps.expedientes._views_legacy'] = _views_legacy
_spec.loader.exec_module(_views_legacy)

# Re-exportar todas las clases publicas de views.py
IsCEO = _views_legacy.IsCEO
EnsureNotBlocked = _views_legacy.EnsureNotBlocked
CreateExpedienteView = _views_legacy.CreateExpedienteView
CommandDispatchView = _views_legacy.CommandDispatchView
SupersedeArtifactView = _views_legacy.SupersedeArtifactView
VoidArtifactView = _views_legacy.VoidArtifactView
ListExpedientesView = _views_legacy.ListExpedientesView
ExpedienteBundleView = _views_legacy.ExpedienteBundleView
DocumentDownloadView = _views_legacy.DocumentDownloadView
CostsListView = _views_legacy.CostsListView
CostsSummaryView = _views_legacy.CostsSummaryView
InvoiceSuggestionView = _views_legacy.InvoiceSuggestionView
InvoiceView = _views_legacy.InvoiceView
FinancialComparisonView = _views_legacy.FinancialComparisonView
MirrorPDFView = _views_legacy.MirrorPDFView
FinancialDashboardView = _views_legacy.FinancialDashboardView
LegalEntitiesListView = _views_legacy.LegalEntitiesListView
FinancialSummaryView = _views_legacy.FinancialSummaryView
DocumentsListView = _views_legacy.DocumentsListView
LogisticsSuggestionsView = _views_legacy.LogisticsSuggestionsView
HandoffSuggestionView = _views_legacy.HandoffSuggestionView
LiquidationPaymentSuggestionView = _views_legacy.LiquidationPaymentSuggestionView
CEOOverrideView = _views_legacy.CEOOverrideView

__all__ = [
    'IsCEO', 'EnsureNotBlocked',
    'CreateExpedienteView', 'CommandDispatchView',
    'SupersedeArtifactView', 'VoidArtifactView',
    'ListExpedientesView', 'ExpedienteBundleView', 'DocumentDownloadView',
    'CostsListView', 'CostsSummaryView',
    'InvoiceSuggestionView', 'InvoiceView',
    'FinancialComparisonView', 'MirrorPDFView',
    'FinancialDashboardView', 'LegalEntitiesListView',
    'FinancialSummaryView', 'DocumentsListView',
    'LogisticsSuggestionsView', 'HandoffSuggestionView',
    'LiquidationPaymentSuggestionView', 'CEOOverrideView',
]
