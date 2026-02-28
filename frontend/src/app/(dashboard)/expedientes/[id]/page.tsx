"use client";

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { formatDistanceToNow, parseISO, format } from 'date-fns';
import { es } from 'date-fns/locale';
import { cn } from '@/lib/utils';
import api from '@/lib/api';
import toast from 'react-hot-toast';
import { ArrowLeft, ShieldAlert, CheckCircle2, XCircle, FileText, Ban } from 'lucide-react';

interface EventLog {
    event_id: string;
    event_type: string;
    aggregate_type: string;
    aggregate_id: string;
    payload: Record<string, unknown>;
    occurred_at: string;
    emitted_by: string;
    processed_at: string | null;
    retry_count: number;
}

interface Artifact {
    artifact_id: string;
    artifact_type: string;
    status: string;
    status_display: string;
    payload: Record<string, unknown>;
    supersedes: number | null;
    superseded_by: number | null;
    created_at: string;
    updated_at: string;
}

interface Expediente {
    expediente_id: number;
    brand: string;
    client: string;
    status: string;
    status_display: string;
    is_blocked: boolean;
    blocked_reason: string;
    blocked_at: string | null;
    mode: string;
    freight_mode: string;
    transport_mode: string;
    dispatch_mode: string;
    credit_clock_started_at: string | null;
    created_at: string;
    legal_entity_name: string;
}

interface ExpedienteBundle {
    expediente: Expediente;
    events: EventLog[];
    artifacts: Artifact[];
    available_actions: string[];
}

const TIMELINE_STATES = [
    { id: 'REGISTRO', label: 'Registro' },
    { id: 'PRODUCCION', label: 'Producción' },
    { id: 'PREPARACION', label: 'Preparación' },
    { id: 'TRANSITO', label: 'En Tránsito' },
    { id: 'DESTINO', label: 'En Destino' },
    { id: 'FACTURADO', label: 'Facturado' },
    { id: 'CERRADO', label: 'Cerrado' }
];

const COMMAND_LABELS: Record<string, string> = {
    'C2': 'Registrar OC',
    'C3': 'Registrar Proforma',
    'C4': 'Decidir Modo',
    'C5': 'Confirmar SAP',
    'C6': 'Confirmar Prod.',
    'C7': 'Registrar Embarque',
    'C8': 'Instruir Despacho',
    'C9': 'Registrar Zarpe',
    'C10': 'Registrar BL',
    'C11': 'Registrar Arribo P.',
    'C12': 'Confirmar Arribo',
    'C13': 'Liberar Aduana',
    'C14': 'Entregar',
};

