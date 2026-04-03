// S22-14 — Tabla de GradeItems con multiplicadores de talla
"use client";

import React, { useEffect, useState } from 'react';
import { Loader2, Package } from 'lucide-react';
import api from '@/lib/api';

interface GradeItem {
  id: number;
  reference_code: string;
  grade_label: string;
  unit_price_usd: string;
  moq_total: number;
  size_multipliers: Record<string, number>;
  tip_type: string | null;
  ncm: string | null;
}

interface Props {
  versionId: number;
}

export function GradeItemsTable({ versionId }: Props) {
  const [items, setItems] = useState<GradeItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchItems = async () => {
      setLoading(true);
      try {
        const res = await api.get<GradeItem[]>(`pricing/pricelists/${versionId}/items/`);
        setItems(res.data);
      } catch (error) {
        console.error("Error fetching grade items:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchItems();
  }, [versionId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-2 py-8 text-text-tertiary text-xs bg-bg-alt/10 rounded-lg">
        <Loader2 size={14} className="animate-spin" /> Cargando ítems de la versión...
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="text-center py-10 bg-bg-alt/10 rounded-lg">
        <Package size={24} className="mx-auto mb-2 opacity-20" />
        <p className="text-xs text-text-tertiary">Sin ítems cargados en esta versión.</p>
      </div>
    );
  }

  // Colectar todas las tallas únicas para las columnas
  const allSizes = Array.from(
    new Set(items.flatMap((i) => Object.keys(i.size_multipliers)))
  ).sort();

  return (
    <div className="overflow-x-auto border border-border/60 rounded-lg shadow-sm">
      <table className="text-[11px] w-full bg-white">
        <thead>
          <tr className="bg-bg-alt/40 font-bold border-b border-border">
            <th className="text-left px-4 py-2 uppercase tracking-wider text-text-secondary">Referencia</th>
            <th className="text-left px-4 py-2 uppercase tracking-wider text-text-secondary">Grade</th>
            <th className="text-right px-4 py-2 uppercase tracking-wider text-text-secondary">Precio USD</th>
            <th className="text-right px-4 py-2 uppercase tracking-wider text-text-secondary">MOQ</th>
            {allSizes.map((s) => (
              <th key={s} className="text-center px-2 py-2 text-text-tertiary font-mono">{s}</th>
            ))}
            <th className="text-left px-4 py-2 uppercase tracking-wider text-text-secondary">Bico</th>
            <th className="text-left px-4 py-2 uppercase tracking-wider text-text-secondary">NCM</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {items.map((item) => (
            <tr key={item.id} className="hover:bg-brand/[0.02] transition-colors">
              <td className="px-4 py-2 font-mono font-semibold text-navy">{item.reference_code}</td>
              <td className="px-4 py-2 text-text-secondary">{item.grade_label}</td>
              <td className="px-4 py-2 text-right font-mono font-bold text-brand">${item.unit_price_usd}</td>
              <td className="px-4 py-2 text-right font-mono text-navy">{item.moq_total}</td>
              {allSizes.map((s) => (
                <td key={s} className="px-2 py-2 text-center">
                  {item.size_multipliers[s] != null ? (
                    <span className="inline-flex items-center justify-center w-5 h-5 rounded bg-brand/5 text-brand font-mono font-bold border border-brand/10">
                      {item.size_multipliers[s]}
                    </span>
                  ) : (
                    <span className="text-text-tertiary opacity-30">—</span>
                  )}
                </td>
              ))}
              <td className="px-4 py-2 text-[10px] uppercase font-medium">{item.tip_type ?? '—'}</td>
              <td className="px-4 py-2 font-mono text-text-tertiary">{item.ncm ?? '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
