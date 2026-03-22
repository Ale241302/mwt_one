from django.db import models
from apps.core.models import TimestampMixin

class InventoryEntry(TimestampMixin):
    product = models.ForeignKey('productos.Producto', on_delete=models.PROTECT, related_name='inventory_entries')
    node = models.ForeignKey('transfers.Node', on_delete=models.PROTECT, related_name='inventory_entries')
    quantity = models.IntegerField(default=0)
    reserved = models.IntegerField(default=0)
    lot_number = models.CharField(max_length=50, blank=True)
    received_at = models.DateTimeField()

    class Meta:
        db_table = 'inventario_inventoryentry'
        unique_together = ('product', 'node', 'lot_number')
        verbose_name = 'Entrada de Inventario'
        verbose_name_plural = 'Entradas de Inventario'
        ordering = ['-received_at']

    def __str__(self):
        return f"{self.product.sku_base} @ {self.node.name} (Lot: {self.lot_number or 'N/A'})"
