"""
S21 — Admin views para control de estado y política de artefactos.

Endpoints (todos requieren is_superuser):
  POST /api/expedientes/{pk}/admin/advance-state/        → avanzar estado lógico
  POST /api/expedientes/{pk}/admin/revert-state/         → retroceder estado lógico
  POST /api/expedientes/{pk}/admin/policy/add-artifact/  → agregar artefacto a un estado
  POST /api/expedientes/{pk}/admin/policy/remove-artifact/ → quitar artefacto de un estado

Notas de diseño:
  - Avanzar/retroceder sigue el orden canónico CANONICAL_ADVANCE_ORDER.
  - CANCELADO y CERRADO son estados terminales; no se avanza desde ellos.
  - custom_artifact_policy persiste en la DB y se aplica en resolve_artifact_policy().
"""
from __future__ import annotations

from django.db import transaction
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.expedientes.models import Expediente, EventLog
from apps.expedientes.enums_exp import AggregateType
from apps.expedientes.services.artifact_policy import ALL_KNOWN_ARTIFACTS
import uuid as _uuid


# ---------------------------------------------------------------------------
# Permiso: solo superusuarios (CEO)
# ---------------------------------------------------------------------------
class IsSuperuser(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_superuser


# ---------------------------------------------------------------------------
# Orden canónico de estados (flujo lineal, sin terminales)
# ---------------------------------------------------------------------------
CANONICAL_ADVANCE_ORDER: list[str] = [
    'REGISTRO',
    'PRODUCCION',
    'PREPARACION',
    'DESPACHO',
    'TRANSITO',
    'EN_DESTINO',
    'CERRADO',
]

TERMINAL_STATES: set[str] = {'CERRADO', 'CANCELADO'}


def _get_expediente(pk):
    try:
        return Expediente.objects.get(pk=pk)
    except Expediente.DoesNotExist:
        return None


# ---------------------------------------------------------------------------
# AdvanceStateView
# ---------------------------------------------------------------------------
class AdvanceStateView(APIView):
    """
    POST /api/expedientes/{pk}/admin/advance-state/
    Avanza el expediente al siguiente estado en CANONICAL_ADVANCE_ORDER.
    Solo disponible para superusers (is_superuser=True).
    """
    permission_classes = [IsSuperuser]

    def post(self, request, pk):
        exp = _get_expediente(pk)
        if not exp:
            return Response({'detail': 'Expediente no encontrado.'}, status=404)

        current = exp.status
        if current in TERMINAL_STATES:
            return Response(
                {'detail': f'El expediente está en estado terminal ({current}). No se puede avanzar.'},
                status=400,
            )

        if current not in CANONICAL_ADVANCE_ORDER:
            return Response(
                {'detail': f'Estado desconocido: {current}. No se puede avanzar automáticamente.'},
                status=400,
            )

        idx = CANONICAL_ADVANCE_ORDER.index(current)
        if idx >= len(CANONICAL_ADVANCE_ORDER) - 1:
            return Response(
                {'detail': 'El expediente ya está en el último estado avanzable.'},
                status=400,
            )

        new_state = CANONICAL_ADVANCE_ORDER[idx + 1]

        with transaction.atomic():
            exp.status = new_state
            exp.save(update_fields=['status'])

            EventLog.objects.create(
                event_type='admin.advance_state',
                aggregate_type=AggregateType.EXPEDIENTE,
                aggregate_id=exp.expediente_id,
                payload={
                    'old_state': current,
                    'new_state': new_state,
                    'by': request.user.email,
                    'reason': 'Admin manual advance',
                },
                occurred_at=timezone.now(),
                emitted_by=f'S21:AdvanceStateView:{request.user.email}',
                correlation_id=_uuid.uuid4(),
            )

        return Response({
            'previous_state': current,
            'new_state': new_state,
            'detail': f'Estado avanzado de {current} a {new_state}.',
        })


# ---------------------------------------------------------------------------
# RevertStateView
# ---------------------------------------------------------------------------
class RevertStateView(APIView):
    """
    POST /api/expedientes/{pk}/admin/revert-state/
    Retrocede el expediente al estado anterior en CANONICAL_ADVANCE_ORDER.
    Solo disponible para superusers.
    """
    permission_classes = [IsSuperuser]

    def post(self, request, pk):
        exp = _get_expediente(pk)
        if not exp:
            return Response({'detail': 'Expediente no encontrado.'}, status=404)

        current = exp.status

        if current == 'CANCELADO':
            return Response(
                {'detail': 'No se puede retroceder un expediente CANCELADO.'},
                status=400,
            )

        if current not in CANONICAL_ADVANCE_ORDER:
            return Response(
                {'detail': f'Estado desconocido: {current}. No se puede retroceder automáticamente.'},
                status=400,
            )

        idx = CANONICAL_ADVANCE_ORDER.index(current)
        if idx == 0:
            return Response(
                {'detail': 'El expediente ya está en el primer estado. No se puede retroceder más.'},
                status=400,
            )

        new_state = CANONICAL_ADVANCE_ORDER[idx - 1]

        with transaction.atomic():
            exp.status = new_state
            exp.save(update_fields=['status'])

            EventLog.objects.create(
                event_type='admin.revert_state',
                aggregate_type=AggregateType.EXPEDIENTE,
                aggregate_id=exp.expediente_id,
                payload={
                    'old_state': current,
                    'new_state': new_state,
                    'by': request.user.email,
                    'reason': 'Admin manual revert',
                },
                occurred_at=timezone.now(),
                emitted_by=f'S21:RevertStateView:{request.user.email}',
                correlation_id=_uuid.uuid4(),
            )

        return Response({
            'previous_state': current,
            'new_state': new_state,
            'detail': f'Estado revertido de {current} a {new_state}.',
        })


# ---------------------------------------------------------------------------
# AddArtifactToPolicyView
# ---------------------------------------------------------------------------
class AddArtifactToPolicyView(APIView):
    """
    POST /api/expedientes/{pk}/admin/policy/add-artifact/
    Payload: { "state": "PRODUCCION", "artifact_type": "ART-19" }

    Agrega un tipo de artefacto al custom_artifact_policy del expediente.
    El artefacto aparecerá en la policy resuelta como opcional.
    """
    permission_classes = [IsSuperuser]

    def post(self, request, pk):
        exp = _get_expediente(pk)
        if not exp:
            return Response({'detail': 'Expediente no encontrado.'}, status=404)

        state = request.data.get('state', '').strip().upper()
        art_type = request.data.get('artifact_type', '').strip().upper()

        if not state:
            return Response({'detail': 'El campo "state" es requerido.'}, status=400)
        if not art_type:
            return Response({'detail': 'El campo "artifact_type" es requerido.'}, status=400)

        # Permitir cualquier artefacto (como números o IDs dinámicos de Builder API)

        custom = dict(exp.custom_artifact_policy or {})
        state_ops = dict(custom.get(state, {}))
        adds = list(state_ops.get('add', []))
        removes = list(state_ops.get('remove', []))

        if art_type in adds:
            return Response({
                'detail': f'{art_type} ya está en los overrides de {state}.',
                'custom_artifact_policy': custom,
            })

        # Si estaba en remove previamente, quitarlo de remove
        if art_type in removes:
            removes.remove(art_type)

        adds.append(art_type)
        state_ops['add'] = adds
        if removes:
            state_ops['remove'] = removes
        elif 'remove' in state_ops:
            del state_ops['remove']

        custom[state] = state_ops

        exp.custom_artifact_policy = custom
        exp.save(update_fields=['custom_artifact_policy'])

        return Response({
            'detail': f'{art_type} agregado a la política del estado {state}.',
            'custom_artifact_policy': custom,
        })


# ---------------------------------------------------------------------------
# RemoveArtifactFromPolicyView
# ---------------------------------------------------------------------------
class RemoveArtifactFromPolicyView(APIView):
    """
    POST /api/expedientes/{pk}/admin/policy/remove-artifact/
    Payload: { "state": "PRODUCCION", "artifact_type": "ART-06" }

    Elimina un tipo de artefacto del estado dado (tanto de la base como de los adds).
    El artefacto desaparecerá de la policy resuelta.
    """
    permission_classes = [IsSuperuser]

    def post(self, request, pk):
        exp = _get_expediente(pk)
        if not exp:
            return Response({'detail': 'Expediente no encontrado.'}, status=404)

        state = request.data.get('state', '').strip().upper()
        art_type = request.data.get('artifact_type', '').strip().upper()

        if not state:
            return Response({'detail': 'El campo "state" es requerido.'}, status=400)
        if not art_type:
            return Response({'detail': 'El campo "artifact_type" es requerido.'}, status=400)


        custom = dict(exp.custom_artifact_policy or {})
        state_ops = dict(custom.get(state, {}))
        adds = list(state_ops.get('add', []))
        removes = list(state_ops.get('remove', []))

        # Si estaba en "add", simplemente lo quitamos de ahí (no necesita ir a remove)
        if art_type in adds:
            adds.remove(art_type)
        elif art_type not in removes:
            removes.append(art_type)

        if adds:
            state_ops['add'] = adds
        elif 'add' in state_ops:
            del state_ops['add']

        if removes:
            state_ops['remove'] = removes
        elif 'remove' in state_ops:
            del state_ops['remove']

        if state_ops:
            custom[state] = state_ops
        elif state in custom:
            del custom[state]

        exp.custom_artifact_policy = custom
        exp.save(update_fields=['custom_artifact_policy'])

        return Response({
            'detail': f'{art_type} removido de la política del estado {state}.',
            'custom_artifact_policy': custom,
        })
