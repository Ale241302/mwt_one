"""Sprint 8 S8-08/09/10: Endpoints Knowledge Container.
Auth: JWT stateless (Camino B). No DB lookup.
D-09: expediente BLOQUEADO — /ask/ funciona normalmente.
"""
import json
import uuid
import logging
from datetime import timedelta

from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def _get_redis():
    import redis
    r = redis.from_url(settings.CELERY_BROKER_URL, decode_responses=True)
    return r


@method_decorator(csrf_exempt, name='dispatch')
class AskView(View):
    """POST /api/knowledge/ask/
    Auth: JWT + cualquiera de ask_knowledge_ops | ask_knowledge_products | ask_knowledge_pricing
    """

    def post(self, request):
        # --- 1. Autenticar JWT + permiso ask_knowledge_* ---
        from rest_framework_simplejwt.authentication import JWTStatelessUserAuthentication
        from rest_framework.exceptions import AuthenticationFailed
        auth = JWTStatelessUserAuthentication()
        try:
            result = auth.authenticate(request)
        except AuthenticationFailed as exc:
            return JsonResponse({'detail': str(exc)}, status=401)
        if result is None:
            return JsonResponse({'detail': 'Authentication required.'}, status=401)
        _, token = result
        token_permissions = token.get('permissions', [])
        ask_perms = {'ask_knowledge_ops', 'ask_knowledge_products', 'ask_knowledge_pricing'}
        if not ask_perms.intersection(set(token_permissions)):
            return JsonResponse({'detail': 'Permission denied. Requires ask_knowledge_*.', }, status=403)

        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'detail': 'Invalid JSON.'}, status=400)

        question = body.get('question', '').strip()
        if not question:
            return JsonResponse({'detail': 'question es requerida.'}, status=400)

        session_id = body.get('session_id') or str(uuid.uuid4())
        user_id = token.get('user_id')
        user_role = token.get('role', '')
        expediente_id = body.get('expediente_id')

        # --- 2. Recuperar historial multi-turn de Redis (prefix kw:) ---
        redis_key = f'kw:session:{user_id}:{session_id}'
        try:
            r = _get_redis()
            history_raw = r.get(redis_key)
            history = json.loads(history_raw) if history_raw else []
        except Exception:
            history = []

        # --- 3-6. Llamar al mwt-knowledge service ---
        import urllib.request
        knowledge_url = getattr(settings, 'KNOWLEDGE_SERVICE_URL', 'http://mwt-knowledge:8001')
        internal_token = getattr(settings, 'KNOWLEDGE_INTERNAL_TOKEN', '')
        payload = json.dumps({
            'question': question,
            'history': history,
            'permissions': token_permissions,
            'user_id': user_id,
            'session_id': session_id,
        }).encode()
        req = urllib.request.Request(
            f'{knowledge_url}/internal/ask/',
            data=payload,
            headers={
                'Content-Type': 'application/json',
                'X-Internal-Token': internal_token,
            },
            method='POST',
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                resp_data = json.loads(resp.read().decode())
        except Exception as exc:
            logger.error('knowledge service error: %s', exc)
            return JsonResponse({'detail': 'Knowledge service unavailable.'}, status=503)

        answer = resp_data.get('answer', '').strip()
        chunks_used = resp_data.get('chunks_used', [])

        if not answer:
            answer = "No se encontraron resultados relevantes en el Knowledge Base para esta pregunta."

        # --- 7. Guardar ConversationLog ---
        from apps.knowledge.models import ConversationLog
        from apps.knowledge.utils import calculate_retention
        from apps.expedientes.models import Expediente

        expediente = None
        if expediente_id:
            try:
                expediente = Expediente.objects.get(pk=expediente_id)
            except Expediente.DoesNotExist:
                pass

        retain = calculate_retention(expediente=expediente)
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            db_user = User.objects.filter(id=user_id).first()
        except Exception:
            db_user = None

        ConversationLog.objects.create(
            session_id=session_id,
            user=db_user,
            user_role=user_role,
            expediente_ref=expediente,
            question=question,
            answer=answer,
            chunks_used=chunks_used,
            retain_until=retain,
        )

        # --- 8. Actualizar Redis TTL 30min ---
        history.append({'role': 'user', 'content': question})
        history.append({'role': 'assistant', 'content': answer})
        try:
            r.setex(redis_key, int(timedelta(minutes=30).total_seconds()), json.dumps(history))
        except Exception:
            pass

        return JsonResponse({'answer': answer, 'session_id': session_id, 'chunks_used': chunks_used})


@method_decorator(csrf_exempt, name='dispatch')
class IndexKBView(View):
    """POST /api/knowledge/index/ — Solo CEO (JWT + role=CEO)."""

    def post(self, request):
        from rest_framework_simplejwt.authentication import JWTStatelessUserAuthentication
        from rest_framework.exceptions import AuthenticationFailed
        auth = JWTStatelessUserAuthentication()
        try:
            result = auth.authenticate(request)
        except AuthenticationFailed as exc:
            return JsonResponse({'detail': str(exc)}, status=401)
        if result is None:
            return JsonResponse({'detail': 'Authentication required.'}, status=401)
        _, token = result
        if token.get('role') != 'CEO':
            return JsonResponse({'detail': 'Solo el CEO puede re-indexar.'}, status=403)

        import urllib.request
        knowledge_url = getattr(settings, 'KNOWLEDGE_SERVICE_URL', 'http://mwt-knowledge:8001')
        internal_token = getattr(settings, 'KNOWLEDGE_INTERNAL_TOKEN', '')
        req = urllib.request.Request(
            f'{knowledge_url}/internal/index/',
            data=b'{}',
            headers={
                'Content-Type': 'application/json',
                'X-Internal-Token': internal_token,
            },
            method='POST',
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                resp_data = json.loads(resp.read().decode())
        except Exception as exc:
            logger.error('knowledge index error: %s', exc)
            return JsonResponse({'detail': 'Knowledge service unavailable.'}, status=503)

        return JsonResponse(resp_data)


@method_decorator(csrf_exempt, name='dispatch')
class SessionListView(View):
    """GET /api/knowledge/sessions/ — JWT. CEO puede filtrar por ?user_id=."""

    def get(self, request):
        from rest_framework_simplejwt.authentication import JWTStatelessUserAuthentication
        from rest_framework.exceptions import AuthenticationFailed
        from apps.knowledge.models import ConversationLog
        auth = JWTStatelessUserAuthentication()
        try:
            result = auth.authenticate(request)
        except AuthenticationFailed as exc:
            return JsonResponse({'detail': str(exc)}, status=401)
        if result is None:
            return JsonResponse({'detail': 'Authentication required.'}, status=401)
        _, token = result
        user_id = token.get('user_id')
        role    = token.get('role')

        filter_user_id = user_id
        if role == 'CEO' and request.GET.get('user_id'):
            filter_user_id = request.GET.get('user_id')

        from django.utils import timezone
        today = timezone.now().date()
        qs = (
            ConversationLog.objects
            .filter(user_id=filter_user_id)
            .filter(retain_until__gte=today)
            .values('session_id')
            .distinct()
            .order_by('session_id')
        )

        # Paginación simple
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        sessions = list(qs)
        total = len(sessions)
        start = (page - 1) * page_size
        page_sessions = sessions[start:start + page_size]

        return JsonResponse({
            'sessions': page_sessions,
            'total': total,
            'page': page,
            'page_size': page_size,
        })


@method_decorator(csrf_exempt, name='dispatch')
class SessionDetailView(View):
    """GET /api/knowledge/sessions/{session_id}/"""

    def get(self, request, session_id):
        from rest_framework_simplejwt.authentication import JWTStatelessUserAuthentication
        from rest_framework.exceptions import AuthenticationFailed
        from apps.knowledge.models import ConversationLog
        auth = JWTStatelessUserAuthentication()
        try:
            result = auth.authenticate(request)
        except AuthenticationFailed as exc:
            return JsonResponse({'detail': str(exc)}, status=401)
        if result is None:
            return JsonResponse({'detail': 'Authentication required.'}, status=401)
        _, token = result
        user_id = token.get('user_id')
        role    = token.get('role')

        from django.utils import timezone
        today = timezone.now().date()
        qs = ConversationLog.objects.filter(session_id=session_id, retain_until__gte=today)
        if role != 'CEO':
            qs = qs.filter(user_id=user_id)

        logs = list(qs.values(
            'id', 'session_id', 'user_id', 'user_role',
            'question', 'answer', 'chunks_used', 'created_at', 'retain_until'
        ))
        if not logs:
            return JsonResponse({'detail': 'Sesión no encontrada o expirada.'}, status=404)
        return JsonResponse({'session_id': session_id, 'logs': logs})
