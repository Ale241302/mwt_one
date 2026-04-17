import logging
from django.db.models import Sum
from .models import Payment

logger = logging.getLogger(__name__)

class FinanceService:
    """
    Servicio para la resolución y gestión de datos financieros.
    Permite el desacoplamiento de la lógica de pagos del resto del sistema.
    """

    @staticmethod
    def get_entity(payment_id):
        """Resuelve un ID de pago a su instancia."""
        try:
            return Payment.objects.get(pk=payment_id)
        except (Payment.DoesNotExist, ValueError):
            return None

    @staticmethod
    def get_expediente_payments(exp_id):
        """
        Retorna el listado de pagos asociados a un expediente.
        Usado por el Portal y Dashboard de forma distribuida.
        """
        return Payment.objects.filter(expediente_id=exp_id).order_by('payment_date')

    @staticmethod
    def get_total_verified(exp_id):
        """
        Calcula el total verificado para un expediente.
        """
        res = Payment.objects.filter(
            expediente_id=exp_id, 
            status__in=['verified', 'credit_released']
        ).aggregate(total=Sum('amount_paid'))
        return res['total'] or 0
