"""
S9-P03 — CRUD endpoints para LegalEntity (Clientes).
GET    /api/core/clients/           → lista todos
POST   /api/core/clients/           → crear cliente
GET    /api/core/clients/{id}/      → detalle
PUT    /api/core/clients/{id}/      → actualizar completo
PATCH  /api/core/clients/{id}/      → actualizar parcial

Permiso requerido: manage_clients (rol CEO — S9-P03)
"""
import json

from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from apps.core.models import LegalEntity
from apps.users.decorators import require_permission


def _entity_dict(e):
    return {
        "id":          e.id,
        "name":        e.name,
        "tax_id":      getattr(e, "tax_id", None),
        "country":     getattr(e, "country", None),
        "entity_type": getattr(e, "entity_type", None),
        "is_active":   getattr(e, "is_active", True),
    }


@method_decorator(csrf_exempt, name="dispatch")
class ClientListCreateView(View):
    """GET + POST /api/core/clients/"""

    @method_decorator(require_permission("manage_clients"))
    def get(self, request):
        qs = LegalEntity.objects.order_by("name")
        return JsonResponse({"clients": [_entity_dict(e) for e in qs]})

    @method_decorator(require_permission("manage_clients"))
    def post(self, request):
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"detail": "JSON inv\u00e1lido."}, status=400)

        name = body.get("name", "").strip()
        if not name:
            return JsonResponse({"detail": "El campo 'name' es requerido."}, status=400)

        kwargs = {"name": name}
        for field in ("tax_id", "country", "entity_type"):
            if field in body:
                kwargs[field] = body[field]

        entity = LegalEntity.objects.create(**kwargs)
        return JsonResponse(_entity_dict(entity), status=201)


@method_decorator(csrf_exempt, name="dispatch")
class ClientDetailView(View):
    """GET + PUT + PATCH /api/core/clients/{client_id}/"""

    def _get_entity(self, client_id):
        try:
            return LegalEntity.objects.get(pk=client_id)
        except LegalEntity.DoesNotExist:
            return None

    @method_decorator(require_permission("manage_clients"))
    def get(self, request, client_id):
        e = self._get_entity(client_id)
        if not e:
            return JsonResponse({"detail": "Cliente no encontrado."}, status=404)
        return JsonResponse(_entity_dict(e))

    @method_decorator(require_permission("manage_clients"))
    def put(self, request, client_id):
        e = self._get_entity(client_id)
        if not e:
            return JsonResponse({"detail": "Cliente no encontrado."}, status=404)
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"detail": "JSON inv\u00e1lido."}, status=400)

        for field in ("name", "tax_id", "country", "entity_type", "is_active"):
            if field in body:
                setattr(e, field, body[field])
        e.save()
        return JsonResponse(_entity_dict(e))

    @method_decorator(require_permission("manage_clients"))
    def patch(self, request, client_id):
        """Partial update — misma lógica que PUT (campos opcionales)."""
        return self.put(request, client_id)
