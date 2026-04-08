# views_financial.py
# S25 FIX: El subpaquete views/ (creado en S25) shadowa al archivo views.py
# en Python, haciendo imposible importar directamente con:
#   from apps.expedientes.views import FinancialDashboardView
#
# Solucion: cargar views.py por path de archivo via importlib,
# completamente fuera del sistema de modulos normal de Python.
# Esto evita el conflicto sin tocar views.py ni views/__init__.py.

import importlib.util
import sys
import os

_views_py_path = os.path.join(os.path.dirname(__file__), 'views.py')
_spec = importlib.util.spec_from_file_location(
    'apps.expedientes._views_legacy',
    _views_py_path,
)
_views_legacy = importlib.util.module_from_spec(_spec)
sys.modules['apps.expedientes._views_legacy'] = _views_legacy
_spec.loader.exec_module(_views_legacy)

FinancialDashboardView = _views_legacy.FinancialDashboardView
FinancialComparisonView = _views_legacy.FinancialComparisonView
FinancialSummaryView = _views_legacy.FinancialSummaryView

__all__ = [
    'FinancialDashboardView',
    'FinancialComparisonView',
    'FinancialSummaryView',
]
