"use client";
/**
 * S10-03 — Detalle Expediente con acordeón de artefactos.
 * S19-12 — Barrido hex: todos los colores reemplazados por CSS vars.
 * S21    — isAdmin desde bundle.is_admin (is_superuser Django) → panel admin.
 * fix    — guard expedienteId en ArtifactModal; botones Costos/Pagos sin disabled.
 * FIX-2026-04-08 — expedienteId con triple fallback: expediente.id ?? expediente.expediente_id ?? params.id
 *                  El backend expone 'expediente_id' pero page.tsx buscaba 'id'.
 *                  Ahora serializers_ui.py también agrega 'id' como alias (fix backend).
 */
import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft, RefreshCw, AlertTriangle, Lock,
  Play, CheckCircle, Clock, XCircle, ArrowRight, Truck,
  ChevronDown, ChevronRight, Package, Info
} from "lucide-react";
import { cn } from "@/lib/utils";
import api from "@/lib/api";
import ExpedienteAccordion from "@/components/expediente/ExpedienteAccordion";
import GateMessage from "@/components/expediente/GateMessage";
import CostTable from "@/components/expediente/CostTable";
import ArtifactModal from "@/components/expediente/ArtifactModal";
import ProformaSection from "@/components/expediente/ProformaSection";
import ReassignLineModal from "@/components/expediente/ReassignLineModal";
import { CANONICAL_STATES, STATE_BADGE_CLASSES } from "@/constants/states";
import { CreditBar } from "@/components/ui/CreditBar";
import { EXPEDIENTE_LEVEL_ARTIFACTS } from "@/constants/proforma-artifact-policy";
import { ARTIFACT_UI_REGISTRY } from "@/constants/artifact-ui-registry";
import { MODE_LABELS } from "@/constants/mode-labels";
import CreateProformaModal from "@/components/expediente/CreateProformaModal";


interface ExpedienteBundle {
  expediente: {
    /** Alias de expediente_id — expuesto desde serializers_ui.py FIX-2026-04-08 */
    id: string;
    /** UUID raw del expediente — campo canónico del modelo Django */
    expediente_id?: string;
    custom_ref: string;
    status: string;
    brand_name: string;
    brand_slug: string;
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
    artifact_id?: string;
    artifact_type: string;
    status: "pending" | "completed" | "voided" | "superseded";
    created_at: string;
    payload: Record<string, any>;
    parent_proforma_id?: string | null;
  }>;
  events: Array<any>;
  product_lines: Array<{
    id: string;
    product_name: string;
    size: string;
    quantity: number;
    unit_price: number;
    total_price: number;
    proforma_id: string | null;
  }>;
  artifact_policy: Record<string, {
    required: string[];
    optional: string[];
    gate_for_advance: string[];
  }>;
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
  costs: any[];
  payments: any[];
  documents: any[];
  /** Viene del backend: True si el usuario autenticado es is_superuser */
  is_admin?: boolean;
}

const CREDIT_BAND_CLASSES = {
  MINT: "bg-[var(--success-bg)] text-[var(--success)] border-[var(--success)]",
  AMBER: "bg-[var(--warning-bg)] text-[var(--warning)] border-[var(--warning)]",
  RED: "bg-[var(--critical-bg)] text-[var(--critical)] border-[var(--critical)]",
};

