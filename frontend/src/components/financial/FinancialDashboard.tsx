'use client';
import { useState, useEffect } from 'react';
import { DollarSign, TrendingUp, AlertTriangle, Clock } from 'lucide-react';
import { KPICard } from './KPICard';
import { AgingTable } from './AgingTable';
import { CreditBadge } from '@/components/ui/CreditBadge';
import { CreditBand } from '@/lib/constants/creditBands';

interface FinancialKPIs {
  total_por_cobrar: number;
  cobrado_mes: number;
  vencido_critico: number;
  promedio_dias_cobro: number;
}

export function FinancialDashboard() {
  const [kpis, setKpis] = useState<FinancialKPIs | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/ui/financial/kpis/')
      .then(r => r.json())
      .then(data => setKpis(data))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="p-6 text-center text-slate-400 text-sm">Cargando KPIs financieros...</div>
  );

  return (
    <div className="flex flex-col gap-6 p-6">
      <div>
        <h1 className="text-xl font-semibold text-[#013A57]">Dashboard financiero</h1>
        <p className="text-sm text-slate-500">Visión consolidada de cobro y riesgo crediticio</p>
      </div>

      {/* KPI Cards — S9-10 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
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
          label="Cr\u00edtico (+90d)"
          value={`$${((kpis?.vencido_critico ?? 0) / 1000).toFixed(0)}K`}
          icon={AlertTriangle}
          trend="down"
        />
        <KPICard
          label="D\u00edas promedio cobro"
          value={`${kpis?.promedio_dias_cobro ?? 0}d`}
          icon={Clock}
          trend="neutral"
        />
      </div>

      {/* Aging — S9-11 */}
      <AgingTable />
    </div>
  );
}
