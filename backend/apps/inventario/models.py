from django.db import models
from apps.core.models import TimestampMixin

from apps.core.models import TimestampMixin, UUIDReferenceField

class InventoryEntry(TimestampMixin):
    product_id = UUIDReferenceField(target_module='productos', db_index=True)
    node_id = UUIDReferenceField(target_module='nodos', db_index=True)
    quantity = models.IntegerField(default=0)
    reserved = models.IntegerField(default=0)
    lot_number = models.CharField(max_length=50, blank=True)
    received_at = models.DateTimeField()

    class Meta:
        db_table = 'inventario_inventoryentry'
        unique_together = ('product_id', 'node_id', 'lot_number')
        verbose_name = 'Entrada de Inventario'
        verbose_name_plural = 'Entradas de Inventario'
        ordering = ['-received_at']

    @property
    def product(self):
        return self.resolve_ref('product_id')

    @property
    def node(self):
        return self.resolve_ref('node_id')

    def __str__(self):
        node_name = self.node.name if self.node else "Nodo Desconocido"
        sku = self.product.sku_base if self.product else "SKU Desconocido"
        return f"{sku} @ {node_name} (Lot: {self.lot_number or 'N/A'})"
