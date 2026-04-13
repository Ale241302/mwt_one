"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { Kanban, Table2, Calendar, AlertTriangle, Lock, ChevronRight, Search } from "lucide-react";
import api from "@/lib/api";
import { PIPELINE_STATES, STATE_LABELS, STATE_BADGE_CLASSES } from "@/constants/states";

type ViewMode = "pipeline" | "tabla" | "calendario";
type CreditLevel = "all" | "green" | "amber" | "red";

interface Expediente {
  id: string;
  ref: string;
  client: string;
  brand: string | null;
  status: string;
  credit_days: number;
  is_blocked: boolean;
  block_reason: string | null;
  artifacts_done: number;
  artifacts_total: number;
  amount: number;
  updated_at: string;
}

function getCreditLevel(days: number, isBlocked: boolean): "green" | "amber" | "red" {
  if (isBlocked || days > 75) return "red";
  if (days >= 60) return "amber";
  return "green";
}

const CREDIT_DOT: Record<string, string> = {
  green: "credit-green",
  amber: "credit-amber",
  red:   "credit-red",
};

export default function PipelinePage() {
  const params = useParams();
  const router = useRouter();
  const lang = (params?.lang as string) || "es";

  const [expedientes, setExpedientes] = useState<Expediente[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<ViewMode>("pipeline");
  const [brandFilter, setBrandFilter] = useState("all");
  const [creditFilter, setCreditFilter] = useState<CreditLevel>("all");
  const [clientSearch, setClientSearch] = useState("");
  const [onlyBlocked, setOnlyBlocked] = useState(false);
  const [brands, setBrands] = useState<string[]>([]);

  const fetchData = useCallback(async () => {
    try {
      const res = await api.get("/ui/expedientes/");
      const data = res.data?.results || res.data || [];
      setExpedientes(data);
      setBrands(Array.from(new Set(data.map((e: Expediente) => e.brand).filter(Boolean))) as string[]);
    } catch (err) {
      console.error("Pipeline fetch error:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const filtered = expedientes.filter((exp) => {
    if (brandFilter !== "all" && exp.brand !== brandFilter) return false;
    if (onlyBlocked && !exp.is_blocked) return false;
    if (clientSearch && !exp.client?.toLowerCase().includes(clientSearch.toLowerCase())) return false;
    if (creditFilter !== "all" && getCreditLevel(exp.credit_days, exp.is_blocked) !== creditFilter) return false;
    return true;
  });

  const byStatus = Object.fromEntries(
    PIPELINE_STATES.map((s) => [s, filtered.filter((e) => e.status === s)])
  );
  const totalFiltered = filtered.filter((e) => (PIPELINE_STATES as readonly string[]).includes(e.status)).length;

  // FIX: ruta correcta sin /dashboard/
  const goToDetail = (id: string) => router.push(`/${lang}/expedientes/${id}`);

  if (loading) {
    return (
      <div>
        <div className="page-header">
          <div><h1 className="page-title">Pipeline operativo</h1><p className="page-subtitle">Cargando...</p></div>
        </div>
        <div className="empty-state"><p>Cargando pipeline...</p></div>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Pipeline operativo</h1>
          <p className="page-subtitle">{totalFiltered} expedientes activos</p>
        </div>
        <div className="flex items-center gap-1 p-1 rounded-lg" style={{ background: "var(--bg-alt)" }}>
          {([
            { mode: "pipeline" as ViewMode, icon: <Kanban size={16} />, label: "Pipeline" },
            { mode: "tabla"    as ViewMode, icon: <Table2  size={16} />, label: "Tabla" },
            { mode: "calendario" as ViewMode, icon: <Calendar size={16} />, label: "Calendario", disabled: true },
          ]).map(({ mode, icon, label, disabled }) => (
            <button
              key={mode}
              onClick={() => !disabled && setViewMode(mode)}
              disabled={disabled}
              className="btn btn-sm"
              style={{
                background: viewMode === mode ? "var(--surface)" : "transparent",
                color: disabled ? "var(--text-disabled)" : viewMode === mode ? "var(--text-primary)" : "var(--text-secondary)",
                boxShadow: viewMode === mode ? "var(--shadow-sm)" : "none",
                borderRadius: "var(--radius-md)",
              }}
            >
              {icon} <span className="hidden sm:inline">{label}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3 mb-6 p-3 rounded-xl" style={{ background: "var(--surface)", border: "1px solid var(--border)" }}>
        <div>
          <label htmlFor="pipeline-brand" className="sr-only">Marca</label>
          <select id="pipeline-brand" value={brandFilter} onChange={(e) => setBrandFilter(e.target.value)} className="input" style={{ width: "auto", minWidth: 160 }}>
            <option value="all">Todas las marcas</option>
            {brands.map((b) => <option key={b} value={b}>{b}</option>)}
          </select>
        </div>
        {(["all", "green", "amber", "red"] as CreditLevel[]).map((level) => (
          <button key={level} onClick={() => setCreditFilter(creditFilter === level ? "all" : level)} className="btn btn-sm"
            style={{ background: creditFilter === level ? "var(--surface-active)" : "transparent", color: "var(--text-primary)", border: `1px solid ${creditFilter === level ? "var(--border-strong)" : "var(--border)"}` }}>
            {level === "all" ? "Todos" : level === "green" ? "Al día" : level === "amber" ? "Riesgo" : "Crítico"}
          </button>
        ))}
        <div className="relative flex-1 min-w-[180px]">
          <label htmlFor="pipeline-search" className="sr-only">Buscar cliente</label>
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: "var(--text-tertiary)" }} />
          <input id="pipeline-search" type="text" placeholder="Buscar cliente..." value={clientSearch} onChange={(e) => setClientSearch(e.target.value)} className="input" style={{ paddingLeft: 36 }} />
        </div>
        <label htmlFor="pipeline-blocked" className="flex items-center gap-2 cursor-pointer text-sm" style={{ color: "var(--text-secondary)" }}>
          <input id="pipeline-blocked" type="checkbox" checked={onlyBlocked} onChange={(e) => setOnlyBlocked(e.target.checked)} className="rounded" />
          Solo bloqueados
        </label>
      </div>

      {viewMode === "pipeline" && (
        <div className="pipeline-grid">
          {PIPELINE_STATES.map((status) => {
            const items = byStatus[status] || [];
            return (
              <div key={status} className="pipeline-column">
                <div className="pipeline-column-header">
                  <span className="pipeline-column-title">{STATE_LABELS[status] || status}</span>
                  <span className="flex items-center justify-center rounded-full" style={{ background: "var(--brand-accent)", color: "var(--brand-primary)", width: 22, height: 22, fontSize: 11, fontWeight: 700 }}>{items.length}</span>
                </div>
                <div className="flex-1 overflow-y-auto">
                  {items.length === 0 ? (
                    <div className="text-center py-8 text-xs" style={{ color: "var(--text-disabled)" }}>Sin expedientes</div>
                  ) : items.map((exp) => {
                    const credit = getCreditLevel(exp.credit_days, exp.is_blocked);
                    const refLabel = exp.ref || `EXP-${exp.id.substring(0, 8)}`;
                    return (
                      <button key={exp.id} type="button"
                        className={`pipeline-card ${exp.is_blocked ? "pipeline-card-blocked" : ""}`}
                        onClick={() => goToDetail(exp.id)}
                        aria-label={`Abrir expediente ${refLabel}`}
                        style={{ width: "100%", textAlign: "left" }}
                      >
                        <div className="flex items-center justify-between gap-2">
                          <span className="pipeline-card-ref">{refLabel}</span>
                          {exp.is_blocked && <span className="badge badge-critical"><Lock size={10} /> Bloqueado</span>}
                        </div>
                        <div className="pipeline-card-client">{exp.client || "—"}</div>
                        <div className="pipeline-card-meta">
                          <div className="flex items-center gap-1">
                            <span className={`credit-dot ${CREDIT_DOT[credit]}`} />
                            {exp.credit_days > 0 && <span className="caption">{exp.credit_days}d</span>}
                          </div>
                          {credit === "red" && !exp.is_blocked && (
                            <span className="badge badge-warning" style={{ fontSize: 10, padding: "1px 4px" }}><AlertTriangle size={10} /> Riesgo</span>
                          )}
                          <div className="flex items-center gap-1 ml-auto" title={`${exp.artifacts_done}/${exp.artifacts_total} artefactos`}>
                            {Array.from({ length: exp.artifacts_total || 0 }).map((_, i) => (
                              <span key={i} className="block rounded-full" style={{ width: 6, height: 6, background: i < (exp.artifacts_done || 0) ? "var(--success)" : "var(--border)" }} />
                            ))}
                            {(exp.artifacts_total || 0) > 0 && <span className="caption ml-1">{exp.artifacts_done || 0}/{exp.artifacts_total}</span>}
                          </div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {viewMode === "tabla" && (
        <div className="table-container">
          <table>
            <thead><tr><th>Ref</th><th>Estado</th><th>Cliente</th><th>Marca</th><th style={{ textAlign: "right" }}>Días crédito</th><th style={{ textAlign: "right" }}>Monto</th><th>Actividad</th><th></th></tr></thead>
            <tbody>
              {filtered.map((exp) => {
                const credit = getCreditLevel(exp.credit_days, exp.is_blocked);
                return (
                  <tr key={exp.id} 
                      className={exp.is_blocked ? "row-critical" : ""}
                      onClick={() => goToDetail(exp.id)}
                      style={{ cursor: "pointer" }}>
                    <td className="cell-ref">{exp.ref || `EXP-${exp.id.substring(0, 8)}`}</td>
                    <td><span className={`badge ${STATE_BADGE_CLASSES[exp.status] ?? "badge-info"}`}>{STATE_LABELS[exp.status] || exp.status}</span></td>
                    <td>{exp.client || "—"}</td>
                    <td>{exp.brand || "—"}</td>
                    <td className="cell-number"><div className="flex items-center justify-end gap-2"><span className={`credit-dot ${CREDIT_DOT[credit]}`} />{exp.credit_days}d</div></td>
                    <td className="cell-money">${exp.amount?.toLocaleString("en-US", { minimumFractionDigits: 2 })}</td>
                    <td className="caption">{exp.updated_at ? new Date(exp.updated_at).toLocaleDateString("es") : "—"}</td>
                    <td><button type="button" className="btn btn-sm btn-ghost" onClick={() => goToDetail(exp.id)} aria-label={`Ver expediente ${exp.ref || exp.id}`}><ChevronRight size={16} /></button></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {viewMode === "calendario" && (
        <div className="empty-state"><Calendar size={48} /><p>Vista calendario disponible en Sprint 10</p></div>
      )}
    </div>
  );
}
