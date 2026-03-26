from apps.expedientes import enums_exp

COMMAND_SPEC = {
    'C1': {
        'name': 'Registrar Expediente',
        'requires_status': None,
        'transition_to': enums_exp.ExpedienteStatus.REGISTRO,
        'creates_art': 'ART-01',
        'requires_ceo': True
    },
    'C2': {
        'name': 'Registrar Proforma',
        'requires_status': enums_exp.ExpedienteStatus.REGISTRO,
        'creates_art': 'ART-02'
    },
    'C3': {
        'name': 'Registrar Orden de Compra',
        'requires_status': enums_exp.ExpedienteStatus.REGISTRO,
        'creates_art': 'ART-03'
    },
    'C4': {
        'name': 'Decidir Modo Import/Comision',
        'requires_status': enums_exp.ExpedienteStatus.REGISTRO,
        'creates_art': None,
        'requires_ceo': True
    },
    'C5': {
        'name': 'Confirmar Registro',
        'requires_status': enums_exp.ExpedienteStatus.REGISTRO,
        'transition_to': enums_exp.ExpedienteStatus.PRODUCCION,
        'creates_art': 'ART-04'
    },
    'C6': {
        'name': 'Registrar Producción',
        'requires_status': enums_exp.ExpedienteStatus.PRODUCCION,
        'transition_to': enums_exp.ExpedienteStatus.PREPARACION,
        'creates_art': 'ART-05'
    },
    'C7': {
        'name': 'Cargar Packing List',
        'requires_status': enums_exp.ExpedienteStatus.PREPARACION,
        'creates_art': 'ART-06'
    },
    'C8': {
        'name': 'Cargar Factura Comercial',
        'requires_status': enums_exp.ExpedienteStatus.PREPARACION,
        'creates_art': 'ART-07'
    },
    'C9': {
        'name': 'Cargar Certificado de Origen',
        'requires_status': enums_exp.ExpedienteStatus.PREPARACION,
        'creates_art': 'ART-08'
    },
    'C10': {
        'name': 'Aprobar Despacho',
        'requires_status': enums_exp.ExpedienteStatus.PREPARACION,
        'creates_art': 'ART-13'
    },
    'C11': {
        'name': 'Confirmar Salida Aduana (China)',
        'requires_status': enums_exp.ExpedienteStatus.PREPARACION,
        'transition_to': enums_exp.ExpedienteStatus.DESPACHO,
        'creates_art': 'ART-09'
    },
    'C11B': {
        'name': 'Confirmar Salida China',
        'requires_status': [enums_exp.ExpedienteStatus.DESPACHO],
        'transition_to': enums_exp.ExpedienteStatus.TRANSITO,
        'creates_art': None,
        'requires_ceo': False,
    },
    'C12': {
        'name': 'Confirmar Arribo CR',
        'requires_status': enums_exp.ExpedienteStatus.TRANSITO,
        'transition_to': enums_exp.ExpedienteStatus.EN_DESTINO,
        'creates_art': 'ART-11'
    },
    'C13': {
        'name': 'Liquidar Expediente',
        'requires_status': enums_exp.ExpedienteStatus.EN_DESTINO,
        'creates_art': 'ART-12'
    },
    'C14': {
        'name': 'Cerrar Expediente',
        'requires_status': enums_exp.ExpedienteStatus.EN_DESTINO,
        'transition_to': enums_exp.ExpedienteStatus.CERRADO,
        'creates_art': None,
        'requires_ceo': True
    },
    'C15': {
        'name': 'Registrar Gasto (Financial)',
        'requires_status': None,
        'creates_art': None
    },
    'C16': {
        'name': 'Cancelar Expediente',
        'requires_status': None,
        'transition_to': enums_exp.ExpedienteStatus.CANCELADO,
        'creates_art': None,
        'requires_ceo': True
    },
    'C17': {
        'name': 'Bloquear Expediente',
        'requires_status': None,
        'creates_art': None
    },
    'C18': {
        'name': 'Desbloquear Expediente',
        'requires_status': None,
        'creates_art': None,
        'requires_ceo': True,
        'bypass_block': True
    },
    'C19': {
        'name': 'Supersede Artifact',
        'requires_status': None,
        'creates_art': None
    },
    'C20': {
        'name': 'Void Artifact',
        'requires_status': None,
        'creates_art': None
    },
    'C21': {
        'name': 'Reabrir Expediente',
        'requires_status': [enums_exp.ExpedienteStatus.CERRADO],
        'transition_to': enums_exp.ExpedienteStatus.EN_DESTINO,
        'creates_art': None,
        'requires_ceo': True
    },
    'C25': {
        'name': 'Registrar Pago (Financial)',
        'requires_status': None,
        'creates_art': None
    },
    'C22': {
        'name': 'Factura Comisión (COMISION mode)',
        'requires_status': enums_exp.ExpedienteStatus.EN_DESTINO,
        'creates_art': 'ART-10'
    },
    'C23': {
        'name': 'Agregar Opción Logística (ART-19)',
        'requires_status': None,
        'creates_art': None
    },
    'C24': {
        'name': 'Decidir Logística (ART-19)',
        'requires_status': None,
        'creates_art': None
    },
    'C29': {
        'name': 'Registrar Compensación (CEO Only)',
        'requires_status': None,
        'creates_art': 'ART-12',
        'requires_ceo': True
    },
    'C30': {
        'name': 'Materializar Logística (Sprint 4)',
        'requires_status': None,
        'creates_art': 'ART-11'
    },
    'C36': {
        'name': 'Add Shipment Update (Manual)',
        'requires_status': None,
        'creates_art': 'ART-05'
    },
    'REOPEN': {
        'name': 'Reabrir Expediente',
        'requires_status': [enums_exp.ExpedienteStatus.CANCELADO],
        'transition_to': enums_exp.ExpedienteStatus.REGISTRO,
        'requires_ceo': True,
        'creates_art': None,
    }
}
