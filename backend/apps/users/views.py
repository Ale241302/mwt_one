"""Sprint 8 S8-05: API Admin Usuarios — CRUD + Permisos.
Sprint 10 S10-01a: Edit (PUT/PATCH) + Delete (DELETE).
Auth: Session + MANAGE_USERS (Camino A).
"""
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json

from apps.core.models import LegalEntity
from .models import MWTUser, UserPermission, Permission, ROLE_PERMISSION_CEILING
from .decorators import require_permission


def _user_dict(user):
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'is_api_user': user.is_api_user,
        'legal_entity_id': user.legal_entity_id,
        'whatsapp_number': user.whatsapp_number,
        'is_active': user.is_active,
    }


@method_decorator(csrf_exempt, name='dispatch')
class UserListCreateView(View):
    """POST /api/admin/users/ | GET /api/admin/users/"""

    @method_decorator(require_permission('manage_users'))
    def get(self, request):
        users = MWTUser.objects.all().order_by('id')
        return JsonResponse({'users': [_user_dict(u) for u in users]})

    @method_decorator(require_permission('manage_users'))
    def post(self, request):
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'detail': 'Invalid JSON.'}, status=400)

        username = body.get('username')
        password = body.get('password')
        role     = body.get('role', 'INTERNAL')
        email    = body.get('email', '')
        legal_entity_id = body.get('legal_entity_id')
        whatsapp = body.get('whatsapp_number')
        is_api   = body.get('is_api_user', False)

        if not username or not password:
            return JsonResponse({'detail': 'username y password son requeridos.'}, status=400)

        if legal_entity_id:
            try:
                LegalEntity.objects.get(pk=legal_entity_id)
            except LegalEntity.DoesNotExist:
                return JsonResponse({'detail': 'LegalEntity no encontrada.'}, status=400)

        user = MWTUser.objects.create(
            username=username,
            password=make_password(password),
            email=email,
            role=role,
            legal_entity_id=legal_entity_id,
            whatsapp_number=whatsapp,
            is_api_user=is_api,
            created_by=request.user,
        )
        return JsonResponse(_user_dict(user), status=201)


@method_decorator(csrf_exempt, name='dispatch')
class UserDetailView(View):
    """GET /api/admin/users/{id}/
       PUT /api/admin/users/{id}/   — S10-01a Edit
       PATCH /api/admin/users/{id}/ — S10-01a Partial Edit
       DELETE /api/admin/users/{id}/ — S10-01a Delete
    """

    @method_decorator(require_permission('manage_users'))
    def get(self, request, user_id):
        try:
            user = MWTUser.objects.get(pk=user_id)
        except MWTUser.DoesNotExist:
            return JsonResponse({'detail': 'Usuario no encontrado.'}, status=404)
        return JsonResponse(_user_dict(user))

    @method_decorator(require_permission('manage_users'))
    def put(self, request, user_id):
        return self._update(request, user_id, partial=False)

    @method_decorator(require_permission('manage_users'))
    def patch(self, request, user_id):
        return self._update(request, user_id, partial=True)

    def _update(self, request, user_id, partial):
        try:
            user = MWTUser.objects.get(pk=user_id)
        except MWTUser.DoesNotExist:
            return JsonResponse({'detail': 'Usuario no encontrado.'}, status=404)

        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'detail': 'Invalid JSON.'}, status=400)

        # Prevent editing yourself via API (safety guard)
        if user.pk == request.user.pk and 'role' in body:
            return JsonResponse({'detail': 'No puedes cambiar tu propio rol.'}, status=400)

        if 'username' in body and body['username']:
            user.username = body['username']
        if 'email' in body:
            user.email = body.get('email', '')
        if 'role' in body and body['role']:
            user.role = body['role']
        if 'whatsapp_number' in body:
            user.whatsapp_number = body.get('whatsapp_number')
        if 'is_api_user' in body:
            user.is_api_user = bool(body['is_api_user'])
        if 'is_active' in body:
            user.is_active = bool(body['is_active'])
        if 'password' in body and body['password']:
            user.password = make_password(body['password'])
        if 'legal_entity_id' in body:
            legal_entity_id = body.get('legal_entity_id')
            if legal_entity_id:
                try:
                    LegalEntity.objects.get(pk=legal_entity_id)
                except LegalEntity.DoesNotExist:
                    return JsonResponse({'detail': 'LegalEntity no encontrada.'}, status=400)
            user.legal_entity_id = legal_entity_id

        user.save()
        return JsonResponse(_user_dict(user))

    @method_decorator(require_permission('manage_users'))
    def delete(self, request, user_id):
        try:
            user = MWTUser.objects.get(pk=user_id)
        except MWTUser.DoesNotExist:
            return JsonResponse({'detail': 'Usuario no encontrado.'}, status=404)

        if user.pk == request.user.pk:
            return JsonResponse({'detail': 'No puedes eliminar tu propio usuario.'}, status=400)

        # Guard: ensure at least one manage_users admin remains
        if user.permissions_set.filter(permission='manage_users').exists():
            other_count = (
                UserPermission.objects
                .filter(permission='manage_users')
                .exclude(user=user)
                .count()
            )
            if other_count == 0:
                return JsonResponse(
                    {'detail': 'cannot_delete_last_manage_users'},
                    status=400
                )

        user.delete()
        return JsonResponse({'detail': 'Usuario eliminado.'}, status=200)


@method_decorator(csrf_exempt, name='dispatch')
class UserPermissionsView(View):
    """GET /api/admin/users/{id}/permissions/
       PATCH /api/admin/users/{id}/permissions/
    """

    @method_decorator(require_permission('manage_users'))
    def get(self, request, user_id):
        try:
            user = MWTUser.objects.get(pk=user_id)
        except MWTUser.DoesNotExist:
            return JsonResponse({'detail': 'Usuario no encontrado.'}, status=404)
        perms = list(user.permissions_set.values_list('permission', flat=True))
        return JsonResponse({'user_id': user_id, 'permissions': perms})

    @method_decorator(require_permission('manage_users'))
    def patch(self, request, user_id):
        try:
            user = MWTUser.objects.get(pk=user_id)
        except MWTUser.DoesNotExist:
            return JsonResponse({'detail': 'Usuario no encontrado.'}, status=404)

        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'detail': 'Invalid JSON.'}, status=400)

        requested = set(body.get('permissions', []))
        ceiling = set(ROLE_PERMISSION_CEILING.get(user.role, []))
        accepted = list(requested & ceiling)
        rejected = list(requested - ceiling)

        if 'manage_users' not in accepted:
            other_manage_count = (
                UserPermission.objects
                .filter(permission='manage_users')
                .exclude(user=user)
                .count()
            )
            if other_manage_count == 0:
                return JsonResponse(
                    {'detail': 'cannot_remove_last_manage_users'},
                    status=400
                )

        with transaction.atomic():
            user.permissions_set.all().delete()
            for perm in accepted:
                UserPermission.objects.create(
                    user=user,
                    permission=perm,
                    granted_by=request.user,
                )

        return JsonResponse({
            'user_id': user_id,
            'permissions_applied': accepted,
            'permissions_rejected': rejected,
        })
