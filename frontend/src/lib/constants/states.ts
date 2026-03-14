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
  REGISTRO:    'Registro',
  PRODUCCION:  'Producción',
  PREPARACION: 'Preparación',
  DESPACHO:    'Despacho',
  TRANSITO:    'Tránsito',
  EN_DESTINO:  'En destino',
  CERRADO:     'Cerrado',
  CANCELADO:   'Cancelado',
};

/** Orden de pasos en el timeline (7 pasos lineales canónicos, sin CANCELADO) */
export const TIMELINE_STEPS: CanonicalState[] = [
  'REGISTRO',
  'PRODUCCION',
  'PREPARACION',
  'DESPACHO',
  'TRANSITO',
  'EN_DESTINO',
  'CERRADO',
];

/**
 * TIMELINE_STATES_CANONICAL
 * Mismos 7 pasos del timeline pero en formato { id, label } para
 * compatibilidad con el componente de timeline en expedientes/[id]/page.tsx
 */
export const TIMELINE_STATES_CANONICAL: { id: CanonicalState; label: string }[] = [
  { id: 'REGISTRO',    label: 'Registro' },
  { id: 'PRODUCCION',  label: 'Producción' },
  { id: 'PREPARACION', label: 'Preparación' },
  { id: 'DESPACHO',    label: 'Despacho' },
  { id: 'TRANSITO',    label: 'Tránsito' },
  { id: 'EN_DESTINO',  label: 'En destino' },
  { id: 'CERRADO',     label: 'Cerrado' },
];
