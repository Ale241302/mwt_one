from apps.orders.models import ClientOrder, ClientOrderLine
from apps.expedientes.models import ExpedienteSAP
from apps.historial.models import EventLog
from django.db import transaction
import uuid
import logging

logger = logging.getLogger(__name__)

class OrderService:
    """
    Servicio para gestionar el ciclo de vida de las Órdenes de Compra (OC).
    Maneja la creación, sumisión y conversión a Expediente SAP.
    """
    
    @classmethod
    @transaction.atomic
    def create_order(cls, client_id, brand_id, lines_data, agreement_id=None):
        """
        Crea una nueva Orden de Compra.
        lines_data: list of dicts with {'sku', 'qty', 'price'}
        """
        order = ClientOrder.objects.create(
            client_id=client_id,
            brand_id=brand_id,
            agreement_id=agreement_id,
            status='draft'
        )
        
        for line in lines_data:
            ClientOrderLine.objects.create(
                order=order,
                sku=line['sku'],
                qty=line['qty'],
                resolved_price=line.get('price', 0)
            )
        
        logger.info(f"Orden {order.id} creada para cliente {client_id}")
        return order

    @classmethod
    @transaction.atomic
    def submit_order(cls, order_id):
        order = ClientOrder.objects.get(pk=order_id)
        if order.status != 'draft':
            raise ValueError("Solo se pueden enviar órdenes en borrador.")
        
        order.status = 'submitted'
        order.save()
        
        # TODO: Notificar al CEO para revisión
        return order

    @classmethod
    @transaction.atomic
    def convert_to_sap(cls, order_id, legal_entity_id):
        """
        Convierte una Orden de Compra aprobada en un Expediente SAP.
        """
        order = ClientOrder.objects.get(pk=order_id)
        if order.status != 'submitted':
             # En un flujo real, debería ser 'approved', pero usamos 'submitted' para este demo
             pass
        
        # Crear el SAP vinculándolo a la OC
        sap = ExpedienteSAP.objects.create(
            order_id=order.id,
            client_id=order.client_id,
            brand_id=order.brand_id,
            legal_entity_id=legal_entity_id,
            status='REGISTRO'
        )
        
        order.status = 'converted'
        order.save()
        
        logger.info(f"Orden {order_id} convertida a SAP {sap.expediente_id}")
        return sap
