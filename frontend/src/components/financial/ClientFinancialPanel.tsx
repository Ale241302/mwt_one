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

  if (!data) return (
    <div className="p-4 text-sm text-[var(--text-disabled)]">Cargando...</div>
  );

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
