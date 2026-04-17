from apps.expedientes.models import ExpedienteSAP
from apps.expedientes.enums_exp import ExpedienteStatus
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

class SAPStateMachine:
    """
    Gestor de transiciones de estado para ExpedienteSAP (SAP numbers).
    Asegura que las transiciones sean válidas y registren eventos en el Historial.
    """
    
    ALLOWED_TRANSITIONS = {
        ExpedienteStatus.REGISTRO: [ExpedienteStatus.PRODUCCION, ExpedienteStatus.CANCELADO],
        ExpedienteStatus.PRODUCCION: [ExpedienteStatus.PREPARACION, ExpedienteStatus.CANCELADO],
        ExpedienteStatus.PREPARACION: [ExpedienteStatus.DESPACHO, ExpedienteStatus.CANCELADO],
        ExpedienteStatus.DESPACHO: [ExpedienteStatus.TRANSITO, ExpedienteStatus.CANCELADO],
        ExpedienteStatus.TRANSITO: [ExpedienteStatus.EN_DESTINO, ExpedienteStatus.CANCELADO],
        ExpedienteStatus.EN_DESTINO: [ExpedienteStatus.CERRADO, ExpedienteStatus.CANCELADO],
        ExpedienteStatus.CERRADO: [ExpedienteStatus.REGISTRO], # Solo con justificación de reapertura
    }

    @classmethod
    def transition_to(cls, sap_id: str, new_status: str, metadata: dict = None):
        """
        Ejecuta la transición de estado de un SAP.
        """
        with transaction.atomic():
            sap = ExpedienteSAP.objects.select_for_update().get(pk=sap_id)
            old_status = sap.status
            
            if new_status not in cls.ALLOWED_TRANSITIONS.get(old_status, []):
                raise ValueError(f"Transición de {old_status} a {new_status} no permitida.")
            
            sap.status = new_status
            sap.save()
            
            # El sistema de historial escuchará el post_save o podemos emitir el evento aquí
            logger.info(f"SAP {sap_id} transicionado de {old_status} a {new_status}")
            
            return sap

    @classmethod
    def can_transition(cls, sap_id: str, new_status: str) -> bool:
        try:
            sap = ExpedienteSAP.objects.get(pk=sap_id)
            return new_status in cls.ALLOWED_TRANSITIONS.get(sap.status, [])
        except ExpedienteSAP.DoesNotExist:
            return False