export default function ExpedienteDetailPage() {
    const params = useParams();
    const id = params.id as string;
    const router = useRouter();
    const { user, loading: authLoading } = useAuth();

    const [bundle, setBundle] = useState<ExpedienteBundle | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchBundle = async () => {
        try {
            setLoading(true);
            setError(null);
            const { data } = await api.get(`/api/ui/expedientes/${id}/`);
            setBundle(data);
        } catch (err: unknown) {
            console.error('Error fetching expediente bundle:', err);
            const e = err as { response?: { data?: { detail?: string } }, message?: string };
            setError(e.response?.data?.detail || 'Error al cargar expediente');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (!authLoading && user) {
            fetchBundle();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [user, authLoading, id]);

    const handleAction = async (cmd: string) => {
        // For now, MVP: we just mock execution with a toast, or we can actually call things if they have no payload.
        // C6 uses no payload.
        toast.success(`Ejecutando acción ${COMMAND_LABELS[cmd] || cmd}...`);
        try {
            let endpoint = '';
            const payload = {};

            switch (cmd) {
                case 'C6': endpoint = `/api/expedientes/${id}/confirm-production/`; break;
                // other commands will need modals.
                default:
                    toast('Acción requiere payload. No implementada en UI aún.', { icon: '🚧' });
                    return;
            }

            await api.post(endpoint, payload);
            toast.success('Comando ejecutado con éxito');
            fetchBundle();
        } catch (err: unknown) {
            const e = err as { response?: { data?: { detail?: string } }, message?: string };
            toast.error('Error al ejecutar: ' + (e.response?.data?.detail || e.message));
        }
    };

    if (loading) {
        return (
            <div className="flex flex-col space-y-4 p-8">
                <div className="h-8 w-64 bg-slate-200 animate-pulse rounded"></div>
                <div className="h-48 bg-slate-200 animate-pulse rounded"></div>
                <div className="h-64 bg-slate-200 animate-pulse rounded"></div>
            </div>
        );
    }

    if (error || !bundle) {
        return (
            <div className="p-8">
                <div className="bg-red-50 text-red-600 p-4 rounded-xl border border-red-200 inline-flex items-center gap-2">
                    <XCircle className="w-5 h-5" />
                    {error || 'No se encontró el expediente'}
                </div>
                <div className="mt-4">
                    <button
                        onClick={() => router.push('/expedientes')}
                        className="text-navy hover:underline"
                    >
                        ← Volver a expedientes
                    </button>
                </div>
            </div>
        );
    }

    const { expediente, artifacts, available_actions } = bundle;

    // Credit clock calculation
    let creditDays = 0;
    let creditType: 'ok' | 'amber' | 'coral' = 'ok';

    if (expediente.credit_clock_started_at) {
        const start = parseISO(expediente.credit_clock_started_at);
        const diffTime = Math.abs(new Date().getTime() - start.getTime());
        creditDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

        if (creditDays >= 75) creditType = 'coral';
        else if (creditDays >= 60) creditType = 'amber';
    }

    // Timeline computation
    const currentStateIndex = TIMELINE_STATES.findIndex(s => s.id === expediente.status);

    return (
        <div className="max-w-6xl mx-auto space-y-6">

            <button
                onClick={() => router.back()}
                className="text-sm text-text-secondary hover:text-navy flex items-center transition-colors"
            >
                <ArrowLeft className="w-4 h-4 mr-1" />
                Volver a expedientes
            </button>

            {/* Header */}
            <div className="flex items-center gap-4 flex-wrap">
                <h1 className="text-3xl font-display font-medium text-text-primary tracking-tight">
                    EXP-2026-{expediente.expediente_id.toString().padStart(4, '0')}
                </h1>
                <div className="flex gap-2 items-center">
                    <span className={cn(
                        "px-2.5 py-1 text-xs font-semibold rounded-full border shadow-sm",
                        expediente.status === 'REGISTRO' ? "bg-slate-100 text-slate-700 border-slate-200" :
                            expediente.status === 'CERRADO' ? "bg-emerald-50 text-emerald-700 border-emerald-200" :
                                "bg-blue-50 text-navy border-blue-200"
                    )}>
                        {expediente.status_display}
                    </span>

                    {creditDays > 0 && (
                        <span className={cn(
                            "flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold rounded-full border shadow-sm",
                            creditType === 'coral' ? "bg-red-50 text-coral border-red-200" :
                                creditType === 'amber' ? "bg-orange-50 text-amber border-orange-200" :
                                    "bg-emerald-50 text-mint border-emerald-200"
                        )}>
                            <span className={cn("w-2 h-2 rounded-full",
                                creditType === 'coral' ? "bg-coral shadow-[0_0_8px_rgba(255,107,107,0.5)]" :
                                    creditType === 'amber' ? "bg-amber shadow-[0_0_8px_rgba(255,190,40,0.5)]" :
                                        "bg-mint shadow-[0_0_8px_rgba(50,215,140,0.5)]"
                            )} />
                            {creditDays} días crédito
                        </span>
                    )}

                    {expediente.is_blocked && (
                        <span className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-bold rounded-full bg-red-100 text-red-700 border border-red-200 shadow-sm animate-pulse-soft">
                            <Ban className="w-3.5 h-3.5" />
                            BLOQUEADO
                        </span>
                    )}
                </div>
            </div>

            {/* Timeline */}
            <div className="bg-surface rounded-2xl border border-border shadow-sm p-6 overflow-x-auto">
                <h4 className="text-sm font-semibold text-text-secondary mb-6 uppercase tracking-wider">Timeline</h4>
                <div className="flex items-center justify-between min-w-[700px]">
                    {TIMELINE_STATES.map((state, idx) => {
                        const isCompleted = idx < currentStateIndex;
                        const isCurrent = idx === currentStateIndex;
                        // find event to know how long it took? MVP: just show structure.
                        return (
                            <div key={state.id} className="relative flex-1 group">
                                {/* Connecting line */}
                                {idx < TIMELINE_STATES.length - 1 && (
                                    <div className={cn(
                                        "absolute top-4 left-1/2 w-full h-[2px] -z-10",
                                        isCompleted ? "bg-navy" : "bg-slate-200"
                                    )} />
                                )}

                                <div className="flex flex-col items-center">
                                    {/* Node */}
                                    <div className={cn(
                                        "w-8 h-8 rounded-full flex items-center justify-center border-2 transition-transform duration-300",
                                        isCompleted ? "bg-navy border-navy text-white" :
                                            isCurrent ? "bg-white border-navy text-navy ring-4 ring-blue-50 scale-110 shadow-md" :
                                                "bg-white border-slate-200 text-slate-400"
                                    )}>
                                        {isCompleted ? <CheckCircle2 className="w-5 h-5" /> :
                                            isCurrent ? <div className="w-3 h-3 bg-navy rounded-full animate-pulse" /> :
                                                <span className="text-xs font-medium">{idx + 1}</span>}
                                    </div>

                                    {/* Label */}
                                    <div className={cn(
                                        "mt-3 text-xs font-medium text-center",
                                        isCurrent ? "text-navy font-bold" :
                                            isCompleted ? "text-text-primary" : "text-text-tertiary"
                                    )}>
                                        {state.label}
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Actions Panel */}
            <div className="bg-surface rounded-2xl border border-border shadow-sm p-6">
                <div className="flex flex-col md:flex-row md:items-start gap-8">

                    <div className="flex-1">
                        <h4 className="text-sm font-semibold text-text-secondary mb-4 flex items-center gap-2">
                            <span className="text-lg">⚡</span> Acciones Pipeline
                        </h4>
                        <div className="flex flex-wrap gap-3">
                            {available_actions.length > 0 ? (
                                available_actions.map(cmd => (
                                    <button
                                        key={cmd}
                                        onClick={() => handleAction(cmd)}
                                        className="bg-navy hover:bg-slate-800 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all shadow-sm active:scale-95"
                                    >
                                        {COMMAND_LABELS[cmd] || cmd}
                                    </button>
                                ))
                            ) : (
                                <div className="text-sm text-text-tertiary flex items-center gap-2">
                                    <ShieldAlert className="w-4 h-4" />
                                    {expediente.is_blocked
                                        ? "Expediente bloqueado. Desbloquear para continuar."
                                        : "No hay acciones disponibles en el estado actual."}
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="hidden md:block w-px bg-border self-stretch" />

                    <div className="flex-1">
                        <h4 className="text-sm font-semibold text-text-secondary mb-4 flex items-center gap-2">
                            <span className="text-lg">🔧</span> Acciones Ops / Admin
                        </h4>
                        <div className="flex flex-wrap gap-3">
                            {expediente.is_blocked ? (
                                <button
                                    onClick={() => toast('Función de desbloqueo pendiente')}
                                    className="bg-red-50 hover:bg-red-100 text-red-700 border border-red-200 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                                >
                                    <Ban className="w-4 h-4 inline-block mr-1.5 -mt-0.5" />
                                    Desbloquear Manual
                                </button>
                            ) : (
                                <button
                                    onClick={() => toast('Función de bloqueo manual pendiente')}
                                    className="bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                                >
                                    <Ban className="w-4 h-4 inline-block mr-1.5 -mt-0.5" />
                                    Bloquear Manual
                                </button>
                            )}
                            <button
                                onClick={() => toast('Registro de costo pendiente')}
                                className="bg-white hover:bg-slate-50 text-navy border border-slate-200 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                            >
                                💰 Registrar Costo
                            </button>
                        </div>
                    </div>

                </div>
            </div>

            {/* Details Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

                {/* Info */}
                <div className="bg-surface rounded-2xl border border-border shadow-sm overflow-hidden flex flex-col">
                    <div className="px-6 py-4 border-b border-border bg-slate-50/50 flex items-center justify-between">
                        <h4 className="text-sm font-semibold text-text-primary">📋 Datos del expediente</h4>
                    </div>
                    <div className="p-6 grid grid-cols-2 gap-y-6 gap-x-4">
                        <div>
                            <div className="text-xs text-text-tertiary uppercase tracking-wider font-semibold mb-1">Cliente</div>
                            <div className="text-sm font-medium text-text-primary">{expediente.client}</div>
                        </div>
                        <div>
                            <div className="text-xs text-text-tertiary uppercase tracking-wider font-semibold mb-1">Marca</div>
                            <div className="text-sm font-medium text-text-primary">{expediente.brand || '—'}</div>
                        </div>
                        <div>
                            <div className="text-xs text-text-tertiary uppercase tracking-wider font-semibold mb-1">Entidad</div>
                            <div className="text-sm font-medium text-text-primary">{expediente.legal_entity_name || '—'}</div>
                        </div>
                        <div>
                            <div className="text-xs text-text-tertiary uppercase tracking-wider font-semibold mb-1">Creado</div>
                            <div className="text-sm font-medium text-text-primary">
                                {format(parseISO(expediente.created_at), 'dd MMM yyyy', { locale: es })}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Artifacts */}
                <div className="bg-surface rounded-2xl border border-border shadow-sm overflow-hidden flex flex-col">
                    <div className="px-6 py-4 border-b border-border bg-slate-50/50 flex items-center justify-between">
                        <h4 className="text-sm font-semibold text-text-primary">📎 Artefactos</h4>
                        <span className="bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full text-xs font-bold font-mono">
                            {artifacts.length}
                        </span>
                    </div>
                    <div className="flex-1 overflow-auto max-h-[300px]">
                        {artifacts.length > 0 ? (
                            <table className="w-full text-sm text-left">
                                <thead className="bg-slate-50 sticky top-0 border-b border-border text-xs text-text-tertiary uppercase font-semibold">
                                    <tr>
                                        <th className="px-6 py-3 font-medium">Tipo</th>
                                        <th className="px-6 py-3 font-medium">Estado</th>
                                        <th className="px-6 py-3 font-medium text-right">Fecha</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-border">
                                    {artifacts.map((art) => (
                                        <tr key={art.artifact_id} className="hover:bg-slate-50/50 transition-colors">
                                            <td className="px-6 py-3 font-medium text-text-secondary">
                                                {art.artifact_type}
                                            </td>
                                            <td className="px-6 py-3">
                                                <span className={cn(
                                                    "px-2 py-0.5 text-xs font-semibold rounded-full border shadow-[inset_0_1px_1px_rgba(255,255,255,0.5)]",
                                                    art.status === 'COMPLETED' ? "bg-emerald-50 text-mint border-emerald-200" :
                                                        art.status === 'SUPERSEDED' ? "bg-slate-100 text-slate-500 border-slate-200" :
                                                            "bg-red-50 text-coral border-red-200"
                                                )}>
                                                    {art.status_display}
                                                </span>
                                            </td>
                                            <td className="px-6 py-3 text-right text-text-tertiary whitespace-nowrap text-xs">
                                                {formatDistanceToNow(parseISO(art.created_at), { addSuffix: true, locale: es })}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        ) : (
                            <div className="p-8 text-center text-text-tertiary text-sm flex flex-col items-center">
                                <FileText className="w-8 h-8 opacity-20 mb-2" />
                                No hay artefactos registrados
                            </div>
                        )}
                    </div>
                </div>

            </div>
        </div>
    );
}
