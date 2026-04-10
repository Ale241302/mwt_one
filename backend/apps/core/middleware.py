import logging

logger = logging.getLogger('mwt.audit')

class DataAccessAuditMiddleware:
    """
    S27-07g2: Remediación G2 — Middleware de auditoría mínimo.
    Loguea accesos a rutas sensibles (expedientes, pagos, documentos).
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # Rutas sensibles que Gatillarán el log de auditoría
        self.sensitive_keywords = ['expedientes', 'pagos', 'documentos', 'commercial']

    def __call__(self, request):
        response = self.get_response(request)
        
        # Solo auditamos si el path contiene keywords sensibles y el usuario está autenticado
        if any(keyword in request.path for keyword in self.sensitive_keywords):
            user = request.user if request.user.is_authenticated else "Anonymous"
            # Solo auditamos métodos que no sean GET (opcional, pero G2 pide rastro de acceso)
            # Para cumplir G2 estrictamente "Audit trail acceso datos personales", auditamos todo
            logger.info(
                f"DATA_ACCESS user={user} method={request.method} path={request.path} status={response.status_code}"
            )
            
        return response
