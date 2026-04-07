"""
Sprint 8 S8-08/09/10 + Sprint 24 S24-05/07/09/11:
Endpoints Knowledge Pipeline con intent routing, visibility filter y logging estructurado.
Auth: JWT stateless.
"""
import json
import uuid
import logging
from datetime import timedelta

from django.db.models import Q
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils import timezone

from apps.knowledge.throttling import KnowledgeRateThrottle  # S24-04

logger = logging.getLogger(__name__)


def _get_redis():
    import redis
    r = redis.from_url(settings.CELERY_BROKER_URL, decode_responses=True)
    return r


def _authenticate_jwt(request):
    """Helper: autentica JWT, retorna (token_payload, error_response)."""
    from rest_framework_simplejwt.authentication import JWTStatelessUserAuthentication
    from rest_framework.exceptions import AuthenticationFailed
    auth = JWTStatelessUserAuthentication()
    try:
        result = auth.authenticate(request)
    except AuthenticationFailed as exc:
        return None, JsonResponse({'detail': str(exc)}, status=401)
    if result is None:
        return None, JsonResponse({'detail': 'Authentication required.'}, status=401)
    _, token = result
    return token, None


# S24-09: Filtro de visibilidad segun rol del usuario
def get_visibility_filter(user_role: str) -> list:
    if user_role.startswith('CLIENT_') or user_role == 'CLIENT':
        return ['PUBLIC', 'PARTNER_B2B']
    if user_role in ('CEO', 'INTERNAL', 'STAFF'):
        return ['PUBLIC', 'PARTNER_B2B', 'INTERNAL']
    return ['PUBLIC']


def _build_visibility_q(user_role: str) -> Q:
    allowed = get_visibility_filter(user_role)
    return Q(visibility__in=allowed)


