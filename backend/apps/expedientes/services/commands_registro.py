from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from apps.expedientes.enums_exp import ExpedienteStatus, CostBehavior, AggregateType
from apps.expedientes.enums_artifacts import ArtifactStatusEnum
from apps.expedientes.exceptions import CommandValidationError, ArtifactMissingError
from apps.expedientes.models import CostLine, EventLog
from .helpers import _has_artifact

def handle_c2(expediente, payload):
    # Registrar Proforma (ART-02)
    # S20-V24: Implementar guardado persistente para permitir edición (Modo Libre)
    from apps.expedientes.models import ArtifactInstance
    items = payload.get('items', [])
    for item in items:
        sku = item.get('sku')
        if not sku:
            continue
    
    # Siempre guardamos o actualizamos para permitir cambios
    ArtifactInstance.objects.update_or_create(
        expediente=expediente,
        artifact_type='ART-02',
        defaults={'payload': payload, 'status': 'completed'}
    )
    return {"message": "Proforma registrada"}

def handle_c3(expediente, payload):
    # Registrar Orden de Compra (ART-03)
    # S20-V24: Corregir fallo de guardado de C3
    from apps.expedientes.models import ArtifactInstance
    ArtifactInstance.objects.update_or_create(
        expediente=expediente,
        artifact_type='ART-03',
        defaults={'payload': payload, 'status': 'completed'}
    )
    return {"message": "Orden de Compra registrada"}

def get_dai_rate(partida, pais):
    return getattr(settings, 'DAI_RATES', {}).get(partida, {}).get(pais)

def get_estimated_fixed_costs(qty):
    recent = CostLine.objects.filter(cost_behavior=CostBehavior.FIXED_PER_OPERATION).order_by('-created_at')[:5]
    if not recent.exists():
        return None
    total = sum(c.amount for c in recent)
    avg = total / recent.count() if recent.count() else 0
    if not qty or Decimal(str(qty)) == 0:
        return avg
    return avg / Decimal(str(qty))

def pre_check_viability(expediente, mode, fob_mwt, fob_cliente, qty):
    if mode != 'FULL':
        return None
    missing_inputs = []
    partida = getattr(expediente, 'partida_arancelaria', None)
    dai_pct = get_dai_rate(partida, expediente.destination) if partida else None
    if dai_pct is None:
        missing_inputs.append('lookup_arancelario')
    flete_pct = getattr(settings, 'VIABILITY_FLETE_PCT', None)
    if flete_pct is None:
        missing_inputs.append('FLETE_PCT')
    fixed_costs = get_estimated_fixed_costs(qty)
    if fixed_costs is None:
        missing_inputs.append('baseline_costos_fijos')
    if missing_inputs:
        return {
            'warning': True,
            'degraded': True,
            'message': f'Config incompleta — cálculo de viabilidad no disponible',
            'missing_inputs': missing_inputs,
        }
    costo_landed_est = Decimal(str(fob_mwt)) * (1 + Decimal(str(flete_pct))) * (1 + Decimal(str(dai_pct))) + Decimal(str(fixed_costs))
    if costo_landed_est > Decimal(str(fob_cliente)):
        delta = costo_landed_est - Decimal(str(fob_cliente))
        return {
            'warning': True,
            'degraded': False,
            'message': f'Modelo C genera pérdida estimada de ${delta:.2f}/par',
            'costo_landed_est': float(costo_landed_est),
            'fob_cliente': float(fob_cliente),
            'delta_per_unit': float(delta),
        }
    return None

def handle_c4(expediente, payload):
    # Decidir Modo Import/Comision
    mode = payload.get('mode')
    if mode not in ['IMPORT', 'COMISION', 'FULL']:
        raise CommandValidationError(f"Invalid mode: {mode}")
    
    fob_mwt = payload.get('fob_mwt', 0)
    fob_cliente = payload.get('fob_cliente', 0)
    qty = payload.get('qty', 0)
    viability_check = pre_check_viability(expediente, mode, fob_mwt, fob_cliente, qty)
    
    if viability_check:
        EventLog.objects.create(
            event_type='viability_check_result',
            aggregate_type=AggregateType.EXPEDIENTE,
            aggregate_id=expediente.expediente_id,
            payload=viability_check,
            occurred_at=timezone.now(),
            correlation_id=expediente.expediente_id,
            emitted_by='C4:DecideModeBC'
        )
        
    expediente.mode = mode
    expediente.save(update_fields=['mode'])
    return {'viability_check': viability_check} if viability_check else {}

def handle_c5(expediente, payload):
    # Confirmar Registro (SAP)
    # S20-V24: MODO LIBRE - Eliminar ArtifactMissingError y persistir ART-04
    from apps.expedientes.models import ArtifactInstance
    
    # S14-05: Snapshot comercial
    now = timezone.now()
    expediente.snapshot_commercial = {
        'snapshot_date': now.isoformat(),
        'pricing_mode': expediente.mode,
        'freight_mode': expediente.freight_mode,
        'transport_mode': expediente.transport_mode,
        'dispatch_mode': expediente.dispatch_mode,
    }
    expediente.save(update_fields=['snapshot_commercial'])

    # Guardar/Actualizar SAP (ART-04)
    ArtifactInstance.objects.update_or_create(
        expediente=expediente,
        artifact_type='ART-04',
        defaults={'payload': payload, 'status': 'completed'}
    )
    return {"message": "SAP Confirmado"}
