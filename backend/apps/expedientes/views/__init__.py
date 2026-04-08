# views/__init__.py
# Re-exporta todas las vistas del views.py original para mantener
# compatibilidad con imports existentes (config/urls.py, etc.)
# El subpaquete views/ contiene los nuevos módulos del S25:
#   - payment_status.py (verify, reject, release_credit)
#   - deferred.py (patch_deferred_price)

from apps.expedientes.views_admin import FinancialDashboardView  # noqa: F401
