"""
S21 — Centralización de permisos del Activity Feed.

REGLA HARD: Los 3 endpoints del feed deben llamar get_visible_events().
JAMÁS duplicar la lógica de permisos inline en las views.
"""
from __future__ import annotations

# Contrato cerrado: event_types que SOLO el CEO puede ver.
CEO_ONLY_EVENT_TYPES: frozenset[str] = frozenset([
    'cost.registered',
    'commission.invoiced',
    'compensation.noted',
])


def get_visible_events(user, base_qs=None):
    """
    Retorna un queryset de EventLog visible para `user` según su rol.

    Jerarquía:
      1. CEO / superuser  → todo
      2. CLIENT_*         → solo su subsidiaria, sin CEO_ONLY_EVENT_TYPES
      3. AGENT_* / resto  → solo expedientes donde el usuario ha operado (EventLog.user=user)

    Param base_qs: queryset de EventLog ya filtrado externamente (opcional).
                   Si es None se usa EventLog.objects.all().
    """
    from apps.expedientes.models import EventLog

    qs = base_qs if base_qs is not None else EventLog.objects.all()
    qs = qs.select_related('expediente', 'proforma', 'user')

    user_role = getattr(user, 'role', None)

    # CEO o superadmin: ve todo sin restricciones
    if user_role == 'CEO' or user.is_superuser:
        return qs

    # CLIENT_*: tiene client_subsidiary → filtrar por subsidiaria y excluir eventos CEO-only
    if getattr(user, 'client_subsidiary', None):
        return qs.filter(
            expediente__client_subsidiary=user.client_subsidiary
        ).exclude(event_type__in=CEO_ONLY_EVENT_TYPES)

    # AGENT_* y cualquier otro rol: solo expedientes donde el agente ha disparado algún evento
    operated_ids = (
        EventLog.objects.filter(user=user)
        .values_list('aggregate_id', flat=True)
        .distinct()
    )
    return qs.filter(aggregate_id__in=operated_ids)
