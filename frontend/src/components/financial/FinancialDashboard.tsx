'use client';
import { useState, useEffect, useCallback } from 'react';
import { DollarSign, TrendingUp, AlertTriangle, Clock, RefreshCw } from 'lucide-react';
import { KPICard } from './KPICard';
import { AgingTable } from './AgingTable';
import api from '@/lib/api';

interface FinancialKPIs {
  total_por_cobrar: number;
  cobrado_mes: number;
  vencido_critico: number;
  promedio_dias_cobro: number;
}

export function FinancialDashboard() {
  const [kpis, setKpis] = useState<FinancialKPIs | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchKpis = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.get('ui/financial/kpis/');
      setKpis(data);
    } catch (err: unknown) {
      const e = err as { message?: string };
      console.error('[FinancialDashboard] fetch error:', e);
      setError('No se pudieron cargar los KPIs financieros.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchKpis(); }, [fetchKpis]);

  return (
    <div className="flex flex-col gap-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-[var(--navy)]">Dashboard financiero</h1>
          <p className="text-sm text-[var(--text-tertiary)]">Visión consolidada de cobro y riesgo crediticio</p>
        </div>
        <button
          onClick={fetchKpis}
          disabled={loading}
          aria-label="Actualizar KPIs"
          className="flex items-center gap-1.5 text-xs text-[var(--text-tertiary)] hover:text-[var(--navy)] border border-[var(--border)] rounded-lg px-3 py-1.5 transition-colors disabled:opacity-40"
        >
          <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
          Actualizar
        </button>
      </div>

      {/* Error banner */}
      {error && (
        <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 rounded-xl px-4 py-3 text-sm">
          <AlertTriangle size={16} className="flex-shrink-0" />
          {error}
          <button onClick={fetchKpis} className="ml-auto text-xs font-semibold underline hover:no-underline">
            Reintentar
          </button>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {loading ? (
          // Skeleton KPI cards
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="card-mwt p-4 flex flex-col gap-3 animate-pulse">
              <div className="flex items-center justify-between">
                <div className="w-8 h-8 rounded-lg bg-[var(--border)]" />
                <div className="w-4 h-4 rounded bg-[var(--border)]" />
              </div>
              <div className="space-y-2">
                <div className="h-7 w-20 bg-[var(--border)] rounded" />
                <div className="h-3 w-24 bg-[var(--border)] rounded" />
              </div>
            </div>
          ))
        ) : (
          <>
            <KPICard
              label="Por cobrar"
              value={`$${((kpis?.total_por_cobrar ?? 0) / 1000).toFixed(0)}K`}
              icon={DollarSign}
              trend="neutral"
            />
            <KPICard
              label="Cobrado este mes"
              value={`$${((kpis?.cobrado_mes ?? 0) / 1000).toFixed(0)}K`}
              icon={TrendingUp}
              trend="up"
            />
            <KPICard
              label="Crítico (+90d)"
              value={`$${((kpis?.vencido_critico ?? 0) / 1000).toFixed(0)}K`}
              icon={AlertTriangle}
              trend="down"
            />
            <KPICard
              label="Días promedio cobro"
              value={`${kpis?.promedio_dias_cobro ?? 0}d`}
              icon={Clock}
              trend="neutral"
            />
          </>
        )}
      </div>

      {/* Aging Table */}
      <AgingTable />
    </div>
  );
}