@method_decorator(csrf_exempt, name='dispatch')
class AskView(View):
    """
    POST /api/knowledge/ask/
    S24-07: Refactorizado con intent routing (Ruta A / Ruta B),
    visibility filter S24-09, throttle S24-04, logging estructurado.
    """
    throttle_classes = [KnowledgeRateThrottle]  # S24-04

    def post(self, request):
        token, err = _authenticate_jwt(request)
        if err:
            return err

        token_permissions = token.get('permissions', [])
        ask_perms = {'ask_knowledge_ops', 'ask_knowledge_products', 'ask_knowledge_pricing'}
        if not ask_perms.intersection(set(token_permissions)):
            return JsonResponse({'detail': 'Permission denied. Requires ask_knowledge_*.'}, status=403)

        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'detail': 'Invalid JSON.'}, status=400)

        question = body.get('question', '').strip()
        if not question:
            return JsonResponse({'detail': 'question es requerida.'}, status=400)

        session_id     = body.get('session_id') or str(uuid.uuid4())
        user_id        = token.get('user_id')
        user_role      = token.get('role', '')
        expediente_id  = body.get('expediente_id')

        redis_key = f'kw:session:{user_id}:{session_id}'
        try:
            r = _get_redis()
            history_raw = r.get(redis_key)
            history = json.loads(history_raw) if history_raw else []
        except Exception as exc:
            logger.warning('S24-07 Redis read error: %s', exc)
            history = []

        try:
            from apps.knowledge.services.intent_classifier import classify_intent, IntentResult
            intent_result: IntentResult = classify_intent(question)
            intent = intent_result.intent
            confidence = intent_result.confidence
        except Exception as exc:
            logger.error('S24-10 intent_classifier error: %s', exc)
            intent = 'ESCALATE'
            confidence = 0.0

        logger.info(
            'S24-07 ask | user=%s role=%s intent=%s confidence=%.2f session=%s',
            user_id, user_role, intent, confidence, session_id
        )

        visibility_allowed = get_visibility_filter(user_role)

        RUTA_A_INTENTS = {'QUERY_PRODUCT', 'QUERY_OPERATIONS', 'ASK_CLARIFICATION'}
        RUTA_B_INTENTS = {'QUERY_EXPEDIENTE', 'DOWNLOAD_DOC', 'ESCALATE'}

        answer = ''
        source_chunks = []
        source_entities = []
        route_used = ''

        if intent in RUTA_A_INTENTS:
            route_used = 'A'
            try:
                import urllib.request as urlreq
                knowledge_url = getattr(settings, 'KNOWLEDGE_SERVICE_URL', 'http://mwt-knowledge:8001')
                internal_token = getattr(settings, 'KNOWLEDGE_INTERNAL_TOKEN', '')
                payload = json.dumps({
                    'question': question,
                    'history': history,
                    'permissions': token_permissions,
                    'user_id': user_id,
                    'session_id': session_id,
                    'visibility_filter': visibility_allowed,
                    'intent': intent,
                }).encode()
                req = urlreq.Request(
                    f'{knowledge_url}/internal/ask/',
                    data=payload,
                    headers={
                        'Content-Type': 'application/json',
                        'X-Internal-Token': internal_token,
                    },
                    method='POST',
                )
                with urlreq.urlopen(req, timeout=30) as resp:
                    resp_data = json.loads(resp.read().decode())
                answer = resp_data.get('answer', '').strip()
                source_chunks = resp_data.get('chunks_used', [])
            except Exception as exc:
                logger.error('S24-07 knowledge service error route_A: %s', exc)
                return JsonResponse({'detail': 'Knowledge service unavailable.'}, status=503)

        elif intent in RUTA_B_INTENTS:
            route_used = 'B'
            try:
                from apps.knowledge.services.orchestrator import orchestrate
                from django.contrib.auth import get_user_model
                User = get_user_model()
                db_user = User.objects.filter(id=user_id).first()
                orch_result = orchestrate(
                    intent=intent,
                    question=question,
                    user=db_user,
                    user_role=user_role,
                    expediente_id=expediente_id,
                    request=request,
                )
                answer = orch_result.get('answer', '')
                source_entities = orch_result.get('source_entities', [])
            except Exception as exc:
                logger.error('S24-11 orchestrator error route_B: %s', exc)
                return JsonResponse({'detail': 'Error procesando la solicitud.'}, status=500)

        if not answer:
            answer = 'No se encontraron resultados relevantes para esta pregunta.'

        try:
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
            from django.contrib.auth import get_user_model
            User = get_user_model()
            db_user = User.objects.filter(id=user_id).first()
            ConversationLog.objects.create(
                session_id=session_id,
                user=db_user,
                user_role=user_role,
                expediente_ref=expediente,
                question=question,
                answer=answer,
                chunks_used=source_chunks,
                retain_until=retain,
            )
        except Exception as exc:
            logger.error('S24-07 ConversationLog save error: %s', exc)

        history.append({'role': 'user', 'content': question})
        history.append({'role': 'assistant', 'content': answer})
        try:
            r.setex(redis_key, int(timedelta(minutes=30).total_seconds()), json.dumps(history))
        except Exception:
            pass

        return JsonResponse({
            'answer': answer,
            'session_id': session_id,
            'source_chunks': source_chunks,
            'source_entities': source_entities,
            'intent': intent,
            'route': route_used,
        })


@method_decorator(csrf_exempt, name='dispatch')
class SearchView(View):
    """
    POST /api/knowledge/search/
    S24-05 hotfix: RAG directo sin microservicio.
    Genera embedding del query via OpenAI y busca en knowledge_chunks via pgvector.
    Body: { "query": str, "top_k": int (default 5) }
    """

    def post(self, request):
        token, err = _authenticate_jwt(request)
        if err:
            return err

        token_permissions = [p.lower() for p in token.get('permissions', [])]
        ask_perms = {'ask_knowledge_ops', 'ask_knowledge_products', 'ask_knowledge_pricing'}
        if not ask_perms.intersection(set(token_permissions)):
            return JsonResponse({'detail': 'Permission denied.'}, status=403)

        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'detail': 'Invalid JSON.'}, status=400)

        query = body.get('query', '').strip()
        top_k = int(body.get('top_k', 5))
        if not query:
            return JsonResponse({'detail': 'query es requerida.'}, status=400)

        user_role = token.get('role', '')
        visibility_allowed = get_visibility_filter(user_role)
        visibility_sql = ', '.join(f"'{v}'" for v in visibility_allowed)

        # Generar embedding del query via OpenAI
        import os
        import openai
        api_key = os.environ.get('OPENAI_API_KEY') or getattr(settings, 'OPENAI_API_KEY', '')
        if not api_key:
            return JsonResponse({'detail': 'OPENAI_API_KEY no configurada.'}, status=500)

        try:
            client = openai.OpenAI(api_key=api_key)
            resp = client.embeddings.create(model='text-embedding-3-small', input=query)
            query_vec = resp.data[0].embedding
        except Exception as exc:
            logger.error('S24-05 embedding error: %s', exc)
            return JsonResponse({'detail': 'Error generando embedding.'}, status=500)

        # Busqueda por similitud coseno en pgvector
        from django.db import connection
        vec_str = '[' + ','.join(str(x) for x in query_vec) + ']'
        try:
            with connection.cursor() as cur:
                cur.execute(f"""
                    SELECT source_file, content, visibility,
                           1 - (embedding <=> %s::vector) AS score
                    FROM knowledge_chunks
                    WHERE visibility IN ({visibility_sql})
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """, [vec_str, vec_str, top_k])
                rows = cur.fetchall()
        except Exception as exc:
            logger.error('S24-05 pgvector query error: %s', exc)
            return JsonResponse({'detail': 'Error en busqueda vectorial.'}, status=500)

        results = [
            {
                'source_file': r[0],
                'content': r[1],
                'visibility': r[2],
                'score': round(float(r[3]), 4),
            }
            for r in rows
        ]

        logger.info('S24-05 search | user=%s top_k=%d results=%d', token.get('user_id'), top_k, len(results))
        return JsonResponse({'query': query, 'results': results, 'total': len(results)})


