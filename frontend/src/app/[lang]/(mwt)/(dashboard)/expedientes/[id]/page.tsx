"use client";

import { useEffect, useState, useCallback, Component, ReactNode } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { formatDistanceToNow, parseISO } from 'date-fns';
import { es } from 'date-fns/locale';
import { cn } from '@/lib/utils';
import api from '@/lib/api';
import toast from 'react-hot-toast';
import {
    ArrowLeft, ShieldAlert, CheckCircle2, XCircle, FileText, Ban,
    DollarSign, CreditCard,
} from 'lucide-react';

// ── Modal / Drawer imports ────────────────────────────────
import ArtifactFormDrawer from '@/components/modals/ArtifactFormDrawer';
import BlockUnblockModal from '@/components/modals/BlockUnblockModal';
import CancelExpedienteModal from '@/components/modals/CancelExpedienteModal';
import InvoiceModal from '@/components/modals/InvoiceModal';
import RegisterCostDrawer from '@/components/modals/RegisterCostDrawer';
import RegisterPaymentDrawer from '@/components/modals/RegisterPaymentDrawer';
import SupersederModal from '@/components/modals/SupersederModal';
import VoidArtifactModal from '@/components/modals/VoidArtifactModal';

// ── Section components ────────────────────────────────────
import CostsSection from '@/components/expediente/CostsSection';
import DocumentMirrorPanel from '@/components/expediente/DocumentMirrorPanel';

// ✅ FIX: Error Boundary para capturar crashes de componentes hijo (404 → .reduce crash)
interface EBState { hasError: boolean }
class SectionErrorBoundary extends Component<{ children: ReactNode; fallback?: ReactNode }, EBState> {
    constructor(props: { children: ReactNode; fallback?: ReactNode }) {
        super(props);
        this.state = { hasError: false };
    }
    static getDerivedStateFromError() { return { hasError: true }; }
    componentDidCatch(error: Error) { console.warn('[SectionErrorBoundary] capturado:', error.message); }
    render() {
        if (this.state.hasError) {
            return this.props.fallback ?? (
                <div className="bg-slate-50 border border-slate-200 rounded-2xl p-6 text-sm text-text-tertiary flex items-center gap-2">
                    <FileText className="w-4 h-4 opacity-40" />
                    Sección no disponible (endpoint pendiente en backend)
                </div>
            );
        }
        return this.props.children;
    }
}

// ───────────────────────── interfaces ─────────────────────

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
    payload: Record<string, string | number | boolean | null | undefined>;
    supersedes: number | null;
    superseded_by: number | null;
    created_at: string;
    updated_at: string;
}

interface Expediente {
    id: string;
    custom_ref: string;
    brand: string;
    brand_name: string;
    client_name: string;
    client_id: string | null;
    legal_entity_id: string;
    status: string;
    is_blocked: boolean;
    block_reason: string;
    mode: string;
    freight_mode: string;
    transport_mode: string;
    dispatch_mode: string;
    payment_status: string;
    price_basis: string;
    credit_clock_started_at: string | null;
    credit_days_elapsed: number;
    credit_band: string;
    total_cost: number;
    artifact_count: number;
    last_event_at: string | null;
}

interface ExpedienteBundle {
    expediente: Expediente;
    events: EventLog[];
    artifacts: Artifact[];
    available_actions: string[];
}

// ───────────────────────── constants ──────────────────────

type ArtifactType = 'ART-01' | 'ART-02' | 'ART-05' | 'ART-06' | 'ART-07' | 'ART-08';

const ARTIFACT_LABELS: Record<string, string> = {
    'ART-01': 'Orden de Compra',
    'ART-02': 'Proforma',
    'ART-03': 'Decisión Modal',
    'ART-04': 'SAP Confirmado',
    'ART-05': 'Embarque',
    'ART-06': 'Cotización Flete',
    'ART-07': 'Despacho Aprobado',
    'ART-08': 'Despacho Aduanal',
    'ART-09': 'Factura MWT',
    'ART-10': 'BL Registrado',
    'ART-19': 'Logística',
};

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
    'C8': 'Cotización Flete',
    'C9': 'Despacho Aduanal',
    'C10': 'Aprobar Despacho',
    'C11': 'Confirmar Zarpe',
    'C12': 'Confirmar Arribo',
    'C13': 'Emitir Factura',
    'C14': 'Cerrar Expediente',
};

