"""
S23-10/11/12 — Permisos DRF para la capa comercial.

Reglas:
- IsCEO: solo usuarios con role == 'CEO'. NUNCA usar is_staff.
- IsCEOOrInternalAgent: CEO o cualquier rol que empiece por 'AGENT_'.
- IsClientUser: cualquier rol que empiece por 'CLIENT_'.
"""
from rest_framework.permissions import BasePermission


class IsCEO(BasePermission):
    """
    Permite acceso solo a usuarios con role == 'CEO'.
    Usado en: ApproveRebateLiquidationView, CommissionRuleViewSet.
    """
    message = 'Solo el CEO puede realizar esta accion.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'role', None) == 'CEO'
        )


class IsCEOOrInternalAgent(BasePermission):
    """
    Permite acceso a CEO o a agentes internos (role empieza por 'AGENT_').
    Usado en: RebateProgramViewSet, RebateLedgerViewSet, ArtifactPolicyViewSet.
    """
    message = 'Acceso restringido a CEO o agentes internos.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        role = getattr(request.user, 'role', '') or ''
        return role == 'CEO' or role.startswith('AGENT_')


class IsClientUser(BasePermission):
    """
    Permite acceso solo a usuarios de tipo cliente (role empieza por 'CLIENT_').
    Usado en: RebateProgressPortalViewSet.
    """
    message = 'Acceso restringido a usuarios del portal de clientes.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        role = getattr(request.user, 'role', '') or ''
        return role.startswith('CLIENT_')
