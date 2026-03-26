from django.utils import timezone
from apps.expedientes.exceptions import ArtifactMissingError, CreditBlockedError
from ..helpers import _has_artifact, _check_credit_gate


def trigger_credit_clock(expediente):
    """S16-02: Inicia el reloj de crédito en el timestamp actual."""
    if not expediente.credit_clock_started_at:
        expediente.credit_clock_started_at = timezone.now()
        expediente.save(update_fields=['credit_clock_started_at'])


def handle_c9(expediente, payload, env=None):
    """Cargar Certificado de Origen (ART-08): registra el certificado de origen.

    Gate: ART-07 (Factura Comercial) requerido.
    S16-02: Verifica override de crédito si expediente bloqueado.
    S16-02: Dispara reloj de crédito si start_event == 'on_shipment'.
    """
    # S16-02: Gate de crédito
    _check_credit_gate(expediente, 'C9')

    # Gate de artefactos: ART-07 Factura Comercial
    if not _has_artifact(expediente, 'ART-07'):
        raise ArtifactMissingError("C9 requiere ART-07 (Factura Comercial).")

    # S16-02: Reloj de crédito según CreditClockRule
    # Leer la regla configurada (si existe). Si no existe → fallback on_arrival.
    # TODO: CEO_INPUT_REQUIRED — CreditClockRule reglas por freight_mode no definidas (S16-09)
    freight_mode = getattr(expediente, 'freight_mode', 'SEA') or 'SEA'
    brand = expediente.brand

    start_event = 'on_arrival'  # Fallback seguro
    try:
        from apps.agreements.models import CreditClockRule
        rule = CreditClockRule.objects.filter(
            brand=brand,
            freight_mode=freight_mode
        ).first()
        if rule:
            start_event = rule.start_event
    except Exception:
        # CreditClockRule no existe todavía (S16-09 es condicional)
        pass

    if start_event == 'on_shipment':
        trigger_credit_clock(expediente)

    return {"message": "Certificado de Origen registrado exitosamente", "credit_clock_trigger": start_event}
