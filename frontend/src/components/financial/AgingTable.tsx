'use client';
import { useState, useEffect } from 'react';
import { CreditBadge } from '@/components/ui/CreditBadge';
import { CreditBand } from '@/lib/constants/creditBands';

interface AgingRow {
  client_id: string;
  client_name: string;
  band_0_30: number;
  band_31_60: number;
  band_61_90: number;
  band_90_plus: number;
  total: number;
  credit_band: CreditBand;
}

export function AgingTable() {
  const [rows, setRows] = useState<AgingRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/ui/financial/aging/')
      .then(r => r.json())
      .then(data => setRows(Array.isArray(data) ? data : (data.results ?? [])))
      .finally(() => setLoading(false));
  }, []);

  const fmt = (n: number) => n > 0 ? `$${(n / 1000).toFixed(0)}K` : '—';

  return (
    <div className="card-mwt overflow-hidden">
      <div className="px-5 py-3 border-b border-slate-100">
        <h2 className="text-sm font-semibold text-[#013A57]">Aging por cliente</h2>
        <p className="text-xs text-slate-400">Cuentas por cobrar segmentadas por vencimiento</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50">
              <th className="text-left px-5 py-2.5 text-xs font-semibold text-slate-500">Cliente</th>
              <th className="text-right px-3 py-2.5 text-xs font-semibold text-slate-500">0–30d</th>
              <th className="text-right px-3 py-2.5 text-xs font-semibold text-slate-500">31–60d</th>
              <th className="text-right px-3 py-2.5 text-xs font-semibold text-slate-500">61–90d</th>
              <th className="text-right px-3 py-2.5 text-xs font-semibold text-[#DC2626]">+90d</th>
              <th className="text-right px-5 py-2.5 text-xs font-semibold text-slate-500">Total</th>
              <th className="text-center px-3 py-2.5 text-xs font-semibold text-slate-500">Semaforo</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} className="text-center py-6 text-slate-400 text-xs">Cargando...</td></tr>
            ) : rows.length === 0 ? (
              <tr><td colSpan={7} className="text-center py-6 text-slate-300 text-xs">Sin datos</td></tr>
            ) : rows.map(row => (
              <tr key={row.client_id} className="border-b border-slate-50 hover:bg-slate-50">
                <td className="px-5 py-3 font-medium text-slate-700">{row.client_name}</td>
                <td className="px-3 py-3 text-right font-mono text-slate-600">{fmt(row.band_0_30)}</td>
                <td className="px-3 py-3 text-right font-mono text-slate-600">{fmt(row.band_31_60)}</td>
                <td className="px-3 py-3 text-right font-mono text-amber-600 font-medium">{fmt(row.band_61_90)}</td>
                <td className="px-3 py-3 text-right font-mono text-red-600 font-semibold">{fmt(row.band_90_plus)}</td>
                <td className="px-5 py-3 text-right font-mono font-semibold text-[#013A57]">{fmt(row.total)}</td>
                <td className="px-3 py-3 text-center"><CreditBadge band={row.credit_band} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
