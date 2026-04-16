"use client";

import { useState, useEffect, useCallback, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import api from "@/lib/api";
import {
    Search, ShieldAlert, X, Plus, ChevronDown, ChevronRight,
    MoreHorizontal, Package, Truck, MapPin, BarChart3,
    TrendingUp, AlertTriangle, Clock, CheckCircle2, Folder
} from "lucide-react";
import { CANONICAL_STATES } from "@/constants/states";
import { formatDistanceToNow } from "date-fns";
import { es } from "date-fns/locale";
import { cn } from "@/lib/utils";

// ─── Types ─────────────────────────────────────────────────────────────────

interface Expediente {
    id: string;
    expediente_id: string;
    custom_ref: string;
    status: string;
    brand: string;
    brand_name: string;
    client_name: string;
    credit_days_elapsed: number;
    credit_band: string;
    total_cost: number;
    total_value: number;
    is_blocked: boolean;
    last_event_at: string | null;
    purchase_order_number: string | null;
    payment_status: string;
    proforma_client_number: string | null;
    shipment_date: string | null;
    product_count: number;
    credit_limit_client: number | null;
    credit_exposure: number | null;
}

interface StatsData {
    kpi: {
        count_produccion: number;
        count_preparacion: number;
        count_despacho_transito: number;
        count_en_destino: number;
        total_active: number;
    };
    credit: {
        total_credit_limit: number;
        total_credit_used: number;
    };
    recent_payments: Array<{
        order_ref: string;
        sap_id: string;
        paid_amount: number;
        payment_date: string | null;
        method: string;
    }>;
    is_admin: boolean;
}

// ─── Status helpers ─────────────────────────────────────────────────────────

function getOrderStatus(exp: Expediente): { label: string; color: string; bg: string; dot: string } {
    if (exp.is_blocked) return { label: "Delayed", color: "text-red-700 dark:text-red-300", bg: "bg-red-100 dark:bg-red-900/30", dot: "bg-red-500" };
    if (exp.credit_band === "RED" || exp.credit_band === "CORAL") return { label: "Delayed", color: "text-red-700 dark:text-red-300", bg: "bg-red-100 dark:bg-red-900/30", dot: "bg-red-500" };
    if (exp.credit_band === "AMBER" || exp.status === "PREPARACION") return { label: "Warning", color: "text-amber-700 dark:text-amber-300", bg: "bg-amber-100 dark:bg-amber-900/30", dot: "bg-amber-500" };
    return { label: "On time", color: "text-emerald-700 dark:text-emerald-300", bg: "bg-emerald-100 dark:bg-emerald-900/30", dot: "bg-emerald-500" };
}

const USD = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
const USDFull = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });

// ─── Sub-components ────────────────────────────────────────────────────────

function KPICard({ icon: Icon, label, count, accent }: {
    icon: React.ElementType; label: string; count: number; accent: string;
}) {
    return (
        <div className={cn(
            "bg-surface border border-border rounded-xl p-4 flex items-center gap-4 shadow-sm",
            "hover:shadow-md hover:-translate-y-0.5 transition-all duration-200"
        )}>
            <div className={cn("w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0", accent)}>
                <Icon size={22} className="text-white" />
            </div>
            <div>
                <p className="text-xs text-text-tertiary font-medium uppercase tracking-wide leading-none mb-1">{label}</p>
                <p className="text-3xl font-bold text-text-primary leading-none">{count}</p>
                <p className="text-xs text-text-tertiary mt-1">Operations</p>
            </div>
        </div>
    );
}

function CreditHealthBar({ limit, used }: { limit: number; used: number }) {
    const pct = limit > 0 ? Math.min(100, Math.round((used / limit) * 100)) : 0;
    const barColor = pct > 80 ? "bg-red-500" : pct > 60 ? "bg-amber-500" : "bg-[#1a6b5a]";
    return (
        <div className="bg-surface border border-border rounded-xl p-5 shadow-sm h-full">
            <h3 className="text-sm font-semibold text-text-primary mb-4">Credit Health</h3>
            <div className="w-full h-3 bg-bg-alt rounded-full overflow-hidden mb-2">
                <div
                    className={cn("h-full rounded-full transition-all duration-700", barColor)}
                    style={{ width: `${pct}%` }}
                />
            </div>
            <p className="text-xs text-text-secondary">
                Crédito Disponible:{" "}
                <span className="font-semibold text-text-primary">{USD.format(limit)}</span>
                {" "}/ Crédito Utilizado:{" "}
                <span className="font-semibold text-text-primary">{USD.format(used)} ({pct}%)</span>
            </p>
        </div>
    );
}

