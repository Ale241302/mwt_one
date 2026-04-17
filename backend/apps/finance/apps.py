from django.apps import AppConfig

class FinanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.finance'
    verbose_name = 'Finanzas'

    def ready(self):
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Módulo Finance (Finanzas y Pagos) inicializado correctamente.")
