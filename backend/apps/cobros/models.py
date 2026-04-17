import uuid
from django.db import models
from apps.core.models import TimestampMixin, UUIDReferenceField

class CollectionAction(TimestampMixin):
    """
    Registro de gestiones de cobro realizadas sobre un cliente o expediente.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client_id = UUIDReferenceField(target_module='clientes', db_index=True)
    expediente_id = UUIDReferenceField(target_module='expedientes', null=True, blank=True)
    
    action_type = models.CharField(
        max_length=50,
        choices=[
            ('email_auto', 'Email Automático'),
            ('call', 'Llamada Telefónica'),
            ('meeting', 'Reunión Presencial'),
            ('legal', 'Acción Legal'),
        ]
    )
    
    notes = models.TextField()
    performed_at = models.DateTimeField(auto_now_add=True)
    performed_by_id = models.CharField(max_length=255, help_text='user_id')
    
    @property
    def client(self):
        return self.resolve_ref('client_id')

    @property
    def expediente(self):
        return self.resolve_ref('expediente_id')

    class Meta:
        db_table = 'cobros_collectionaction'
        ordering = ['-performed_at']
