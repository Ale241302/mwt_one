from apps.core.dispatcher import register_hook
from apps.inventario.services import InventoryService

@register_hook
def inventory_sync_on_transfer_hook(expediente, command_code, user, result, **kwargs):
    """
    Hook que sincroniza el inventario cuando se recibe una transferencia.
    Escucha el código de comando 'C33' (ReceiveTransfer).
    """
    if command_code == 'C33' and result:
        # result es la instancia de Transfer recibida
        InventoryService.process_transfer_receipt(result.transfer_id)
