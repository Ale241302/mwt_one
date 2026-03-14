// ─────────────────────────────────────────────────────────────────────────────
// ENT_OPS_STATE_MACHINE v1.2.2 — fuente de verdad de estados canónicos
// S9-01 — Sprint 9 Fase 0
// ─────────────────────────────────────────────────────────────────────────────

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

// Estados activos en pipeline (sin CERRADO ni CANCELADO)
export const PIPELINE_STATES = [
  'REGISTRO',
  'PRODUCCION',
  'PREPARACION',
  'DESPACHO',
  'TRANSITO',
  'EN_DESTINO',
] as const;

// Estados lineales del timeline (sin CANCELADO — va como badge lateral)
export const TIMELINE_STATES_CANONICAL = [
  { id: 'REGISTRO',    label: 'Registro' },
  { id: 'PRODUCCION',  label: 'Producción' },
  { id: 'PREPARACION', label: 'Preparación' },
  { id: 'DESPACHO',    label: 'Despacho' },
  { id: 'TRANSITO',    label: 'Tránsito' },
  { id: 'EN_DESTINO',  label: 'En destino' },
  { id: 'CERRADO',     label: 'Cerrado' },
] as const;

// Colores de badge por estado (design system ENT_PLAT_DESIGN_TOKENS)
export const STATE_BADGE_CLASSES: Record<string, string> = {
  REGISTRO:    'bg-slate-100 text-slate-700 border-slate-200',
  PRODUCCION:  'bg-blue-50 text-blue-700 border-blue-200',
  PREPARACION: 'bg-amber-50 text-amber-700 border-amber-200',
  DESPACHO:    'bg-orange-50 text-orange-700 border-orange-200',
  TRANSITO:    'bg-purple-50 text-purple-700 border-purple-200',
  EN_DESTINO:  'bg-teal-50 text-teal-700 border-teal-200',
  CERRADO:     'bg-emerald-50 text-emerald-700 border-emerald-200',
  CANCELADO:   'bg-red-50 text-red-700 border-red-200',
};

// Etiquetas legibles en español
export const STATE_LABELS: Record<string, string> = {
  REGISTRO:    'Registro',
  PRODUCCION:  'Producción',
  PREPARACION: 'Preparación',
  DESPACHO:    'Despacho',
  TRANSITO:    'Tránsito',
  EN_DESTINO:  'En destino',
  CERRADO:     'Cerrado',
  CANCELADO:   'Cancelado',
};
