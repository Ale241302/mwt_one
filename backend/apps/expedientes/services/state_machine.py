from apps.expedientes.models import Expediente
from apps.expedientes.enums_exp import ExpedienteStatus
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

def can_transition_to(expediente, cmd_id, user):
    """
    Verifica si un comando puede ejecutarse según el estado actual y el usuario.
    Regresa (bool, reason).
    """
    from .constants import COMMAND_SPEC
    
    spec = COMMAND_SPEC.get(cmd_id)
    if not spec:
        return False, f"Comando {cmd_id} no reconocido."

    # 1. Block check
    if expediente.is_blocked and not spec.get('bypass_block', False):
        return False, f"Expediente bloqueado: {expediente.blocked_reason or 'Sin razón'}"

    # 2. Status check
    req_status = spec.get('requires_status')
    if req_status and expediente.status != req_status:
        return False, f"Estado {expediente.status} no válido para {cmd_id}. Requiere {req_status}."

    # 3. Permissions check
    if spec.get('requires_ceo', False) and not (user.is_superuser or getattr(user, 'is_staff', False)):
        return False, "Operación autorizada solo para personal administrativo / CEO."

    return True, ""


class SAPStateMachine:
    """
    Gestor de transiciones de estado para ExpedienteSAP.
    Asegura que las transiciones sean válidas.
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
            sap = Expediente.objects.select_for_update().get(pk=sap_id)
            old_status = sap.status
            
            if new_status not in cls.ALLOWED_TRANSITIONS.get(old_status, []):
                raise ValueError(f"Transición de {old_status} a {new_status} no permitida.")
            
            sap.status = new_status
            sap.save()
            
            logger.info(f"SAP {sap_id} transicionado de {old_status} a {new_status}")
            return sap

    @classmethod
    def can_transition(cls, sap_id: str, new_status: str) -> bool:
        try:
            sap = Expediente.objects.get(pk=sap_id)
            return new_status in cls.ALLOWED_TRANSITIONS.get(sap.status, [])
        except Expediente.DoesNotExist:
            return False
