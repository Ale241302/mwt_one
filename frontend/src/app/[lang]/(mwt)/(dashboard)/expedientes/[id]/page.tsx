"use client";
/**
 * S10-03 — Detalle Expediente con acordeón de artefactos.
 * Refactor del bundle view para cumplir la fase 1 de Sprint 10.
 */
import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft, RefreshCw, AlertTriangle, Lock,
  Play, CheckCircle, Clock, XCircle, ArrowRight
} from "lucide-react";
import { cn } from "@/lib/utils";
import api from "@/lib/api";
import ExpedienteAccordion from "@/components/expediente/ExpedienteAccordion";
import GateMessage from "@/components/expediente/GateMessage";
import CostTable from "@/components/expediente/CostTable";
import ArtifactModal from "@/components/expediente/ArtifactModal";

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
  available_actions: string[];
  credit_clock: {
    days: number;
    band: "MINT" | "AMBER" | "RED";
    started_at: string | null;
    is_ignored: boolean;
  };
}

const STATE_BADGE_CLASSES: Record<string, string> = {
  REGISTRO: "bg-[#EFF6FF] text-[#1D4ED8]",
  PREPARACION: "bg-[#FEF3C7] text-[#D97706]",
  PRODUCCION: "bg-[#FEF3C7] text-[#D97706]",
  DESPACHO: "bg-[#FEF3C7] text-[#D97706]",
  TRANSITO: "bg-[#FEF3C7] text-[#D97706]",
  EN_DESTINO: "bg-[#FEF3C7] text-[#D97706]",
  CERRADO: "bg-[#F0FAF6] text-[#0E8A6D]",
  CANCELADO: "bg-[#FEF2F2] text-[#DC2626]",
  BLOQUEADO: "bg-[#F1F5F9] text-[#475569]",
};

const CREDIT_BAND_COLORS = {
  MINT: "bg-[#F0FAF6] text-[#0E8A6D] border-[#BBF7D0]",
  AMBER: "bg-[#FFF7ED] text-[#B45309] border-[#FDE68A]",
  RED: "bg-[#FEF2F2] text-[#DC2626] border-[#FECACA]",
};

const CANONICAL_STATES = [
  "REGISTRO", "PREPARACION", "PRODUCCION", 
  "DESPACHO", "TRANSITO", "EN_DESTINO", "CERRADO"
];

// Requisitos para avanzar de cada fase según canonical workflow
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

