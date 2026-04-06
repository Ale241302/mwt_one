// S23-14 — RebateProgressBar: barra de progreso de rebate para Client Console
// IMPORTANTE: NO mostrar rebate_value, accrued_rebate ni umbrales absolutos
"use client";

import React from 'react';
import { TrendingUp, CheckCircle, Clock } from 'lucide-react';

// ─── Tipos alineados con RebateProgressPortalSerializer ───────────────────────
type ThresholdType = 'none' | 'amount' | 'units';

export interface RebateProgressItem {
  program_name: string;
  period: string;           // e.g. "Q1 2026" o "2026-01-01 / 2026-03-31"
  threshold_type: ThresholdType;
  progress_percentage: number; // 0-100; backend calcula esto, nunca calcularlo aquí
  threshold_met: boolean;
}

interface Props {
  items: RebateProgressItem[];
  loading?: boolean;
}

// ─── Barra individual ─────────────────────────────────────────────────────────
function ProgressBar({
  item,
}: {
  item: RebateProgressItem;
}) {
  const pct = Math.min(100, Math.max(0, item.progress_percentage));

  const barColor = item.threshold_met
    ? 'bg-emerald-500'
    : pct >= 75
    ? 'bg-brand'
    : pct >= 40
    ? 'bg-amber-400'
    : 'bg-text-tertiary';

  const thresholdLabel: Record<ThresholdType, string> = {
    none:   'Sin umbral mínimo',
    amount: 'Progreso por monto',
    units:  'Progreso por unidades',
  };

  return (
    <div className="card px-5 py-4 space-y-3">
      {/* Cabecera */}
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-sm font-semibold text-text-primary">{item.program_name}</p>
          <p className="text-xs text-text-tertiary mt-0.5">
            {item.period} · {thresholdLabel[item.threshold_type]}
          </p>
        </div>
        {item.threshold_met ? (
          <div className="flex items-center gap-1 text-emerald-600">
            <CheckCircle size={14} />
            <span className="text-xs font-semibold">Umbral alcanzado</span>
          </div>
        ) : (
          <div className="flex items-center gap-1 text-text-tertiary">
            <Clock size={13} />
            <span className="text-xs">En progreso</span>
          </div>
        )}
      </div>

      {/* Barra de progreso */}
      <div>
        <div className="flex justify-between items-center mb-1">
          <span className="text-[10px] text-text-tertiary">Progreso</span>
          <span className="text-xs font-bold tabular-nums text-text-primary">
            {item.threshold_type === 'none' ? '100%' : `${pct.toFixed(0)}%`}
          </span>
        </div>
        <div className="h-2 w-full bg-bg-alt rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-700 ${barColor}`}
            style={{ width: item.threshold_type === 'none' ? '100%' : `${pct}%` }}
          />
        </div>
      </div>
    </div>
  );
}

// ─── Skeleton loader ──────────────────────────────────────────────────────────
function SkeletonCard() {
  return (
    <div className="card px-5 py-4 space-y-3 animate-pulse">
      <div className="h-4 w-1/2 bg-bg-alt rounded" />
      <div className="h-3 w-1/3 bg-bg-alt rounded" />
      <div className="h-2 w-full bg-bg-alt rounded-full" />
    </div>
  );
}

// ─── Componente exportado ─────────────────────────────────────────────────────
export function RebateProgressBar({ items, loading = false }: Props) {
  if (loading) {
    return (
      <div className="space-y-3">
        <SkeletonCard />
        <SkeletonCard />
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="card p-10 text-center">
        <TrendingUp size={36} className="mx-auto mb-3 opacity-20 text-text-tertiary" />
        <p className="text-sm text-text-tertiary">No tienes programas de incentivo activos en este período.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {items.map((item, i) => (
        <ProgressBar key={`${item.program_name}-${i}`} item={item} />
      ))}
    </div>
  );
}