function PaymentsTable({ payments }: { payments: StatsData["recent_payments"] }) {
    return (
        <div className="bg-surface border border-border rounded-xl p-5 shadow-sm">
            <h3 className="text-sm font-semibold text-text-primary mb-4">Pagos Realizados</h3>
            {payments.length === 0 ? (
                <p className="text-xs text-text-tertiary text-center py-4">Sin pagos registrados</p>
            ) : (
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead>
                            <tr className="text-[10px] uppercase text-text-tertiary tracking-wide border-b border-border">
                                <th className="pb-2 pr-3">Order Ref</th>
                                <th className="pb-2 pr-3">SAP ID</th>
                                <th className="pb-2 pr-3 text-right">Paid Amount</th>
                                <th className="pb-2">Payment Date</th>
                            </tr>
                        </thead>
                        <tbody>
                            {payments.map((p, i) => (
                                <tr key={i} className="border-b border-border/50 last:border-0">
                                    <td className="py-2 pr-3 text-xs font-mono text-text-primary">{p.order_ref}</td>
                                    <td className="py-2 pr-3 text-xs text-text-secondary">{p.sap_id}</td>
                                    <td className="py-2 pr-3 text-xs font-semibold text-right text-text-primary">{USDFull.format(p.paid_amount)}</td>
                                    <td className="py-2 text-xs text-text-tertiary">{p.payment_date || "—"}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}

function SKUTable({ expedientes }: { expedientes: Expediente[] }) {
    // Muestra los expedientes con sus datos de línea de producto en modo "inventario"
    const rows = expedientes.slice(0, 8).map(exp => ({
        sku: exp.proforma_client_number ? `SAP-${exp.proforma_client_number.slice(-2)}` : `SKU-${String(expedientes.indexOf(exp) + 1).padStart(4, "0")}`,
        product: exp.brand_name ? `${exp.brand_name} Products` : "Mixed Products",
        quantity: exp.product_count || 0,
        value: USDFull.format(exp.total_value || 0),
        oc: exp.custom_ref,
        sap: exp.proforma_client_number || "—",
    }));

    return (
        <div className="bg-surface border border-border rounded-xl p-5 shadow-sm">
            <h3 className="text-sm font-semibold text-text-primary mb-4">Purchased Products &amp; SKU Inventory</h3>
            <div className="overflow-x-auto">
                <table className="w-full text-left">
                    <thead>
                        <tr className="text-[10px] uppercase text-text-tertiary tracking-wide border-b border-border">
                            <th className="pb-2 pr-4">SKU</th>
                            <th className="pb-2 pr-4">Product Name</th>
                            <th className="pb-2 pr-4 text-right">Quantity</th>
                            <th className="pb-2 pr-4 text-right">Value</th>
                            <th className="pb-2 pr-4">OC</th>
                            <th className="pb-2">SAP</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows.length === 0 ? (
                            <tr>
                                <td colSpan={6} className="py-6 text-center text-xs text-text-tertiary">Sin datos de producto</td>
                            </tr>
                        ) : rows.map((r, i) => (
                            <tr key={i} className="border-b border-border/50 last:border-0 hover:bg-bg-alt/40 transition-colors">
                                <td className="py-2.5 pr-4 text-xs font-mono font-semibold text-text-primary">{r.sku}</td>
                                <td className="py-2.5 pr-4 text-xs text-text-secondary">{r.product}</td>
                                <td className="py-2.5 pr-4 text-xs text-right tabular-nums">{r.quantity}</td>
                                <td className="py-2.5 pr-4 text-xs text-right tabular-nums font-semibold">{r.value}</td>
                                <td className="py-2.5 pr-4 text-xs font-mono text-text-secondary">{r.oc}</td>
                                <td className="py-2.5 text-xs text-text-secondary">{r.sap}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

function OrderRow({
    exp,
    onOpenOC,
    onOpenExpediente,
}: {
    exp: Expediente;
    onOpenOC: (id: string) => void;
    onOpenExpediente: (id: string) => void;
}) {
    const [expanded, setExpanded] = useState(false);
    const s = getOrderStatus(exp);
    const expId = exp.expediente_id || exp.id;

    // Build a fake SAP entry from the expediente data so there's always
    // something to show when expanded. Real SAP data would come from the API.
    const sapEntries: Array<{ sap_id: string; status: string; shipping_method: string }> = [];
    if (exp.proforma_client_number) {
        sapEntries.push({
            sap_id: exp.proforma_client_number,
            status: exp.status,
            shipping_method: "—",
        });
    }

    return (
        <>
            {/* ── Main OC row ── */}
            <tr
                className="border-b border-border/60 hover:bg-bg-alt/30 transition-colors"
            >
                {/* Expand toggle */}
                <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => setExpanded(v => !v)}
                            className="text-text-tertiary hover:text-text-primary transition-colors"
                        >
                            {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                        </button>
                        <span className="text-xs font-mono font-semibold text-text-primary">{exp.custom_ref}</span>
                    </div>
                </td>
                <td className="px-4 py-3 text-xs text-text-secondary">
                    {exp.client_name}{exp.brand_name && exp.brand_name !== "Sin Marca" ? ` / ${exp.brand_name}` : ""}
                </td>
                <td className="px-4 py-3">
                    <span className={cn(
                        "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold",
                        s.bg, s.color
                    )}>
                        <span className={cn("w-1.5 h-1.5 rounded-full", s.dot)} />
                        {s.label}
                    </span>
                </td>
                <td className="px-4 py-3 text-xs font-semibold text-right tabular-nums text-text-primary">
                    {USDFull.format(exp.total_value || exp.total_cost || 0)}
                </td>
                <td className="px-4 py-3">
                    {/* ··· goes to OC detail view */}
                    <button
                        onClick={() => onOpenOC(expId)}
                        className="p-1.5 rounded hover:bg-border/40 transition-colors text-text-tertiary hover:text-text-primary"
                        title="Ver detalle de OC"
                    >
                        <MoreHorizontal size={16} />
                    </button>
                </td>
            </tr>

            {/* ── Expanded: SAP sub-rows ── */}
            {expanded && (
                <tr className="bg-bg-alt/20 border-b border-border/40">
                    <td colSpan={5} className="px-0 py-0">
                        {sapEntries.length === 0 ? (
                            // No SAP data yet — show expediente info + link
                            <div className="pl-12 pr-5 py-4 space-y-3">
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                                    <div>
                                        <p className="text-text-tertiary uppercase tracking-wide text-[10px] mb-0.5">Estado</p>
                                        <p className="font-semibold text-text-primary">{exp.status.replace(/_/g, " ")}</p>
                                    </div>
                                    <div>
                                        <p className="text-text-tertiary uppercase tracking-wide text-[10px] mb-0.5">Pago</p>
                                        <p className="font-semibold text-text-primary capitalize">{exp.payment_status || "—"}</p>
                                    </div>
                                    <div>
                                        <p className="text-text-tertiary uppercase tracking-wide text-[10px] mb-0.5">Días Crédito</p>
                                        <p className={cn("font-semibold",
                                            exp.credit_band === "RED" ? "text-red-500"
                                            : exp.credit_band === "AMBER" ? "text-amber-500"
                                            : "text-emerald-600"
                                        )}>{exp.credit_days_elapsed || 0}d</p>
                                    </div>
                                    <div>
                                        <p className="text-text-tertiary uppercase tracking-wide text-[10px] mb-0.5">Última Actividad</p>
                                        <p className="font-medium text-text-secondary">
                                            {exp.last_event_at
                                                ? formatDistanceToNow(new Date(exp.last_event_at), { addSuffix: true, locale: es })
                                                : "Sin actividad"}
                                        </p>
                                    </div>
                                </div>
                                <div className="flex gap-4">
                                    <button
                                        onClick={() => onOpenExpediente(expId)}
                                        className="text-xs text-[#1a6b5a] hover:underline font-medium flex items-center gap-1"
                                    >
                                        Ver expediente SAP →
                                    </button>
                                    <button
                                        onClick={() => onOpenOC(expId)}
                                        className="text-xs text-text-tertiary hover:text-text-primary hover:underline font-medium"
                                    >
                                        Ver detalle OC →
                                    </button>
                                </div>
                            </div>
                        ) : (
                            // SAP entries table
                            <div className="pl-10 pr-4 py-3">
                                <p className="text-[10px] uppercase tracking-wide text-text-tertiary font-semibold mb-2">SAPs Asociados</p>
                                <table className="w-full text-left">
                                    <thead>
                                        <tr className="text-[10px] uppercase text-text-tertiary tracking-wide border-b border-border">
                                            <th className="pb-1.5 pr-4">SAP ID</th>
                                            <th className="pb-1.5 pr-4">Estado</th>
                                            <th className="pb-1.5 pr-4">Método de Envío</th>
                                            <th className="pb-1.5">Acciones</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {sapEntries.map((sap, i) => {
                                            const ss = getOrderStatus(exp);
                                            return (
                                                <tr key={i} className="border-b border-border/30 last:border-0 hover:bg-bg-alt/40 transition-colors">
                                                    <td className="py-2 pr-4 text-xs font-mono font-bold text-[#1a6b5a]">
                                                        {sap.sap_id}
                                                    </td>
                                                    <td className="py-2 pr-4">
                                                        <span className={cn(
                                                            "text-[10px] px-2 py-0.5 rounded font-semibold uppercase",
                                                            ss.bg, ss.color
                                                        )}>
                                                            {sap.status.replace(/_/g, " ")}
                                                        </span>
                                                    </td>
                                                    <td className="py-2 pr-4 text-xs text-text-secondary">
                                                        {sap.shipping_method}
                                                    </td>
                                                    <td className="py-2">
                                                        {/* SAP click → expediente detail */}
                                                        <button
                                                            onClick={() => onOpenExpediente(expId)}
                                                            className="text-xs text-[#1a6b5a] hover:underline font-medium"
                                                        >
                                                            Ver expediente
                                                        </button>
                                                    </td>
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </td>
                </tr>
            )}
        </>
    );
}

// ─── Main Page ─────────────────────────────────────────────────────────────

function ExpedientesContent() {
    const router = useRouter();
    const searchParams = useSearchParams();

    const [data, setData] = useState<Expediente[]>([]);
    const [stats, setStats] = useState<StatsData | null>(null);
    const [loading, setLoading] = useState(true);
    const [statsLoading, setStatsLoading] = useState(true);

    const [globalSearch, setGlobalSearch] = useState(searchParams.get("search") || "");
    const [statusFilter, setStatusFilter] = useState(searchParams.get("status") || "");
    const [isBlocked, setIsBlocked] = useState(searchParams.get("is_blocked") === "true");

    // ── Fetch stats (KPI cards + credit + payments) ──
    const fetchStats = useCallback(async () => {
        setStatsLoading(true);
        try {
            const res = await api.get("ui/expedientes/stats/");
            setStats(res.data);
        } catch {
            setStats(null);
        } finally {
            setStatsLoading(false);
        }
    }, []);

    // ── Fetch expedientes list ──
    const fetchExpedientes = useCallback(async () => {
        setLoading(true);
        try {
            const params = new URLSearchParams();
            if (statusFilter) params.append("status", statusFilter);
            if (globalSearch) params.append("search", globalSearch);

            const res = await api.get(`ui/expedientes/?${params.toString()}`);
            const items = Array.isArray(res.data) ? res.data : (res.data.results || []);
            setData(items);
        } catch {
            setData([]);
        } finally {
            setLoading(false);
        }
    }, [statusFilter, globalSearch]);

    useEffect(() => { fetchStats(); }, [fetchStats]);
    useEffect(() => { fetchExpedientes(); }, [fetchExpedientes]);

    // ··· button → OC detail view
    const openOC = (id: string) => {
        router.push(`/oc/${id}`);
    };
    // SAP sub-row click → expediente detail
    const openExpediente = (id: string) => {
        router.push(`/expedientes/${id}`);
    };

    const filteredData = isBlocked ? data.filter(e => e.is_blocked) : data;

    // ── Loading skeleton for KPI ──
    const KPILoading = () => (
        <div className="h-24 bg-border animate-pulse rounded-xl" />
    );

    return (
        <div className="space-y-6 pb-8">
            {/* ── Header ── */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div className="flex items-center gap-3">
                    <button
                        onClick={() => router.back()}
                        className="p-1.5 rounded-lg hover:bg-bg-alt transition-colors text-text-tertiary hover:text-text-primary"
                    >
                        <ChevronDown size={18} className="rotate-90" />
                    </button>
                    <h1 className="text-xl font-bold text-text-primary">
                        MWT Logistics &amp; Financial Control Center
                    </h1>
                </div>
                <div className="flex items-center gap-3 w-full sm:w-auto">
                    {/* Global search */}
                    <div className="relative flex-1 sm:w-96">
                        <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-tertiary" />
                        <input
                            type="text"
                            placeholder="Search (now scans SKUs, SAPs, OCs)"
                            value={globalSearch}
                            onChange={e => setGlobalSearch(e.target.value)}
                            className="w-full bg-surface border border-border rounded-lg pl-9 pr-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#1a6b5a]/40 transition-all"
                        />
                    </div>
                    <button
                        onClick={() => router.push("/expedientes/nuevo")}
                        className="bg-[#1a6b5a] hover:bg-[#155448] text-white px-4 py-2 rounded-lg text-sm font-medium transition-all shadow-sm active:scale-95 flex items-center gap-2 whitespace-nowrap"
                    >
                        <Plus size={15} /> Nuevo
                    </button>
                </div>
            </div>

            {/* ── KPI Cards ── */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                {statsLoading ? (
                    Array.from({ length: 4 }).map((_, i) => <KPILoading key={i} />)
                ) : (
                    <>
                        <KPICard
                            icon={Package}
                            label="En Producción"
                            count={(stats?.kpi.count_produccion || 0) + (stats?.kpi.count_preparacion || 0)}
                            accent="bg-[#1a6b5a]"
                        />
                        <KPICard
                            icon={Truck}
                            label="En Despacho/Tránsito"
                            count={stats?.kpi.count_despacho_transito || 0}
                            accent="bg-[#2a7d6a]"
                        />
                        <KPICard
                            icon={MapPin}
                            label="En Destino"
                            count={stats?.kpi.count_en_destino || 0}
                            accent="bg-[#1a6b5a]"
                        />
                        <KPICard
                            icon={BarChart3}
                            label="Total Operations"
                            count={stats?.kpi.total_active || 0}
                            accent="bg-[#2a7d6a]"
                        />
                    </>
                )}
            </div>

            {/* ── Main Grid: SKU Table + Credit/Payments ── */}
            <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
                {/* Left: SKU Inventory (2/3) */}
                <div className="xl:col-span-2">
                    {loading ? (
                        <div className="bg-surface border border-border rounded-xl p-5 animate-pulse h-64" />
                    ) : (
                        <SKUTable expedientes={filteredData} />
                    )}
                </div>

                {/* Right: Credit + Payments (1/3) */}
                <div className="flex flex-col gap-4">
                    {statsLoading ? (
                        <>
                            <div className="h-28 bg-border animate-pulse rounded-xl" />
                            <div className="h-40 bg-border animate-pulse rounded-xl" />
                        </>
                    ) : (
                        <>
                            <CreditHealthBar
                                limit={stats?.credit.total_credit_limit || 0}
                                used={stats?.credit.total_credit_used || 0}
                            />
                            <PaymentsTable payments={stats?.recent_payments || []} />
                        </>
                    )}
                </div>
            </div>

            {/* ── Grouped Order List ── */}
            <div className="bg-surface border border-border rounded-xl shadow-sm overflow-hidden">
                {/* Toolbar */}
                <div className="px-5 py-4 border-b border-border flex flex-wrap gap-3 items-center justify-between">
                    <h3 className="text-sm font-semibold text-text-primary">Grouped Order List</h3>
                    <div className="flex items-center gap-3 flex-wrap">
                        <select
                            value={statusFilter}
                            onChange={e => setStatusFilter(e.target.value)}
                            className="bg-bg border border-border rounded-lg px-3 py-1.5 text-xs text-text-secondary focus:outline-none focus:ring-2 focus:ring-[#1a6b5a]/40"
                        >
                            <option value="">Estado: Todos</option>
                            {CANONICAL_STATES.map(s => (
                                <option key={s} value={s}>{s.replace(/_/g, " ")}</option>
                            ))}
                        </select>
                        <label className="flex items-center gap-2 cursor-pointer select-none text-xs text-text-secondary">
                            <input
                                type="checkbox"
                                checked={isBlocked}
                                onChange={e => setIsBlocked(e.target.checked)}
                                className="w-3.5 h-3.5 accent-[#1a6b5a]"
                            />
                            Solo bloqueados {isBlocked && <ShieldAlert size={12} className="text-red-500" />}
                        </label>
                        {(statusFilter || isBlocked) && (
                            <button
                                onClick={() => { setStatusFilter(""); setIsBlocked(false); }}
                                className="text-xs text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 px-2 py-1 rounded flex items-center gap-1 transition-colors"
                            >
                                Limpiar <X size={11} />
                            </button>
                        )}
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead>
                            <tr className="bg-bg-alt/60 text-[10px] uppercase text-text-tertiary tracking-wider border-b border-border">
                                <th className="px-4 py-3">Customer Purchase Order (OC Cliente)</th>
                                <th className="px-4 py-3">Client/Brand</th>
                                <th className="px-4 py-3">Status</th>
                                <th className="px-4 py-3 text-right">Total Cost</th>
                                <th className="px-4 py-3">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                Array.from({ length: 5 }).map((_, i) => (
                                    <tr key={i} className="border-b border-border animate-pulse">
                                        <td className="px-4 py-3"><div className="h-4 bg-border rounded w-32" /></td>
                                        <td className="px-4 py-3"><div className="h-4 bg-border rounded w-24" /></td>
                                        <td className="px-4 py-3"><div className="h-6 bg-border rounded-full w-20" /></td>
                                        <td className="px-4 py-3 text-right"><div className="h-4 bg-border rounded w-20 ml-auto" /></td>
                                        <td className="px-4 py-3"><div className="h-4 bg-border rounded w-8" /></td>
                                    </tr>
                                ))
                            ) : filteredData.length === 0 ? (
                                <tr>
                                    <td colSpan={5} className="px-5 py-16 text-center">
                                        <div className="flex flex-col items-center justify-center gap-3">
                                            <Folder size={40} className="text-border-strong opacity-40" />
                                            <p className="text-sm font-medium text-text-secondary">No se encontraron expedientes</p>
                                            <p className="text-xs text-text-tertiary">Ajusta los filtros o crea un nuevo expediente.</p>
                                        </div>
                                    </td>
                                </tr>
                            ) : (
                                filteredData.map(exp => (
                                    <OrderRow
                                        key={exp.expediente_id || exp.id}
                                        exp={exp}
                                        onOpenOC={openOC}
                                        onOpenExpediente={openExpediente}
                                    />
                                ))
                            )}
                        </tbody>
                    </table>
                </div>

                {!loading && filteredData.length > 0 && (
                    <div className="px-5 py-3 border-t border-border flex items-center justify-between">
                        <p className="text-xs text-text-tertiary">
                            Total: <span className="font-semibold text-text-primary">{filteredData.length}</span> expedientes
                        </p>
                        {isBlocked && (
                            <span className="flex items-center gap-1 text-xs text-red-500">
                                <ShieldAlert size={12} /> {filteredData.length} bloqueados
                            </span>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

export default function ExpedientesListPage() {
    return (
        <Suspense fallback={
            <div className="flex items-center justify-center h-64">
                <div className="flex flex-col items-center gap-3 text-text-tertiary">
                    <div className="w-8 h-8 border-2 border-[#1a6b5a] border-t-transparent rounded-full animate-spin" />
                    <p className="text-sm">Cargando center de control...</p>
                </div>
            </div>
        }>
            <ExpedientesContent />
        </Suspense>
    );
}
