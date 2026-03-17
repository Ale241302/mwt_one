/* Canonical States — Sprint 9.1
   Source of truth: ENT_OPS_STATE_MACHINE v1.2.2
   Fix S9.1-02: UTF-8 real en strings españoles (tildes y eñes)
   Exports adicionales: PIPELINE_STATES, STATE_BADGE_CLASSES, STATE_LABELS */

export const CANONICAL_STATES = [
  "REGISTRO", "PRODUCCION", "PREPARACION", "DESPACHO",
  "TRANSITO", "EN_DESTINO", "CERRADO", "CANCELADO",
] as const;

export type CanonicalState = (typeof CANONICAL_STATES)[number];

export const STATE_LABELS: Record<string, string> = {
  REGISTRO: "Registro",
  PRODUCCION: "Producción",
  PREPARACION: "Preparación",
  DESPACHO: "Despacho",
  TRANSITO: "Tránsito",
  EN_DESTINO: "En destino",
  CERRADO: "Cerrado",
  CANCELADO: "Cancelado",
};

export const STATE_BADGE_CLASSES: Record<string, string> = {
  REGISTRO: "badge-info",
  PRODUCCION: "badge-warning",
  PREPARACION: "badge-warning",
  DESPACHO: "badge-info",
  TRANSITO: "badge-info",
  EN_DESTINO: "badge-success",
  CERRADO: "badge-success",
  CANCELADO: "badge-critical",
};

export const PIPELINE_STATES = CANONICAL_STATES.filter(
  (s) => s !== "CERRADO" && s !== "CANCELADO"
);

export const TERMINAL_STATES = ["CERRADO", "CANCELADO"] as const;
