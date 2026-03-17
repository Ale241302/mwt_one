"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { FolderOpen, Search, ChevronRight, Lock, AlertTriangle } from "lucide-react";
import api from "@/lib/api";
import { STATE_LABELS, STATE_BADGE_CLASSES } from "@/constants/states";

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
  red: "credit-red",
};

export default function ExpedientesPage() {
  const params = useParams();
  const router = useRouter();
  const lang = (params?.lang as string) || "es";

  const [expedientes, setExpedientes] = useState<Expediente[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const fetchData = useCallback(async () => {
    try {
      const res = await api.get("/api/ui/expedientes/");
      setExpedientes(res.data?.results || res.data || []);
    } catch (err) {
      console.error("Expedientes fetch error:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const statuses = Array.from(new Set(expedientes.map((e) => e.status)));

  const filtered = expedientes.filter((exp) => {
    if (statusFilter !== "all" && exp.status !== statusFilter) return false;
    if (search && ![
      exp.ref, exp.client, exp.brand,
    ].some((v) => v?.toLowerCase().includes(search.toLowerCase()))) return false;
    return true;
  });

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Expedientes</h1>
          <p className="page-subtitle">{loading ? "Cargando..." : `${filtered.length} expediente${filtered.length !== 1 ? "s" : ""}`}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3 mb-6">
        <div className="relative flex-1 min-w-[200px]" style={{ maxWidth: 360 }}>
          <label htmlFor="exp-search" className="sr-only">Buscar expedientes</label>
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: "var(--text-tertiary)" }} />
          <input
            id="exp-search"
            type="text"
            placeholder="Ref, cliente, marca..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input"
            style={{ paddingLeft: 36 }}
          />
        </div>
        <div>
          <label htmlFor="exp-status" className="sr-only">Estado</label>
          <select
            id="exp-status"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="input"
            style={{ width: "auto", minWidth: 160 }}
          >
            <option value="all">Todos los estados</option>
            {statuses.map((s) => (
              <option key={s} value={s}>{STATE_LABELS[s] || s}</option>
            ))}
          </select>
        </div>
      </div>

      {loading ? (
        <div className="empty-state"><p>Cargando expedientes...</p></div>
      ) : filtered.length === 0 ? (
        <div className="empty-state">
          <FolderOpen size={48} />
          <p>Sin expedientes registrados.</p>
        </div>
      ) : (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Ref</th>
                <th>Estado</th>
                <th>Cliente</th>
                <th>Marca</th>
                <th style={{ textAlign: "right" }}>Días crédito</th>
                <th style={{ textAlign: "right" }}>Monto</th>
                <th>Actualizado</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((exp) => {
                const credit = getCreditLevel(exp.credit_days, exp.is_blocked);
                return (
                  <tr key={exp.id} className={exp.is_blocked ? "row-critical" : ""}>
                    <td>
                      <div className="flex items-center gap-2">
                        <span className="cell-ref">{exp.ref || `EXP-${exp.id.substring(0, 8)}`}</span>
                        {exp.is_blocked && <Lock size={12} style={{ color: "var(--critical)" }} />}
                      </div>
                    </td>
                    <td>
                      <span className={`badge ${STATE_BADGE_CLASSES[exp.status] ?? "badge-info"}`}>
                        {STATE_LABELS[exp.status] || exp.status}
                      </span>
                    </td>
                    <td>{exp.client || "—"}</td>
                    <td>{exp.brand || "—"}</td>
                    <td className="cell-number">
                      <div className="flex items-center justify-end gap-2">
                        <span className={`credit-dot ${CREDIT_DOT[credit]}`} />
                        {exp.credit_days > 0 ? `${exp.credit_days}d` : "—"}
                        {credit === "red" && !exp.is_blocked && <AlertTriangle size={12} style={{ color: "var(--warning)" }} />}
                      </div>
                    </td>
                    <td className="cell-money">
                      ${(exp.amount || 0).toLocaleString("en-US", { minimumFractionDigits: 2 })}
                    </td>
                    <td className="caption">
                      {exp.updated_at ? new Date(exp.updated_at).toLocaleDateString("es") : "—"}
                    </td>
                    <td>
                      <button
                        type="button"
                        className="btn btn-sm btn-ghost"
                        onClick={() => router.push(`/${lang}/dashboard/expedientes/${exp.id}`)}
                        aria-label={`Ver expediente ${exp.ref || exp.id}`}
                      >
                        <ChevronRight size={16} />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
