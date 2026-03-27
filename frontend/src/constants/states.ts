/**
 * S17-02: DESPACHO added to CANONICAL_STATES and STATE_BADGE_CLASSES
 * Single source of truth for expediente states used across the frontend.
 */
export const CANONICAL_STATES = [
  'REGISTRO',
  'PRODUCCION',
  'PREPARACION',
  'DESPACHO',
  'TRANSITO',
  'EN_DESTINO',
  'CERRADO',
  'CANCELADO',
] as const;

export type ExpedienteStatus = typeof CANONICAL_STATES[number];

/** Alias for backward compat with components using CanonicalState */
export type CanonicalState = ExpedienteStatus;

export const STATE_BADGE_CLASSES: Record<string, string> = {
  REGISTRO:    'bg-blue-50 text-blue-700 border border-blue-200',
  PRODUCCION:  'bg-amber-50 text-amber-700 border border-amber-200',
  PREPARACION: 'bg-orange-50 text-orange-700 border border-orange-200',
  DESPACHO:    'bg-purple-50 text-purple-700 border border-purple-200',
  TRANSITO:    'bg-sky-50 text-sky-700 border border-sky-200',
  EN_DESTINO:  'bg-teal-50 text-teal-700 border border-teal-200',
  CERRADO:     'bg-green-50 text-green-700 border border-green-200',
  CANCELADO:   'bg-red-50 text-red-700 border border-red-200',
};

/** Gate message label per state — what needs to be done to advance */
export const GATE_LABELS: Record<string, string> = {
  REGISTRO:    'Completar documentos de registro para avanzar a Producción',
  PRODUCCION:  'Finalizar producción para avanzar a Preparación',
  PREPARACION: 'Completar documentos de preparación para avanzar a Despacho',
  DESPACHO:    'Confirmar salida de aduana China para avanzar a Tránsito',
  TRANSITO:    'Confirmar arribo para avanzar a En Destino',
  EN_DESTINO:  'Registrar factura MWT y saldo pagado para cerrar el expediente',
  CERRADO:     '',
  CANCELADO:   '',
};

/** Human-readable label per state */
export const STATE_LABELS: Record<string, string> = {
  REGISTRO:    'Registro',
  PRODUCCION:  'Producción',
  PREPARACION: 'Preparación',
  DESPACHO:    'Despacho',
  TRANSITO:    'Tránsito',
  EN_DESTINO:  'En Destino',
  CERRADO:     'Cerrado',
  CANCELADO:   'Cancelado',
};

/** States shown in the pipeline board view (excludes terminal states) */
export const PIPELINE_STATES: ExpedienteStatus[] = [
  'REGISTRO',
  'PRODUCCION',
  'PREPARACION',
  'DESPACHO',
  'TRANSITO',
  'EN_DESTINO',
];

/** Ordered steps for the timeline component (includes CERRADO, excludes CANCELADO) */
export const TIMELINE_STEPS: CanonicalState[] = [
  'REGISTRO',
  'PRODUCCION',
  'PREPARACION',
  'DESPACHO',
  'TRANSITO',
  'EN_DESTINO',
  'CERRADO',
];
