import uuid
from django.db import models
from apps.core.models import BaseModel

class Event(BaseModel):
    """
    Registro inmutable de eventos de negocio en el sistema distribuido.
    Sirve como fuente de verdad para el historial de cambios de cualquier entidad.
    """
    event_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    module_source = models.CharField(max_length=50, db_index=True, help_text="Módulo que originó el evento")
    entity_type = models.CharField(max_length=50, db_index=True, help_text="Tipo de entidad (e.g., 'Brand', 'SAP')")
    entity_id = models.CharField(max_length=100, db_index=True, help_text="ID de la entidad referenciada")
    payload = models.JSONField(default=dict, help_text="Datos completos del evento")
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'historial_event'
        ordering = ['-timestamp']
        verbose_name = 'Evento de Historial'
        verbose_name_plural = 'Eventos de Historial'

    def __str__(self):
        return f"[{self.module_source}] {self.entity_type}:{self.entity_id} at {self.timestamp}"
