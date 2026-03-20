from apps.expedientes.models import PaymentLine, CostLine
from .helpers import _update_payment_status

def handle_c15(expediente, payload):
    # Registrar Gasto (Financial)
    CostLine.objects.create(
        expediente=expediente,
        amount=payload.get('amount'),
        category=payload.get('category'),
        provider=payload.get('provider')
    )

def handle_c21(expediente, payload):
    # Registrar Pago (Financial)
    # This was a complex logic in services.py 420:
    PaymentLine.objects.create(
        expediente=expediente,
        amount=payload.get('amount'),
        method=payload.get('method'),
        reference=payload.get('reference')
    )
    _update_payment_status(expediente)
