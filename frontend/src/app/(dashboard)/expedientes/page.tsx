"use client";

import { useState, useEffect, useCallback, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import api from "@/lib/api";
import { Search, ShieldAlert, X, ArrowUp, ArrowDown, Folder, ChevronLeft, ChevronRight } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { es } from "date-fns/locale";
import { cn } from "@/lib/utils";

interface Expediente {
    id: string;
    custom_ref: string;
    status: string;
    brand_name: string;
    client_name: string;
    credit_days_elapsed: number;
    credit_band: string;
    total_cost: number;
    is_blocked: boolean;
    last_event_at: string | null;
}

interface PaginatedResponse {
    count: number;
    next: string | null;
    previous: string | null;
    results: Expediente[];
}

const statusOptions = [
    "REGISTRO", "EVALUACION_PREVIA", "FORMALIZACION", "PRODUCCION",
    "QC", "TRANSITO", "ENTREGA", "CERRADO"
];

const brandOptions = [
    "SKECHERS", "ON", "SPEEDO", "TOMS", "ASICS", "VIVAIA"
];

function ExpedientesContent() {
    const router = useRouter();
    const searchParams = useSearchParams();

    // State
    const [data, setData] = useState<PaginatedResponse | null>(null);
    const [loading, setLoading] = useState(true);

    // Filters from URL or default
    const [statusFilter, setStatusFilter] = useState(searchParams.get("status") || "");
    const [brandFilter, setBrandFilter] = useState(searchParams.get("brand_name") || "");
    const [clientFilter, setClientFilter] = useState(searchParams.get("client_name") || "");
    const [isBlocked, setIsBlocked] = useState(searchParams.get("is_blocked") === "true");

    // Sorting
    const [ordering, setOrdering] = useState(searchParams.get("ordering") || "-created_at");

    // Pagination
    const [page, setPage] = useState(Number(searchParams.get("page")) || 1);
    const pageSize = 25;

    const fetchExpedientes = useCallback(async () => {
        setLoading(true);
        try {
            const params = new URLSearchParams();
            if (statusFilter) params.append("status", statusFilter);
            if (brandFilter) params.append("brand_name", brandFilter);
            if (clientFilter) params.append("client_name__icontains", clientFilter); // assuming partial match
            if (isBlocked) params.append("is_blocked", "true");
            params.append("ordering", ordering);
            params.append("page", page.toString());
            params.append("page_size", pageSize.toString());

            const res = await api.get(`/ui/expedientes/?${params.toString()}`);
            setData(res.data);

            // Update URL for shareability
            router.replace(`/expedientes?${params.toString()}`, { scroll: false });
        } catch (error) {
            console.error("Error fetching expedientes", error);
        } finally {
            setLoading(false);
        }
    }, [statusFilter, brandFilter, clientFilter, isBlocked, ordering, page, router]);

    useEffect(() => {
        fetchExpedientes();
    }, [fetchExpedientes]);

    // Handlers
    const handleSort = (field: string) => {
        if (ordering === field) {
            setOrdering(`-${field}`);
        } else {
            setOrdering(field);
        }
        setPage(1);
    };

    const getSortIcon = (field: string) => {
        if (ordering === field) return <ArrowUp size={14} className="ml-1 inline" />;
        if (ordering === `-${field}`) return <ArrowDown size={14} className="ml-1 inline" />;
        return <span className="ml-1 inline-block w-[14px]"></span>;
    };

    const formatter = new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
    });

    const getStatusBadgeColor = (status: string) => {
        switch (status) {
            case 'REGISTRO': return 'bg-ice-soft text-navy border-ice';
            case 'EVALUACION_PREVIA': return 'bg-amber-soft text-amber border-amber/30';
            case 'PRODUCCION': return 'bg-mint-soft text-mint-dark border-mint/30';
            case 'TRANSITO': return 'bg-bg-alt text-text-secondary border-border';
            case 'CERRADO': return 'bg-success-soft text-success border-success/30';
            default: return 'bg-surface hover:bg-surface-hover border-border text-text-secondary';
        }
    };

    const getCreditColor = (band: string) => {
        if (band === 'CORAL') return 'bg-coral';
        if (band === 'AMBER') return 'bg-amber';
        return 'bg-mint';
    };

    return (
        <div className="space-y-6">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                    <h1 className="text-2xl font-display font-bold">Expedientes</h1>
                    <p className="text-sm text-text-tertiary">
                        Gestiona el ciclo de vida, aduanas y bodegaje.
                    </p>
                </div>
            </div>

            {/* Filters Bar */}
            <div className="bg-surface p-4 rounded-xl shadow-sm border border-border flex flex-wrap gap-4 items-center">
                <div className="flex bg-bg border border-border rounded-lg relative flex-1 min-w-[200px]">
                    <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-tertiary" />
                    <input
                        type="text"
                        placeholder="Buscar por cliente..."
                        value={clientFilter}
                        onChange={(e) => { setClientFilter(e.target.value); setPage(1); }}
                        className="w-full bg-transparent pl-10 pr-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-mint-soft rounded-lg"
                    />
                </div>

                <select
                    value={statusFilter}
                    onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
                    className="bg-bg border border-border rounded-lg px-4 py-2 text-sm text-text-secondary focus:outline-none focus:ring-2 focus:ring-mint-soft"
                >
                    <option value="">Estado: Todos</option>
                    {statusOptions.map(s => <option key={s} value={s}>{s}</option>)}
                </select>

                <select
                    value={brandFilter}
                    onChange={(e) => { setBrandFilter(e.target.value); setPage(1); }}
                    className="bg-bg border border-border rounded-lg px-4 py-2 text-sm text-text-secondary focus:outline-none focus:ring-2 focus:ring-mint-soft"
                >
                    <option value="">Marca: Todas</option>
                    {brandOptions.map(b => <option key={b} value={b}>{b}</option>)}
                </select>

                <label className="flex items-center space-x-2 cursor-pointer select-none">
                    <input
                        type="checkbox"
                        checked={isBlocked}
                        onChange={(e) => { setIsBlocked(e.target.checked); setPage(1); }}
                        className="w-4 h-4 text-mint bg-bg border-border rounded focus:ring-mint focus:ring-2 accent-mint"
                    />
                    <span className="text-sm text-text-secondary flex items-center">
                        Solo bloqueados {isBlocked && <ShieldAlert size={14} className="ml-1 text-coral" />}
                    </span>
                </label>

                {(statusFilter || brandFilter || clientFilter || isBlocked) && (
                    <button
                        onClick={() => {
                            setStatusFilter("");
                            setBrandFilter("");
                            setClientFilter("");
                            setIsBlocked(false);
                            setPage(1);
                        }}
                        className="text-xs text-coral hover:bg-coral-soft px-2 py-1 rounded flex items-center transition-colors"
                    >
                        Limpiar <X size={12} className="ml-1" />
                    </button>
                )}
            </div>

            {/* Data Table */}
            <div className="bg-surface rounded-xl shadow-sm border border-border overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse whitespace-nowrap">
                        <thead>
                            <tr className="bg-bg-alt/50 text-xs uppercase text-text-tertiary font-semibold tracking-wider border-b border-border">
                                <th className="px-5 py-4">Ref</th>
                                <th className="px-5 py-4 cursor-pointer hover:text-text-primary select-none w-40" onClick={() => handleSort('status')}>
                                    Estado {getSortIcon('status')}
                                </th>
                                <th className="px-5 py-4">Cliente</th>
                                <th className="px-5 py-4">Marca</th>
                                <th className="px-5 py-4 cursor-pointer hover:text-text-primary select-none" onClick={() => handleSort('credit_days_elapsed')}>
                                    Días Crédito {getSortIcon('credit_days_elapsed')}
                                </th>
                                <th className="px-5 py-4 text-right cursor-pointer hover:text-text-primary select-none" onClick={() => handleSort('total_cost')}>
                                    Monto {getSortIcon('total_cost')}
                                </th>
                                <th className="px-5 py-4 cursor-pointer hover:text-text-primary select-none" onClick={() => handleSort('last_event_at')}>
                                    Actividad {getSortIcon('last_event_at')}
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                // Skeleton loading
                                Array.from({ length: 5 }).map((_, i) => (
                                    <tr key={i} className="border-b border-divider animate-pulse">
                                        <td className="px-5 py-4"><div className="h-4 bg-border rounded w-20"></div></td>
                                        <td className="px-5 py-4"><div className="h-6 bg-border rounded-full w-24"></div></td>
                                        <td className="px-5 py-4"><div className="h-4 bg-border rounded w-32"></div></td>
                                        <td className="px-5 py-4"><div className="h-4 bg-border rounded w-20"></div></td>
                                        <td className="px-5 py-4"><div className="h-4 bg-border rounded w-16"></div></td>
                                        <td className="px-5 py-4 text-right"><div className="h-4 bg-border rounded w-24 ml-auto"></div></td>
                                        <td className="px-5 py-4"><div className="h-4 bg-border rounded w-28"></div></td>
                                    </tr>
                                ))
                            ) : data?.results.length === 0 ? (
                                // Empty state
                                <tr>
                                    <td colSpan={7} className="px-5 py-16 text-center text-text-tertiary">
                                        <div className="flex flex-col items-center justify-center">
                                            <Folder size={48} className="text-border-strong mb-4 opacity-50" />
                                            <p className="text-lg font-medium text-text-secondary">No se encontraron expedientes</p>
                                            <p className="text-sm mt-1">Ajusta los filtros de búsqueda o crea un nuevo expediente desde la API.</p>
                                        </div>
                                    </td>
                                </tr>
                            ) : (
                                data?.results.map((exp, idx) => (
                                    <tr
                                        key={exp.id}
                                        onClick={() => router.push(`/expedientes/${exp.id}`)}
                                        className={cn(
                                            "group cursor-pointer transition-colors border-b border-divider",
                                            "hover:bg-surface-hover hover:border-l-[3px] hover:border-l-mint",
                                            exp.is_blocked ? "border-r-[3px] border-r-coral bg-coral-soft/5" : "border-r-[3px] border-r-transparent",
                                            idx % 2 === 0 ? "bg-surface" : "bg-bg-alt/30",
                                            // Specific case for dual indicator: keep both borders visible
                                            exp.is_blocked && "hover:border-r-coral"
                                        )}
                                        // The left border trick dynamically adjusts padding so layout doesn't shift
                                        style={{ borderLeftWidth: '3px', borderLeftColor: 'transparent' }}
                                    >
                                        <td className="px-5 py-4 font-mono text-sm text-text-primary relative group-hover:text-mint transition-colors">
                                            {exp.custom_ref}
                                        </td>
                                        <td className="px-5 py-4">
                                            <span className={cn(
                                                "inline-flex font-semibold px-2.5 py-1 rounded-md text-[11px] leading-none uppercase border",
                                                getStatusBadgeColor(exp.status)
                                            )}>
                                                {exp.status.replace(/_/g, ' ')}
                                            </span>
                                        </td>
                                        <td className="px-5 py-4 text-sm font-medium text-text-secondary">
                                            {exp.client_name}
                                        </td>
                                        <td className="px-5 py-4 text-sm text-text-secondary">
                                            {exp.brand_name}
                                        </td>
                                        <td className="px-5 py-4">
                                            <div className="flex items-center">
                                                <span className={cn("w-2 h-2 rounded-full mr-2", getCreditColor(exp.credit_band))}></span>
                                                <span className="text-sm font-medium">{exp.credit_days_elapsed} d</span>
                                            </div>
                                        </td>
                                        <td className="px-5 py-4 text-right tabular-nums text-sm font-medium text-text-primary">
                                            {formatter.format(exp.total_cost || 0)}
                                        </td>
                                        <td className="px-5 py-4 text-sm text-text-tertiary">
                                            {exp.last_event_at
                                                ? formatDistanceToNow(new Date(exp.last_event_at), { addSuffix: true, locale: es })
                                                : 'Sin actividad'}
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Pagination Footer */}
                {data && data.count > 0 && (
                    <div className="px-5 py-4 border-t border-border flex items-center justify-between text-sm">
                        <div className="text-text-tertiary">
                            Mostrando <span className="font-medium text-text-primary">{(page - 1) * pageSize + 1}</span> a <span className="font-medium text-text-primary">{Math.min(page * pageSize, data.count)}</span> de <span className="font-medium text-text-primary">{data.count}</span>
                        </div>

                        <div className="flex items-center space-x-2">
                            <button
                                onClick={() => setPage(page - 1)}
                                disabled={!data.previous}
                                className="p-1.5 rounded border border-border text-text-secondary disabled:opacity-50 disabled:cursor-not-allowed hover:bg-bg transition-colors"
                                title="Página Anterior"
                            >
                                <ChevronLeft size={16} />
                            </button>

                            {/* Basic page numbers for MVP, could use a proper ellipsis pagination later */}
                            <span className="px-3 py-1 font-medium bg-mint-soft text-mint-dark rounded-md">
                                {page}
                            </span>

                            <button
                                onClick={() => setPage(page + 1)}
                                disabled={!data.next}
                                className="p-1.5 rounded border border-border text-text-secondary disabled:opacity-50 disabled:cursor-not-allowed hover:bg-bg transition-colors"
                                title="Página Siguiente"
                            >
                                <ChevronRight size={16} />
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

export default function ExpedientesListPage() {
    return (
        <Suspense fallback={
            <div className="flex items-center justify-center h-64 text-text-tertiary">
                Cargando expedientes...
            </div>
        }>
            <ExpedientesContent />
        </Suspense>
    );
}