const CMD_TO_ARTIFACT: Partial<Record<string, ArtifactType>> = {
    'C2': 'ART-01',
    'C3': 'ART-02',
    'C7': 'ART-05',
    'C8': 'ART-06',
    'C9': 'ART-08',
    'C10': 'ART-07',
};

// Estados en los que se permite emitir factura
const INVOICE_ALLOWED_STATUSES = ['DESTINO', 'FACTURADO'];

// ─────────────── ArtifactPayloadCard (ART-06 / ART-08) ───

function ArtifactPayloadCard({ artifact }: { artifact: Artifact }) {
    const p = artifact.payload || {};
    const type = artifact.artifact_type;

    if (type === 'ART-06') {
        return (
            <div className="bg-blue-50/50 rounded-xl border border-blue-100 p-5 space-y-3">
                <div className="flex items-center justify-between">
                    <h5 className="text-sm font-bold text-navy flex items-center gap-2">
                        🚢 {ARTIFACT_LABELS['ART-06'] || 'ART-06'}
                    </h5>
                    <span className={cn(
                        "px-2 py-0.5 text-xs font-semibold rounded-full border",
                        artifact.status === 'COMPLETED' ? "bg-emerald-50 text-mint border-emerald-200" :
                            "bg-amber-50 text-amber-700 border-amber-200"
                    )}>
                        {artifact.status_display}
                    </span>
                </div>
                <div className="grid grid-cols-2 gap-3 text-sm">
                    {p.carrier && (
                        <div>
                            <div className="text-xs text-text-tertiary uppercase font-semibold mb-0.5">Naviera / Carrier</div>
                            <div className="font-medium text-text-primary">{String(p.carrier)}</div>
                        </div>
                    )}
                    {p.freight_cost !== undefined && (
                        <div>
                            <div className="text-xs text-text-tertiary uppercase font-semibold mb-0.5">Costo Flete</div>
                            <div className="font-medium text-text-primary">
                                ${Number(p.freight_cost).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                            </div>
                        </div>
                    )}
                    {p.transit_days !== undefined && (
                        <div>
                            <div className="text-xs text-text-tertiary uppercase font-semibold mb-0.5">Días Tránsito</div>
                            <div className="font-medium text-text-primary">{String(p.transit_days)} días</div>
                        </div>
                    )}
                    {p.eta && (
                        <div>
                            <div className="text-xs text-text-tertiary uppercase font-semibold mb-0.5">ETA</div>
                            <div className="font-medium text-text-primary">{String(p.eta)}</div>
                        </div>
                    )}
                    {p.origin_port && (
                        <div>
                            <div className="text-xs text-text-tertiary uppercase font-semibold mb-0.5">Puerto Origen</div>
                            <div className="font-medium text-text-primary">{String(p.origin_port)}</div>
                        </div>
                    )}
                    {p.destination_port && (
                        <div>
                            <div className="text-xs text-text-tertiary uppercase font-semibold mb-0.5">Puerto Destino</div>
                            <div className="font-medium text-text-primary">{String(p.destination_port)}</div>
                        </div>
                    )}
                    {p.container_type && (
                        <div>
                            <div className="text-xs text-text-tertiary uppercase font-semibold mb-0.5">Tipo Contenedor</div>
                            <div className="font-medium text-text-primary">{String(p.container_type)}</div>
                        </div>
                    )}
                    {p.incoterm && (
                        <div>
                            <div className="text-xs text-text-tertiary uppercase font-semibold mb-0.5">Incoterm</div>
                            <div className="font-medium text-text-primary">{String(p.incoterm)}</div>
                        </div>
                    )}
                </div>
                {p.file_url && (
                    <a href={String(p.file_url)} target="_blank" rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 text-xs text-navy hover:underline mt-1">
                        <FileText className="w-3.5 h-3.5" /> Ver documento
                    </a>
                )}
            </div>
        );
    }

    if (type === 'ART-08') {
        return (
            <div className="bg-emerald-50/50 rounded-xl border border-emerald-100 p-5 space-y-3">
                <div className="flex items-center justify-between">
                    <h5 className="text-sm font-bold text-emerald-800 flex items-center gap-2">
                        📋 {ARTIFACT_LABELS['ART-08'] || 'ART-08'}
                    </h5>
                    <span className={cn(
                        "px-2 py-0.5 text-xs font-semibold rounded-full border",
                        artifact.status === 'COMPLETED' ? "bg-emerald-50 text-mint border-emerald-200" :
                            "bg-amber-50 text-amber-700 border-amber-200"
                    )}>
                        {artifact.status_display}
                    </span>
                </div>
                <div className="grid grid-cols-2 gap-3 text-sm">
                    {p.customs_agent && (
                        <div>
                            <div className="text-xs text-text-tertiary uppercase font-semibold mb-0.5">Agente Aduanal</div>
                            <div className="font-medium text-text-primary">{String(p.customs_agent)}</div>
                        </div>
                    )}
                    {p.customs_cost !== undefined && (
                        <div>
                            <div className="text-xs text-text-tertiary uppercase font-semibold mb-0.5">Costo Aduana</div>
                            <div className="font-medium text-text-primary">
                                ${Number(p.customs_cost).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                            </div>
                        </div>
                    )}
                    {p.customs_declaration && (
                        <div>
                            <div className="text-xs text-text-tertiary uppercase font-semibold mb-0.5">Declaración</div>
                            <div className="font-medium text-text-primary">{String(p.customs_declaration)}</div>
                        </div>
                    )}
                    {p.tariff_code && (
                        <div>
                            <div className="text-xs text-text-tertiary uppercase font-semibold mb-0.5">Código Arancelario</div>
                            <div className="font-medium text-text-primary">{String(p.tariff_code)}</div>
                        </div>
                    )}
                    {p.tax_amount !== undefined && (
                        <div>
                            <div className="text-xs text-text-tertiary uppercase font-semibold mb-0.5">Impuestos</div>
                            <div className="font-medium text-text-primary">
                                ${Number(p.tax_amount).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                            </div>
                        </div>
                    )}
                    {p.dispatch_mode && (
                        <div>
                            <div className="text-xs text-text-tertiary uppercase font-semibold mb-0.5">Modo Despacho</div>
                            <div className="font-medium text-text-primary">{String(p.dispatch_mode).toUpperCase()}</div>
                        </div>
                    )}
                </div>
                {p.file_url && (
                    <a href={String(p.file_url)} target="_blank" rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 text-xs text-emerald-700 hover:underline mt-1">
                        <FileText className="w-3.5 h-3.5" /> Ver documento
                    </a>
                )}
            </div>
        );
    }

    return null;
}

// ═══════════════════════════ MAIN PAGE ════════════════════

export default function ExpedienteDetailPage() {
    const params = useParams();
    const id = params.id as string;
    const router = useRouter();
    const { user, loading: authLoading } = useAuth();

    // ── Core data ─────────────────────────────────────────
    const [bundle, setBundle] = useState<ExpedienteBundle | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // ── Modal / Drawer states ─────────────────────────────
    const [artifactDrawerOpen, setArtifactDrawerOpen] = useState(false);
    const [artifactDrawerType, setArtifactDrawerType] = useState<ArtifactType>('ART-01');

    const [blockModalOpen, setBlockModalOpen] = useState(false);
    const [cancelModalOpen, setCancelModalOpen] = useState(false);
    const [invoiceModalOpen, setInvoiceModalOpen] = useState(false);
    const [costDrawerOpen, setCostDrawerOpen] = useState(false);
    const [paymentDrawerOpen, setPaymentDrawerOpen] = useState(false);
    const [voidModalOpen, setVoidModalOpen] = useState(false);

    const [supersederOpen, setSupersederOpen] = useState(false);
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const [supersederArtifact, _setSupersederArtifact] = useState<{ id: string; type: string }>({ id: '', type: '' });

    // ── Fetch ─────────────────────────────────────────────
    const fetchBundle = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            const { data } = await api.get(`ui/expedientes/${id}/`);
            setBundle(data);
        } catch (err: unknown) {
            console.error('Error fetching expediente bundle:', err);
            const e = err as { response?: { data?: { detail?: string } }, message?: string };
            setError(e.response?.data?.detail || 'Error al cargar expediente');
        } finally {
            setLoading(false);
        }
    }, [id]);

    useEffect(() => {
        if (!authLoading && user) {
            fetchBundle();
        }
    }, [user, authLoading, fetchBundle]);

    // ── Handlers ──────────────────────────────────────────

    const openArtifactDrawer = (type: ArtifactType) => {
        setArtifactDrawerType(type);
        setArtifactDrawerOpen(true);
    };

    const handleAction = async (cmd: string) => {
        const drawerType = CMD_TO_ARTIFACT[cmd];
        if (drawerType) {
            openArtifactDrawer(drawerType);
            return;
        }

        if (cmd === 'C13') {
            setInvoiceModalOpen(true);
            return;
        }

        try {
            let endpoint = '';
            const payload = {};

            switch (cmd) {
                case 'C6': endpoint = `expedientes/${id}/confirm-production/`; break;
                case 'C11': endpoint = `expedientes/${id}/confirm-departure/`; break;
                case 'C12': endpoint = `expedientes/${id}/confirm-arrival/`; break;
                case 'C14': endpoint = `expedientes/${id}/close/`; break;
                default:
                    toast('Acción requiere payload. No implementada en UI aún.', { icon: '🚧' });
                    return;
            }

            toast.success(`Ejecutando ${COMMAND_LABELS[cmd] || cmd}...`);
            await api.post(endpoint, payload);
            toast.success('Comando ejecutado con éxito');
            fetchBundle();
        } catch (err: unknown) {
            const e = err as { response?: { data?: { detail?: string } }, message?: string };
            toast.error('Error al ejecutar: ' + (e.response?.data?.detail || e.message));
        }
    };

    // ── Loading / Error states ────────────────────────────

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

    const currentStateIndex = TIMELINE_STATES.findIndex(s => s.id === expediente.status);

    const enrichedArtTypes = new Set(['ART-06', 'ART-08']);
    const enrichedArtifacts = artifacts.filter(a => enrichedArtTypes.has(a.artifact_type) && a.status !== 'SUPERSEDED');

    const hasInvoice = artifacts.some(a => a.artifact_type === 'ART-09' && a.status === 'COMPLETED');
    // ✅ FIX: Solo mostrar "Emitir Factura" si el estado lo permite
    const canIssueInvoice = INVOICE_ALLOWED_STATUSES.includes(expediente.status);

    return (
        <div className="max-w-6xl mx-auto space-y-6">

            <button
                onClick={() => router.back()}
                className="text-sm text-text-secondary hover:text-navy flex items-center transition-colors"
            >
                <ArrowLeft className="w-4 h-4 mr-1" />
                Volver a expedientes
            </button>

            {/* ───────── Header ───────── */}
            <div className="flex items-center gap-4 flex-wrap">
                <h1 className="text-3xl font-display font-medium text-text-primary tracking-tight">
                    {expediente.custom_ref || `EXP-${expediente.id?.toString().slice(0, 8)}`}
                </h1>
                <div className="flex gap-2 items-center">
                    <span className={cn(
                        "px-2.5 py-1 text-xs font-semibold rounded-full border shadow-sm",
                        expediente.status === 'REGISTRO' ? "bg-slate-100 text-slate-700 border-slate-200" :
                            expediente.status === 'CERRADO' ? "bg-emerald-50 text-emerald-700 border-emerald-200" :
                                "bg-blue-50 text-navy border-blue-200"
                    )}>
                        {expediente.status}
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

            {/* ───────── Timeline ───────── */}
            <div className="bg-surface rounded-2xl border border-border shadow-sm p-6 overflow-x-auto">
                <h4 className="text-sm font-semibold text-text-secondary mb-6 uppercase tracking-wider">Timeline</h4>
                <div className="flex items-center justify-between min-w-[700px]">
                    {TIMELINE_STATES.map((state, idx) => {
                        const isCompleted = idx < currentStateIndex;
                        const isCurrent = idx === currentStateIndex;
                        return (
                            <div key={state.id} className="relative flex-1 group">
                                {idx < TIMELINE_STATES.length - 1 && (
                                    <div className={cn(
                                        "absolute top-4 left-1/2 w-full h-[2px] -z-10",
                                        isCompleted ? "bg-navy" : "bg-slate-200"
                                    )} />
                                )}

                                <div className="flex flex-col items-center">
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

            {/* ───────── Actions Panel ───────── */}
            <div className="bg-surface rounded-2xl border border-border shadow-sm p-6">
                <div className="flex flex-col md:flex-row md:items-start gap-8">

                    {/* Pipeline actions */}
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

                    {/* Ops / Admin actions */}
                    <div className="flex-1">
                        <h4 className="text-sm font-semibold text-text-secondary mb-4 flex items-center gap-2">
                            <span className="text-lg">🔧</span> Acciones Ops / Admin
                        </h4>
                        <div className="flex flex-wrap gap-3">
                            <button
                                onClick={() => setBlockModalOpen(true)}
                                className={cn(
                                    "px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5",
                                    expediente.is_blocked
                                        ? "bg-red-50 hover:bg-red-100 text-red-700 border border-red-200"
                                        : "bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200"
                                )}
                            >
                                <Ban className="w-4 h-4" />
                                {expediente.is_blocked ? 'Desbloquear Manual' : 'Bloquear Manual'}
                            </button>

                            <button
                                onClick={() => setCostDrawerOpen(true)}
                                className="bg-white hover:bg-slate-50 text-navy border border-slate-200 px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5"
                            >
                                <DollarSign className="w-4 h-4" />
                                Registrar Costo
                            </button>

                            <button
                                onClick={() => setPaymentDrawerOpen(true)}
                                className="bg-white hover:bg-slate-50 text-navy border border-slate-200 px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5"
                            >
                                <CreditCard className="w-4 h-4" />
                                Registrar Pago
                            </button>

                            <button
                                onClick={() => setCancelModalOpen(true)}
                                className="bg-white hover:bg-red-50 text-red-600 border border-red-200 px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5"
                            >
                                <XCircle className="w-4 h-4" />
                                Cancelar Expediente
                            </button>

                            {/* ✅ FIX: Emitir Factura solo visible si status lo permite y no hay factura activa */}
                            {!hasInvoice && canIssueInvoice && (
                                <button
                                    onClick={() => setInvoiceModalOpen(true)}
                                    className="bg-white hover:bg-slate-50 text-navy border border-slate-200 px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5"
                                >
                                    <FileText className="w-4 h-4" />
                                    Emitir Factura
                                </button>
                            )}

                            {/* Anular Factura solo si ya existe una factura activa */}
                            {hasInvoice && (
                                <button
                                    onClick={() => setVoidModalOpen(true)}
                                    className="bg-white hover:bg-red-50 text-red-600 border border-red-200 px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5"
                                >
                                    <FileText className="w-4 h-4" />
                                    Anular Factura
                                </button>
                            )}
                        </div>
                    </div>

                </div>
            </div>

            {/* ───────── Details Grid ───────── */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

                {/* Info */}
                <div className="bg-surface rounded-2xl border border-border shadow-sm overflow-hidden flex flex-col">
                    <div className="px-6 py-4 border-b border-border bg-slate-50/50 flex items-center justify-between">
                        <h4 className="text-sm font-semibold text-text-primary">📋 Datos del expediente</h4>
                    </div>
                    <div className="p-6 grid grid-cols-2 gap-y-6 gap-x-4">
                        <div>
                            <div className="text-xs text-text-tertiary uppercase tracking-wider font-semibold mb-1">Cliente</div>
                            <div className="text-sm font-medium text-text-primary">{expediente.client_name || '—'}</div>
                        </div>
                        <div>
                            <div className="text-xs text-text-tertiary uppercase tracking-wider font-semibold mb-1">Marca</div>
                            <div className="text-sm font-medium text-text-primary">{expediente.brand || '—'}</div>
                        </div>
                        <div>
                            <div className="text-xs text-text-tertiary uppercase tracking-wider font-semibold mb-1">Entidad</div>
                            <div className="text-sm font-medium text-text-primary">{expediente.legal_entity_id || '—'}</div>
                        </div>
                        <div>
                            <div className="text-xs text-text-tertiary uppercase tracking-wider font-semibold mb-1">Modo</div>
                            <div className="text-sm font-medium text-text-primary">
                                {expediente.mode || '—'}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Artifacts Table */}
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
                                                {ARTIFACT_LABELS[art.artifact_type] || art.artifact_type}
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

            {/* ───────── Enriched Artifact Cards (ART-06, ART-08) ───────── */}
            {enrichedArtifacts.length > 0 && (
                <div className="space-y-4">
                    <h4 className="text-sm font-semibold text-text-secondary uppercase tracking-wider flex items-center gap-2">
                        📦 Detalle de Artefactos Clave
                    </h4>
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                        {enrichedArtifacts.map(art => (
                            <ArtifactPayloadCard key={art.artifact_id} artifact={art} />
                        ))}
                    </div>
                </div>
            )}

            {/* ───────── Costs Section ───────── */}
            <SectionErrorBoundary>
                <CostsSection
                    expedienteId={id}
                    onRegisterCost={() => setCostDrawerOpen(true)}
                />
            </SectionErrorBoundary>

            {/* ───────── Documents Mirror Panel ───────── */}
            <SectionErrorBoundary>
                <DocumentMirrorPanel expedienteId={id} />
            </SectionErrorBoundary>

            {/* ═══════════ Modals / Drawers ═══════════ */}

            <ArtifactFormDrawer
                open={artifactDrawerOpen}
                onClose={() => setArtifactDrawerOpen(false)}
                expedienteId={id}
                artifactType={artifactDrawerType}
                expedienteMode={expediente.mode}
                freightMode={expediente.freight_mode}
                dispatchMode={expediente.dispatch_mode}
                artifacts={artifacts}
                onSuccess={fetchBundle}
            />

            <BlockUnblockModal
                open={blockModalOpen}
                onClose={() => setBlockModalOpen(false)}
                expedienteId={id}
                isBlocked={expediente.is_blocked}
                blockReason={expediente.block_reason}
                onSuccess={fetchBundle}
            />

            <CancelExpedienteModal
                open={cancelModalOpen}
                onClose={() => setCancelModalOpen(false)}
                expedienteId={id}
                currentStatus={expediente.status}
                onSuccess={fetchBundle}
            />

            <InvoiceModal
                open={invoiceModalOpen}
                onClose={() => setInvoiceModalOpen(false)}
                expedienteId={id}
                clientName={expediente.client_name}
                expedienteMode={expediente.mode}
                dispatchMode={expediente.dispatch_mode}
                artifacts={artifacts}
                onSuccess={fetchBundle}
            />

            <RegisterCostDrawer
                open={costDrawerOpen}
                onClose={() => setCostDrawerOpen(false)}
                expedienteId={id}
                onSuccess={fetchBundle}
            />

            <RegisterPaymentDrawer
                open={paymentDrawerOpen}
                onClose={() => setPaymentDrawerOpen(false)}
                expedienteId={id}
                onSuccess={fetchBundle}
            />

            <SupersederModal
                open={supersederOpen}
                onClose={() => setSupersederOpen(false)}
                expedienteId={id}
                artifactId={supersederArtifact.id}
                artifactType={supersederArtifact.type}
                onSuccess={fetchBundle}
            />

            <VoidArtifactModal
                open={voidModalOpen}
                onClose={() => setVoidModalOpen(false)}
                expedienteId={id}
                onSuccess={fetchBundle}
            />

        </div>
    );
}
