/**
 * S9-01 — ENT_OPS_STATE_MACHINE v1.2.2
 * Únicos estados canónicos válidos para el pipeline.
 * NO agregar más sin aprobación CEO.
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

export type CanonicalState = typeof CANONICAL_STATES[number];

/** Estados activos en el pipeline Kanban (excluye terminales) */
export const PIPELINE_STATES: CanonicalState[] = [
  'REGISTRO',
  'PRODUCCION',
  'PREPARACION',
  'DESPACHO',
  'TRANSITO',
  'EN_DESTINO',
];

/** Estados terminales */
export const TERMINAL_STATES: CanonicalState[] = ['CERRADO', 'CANCELADO'];

/** Labels de display en español */
export const STATE_LABELS: Record<CanonicalState, string> = {
  REGISTRO: 'Registro',
  PRODUCCION: 'Producción',
  PREPARACION: 'Preparación',
  DESPACHO: 'Despacho',
  TRANSITO: 'Tránsito',
  EN_DESTINO: 'En destino',
  CERRADO: 'Cerrado',
  CANCELADO: 'Cancelado',
};

/** Orden de pasos en el timeline (7 pasos lineales canónicos) */
export const TIMELINE_STEPS: CanonicalState[] = [
  'REGISTRO',
  'PRODUCCION',
  'PREPARACION',
  'DESPACHO',
  'TRANSITO',
  'EN_DESTINO',
  'CERRADO',
];
