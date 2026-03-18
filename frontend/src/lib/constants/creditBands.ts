/**
 * Semáforo de riesgo crediticio — ENT_PLAT_DESIGN_TOKENS
 * NUNCA mostrar solo color. Siempre color + texto + ícono Lucide.
 */
export type CreditBand = 'GREEN' | 'AMBER' | 'RED';

export const CREDIT_BAND_CONFIG: Record<CreditBand, {
  label: string;
  className: string;
  icon: string;
}> = {
  GREEN: { label: 'AL DÍA', className: 'bg-green-50 text-green-700 border-green-200', icon: 'check-circle' },
  AMBER: { label: 'RIESGO', className: 'bg-amber-50 text-amber-700 border-amber-200', icon: 'alert-triangle' },
  RED:   { label: 'CRÍTICO', className: 'bg-red-50 text-red-700 border-red-200', icon: 'alert-octagon' },
};
