"""
S24-11: Orchestrator para Ruta B del Knowledge Pipeline.

Maneja intents que requieren datos live de la DB:
  QUERY_EXPEDIENTE -> ORM Django, solo expedientes del usuario
  DOWNLOAD_DOC     -> Signed URL MinIO (reutiliza logica S24-05)
  ESCALATE         -> Alerta al CEO, SIN respuesta automatica al cliente
"""
from __future__ import annotations

import logging
from typing import Optional, Any

from django.utils import timezone

logger = logging.getLogger(__name__)


def orchestrate(
    intent: str,
    question: str,
    user: Any,
    user_role: str,
    expediente_id: Optional[str | int] = None,
    request: Any = None,
) -> dict:
    """
    Orquesta la respuesta segun intent de Ruta B.

    Returns:
        dict con claves:
          - answer (str)
          - source_entities (list)
          - escalated (bool, opcional)
    """
    if intent == 'QUERY_EXPEDIENTE':
        return _handle_query_expediente(user, user_role, expediente_id, question)
    elif intent == 'DOWNLOAD_DOC':
        return _handle_download_doc(user, expediente_id, request)
    elif intent == 'ESCALATE':
        return _handle_escalate(user, user_role, question)
    else:
        logger.warning('S24-11 orchestrator: intent desconocido=%s -> escalate', intent)
        return _handle_escalate(user, user_role, question)


# ---------------------------------------------------------------------------
# QUERY_EXPEDIENTE — datos live del ORM
# ---------------------------------------------------------------------------
def _handle_query_expediente(
    user: Any,
    user_role: str,
    expediente_id: Optional[str | int],
    question: str,
) -> dict:
    """
    Consulta expedientes del usuario. Solo retorna expedientes propios.
    CEO e INTERNAL pueden ver todos.
    """
    try:
        from apps.expedientes.models import Expediente

        if user_role in ('CEO', 'INTERNAL', 'STAFF'):
            qs = Expediente.objects.all()
        else:
            # CLIENT_* solo ve sus expedientes
            qs = Expediente.objects.filter(cliente=user)

        if expediente_id:
            qs = qs.filter(pk=expediente_id)

        # Limitar a 10 resultados para respuesta
        expedientes = list(
            qs.order_by('-created_at')[:10].values(
                'id', 'referencia', 'estado', 'created_at', 'updated_at'
            )
        )

        if not expedientes:
            answer = (
                'No encontre expedientes asociados a tu cuenta para esa consulta. '
                'Si crees que es un error, contacta a nuestro equipo.'
            )
            return {'answer': answer, 'source_entities': []}

        # Formatear respuesta
        lines = []
        for exp in expedientes:
            estado = exp.get('estado', 'Sin estado')
            ref    = exp.get('referencia', str(exp['id']))
            fecha  = str(exp.get('updated_at', exp.get('created_at', '')))[:10]
            lines.append(f'- **{ref}**: {estado} (actualizado: {fecha})')

        answer = 'Aqui estan tus expedientes:\n' + '\n'.join(lines)
        logger.info(
            'S24-11 QUERY_EXPEDIENTE user=%s role=%s found=%d',
            getattr(user, 'id', None), user_role, len(expedientes)
        )
        return {'answer': answer, 'source_entities': expedientes}

    except Exception as exc:
        logger.error('S24-11 _handle_query_expediente error: %s', exc)
        return {
            'answer': 'No fue posible consultar tus expedientes en este momento.',
            'source_entities': [],
        }


