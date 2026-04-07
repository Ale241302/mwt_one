"""
S24-14 — Observabilidad: handlers, signals y middleware para los 4 tipos de eventos
1. Emisión de signed URL → ya en orchestrator.py via EventLog
2. 429s del DRF → custom exception handler
3. Refresh token blacklisted → signal post_save en BlacklistedToken
4. Errores en knowledge endpoint → try/except → logging.error (en views.py)
"""
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.views import exception_handler as drf_default_exception_handler
from rest_framework.exceptions import Throttled
from rest_framework.response import Response

logger = logging.getLogger("mwt.observability")


# ---------------------------------------------------------------------------
# EVENTO 2 — Custom DRF Exception Handler: loguear 429s
# ---------------------------------------------------------------------------

def custom_exception_handler(exc, context):
    """
    Handler DRF extendido.
    - Loguea 429 Throttled con usuario + endpoint + timestamp.
    - Propaga todos los demás al handler default.

    Registrar en settings.py:
        REST_FRAMEWORK = {
            'EXCEPTION_HANDLER': 'backend.apps.knowledge.observability.custom_exception_handler',
        }
    """
    response = drf_default_exception_handler(exc, context)

    if isinstance(exc, Throttled):
        request = context.get("request")
        view = context.get("view")
        user = getattr(request, "user", None)
        endpoint = getattr(request, "path", "unknown")

        logger.warning(
            "THROTTLE_429",
            extra={
                "event_type": "THROTTLE_429",
                "user_id": getattr(user, "id", None),
                "username": getattr(user, "username", "anonymous"),
                "endpoint": endpoint,
                "view": view.__class__.__name__ if view else "unknown",
                "wait_seconds": exc.wait,
            },
        )

        if response is not None:
            response.data["event_logged"] = True
            response.data["retry_after"] = exc.wait

    return response


# ---------------------------------------------------------------------------
# EVENTO 3 — Signal: Refresh token blacklisted → log
# ---------------------------------------------------------------------------

def register_blacklist_signal():
    """
    Registra el signal para BlacklistedToken de djangorestframework-simplejwt.
    Llamar desde AppConfig.ready() del app knowledge (o core).

    Ejemplo en apps.py:
        from backend.apps.knowledge.observability import register_blacklist_signal
        class KnowledgeConfig(AppConfig):
            def ready(self):
                register_blacklist_signal()
    """
    try:
        from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

        @receiver(post_save, sender=BlacklistedToken, weak=False)
        def on_token_blacklisted(sender, instance, created, **kwargs):
            if created:
                outstanding = getattr(instance, "token", None)
                user = None
                if outstanding:
                    try:
                        from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
                        ot = OutstandingToken.objects.get(id=outstanding.id)
                        user = ot.user
                    except Exception:
                        pass

                logger.info(
                    "TOKEN_BLACKLISTED",
                    extra={
                        "event_type": "TOKEN_BLACKLISTED",
                        "user_id": getattr(user, "id", None),
                        "username": getattr(user, "username", "unknown"),
                        "token_jti": getattr(outstanding, "jti", None),
                    },
                )
    except ImportError:
        logger.warning("simplejwt token_blacklist no instalado — signal TOKEN_BLACKLISTED no registrado")


# ---------------------------------------------------------------------------
# EVENTO 4 — Helper para knowledge views: log estructurado de errores
# ---------------------------------------------------------------------------

def log_knowledge_error(exc: Exception, request, context: dict = None):
    """
    Loguear errores del knowledge endpoint de forma estructurada.
    Usar en los except blocks de AskView:

        except Exception as e:
            log_knowledge_error(e, request, {"question": question})
            return Response({...}, status=200)
    """
    user = getattr(request, "user", None)
    logger.error(
        "KNOWLEDGE_ERROR",
        exc_info=True,
        extra={
            "event_type": "KNOWLEDGE_ERROR",
            "user_id": getattr(user, "id", None),
            "username": getattr(user, "username", "anonymous"),
            "endpoint": getattr(request, "path", "/api/knowledge/ask/"),
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "context": context or {},
        },
    )


# ---------------------------------------------------------------------------
# Configuración de logging recomendada (agregar a settings/base.py)
# ---------------------------------------------------------------------------

LOGGING_CONFIG_SNIPPET = """
# Agregar a settings/base.py → LOGGING dict

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
    },
    'loggers': {
        'mwt.observability': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
"""
