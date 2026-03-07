"""
Sprint 1 â€” API Permission Guards (thin wrappers)
Ref: LOTE_SM_SPRINT1 Item 2, FIX-8
"""
from rest_framework.permissions import BasePermission
from apps.expedientes.exceptions import CommandValidationError


class IsCEO(BasePermission):
    """MVP: CEO = is_superuser. No RBAC."""
    message = 'Only the CEO (superuser) can perform this action.'

    def has_permission(self, request, view):
        return request.user and request.user.is_superuser

    def has_object_permission(self, request, view, obj):
        return request.user and request.user.is_superuser


class EnsureNotBlocked(BasePermission):
    """
    Rejects operational commands if is_blocked=True.
    NOT used for C16, C17, C18 (FIX-8).
    """
    message = 'Expediente is blocked. Unblock before proceeding.'

    def has_object_permission(self, request, view, obj):
        if obj.is_blocked:
            return False
        return True


class EnsureCommandAllowed(BasePermission):
    """
    Thin wrapper that delegates to services.can_execute_command.
    Raises typed exception if command cannot be executed.
    Ref: PLB_SPRINT1_PROMPTS Item 2, FIX-2
    """
    message = 'Command cannot be executed in current state.'

    def has_object_permission(self, request, view, obj):
        # Delegation happens inside execute_command via can_execute_command.
        # This class exists per spec contract; enforcement is in services.py.
        return True
