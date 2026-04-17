import json
import redis
from django.conf import settings
from django.utils import timezone

class EventBus:
    """
    Bus de eventos para comunicación asíncrona entre módulos.
    Utiliza Redis pub/sub para la difusión de eventos de dominio.
    """
    
    @staticmethod
    def _get_client():
        # Usamos la configuración de Redis de los CACHES o una específica si existe
        redis_url = getattr(settings, 'REDIS_URL', 'redis://redis:6379/0')
        if not redis_url and 'default' in settings.CACHES:
            redis_url = settings.CACHES['default']['LOCATION']
        return redis.from_url(redis_url)

    @staticmethod
    def publish(event_type, payload):
        """
        Publica un evento en el bus.
        event_type: string (e.g., 'sap.status_changed')
        payload: dict con los datos del evento
        """
        try:
            client = EventBus._get_client()
            message = {
                'event_type': event_type,
                'payload': payload,
                'timestamp': timezone.now().isoformat()
            }
            client.publish('mwt_events', json.dumps(message))
            
            # También podríamos registrar el evento en el Historial aquí
            # Pero es mejor que cada módulo lo haga explícitamente o vía un listener
        except Exception as e:
            # Fallback a logging si falla Redis
            import logging
            logger = logging.getLogger('mwt.events')
            logger.error(f"Error publishing event {event_type}: {str(e)}")
