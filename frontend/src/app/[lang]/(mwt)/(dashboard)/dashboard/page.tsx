"use client";
/**
 * S10-05b — Dashboard mejorado
 * Cards KPI + breakdown por estado + next actions.
 */
import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  TrendingUp, Package, DollarSign, Clock,
  AlertTriangle, CheckCircle, ArrowRight, RefreshCw
} from "lucide-react";
import { cn } from "@/lib/utils";
import api from "@/lib/api";

// ─── Types ─────────────────────────────────────────────────────────────────────

interface DashboardCards {
  active_count: number;
  total_cost: number;
  total_invoiced: number;
  total_paid: number;
  total_receivables: number;
  margin: number;
  currency: string;
}

interface BrandBreakdown {
  brand: string;
  count: number;
  total_cost: number;
  total_invoiced: number;
}

interface StatusBreakdown {
  status: string;
  count: number;
}

interface NextAction {
  id: string;
  ref_number: string;
  client: string;
  action: string;
  urgency: "high" | "medium" | "normal";
}

interface DashboardData {
  cards: DashboardCards;
  brand_breakdown: BrandBreakdown[];
  status_breakdown?: StatusBreakdown[];
  next_actions?: NextAction[];
}

// ─── Helpers ─────────────────────────────────────────────────────────────────────

function fmt(n: number, currency = "USD") {
  return new Intl.NumberFormat("es-CO", { style: "currency", currency, maximumFractionDigits: 0 }).format(n);
}

const CREDIT_COLORS = {
  MINT:  "border-green-200 bg-green-50 text-green-700",
  AMBER: "border-amber-200 bg-amber-50 text-amber-700",
  RED:   "border-red-200 bg-red-50 text-red-700",
};

// ─── KPI Card ─────────────────────────────────────────────────────────────────────

