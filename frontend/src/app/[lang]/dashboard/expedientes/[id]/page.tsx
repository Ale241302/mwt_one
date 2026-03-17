"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft, Lock, AlertTriangle, FileText, DollarSign,
  Package, ChevronDown, ChevronUp, ExternalLink, Clock,
} from "lucide-react";
import api from "@/lib/api";
import { STATE_LABELS, STATE_BADGE_CLASSES } from "@/constants/states";

/* ─── Types ─── */
interface Artifact {
  id: string;
  type: string;
  label: string;
  status: string;
  url?: string;
  created_at: string;
}

interface Cost {
  id: string;
  category: string;
  description: string;
  amount: number;
  currency: string;
  created_at: string;
}

interface Payment {
  id: string;
  amount: number;
  currency: string;
  method: string;
  date: string;
  reference?: string;
}

interface HistoryEntry {
  id: string;
  action: string;
  from_status?: string;
  to_status?: string;
  note?: string;
  created_at: string;
  user?: string;
}

interface ExpedienteDetail {
  id: string;
  ref: string;
  client: string;
  client_id?: string;
  brand: string | null;
  status: string;
  credit_days: number;
  is_blocked: boolean;
  block_reason: string | null;
  amount: number;
  currency: string;
  origin: string | null;
  destination: string | null;
  incoterm: string | null;
  purchase_order: string | null;
  created_at: string;
  updated_at: string;
  artifacts: Artifact[];
  costs: Cost[];
  payments: Payment[];
  history: HistoryEntry[];
}

/* ─── Accordion section ─── */
function Section({ title, icon, count, children, defaultOpen = false }: {
  title: string;
  icon: React.ReactNode;
  count?: number;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="card mb-4">
      <button
        type="button"
        className="flex items-center justify-between w-full p-5"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        style={{ background: "none", border: "none", cursor: "pointer", textAlign: "left" }}
      >
        <div className="flex items-center gap-3">
          <span style={{ color: "var(--text-secondary)" }}>{icon}</span>
          <span className="heading-md">{title}</span>
          {count !== undefined && (
            <span className="sidebar-counter" style={{ marginLeft: 0 }}>{count}</span>
          )}
        </div>
        {open ? <ChevronUp size={18} style={{ color: "var(--text-tertiary)" }} /> : <ChevronDown size={18} style={{ color: "var(--text-tertiary)" }} />}
      </button>
      {open && (
        <div style={{ borderTop: "1px solid var(--border)", padding: "var(--space-5)" }}>
          {children}
        </div>
      )}
    </div>
  );
}

