from django.apps import AppConfig

class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.orders'
    label = 'orders'

    def ready(self):
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Módulo Orders (Órdenes de Compra) inicializado correctamente.")
