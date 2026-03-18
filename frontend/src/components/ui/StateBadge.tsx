'use client';
import { STATE_LABELS, CanonicalState } from '@/lib/constants/states';

const STATE_COLORS: Record<CanonicalState, string> = {
  REGISTRO:    'bg-blue-50 text-blue-700',
  PRODUCCION:  'bg-orange-50 text-orange-700',
  PREPARACION: 'bg-amber-50 text-amber-700',
  DESPACHO:    'bg-purple-50 text-purple-700',
  TRANSITO:    'bg-sky-50 text-sky-700',
  EN_DESTINO:  'bg-green-50 text-green-700',
  CERRADO:     'bg-slate-100 text-slate-600',
  CANCELADO:   'bg-red-50 text-red-600',
};

interface StateBadgeProps {
  state: CanonicalState;
  className?: string;
}

export function StateBadge({ state, className = '' }: StateBadgeProps) {
  const colorClass = STATE_COLORS[state] ?? 'bg-slate-100 text-slate-600';
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold tracking-[0.5px] uppercase ${colorClass} ${className}`}
    >
      {STATE_LABELS[state] ?? state}
    </span>
  );
}