/* ─── Main Page ─── */
export default function ExpedienteDetailPage() {
  const params = useParams();
  const router = useRouter();
  const lang = (params?.lang as string) || "es";
  const id = params?.id as string;

  const [exp, setExp] = useState<ExpedienteDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const res = await api.get(`/api/ui/expedientes/${id}/`);
      setExp(res.data);
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 404 || status === 400) setNotFound(true);
      else console.error("Expediente detail error:", err);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { if (id) fetchData(); }, [fetchData, id]);

  /* ── Loading ── */
  if (loading) {
    return (
      <div>
        <button type="button" className="btn btn-sm btn-ghost mb-6" onClick={() => router.back()}>
          <ArrowLeft size={16} /> Volver
        </button>
        <div className="empty-state"><p>Cargando expediente...</p></div>
      </div>
    );
  }

  /* ── Not found ── */
  if (notFound || !exp) {
    return (
      <div>
        <button type="button" className="btn btn-sm btn-ghost mb-6" onClick={() => router.back()}>
          <ArrowLeft size={16} /> Volver
        </button>
        <div className="empty-state">
          <FileText size={48} />
          <p>Expediente no encontrado.</p>
        </div>
      </div>
    );
  }

  const totalCosts = exp.costs?.reduce((s, c) => s + (c.amount || 0), 0) || 0;
  const totalPayments = exp.payments?.reduce((s, p) => s + (p.amount || 0), 0) || 0;
  const balance = totalPayments - totalCosts;

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <button type="button" className="btn btn-sm btn-ghost mb-4" onClick={() => router.push(`/${lang}/dashboard/expedientes`)}>
          <ArrowLeft size={16} /> Expedientes
        </button>
        <div className="page-header">
          <div>
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="page-title">{exp.ref || `EXP-${exp.id.substring(0, 8)}`}</h1>
              <span className={`badge ${STATE_BADGE_CLASSES[exp.status] ?? "badge-info"}`}>
                {STATE_LABELS[exp.status] || exp.status}
              </span>
              {exp.is_blocked && (
                <span className="badge badge-critical"><Lock size={10} /> Bloqueado</span>
              )}
            </div>
            <p className="page-subtitle" style={{ marginTop: "var(--space-1)" }}>
              {exp.client}{exp.brand ? ` · ${exp.brand}` : ""}
            </p>
          </div>
        </div>

        {exp.is_blocked && exp.block_reason && (
          <div className="flex items-start gap-3 p-4 rounded-xl mb-4" style={{ background: "var(--critical-bg)", border: "1px solid var(--critical)", color: "var(--critical)" }}>
            <AlertTriangle size={18} style={{ flexShrink: 0, marginTop: 1 }} />
            <div>
              <span className="heading-sm block">Expediente bloqueado</span>
              <span className="body-sm">{exp.block_reason}</span>
            </div>
          </div>
        )}
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        {([
          { label: "Días crédito", value: exp.credit_days > 0 ? `${exp.credit_days}d` : "—", warn: exp.credit_days > 60 },
          { label: "Monto expediente", value: `$${(exp.amount || 0).toLocaleString("en-US", { minimumFractionDigits: 2 })}` },
          { label: "Total costos", value: `$${totalCosts.toLocaleString("en-US", { minimumFractionDigits: 2 })}` },
          { label: "Balance", value: `$${balance.toLocaleString("en-US", { minimumFractionDigits: 2, signDisplay: "always" })}`, warn: balance < 0 },
        ]).map(({ label, value, warn }) => (
          <div key={label} className="stat-card">
            <div className="stat-label">{label}</div>
            <div className="stat-value" style={{ fontSize: 20, color: warn ? "var(--critical)" : undefined }}>{value}</div>
          </div>
        ))}
      </div>

      {/* Info general */}
      <Section title="Información general" icon={<FileText size={18} />} defaultOpen>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-3">
          {([
            ["Referencia", exp.ref || "—"],
            ["Cliente", exp.client || "—"],
            ["Marca", exp.brand || "—"],
            ["Orden de compra", exp.purchase_order || "—"],
            ["Origen", exp.origin || "—"],
            ["Destino", exp.destination || "—"],
            ["Incoterm", exp.incoterm || "—"],
            ["Moneda", exp.currency || "—"],
            ["Creado", exp.created_at ? new Date(exp.created_at).toLocaleDateString("es") : "—"],
            ["Actualizado", exp.updated_at ? new Date(exp.updated_at).toLocaleDateString("es") : "—"],
          ] as [string, string][]).map(([label, value]) => (
            <div key={label} className="flex justify-between py-1" style={{ borderBottom: "1px solid var(--divider)" }}>
              <span className="body-sm" style={{ color: "var(--text-tertiary)" }}>{label}</span>
              <span className="body-sm" style={{ color: "var(--text-primary)", fontWeight: 500 }}>{value}</span>
            </div>
          ))}
        </div>
      </Section>

      {/* Artefactos */}
      <Section title="Artefactos" icon={<Package size={18} />} count={exp.artifacts?.length || 0}>
        {(!exp.artifacts || exp.artifacts.length === 0) ? (
          <p className="body-sm" style={{ color: "var(--text-tertiary)" }}>Sin artefactos registrados.</p>
        ) : (
          <div className="table-container">
            <table>
              <thead><tr><th>Tipo</th><th>Descripción</th><th>Estado</th><th>Fecha</th><th></th></tr></thead>
              <tbody>
                {exp.artifacts.map((a) => (
                  <tr key={a.id}>
                    <td><span className="mono-sm">{a.type}</span></td>
                    <td>{a.label || "—"}</td>
                    <td><span className="badge badge-info">{a.status}</span></td>
                    <td className="caption">{a.created_at ? new Date(a.created_at).toLocaleDateString("es") : "—"}</td>
                    <td>
                      {a.url && (
                        <a href={a.url} target="_blank" rel="noopener noreferrer" className="btn btn-sm btn-ghost" aria-label="Ver artefacto">
                          <ExternalLink size={14} />
                        </a>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>

      {/* Costos */}
      <Section title="Costos" icon={<DollarSign size={18} />} count={exp.costs?.length || 0}>
        {(!exp.costs || exp.costs.length === 0) ? (
          <p className="body-sm" style={{ color: "var(--text-tertiary)" }}>Sin costos registrados.</p>
        ) : (
          <div className="table-container">
            <table>
              <thead><tr><th>Categoría</th><th>Descripción</th><th style={{ textAlign: "right" }}>Monto</th><th>Moneda</th><th>Fecha</th></tr></thead>
              <tbody>
                {exp.costs.map((c) => (
                  <tr key={c.id}>
                    <td>{c.category || "—"}</td>
                    <td>{c.description || "—"}</td>
                    <td className="cell-money">${(c.amount || 0).toLocaleString("en-US", { minimumFractionDigits: 2 })}</td>
                    <td>{c.currency || "—"}</td>
                    <td className="caption">{c.created_at ? new Date(c.created_at).toLocaleDateString("es") : "—"}</td>
                  </tr>
                ))}
                <tr style={{ background: "var(--bg-alt)" }}>
                  <td colSpan={2} style={{ fontWeight: 600 }}>Total costos</td>
                  <td className="cell-money">${totalCosts.toLocaleString("en-US", { minimumFractionDigits: 2 })}</td>
                  <td colSpan={2}></td>
                </tr>
              </tbody>
            </table>
          </div>
        )}
      </Section>

      {/* Pagos */}
      <Section title="Pagos" icon={<DollarSign size={18} />} count={exp.payments?.length || 0}>
        {(!exp.payments || exp.payments.length === 0) ? (
          <p className="body-sm" style={{ color: "var(--text-tertiary)" }}>Sin pagos registrados.</p>
        ) : (
          <div className="table-container">
            <table>
              <thead><tr><th>Método</th><th>Referencia</th><th style={{ textAlign: "right" }}>Monto</th><th>Moneda</th><th>Fecha</th></tr></thead>
              <tbody>
                {exp.payments.map((p) => (
                  <tr key={p.id}>
                    <td>{p.method || "—"}</td>
                    <td><span className="mono-sm">{p.reference || "—"}</span></td>
                    <td className="cell-money">${(p.amount || 0).toLocaleString("en-US", { minimumFractionDigits: 2 })}</td>
                    <td>{p.currency || "—"}</td>
                    <td className="caption">{p.date ? new Date(p.date).toLocaleDateString("es") : "—"}</td>
                  </tr>
                ))}
                <tr style={{ background: "var(--bg-alt)" }}>
                  <td colSpan={2} style={{ fontWeight: 600 }}>Total pagado</td>
                  <td className="cell-money">${totalPayments.toLocaleString("en-US", { minimumFractionDigits: 2 })}</td>
                  <td colSpan={2}></td>
                </tr>
              </tbody>
            </table>
          </div>
        )}
      </Section>

      {/* Historial */}
      <Section title="Historial" icon={<Clock size={18} />} count={exp.history?.length || 0}>
        {(!exp.history || exp.history.length === 0) ? (
          <p className="body-sm" style={{ color: "var(--text-tertiary)" }}>Sin historial registrado.</p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
            {exp.history.map((h) => (
              <div key={h.id} className="flex gap-4 p-3 rounded-lg" style={{ background: "var(--bg-alt)" }}>
                <div style={{ flexShrink: 0, paddingTop: 2 }}>
                  <div style={{ width: 10, height: 10, borderRadius: "50%", background: "var(--brand-accent)", marginTop: 4 }} />
                </div>
                <div style={{ flex: 1 }}>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="heading-sm">{h.action}</span>
                    {h.from_status && h.to_status && (
                      <span className="caption" style={{ color: "var(--text-tertiary)" }}>
                        {STATE_LABELS[h.from_status] || h.from_status} → {STATE_LABELS[h.to_status] || h.to_status}
                      </span>
                    )}
                  </div>
                  {h.note && <p className="body-sm mt-1" style={{ color: "var(--text-secondary)" }}>{h.note}</p>}
                  <div className="caption mt-1" style={{ color: "var(--text-tertiary)" }}>
                    {h.user && <span>{h.user} · </span>}
                    {h.created_at ? new Date(h.created_at).toLocaleString("es") : ""}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Section>
    </div>
  );
}
