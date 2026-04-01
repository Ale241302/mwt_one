from apps.expedientes import enums_exp

COMMAND_SPEC = {
    'C1': {
        'name': 'Crear Expediente',
        'requires_status': None,
        'transition_to': enums_exp.ExpedienteStatus.REGISTRO,
        'creates_art': 'ART-01'
    },
    'C2': {
        'name': 'Registrar Proforma',
        'requires_status': None,
        'creates_art': 'ART-02'
    },
    'C3': {
        'name': 'Registrar Orden de Compra',
        'requires_status': None,
        'creates_art': 'ART-01'
    },
    'C4': {
        'name': 'Decisión Modal (CEO)',
        'requires_status': None,
        'creates_art': 'ART-03',
        'requires_ceo': True
    },
    'C5': {
        'name': 'Confirmar Registro → PRODUCCION',
        'requires_status': None,
        'transition_to': enums_exp.ExpedienteStatus.PRODUCCION,
        'creates_art': 'ART-04'
    },
    'C6': {
        'name': 'Confirmación Producción',
        'requires_status': None,
        'creates_art': 'ART-06'
    },
    'C7': {
        'name': 'Registrar Embarque',
        'requires_status': None,
        'creates_art': 'ART-05'
    },
    'C8': {
        'name': 'Cotización Flete',
        'requires_status': None,
        'creates_art': 'ART-08'
    },
    'C9': {
        'name': 'Despacho Aduanal',
        'requires_status': None,
        'creates_art': 'ART-09'
    },
    'C10': {
        'name': 'Aprobar Despacho',
        'requires_status': None,
        'creates_art': 'ART-07'
    },
    'C11': {
        'name': 'BL Registrado',
        'requires_status': None,
        'creates_art': 'ART-10'
    },
    'C11B': {
        'name': 'Confirmar Salida Despacho → TRANSITO',
        'requires_status': None,
        'transition_to': enums_exp.ExpedienteStatus.TRANSITO,
        'creates_art': None
    },
    'C12': {
        'name': 'Confirmar Arribo CR → EN_DESTINO',
        'requires_status': None,
        'transition_to': enums_exp.ExpedienteStatus.EN_DESTINO,
        'creates_art': 'ART-11'
    },
    'C13': {
        'name': 'Factura MWT',
        'requires_status': None,
        'creates_art': 'ART-13'
    },
    'C14': {
        'name': 'Finalizar Expediente → CERRADO',
        'requires_status': None,
        'transition_to': enums_exp.ExpedienteStatus.CERRADO,
        'creates_art': None
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
        'creates_art': 'ART-16',
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
    # S17-03: REOPEN verified in COMMAND_SPEC
    'REOPEN': {
        'name': 'Reabrir Expediente (CEO Only)',
        'requires_status': enums_exp.ExpedienteStatus.CANCELADO,
        'transition_to': enums_exp.ExpedienteStatus.REGISTRO,
        'creates_art': None,
        'requires_ceo': True
    },
    'CANCEL': {
        'name': 'Cancelar Expediente (alias)',
        'requires_status': None,
        'transition_to': enums_exp.ExpedienteStatus.CANCELADO,
        'creates_art': None,
        'requires_ceo': True
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
    }
}
