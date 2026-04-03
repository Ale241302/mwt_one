from django.apps import AppConfig


class PricingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.pricing'
    label = 'pricing'

    def ready(self):
        import apps.pricing.signals  # noqa: F401 — conecta los signals al iniciar la app
