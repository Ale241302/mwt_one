"use client";
/**
 * OC Detail Page — Vista de Cliente: Detalle de OC y SAPs
 *
 * REDESIGN-2026-04-16:
 *  - Columna SAP Asociado VISIBLE para todos (no solo admin)
 *  - Vista cliente: muestra SKU, Nombre, SAP Asociado, Cantidad OC, Precio OC, Cantidad Real Recibida
 *    NO muestra Precio Real de Compra (solo admin)
 *  - Progreso: badge "EN CURSO" a la izquierda, incoterms badge a la derecha
 *  - Proformas Asociadas: lista numerada estilo "Download de Documento N: descripción"
 *  - Eventos: texto human-readable
 *  - Panel financiero más compacto y limpio
 */
import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import api from "@/lib/api";
import {
    ArrowLeft, Plus, Download, FileText, FileSpreadsheet,
    AlertTriangle, Package, Truck,
    X, Upload, ExternalLink, Loader2, ShieldAlert,
    CheckCircle2,
} from "lucide-react";
import { cn } from "@/lib/utils";

// ─── Types ───────────────────────────────────────────────────────────────────

interface ProductLine {
    id: number;
    sku: string;
    product_name: string;
    quantity_oc: number;
    price_oc: number;
    quantity_real: number;
    price_real: number;
    sap_ref: string | null;
}

interface SAPEntry {
    id: number;
    sap_id: string;
    status: string;
    shipping_method: string;
    expediente_id: string;
    url: string;
}

interface OCProforma {
    id: number;
    proforma_number: string;
    file_url: string | null;
    filename: string;
    file_type: string | null;
    notes: string | null;
    created_at: string;
    created_by: string | null;
}

interface OCEvent {
    id: string;
    event_type: string;
    occurred_at: string;
    emitted_by: string;
}

interface OCBundle {
    expediente_id: string;
    oc_ref: string;
    client_name: string;
    brand_name: string;
    status: string;
    payment_status: string;
    progress_pct: number;
    is_admin: boolean;
    incoterms: string;
    product_lines: ProductLine[];
    sap_entries: SAPEntry[];
    oc_proformas: OCProforma[];
    financials: {
        total_oc: number;
        total_paid: number;
        remaining_credit: number;
        currency: string;
    };
    events: OCEvent[];
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

const USD = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });

/** Map backend event_type codes to human-readable strings */
function humanizeEvent(eventType: string): string {
    const map: Record<string, string> = {
        "expediente.registered":       "Order Confirmed",
        "expediente.oc_registered":    "Order Confirmed",
        "expediente.produccion":       "Production Started",
        "expediente.production_confirmed": "Production Confirmed",
        "expediente.preparacion":      "Preparation Started",
        "expediente.despacho":         "Dispatch Initiated",
        "expediente.transito":         "In Transit",
        "expediente.en_destino":       "Arrived at Destination",
        "expediente.cerrado":          "Order Closed",
        "artifact.completed":          "Document Available",
        "artifact.created":            "Document Created",
        "payment.registered":          "Payment Registered",
        "payment.released":            "Payment Released",
    };
    // Try direct match first, then try prefix matching
    if (map[eventType]) return map[eventType];
    for (const [key, val] of Object.entries(map)) {
        if (eventType.includes(key.split(".")[1] ?? "")) return val;
    }
    // Fallback: capitalize and clean underscores
    return eventType.replace(/\./g, " · ").replace(/_/g, " ")
        .replace(/\b\w/g, c => c.toUpperCase());
}

