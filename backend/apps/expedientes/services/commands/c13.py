from apps.expedientes.exceptions import CommandValidationError

def handle_c13(expediente, payload):
    """Registrar Factura MWT (ART-12)."""
    invoice_num = payload.get('invoice_number')
    if not invoice_num:
        raise CommandValidationError("C13 requires an invoice_number in payload.")
    
    # In a real system, we might link this to a Financial model or update a field
    return {"message": f"MWT Invoice {invoice_num} registered"}
