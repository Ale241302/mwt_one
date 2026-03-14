'use client';
import { CreditBand } from '@/lib/constants/creditBands';
import { ExpedienteCard } from './PipelineView';

interface Filters {
  brand: string;
  credit_band: CreditBand | '';
  client: string;
  only_blocked: boolean;
}

interface PipelineFiltersProps {
  expedientes: ExpedienteCard[];
  filters: Filters;
  onChange: (f: Filters) => void;
}

export function PipelineFilters({ expedientes, filters, onChange }: PipelineFiltersProps) {
  const brands = Array.from(new Set(expedientes.map(e => e.brand))).sort();
  const clients = Array.from(new Set(expedientes.map(e => e.client))).sort();

  return (
    <div className="flex flex-wrap items-center gap-3 bg-white border border-slate-200 rounded-xl px-4 py-2.5">
      {/* Brand */}
      <select
        value={filters.brand}
        onChange={e => onChange({ ...filters, brand: e.target.value })}
        className="text-sm border-none bg-transparent text-slate-600 focus:ring-0 cursor-pointer"
        aria-label="Filtrar por marca"
      >
        <option value="">Todas las marcas</option>
        {brands.map(b => <option key={b} value={b}>{b}</option>)}
      </select>

      {/* Credit band */}
      <div className="flex items-center gap-1.5">
        {(['GREEN', 'AMBER', 'RED'] as CreditBand[]).map(band => (
          <button
            key={band}
            onClick={() => onChange({ ...filters, credit_band: filters.credit_band === band ? '' : band })}
            className={`px-2.5 py-1 rounded-lg text-xs font-semibold uppercase tracking-[0.5px] border transition-colors ${
              filters.credit_band === band
                ? band === 'GREEN' ? 'bg-[#0E8A6D] text-white border-[#0E8A6D]'
                  : band === 'AMBER' ? 'bg-[#B45309] text-white border-[#B45309]'
                  : 'bg-[#DC2626] text-white border-[#DC2626]'
                : 'bg-white text-slate-500 border-slate-200 hover:border-slate-300'
            }`}
          >
            {band === 'GREEN' ? 'Al d\u00eda' : band === 'AMBER' ? 'Riesgo' : 'Cr\u00edtico'}
          </button>
        ))}
      </div>

      {/* Client search */}
      <input
        type="text"
        value={filters.client}
        onChange={e => onChange({ ...filters, client: e.target.value })}
        placeholder="Buscar cliente..."
        className="text-sm border border-slate-200 rounded-lg px-3 py-1 focus:outline-none focus:ring-1 focus:ring-[#013A57]"
      />

      {/* Only blocked */}
      <label className="flex items-center gap-1.5 cursor-pointer text-sm text-slate-600">
        <input
          type="checkbox"
          checked={filters.only_blocked}
          onChange={e => onChange({ ...filters, only_blocked: e.target.checked })}
          className="accent-[#013A57]"
        />
        Solo bloqueados
      </label>
    </div>
  );
}
