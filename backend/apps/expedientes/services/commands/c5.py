from django.utils import timezone


def handle_c5(expediente, payload, env=None):
    """Confirmar SAP (C5) — sin gate de artefactos, permite SAP en cualquier momento."""
    sap_number = payload.get('sap_number', '')

    # S14-05: Save immutable snapshot of commercial terms
    now = timezone.now()
    expediente.snapshot_commercial = {
        'snapshot_date': now.isoformat(),
        'sap_number': sap_number,
        'pricing_mode': expediente.mode,
        'freight_mode': expediente.freight_mode,
        'transport_mode': expediente.transport_mode,
        'dispatch_mode': expediente.dispatch_mode,
        'credit_clock_start_rule': getattr(expediente, 'credit_clock_start_rule', None),
    }

    # S16-04: Assign agreement defaults (optional — skip silently if field not present)
    try:
        from ..pricing import assign_agreement_defaults
        assign_agreement_defaults(expediente)
    except (AttributeError, Exception):
        pass  # subsidiary_id or agreement lookup not available — non-blocking

    expediente.save(update_fields=['snapshot_commercial'])
