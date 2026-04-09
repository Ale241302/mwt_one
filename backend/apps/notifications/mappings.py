"""
S26-09: Mapeo trigger → template_key.
action_source (EventLog) → template_key (NotificationTemplate).
Cobranza (payment.overdue) → via cron, no hook.
proforma.sent → via endpoint manual H3, no hook.
"""

TRIGGER_TO_TEMPLATE = {
    # action_source (EventLog)  → template_key (NotificationTemplate)
    'C1':              'expediente.registered',
    'C5':              'expediente.production_started',
    'C11':             'expediente.dispatched',
    'C13':             'expediente.in_transit',
    'C15':             'expediente.delivered',
    'verify_payment':  'payment.verified',
    'reject_payment':  'payment.rejected',
    'release_credit':  'payment.credit_released',
    # Cobranza (payment.overdue) se maneja via cron, no via hook.
    # proforma.sent se maneja via endpoint manual H3, no via hook.
}
