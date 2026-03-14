'use client';
import { useState, useEffect } from 'react';
import { Kanban, Table2, Calendar } from 'lucide-react';
import { PIPELINE_STATES, STATE_LABELS, CanonicalState } from '@/lib/constants/states';
import { PipelineColumn } from './PipelineColumn';
import { PipelineFilters } from './PipelineFilters';
import { CreditBand } from '@/lib/constants/creditBands';

export interface ExpedienteCard {
  id: string;
  ref: string;
  client: string;
  brand: string;
  brand_color?: string;
  status: CanonicalState;
  credit_band: CreditBand;
  is_blocked: boolean;
  pending_action?: string;
  artifacts_done: number;
  artifacts_total: number;
}

export type ViewMode = 'pipeline' | 'table';

export function PipelineView() {
  const [viewMode, setViewMode] = useState<ViewMode>('pipeline');
  const [expedientes, setExpedientes] = useState<ExpedienteCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<{
    brand: string;
    credit_band: CreditBand | '';
    client: string;
    only_blocked: boolean;
  }>({ brand: '', credit_band: '', client: '', only_blocked: false });

  useEffect(() => {
    async function fetchAll() {
      setLoading(true);
      try {
        const results = await Promise.all(
          PIPELINE_STATES.map(s =>
            fetch(`/api/ui/expedientes/?status=${s}`).then(r => r.json())
          )
        );
        const all: ExpedienteCard[] = results.flatMap((r: { results?: ExpedienteCard[] } | ExpedienteCard[]) =>
          Array.isArray(r) ? r : (r.results ?? [])
        );
        setExpedientes(all);
      } finally {
        setLoading(false);
      }
    }
    fetchAll();
  }, []);

  const filtered = expedientes.filter(e => {
    if (filters.brand && e.brand !== filters.brand) return false;
    if (filters.credit_band && e.credit_band !== filters.credit_band) return false;
    if (filters.client && !e.client.toLowerCase().includes(filters.client.toLowerCase())) return false;
    if (filters.only_blocked && !e.is_blocked) return false;
    return true;
  });

  const byState = (state: CanonicalState) => filtered.filter(e => e.status === state);

  return (
    <div className="flex flex-col h-full gap-4 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-[#013A57]">Pipeline operativo</h1>
          <p className="text-sm text-slate-500">{filtered.length} expediente{filtered.length !== 1 ? 's' : ''}</p>
        </div>

        {/* View toggle */}
        <div className="flex items-center gap-1 border border-slate-200 rounded-xl p-1 bg-white">
          <button
            onClick={() => setViewMode('pipeline')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              viewMode === 'pipeline'
                ? 'bg-[#013A57] text-white'
                : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            <Kanban size={14} />
            Pipeline
          </button>
          <button
            onClick={() => setViewMode('table')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              viewMode === 'table'
                ? 'bg-[#013A57] text-white'
                : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            <Table2 size={14} />
            Tabla
          </button>
          <button
            disabled
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium text-slate-300 cursor-not-allowed"
            title="Disponible en Sprint 10"
          >
            <Calendar size={14} />
            Calendario
          </button>
        </div>
      </div>

      {/* Filters */}
      <PipelineFilters
        expedientes={expedientes}
        filters={filters}
        onChange={setFilters}
      />

      {/* Kanban grid */}
      {loading ? (
        <div className="flex-1 flex items-center justify-center text-slate-400 text-sm">Cargando pipeline...</div>
      ) : (
        <div className="flex-1 overflow-x-auto">
          <div className="flex gap-3 h-full min-w-max pb-4">
            {PIPELINE_STATES.map(state => (
              <PipelineColumn
                key={state}
                state={state}
                label={STATE_LABELS[state]}
                cards={byState(state)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
