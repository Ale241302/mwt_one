/**
 * Semáforo de riesgo crediticio — ENT_PLAT_DESIGN_TOKENS
 * NUNCA mostrar solo color. Siempre color + texto + ícono Lucide.
 */
export type CreditBand = 'GREEN' | 'AMBER' | 'RED';

export const CREDIT_BAND_CONFIG: Record<CreditBand, {
  label: string;
  bg: string;
  text: string;
  icon: string;
}> = {
  GREEN: { label: 'AL DÍA', bg: '#F0FAF6', text: '#0E8A6D', icon: 'check-circle' },
  AMBER: { label: 'RIESGO', bg: '#FFF7ED', text: '#B45309', icon: 'alert-triangle' },
  RED:   { label: 'CRÍTICO', bg: '#FEF2F2', text: '#DC2626', icon: 'alert-octagon' },
};
