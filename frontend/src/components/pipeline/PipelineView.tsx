"use client";
import { useState, useEffect, useCallback } from "react";
import { Kanban, Table2, Calendar, AlertTriangle } from "lucide-react";
import { PIPELINE_STATES, STATE_LABELS, CanonicalState } from "@/lib/constants/states";
import { PipelineColumn } from "./PipelineColumn";
import { PipelineFilters } from "./PipelineFilters";
import { CreditBadge } from "@/components/ui/CreditBadge";
import { StateBadge } from "@/components/ui/StateBadge";
import { CreditBand } from "@/lib/constants/creditBands";
import { cn } from "@/lib/utils";
import api from "@/lib/api";
import { useRouter } from "next/navigation";

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

export type ViewMode = "pipeline" | "table";

export function PipelineView() {
  const router = useRouter();
  const [viewMode, setViewMode] = useState<ViewMode>("pipeline");
  const [expedientes, setExpedientes] = useState<ExpedienteCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<{
    brand: string;
    credit_band: CreditBand | "";
    client: string;
    only_blocked: boolean;
  }>({
    brand: "",
    credit_band: "",
    client: "",
    only_blocked: false,
  });

  // fix: usa api (axios con token) en lugar de fetch() nativo
  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const results = await Promise.all(
        PIPELINE_STATES.map((s) =>
          api.get(`ui/expedientes/?status=${s}`).then((r) => r.data)
        )
      );
      const all: ExpedienteCard[] = results.flatMap(
        (r: { results?: ExpedienteCard[] } | ExpedienteCard[]) =>
          Array.isArray(r) ? r : (r.results ?? [])
      );
      setExpedientes(all);
    } catch (err: unknown) {
      const e = err as { message?: string };
      console.error("[PipelineView] fetch error:", e);
      setError("No se pudo cargar el pipeline. Verifica tu conexión.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const filtered = expedientes.filter((e) => {
    if (filters.brand && e.brand !== filters.brand) return false;
    if (filters.credit_band && e.credit_band !== filters.credit_band) return false;
    if (filters.client && !e.client.toLowerCase().includes(filters.client.toLowerCase())) return false;
    if (filters.only_blocked && !e.is_blocked) return false;
    return true;
  });

  const byState = (state: CanonicalState) => filtered.filter((e) => e.status === state);

  return (
    <div className="flex flex-col h-full gap-4 p-6">
      {/* ── Header ── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-[var(--navy)]">Pipeline operativo</h1>
          <p className="text-sm text-[var(--text-tertiary)]">
            {loading ? "Cargando..." : `${filtered.length} expediente${filtered.length !== 1 ? "s" : ""}`}
          </p>
        </div>

        {/* View toggle */}
        <div className="flex items-center gap-1 border border-[var(--border)] rounded-xl p-1 bg-[var(--surface)]">
          <button
            onClick={() => setViewMode("pipeline")}
            aria-pressed={viewMode === "pipeline"}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors",
              viewMode === "pipeline"
                ? "bg-[var(--navy)] text-[var(--text-inverse)]"
                : "text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]"
            )}
          >
            <Kanban size={14} />
            Pipeline
          </button>
          <button
            onClick={() => setViewMode("table")}
            aria-pressed={viewMode === "table"}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors",
              viewMode === "table"
                ? "bg-[var(--navy)] text-[var(--text-inverse)]"
                : "text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]"
            )}
          >
            <Table2 size={14} />
            Tabla
          </button>
          <button
            disabled
            title="Disponible en Sprint 10"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium text-[var(--text-disabled)] cursor-not-allowed"
          >
            <Calendar size={14} />
            Calendario
          </button>
        </div>
      </div>

      {/* ── Filters ── */}
      <PipelineFilters expedientes={expedientes} filters={filters} onChange={setFilters} />

      {/* ── Error state ── */}
      {error && (
        <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 rounded-xl px-4 py-3 text-sm">
          <AlertTriangle size={16} className="flex-shrink-0" />
          {error}
          <button
            onClick={fetchAll}
            className="ml-auto text-xs font-semibold underline hover:no-underline"
          >
            Reintentar
          </button>
        </div>
      )}

      {/* ── Content ── */}
      {loading ? (
        // Skeleton de columnas
        <div className="flex gap-3 overflow-x-auto pb-4">
          {PIPELINE_STATES.map((s) => (
            <div key={s} className="flex flex-col w-64 min-w-[256px] gap-2">
              <div className="h-5 bg-[var(--border)] rounded animate-pulse w-24" />
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="h-24 bg-[var(--border)] rounded-xl animate-pulse" />
              ))}
            </div>
          ))}
        </div>
      ) : viewMode === "pipeline" ? (
        // ── Kanban board ──
        <div className="flex-1 overflow-x-auto">
          <div className="flex gap-3 h-full min-w-max pb-4">
            {PIPELINE_STATES.map((state) => (
              <PipelineColumn
                key={state}
                state={state}
                label={STATE_LABELS[state]}
                cards={byState(state)}
              />
            ))}
          </div>
        </div>
      ) : (
        // ── Table view ──
        <div className="flex-1 overflow-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="border-b border-[var(--border)] bg-[var(--bg-alt)] text-left">
                <th className="px-4 py-2.5 text-xs font-semibold text-[var(--text-tertiary)] uppercase tracking-[0.5px]">Ref</th>
                <th className="px-4 py-2.5 text-xs font-semibold text-[var(--text-tertiary)] uppercase tracking-[0.5px]">Cliente</th>
                <th className="px-4 py-2.5 text-xs font-semibold text-[var(--text-tertiary)] uppercase tracking-[0.5px]">Brand</th>
                <th className="px-4 py-2.5 text-xs font-semibold text-[var(--text-tertiary)] uppercase tracking-[0.5px]">Estado</th>
                <th className="px-4 py-2.5 text-xs font-semibold text-[var(--text-tertiary)] uppercase tracking-[0.5px]">Crédito</th>
                <th className="px-4 py-2.5 text-xs font-semibold text-[var(--text-tertiary)] uppercase tracking-[0.5px]">Avance</th>
                <th className="px-4 py-2.5 text-xs font-semibold text-[var(--text-tertiary)] uppercase tracking-[0.5px]">Acción pendiente</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-10 text-center text-[var(--text-disabled)]">
                    No hay expedientes con los filtros aplicados
                  </td>
                </tr>
              ) : (
                filtered.map((e, i) => (
                  <tr
                    key={e.id}
                    className={cn(
                      "border-b border-[var(--divider)] hover:bg-[var(--surface-hover)] transition-colors cursor-pointer",
                      i % 2 === 0 ? "bg-[var(--surface)]" : "bg-[var(--bg)]"
                    )}
                    onClick={() => router.push(`/expedientes/${e.id}`)}
                  >
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1.5">
                        {e.is_blocked && (
                          <AlertTriangle size={12} className="text-[var(--coral)]" aria-label="Bloqueado" />
                        )}
                        <span className="font-mono text-xs font-semibold text-[var(--navy)]">{e.ref}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-[var(--text-secondary)] max-w-[160px] truncate">{e.client}</td>
                    <td className="px-4 py-3">
                      <span
                        className="inline-block text-[10px] font-semibold px-2 py-0.5 rounded-full uppercase tracking-[0.5px]"
                        style={{
                          background: e.brand_color ? `${e.brand_color}20` : "var(--bg-alt)",
                          color: e.brand_color ?? "var(--text-tertiary)",
                        }}
                      >
                        {e.brand}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <StateBadge state={e.status} />
                    </td>
                    <td className="px-4 py-3">
                      <CreditBadge band={e.credit_band} />
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1.5">
                        <div className="flex gap-0.5">
                          {Array.from({ length: e.artifacts_total }).map((_, idx) => (
                            <span
                              key={idx}
                              className={cn(
                                "inline-block w-2 h-2 rounded-full",
                                idx < e.artifacts_done ? "bg-[var(--mint)]" : "bg-[var(--border)]"
                              )}
                            />
                          ))}
                        </div>
                        <span className="text-[10px] text-[var(--text-disabled)]">
                          {e.artifacts_done}/{e.artifacts_total}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-xs text-[var(--text-tertiary)] italic max-w-[200px] truncate">
                      {e.pending_action ?? "—"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
