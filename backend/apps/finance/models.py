import uuid
from django.db import models
from django.conf import settings
from apps.core.models import TimestampMixin, UUIDReferenceField

class Invoice(TimestampMixin):
    """
    Representación financiera de una proforma/orden. 
    Desacoplada de expedientes físicos.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice_number = models.CharField(max_length=50, unique=True, help_text='Número legal de factura')
    order_id = UUIDReferenceField(target_module='orders', null=True, blank=True)
    expediente_id = UUIDReferenceField(target_module='expedientes', db_index=True)
    
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Borrador'),
            ('sent', 'Enviada'),
            ('paid', 'Pagada'),
            ('cancelled', 'Anulada'),
        ],
        default='draft'
    )
    
    @property
    def order(self):
        return self.resolve_ref('order_id')

    @property
    def expediente(self):
        return self.resolve_ref('expediente_id')

    class Meta:
        db_table = 'finance_invoice'

class Payment(TimestampMixin):
    """
    Refactor de ExpedientePago. 
    Gestión de ingresos vinculados a expedientes o facturas.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    expediente_id = UUIDReferenceField(target_module='expedientes', db_index=True)
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    
    tipo_pago = models.CharField(
        max_length=20,
        choices=[('COMPLETO', 'Pago Completo'), ('PARCIAL', 'Pago Parcial')],
    )
    metodo_pago = models.CharField(
        max_length=30,
        choices=[
            ('TRANSFERENCIA', 'Transferencia Bancaria'),
            ('NOTA_CREDITO', 'Nota de Crédito'),
        ],
    )
    payment_date = models.DateField()
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    
    # S25 Machine states
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pendiente verificación'),
        ('verified', 'Verificado'),
        ('credit_released', 'Crédito liberado'),
        ('rejected', 'Rechazado'),
    ]
    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by_id = models.CharField(max_length=255, blank=True, null=True, help_text='user_id')
    rejection_reason = models.TextField(blank=True, default='')

    @property
    def expediente(self):
        return self.resolve_ref('expediente_id')

    class Meta:
        db_table = 'finance_payment'