function KpiCard({
  label, value, icon, sub, color
}: { label: string; value: string; icon: React.ReactNode; sub?: string; color?: string }) {
  return (
    <div className="card p-5 flex items-start gap-4">
      <div
        className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
        style={{ background: color ? `${color}20` : "var(--brand-accent-soft)" }}
      >
        <span style={{ color: color ?? "var(--brand-primary)" }}>{icon}</span>
      </div>
      <div className="min-w-0">
        <p className="caption text-text-tertiary">{label}</p>
        <p className="text-xl font-bold text-navy truncate">{value}</p>
        {sub && <p className="caption text-text-tertiary mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function DashboardPage() {
  const params = useParams();
  const lang = (params?.lang as string) || "es";

  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboard = useCallback(async (quiet = false) => {
    if (!quiet) setLoading(true);
    else setRefreshing(true);
    setError(null);
    try {
      const [finRes, dashRes] = await Promise.allSettled([
        api.get("/ui/dashboard/financial/"),
        api.get("/ui/dashboard/"),
      ]);

      const fin = finRes.status === "fulfilled" ? finRes.value.data : null;
      const dash = dashRes.status === "fulfilled" ? dashRes.value.data : null;

      if (!fin || !dash) throw new Error("No se pudo cargar el dashboard completo.");

      setData({
        cards: fin.cards,
        brand_breakdown: fin.brand_breakdown ?? [],
        status_breakdown: dash.by_status,
        next_actions: dash.next_actions,
      });
    } catch (e: unknown) {
      setError((e as { message?: string })?.message ?? "Error al cargar dashboard.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { fetchDashboard(); }, [fetchDashboard]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="text-text-secondary text-sm">Cargando dashboard…</div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="empty-state">
        <AlertTriangle size={40} />
        <p>{error ?? "Sin datos."}</p>
        <button className="btn btn-sm btn-secondary mt-2" onClick={() => fetchDashboard()}>Reintentar</button>
      </div>
    );
  }

  const { cards, brand_breakdown, status_breakdown, next_actions } = data;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">Resumen operativo y financiero de expedientes activos.</p>
        </div>
        <button
          className="btn btn-sm btn-ghost"
          onClick={() => fetchDashboard(true)}
          disabled={refreshing}
          aria-label="Actualizar dashboard"
        >
          <RefreshCw size={15} className={cn(refreshing && "animate-spin")} />
          {refreshing ? "Actualizando..." : "Actualizar"}
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
        <KpiCard label="Expedientes activos" value={String(cards.active_count)} icon={<Package size={20}/>} />
        <KpiCard label="Costo total" value={fmt(cards.total_cost, cards.currency)} icon={<DollarSign size={20}/>} color="#B45309" />
        <KpiCard label="Facturado" value={fmt(cards.total_invoiced, cards.currency)} icon={<TrendingUp size={20}/>} color="#0E8A6D" />
        <KpiCard label="Cobrado" value={fmt(cards.total_paid, cards.currency)} icon={<CheckCircle size={20}/>} color="#0E8A6D" />
        <KpiCard label="Por cobrar" value={fmt(cards.total_receivables, cards.currency)} icon={<Clock size={20}/>} color="#1D4ED8" />
        <KpiCard
          label="Margen"
          value={fmt(cards.margin, cards.currency)}
          icon={<TrendingUp size={20}/>}
          color={cards.margin >= 0 ? "#0E8A6D" : "#DC2626"}
          sub={cards.total_invoiced ? `${((cards.margin / cards.total_invoiced) * 100).toFixed(1)}%` : undefined}
        />
      </div>

      {/* Mini Pipeline */}
      {status_breakdown && status_breakdown.length > 0 && (
        <div className="card p-5">
          <h2 className="heading-sm font-semibold mb-4 text-navy">Pipeline Operativo</h2>
          <div className="flex gap-[2px] h-3 rounded-full overflow-hidden shadow-sm bg-border/40">
            {["RECIBIDO", "PREPARACION", "REVISION", "OPERACION", "LIQUIDACION", "CERRADO"].map(st => {
              const count = status_breakdown.find(s => s.status === st)?.count || 0;
              const total = status_breakdown.reduce((acc, curr) => acc + curr.count, 0) || 1;
              const flexBasis = `${(count / total) * 100}%`;
              return count > 0 ? (
                <div key={st} style={{ width: flexBasis }} className="bg-brand-primary transition-all duration-300" title={`${st}: ${count}`} />
              ) : null;
            })}
          </div>
          <div className="flex justify-between mt-3 text-xs text-text-tertiary">
            {["RECIBIDO", "PREPARACION", "REVISION", "OPERACION", "LIQUIDACION", "CERRADO"].map(st => (
              <div key={st} className="flex flex-col items-center flex-1">
                <span className="font-semibold text-navy">{status_breakdown.find(s => s.status === st)?.count || 0}</span>
                <span className="text-[10px] uppercase truncate w-full text-center mt-0.5" style={{letterSpacing: "0.5px"}}>{st}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Brand breakdown */}
        <div>
          <h2 className="heading-sm font-semibold mb-3 text-navy">Breakdown por marca</h2>
          <div className="card overflow-hidden">
            {brand_breakdown.length === 0 ? (
              <div className="p-8 text-center text-text-tertiary text-sm">Sin datos de marcas.</div>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    {["Marca", "Exp.", "Costo", "Facturado"].map((h) => (
                      <th key={h} className="text-left px-4 py-2.5 text-xs font-semibold uppercase tracking-[0.5px] text-text-secondary">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {brand_breakdown.map((b) => (
                    <tr key={b.brand} className="hover:bg-bg">
                      <td className="px-4 py-2.5 font-medium text-navy">{b.brand}</td>
                      <td className="px-4 py-2.5 text-text-secondary">{b.count}</td>
                      <td className="px-4 py-2.5 text-text-secondary">{fmt(b.total_cost)}</td>
                      <td className="px-4 py-2.5 text-text-secondary">{fmt(b.total_invoiced)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* Status breakdown */}
        {status_breakdown && status_breakdown.length > 0 && (
          <div>
            <h2 className="heading-sm font-semibold mb-3 text-navy">Breakdown por estado</h2>
            <div className="card p-4 space-y-3">
              {status_breakdown.map((s) => (
                <div key={s.status} className="flex items-center justify-between">
                  <span className="text-sm text-navy">{s.status}</span>
                  <span className="font-semibold text-text-secondary">{s.count}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Next actions */}
      {next_actions && next_actions.length > 0 && (
        <div>
          <h2 className="heading-sm font-semibold mb-3 text-navy">Acciones pendientes</h2>
          <div className="grid gap-3">
            {next_actions.map((item) => (
              <div key={item.id} className={cn("card p-4 border flex items-center justify-between gap-4", 
                item.urgency === "high" ? "border-red-200 bg-red-50 text-red-700" :
                item.urgency === "medium" ? "border-amber-200 bg-amber-50 text-amber-700" :
                "border-green-200 bg-green-50 text-green-700"
              )}>
                <div>
                  <p className="font-semibold text-sm">{item.client} — #{item.ref_number}</p>
                  <p className="caption mt-0.5">
                    {item.action}
                  </p>
                </div>
                <Link
                  href={`/${lang}/expedientes/${item.id}`}
                  className="btn btn-sm btn-ghost shrink-0"
                >
                  Ver <ArrowRight size={13}/>
                </Link>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
