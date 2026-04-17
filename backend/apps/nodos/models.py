import uuid
from django.db import models
from apps.core.models import BaseModel, LegalEntity, UUIDReferenceField
from .enums import NodeType, NodeStatus

class Node(BaseModel):
    """
    Representa un punto logístico (bodega, fábrica, etc.) en el sistema.
    Extraído de transfers para ser un módulo catalizador independiente.
    """
    name = models.CharField(max_length=200)
    legal_entity_id = UUIDReferenceField(
        target_module='core', 
        target_model='LegalEntity',
        db_index=True
    )

    @property
    def legal_entity(self):
        return self.resolve_ref('legal_entity_id')
    node_type = models.CharField(max_length=30, choices=NodeType.choices)
    location = models.CharField(max_length=500, blank=True)
    status = models.CharField(
        max_length=20, choices=NodeStatus.choices, default=NodeStatus.ACTIVE
    )

    class Meta:
        db_table = 'nodos_node'
        verbose_name = 'Nodo'
        verbose_name_plural = 'Nodos'

    def __str__(self):
        return f'{self.name} ({self.get_node_type_display()})'
