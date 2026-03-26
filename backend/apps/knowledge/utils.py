"""Sprint 8 S8-06: Única fuente de verdad para retención de ConversationLog."""
from datetime import date, timedelta

# Reglas de retención (en días):
# 1. Expediente CERRADO: retain 365 días desde closed_at (si existe) o created_at
# 2. Expediente ABIERTO/otro estado: retain 90 días desde created_at
# 3. Sin expediente: retain 30 días desde created_at

RETENTION_CLOSED_DAYS = 365
RETENTION_OPEN_DAYS   = 90
RETENTION_NO_EXP_DAYS = 30


def calculate_retention(expediente=None, reference_date=None) -> date:
    """Calcula la fecha `retain_until` para un ConversationLog.

    Args:
        expediente: instancia de Expediente o None
        reference_date: fecha base (default: hoy)
    Returns:
        date: fecha hasta la cual retener el log
    """
    if reference_date is None:
        reference_date = date.today()

    if expediente is None:
        return reference_date + timedelta(days=RETENTION_NO_EXP_DAYS)

    if expediente.status == 'CERRADO':
        # closed_at es opcional: puede no estar en el modelo todavía (S8-06 pendiente migra)
        closed_at = getattr(expediente, 'closed_at', None)
        if closed_at:
            base = closed_at.date() if hasattr(closed_at, 'date') else closed_at
            return base + timedelta(days=RETENTION_CLOSED_DAYS)
        # Fallback: usar created_at si closed_at no existe
        created_at = getattr(expediente, 'created_at', None)
        if created_at:
            base = created_at.date() if hasattr(created_at, 'date') else created_at
            return base + timedelta(days=RETENTION_CLOSED_DAYS)
        return reference_date + timedelta(days=RETENTION_CLOSED_DAYS)

    return reference_date + timedelta(days=RETENTION_OPEN_DAYS)