@method_decorator(csrf_exempt, name='dispatch')
class IndexKBView(View):
    """POST /api/knowledge/index/ — Solo CEO."""

    def post(self, request):
        token, err = _authenticate_jwt(request)
        if err:
            return err
        if token.get('role') != 'CEO':
            return JsonResponse({'detail': 'Solo el CEO puede re-indexar.'}, status=403)

        import urllib.request as urlreq
        knowledge_url = getattr(settings, 'KNOWLEDGE_SERVICE_URL', 'http://mwt-knowledge:8001')
        internal_token = getattr(settings, 'KNOWLEDGE_INTERNAL_TOKEN', '')
        req = urlreq.Request(
            f'{knowledge_url}/internal/index/',
            data=b'{}',
            headers={
                'Content-Type': 'application/json',
                'X-Internal-Token': internal_token,
            },
            method='POST',
        )
        try:
            with urlreq.urlopen(req, timeout=120) as resp:
                resp_data = json.loads(resp.read().decode())
        except Exception as exc:
            logger.error('knowledge index error: %s', exc)
            return JsonResponse({'detail': 'Knowledge service unavailable.'}, status=503)

        return JsonResponse(resp_data)


@method_decorator(csrf_exempt, name='dispatch')
class SessionListView(View):
    """GET /api/knowledge/sessions/ — JWT."""

    def get(self, request):
        token, err = _authenticate_jwt(request)
        if err:
            return err
        user_id = token.get('user_id')
        role    = token.get('role')

        filter_user_id = user_id
        if role == 'CEO' and request.GET.get('user_id'):
            filter_user_id = request.GET.get('user_id')

        from apps.knowledge.models import ConversationLog
        today = timezone.now().date()
        qs = (
            ConversationLog.objects
            .filter(user_id=filter_user_id)
            .filter(retain_until__gte=today)
            .values('session_id')
            .distinct()
            .order_by('session_id')
        )
        page      = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        sessions  = list(qs)
        total     = len(sessions)
        start     = (page - 1) * page_size
        return JsonResponse({
            'sessions': sessions[start:start + page_size],
            'total': total,
            'page': page,
            'page_size': page_size,
        })


@method_decorator(csrf_exempt, name='dispatch')
class SessionDetailView(View):
    """GET /api/knowledge/sessions/{session_id}/"""

    def get(self, request, session_id):
        token, err = _authenticate_jwt(request)
        if err:
            return err
        user_id = token.get('user_id')
        role    = token.get('role')

        from apps.knowledge.models import ConversationLog
        today = timezone.now().date()
        qs = ConversationLog.objects.filter(session_id=session_id, retain_until__gte=today)
        if role != 'CEO':
            qs = qs.filter(user_id=user_id)

        logs = list(qs.values(
            'id', 'session_id', 'user_id', 'user_role',
            'question', 'answer', 'chunks_used', 'created_at', 'retain_until'
        ))
        if not logs:
            return JsonResponse({'detail': 'Sesion no encontrada o expirada.'}, status=404)
        return JsonResponse({'session_id': session_id, 'logs': logs})
