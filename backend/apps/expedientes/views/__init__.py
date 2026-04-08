# views/__init__.py
# Subpaquete creado en S25 para alojar los nuevos handlers:
#   - payment_status.py  (verify, reject, release_credit, release_all_verified)
#   - deferred.py        (patch_deferred_price)
#
# NOTA: Este paquete shadowa al archivo views.py en Python.
# Cualquier clase de views.py que se necesite en otros modulos
# debe importarse desde apps.expedientes.views_financial (reexports seguros)
# o directamente desde apps.expedientes.views.<modulo>.
