from apps.expedientes.enums_exp import ExpedienteStatus

def handle_c16(expediente, payload):
    # Cancelar Expediente
    expediente.status = ExpedienteStatus.CANCELADO
    expediente.save(update_fields=['status'])

def handle_c17(expediente, payload, env=None):
    # Bloquear Expediente
    expediente.is_blocked = True
    expediente.save(update_fields=['is_blocked'])

def handle_c18(expediente, payload, env=None):
    # Desbloquear Expediente
    expediente.is_blocked = False
    expediente.save(update_fields=['is_blocked'])
