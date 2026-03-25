"""S16-01A: C1 — RegistrarExpediente con reserva de crédito.

Spec changes:
- check_and_reserve_credit(expediente, brand, subsidiary) — firma corregida
- Retorna dict con 'credit_check' key
- Si crédito insuficiente y sin override CEO → raise CreditBlockedError
- credit_warning = True si >= 80% del límite
- credit_blocked = amount si excede límite (marca bloqueo, no bloquea C1 en sí)
"""
from decimal import Decimal
from django.db import transaction

from apps.expedientes.models import Expediente, ArtifactInstance
from apps.expedientes.enums_exp import ExpedienteStatus
from apps.expedientes.enums_artifacts import ArtifactStatusEnum
from apps.expedientes.exceptions import CreditBlockedError
from apps.brands.models import Brand
from apps.clientes.models import LegalEntity, ClientSubsidiary
from apps.agreements.models import CreditExposure


def check_and_reserve_credit(expediente, brand, subsidiary):
    """S16-01A: Evalúa crédito disponible y reserva si aplica.

    Reglas:
    - Solo aplica a expedientes IMPORT.
    - Si no existe CreditPolicy activa → pass (no bloquear).
    - Si hay CreditOverride CEO para C1 → pass.
    - Si reserva supera límite → CreditBlockedError.
    - Si exposición >= 80% del límite → credit_warning = True.

    Returns:
        dict: {
            'status': 'ok' | 'warning' | 'blocked',
            'reserved': float,
            'limit': float,
            'override': bool,
            'message': str,
        }
    """
    if expediente.mode != 'IMPORT':
        return {
            'status': 'ok',
            'reserved': 0,
            'limit': 0,
            'override': False,
            'message': 'Credit check skipped: mode is not IMPORT',
        }

    # S16-01B: Verificar si CEO emitió override para C1
    has_override = False
    try:
        from apps.agreements.models import CreditOverride
        has_override = CreditOverride.objects.filter(
            expediente=expediente,
            command_code='C1'
        ).exists()
    except Exception:
        pass

    if has_override:
        return {
            'status': 'ok',
            'reserved': 0,
            'limit': 0,
            'override': True,
            'message': 'Credit check bypassed: CEO override active for C1',
        }

    # Buscar CreditExposure activa para brand × subsidiary
    subject_id = subsidiary.id if subsidiary else (expediente.client.id if expediente.client else None)
    exposure = CreditExposure.calculate(
        brand=brand,
        subject_type='subsidiary',
        subject_id=subject_id,
    )

    if not exposure:
        return {
            'status': 'ok',
            'reserved': 0,
            'limit': 0,
            'override': False,
            'message': 'No credit policy found — pass',
        }

    amount = expediente.estimated_amount or Decimal('0')
    limit = exposure.policy.max_amount
    current_total = exposure.current_exposure + exposure.reserved_amount

    # Calcular estado del crédito
    if current_total + amount > limit:
        # Bloqueo — sin override ya descartado arriba
        expediente.credit_blocked = True
        expediente.save(update_fields=['credit_blocked'])
        raise CreditBlockedError(
            f"Crédito insuficiente. Límite: {limit}, Usado: {current_total}, "
            f"Solicitado: {amount}. CEO debe emitir CreditOverride para C1."
        )

    # Reservar
    success, message = exposure.reserve(amount)
    if not success:
        raise CreditBlockedError(f"No se pudo reservar crédito: {message}")

    # Warning threshold 80%
    new_total = current_total + amount
    credit_status = 'ok'
    if new_total >= limit * Decimal('0.8'):
        credit_status = 'warning'
        expediente.credit_warning = True
        expediente.save(update_fields=['credit_warning'])

    return {
        'status': credit_status,
        'reserved': float(amount),
        'limit': float(limit),
        'override': False,
        'message': f'Crédito reservado. {credit_status.upper()}',
    }


def handle_c1(user, payload):
    """S16-01A: Registrar Expediente — command C1.

    Retorna dict con key 'credit_check' para transparencia en el response.
    """
    with transaction.atomic():
        entity_id = payload.get('entity_id')
        le, _ = LegalEntity.objects.get_or_create(entity_id=entity_id)

        brand_slug = payload.get('brand', 'marluvas').lower()
        brand, _ = Brand.objects.get_or_create(
            slug=brand_slug,
            defaults={'name': brand_slug.upper()}
        )

        # Resolver subsidiary si viene en el payload
        subsidiary = None
        subsidiary_id = payload.get('subsidiary_id')
        if subsidiary_id:
            subsidiary = ClientSubsidiary.objects.filter(pk=subsidiary_id).first()

        exp = Expediente.objects.create(
            external_id=payload.get('external_id'),
            legal_entity=le,
            client=le,
            brand=brand,
            status=ExpedienteStatus.REGISTRO,
            mode=payload.get('mode', 'IMPORT'),
            freight_mode=payload.get('freight_mode', 'FCL'),
            estimated_amount=Decimal(str(payload.get('estimated_amount', 0))),
        )

        # S16-01A: Reserva de crédito (puede levantar CreditBlockedError)
        credit_check = check_and_reserve_credit(exp, brand, subsidiary)

        # ART-01: Folio de registro (se crea siempre en C1)
        ArtifactInstance.objects.create(
            expediente=exp,
            artifact_type='ART-01',
            status=ArtifactStatusEnum.COMPLETED,
            payload=payload,
        )

        return {
            'expediente_id': str(exp.pk),
            'external_id': exp.external_id,
            'status': exp.status,
            'credit_check': credit_check,
        }
