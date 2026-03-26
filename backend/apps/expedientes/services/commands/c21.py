from apps.expedientes.exceptions import CommandValidationError

def handle_c21(expediente, payload, env=None):
    """S16-06: Reabrir Expediente.
    Increments reopen_count and returns the status to EN_DESTINO.
    S17-09: Only authorized for CEO (is_superuser).
    """
    if expediente.status != 'CERRADO':
        raise CommandValidationError("Solo se pueden reabrir expedientes CERRADOS.")
    
    user = env.get('user') if env else None
    if not user or not user.is_superuser:
        raise CommandValidationError("Solo el CEO (superuser) puede reabrir expedientes.")

    expediente.status = 'EN_DESTINO'
    expediente.reopen_count = (expediente.reopen_count or 0) + 1
    expediente.save(update_fields=['status', 'reopen_count'])
    
    return {
        "message": "Expediente reabierto exitosamente",
        "reopen_count": expediente.reopen_count
    }