const STATE_TO_ADVANCE_COMMAND: Record<string, string> = {
  'REGISTRO': 'C5',
  'PRODUCCION': 'C11B',
  'PREPARACION': 'C10',
  'DESPACHO': 'C11',
  'TRANSITO': 'C12',
  'EN_DESTINO': 'C14',
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
  const [activeModal, setActiveModal] = useState<{ commandKey: string; artifact?: any } | null>(null);
  const [reassignLineId, setReassignLineId] = useState<string | null>(null);
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

  /**
   * FIX-2026-04-08: Triple fallback para garantizar que expedienteId NUNCA sea vacío.
   * Orden de prioridad:
   *   1. expediente.id          — alias agregado por serializers_ui.py (fix backend)
   *   2. expediente.expediente_id — campo UUID canónico del modelo Django
   *   3. id (params.id)         — UUID de la URL — siempre disponible como último recurso
   */
  const expedienteId: string = expediente.id || expediente.expediente_id || id || '';

  const isAdmin = bundle.is_admin === true;
  const creditCls = CREDIT_BAND_CLASSES[bundle.credit_clock?.band ?? "MINT"];
  const currentState = expediente.status === "ABIERTO" ? "REGISTRO" : expediente.status;

  const hasAction = (actionId: string) => {
    const actions = bundle.available_actions;
    if (!actions) return false;
    const lowerId = actionId.toLowerCase();
    return (
      actions.primary?.some((a: any) => a.id?.toLowerCase() === lowerId) ||
      actions.secondary?.some((a: any) => a.id?.toLowerCase() === lowerId) ||
      actions.ops?.some((a: any) => a.id?.toLowerCase() === lowerId)
    );
  };

  const calculateAdvanceValidation = () => {
    if (currentState === "CERRADO" || currentState === "CANCELADO") return { canAdvance: false, errors: [] };
    
    const currentPolicy = bundle.artifact_policy?.[currentState];
    const errors: string[] = [];
    
    if (currentPolicy) {
      const gateArtifacts = currentPolicy.gate_for_advance || [];
      const completedTypes = new Set(
        (bundle.artifacts || [])
          .filter(a => a.status?.toUpperCase() === 'COMPLETED')
          .map(a => a.artifact_type)
      );
      
      gateArtifacts.forEach((artType: string) => {
        if (!completedTypes.has(artType)) {
          const label = ARTIFACT_UI_REGISTRY[artType]?.label || artType;
          errors.push(`Falta: ${label}`);
        }
      });
    }

    if (currentState === "REGISTRO") {
      const orphanLines = (bundle.product_lines || []).filter((l: any) => l.proforma_id === null);
      if (orphanLines.length > 0) {
        errors.push(`${orphanLines.length} línea(s) sin proforma`);
      }
      
      const proformas = (bundle.artifacts || []).filter(
        a => a.artifact_type === 'ART-02' && a.status?.toUpperCase() === 'COMPLETED'
      );
      const noMode = proformas.filter(p => !p.payload?.mode);
      if (noMode.length > 0) {
        errors.push(`${noMode.length} proforma(s) sin modo`);
      }
    }

    const gateCommand = STATE_TO_ADVANCE_COMMAND[currentState];
    const canAdvance = errors.length === 0 && !!gateCommand && hasAction(gateCommand);
    
    return { canAdvance, errors };
  };

  const { canAdvance, errors: advanceErrors } = calculateAdvanceValidation();
  const hasArt06 = bundle.artifacts.some(a => a.artifact_type === 'ART-06' && a.status?.toUpperCase() === 'COMPLETED');
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
              {isAdmin && (
                <span className="badge text-[10px] bg-amber-100 text-amber-700 border border-amber-300 px-2 py-0.5">
                  👑 ADMIN
                </span>
              )}
            </div>
            <p className="page-subtitle">{expediente.client_name || "Sin Cliente"} · {expediente.brand_name || "Sin Marca"}</p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
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
            <button className="btn btn-sm btn-danger-outline" onClick={() => setActiveModal({ commandKey: "C17" })}>
              <Lock size={14} /> Bloquear
            </button>
          )}
          {hasAction("C18") && expediente.is_blocked && (
            <button className="btn btn-sm" style={{ color: "var(--success)", borderColor: "var(--success)", background: "transparent", border: "1px solid" }} onClick={() => setActiveModal({ commandKey: "C18" })}>
              <Lock size={14} /> Desbloquear
            </button>
          )}

          {/* Costos y Pagos: siempre clickeables cuando bundle está cargado */}
          <button
            className="btn btn-sm btn-secondary"
            onClick={() => setActiveModal({ commandKey: "C15" })}
          >
            Costos
          </button>
          <button
            className="btn btn-sm btn-secondary"
            onClick={() => setActiveModal({ commandKey: "C21" })}
          >
            Pagos
          </button>

          {hasAction("C16") && (
            <button className="btn btn-sm btn-danger-outline" onClick={() => setActiveModal({ commandKey: "C16" })}>Cancelar</button>
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
        <div><span className="text-[var(--text-tertiary)]">Modalidad:</span> <span className="font-medium text-[var(--interactive)] ml-1">{MODE_LABELS[expediente.mode] || expediente.mode || "—"}</span></div>
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
          <GateMessage requiredToAdvance={advanceErrors} currentState={currentState} />

          {!canAdvance && advanceErrors.length > 0 && (
            <div className="card p-4 bg-amber-50 border-amber-200 mb-6 flex items-start gap-4">
              <div className="p-2 bg-white rounded-lg shadow-sm border border-amber-100 text-amber-600">
                <Info size={20} />
              </div>
              <div>
                <p className="text-sm font-semibold text-amber-900 mb-1">Pendiente para avanzar a la siguiente fase</p>
                <div className="flex flex-wrap gap-2">
                  {advanceErrors.map((err, i) => (
                    <span key={i} className="px-2 py-0.5 bg-amber-100/50 text-amber-700 text-[11px] font-medium rounded-full border border-amber-200">
                      {err}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}

          {canAdvance && (
            <button
              className="w-full btn btn-primary bg-[var(--interactive)] text-white flex items-center justify-center gap-2 py-3 shadow-md hover:shadow-lg transition-all"
              onClick={() => setActiveModal({ commandKey: STATE_TO_ADVANCE_COMMAND[currentState]! })}
            >
              Avanzar a la siguiente fase <ArrowRight size={16} />
            </button>
          )}

          {showC11B && (
            <button
              className="w-full btn btn-secondary flex items-center justify-center gap-2 py-3 shadow-sm mt-4 text-[var(--info)] border-[var(--info)]"
              onClick={() => setActiveModal({ commandKey: "C11B" })}
            >
              <Truck size={18} /> Confirmar Salida (China)
            </button>
          )}

          {bundle.product_lines && bundle.product_lines.length > 0 && (
            <section className="space-y-6 mb-8">
              <div className="flex items-center justify-between">
                <h2 className="heading-sm font-semibold flex items-center gap-2 text-[var(--interactive)]">
                   <Package size={18} /> Proformas y Líneas
                </h2>
                {currentState === "REGISTRO" && hasAction("C3") && (
                  <button 
                    className="btn btn-sm btn-outline text-[var(--interactive)] border-[var(--interactive)] hover:bg-[var(--interactive)]/5 flex items-center gap-1.5"
                    onClick={() => setActiveModal({ commandKey: "C3" })}
                  >
                    + Crear Proforma
                  </button>
                )}
              </div>

              {(() => {
                const proformas = (bundle.artifacts || []).filter(a => a.artifact_type === 'ART-02');
                const orphanLines = (bundle.product_lines || []).filter(l => l.proforma_id === null);

                return (
                  <>
                    {proformas.map(pf => (
                      <ProformaSection
                        key={pf.id}
                        proforma={pf}
                        brandSlug={expediente.brand_slug}
                        currentState={currentState}
                        lines={(bundle.product_lines || []).filter(l => l.proforma_id === pf.id)}
                        childArtifacts={(bundle.artifacts || []).filter(a => a.parent_proforma_id === pf.id)}
                        availableActions={bundle.available_actions}
                        onActionClick={(cmd, art) => setActiveModal({ commandKey: cmd, artifact: art })}
                        hasAction={hasAction}
                        onReassignLine={(lineId) => setReassignLineId(lineId)}
                        isEditable={currentState === 'REGISTRO'}
                      />
                    ))}

                    {orphanLines.length > 0 && (
                      <div className="card border-dashed border-2 border-red-200 bg-red-50/10 overflow-hidden">
                        <div className="px-5 py-4 flex items-center justify-between bg-red-50/20">
                          <div className="flex items-center gap-2 text-red-700">
                            <AlertTriangle size={16} />
                            <span className="font-semibold text-sm">Líneas sin asignar a proforma</span>
                          </div>
                          <span className="text-[10px] font-bold text-red-500 uppercase px-2 py-0.5 bg-white border border-red-200 rounded">Acción Requerida</span>
                        </div>
                        <div className="overflow-x-auto">
                          <table className="w-full text-left text-sm">
                            <tbody className="divide-y divide-red-100">
                              {orphanLines.map(line => (
                                <tr key={line.id} className="hover:bg-red-50/20 transition-colors">
                                  <td className="px-5 py-3 flex items-center gap-2">
                                    <Package size={14} className="text-red-400" />
                                    <span>{line.product_name}</span>
                                  </td>
                                  <td className="px-5 py-3 text-red-600 text-xs font-medium">Sin Proforma</td>
                                  <td className="px-5 py-3 text-right">
                                    <button 
                                      className="btn btn-sm btn-ghost text-red-700 hover:bg-red-100"
                                      onClick={() => setReassignLineId(line.id)}
                                    >
                                      Asignar
                                    </button>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                  </>
                );
              })()}
            </section>
          )}

          <ExpedienteAccordion
            expedienteId={expedienteId}
            expedienteData={{ ...expediente, artifacts: bundle.artifacts, artifact_policy: bundle.artifact_policy }}
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
            onActionClick={(cmd, artifact) => setActiveModal({ commandKey: cmd, artifact })}
            isAdmin={isAdmin}
          />

          <CostTable expedienteId={expedienteId} />
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
                        {ev.payload && Object.keys(ev.payload).length > 0 && (
                          <details className="mt-1">
                            <summary className="text-[10px] text-[var(--text-tertiary)] cursor-pointer hover:text-[var(--text-secondary)]">Ver payload</summary>
                            <pre className="mt-1 text-[9px] bg-[var(--bg-alt)] rounded p-2 overflow-x-auto text-[var(--text-tertiary)] whitespace-pre-wrap break-all">
                              {JSON.stringify(ev.payload, null, 2)}
                            </pre>
                          </details>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {activeModal?.commandKey === "C2" ? (
        <CreateProformaModal
          open={true}
          expedienteId={expedienteId}
          brandSlug={bundle.expediente.brand_slug}
          orphanLines={(bundle.product_lines || []).filter(l => l.proforma_id === null)}
          onClose={() => setActiveModal(null)}
          onRefresh={() => fetchBundle(true)}
        />
      ) : activeModal && (
        <ArtifactModal
          open={true}
          expedienteId={expedienteId}
          commandKey={activeModal.commandKey}
          artifact={activeModal.artifact}
          onClose={() => setActiveModal(null)}
          onSuccess={() => { setActiveModal(null); fetchBundle(true); }}
          isAdmin={isAdmin}
        />
      )}

      {reassignLineId && (
        <ReassignLineModal
          open={true}
          expedienteId={expedienteId}
          lineId={reassignLineId}
          proformas={(bundle.artifacts || []).filter(a => a.artifact_type === 'ART-02')}
          onClose={() => setReassignLineId(null)}
          onSuccess={() => { setReassignLineId(null); fetchBundle(true); }}
        />
      )}
    </div>
  );
}
