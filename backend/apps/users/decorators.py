"""Sprint 8 S8-04: Decoradores de permiso.
Camino A: Session  → /api/admin/
Camino B: JWT      → /api/knowledge/
"""
from functools import wraps
from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTStatelessUserAuthentication
from rest_framework.exceptions import AuthenticationFailed


def require_permission(permission):
    """Camino A — Session. Verifica permiso contra DB."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user or not request.user.is_authenticated:
                return JsonResponse({'detail': 'Authentication required.'}, status=401)
            if not request.user.has_permission(permission):
                return JsonResponse({'detail': 'Permission denied.', 'required': permission}, status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_permission_jwt(permission):
    """Camino B — JWT stateless. Lee permisos directamente del token, sin DB lookup."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            auth = JWTStatelessUserAuthentication()
            try:
                result = auth.authenticate(request)
            except AuthenticationFailed as exc:
                return JsonResponse({'detail': str(exc)}, status=401)
            if result is None:
                return JsonResponse({'detail': 'Authentication required.'}, status=401)
            user, token = result
            # Leer permisos del payload JWT (sin DB)
            token_permissions = token.get('permissions', [])
            if permission not in token_permissions:
                return JsonResponse({'detail': 'Permission denied.', 'required': permission}, status=403)
            request.jwt_user = user
            request.jwt_token = token
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
