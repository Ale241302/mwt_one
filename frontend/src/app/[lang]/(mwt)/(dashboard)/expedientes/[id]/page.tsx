"use client";
/**
 * S10-03 — Detalle Expediente con acordeón de artefactos.
 * S19-12 — Barrido hex: todos los colores reemplazados por CSS vars.
 */
import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft, RefreshCw, AlertTriangle, Lock,
  Play, CheckCircle, Clock, XCircle, ArrowRight, Truck
} from "lucide-react";
import { cn } from "@/lib/utils";
import api from "@/lib/api";
import ExpedienteAccordion from "@/components/expediente/ExpedienteAccordion";
import GateMessage from "@/components/expediente/GateMessage";
import CostTable from "@/components/expediente/CostTable";
import ArtifactModal from "@/components/expediente/ArtifactModal";
import { CANONICAL_STATES, STATE_BADGE_CLASSES } from "@/constants/states";
import { CreditBar } from "@/components/ui/CreditBar";


interface ExpedienteBundle {
  expediente: {
    id: string;
    custom_ref: string;
    status: string;
    brand_name: string;
    client_name: string;
    mode: string;
    freight_mode: string;
    transport_mode: string;
    dispatch_mode: string;
    payment_status: string;
    is_blocked: boolean;
    block_reason: string;
    total_cost: number;
    artifact_count: number;
  };
  artifacts: Array<{
    id: string;
    artifact_type: string;
    status: "pending" | "completed" | "voided" | "superseded";
    created_at: string;
    payload: Record<string, unknown>;
  }>;
  events: Array<{
    id: string;
    event_type: string;
    occurred_at: string;
    emitted_by: string;
    payload: Record<string, unknown>;
  }>;
  costs: any[];
  payments: any[];
  documents: any[];
  available_actions: {
    primary: any[];
    secondary: any[];
    ops: any[];
  };
  credit_clock: {
    days: number;
    band: "MINT" | "AMBER" | "RED";
    started_at: string | null;
    is_ignored: boolean;
  };
}

// S19-12: reemplazados todos los hex por CSS vars del design system
const CREDIT_BAND_CLASSES = {
  MINT: "bg-[var(--success-bg)] text-[var(--success)] border-[var(--success)]",
  AMBER: "bg-[var(--warning-bg)] text-[var(--warning)] border-[var(--warning)]",
  RED: "bg-[var(--critical-bg)] text-[var(--critical)] border-[var(--critical)]",
};

const PHASE_REQUIREMENTS: Record<string, string[]> = {
  "REGISTRO": ["ART-01 (OC)", "ART-02 (Proforma)"],
  "PREPARACION": ["ART-03 (Decisión Modal)", "ART-07 (Cotización Flete)", "ART-08 (Aduana)"],
  "PRODUCCION": ["ART-04 (SAP)", "ART-19 (Materialización Logística)"],
  "DESPACHO": ["ART-05 (Confirmación Prod)", "ART-06 (Embarque)"],
  "TRANSITO": ["ART-10 (Factura Comisión)"],
  "EN_DESTINO": ["ART-09 (Factura MWT)", "Saldo Pagado (Finanzas)"],
  "CERRADO": [],
  "CANCELADO": []
};

const GATE_ACTIONS: Record<string, string> = {
  "REGISTRO": "Cerrar Registro",
  "PREPARACION": "C10",
  "PRODUCCION": "C6",
  "DESPACHO": "C11",
  "TRANSITO": "C12",
  "EN_DESTINO": "C14",
};

