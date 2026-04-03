// S22-15 — Sub-fila expandible con multiplicadores por talla
"use client";

import React from 'react';

interface Props {
  sizeMultipliers: Record<string, number>;
  moqTotal: number;
  gradePriceUsd: string | null;
}

export function SizeMultipliersExpand({ sizeMultipliers, moqTotal, gradePriceUsd }: Props) {
  const entries = Object.entries(sizeMultipliers);

  if (entries.length === 0) {
    return (
      <div className="px-6 py-3 text-xs text-text-tertiary bg-[var(--bg-alt)]">
        Sin multiplicadores de talla registrados.
      </div>
    );
  }

  return (
    <div className="px-6 py-4 bg-[var(--bg-alt)] border-t border-border">
      <div className="flex items-center gap-6 mb-3">
        <div className="text-xs">
          <span className="text-text-tertiary">MOQ Grade:</span>{' '}
          <span className="font-mono font-semibold text-text-primary">{moqTotal}</span>
        </div>
        {gradePriceUsd && (
          <div className="text-xs">
            <span className="text-text-tertiary">Precio base:</span>{' '}
            <span className="font-mono font-semibold text-text-primary">${gradePriceUsd}</span>
          </div>
        )}
      </div>
      <div className="flex flex-wrap gap-2">
        {entries.map(([size, multiplier]) => (
          <div
            key={size}
            className="flex flex-col items-center rounded-lg border border-border bg-white px-3 py-2 min-w-[56px]"
          >
            <span className="text-xs text-text-tertiary font-medium">{size}</span>
            <span className="text-sm font-bold font-mono text-brand mt-0.5">{multiplier}</span>
            <span className="text-[10px] text-text-tertiary">pares</span>
          </div>
        ))}
      </div>
    </div>
  );
}
