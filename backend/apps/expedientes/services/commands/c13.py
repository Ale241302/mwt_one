from apps.expedientes.exceptions import CommandValidationError

def handle_c13(expediente, payload, env=None):
    """Registrar Factura MWT (ART-12)."""
    invoice_num = payload.get('invoice_number')
    if not invoice_num:
        raise CommandValidationError("C13 requires an invoice_number in payload.")
    
    # S16-09: Trigger credit clock if start_event == 'on_invoice'
    from ..helpers import _trigger_credit_clock
    _trigger_credit_clock(expediente, 'on_invoice')

    return {"message": f"MWT Invoice {invoice_num} registered"}
