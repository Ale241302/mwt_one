# views/__init__.py
# Re-exporta vistas del módulo views.py original para mantener
# compatibilidad con imports existentes (config/urls.py, etc.)
# Usa importlib para evitar import circular ya que views/ shadow-ea views.py

import importlib as _importlib
import sys as _sys
import os as _os

# Carga views.py directamente por path para evitar el conflicto
# de nombres entre el paquete views/ y el archivo views.py
_views_path = _os.path.join(
    _os.path.dirname(_os.path.dirname(__file__)),
    'views.py'
)
_spec = _importlib.util.spec_from_file_location(
    'apps.expedientes._views_legacy',
    _views_path,
)
_views_legacy = _importlib.util.module_from_spec(_spec)
_sys.modules['apps.expedientes._views_legacy'] = _views_legacy
_spec.loader.exec_module(_views_legacy)

FinancialDashboardView = _views_legacy.FinancialDashboardView  # noqa: F401
