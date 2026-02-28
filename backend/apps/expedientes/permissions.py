"""
Sprint 1 — API Permission Guards (thin wrappers)
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
