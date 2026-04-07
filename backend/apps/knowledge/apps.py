from django.apps import AppConfig


class KnowledgeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.knowledge'
    verbose_name = 'Knowledge'

    def ready(self):
        """S24-14: Registrar signal de blacklist al iniciar la app."""
        try:
            from apps.knowledge.observability import register_blacklist_signal
            register_blacklist_signal()
        except Exception:
            # No bloquear el arranque si simplejwt blacklist no está instalado
            pass
