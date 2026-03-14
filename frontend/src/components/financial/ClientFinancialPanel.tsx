'use client';
import { useState, useEffect, useCallback } from 'react';
import { CreditBadge } from '@/components/ui/CreditBadge';
import { KPICard } from './KPICard';
import { DollarSign, Clock, AlertTriangle, TrendingUp } from 'lucide-react';
import { CreditBand } from '@/lib/constants/creditBands';
import api from '@/lib/api';

interface ClientFinancial {
  client_id: string;
  client_name: string;
  credit_band: CreditBand;
  total_por_cobrar: number;
  vencido_90_plus: number;
  dias_promedio_cobro: number;
  ultimo_pago?: string;
  limite_credito?: number;
}

interface ClientFinancialPanelProps {
  clientId: string;
}

export function ClientFinancialPanel({ clientId }: ClientFinancialPanelProps) {
  const [data, setData] = useState<ClientFinancial | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { data: res } = await api.get(`ui/clientes/${clientId}/financial/`);
      setData(res);
    } catch (err: unknown) {
      const e = err as { message?: string };
      console.error('[ClientFinancialPanel] fetch error:', e);
      setError('No se pudo cargar el estado crediticio.');
    } finally {
      setLoading(false);
    }
  }, [clientId]);

  useEffect(() => { fetchData(); }, [fetchData]);

  // Skeleton
  if (loading) {
    return (
      <div className="card-mwt p-5 flex flex-col gap-4 animate-pulse">
        <div className="flex items-center justify-between">
          <div className="h-4 w-32 bg-[var(--border)] rounded" />
          <div className="h-5 w-16 bg-[var(--border)] rounded-full" />
        </div>
        <div className="grid grid-cols-2 gap-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-20 bg-[var(--border)] rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  // Error
  if (error || !data) {
    return (
      <div className="card-mwt p-4 flex items-center gap-2 text-sm text-red-600 bg-red-50">
        <AlertTriangle size={15} className="flex-shrink-0" />
        {error ?? 'Error al cargar datos financieros'}
        <button onClick={fetchData} className="ml-auto text-xs font-semibold underline">Reintentar</button>
      </div>
    );
  }

  return (
    <div className="card-mwt p-5 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-[var(--navy)]">Estado crediticio</h3>
        <CreditBadge band={data.credit_band} />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <KPICard
          label="Por cobrar"
          value={`$${(data.total_por_cobrar / 1000).toFixed(0)}K`}
          icon={DollarSign}
          trend="neutral"
        />
        <KPICard
          label="Crítico +90d"
          value={`$${(data.vencido_90_plus / 1000).toFixed(0)}K`}
          icon={AlertTriangle}
          trend={data.vencido_90_plus > 0 ? 'down' : 'neutral'}
        />
        <KPICard
          label="Días promedio"
          value={`${data.dias_promedio_cobro}d`}
          icon={Clock}
          trend="neutral"
        />
        {data.limite_credito != null && (
          <KPICard
            label="Límite crédito"
            value={`$${(data.limite_credito / 1000).toFixed(0)}K`}
            icon={TrendingUp}
            trend="neutral"
          />
        )}
      </div>

      {data.ultimo_pago && (
        <p className="text-xs text-[var(--text-tertiary)]">
          Último pago:{' '}
          <span className="font-medium text-[var(--text-secondary)]">{data.ultimo_pago}</span>
        </p>
      )}
    </div>
  );
}
