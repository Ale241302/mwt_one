# views_financial.py
# S25 FIX: Este archivo existe porque views/__init__.py (subpaquete S25)
# shadowa al archivo views.py en Python, rompiendo imports desde config/urls.py.
# FinancialDashboardView, FinancialComparisonView y FinancialSummaryView
# se reexportan aqui para que config/urls.py y urls.py los importen sin conflicto.
#
# El archivo views.py original NO se modifica para preservar el resto de sus vistas
# que son importadas por apps/expedientes/urls.py.

from apps.expedientes.views import (
    FinancialDashboardView,
    FinancialComparisonView,
    FinancialSummaryView,
)

__all__ = [
    'FinancialDashboardView',
    'FinancialComparisonView',
    'FinancialSummaryView',
]
