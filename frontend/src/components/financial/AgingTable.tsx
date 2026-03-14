'use client';
import { useState, useEffect, useCallback } from 'react';
import { CreditBadge } from '@/components/ui/CreditBadge';
import { CreditBand } from '@/lib/constants/creditBands';
import { AlertTriangle, BarChart3 } from 'lucide-react';
import api from '@/lib/api';

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
  const [error, setError] = useState<string | null>(null);

  const fetchAging = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.get('ui/financial/aging/');
      setRows(Array.isArray(data) ? data : (data.results ?? []));
    } catch (err: unknown) {
      const e = err as { message?: string };
      console.error('[AgingTable] fetch error:', e);
      setError('No se pudo cargar la tabla de aging.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAging(); }, [fetchAging]);

  const fmt = (n: number) => n > 0 ? `$${(n / 1000).toFixed(0)}K` : '—';

  return (
    <div className="card-mwt overflow-hidden">
      <div className="px-5 py-3 border-b border-[var(--border)] flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-[var(--navy)]">Aging por cliente</h2>
          <p className="text-xs text-[var(--text-tertiary)]">Cuentas por cobrar segmentadas por vencimiento</p>
        </div>
        {/* Total rows badge */}
        {!loading && rows.length > 0 && (
          <span className="text-xs bg-[var(--bg-alt)] text-[var(--text-tertiary)] px-2 py-0.5 rounded-full font-medium">
            {rows.length} clientes
          </span>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 bg-red-50 border-b border-red-100 text-red-700 px-5 py-2.5 text-xs">
          <AlertTriangle size={13} className="flex-shrink-0" />
          {error}
          <button onClick={fetchAging} className="ml-auto font-semibold underline">Reintentar</button>
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[var(--border)] bg-[var(--bg-alt)] text-left">
              <th className="text-left px-5 py-2.5 text-xs font-semibold text-[var(--text-tertiary)] uppercase tracking-[0.5px]">Cliente</th>
              <th className="text-right px-3 py-2.5 text-xs font-semibold text-[var(--text-tertiary)] uppercase tracking-[0.5px]">0–30d</th>
              <th className="text-right px-3 py-2.5 text-xs font-semibold text-[var(--text-tertiary)] uppercase tracking-[0.5px]">31–60d</th>
              <th className="text-right px-3 py-2.5 text-xs font-semibold text-amber-500 uppercase tracking-[0.5px]">61–90d</th>
              <th className="text-right px-3 py-2.5 text-xs font-semibold text-red-500 uppercase tracking-[0.5px]">+90d</th>
              <th className="text-right px-5 py-2.5 text-xs font-semibold text-[var(--text-tertiary)] uppercase tracking-[0.5px]">Total</th>
              <th className="text-center px-3 py-2.5 text-xs font-semibold text-[var(--text-tertiary)] uppercase tracking-[0.5px]">Semáforo</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              // Skeleton rows
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i} className="border-b border-[var(--divider)] animate-pulse">
                  <td className="px-5 py-3"><div className="h-4 bg-[var(--border)] rounded w-32" /></td>
                  {Array.from({ length: 5 }).map((_, j) => (
                    <td key={j} className="px-3 py-3 text-right"><div className="h-4 bg-[var(--border)] rounded w-12 ml-auto" /></td>
                  ))}
                  <td className="px-3 py-3"><div className="h-5 bg-[var(--border)] rounded-full w-16 mx-auto" /></td>
                </tr>
              ))
            ) : rows.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-5 py-12 text-center">
                  <div className="flex flex-col items-center gap-2 text-[var(--text-disabled)]">
                    <BarChart3 size={28} className="opacity-30" />
                    <span className="text-xs">Sin datos de aging disponibles</span>
                  </div>
                </td>
              </tr>
            ) : rows.map((row, i) => (
              <tr
                key={row.client_id}
                className={`border-b border-[var(--divider)] hover:bg-[var(--surface-hover)] transition-colors ${
                  i % 2 === 0 ? 'bg-[var(--surface)]' : 'bg-[var(--bg-alt)]/30'
                }`}
              >
                <td className="px-5 py-3 font-medium text-[var(--text-primary)]">{row.client_name}</td>
                <td className="px-3 py-3 text-right font-mono text-[var(--text-secondary)] text-sm">{fmt(row.band_0_30)}</td>
                <td className="px-3 py-3 text-right font-mono text-[var(--text-secondary)] text-sm">{fmt(row.band_31_60)}</td>
                <td className="px-3 py-3 text-right font-mono text-amber-600 font-medium text-sm">{fmt(row.band_61_90)}</td>
                <td className="px-3 py-3 text-right font-mono text-red-600 font-semibold text-sm">{fmt(row.band_90_plus)}</td>
                <td className="px-5 py-3 text-right font-mono font-semibold text-[var(--navy)] text-sm">{fmt(row.total)}</td>
                <td className="px-3 py-3 text-center"><CreditBadge band={row.credit_band} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
