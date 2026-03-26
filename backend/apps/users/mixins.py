"""Sprint 8 S8-04: Mixins class-based equivalentes a los decoradores."""
from django.http import JsonResponse
from rest_framework.exceptions import AuthenticationFailed


class PermissionRequiredMixin:
    """Camino A — Session. Usar en CBV bajo /api/admin/."""
    required_permission = None  # subclase debe definir

    def dispatch(self, request, *args, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return JsonResponse({'detail': 'Authentication required.'}, status=401)
        if not request.user.has_permission(self.required_permission):
            return JsonResponse(
                {'detail': 'Permission denied.', 'required': self.required_permission},
                status=403
            )
        return super().dispatch(request, *args, **kwargs)


class JWTPermissionRequiredMixin:
    """Camino B — JWT stateless. Usar en CBV bajo /api/knowledge/."""
    required_permission = None  # subclase debe definir

    def dispatch(self, request, *args, **kwargs):
        # Import diferido para evitar resolución temprana del modelo swappable
        from rest_framework_simplejwt.authentication import JWTStatelessUserAuthentication
        auth = JWTStatelessUserAuthentication()
        try:
            result = auth.authenticate(request)
        except AuthenticationFailed as exc:
            return JsonResponse({'detail': str(exc)}, status=401)
        if result is None:
            return JsonResponse({'detail': 'Authentication required.'}, status=401)
        user, token = result
        token_permissions = token.get('permissions', [])
        if self.required_permission not in token_permissions:
            return JsonResponse(
                {'detail': 'Permission denied.', 'required': self.required_permission},
                status=403
            )
        request.jwt_user = user
        request.jwt_token = token
        return super().dispatch(request, *args, **kwargs)
