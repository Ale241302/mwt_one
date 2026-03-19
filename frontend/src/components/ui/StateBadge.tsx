'use client';
import { STATE_LABELS, STATE_BADGE_CLASSES, CanonicalState } from '@/constants/states';

const STATE_COLORS: Record<string, string> = STATE_BADGE_CLASSES;


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
