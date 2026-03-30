# S20-10 — change_proforma_mode() con void automático
# Fuente única para cambio de modo de proforma con void de artefactos.
# NUNCA duplicar void_map ni BRAND_ALLOWED_MODES aquí; se importan desde artifact_policy.

from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.expedientes.services.artifact_policy import BRAND_ALLOWED_MODES

VALID_MODES = ('mode_b', 'mode_c', 'default')

# Artefactos a void según la transición de modo
void_map: dict[tuple[str, str], str] = {
    ('mode_b', 'mode_c'): 'ART-10',
    ('mode_c', 'mode_b'): 'ART-09',
}


def change_proforma_mode(
    proforma,
    new_mode: str,
    confirm_void: bool = False,
    user=None,
) -> dict:
    """
    Cambia el modo de una proforma (ART-02), con void automático de artefactos
    afectados según void_map.

    Flujo:
    1. Validaciones rápidas ANTES del lock (falla rápido)
    2. transaction.atomic() + select_for_update() en proforma, expediente y artefactos
    3. Re-fetch old_mode DENTRO del lock (evita stale reads)
    4. Si old_mode == new_mode → early return dentro del lock
    5. Sin confirm_void → retorna preview
    6. Con confirm_void → void + cambio de mode + EventLog

    Returns:
        dict con claves: changed, message, voided_artifacts (preview o ejecutado)
    """
    from apps.expedientes.models import ArtifactInstance, EventLog
    from apps.expedientes.enums_exp import AggregateType
    import uuid

    # ── 1. Validaciones rápidas (antes del lock) ──────────────────────────────
    if new_mode not in VALID_MODES:
        raise ValueError(f"Modo inválido: '{new_mode}'. Válidos: {VALID_MODES}")

    expediente = proforma.expediente
    brand_slug: str = ''
    try:
        brand_slug = expediente.brand.slug
    except Exception:
        pass

    if not brand_slug or brand_slug not in BRAND_ALLOWED_MODES:
        raise ValueError(
            f"La brand '{brand_slug}' no está configurada en BRAND_ALLOWED_MODES."
        )

    allowed = BRAND_ALLOWED_MODES[brand_slug]
    if new_mode not in allowed:
        raise ValueError(
            f"Modo '{new_mode}' no permitido para brand '{brand_slug}'. "
            f"Permitidos: {allowed}"
        )

    # ── 2. Lock atómico ───────────────────────────────────────────────────────
    with transaction.atomic():
        # Re-fetch con lock para leer old_mode real (no stale)
        pf_locked = (
            ArtifactInstance.objects
            .select_for_update(of=('self',))
            .get(pk=proforma.pk)
        )
        exp_locked = (
            expediente.__class__.objects
            .select_for_update(of=('self',))
            .get(pk=expediente.pk)
        )

        old_mode: str = pf_locked.payload.get('mode', '')

        # ── 3. Early return si mismo modo (dentro del lock) ───────────────────
        if old_mode == new_mode:
            return {'changed': False, 'message': 'Mismo modo'}

        # ── 4. Buscar artefactos a void ───────────────────────────────────────
        art_type_to_void = void_map.get((old_mode, new_mode))
        artifacts_to_void = []

        if art_type_to_void:
            artifacts_to_void = list(
                ArtifactInstance.objects
                .select_for_update(of=('self',))
                .filter(
                    expediente=exp_locked,
                    artifact_type=art_type_to_void,
                    parent_proforma=pf_locked,
                )
                .exclude(status='VOIDED')
            )

        # ── 5. Preview si confirm_void=False y hay artefactos afectados ───────
        if artifacts_to_void and not confirm_void:
            return {
                'changed': False,
                'message': 'Preview: confirma para ejecutar el void',
                'preview': True,
                'old_mode': old_mode,
                'new_mode': new_mode,
                'voided_artifacts': [
                    {'artifact_id': str(a.artifact_id), 'artifact_type': a.artifact_type}
                    for a in artifacts_to_void
                ],
            }

        # ── 6. Ejecutar void + cambio de mode ─────────────────────────────────
        voided_ids = []
        now = timezone.now()

        for art in artifacts_to_void:
            art.status = 'VOIDED'
            art.payload = {
                **art.payload,
                'voided_at': now.isoformat(),
                'voided_reason': f'change_proforma_mode: {old_mode}→{new_mode}',
            }
            art.save(update_fields=['status', 'payload'])
            voided_ids.append(str(art.artifact_id))

        # Cambiar mode en payload de la proforma
        pf_locked.payload = {**pf_locked.payload, 'mode': new_mode}
        pf_locked.save(update_fields=['payload'])

        # EventLog
        EventLog.objects.create(
            event_type='proforma.mode_changed',
            aggregate_type=AggregateType.EXPEDIENTE,
            aggregate_id=exp_locked.expediente_id,
            payload={
                'proforma_id': str(pf_locked.artifact_id),
                'old_mode': old_mode,
                'new_mode': new_mode,
                'voided_artifacts': voided_ids,
            },
            occurred_at=now,
            emitted_by='S20-10:change_proforma_mode',
            correlation_id=uuid.uuid4(),
        )

        return {
            'changed': True,
            'old_mode': old_mode,
            'new_mode': new_mode,
            'voided_artifacts': voided_ids,
        }
