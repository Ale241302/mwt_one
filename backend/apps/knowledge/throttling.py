# S24-04: Custom throttle class para knowledge endpoints
# Rate: 10 requests/min por usuario autenticado
from rest_framework.throttling import UserRateThrottle


class KnowledgeRateThrottle(UserRateThrottle):
    """
    Throttle personalizado para el endpoint /api/knowledge/ask/.
    Limita a 10 requests por minuto por usuario autenticado.
    Se aplica además del throttle global (user=60/min).
    Sprint 24 — S24-04
    """
    scope = 'knowledge'
    rate = '10/min'