function getStatusStyle(status: string): { bg: string; text: string } {
    const map: Record<string, { bg: string; text: string }> = {
        PRODUCCION:  { bg: "bg-amber-100",  text: "text-amber-700" },
        PREPARACION: { bg: "bg-blue-100",   text: "text-blue-700" },
        DESPACHO:    { bg: "bg-purple-100", text: "text-purple-700" },
        TRANSITO:    { bg: "bg-sky-100",    text: "text-sky-700" },
        EN_DESTINO:  { bg: "bg-teal-100",   text: "text-teal-700" },
        CERRADO:     { bg: "bg-gray-100",   text: "text-gray-600" },
        CANCELADO:   { bg: "bg-red-100",    text: "text-red-700" },
        REGISTRO:    { bg: "bg-slate-100",  text: "text-slate-600" },
    };
    return map[status] ?? { bg: "bg-slate-100", text: "text-slate-600" };
}

function getProgressLabel(status: string): string {
    const map: Record<string, string> = {
        REGISTRO:    "REGISTRO",
        PRODUCCION:  "EN CURSO",
        PREPARACION: "EN CURSO",
        DESPACHO:    "EN TRÁNSITO",
        TRANSITO:    "EN TRÁNSITO",
        EN_DESTINO:  "EN DESTINO",
        CERRADO:     "COMPLETADO",
        CANCELADO:   "CANCELADO",
    };
    return map[status] ?? status;
}

function getShippingIcon(method: string): string {
    const lower = method.toLowerCase();
    if (lower.includes("aér") || lower.includes("aer") || lower.includes("air")) return "✈";
    if (lower.includes("marítim") || lower.includes("maritim") || lower.includes("sea") || lower.includes("ocean")) return "⛴";
    if (lower.includes("terrestre") || lower.includes("land") || lower.includes("road")) return "🚛";
    return "📦";
}

function fileIcon(type: string | null) {
    if (type === "pdf")  return <FileText size={15} className="text-red-500 flex-shrink-0" />;
    if (type === "xlsx") return <FileSpreadsheet size={15} className="text-green-600 flex-shrink-0" />;
    return <FileText size={15} className="text-text-tertiary flex-shrink-0" />;
}

// ─── Modal: Añadir Proforma (admin only) ──────────────────────────────────────

interface ProformaModalProps {
    expedienteId: string;
    onClose: () => void;
    onSuccess: (pf: OCProforma) => void;
}

