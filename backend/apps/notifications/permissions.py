"""
S26: Permisos para el sistema de notificaciones.
IsCEO: solo usuarios con role='CEO' o is_superuser pueden acceder.
"""
from rest_framework.permissions import BasePermission


class IsCEO(BasePermission):
    """
    Permite acceso solo a usuarios con role CEO o superusers.
    Compatible con el patrón de permisos del codebase MWT.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        role = getattr(request.user, 'role', None)
        return role == 'CEO'