export default function ExpedienteDetailPage() {
  const params = useParams();
  const router = useRouter();
  const lang = (params?.lang as string) || "es";
  const id = params?.id as string;

  const [bundle, setBundle] = useState<ExpedienteBundle | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [activeModal, setActiveModal] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'internal' | 'client'>('internal');

  const fetchBundle = useCallback(async (quiet = false) => {
    if (!quiet) setLoading(true);
    else setRefreshing(true);
    setError(null);
    try {
      const res = await api.get(`/ui/expedientes/${id}/`);
      const data = res.data;
      if (data) {
        data.artifacts = Array.isArray(data.artifacts) ? data.artifacts : [];
        data.events = Array.isArray(data.events) ? data.events : [];
        data.costs = Array.isArray(data.costs) ? data.costs : [];
        data.payments = Array.isArray(data.payments) ? data.payments : [];
        data.documents = Array.isArray(data.documents) ? data.documents : [];
        if (data.available_actions) {
          data.available_actions.primary = Array.isArray(data.available_actions.primary) ? data.available_actions.primary : [];
          data.available_actions.secondary = Array.isArray(data.available_actions.secondary) ? data.available_actions.secondary : [];
          data.available_actions.ops = Array.isArray(data.available_actions.ops) ? data.available_actions.ops : [];
        } else {
          data.available_actions = { primary: [], secondary: [], ops: [] };
        }
      }
      setBundle(data);
    } catch (e: any) {
      setError(e.message ?? "Error al cargar expediente");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [id]);

  useEffect(() => { fetchBundle(); }, [fetchBundle]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="text-[var(--text-secondary)] text-sm">Cargando expediente…</div>
      </div>
    );
  }

  if (error || !bundle) {
    return (
      <div className="empty-state">
        <AlertTriangle size={40} />
        <p>{error ?? "Expediente no encontrado."}</p>
        <button className="btn btn-sm btn-secondary mt-2" onClick={() => router.back()}>Volver</button>
      </div>
    );
  }

  const { expediente } = bundle;
  const creditCls = CREDIT_BAND_CLASSES[bundle.credit_clock?.band ?? "MINT"];
  const currentState = expediente.status === "ABIERTO" ? "REGISTRO" : expediente.status;

  const calculateMissingRequirements = () => {
    if (currentState === "CERRADO" || currentState === "CANCELADO") return [];
    const reqs = PHASE_REQUIREMENTS[currentState] || [];
    const missing: string[] = [];
    reqs.forEach(reqName => {
      const artifactId = reqName.split(" ")[0];
      if (artifactId.startsWith("ART-")) {
        const hasCompletedArtifact = (bundle.artifacts || []).some(
          a => a.artifact_type === artifactId && a.status === "completed"
        );
        if (!hasCompletedArtifact) missing.push(reqName);
      } else if (reqName.includes("Saldo Pagado")) {
        if (expediente.payment_status !== "PAID") missing.push(reqName);
      }
    });
    return missing;
  };

  const hasAction = (actionId: string) => {
    const actions = bundle.available_actions;
    if (!actions) return false;
    return (
      actions.primary?.some((a: any) => a.id === actionId) ||
      actions.secondary?.some((a: any) => a.id === actionId) ||
      actions.ops?.some((a: any) => a.id === actionId)
    );
  };

  const missingReqs = calculateMissingRequirements();
  const gateCommand = GATE_ACTIONS[currentState];
  const canAdvance = !!(missingReqs.length === 0 && gateCommand && hasAction(gateCommand));
  const hasArt06 = bundle.artifacts.some(a => a.artifact_type === 'ART-06' && a.status === 'completed');
  const showC11B = currentState === 'DESPACHO' && hasArt06 && hasAction('C11B');

  return (
    <div className="space-y-6">
      {/* ─── Top bar ─── */}
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <Link href={`/${lang}/expedientes`} className="btn btn-sm btn-ghost p-2 mt-1">
            <ArrowLeft size={16} />
          </Link>
          <div>
            <div className="flex items-center gap-3 mb-1.5">
              <h1 className="page-title leading-none">Expediente <span className="font-mono text-[var(--interactive)]">{expediente.custom_ref}</span></h1>
              <span className={cn(
                "badge text-xs font-semibold px-2.5 py-0.5",
                STATE_BADGE_CLASSES[expediente.status] ?? "bg-[var(--bg)] text-[var(--text-secondary)]"
              )}>
                {expediente.status}
              </span>
              {expediente.status === 'CANCELADO' && (
                <span className="badge badge-critical flex items-center gap-1 text-[10px]"><XCircle size={10} /> CRÍTICO</span>
              )}
              {expediente.is_blocked && (
                <span className="badge badge-critical flex items-center gap-1 text-[10px]">
                  <Lock size={10} /> BLOQUEADO
                </span>
              )}
            </div>
            <p className="page-subtitle">{expediente.client_name || "Sin Cliente"} · {expediente.brand_name || "Sin Marca"}</p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Toggle Interna/Cliente */}
          <div className="flex items-center gap-1 p-1 rounded-lg bg-[var(--bg-alt)] border border-[var(--border)]">
            <button
              onClick={() => setViewMode('internal')}
              className={cn(
                "px-3 py-1 text-xs font-medium rounded transition-all",
                viewMode === 'internal'
                  ? "bg-[var(--surface)] shadow-sm text-[var(--interactive)]"
                  : "text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]"
              )}
            >
              Interna
            </button>
            <button
              onClick={() => setViewMode('client')}
              className={cn(
                "px-3 py-1 text-xs font-medium rounded transition-all",
                viewMode === 'client'
                  ? "bg-[var(--surface)] shadow-sm text-[var(--interactive)]"
                  : "text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]"
              )}
            >
              Cliente
            </button>
          </div>

          <div className="h-6 w-px bg-[var(--border)] mx-1" />

          {hasAction("C17") && !expediente.is_blocked && (
            <button className="btn btn-sm btn-danger-outline" onClick={() => setActiveModal("C17")}>
              <Lock size={14} /> Bloquear
            </button>
          )}
          {hasAction("C18") && expediente.is_blocked && (
            <button className="btn btn-sm" style={{ color: "var(--success)", borderColor: "var(--success)", background: "transparent", border: "1px solid" }} onClick={() => setActiveModal("C18")}>
              <Lock size={14} /> Desbloquear
            </button>
          )}
          <button className="btn btn-sm btn-secondary" onClick={() => setActiveModal("C15")}>Costos</button>
          <button className="btn btn-sm btn-secondary" onClick={() => setActiveModal("C21")}>Pagos</button>
          {hasAction("C16") && (
            <button className="btn btn-sm btn-danger-outline" onClick={() => setActiveModal("C16")}>Cancelar</button>
          )}
          <button
            className="btn btn-sm btn-ghost"
            onClick={() => fetchBundle(true)}
            disabled={refreshing}
            aria-label="Actualizar"
          >
            <RefreshCw size={15} className={cn(refreshing && "animate-spin")} />
          </button>
        </div>
      </div>

      {/* ─── Credit Indicator ─── */}
      {viewMode === 'internal' && (
        <div className="animate-in fade-in slide-in-from-top-2 duration-500">
          <CreditBar
            used={expediente.total_cost || 0}
            total={100000}
            currency="USD"
            className="shadow-sm"
          />
        </div>
      )}

      {/* ─── Metadata Row ─── */}
      <div className="card p-4 flex flex-wrap gap-x-8 gap-y-4 text-sm">
        <div><span className="text-[var(--text-tertiary)]">Modalidad:</span> <span className="font-medium text-[var(--interactive)] ml-1">{expediente.mode || "—"}</span></div>
        <div><span className="text-[var(--text-tertiary)]">Flete:</span> <span className="font-medium text-[var(--interactive)] ml-1">{expediente.freight_mode || "—"}</span></div>
        <div><span className="text-[var(--text-tertiary)]">Transporte:</span> <span className="font-medium text-[var(--interactive)] ml-1">{expediente.transport_mode || "—"}</span></div>
        <div><span className="text-[var(--text-tertiary)]">Despacho:</span> <span className="font-medium text-[var(--interactive)] ml-1">{expediente.dispatch_mode || "—"}</span></div>
      </div>

      {/* ─── Timeline ─── */}
      <div className="card p-5 overflow-x-auto hide-scrollbar">
        <div className="flex items-center min-w-max">
          {CANONICAL_STATES.map((state, idx) => {
            const isPast = CANONICAL_STATES.indexOf(state as any) < CANONICAL_STATES.indexOf(currentState as any);
            const isCurrent = state === currentState;
            return (
              <div key={state} className="flex items-center">
                <div className={cn(
                  "flex items-center justify-center h-8 px-4 rounded-full text-xs font-semibold whitespace-nowrap transition-colors",
                  isPast
                    ? "bg-[var(--success)] text-[var(--text-inverse)]"
                    : isCurrent
                    ? "bg-[var(--interactive)] text-[var(--text-inverse)] shadow-sm"
                    : "bg-[var(--bg)] text-[var(--text-tertiary)]"
                )}>
                  {state}
                </div>
                {idx < CANONICAL_STATES.length - 1 && (
                  <div className={cn(
                    "w-8 h-0.5 mx-2 rounded",
                    isPast ? "bg-[var(--success)]" : "bg-[var(--border)]"
                  )} />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* ─── KPI row ─── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card p-4">
          <p className="caption text-[var(--text-tertiary)] mb-1">Estado pago</p>
          <div className="flex items-center gap-2">
            <p className="heading-sm font-semibold">{expediente.payment_status ?? "—"}</p>
            {expediente.payment_status === "PAID" && <CheckCircle size={14} className="text-[var(--success)]" />}
          </div>
        </div>
        <div className="card p-4">
          <p className="caption text-[var(--text-tertiary)] mb-1">Artefactos</p>
          <p className="heading-sm font-semibold">{Array.isArray(bundle.artifacts) ? bundle.artifacts.length : 0}</p>
        </div>
        <div className="card p-4">
          <p className="caption text-[var(--text-tertiary)] mb-1">Costo Total</p>
          <p className="heading-sm font-semibold">${Number(expediente.total_cost || 0).toLocaleString()}</p>
        </div>
        <div className={cn("card p-4 border", creditCls)}>
          <p className="caption mb-1">Crédito ({bundle.credit_clock?.band || "MINT"})</p>
          <p className="heading-sm font-semibold">{bundle.credit_clock?.days ?? 0} días</p>
        </div>
      </div>

      {/* ─── Main content ─── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <GateMessage requiredToAdvance={missingReqs} currentState={currentState} />

          {canAdvance && (
            <button
              className="w-full btn btn-primary flex items-center justify-center gap-2 py-3 shadow-sm hover:shadow"
              onClick={() => setActiveModal(gateCommand)}
            >
              Avanzar a la siguiente fase <ArrowRight size={16} />
            </button>
          )}

          {showC11B && (
            <button
              className="w-full btn btn-secondary flex items-center justify-center gap-2 py-3 shadow-sm mt-4"
              style={{ color: "var(--info)", borderColor: "var(--info)" }}
              onClick={() => setActiveModal("C11B")}
            >
              <Truck size={18} /> Confirmar Salida (China)
            </button>
          )}

          <ExpedienteAccordion
            expedienteId={expediente.id}
            artifacts={(Array.isArray(bundle.artifacts) ? bundle.artifacts : []).map(a => ({
              artifact_id: a.id,
              artifact_type: a.artifact_type,
              status: a.status,
              created_at: a.created_at,
              payload: a.payload
            }))}
            availableActions={bundle.available_actions || { primary: [], secondary: [], ops: [] }}
            onRefresh={() => fetchBundle(true)}
            currentState={currentState}
          />

          <CostTable expedienteId={expediente.id} />
        </div>

        <div>
          <h2 className="heading-sm font-semibold mb-3 text-[var(--interactive)]">Historial de eventos</h2>
          <div className="card overflow-hidden h-[600px] flex flex-col">
            <div className="flex-1 overflow-y-auto min-h-0 relative">
              {(!Array.isArray(bundle.events) || bundle.events.length === 0) ? (
                <div className="p-6 text-center text-[var(--text-tertiary)] text-sm absolute inset-0 flex items-center justify-center">
                  Sin eventos aún.
                </div>
              ) : (
                <div className="divide-y divide-[var(--divider)]">
                  {bundle.events.map((ev) => (
                    <div key={ev.id} className="px-5 py-3.5 hover:bg-[var(--surface-hover)] transition-colors group">
                      <div className="flex flex-col gap-1.5">
                        <div className="flex items-center justify-between">
                          <span className="font-mono text-[10px] tracking-tight font-semibold text-[var(--interactive)] bg-[var(--brand-accent-soft)] px-1.5 py-0.5 rounded border border-[var(--border)]">
                            {ev.event_type}
                          </span>
                          <span className="text-[10px] text-[var(--text-tertiary)] whitespace-nowrap">
                            {ev.occurred_at
                              ? new Date(ev.occurred_at).toLocaleDateString("es-CO", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })
                              : "—"}
                          </span>
                        </div>
                        <p className="text-xs text-[var(--text-secondary)] truncate pr-2" title={ev.emitted_by}>
                          Ref: {ev.emitted_by}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {activeModal && (
        <ArtifactModal
          open={true}
          expedienteId={expediente.id}
          commandKey={activeModal}
          onClose={() => setActiveModal(null)}
          onSuccess={() => { setActiveModal(null); fetchBundle(true); }}
        />
      )}
    </div>
  );
}