function ProformaModal({ expedienteId, onClose, onSuccess }: ProformaModalProps) {
    const [proformaNumber, setProformaNumber] = useState("");
    const [fileUrl, setFileUrl] = useState("");
    const [filename, setFilename] = useState("");
    const [notes, setNotes] = useState("");
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleUrlChange = (val: string) => {
        setFileUrl(val);
        if (val && !filename) {
            const parts = val.split("/");
            const last = parts[parts.length - 1];
            if (last && last.includes(".")) setFilename(decodeURIComponent(last));
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!proformaNumber.trim()) { setError("El número de proforma es requerido."); return; }
        setSaving(true); setError(null);
        try {
            const lower = fileUrl.toLowerCase();
            let file_type: string | undefined;
            if (lower.endsWith(".pdf")) file_type = "pdf";
            else if (lower.endsWith(".xlsx") || lower.endsWith(".xls")) file_type = "xlsx";
            else if (fileUrl) file_type = "other";

            const res = await api.post(`ui/expedientes/${expedienteId}/oc/proformas/`, {
                proforma_number: proformaNumber.trim(),
                file_url: fileUrl.trim() || null,
                filename: filename.trim() || null,
                file_type: file_type || null,
                notes: notes.trim() || null,
            });
            onSuccess(res.data);
        } catch (err: unknown) {
            const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
            setError(msg || "Error al crear la proforma.");
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-surface border border-border rounded-2xl shadow-2xl w-full max-w-md">
                <div className="flex items-center justify-between px-6 py-4 border-b border-border">
                    <h2 className="text-base font-semibold text-text-primary">Añadir Proforma</h2>
                    <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-bg-alt transition-colors">
                        <X size={16} className="text-text-tertiary" />
                    </button>
                </div>
                <form onSubmit={handleSubmit} className="px-6 py-5 space-y-4">
                    <div>
                        <label className="block text-xs font-medium text-text-secondary mb-1.5">
                            Número de Proforma <span className="text-red-500">*</span>
                        </label>
                        <input
                            type="text"
                            value={proformaNumber}
                            onChange={e => setProformaNumber(e.target.value)}
                            placeholder="PF-12345 / OC-2026-001"
                            className="w-full bg-bg border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#1a6b5a]/40 transition-all"
                            autoFocus
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-text-secondary mb-1.5">
                            URL del Archivo <span className="text-text-tertiary text-[10px]">(PDF o XLSX)</span>
                        </label>
                        <div className="relative">
                            <Upload size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-tertiary" />
                            <input
                                type="url"
                                value={fileUrl}
                                onChange={e => handleUrlChange(e.target.value)}
                                placeholder="https://drive.google.com/..."
                                className="w-full bg-bg border border-border rounded-lg pl-8 pr-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#1a6b5a]/40 transition-all"
                            />
                        </div>
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-text-secondary mb-1.5">Nombre del Archivo</label>
                        <input
                            type="text"
                            value={filename}
                            onChange={e => setFilename(e.target.value)}
                            placeholder="proforma_octubre.pdf"
                            className="w-full bg-bg border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#1a6b5a]/40 transition-all"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-text-secondary mb-1.5">
                            Notas <span className="text-text-tertiary text-[10px]">(opcional)</span>
                        </label>
                        <textarea
                            value={notes}
                            onChange={e => setNotes(e.target.value)}
                            rows={2}
                            placeholder="Información adicional..."
                            className="w-full bg-bg border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#1a6b5a]/40 transition-all resize-none"
                        />
                    </div>
                    {error && (
                        <div className="flex items-center gap-2 text-xs text-red-600 bg-red-50 px-3 py-2 rounded-lg">
                            <AlertTriangle size={13} /> {error}
                        </div>
                    )}
                    <div className="flex gap-3 pt-1">
                        <button
                            type="button"
                            onClick={onClose}
                            className="flex-1 px-4 py-2 text-sm border border-border rounded-lg hover:bg-bg-alt transition-colors"
                        >
                            Cancelar
                        </button>
                        <button
                            type="submit"
                            disabled={saving}
                            className="flex-1 px-4 py-2 text-sm bg-[#1a6b5a] hover:bg-[#155448] text-white rounded-lg font-medium transition-all active:scale-95 disabled:opacity-60 flex items-center justify-center gap-2"
                        >
                            {saving ? <Loader2 size={14} className="animate-spin" /> : <Plus size={14} />}
                            {saving ? "Guardando..." : "Crear Proforma"}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function OCDetailPage() {
    const params = useParams();
    const router = useRouter();
    const id = params?.id as string;

    const [bundle, setBundle] = useState<OCBundle | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showProformaModal, setShowProformaModal] = useState(false);

    const fetchBundle = useCallback(async () => {
        if (!id) return;
        setLoading(true);
        setError(null);
        try {
            const res = await api.get(`ui/expedientes/${id}/oc/`);
            setBundle(res.data);
        } catch {
            setError("No se pudo cargar la Orden de Compra. Verifica que tienes acceso.");
        } finally {
            setLoading(false);
        }
    }, [id]);

    useEffect(() => { fetchBundle(); }, [fetchBundle]);

    const handleProformaSuccess = (pf: OCProforma) => {
        setBundle(prev => prev ? { ...prev, oc_proformas: [pf, ...prev.oc_proformas] } : prev);
        setShowProformaModal(false);
    };

    // ── Loading ──
    if (loading) {
        return (
            <div className="flex items-center justify-center h-72">
                <div className="flex flex-col items-center gap-3 text-text-tertiary">
                    <div className="w-8 h-8 border-2 border-[#1a6b5a] border-t-transparent rounded-full animate-spin" />
                    <p className="text-sm">Cargando OC...</p>
                </div>
            </div>
        );
    }

    // ── Error ──
    if (error || !bundle) {
        return (
            <div className="flex flex-col items-center justify-center h-72 gap-4">
                <ShieldAlert size={40} className="text-red-400" />
                <p className="text-base font-medium text-text-secondary">{error || "OC no encontrada"}</p>
                <button
                    onClick={() => router.back()}
                    className="text-sm text-[#1a6b5a] hover:underline flex items-center gap-1"
                >
                    <ArrowLeft size={14} /> Volver
                </button>
            </div>
        );
    }

    const { financials, product_lines, sap_entries, oc_proformas, events } = bundle;
    const statusStyle = getStatusStyle(bundle.status);
    const progressLabel = getProgressLabel(bundle.status);

    return (
        <>
            {showProformaModal && (
                <ProformaModal
                    expedienteId={bundle.expediente_id}
                    onClose={() => setShowProformaModal(false)}
                    onSuccess={handleProformaSuccess}
                />
            )}

            <div className="space-y-5 pb-10">

                {/* ── Page title (visible en ambas vistas) ── */}
                <div className="text-xs text-text-tertiary font-medium uppercase tracking-wide">
                    Vista de Cliente — Detalle de OC y SAPs
                </div>

                {/* ── Header ── */}
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                    <div>
                        <button
                            onClick={() => router.back()}
                            className="flex items-center gap-1.5 text-sm text-text-tertiary hover:text-text-primary mb-2 transition-colors"
                        >
                            <ArrowLeft size={14} /> Volver
                        </button>
                        <h1 className="text-2xl font-bold text-text-primary">
                            Orden de Compra (OC) #{bundle.oc_ref}
                        </h1>
                        <p className="text-sm text-text-tertiary mt-0.5">
                            Cliente: <span className="font-medium text-text-secondary">{bundle.client_name}</span>
                            {" · "}
                            Valor Total: <span className="font-semibold text-text-primary">{USD.format(financials.total_oc)}</span>
                        </p>
                    </div>

                    {/* Admin-only buttons */}
                    {bundle.is_admin && (
                        <div className="flex gap-2 flex-shrink-0">
                            <button
                                disabled
                                title="Próximamente"
                                className="flex items-center gap-1.5 px-3 py-2 bg-surface border border-border text-text-secondary rounded-lg text-sm font-medium opacity-50 cursor-not-allowed"
                            >
                                <Plus size={14} /> Añadir SAP
                            </button>
                            <button
                                onClick={() => setShowProformaModal(true)}
                                className="flex items-center gap-1.5 px-4 py-2 bg-[#1a6b5a] hover:bg-[#155448] text-white rounded-lg text-sm font-medium transition-all shadow-sm active:scale-95"
                            >
                                <Plus size={14} /> Añadir Proforma
                            </button>
                        </div>
                    )}
                </div>

                {/* ── Main 3-column grid ── */}
                <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">

                    {/* ════ LEFT — 2/3 width ════ */}
                    <div className="xl:col-span-2 space-y-5">

                        {/* Progress bar */}
                        <div className="bg-surface border border-border rounded-xl p-5 shadow-sm">
                            <h3 className="text-sm font-semibold text-text-primary mb-3">
                                Progreso General de OC
                            </h3>
                            {/* Bar */}
                            <div className="relative w-full h-4 bg-bg-alt rounded-full overflow-visible mb-3">
                                <div
                                    className="h-full bg-[#1a6b5a] rounded-full transition-all duration-700 relative"
                                    style={{ width: `${bundle.progress_pct}%` }}
                                >
                                    {bundle.progress_pct > 5 && (
                                        <div className="absolute right-0 top-1/2 -translate-y-1/2 w-4 h-4 border-2 border-white bg-[#1a6b5a] rounded-full shadow-sm" />
                                    )}
                                </div>
                            </div>
                            {/* Badges row: status label left, incoterms right */}
                            <div className="flex items-center justify-between">
                                <span className={cn(
                                    "text-xs px-3 py-1 rounded-full font-bold uppercase tracking-wide",
                                    progressLabel === "EN CURSO"
                                        ? "bg-emerald-100 text-emerald-700"
                                        : progressLabel === "COMPLETADO"
                                        ? "bg-[#1a6b5a]/10 text-[#1a6b5a]"
                                        : statusStyle.bg, statusStyle.text
                                )}>
                                    {progressLabel}
                                </span>
                                {bundle.incoterms && bundle.incoterms !== "—" && (
                                    <span className="text-[11px] font-bold px-3 py-1 rounded-full bg-amber-100 text-amber-700 uppercase tracking-wide">
                                        {bundle.incoterms}
                                    </span>
                                )}
                            </div>
                        </div>

                        {/* ── Product Detail Table ── */}
                        <div className="bg-surface border border-border rounded-xl shadow-sm overflow-hidden">
                            <div className="px-5 py-4 border-b border-border">
                                <h3 className="text-sm font-semibold text-text-primary">
                                    Detalle de Productos de la OC
                                </h3>
                            </div>
                            <div className="overflow-x-auto">
                                <table className="w-full text-left text-sm">
                                    <thead>
                                        <tr className="bg-bg-alt/60 text-[10px] uppercase text-text-tertiary tracking-wider border-b border-border">
                                            <th className="px-4 py-3">SKU</th>
                                            <th className="px-4 py-3">Nombre del Producto</th>
                                            {/* SAP Asociado: visible for ALL users (client + admin) */}
                                            <th className="px-4 py-3">SAP Asociado</th>
                                            <th className="px-4 py-3 text-right">Cantidad OC</th>
                                            <th className="px-4 py-3 text-right">Precio OC</th>
                                            <th className="px-4 py-3 text-right">Cantidad Real Recibida</th>
                                            {/* Price Real: admin only */}
                                            {bundle.is_admin && (
                                                <th className="px-4 py-3 text-right">Precio Real de Compra</th>
                                            )}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {product_lines.length === 0 ? (
                                            <tr>
                                                <td
                                                    colSpan={bundle.is_admin ? 7 : 6}
                                                    className="px-4 py-8 text-center text-sm text-text-tertiary"
                                                >
                                                    Sin líneas de producto registradas
                                                </td>
                                            </tr>
                                        ) : product_lines.map(line => (
                                            <tr
                                                key={line.id}
                                                className="border-b border-border/50 last:border-0 hover:bg-bg-alt/30 transition-colors"
                                            >
                                                <td className="px-4 py-2.5 text-xs font-mono font-semibold text-text-primary">
                                                    {line.sku}
                                                </td>
                                                <td className="px-4 py-2.5 text-xs text-text-secondary">
                                                    {line.product_name}
                                                </td>
                                                {/* SAP Asociado badge — always shown */}
                                                <td className="px-4 py-2.5">
                                                    {line.sap_ref ? (
                                                        <span className="text-[11px] font-bold px-2 py-0.5 rounded bg-[#1a3a32] text-white">
                                                            {line.sap_ref}
                                                        </span>
                                                    ) : (
                                                        <span className="text-xs text-text-tertiary">—</span>
                                                    )}
                                                </td>
                                                <td className="px-4 py-2.5 text-xs text-right tabular-nums text-text-secondary">
                                                    {line.quantity_oc.toLocaleString()}
                                                </td>
                                                <td className="px-4 py-2.5 text-xs text-right tabular-nums text-text-secondary">
                                                    {USD.format(line.price_oc)}
                                                </td>
                                                <td className="px-4 py-2.5 text-xs text-right tabular-nums text-text-secondary">
                                                    {line.quantity_real.toLocaleString()}
                                                </td>
                                                {/* Price Real — admin only */}
                                                {bundle.is_admin && (
                                                    <td className="px-4 py-2.5 text-xs text-right tabular-nums font-semibold text-text-primary">
                                                        {USD.format(line.price_real)}
                                                    </td>
                                                )}
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>

                        {/* ── Bottom row: SAP Asociados + Proformas ── */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">

                            {/* Envíos SAP Asociados */}
                            <div className="bg-surface border border-border rounded-xl shadow-sm overflow-hidden">
                                <div className="px-5 py-4 border-b border-border flex items-center gap-2">
                                    <Truck size={15} className="text-[#1a6b5a]" />
                                    <h3 className="text-sm font-semibold text-text-primary">Envíos SAP Asociados</h3>
                                </div>
                                <div className="overflow-x-auto">
                                    <table className="w-full text-left">
                                        <thead>
                                            <tr className="bg-bg-alt/50 text-[10px] uppercase text-text-tertiary tracking-wide border-b border-border">
                                                <th className="px-4 py-2.5">SAP ID</th>
                                                <th className="px-4 py-2.5">Estado</th>
                                                <th className="px-4 py-2.5">Método de Envío</th>
                                                <th className="px-4 py-2.5">Acciones</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {sap_entries.length === 0 ? (
                                                <tr>
                                                    <td colSpan={4} className="px-4 py-6 text-center text-xs text-text-tertiary">
                                                        Sin SAPs registrados
                                                    </td>
                                                </tr>
                                            ) : sap_entries.map(sap => {
                                                const ss = getStatusStyle(sap.status);
                                                const icon = getShippingIcon(sap.shipping_method);
                                                return (
                                                    <tr key={sap.id} className="border-b border-border/50 last:border-0 hover:bg-bg-alt/20 transition-colors">
                                                        <td className="px-4 py-2.5 text-xs font-mono font-semibold text-text-primary">
                                                            {sap.sap_id}
                                                        </td>
                                                        <td className="px-4 py-2.5">
                                                            <span className={cn(
                                                                "text-[10px] px-2 py-0.5 rounded font-semibold uppercase",
                                                                ss.bg, ss.text
                                                            )}>
                                                                {sap.status.replace(/_/g, " ")}
                                                            </span>
                                                        </td>
                                                        <td className="px-4 py-2.5 text-xs text-text-secondary">
                                                            {sap.shipping_method === "—" ? "—" : (
                                                                <span className="flex items-center gap-1">
                                                                    <span>{icon}</span>
                                                                    <span>{sap.shipping_method}</span>
                                                                </span>
                                                            )}
                                                        </td>
                                                        <td className="px-4 py-2.5">
                                                            <button
                                                                onClick={() => router.push(`/expedientes/${sap.expediente_id}`)}
                                                                className="text-xs text-[#1a6b5a] hover:underline font-medium"
                                                            >
                                                                Ver detalles
                                                            </button>
                                                        </td>
                                                    </tr>
                                                );
                                            })}
                                        </tbody>
                                    </table>
                                </div>
                            </div>

                            {/* Proformas Asociadas */}
                            <div className="bg-surface border border-border rounded-xl shadow-sm overflow-hidden">
                                <div className="px-5 py-4 border-b border-border flex items-center gap-2">
                                    <Package size={15} className="text-[#1a6b5a]" />
                                    <h3 className="text-sm font-semibold text-text-primary">Proformas Asociadas</h3>
                                </div>
                                <div className="px-5 py-4 space-y-3">
                                    {oc_proformas.length === 0 ? (
                                        <p className="text-xs text-text-tertiary text-center py-3">
                                            Sin proformas asociadas.
                                        </p>
                                    ) : oc_proformas.map((pf, idx) => (
                                        <div key={pf.id} className="flex items-center gap-2.5">
                                            {fileIcon(pf.file_type)}
                                            <div className="flex-1 min-w-0">
                                                {pf.file_url ? (
                                                    <a
                                                        href={pf.file_url}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="text-sm text-[#1a6b5a] hover:underline font-medium flex items-center gap-1"
                                                    >
                                                        <Download size={12} className="flex-shrink-0" />
                                                        <span className="truncate">
                                                            Download de Documento {idx + 1}
                                                            {pf.notes ? `: ${pf.notes}` : pf.filename ? `: ${pf.filename}` : ""}
                                                        </span>
                                                    </a>
                                                ) : (
                                                    <span className="text-sm text-text-tertiary flex items-center gap-1">
                                                        <Download size={12} className="flex-shrink-0 opacity-40" />
                                                        {pf.filename || pf.proforma_number}
                                                    </span>
                                                )}
                                                {pf.notes && pf.file_url && (
                                                    <p className="text-[10px] text-text-tertiary truncate mt-0.5 ml-4">
                                                        {pf.proforma_number}
                                                    </p>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* ════ RIGHT — 1/3 width ════ */}
                    <div className="space-y-5">

                        {/* Financial summary */}
                        <div className="bg-surface border border-border rounded-xl shadow-sm p-5 divide-y divide-border">
                            <div className="pb-4">
                                <p className="text-xs text-text-tertiary font-medium">Total OC Amount</p>
                                <p className="text-2xl font-bold text-text-primary mt-0.5">
                                    {USD.format(financials.total_oc)}
                                </p>
                            </div>
                            <div className="py-4">
                                <p className="text-xs text-text-tertiary font-medium">Total Payments Made</p>
                                <p className="text-2xl font-bold text-[#1a6b5a] mt-0.5">
                                    {USD.format(financials.total_paid)}
                                </p>
                            </div>
                            <div className="pt-4">
                                <p className="text-xs text-text-tertiary font-medium">Remaining Credit</p>
                                <p className={cn(
                                    "text-2xl font-bold mt-0.5",
                                    financials.remaining_credit > 0 ? "text-amber-600" : "text-emerald-600"
                                )}>
                                    {USD.format(Math.max(0, financials.remaining_credit))}
                                </p>
                            </div>
                        </div>

                        {/* Event History */}
                        <div className="bg-surface border border-border rounded-xl shadow-sm p-5">
                            <h3 className="text-sm font-semibold text-text-primary mb-4">Historial de eventos</h3>
                            {events.length === 0 ? (
                                <p className="text-xs text-text-tertiary">Sin eventos registrados.</p>
                            ) : (
                                <div className="space-y-3">
                                    {events.slice(0, 8).map((ev, i) => (
                                        <div key={ev.id ?? i} className="flex gap-3">
                                            {/* Timeline dot + line */}
                                            <div className="flex flex-col items-center flex-shrink-0">
                                                <div className={cn(
                                                    "w-2.5 h-2.5 rounded-full mt-0.5 border-2",
                                                    i === 0
                                                        ? "bg-[#1a6b5a] border-[#1a6b5a]"
                                                        : "bg-white border-border-strong"
                                                )} />
                                                {i < Math.min(events.length, 8) - 1 && (
                                                    <div className="w-px flex-1 bg-border mt-1 min-h-[16px]" />
                                                )}
                                            </div>
                                            <div className="pb-3 flex-1 min-w-0">
                                                <p className="text-[10px] text-text-tertiary">
                                                    {ev.occurred_at
                                                        ? new Date(ev.occurred_at).toLocaleDateString("es-CR", {
                                                            day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit"
                                                          })
                                                        : "—"}
                                                </p>
                                                <p className="text-xs text-text-secondary font-medium mt-0.5">
                                                    {humanizeEvent(ev.event_type)}
                                                </p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* Admin-only: link to full expediente */}
                        {bundle.is_admin && (
                            <button
                                onClick={() => router.push(`/expedientes/${bundle.expediente_id}`)}
                                className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-bg-alt border border-border rounded-xl text-sm text-text-secondary hover:text-text-primary hover:bg-surface transition-all"
                            >
                                <ExternalLink size={14} />
                                Ver Expediente Completo
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </>
    );
}
