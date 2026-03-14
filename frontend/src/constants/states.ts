/**
 * S9-01 — CANONICAL_STATES
 * Fuente única de verdad para estados de expedientes y artefactos.
 * Usar estos valores en todo el codebase; nunca strings literales.
 */

export const CANONICAL_STATES = {
  // ── Expediente states ──────────────────────────────────────────────────
  EXPEDIENTE: {
    ACTIVO:      'activo',
    BLOQUEADO:   'bloqueado',
    CANCELADO:   'cancelado',
    COMPLETADO:  'completado',
    PENDIENTE:   'pendiente',
  },

  // ── Artefacto states ───────────────────────────────────────────────────
  ARTEFACTO: {
    DRAFT:       'draft',
    VIGENTE:     'vigente',
    SUPERSEDED:  'superseded',
    VOID:        'void',
  },

  // ── Pago / Costo states ────────────────────────────────────────────────
  PAGO: {
    PENDIENTE:   'pendiente',
    PAGADO:      'pagado',
    VENCIDO:     'vencido',
    ANULADO:     'anulado',
  },

  // ── Liquidación states ─────────────────────────────────────────────────
  LIQUIDACION: {
    BORRADOR:    'borrador',
    EMITIDA:     'emitida',
    APROBADA:    'aprobada',
    RECHAZADA:   'rechazada',
    CERRADA:     'cerrada',
  },

  // ── Nodo / Nodo states ─────────────────────────────────────────────────
  NODO: {
    ACTIVO:      'activo',
    INACTIVO:    'inactivo',
    SUSPENDIDO:  'suspendido',
  },

  // ── Transfer states ────────────────────────────────────────────────────
  TRANSFER: {
    PENDIENTE:   'pendiente',
    EN_PROCESO:  'en_proceso',
    COMPLETADO:  'completado',
    FALLIDO:     'fallido',
    REVERTIDO:   'revertido',
  },

  // ── Pipeline stage states ──────────────────────────────────────────────
  PIPELINE: {
    PROSPECTO:         'prospecto',
    CONTACTO_INICIAL:  'contacto_inicial',
    DOCUMENTACION:     'documentacion',
    EVALUACION:        'evaluacion',
    APROBADO:          'aprobado',
    RECHAZADO:         'rechazado',
  },
} as const;

// ── Type helpers ────────────────────────────────────────────────────────────
export type ExpedienteState  = typeof CANONICAL_STATES.EXPEDIENTE[keyof typeof CANONICAL_STATES.EXPEDIENTE];
export type ArtefactoState   = typeof CANONICAL_STATES.ARTEFACTO[keyof typeof CANONICAL_STATES.ARTEFACTO];
export type PagoState        = typeof CANONICAL_STATES.PAGO[keyof typeof CANONICAL_STATES.PAGO];
export type LiquidacionState = typeof CANONICAL_STATES.LIQUIDACION[keyof typeof CANONICAL_STATES.LIQUIDACION];
export type NodoState        = typeof CANONICAL_STATES.NODO[keyof typeof CANONICAL_STATES.NODO];
export type TransferState    = typeof CANONICAL_STATES.TRANSFER[keyof typeof CANONICAL_STATES.TRANSFER];
export type PipelineStage    = typeof CANONICAL_STATES.PIPELINE[keyof typeof CANONICAL_STATES.PIPELINE];

// ── Badge color map (para usar con .badge-mwt en globals.css) ───────────────
export const STATE_BADGE_CLASS: Record<string, string> = {
  // Expediente
  activo:       'badge-success',
  bloqueado:    'badge-warning',
  cancelado:    'badge-danger',
  completado:   'badge-info',
  pendiente:    'badge-neutral',
  // Artefacto
  draft:        'badge-neutral',
  vigente:      'badge-success',
  superseded:   'badge-warning',
  void:         'badge-danger',
  // Pago
  pagado:       'badge-success',
  vencido:      'badge-danger',
  anulado:      'badge-neutral',
  // Liquidacion
  borrador:     'badge-neutral',
  emitida:      'badge-info',
  aprobada:     'badge-success',
  rechazada:    'badge-danger',
  cerrada:      'badge-neutral',
  // Nodo
  inactivo:     'badge-neutral',
  suspendido:   'badge-warning',
  // Transfer
  en_proceso:   'badge-info',
  completado:   'badge-success',
  fallido:      'badge-danger',
  revertido:    'badge-warning',
  // Pipeline
  prospecto:        'badge-neutral',
  contacto_inicial: 'badge-info',
  documentacion:    'badge-info',
  evaluacion:       'badge-warning',
  aprobado:         'badge-success',
  rechazado:        'badge-danger',
};
