import uuid
from django.utils import timezone
from django.db import transaction
from apps.inventario.models import InventoryEntry
from apps.core.registry import ModuleRegistry

class InventoryService:
    """Servicio para gestión de inventario distribuido."""

    @staticmethod
    def _create_inventory_event(product_id, node_id, quantity, action, emitted_by):
        """Helper para registrar movimientos en el EventLog resuelto dinámicamente."""
        event_model = ModuleRegistry.get_model('expedientes', 'EventLog')
        if not event_model:
            logger.warning("EventLog no disponible para el registro de inventario.")
            return

        event_model.objects.create(
            event_type='inventory.moved',
            aggregate_type='INV',
            aggregate_id=uuid.uuid4(),
            payload={
                'product_id': str(product_id),
                'node_id': str(node_id),
                'quantity': quantity,
                'action': action,
            },
            occurred_at=timezone.now(),
            emitted_by=emitted_by,
            processed_at=timezone.now(),
            correlation_id=uuid.uuid4(),
        )

    @staticmethod
    @transaction.atomic
    def update_stock(product_id, node_id, quantity_change, action_name):
        """
        Incrementa o decrementa el stock de un producto en un nodo.
        quantity_change puede ser positivo o negativo.
        """
        entry, created = InventoryEntry.objects.get_or_create(
            product_id=product_id,
            node_id=node_id,
            defaults={'received_at': timezone.now()}
        )
        entry.quantity += quantity_change
        if entry.quantity < 0:
            # En un sistema real podrías permitir stock negativo o lanzar error
            # Por ahora, registramos pero permitimos.
            pass
        
        entry.save()
        
        InventoryService._create_inventory_event(
            product_id, node_id, quantity_change, action_name, "InventoryService"
        )
        return entry

    @staticmethod
    def process_transfer_receipt(transfer_id):
        """
        Procesa la recepción de una transferencia y actualiza el inventario.
        Invocado por el Event Dispatcher.
        """
        transfer_service = ModuleRegistry.get_service_class('transfers')
        product_service = ModuleRegistry.get_service_class('productos')
        
        if not transfer_service or not product_service:
            return
            
        transfer = transfer_service.get_entity(transfer_id)
        if not transfer or transfer.status != 'received':
            return

        with transaction.atomic():
            for line in transfer.lines.all():
                # Encontrar el producto por SKU (desacoplado)
                product = product_service.get_variant(line.sku)
                if not product:
                    # Log error: SKU desconocido
                    continue
                
                product_uuid = product.product.id
                
                # Incrementar en nodo destino
                if line.quantity_received:
                    InventoryService.update_stock(
                        product_uuid, 
                        transfer.to_node_id, 
                        line.quantity_received, 
                        f"Receipt from {transfer.transfer_id}"
                    )
                
                # Decrementar en nodo origen (asumiendo que no se hizo en el dispatch)
                # NOTA: En una refactorización completa, el dispatch decrementa y el receipt incrementa.
                # Para esta fase, haremos ambos en el receipt para asegurar consistencia.
                InventoryService.update_stock(
                    product_uuid, 
                    transfer.from_node_id, 
                    -(line.quantity_dispatched), 
                    f"Dispatch to {transfer.transfer_id}"
                )
