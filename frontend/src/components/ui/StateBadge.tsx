'use client';
import { STATE_LABELS, CanonicalState } from '@/lib/constants/states';

const STATE_COLORS: Record<CanonicalState, { bg: string; text: string }> = {
  REGISTRO:    { bg: '#EFF6FF', text: '#1D4ED8' },
  PRODUCCION:  { bg: '#FFF7ED', text: '#C2410C' },
  PREPARACION: { bg: '#FFFBEB', text: '#B45309' },
  DESPACHO:    { bg: '#F5F3FF', text: '#6D28D9' },
  TRANSITO:    { bg: '#F0F9FF', text: '#0369A1' },
  EN_DESTINO:  { bg: '#F0FAF6', text: '#0E8A6D' },
  CERRADO:     { bg: '#F1F5F9', text: '#475569' },
  CANCELADO:   { bg: '#FEF2F2', text: '#DC2626' },
};

interface StateBadgeProps {
  state: CanonicalState;
  className?: string;
}

export function StateBadge({ state, className = '' }: StateBadgeProps) {
  const colors = STATE_COLORS[state] ?? { bg: '#F1F5F9', text: '#475569' };
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold tracking-[0.5px] uppercase ${className}`}
      style={{ backgroundColor: colors.bg, color: colors.text }}
    >
      {STATE_LABELS[state] ?? state}
    </span>
  );
}
