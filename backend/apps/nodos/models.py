import uuid
from django.db import models
from apps.core.models import BaseModel, LegalEntity
from .enums import NodeType, NodeStatus

class Node(BaseModel):
    """
    Representa un punto logístico (bodega, fábrica, etc.) en el sistema.
    Extraído de transfers para ser un módulo catalizador independiente.
    """
    name = models.CharField(max_length=200)
    legal_entity = models.ForeignKey(
        LegalEntity, on_delete=models.PROTECT, related_name='nodes'
    )
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