# ---------------------------------------------------------------------------
# DOWNLOAD_DOC — Signed URL MinIO
# ---------------------------------------------------------------------------
def _handle_download_doc(
    user: Any,
    expediente_id: Optional[str | int],
    request: Any,
) -> dict:
    """
    Genera una signed URL de MinIO para el documento solicitado.
    Verifica que el usuario sea el propietario del expediente.
    Registra la emision en EventLog (S24-05).
    """
    if not expediente_id:
        return {
            'answer': (
                'Para descargar un documento necesito que me indiques '
                'el numero de expediente o referencia.'
            ),
            'source_entities': [],
        }

    try:
        from apps.expedientes.models import Expediente
        from django.conf import settings
        from minio import Minio
        from minio.error import S3Error
        from datetime import timedelta

        # Verificar propiedad (S24-05)
        try:
            if hasattr(user, 'role') and user.role in ('CEO', 'INTERNAL', 'STAFF'):
                expediente = Expediente.objects.get(pk=expediente_id)
            else:
                expediente = Expediente.objects.get(pk=expediente_id, cliente=user)
        except Expediente.DoesNotExist:
            logger.warning(
                'S24-11 DOWNLOAD_DOC: user=%s no owner of expediente=%s',
                getattr(user, 'id', None), expediente_id
            )
            return {
                'answer': 'No tienes permiso para acceder a ese documento.',
                'source_entities': [],
            }

        # Buscar el artifact principal del expediente
        object_name = None
        try:
            from apps.expedientes.models import ExpedienteArtifact
            artifact = ExpedienteArtifact.objects.filter(
                expediente=expediente
            ).order_by('-created_at').first()
            if artifact:
                object_name = artifact.minio_key
        except Exception:
            pass

        if not object_name:
            return {
                'answer': (
                    f'No encontre documentos adjuntos para el expediente '
                    f'{getattr(expediente, "referencia", expediente_id)}.'
                ),
                'source_entities': [],
            }

        # Generar presigned URL TTL 15 min (S24-05)
        client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        url = client.presigned_get_object(
            bucket_name=settings.MINIO_BUCKET_NAME,
            object_name=object_name,
            expires=timedelta(minutes=15),
        )

        # Registrar emision en EventLog (S24-05)
        try:
            from apps.audit.models import EventLog
            ip = (
                request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
                or request.META.get('REMOTE_ADDR', '')
            ) if request else ''
            EventLog.objects.create(
                actor=user,
                event_type='SIGNED_URL_ISSUED',
                payload={
                    'artifact_key': object_name,
                    'expediente_id': str(expediente.id),
                    'ip': ip,
                    'timestamp': timezone.now().isoformat(),
                }
            )
        except Exception as log_exc:
            logger.warning('S24-11 EventLog write error: %s', log_exc)

        logger.info(
            'S24-11 DOWNLOAD_DOC signed URL issued: user=%s expediente=%s',
            getattr(user, 'id', None), expediente_id
        )
        return {
            'answer': (
                f'Aqui esta el enlace de descarga (valido por 15 minutos):\n{url}'
            ),
            'source_entities': [{'expediente_id': str(expediente_id), 'url': url}],
        }

    except Exception as exc:
        logger.error('S24-11 _handle_download_doc error: %s', exc)
        return {
            'answer': 'No fue posible generar el documento en este momento.',
            'source_entities': [],
        }


# ---------------------------------------------------------------------------
# ESCALATE — Alerta al CEO, SIN respuesta automatica
# ---------------------------------------------------------------------------
def _handle_escalate(user: Any, user_role: str, question: str) -> dict:
    """
    Registra una alerta de escalacion para el CEO.
    NO genera respuesta automatica al cliente.
    """
    try:
        from apps.audit.models import EventLog
        EventLog.objects.create(
            actor=user,
            event_type='KNOWLEDGE_ESCALATION',
            payload={
                'user_role': user_role,
                'question_snippet': question[:200],
                'timestamp': timezone.now().isoformat(),
            }
        )
        logger.warning(
            'S24-11 ESCALATE: user=%s role=%s question="%s"',
            getattr(user, 'id', None), user_role, question[:80]
        )
    except Exception as exc:
        logger.error('S24-11 _handle_escalate EventLog error: %s', exc)

    return {
        'answer': (
            'Tu consulta ha sido escalada a nuestro equipo. '
            'Un agente se comunicara contigo a la brevedad.'
        ),
        'source_entities': [],
        'escalated': True,
    }
