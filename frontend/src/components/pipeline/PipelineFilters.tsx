"use client";
import { cn } from "@/lib/utils";
import { CreditBand } from "@/lib/constants/creditBands";
import { ExpedienteCard } from "./PipelineView";

interface Filters {
  brand: string;
  credit_band: CreditBand | "";
  client: string;
  only_blocked: boolean;
}

interface PipelineFiltersProps {
  expedientes: ExpedienteCard[];
  filters: Filters;
  onChange: (f: Filters) => void;
}

const BAND_CONFIG: Record<CreditBand, { label: string; active: string }> = {
  GREEN: { label: "Al día",   active: "bg-[var(--success)] text-[var(--text-inverse)] border-[var(--success)]" },
  AMBER: { label: "Riesgo",   active: "bg-[var(--amber)]  text-[var(--text-inverse)] border-[var(--amber)]" },
  RED:   { label: "Crítico",  active: "bg-[var(--coral)]  text-[var(--text-inverse)] border-[var(--coral)]" },
};

export function PipelineFilters({ expedientes, filters, onChange }: PipelineFiltersProps) {
  const brands = Array.from(new Set(expedientes.map((e) => e.brand))).sort();

  return (
    <div className="flex flex-wrap items-center gap-3 bg-[var(--surface)] border border-[var(--border)] rounded-xl px-4 py-2.5">
      {/* Brand */}
      <select
        value={filters.brand}
        onChange={(e) => onChange({ ...filters, brand: e.target.value })}
        aria-label="Filtrar por marca"
        className="text-sm border-none bg-transparent text-[var(--text-secondary)] focus:ring-0 cursor-pointer"
      >
        <option value="">Todas las marcas</option>
        {brands.map((b) => <option key={b} value={b}>{b}</option>)}
      </select>

      {/* Separador */}
      <span className="w-px h-4 bg-[var(--divider)]" aria-hidden />

      {/* Credit band pills */}
      <div className="flex items-center gap-1.5" role="group" aria-label="Filtrar por semáforo de crédito">
        {(["GREEN", "AMBER", "RED"] as CreditBand[]).map((band) => (
          <button
            key={band}
            onClick={() => onChange({ ...filters, credit_band: filters.credit_band === band ? "" : band })}
            aria-pressed={filters.credit_band === band}
            className={cn(
              "px-2.5 py-1 rounded-lg text-xs font-semibold uppercase tracking-[0.5px] border transition-colors",
              filters.credit_band === band
                ? BAND_CONFIG[band].active
                : "bg-[var(--surface)] text-[var(--text-tertiary)] border-[var(--border)] hover:border-[var(--border-strong)]"
            )}
          >
            {BAND_CONFIG[band].label}
          </button>
        ))}
      </div>

      {/* Separador */}
      <span className="w-px h-4 bg-[var(--divider)]" aria-hidden />

      {/* Client search */}
      <input
        type="text"
        value={filters.client}
        onChange={(e) => onChange({ ...filters, client: e.target.value })}
        placeholder="Buscar cliente..."
        aria-label="Buscar cliente"
        className="text-sm border border-[var(--border)] rounded-lg px-3 py-1 bg-[var(--surface)] text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--navy)] placeholder:text-[var(--text-disabled)]"
      />

      {/* Only blocked */}
      <label className="flex items-center gap-1.5 cursor-pointer text-sm text-[var(--text-secondary)]">
        <input
          type="checkbox"
          checked={filters.only_blocked}
          onChange={(e) => onChange({ ...filters, only_blocked: e.target.checked })}
          className="accent-[var(--navy)]"
        />
        Solo bloqueados
      </label>
    </div>
  );
}
