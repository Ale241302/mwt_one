"use client";

import { useState, useEffect, useCallback } from 'react';
import { DollarSign, Plus } from 'lucide-react';
import api from '@/lib/api';

interface Cost {
  id: string;
  cost_type: string;
  description?: string;
  phase: string;
  amount: number;
  currency: string;
  visibility: 'internal' | 'client';
}

interface FinancialSummary {
  total_billed_client: number;
  total_costs: number;
  total_paid: number;
  payment_status: string;
  has_invoice: boolean;
}

interface CostsSectionProps {
  expedienteId: string;
  onRegisterCost: () => void;
}

export default function CostsSection({ expedienteId, onRegisterCost }: CostsSectionProps) {
  const [view, setView] = useState<'internal' | 'client'>('internal');
  const [costs, setCosts] = useState<Cost[]>([]);
  const [summary, setSummary] = useState<FinancialSummary | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [costsRes, summaryRes] = await Promise.all([
        api.get(`expedientes/${expedienteId}/costs/`),
        api.get(`expedientes/${expedienteId}/financial-summary/`).catch(() => ({ data: null })),
      ]);
      setCosts(costsRes.data?.results ?? costsRes.data ?? []);
      setSummary(summaryRes.data);
    } catch {
      /* costs endpoint failed */
    } finally {
      setLoading(false);
    }
  }, [expedienteId]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const displayedCosts = view === 'client'
    ? costs.filter(c => c.visibility === 'client')
    : costs;

  const totalCosts = displayedCosts.reduce((sum, c) => sum + c.amount, 0);
  const hasInvoice = summary?.has_invoice ?? false;
  const margin = hasInvoice && summary
    ? summary.total_billed_client - (summary.total_costs ?? totalCosts)
    : null;

  return (
    <div className="bg-surface rounded-2xl border border-border shadow-sm p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-2">
          <DollarSign className="w-4 h-4 text-text-secondary" />
          <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wider">Costos</h2>
          <span className="px-2 py-0.5 bg-border text-text-secondary text-xs font-semibold rounded-full">
            {costs.length}
          </span>
        </div>
        <div className="flex items-center gap-3">
          {/* Toggle */}
          <div className="flex rounded-lg border border-border overflow-hidden text-xs font-medium">
            {(['internal', 'client'] as const).map(v => (
              <button
                key={v}
                onClick={() => setView(v)}
                className={`px-3 py-1.5 transition-colors ${
                  view === v
                    ? 'bg-navy text-white'
                    : 'bg-surface text-text-secondary hover:bg-bg-alt'
                }`}
              >
                {v === 'internal' ? 'Vista Interna' : 'Vista Cliente'}
              </button>
            ))}
          </div>
          <button
            onClick={onRegisterCost}
            className="bg-navy hover:bg-slate-800 text-white px-3 py-1.5 rounded-lg text-xs font-medium transition-all shadow-sm active:scale-95 flex items-center gap-1.5"
          >
            <Plus size={13} /> Registrar Costo
          </button>
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div className="space-y-2">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-10 bg-border rounded animate-pulse" />
          ))}
        </div>
      ) : displayedCosts.length === 0 ? (
        <div className="text-center py-10 text-text-tertiary">
          <DollarSign className="w-8 h-8 mx-auto mb-2 opacity-30" />
          <p className="text-sm">Sin costos registrados</p>
        </div>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  {['Tipo', 'Descripción', 'Fase', 'Monto', ...(view === 'internal' ? ['Visibilidad'] : [])].map(h => (
                    <th key={h} className="text-left text-xs font-semibold text-text-tertiary uppercase tracking-wider pb-2 pr-4">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {displayedCosts.map(cost => (
                  <tr key={cost.id} className="hover:bg-bg-alt transition-colors">
                    <td className="py-2.5 pr-4">
                      <span className="px-2.5 py-1 text-xs font-semibold rounded-full border shadow-sm bg-surface text-text-secondary border-border">
                        {cost.cost_type}
                      </span>
                    </td>
                    <td className="py-2.5 pr-4 text-text-secondary">{cost.description || '—'}</td>
                    <td className="py-2.5 pr-4 text-text-secondary">{cost.phase}</td>
                    <td className="py-2.5 pr-4 font-medium text-text-primary">
                      {cost.currency} {cost.amount.toLocaleString('es-CO', { minimumFractionDigits: 2 })}
                    </td>
                    {view === 'internal' && (
                      <td className="py-2.5">
                        <span className={`px-2 py-0.5 text-xs font-semibold rounded-full ${
                          cost.visibility === 'client'
                            ? 'bg-blue-50 text-blue-700 border border-blue-200'
                            : 'bg-slate-100 text-slate-600 border border-slate-200'
                        }`}>
                          {cost.visibility === 'client' ? 'Cliente' : 'Interno'}
                        </span>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Footer */}
          <div className="mt-4 pt-4 border-t border-border flex items-center justify-between">
            <div className="text-sm text-text-secondary">
              Total costos: <span className="font-semibold text-text-primary">
                {totalCosts.toLocaleString('es-CO', { minimumFractionDigits: 2, style: 'decimal' })}
              </span>
            </div>
            {view === 'internal' && (
              <div className="text-sm text-text-secondary">
                Margen bruto:{' '}
                {margin === null ? (
                  <span className="text-text-tertiary italic">n/a (sin factura)</span>
                ) : (
                  <span className={`font-semibold ${
                    margin >= 0 ? 'text-mint' : 'text-coral'
                  }`}>
                    {margin >= 0 ? '+' : ''}
                    {margin.toLocaleString('es-CO', { minimumFractionDigits: 2 })}
                  </span>
                )}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
