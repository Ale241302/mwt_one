// S22-14 — Tabla de GradeItems con multiplicadores de talla
"use client";

import React, { useEffect, useState } from 'react';
import { Loader2 } from 'lucide-react';

interface GradeItem {
  id: number;
  reference_code: string;
  grade_label: string;
  unit_price_usd: string;
  moq_total: number;
  available_sizes: string[];
  size_multipliers: Record<string, number>;
  tip_type: string | null;
  ncm: string | null;
}

interface Props {
  versionId: number;
}

// Mock — reemplazar con GET /api/pricing/pricelists/{id}/items/
const MOCK_ITEMS: GradeItem[] = [
  {
    id: 1, reference_code: 'MRL-0001', grade_label: 'G1 (33-38)',
    unit_price_usd: '28.50', moq_total: 12,
    available_sizes: ['33/34','35/36','37/38'],
    size_multipliers: { '33/34': 2, '35/36': 4, '37/38': 6 },
    tip_type: 'Composite', ncm: '6402.99.90',
  },
  {
    id: 2, reference_code: 'MRL-0002', grade_label: 'G2 (39-44)',
    unit_price_usd: '31.00', moq_total: 12,
    available_sizes: ['39/40','41/42','43/44'],
    size_multipliers: { '39/40': 4, '41/42': 4, '43/44': 4 },
    tip_type: 'Steel', ncm: '6402.99.90',
  },
  {
    id: 3, reference_code: 'MRL-0003', grade_label: 'G3 (45-48)',
    unit_price_usd: '34.75', moq_total: 6,
    available_sizes: ['45/46','47/48'],
    size_multipliers: { '45/46': 4, '47/48': 2 },
    tip_type: 'Composite', ncm: '6402.99.90',
  },
];

export function GradeItemsTable({ versionId }: Props) {
  const [items, setItems] = useState<GradeItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    // TODO: fetch real `/api/pricing/pricelists/${versionId}/items/`
    setTimeout(() => {
      setItems(MOCK_ITEMS);
      setLoading(false);
    }, 600);
  }, [versionId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-2 py-8 text-text-tertiary text-xs">
        <Loader2 size={14} className="animate-spin" /> Cargando ítems...
      </div>
    );
  }

  if (items.length === 0) {
    return <p className="text-xs text-text-tertiary text-center py-6">Sin ítems en esta versión.</p>;
  }

  // Colectar todas las tallas únicas para las columnas
  const allSizes = Array.from(
    new Set(items.flatMap((i) => i.available_sizes))
  );

  return (
    <div className="overflow-x-auto">
      <table className="text-xs w-full">
        <thead>
          <tr className="bg-[var(--bg-alt)]">
            <th className="text-left px-4 py-2">Referencia</th>
            <th className="text-left px-4 py-2">Grade</th>
            <th className="text-right px-4 py-2">Precio USD</th>
            <th className="text-right px-4 py-2">MOQ</th>
            {allSizes.map((s) => (
              <th key={s} className="text-center px-3 py-2 text-text-tertiary">{s}</th>
            ))}
            <th className="text-left px-4 py-2">Bico</th>
            <th className="text-left px-4 py-2">NCM</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id} className="border-t border-border hover:bg-[var(--bg-alt)]/50 transition-colors">
              <td className="px-4 py-2 font-mono font-medium">{item.reference_code}</td>
              <td className="px-4 py-2">{item.grade_label}</td>
              <td className="px-4 py-2 text-right font-mono">${item.unit_price_usd}</td>
              <td className="px-4 py-2 text-right font-mono">{item.moq_total}</td>
              {allSizes.map((s) => (
                <td key={s} className="px-3 py-2 text-center">
                  {item.size_multipliers[s] != null ? (
                    <span className="inline-flex items-center justify-center w-6 h-6 rounded bg-brand/10 text-brand font-mono font-semibold">
                      {item.size_multipliers[s]}
                    </span>
                  ) : (
                    <span className="text-text-tertiary">—</span>
                  )}
                </td>
              ))}
              <td className="px-4 py-2 text-text-secondary">{item.tip_type ?? '—'}</td>
              <td className="px-4 py-2 font-mono text-text-secondary">{item.ncm ?? '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
