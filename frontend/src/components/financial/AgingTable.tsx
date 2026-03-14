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
      <div className="px-5 py-3 border-b border-[var(--border)]">
        <h2 className="text-sm font-semibold text-[var(--navy)]">Aging por cliente</h2>
        <p className="text-xs text-[var(--text-disabled)]">Cuentas por cobrar segmentadas por vencimiento</p>
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
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="border-b border-[var(--border)] bg-[var(--bg-alt)]">
              <th className="text-left px-5 py-2.5 text-xs font-semibold text-[var(--text-tertiary)]">Cliente</th>
              <th className="text-right px-3 py-2.5 text-xs font-semibold text-[var(--text-tertiary)]">0–30d</th>
              <th className="text-right px-3 py-2.5 text-xs font-semibold text-[var(--text-tertiary)]">31–60d</th>
              <th className="text-right px-3 py-2.5 text-xs font-semibold text-[var(--text-tertiary)]">61–90d</th>
              <th className="text-right px-3 py-2.5 text-xs font-semibold text-[var(--coral)]">+90d</th>
              <th className="text-right px-5 py-2.5 text-xs font-semibold text-[var(--text-tertiary)]">Total</th>
              <th className="text-center px-3 py-2.5 text-xs font-semibold text-[var(--text-tertiary)]">Semáforo</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={7} className="text-center py-6 text-[var(--text-disabled)] text-xs">Cargando...</td>
              </tr>
            ) : rows.length === 0 ? (
              <tr>
                <td colSpan={7} className="text-center py-6 text-[var(--text-disabled)] text-xs">Sin datos</td>
              </tr>
            ) : (
              rows.map((row, i) => (
                <tr
                  key={row.client_id}
                  className="border-b border-[var(--divider)] hover:bg-[var(--surface-hover)] transition-colors"
                >
                  <td className="px-5 py-3 font-medium text-[var(--text-primary)]">{row.client_name}</td>
                  <td className="px-3 py-3 text-right font-mono text-[var(--text-secondary)]">{fmt(row.band_0_30)}</td>
                  <td className="px-3 py-3 text-right font-mono text-[var(--text-secondary)]">{fmt(row.band_31_60)}</td>
                  <td className="px-3 py-3 text-right font-mono text-[var(--amber)] font-medium">{fmt(row.band_61_90)}</td>
                  <td className="px-3 py-3 text-right font-mono text-[var(--coral)] font-semibold">{fmt(row.band_90_plus)}</td>
                  <td className="px-5 py-3 text-right font-mono font-semibold text-[var(--navy)]">{fmt(row.total)}</td>
                  <td className="px-3 py-3 text-center"><CreditBadge band={row.credit_band} /></td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
