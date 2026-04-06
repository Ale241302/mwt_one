"""
S23-05 — Resolvers de ArtifactPolicy.

resolve_artifact_policy(): DB primero → fallback a constante Python.
update_artifact_policy(): desactiva ANTES de crear, dentro de transaction.atomic().
MultipleObjectsReturned → EventLog(event_type='artifact_policy.integrity_error').
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from django.db import transaction

logger = logging.getLogger(__name__)


def resolve_artifact_policy(brand_slug: str) -> Dict[str, Any]:
    """
    S23-05: Resuelve la política de artefactos para una marca.

    Prioridad:
      1. BrandArtifactPolicyVersion activa en DB.
      2. Fallback a constante ARTIFACT_POLICY en apps/expedientes/services/artifact_policy.py

    Si hay múltiples versiones activas (integridad comprometida), emite
    EventLog(event_type='artifact_policy.integrity_error') y retorna la más reciente.
    """
    from apps.commercial.models import BrandArtifactPolicyVersion

    try:
        version = (
            BrandArtifactPolicyVersion.objects
            .filter(brand_id=brand_slug, is_active=True)
            .order_by('-version')
            .get()
        )
        return version.artifact_policy

    except BrandArtifactPolicyVersion.DoesNotExist:
        # Fallback a constante Python
        return _get_fallback_policy(brand_slug)

    except BrandArtifactPolicyVersion.MultipleObjectsReturned:
        # Error de integridad — emitir EventLog y usar la versión más reciente
        _emit_integrity_error(brand_slug)
        version = (
            BrandArtifactPolicyVersion.objects
            .filter(brand_id=brand_slug, is_active=True)
            .order_by('-version')
            .first()
        )
        return version.artifact_policy if version else _get_fallback_policy(brand_slug)


def update_artifact_policy(
    brand_slug: str,
    new_policy: Dict[str, Any],
    notes: str = '',
    changed_by=None,
) -> 'BrandArtifactPolicyVersion':
    """
    S23-05: Crea una nueva versión de la política de artefactos para la marca.

    Regla append-only:
      1. Desactiva la versión activa actual (ANTES de crear la nueva).
      2. Crea la nueva versión con is_active=True.
      3. Enlaza superseded_by en la versión anterior.
    Todo dentro de transaction.atomic() para no violar UniqueConstraint activa.
    """
    from apps.commercial.models import BrandArtifactPolicyVersion
    from apps.audit.models import ConfigChangeLog
    import json

    with transaction.atomic():
        # Paso 1: Desactivar versión activa actual
        current_active: Optional[BrandArtifactPolicyVersion] = (
            BrandArtifactPolicyVersion.objects
            .filter(brand_id=brand_slug, is_active=True)
            .order_by('-version')
            .first()
        )

        next_version_number = 1
        if current_active:
            next_version_number = current_active.version + 1
            current_active.is_active = False
            current_active.save(update_fields=['is_active', 'updated_at'])

        # Paso 2: Crear nueva versión activa
        new_version = BrandArtifactPolicyVersion.objects.create(
            brand_id=brand_slug,
            version=next_version_number,
            artifact_policy=new_policy,
            is_active=True,
            notes=notes,
        )

        # Paso 3: Enlazar superseded_by en la versión anterior
        if current_active:
            current_active.superseded_by = new_version
            current_active.save(update_fields=['superseded_by', 'updated_at'])

        # Registro de auditoría
        ConfigChangeLog.objects.create(
            user=changed_by,
            model_name='BrandArtifactPolicyVersion',
            record_id=str(new_version.id),
            action='create',
            changes={
                'brand': brand_slug,
                'version': next_version_number,
                'new_value': json.dumps(new_policy),
                'previous_version': current_active.version if current_active else None,
            },
        )

    return new_version


# ---------------------------------------------------------------------------
# Helpers privados
# ---------------------------------------------------------------------------

def _get_fallback_policy(brand_slug: str) -> Dict[str, Any]:
    """
    Fallback a la constante ARTIFACT_POLICY en expedientes.
    Si la constante es un dict por brand, intenta resolver para brand_slug.
    Si no, retorna la constante completa.
    """
    try:
        from apps.expedientes.services.artifact_policy import ARTIFACT_POLICY
        if isinstance(ARTIFACT_POLICY, dict):
            return ARTIFACT_POLICY.get(brand_slug, ARTIFACT_POLICY)
        return ARTIFACT_POLICY
    except ImportError:
        logger.warning(
            'artifact_policy fallback: no se pudo importar ARTIFACT_POLICY '
            'de apps.expedientes.services.artifact_policy'
        )
        return {}


def _emit_integrity_error(brand_slug: str) -> None:
    """Emite un EventLog de integridad cuando hay múltiples versiones activas."""
    try:
        from apps.audit.models import ConfigChangeLog
        ConfigChangeLog.objects.create(
            user=None,
            model_name='BrandArtifactPolicyVersion',
            record_id=brand_slug,
            action='integrity_error',
            changes={
                'event_type': 'artifact_policy.integrity_error',
                'brand': brand_slug,
                'detail': 'Multiple active BrandArtifactPolicyVersion found for brand.',
            },
        )
    except Exception as exc:  # noqa: BLE001
        logger.error('Failed to emit artifact_policy.integrity_error: %s', exc)