// Acciones de transición (Gate actions)
const GATE_ACTIONS: Record<string, string> = {
  "REGISTRO": "Cerrar Registro", // CERRAR REGISTRO doesn't physically exist as command, usually auto or manual C4
  "PREPARACION": "C10", // ApproveDispatch
  "PRODUCCION": "C6", // ConfirmProduction
  "DESPACHO": "C11", // ConfirmDeparture
  "TRANSITO": "C12", // ConfirmArrival
  "EN_DESTINO": "C14", // CloseExpediente
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

  const fetchBundle = useCallback(async (quiet = false) => {
    if (!quiet) setLoading(true);
    else setRefreshing(true);
    setError(null);
    try {
      const res = await api.get(`/ui/expedientes/${id}/`);
      setBundle(res.data);
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
        <div className="text-text-secondary text-sm">Cargando expediente…</div>
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
  const creditCls = CREDIT_BAND_COLORS[bundle.credit_clock?.band ?? "MINT"];
  const currentState = expediente.status === "ABIERTO" ? "REGISTRO" : expediente.status;

  // Calculamos los requerimientos faltantes para el GateMessage
  const calculateMissingRequirements = () => {
    if (currentState === "CERRADO" || currentState === "CANCELADO") return [];
    
    // We mock missing requirements logic based on completed artifacts
    const reqs = PHASE_REQUIREMENTS[currentState] || [];
    const missing: string[] = [];
    
    reqs.forEach(reqName => {
      const artifactId = reqName.split(" ")[0]; // ej: "ART-01"
      if (artifactId.startsWith("ART-")) {
        const hasCompletedArtifact = bundle.artifacts.some(
          a => a.artifact_type === artifactId && a.status === "completed"
        );
        if (!hasCompletedArtifact) missing.push(reqName);
      } else if (reqName.includes("Saldo Pagado")) {
        if (expediente.payment_status !== "PAID") missing.push(reqName);
      }
    });
    
    return missing;
  };

  const missingReqs = calculateMissingRequirements();
  const gateCommand = GATE_ACTIONS[currentState];
  const canAdvance = missingReqs.length === 0 && gateCommand && bundle.available_actions.includes(gateCommand);

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
              <h1 className="page-title leading-none">Expediente <span className="font-mono text-navy">{expediente.custom_ref}</span></h1>
              <span className={cn(
                "badge text-xs font-semibold px-2.5 py-0.5",
                STATE_BADGE_CLASSES[expediente.status] ?? "bg-bg text-text-secondary"
              )}>
                {expediente.status}
              </span>
              {expediente.status === 'CANCELADO' && (
                <span className="badge badge-error flex items-center gap-1 text-[10px]"><XCircle size={10} /> CRÍTICO</span>
              )}
              {expediente.is_blocked && (
                <span className="badge bg-[#FEF2F2] text-[#DC2626] flex items-center gap-1 text-[10px]">
                  <Lock size={10} /> BLOQUEADO
                </span>
              )}
            </div>
            <p className="page-subtitle">{expediente.client_name || "Sin Cliente"} · {expediente.brand_name || "Sin Marca"}</p>
          </div>
        </div>
        
        <div className="flex flex-wrap items-center gap-2">
          {bundle.available_actions.includes("C17") && !expediente.is_blocked && (
             <button className="btn btn-sm btn-outline text-coral border-coral/30 hover:bg-coral/5" onClick={() => setActiveModal("C17")}><Lock size={14}/> Bloquear</button>
          )}
          {bundle.available_actions.includes("C18") && expediente.is_blocked && (
             <button className="btn btn-sm btn-outline text-success border-success/30 hover:bg-success/5" onClick={() => setActiveModal("C18")}><Lock size={14}/> Desbloquear</button>
          )}
          {/* Default actions */}
          <button className="btn btn-sm btn-secondary" onClick={() => setActiveModal("C15")}>Costos</button>
          <button className="btn btn-sm btn-secondary" onClick={() => setActiveModal("C21")}>Pagos</button>
          {bundle.available_actions.includes("C16") && (
             <button className="btn btn-sm btn-outline text-coral" onClick={() => setActiveModal("C16")}>Cancelar</button>
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

      {/* ─── Metadata Row ─── */}
      <div className="card p-4 flex flex-wrap gap-x-8 gap-y-4 text-sm bg-white border border-border">
        <div><span className="text-text-tertiary">Modalidad:</span> <span className="font-medium text-navy ml-1">{expediente.mode || "—"}</span></div>
        <div><span className="text-text-tertiary">Flete:</span> <span className="font-medium text-navy ml-1">{expediente.freight_mode || "—"}</span></div>
        <div><span className="text-text-tertiary">Transporte:</span> <span className="font-medium text-navy ml-1">{expediente.transport_mode || "—"}</span></div>
        <div><span className="text-text-tertiary">Despacho:</span> <span className="font-medium text-navy ml-1">{expediente.dispatch_mode || "—"}</span></div>
      </div>

      {/* ─── Timeline ─── */}
      <div className="card p-5 overflow-x-auto hide-scrollbar">
        <div className="flex items-center min-w-max">
          {CANONICAL_STATES.map((state, idx) => {
            const isPast = CANONICAL_STATES.indexOf(state) < CANONICAL_STATES.indexOf(currentState);
            const isCurrent = state === currentState;
            return (
              <div key={state} className="flex items-center">
                <div className={cn(
                  "flex items-center justify-center h-8 px-4 rounded-full text-xs font-semibold whitespace-nowrap transition-colors",
                  isPast ? "bg-success text-white" : 
                  isCurrent ? "bg-brand text-white shadow-sm" : 
                  "bg-bg text-text-tertiary"
                )}>
                  {state}
                </div>
                {idx < CANONICAL_STATES.length - 1 && (
                  <div className={cn(
                    "w-8 h-0.5 mx-2 rounded",
                    isPast ? "bg-success/50" : "bg-border"
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
          <p className="caption text-text-tertiary mb-1">Estado pago</p>
          <div className="flex items-center gap-2">
            <p className="heading-sm font-semibold">{expediente.payment_status ?? "—"}</p>
            {expediente.payment_status === "PAID" && <CheckCircle size={14} className="text-success" />}
          </div>
        </div>
        <div className="card p-4">
          <p className="caption text-text-tertiary mb-1">Artefactos</p>
          <p className="heading-sm font-semibold">{bundle.artifacts.length}</p>
        </div>
        <div className="card p-4">
          <p className="caption text-text-tertiary mb-1">Costo Total</p>
          <p className="heading-sm font-semibold">${Number(expediente.total_cost || 0).toLocaleString()}</p>
        </div>
        <div className={cn("card p-4 border", creditCls)}>
          <p className="caption mb-1">Crédito ({bundle.credit_clock?.band || "MINT"})</p>
          <p className="heading-sm font-semibold">{bundle.credit_clock?.days ?? 0} días</p>
        </div>
      </div>

      {/* ─── Main content: Gate Message + Accordion + Events + Costs ─── */}
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
          
          <ExpedienteAccordion
            expedienteId={expediente.id}
            artifacts={bundle.artifacts.map(a => ({
              artifact_id: a.id,
              artifact_type: a.artifact_type,
              status: a.status,
              created_at: a.created_at,
              payload: a.payload
            }))}
            availableActions={bundle.available_actions}
            onRefresh={() => fetchBundle(true)}
            currentState={currentState}
          />

          <CostTable expedienteId={expediente.id} />
        </div>

        <div>
          <h2 className="heading-sm font-semibold mb-3 text-navy">Historial de eventos</h2>
          <div className="card overflow-hidden h-[600px] flex flex-col">
            <div className="flex-1 overflow-y-auto min-h-0 relative">
            {bundle.events.length === 0 ? (
              <div className="p-6 text-center text-text-tertiary text-sm absolute inset-0 flex items-center justify-center">Sin eventos aún.</div>
            ) : (
              <div className="divide-y divide-divider">
                {bundle.events.map((ev) => (
                  <div key={ev.id} className="px-5 py-3.5 hover:bg-bg/50 transition-colors group">
                    <div className="flex flex-col gap-1.5">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-[10px] tracking-tight font-semibold text-navy bg-brand-accent-soft px-1.5 py-0.5 rounded border border-brand/10">
                          {ev.event_type}
                        </span>
                        <span className="text-[10px] text-text-tertiary whitespace-nowrap">
                           {ev.occurred_at ? new Date(ev.occurred_at).toLocaleDateString("es-CO", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }) : "—"}
                        </span>
                      </div>
                      <p className="text-xs text-text-secondary truncate pr-2" title={ev.emitted_by}>
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
