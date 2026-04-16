"use client";
/**
 * Expediente Detail Page — Admin + Client dual layout
 *
 * REDESIGN-2026-04-16b: Match the design mockup exactly.
 *  - Admin view: 3 columns
 *    Left:   "Artifact" accordion — fases pasadas expandidas, futuras bloqueadas 🔒
 *    Center: "Tabla de Costos" (dark teal header per active phase) + pending artifacts
 *            with action buttons + CostTable + "Registro de Pagos"
 *    Right:  DeferredPricePanel + EventsPanel (human-readable)
 *  - Client view: same 3 cols but simplified (no admin controls)
 *  - Phase locking: past phases = full access, current = full access, future = LOCKED (visual + disabled)
 */
import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft, RefreshCw, AlertTriangle, Lock,
  CheckCircle, Pencil, Plus, Upload, FileText,
  Info, Download, Eye, EyeOff, ArrowRight, Truck, Package,
  ChevronDown, ChevronRight as ChevronRightIcon
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
import { EXPEDIENTE_LEVEL_ARTIFACTS } from "@/constants/proforma-artifact-policy";
import { ARTIFACT_UI_REGISTRY } from "@/constants/artifact-ui-registry";
import { MODE_LABELS } from "@/constants/mode-labels";
import CreateProformaModal from "@/components/expediente/CreateProformaModal";
import { fetchBuilderArtifacts } from "@/lib/builderApi";

// ── S25 imports ────────────────────────────────────────────────────────────────
import CreditBar from "@/components/expediente/CreditBar";
import PagosSection from "@/components/expediente/PagosSection";
import DeferredPricePanel from "@/components/expediente/DeferredPricePanel";
import FamilyBanner from "@/components/expediente/FamilyBanner";
import { PortalPagosTab } from "@/components/portal/PortalPagosTab";
import NotificationLogsSection from "@/components/expediente/NotificationLogsSection";

// ─── Types ────────────────────────────────────────────────────────────────────

interface ExpedienteRef {
  expediente_id: string;
  ref_number?: string;
  custom_ref?: string;
}

interface CostLine {
  id: string;
  cost_type: string;
  description: string;
  amount: number;
  currency: string;
  phase: string;
  visible_to_client: boolean;
}

interface ExpedienteBundle {
  expediente: {
    id: string;
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
    deferred_total_price?: number | null;
    deferred_visible?: boolean;
    parent_expediente?: ExpedienteRef | null;
    child_expedientes?: ExpedienteRef[];
    is_inverted_child?: boolean;
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
  credit_snapshot?: {
    payment_coverage?: "none" | "partial" | "complete";
    coverage_pct?: number;
    total_released?: number;
    total_pending?: number;
    total_rejected?: number;
    expediente_total?: number;
    credit_released?: boolean;
  };
  costs: CostLine[];
  payments: any[];
  documents: any[];
  is_admin?: boolean;
}

// ─── Constants ────────────────────────────────────────────────────────────────

const CREDIT_BAND_CLASSES = {
  MINT:  "bg-emerald-50 text-emerald-700 border-emerald-200",
  AMBER: "bg-amber-50 text-amber-700 border-amber-200",
  RED:   "bg-red-50 text-red-700 border-red-200",
};

const STATE_TO_ADVANCE_COMMAND: Record<string, string> = {
  REGISTRO:    "C5",
  PRODUCCION:  "C11B",
  PREPARACION: "C10",
  DESPACHO:    "C11",
  TRANSITO:    "C12",
  EN_DESTINO:  "C14",
};

// Artifact → phase mapping
const ARTIFACT_PHASE_MAP: Record<string, string> = {
  "ART-01": "REGISTRO",  "ART-02": "REGISTRO",  "ART-22": "REGISTRO",
  "ART-03": "PRODUCCION","ART-04": "PRODUCCION","ART-05": "PRODUCCION","ART-06": "PRODUCCION",
  "ART-07": "PREPARACION","ART-08": "PREPARACION","ART-09": "PREPARACION","ART-12": "PREPARACION",
  "ART-19": "DESPACHO",
  "ART-10": "TRANSITO", "ART-36": "TRANSITO",
  "ART-11": "EN_DESTINO","ART-13": "EN_DESTINO",
  "ART-16": "CERRADO",
};

const PHASE_ORDER = ["REGISTRO","PRODUCCION","PREPARACION","DESPACHO","TRANSITO","EN_DESTINO","CERRADO"];

// Human-readable event labels
function humanizeEvent(ev: any): string {
  const type: string = ev?.event_type ?? "";
  const map: Record<string, string> = {
    "expediente.registered":           "Expediente registrado",
    "expediente.oc_registered":        "Orden de Compra completada",
    "expediente.produccion":           "Producción iniciada",
    "expediente.production_confirmed": "Confirmación Producción recibida",
    "expediente.preparacion":          "Preparación iniciada",
    "expediente.despacho":             "Despacho aprobado",
    "expediente.transito":             "Embarque en tránsito",
    "expediente.en_destino":           "Llegó a destino",
    "expediente.cerrado":              "Expediente cerrado",
    "artifact.completed":              "Documento disponible",
    "artifact.created":                "Documento creado",
    "payment.registered":              "Pago registrado",
    "payment.released":                "Crédito liberado",
  };
  if (map[type]) return map[type];
  // Fallback with emitted_by for "Packing List solicitado por Admin" style
  const clean = type.replace(/\./g, ": ").replace(/_/g, " ");
  if (ev?.emitted_by && /admin|ceo|interno/i.test(ev.emitted_by)) {
    return `${clean} por ${ev.emitted_by}`;
  }
  return clean.replace(/\b\w/g, c => c.toUpperCase());
}

// ─── Timeline Bar ─────────────────────────────────────────────────────────────

function TimelineBar({ currentState }: { currentState: string }) {
  const curIdx = CANONICAL_STATES.indexOf(currentState as any);
  return (
    <div className="bg-surface border border-border rounded-xl px-2 py-2 overflow-x-auto">
      <div className="flex items-center min-w-max">
        {CANONICAL_STATES.map((state, idx) => {
          const isPast    = idx < curIdx;
          const isCurrent = state === currentState;
          return (
            <div key={state} className="flex items-center">
              <div className={cn(
                "flex items-center justify-center h-9 px-4 text-[11px] font-semibold whitespace-nowrap transition-all",
                idx === 0 ? "rounded-l-full" : "",
                idx === CANONICAL_STATES.length - 1 ? "rounded-r-full" : "",
                isPast    ? "bg-[#1a6b5a] text-white"
                : isCurrent ? "bg-[#0f2d25] text-white font-bold"
                : "bg-bg-alt text-text-tertiary"
              )}>
                {isPast && <span className="mr-1 text-white/80 text-xs">✓</span>}
                {state}
              </div>
              {idx < CANONICAL_STATES.length - 1 && (
                <div className={cn(
                  "w-0 h-0 border-t-[18px] border-b-[18px] border-l-[10px]",
                  "border-t-transparent border-b-transparent",
                  isPast ? "border-l-[#1a6b5a]" : isCurrent ? "border-l-[#0f2d25]" : "border-l-bg-alt"
                )} />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── KPI Cards Row ────────────────────────────────────────────────────────────

function KPIRow({ expediente, artifactsCount, creditDays, creditBand }: {
  expediente: ExpedienteBundle["expediente"];
  artifactsCount: number;
  creditDays: number;
  creditBand: "MINT" | "AMBER" | "RED";
}) {
  const creditCls = CREDIT_BAND_CLASSES[creditBand];
  const payLabel = expediente.payment_status === "PAID" ? "Pagado"
    : expediente.payment_status === "PARTIAL" ? "Parcial"
    : expediente.payment_status ?? "—";
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      <div className="bg-surface border border-border rounded-xl p-4">
        <p className="text-[10px] text-text-tertiary uppercase tracking-wide mb-0.5">Estado pago</p>
        <p className="text-lg font-bold text-text-primary">{payLabel}</p>
      </div>
      <div className="bg-surface border border-border rounded-xl p-4">
        <p className="text-[10px] text-text-tertiary uppercase tracking-wide mb-0.5">Artefactos</p>
        <p className="text-3xl font-bold text-text-primary">{artifactsCount}</p>
      </div>
      <div className="bg-surface border border-border rounded-xl p-4">
        <p className="text-[10px] text-text-tertiary uppercase tracking-wide mb-0.5">Costo Total</p>
        <p className="text-lg font-bold text-text-primary">
          ${Number(expediente.total_cost || 0).toLocaleString("en-US", { minimumFractionDigits: 2 })}
        </p>
      </div>
      <div className={cn("border rounded-xl p-4", creditCls)}>
        <p className="text-[10px] uppercase tracking-wide mb-0.5 font-semibold">Crédito ({creditBand})</p>
        <p className="text-lg font-bold">{creditDays} días restantes</p>
      </div>
    </div>
  );
}

// ─── Admin Artifact Accordion (left column) ───────────────────────────────────
// Shows: completed phases expanded, current phase expanded, future phases LOCKED

function AdminArtifactAccordion({
  artifacts, currentState, onActionClick, availableActions
}: {
  artifacts: ExpedienteBundle["artifacts"];
  currentState: string;
  onActionClick: (cmd: string, artifact?: any) => void;
  availableActions: ExpedienteBundle["available_actions"];
}) {
  const curIdx = PHASE_ORDER.indexOf(currentState);

  // Group by phase
  const byPhase: Record<string, typeof artifacts> = {};
  for (const art of artifacts) {
    const ph = ARTIFACT_PHASE_MAP[art.artifact_type] ?? "REGISTRO";
    if (!byPhase[ph]) byPhase[ph] = [];
    byPhase[ph].push(art);
  }

  // Open by default: phases <= current
  const [openPhases, setOpenPhases] = useState<Record<string, boolean>>(() => {
    const init: Record<string, boolean> = {};
    PHASE_ORDER.forEach((ph, i) => { if (i <= curIdx) init[ph] = true; });
    return init;
  });

  const toggle = (ph: string) => setOpenPhases(p => ({ ...p, [ph]: !p[ph] }));

  return (
    <div className="bg-surface border border-border rounded-xl shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-5 py-3 border-b border-border bg-bg-alt/30">
        <h3 className="text-sm font-semibold text-text-primary">Artifact</h3>
      </div>

      <div className="divide-y divide-border/60">
        {PHASE_ORDER.map((phase, phIdx) => {
          const arts = byPhase[phase] ?? [];
          const phaseIdx = PHASE_ORDER.indexOf(phase);
          const isLocked = phaseIdx > curIdx;
          const isCurrent = phase === currentState;
          const isPast = phaseIdx < curIdx;
          const completedCount = arts.filter(a => a.status === "completed").length;
          const isOpen = openPhases[phase] ?? false;

          return (
            <div key={phase}>
              {/* Phase header row */}
              <button
                onClick={() => !isLocked && toggle(phase)}
                disabled={isLocked}
                className={cn(
                  "w-full flex items-center justify-between px-5 py-3 text-left transition-colors",
                  isLocked ? "opacity-50 cursor-not-allowed" : "hover:bg-bg-alt/40"
                )}
              >
                <div className="flex items-center gap-2">
                  {isPast && <CheckCircle size={13} className="text-emerald-500 flex-shrink-0" />}
                  {isLocked && <Lock size={12} className="text-text-tertiary flex-shrink-0 opacity-60" />}
                  <span className={cn(
                    "text-xs font-bold uppercase tracking-wide",
                    isPast ? "text-emerald-700" : isCurrent ? "text-text-primary" : "text-text-tertiary"
                  )}>
                    {phase}
                  </span>
                  {!isLocked && (
                    <span className="text-[10px] text-text-tertiary ml-1">
                      {completedCount} completados
                    </span>
                  )}
                </div>
                {!isLocked && (
                  <span className="text-text-tertiary">
                    {isOpen ? <ChevronDown size={14} /> : <ChevronRightIcon size={14} />}
                  </span>
                )}
              </button>

              {/* Phase artifacts */}
              {isOpen && !isLocked && (
                <div className="px-5 pb-4 space-y-3">
                  {arts.length === 0 && (
                    <p className="text-xs text-text-tertiary italic">Sin artefactos en esta fase.</p>
                  )}
                  {arts.map(art => {
                    const meta = ARTIFACT_UI_REGISTRY[art.artifact_type];
                    const label = meta?.label ?? art.artifact_type;
                    const isDone = art.status === "completed";
                    const count = art.payload?.count;
                    const lastDate = art.payload?.last_date ?? art.created_at;

                    return (
                      <div key={art.id} className={cn(
                        "rounded-xl border p-3 space-y-1.5",
                        isDone ? "border-emerald-200 bg-emerald-50/40" : "border-border bg-bg-alt/20"
                      )}>
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex items-center gap-2 flex-1 min-w-0">
                            <span className={cn(
                              "w-5 h-5 rounded-full flex-shrink-0 flex items-center justify-center",
                              isDone ? "bg-emerald-100" : "bg-border"
                            )}>
                              {isDone
                                ? <CheckCircle size={12} className="text-emerald-600" />
                                : <span className="w-2 h-2 rounded-full bg-text-tertiary" />}
                            </span>
                            <div className="min-w-0">
                              <p className={cn("text-xs font-semibold truncate", isDone ? "text-text-primary" : "text-text-secondary")}>
                                {label}
                              </p>
                              {isDone && lastDate && (
                                <p className="text-[10px] text-text-tertiary">
                                  {new Date(lastDate).toLocaleDateString("es-CR", { day: "2-digit", month: "short", year: "numeric" })}
                                </p>
                              )}
                              {count != null && (
                                <div className="flex items-center gap-1 mt-0.5">
                                  <span className="inline-block text-[9px] bg-emerald-100 text-emerald-700 px-1.5 py-0.5 rounded font-bold uppercase">
                                    COMPLETADO
                                  </span>
                                  <span className="text-[9px] text-text-tertiary">
                                    · {count} REGISTRO{count !== 1 ? "S" : ""}
                                  </span>
                                </div>
                              )}
                            </div>
                          </div>

                          {/* Actions */}
                          {isDone && (
                            <button
                              onClick={() => onActionClick("VIEW", art)}
                              className="text-[11px] font-medium text-[#1a6b5a] hover:underline flex-shrink-0 whitespace-nowrap"
                            >
                              Ver detalle
                            </button>
                          )}
                          {!isDone && meta?.command && (
                            <button
                              onClick={() => onActionClick(meta.command, art)}
                              className="text-[11px] font-medium text-[#1a6b5a] hover:underline flex-shrink-0"
                            >
                              Registrar
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── Cost + Actions Center Column ─────────────────────────────────────────────

function CostActionsCenter({
  bundle, expedienteId, currentState, isAdmin, onActionClick, hasAction, onRefresh
}: {
  bundle: ExpedienteBundle;
  expedienteId: string;
  currentState: string;
  isAdmin: boolean;
  onActionClick: (cmd: string, art?: any) => void;
  hasAction: (cmd: string) => boolean;
  onRefresh: () => void;
}) {
  const [clientView, setClientView] = useState(false);

  // Pending artifacts for the CURRENT phase (items needing user action)
  const currentPhaseArtifacts = (bundle.artifacts || []).filter(art => {
    const phase = ARTIFACT_PHASE_MAP[art.artifact_type];
    return phase === currentState && art.status !== "completed";
  });

  return (
    <div className="space-y-4">
      {/* ── Tabla de Costos ── */}
      <div className="bg-surface border border-border rounded-xl shadow-sm overflow-hidden">
        {/* Dark header with phase name */}
        <div className="px-5 py-3 flex items-center justify-between bg-[#0f2d25]">
          <h3 className="text-sm font-semibold text-white">Tabla de Costos</h3>
          {/* Vista Cliente toggle */}
          <div className="flex items-center gap-2">
            <span className="text-[11px] text-white/60">Vista Cliente</span>
            <button
              onClick={() => setClientView(v => !v)}
              className={cn(
                "relative w-9 h-5 rounded-full transition-all duration-200",
                clientView ? "bg-[#1a6b5a]" : "bg-white/20"
              )}
            >
              <div className={cn(
                "absolute top-0.5 w-4 h-4 rounded-full bg-white shadow-sm transition-all duration-200",
                clientView ? "left-4" : "left-0.5"
              )} />
            </button>
          </div>
        </div>

        {/* Current phase pending action items */}
        {currentPhaseArtifacts.length > 0 && isAdmin && (
          <div className="border-b border-border">
            <div className="px-5 py-2.5 bg-[#0f2d25]/5">
              <p className="text-[10px] font-bold uppercase tracking-wide text-[#1a6b5a]">{currentState}</p>
            </div>
            <div className="px-5 py-2 space-y-1.5">
              {currentPhaseArtifacts.map(art => {
                const meta = ARTIFACT_UI_REGISTRY[art.artifact_type];
                const label = meta?.label ?? art.artifact_type;
                const cmd = meta?.command;
                return (
                  <div key={art.id} className="flex items-center justify-between py-1.5">
                    <div className="flex items-center gap-2">
                      <FileText size={13} className="text-text-tertiary" />
                      <span className="text-xs text-text-secondary">{label}</span>
                    </div>
                    {cmd && hasAction(cmd) && (
                      <button
                        onClick={() => onActionClick(cmd, art)}
                        className="flex items-center gap-1.5 px-3 py-1 text-xs font-semibold bg-[#0f2d25] text-white rounded-lg hover:bg-[#1a6b5a] transition-colors"
                      >
                        <Upload size={12} /> Cargar archivo
                      </button>
                    )}
                    {cmd && hasAction(cmd) && label.toLowerCase().includes("cotizaci") && (
                      <button
                        onClick={() => onActionClick(cmd, art)}
                        className="flex items-center gap-1.5 px-3 py-1 text-xs font-semibold bg-[#0f2d25] text-white rounded-lg hover:bg-[#1a6b5a] transition-colors"
                      >
                        Solicitar
                      </button>
                    )}
                  </div>
                );
              })}
              {isAdmin && (
                <button
                  onClick={() => onActionClick("C15")}
                  className="flex items-center gap-1 text-xs text-[#1a6b5a] hover:underline font-medium mt-1"
                >
                  <Plus size={12} /> Agregar artefacto (admin)
                </button>
              )}
            </div>
          </div>
        )}

        {/* Cost table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-bg-alt/60 text-[10px] uppercase text-text-tertiary tracking-wider border-b border-border">
                <th className="px-4 py-2.5">Tipo</th>
                <th className="px-4 py-2.5">Descripción</th>
                <th className="px-4 py-2.5">Fase</th>
                <th className="px-4 py-2.5 text-right">Monto</th>
                {isAdmin && !clientView && <th className="px-4 py-2.5 text-center">Vis. Cliente</th>}
              </tr>
            </thead>
            <tbody>
              {(clientView
                ? bundle.costs.filter(c => c.visible_to_client)
                : bundle.costs
              ).length === 0 ? (
                <tr>
                  <td colSpan={isAdmin && !clientView ? 5 : 4} className="px-4 py-6 text-center text-xs text-text-tertiary">
                    Sin costos registrados
                  </td>
                </tr>
              ) : (clientView ? bundle.costs.filter(c => c.visible_to_client) : bundle.costs).map(c => (
                <tr key={c.id} className="border-b border-border/50 last:border-0 hover:bg-bg-alt/30 transition-colors">
                  <td className="px-4 py-2.5 text-xs font-medium text-text-secondary">{c.cost_type}</td>
                  <td className="px-4 py-2.5 text-xs text-text-secondary">{c.description}</td>
                  <td className="px-4 py-2.5 text-[10px] text-text-tertiary">{c.phase}</td>
                  <td className="px-4 py-2.5 text-xs font-semibold text-right text-text-primary">
                    {c.currency} ${Number(c.amount).toLocaleString("en-US", { minimumFractionDigits: 2 })}
                  </td>
                  {isAdmin && !clientView && (
                    <td className="px-4 py-2.5 text-center">
                      {c.visible_to_client
                        ? <Eye size={13} className="text-[#1a6b5a] mx-auto" />
                        : <EyeOff size={13} className="text-text-tertiary mx-auto" />}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Registro de Pagos ── */}
      <div className="bg-surface border border-border rounded-xl overflow-hidden shadow-sm">
        <div className="px-5 py-3 border-b border-border flex items-center justify-between">
          <h3 className="text-sm font-semibold text-text-primary">Registro de Pagos</h3>
          {isAdmin && (
            <button
              onClick={() => onActionClick("C21")}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-[#0f2d25] text-white rounded-lg hover:bg-[#1a6b5a] transition-colors shadow-sm"
            >
              Registrar pago
            </button>
          )}
        </div>
        <PagosSection
          expedienteId={expedienteId}
          isCeo={isAdmin}
          onCreditRefresh={onRefresh}
        />
      </div>
    </div>
  );
}

// ─── Right Panel ──────────────────────────────────────────────────────────────

function RightPanel({ bundle, expedienteId, isAdmin, onRefresh }: {
  bundle: ExpedienteBundle;
  expedienteId: string;
  isAdmin: boolean;
  onRefresh: () => void;
}) {
  const { expediente } = bundle;
  return (
    <div className="space-y-4">
      {/* Deferred Price */}
      {isAdmin && (
        <DeferredPricePanel
          expedienteId={expedienteId}
          deferredTotalPrice={expediente.deferred_total_price ?? null}
          deferredVisible={expediente.deferred_visible ?? false}
          isCeo={true}
          onUpdate={onRefresh}
        />
      )}
      {!isAdmin && expediente.deferred_total_price != null && expediente.deferred_total_price > 0 && (
        <div className="bg-surface border border-border rounded-xl p-5">
          <h3 className="text-sm font-semibold text-text-primary mb-1">Precio diferido</h3>
          <p className="text-2xl font-bold text-text-primary">
            ${Number(expediente.deferred_total_price).toLocaleString("en-US", { minimumFractionDigits: 2 })}
          </p>
          <p className="text-xs text-text-tertiary mt-1">Vence en 30 días</p>
        </div>
      )}

      {/* Notification logs (admin only) */}
      {isAdmin && (
        <div className="bg-surface border border-border rounded-xl p-4">
          <NotificationLogsSection expedienteId={expedienteId} isCeo={isAdmin} />
        </div>
      )}

      {/* Events timeline */}
      <div className="bg-surface border border-border rounded-xl shadow-sm overflow-hidden">
        <div className="px-5 py-3 border-b border-border">
          <h3 className="text-sm font-semibold text-text-primary">Historial de eventos</h3>
        </div>
        <div className="overflow-y-auto max-h-[480px]">
          {(!Array.isArray(bundle.events) || bundle.events.length === 0) ? (
            <div className="px-5 py-8 text-center text-sm text-text-tertiary">Sin eventos aún.</div>
          ) : (
            <div className="px-5 py-4 space-y-4">
              {bundle.events.slice(0, isAdmin ? 100 : 10).map((ev, i) => (
                <div key={ev.id ?? i} className="flex gap-3">
                  <div className="flex flex-col items-center flex-shrink-0">
                    <div className={cn(
                      "w-2.5 h-2.5 rounded-full mt-0.5 border-2 flex-shrink-0",
                      i === 0 ? "bg-[#1a6b5a] border-[#1a6b5a]" : "bg-white border-border-strong"
                    )} />
                    {i < Math.min(bundle.events.length, isAdmin ? 100 : 10) - 1 && (
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
                      {humanizeEvent(ev)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Client Documents Accordion ───────────────────────────────────────────────

function ClientDocumentsAccordion({ artifacts }: { artifacts: ExpedienteBundle["artifacts"] }) {
  const [openPhases, setOpenPhases] = useState<Record<string, boolean>>({ REGISTRO: true, PRODUCCION: true });
  const byPhase: Record<string, typeof artifacts> = {};
  for (const art of artifacts) {
    const ph = ARTIFACT_PHASE_MAP[art.artifact_type] ?? "REGISTRO";
    if (!byPhase[ph]) byPhase[ph] = [];
    byPhase[ph].push(art);
  }
  const toggle = (ph: string) => setOpenPhases(p => ({ ...p, [ph]: !p[ph] }));

  return (
    <div className="bg-surface border border-border rounded-xl shadow-sm overflow-hidden">
      <div className="px-5 py-3 border-b border-border">
        <h3 className="text-sm font-semibold text-text-primary">Documentos Confirmados</h3>
      </div>
      <div className="divide-y divide-border/60">
        {PHASE_ORDER.filter(ph => byPhase[ph]?.length).map(phase => {
          const arts = byPhase[phase] ?? [];
          const completed = arts.filter(a => a.status === "completed").length;
          const isOpen = openPhases[phase] ?? false;
          return (
            <div key={phase}>
              <button
                onClick={() => toggle(phase)}
                className="w-full flex items-center justify-between px-5 py-3 hover:bg-bg-alt/40 text-left"
              >
                <span className="text-xs font-semibold text-text-secondary uppercase tracking-wide">
                  {phase} <span className="text-emerald-600 font-normal ml-1">({completed}/{arts.length})</span>
                </span>
                {isOpen ? <ChevronDown size={14} className="text-text-tertiary" /> : <ChevronRightIcon size={14} className="text-text-tertiary" />}
              </button>
              {isOpen && (
                <div className="px-5 pb-4 space-y-2.5">
                  {arts.map(art => {
                    const meta = ARTIFACT_UI_REGISTRY[art.artifact_type];
                    const label = meta?.label ?? art.artifact_type;
                    const isDone = art.status === "completed";
                    const fileUrl = art.payload?.file_url ?? art.payload?.url ?? null;
                    return (
                      <div key={art.id} className="flex items-center justify-between gap-3">
                        <div className="flex items-center gap-2 flex-1 min-w-0">
                          <span className={cn("w-5 h-5 rounded-full flex-shrink-0 flex items-center justify-center",
                            isDone ? "bg-emerald-100" : "bg-border")}>
                            {isDone ? <CheckCircle size={12} className="text-emerald-600" /> : <span className="w-2 h-2 rounded-full bg-text-tertiary" />}
                          </span>
                          <p className={cn("text-xs font-medium truncate", isDone ? "text-text-primary" : "text-text-tertiary")}>
                            {label}
                          </p>
                        </div>
                        {fileUrl && (
                          <a href={fileUrl} target="_blank" rel="noopener noreferrer"
                            className="flex items-center gap-1 text-xs text-[#1a6b5a] hover:underline font-medium flex-shrink-0">
                            <Download size={12} /> Descargar
                          </a>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

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
  const [viewMode, setViewMode] = useState<"internal" | "client">("internal");
  const [builderContext, setBuilderContext] = useState<any[]>([]);

  useEffect(() => {
    fetchBuilderArtifacts().then(data => setBuilderContext(data || [])).catch(() => {});
  }, []);

  const fetchBundle = useCallback(async (quiet = false) => {
    if (!quiet) setLoading(true);
    else setRefreshing(true);
    setError(null);
    try {
      const res = await api.get(`/ui/expedientes/${id}/`);
      const data = res.data;
      if (data) {
        data.artifacts = Array.isArray(data.artifacts) ? data.artifacts : [];
        data.events    = Array.isArray(data.events)    ? data.events    : [];
        data.costs     = Array.isArray(data.costs)     ? data.costs     : [];
        data.payments  = Array.isArray(data.payments)  ? data.payments  : [];
        data.documents = Array.isArray(data.documents) ? data.documents : [];
        data.available_actions = data.available_actions ?? { primary: [], secondary: [], ops: [] };
        ["primary","secondary","ops"].forEach(k => {
          if (!Array.isArray(data.available_actions[k])) data.available_actions[k] = [];
        });
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

  if (loading) return (
    <div className="flex items-center justify-center min-h-64">
      <div className="flex flex-col items-center gap-3 text-text-tertiary">
        <div className="w-8 h-8 border-2 border-[#1a6b5a] border-t-transparent rounded-full animate-spin" />
        <p className="text-sm">Cargando expediente…</p>
      </div>
    </div>
  );

  if (error || !bundle) return (
    <div className="flex flex-col items-center justify-center min-h-64 gap-4">
      <AlertTriangle size={40} className="text-red-400" />
      <p className="text-sm text-text-secondary">{error ?? "Expediente no encontrado."}</p>
      <button className="text-sm text-[#1a6b5a] hover:underline flex items-center gap-1" onClick={() => router.back()}>
        <ArrowLeft size={14} /> Volver
      </button>
    </div>
  );

  const { expediente } = bundle;
  const expedienteId: string = expediente.id || expediente.expediente_id || id || "";
  const isAdmin = bundle.is_admin === true;
  const currentState = expediente.status === "ABIERTO" ? "REGISTRO" : expediente.status;
  const creditBand  = bundle.credit_clock?.band ?? "MINT";
  const creditDays  = bundle.credit_clock?.days ?? 0;
  const displayMode = isAdmin ? viewMode : "client";
  const artifactsCount = bundle.artifacts.length;

  const hasAction = (actionId: string) => {
    const actions = bundle.available_actions;
    if (!actions) return false;
    const lowerId = actionId.toLowerCase();
    return (
      actions.primary?.some((a: any)   => a.id?.toLowerCase() === lowerId) ||
      actions.secondary?.some((a: any) => a.id?.toLowerCase() === lowerId) ||
      actions.ops?.some((a: any)       => a.id?.toLowerCase() === lowerId)
    );
  };

  // Phase advance validation
  const calculateAdvanceValidation = () => {
    if (currentState === "CERRADO" || currentState === "CANCELADO") return { canAdvance: false, errors: [] };
    const policy = bundle.artifact_policy?.[currentState];
    const errors: string[] = [];
    if (policy) {
      const completed = new Set(bundle.artifacts.filter(a => a.status?.toUpperCase() === "COMPLETED").map(a => a.artifact_type));
      (policy.gate_for_advance || []).forEach((t: string) => {
        if (!completed.has(t)) errors.push(`Falta: ${ARTIFACT_UI_REGISTRY[t]?.label || t}`);
      });
    }
    if (currentState === "REGISTRO") {
      const orphans = bundle.product_lines.filter(l => l.proforma_id === null);
      if (orphans.length > 0) errors.push(`${orphans.length} línea(s) sin proforma`);
    }
    const gateCmd = STATE_TO_ADVANCE_COMMAND[currentState];
    return { canAdvance: errors.length === 0 && !!gateCmd && hasAction(gateCmd), errors };
  };

  const { canAdvance, errors: advanceErrors } = calculateAdvanceValidation();

  // Credit snapshot
  const snap = bundle.credit_snapshot;
  const paymentCoverage = snap?.payment_coverage ?? "none";
  const coveragePct     = snap?.coverage_pct     ?? 0;
  const totalReleased   = snap?.total_released   ?? 0;
  const creditReleased  = snap?.credit_released  ?? false;
  const portalMeta = {
    expediente_id: expedienteId,
    payment_coverage: paymentCoverage as "none" | "partial" | "complete",
    coverage_pct: coveragePct,
    credit_released: creditReleased,
    deferred_total_price: expediente.deferred_total_price ?? null,
    deferred_visible: expediente.deferred_visible ?? false,
    total_lines_value: expediente.total_cost,
  };

  return (
    <div className="space-y-4 pb-10">

      {/* ─── Top Bar ────────────────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Link href={`/${lang}/expedientes`}
            className="p-1.5 rounded-lg hover:bg-bg-alt transition-colors text-text-tertiary hover:text-text-primary">
            <ArrowLeft size={18} />
          </Link>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-xl font-bold text-text-primary">Expediente</h1>
              {/* Status badge */}
              <span className={cn(
                "text-[11px] font-bold px-2.5 py-1 rounded-full",
                STATE_BADGE_CLASSES[expediente.status] ?? "bg-gray-100 text-gray-600"
              )}>
                {expediente.status}
              </span>
              {/* Admin badge */}
              {isAdmin && displayMode === "internal" && (
                <span className="text-[11px] font-bold px-2.5 py-1 rounded-full bg-[#0f2d25] text-white">
                  ADMIN
                </span>
              )}
              {/* Blocked */}
              {expediente.is_blocked && (
                <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-red-100 text-red-700 flex items-center gap-1">
                  <Lock size={10} /> BLOQUEADO
                </span>
              )}
            </div>
            <p className="text-sm text-text-tertiary mt-0.5">
              {expediente.client_name || "Sin Cliente"} · {expediente.brand_name || "Sin Marca"}
            </p>
          </div>
        </div>

        {/* Right actions */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* Toggle Interna / Cliente */}
          {isAdmin && (
            <div className="flex items-center gap-2 bg-bg-alt border border-border rounded-lg px-3 py-1.5">
              <span className="text-xs text-text-secondary font-medium">Interna</span>
              <button
                onClick={() => setViewMode(v => v === "internal" ? "client" : "internal")}
                className={cn(
                  "relative w-10 h-5 rounded-full transition-all duration-200",
                  viewMode === "client" ? "bg-[#1a6b5a]" : "bg-border-strong"
                )}
              >
                <div className={cn(
                  "absolute top-0.5 w-4 h-4 rounded-full bg-white shadow-sm transition-all duration-200",
                  viewMode === "client" ? "left-5" : "left-0.5"
                )} />
              </button>
              <span className="text-xs text-text-secondary font-medium">Cliente</span>
            </div>
          )}

          {/* Admin action buttons (internal only) */}
          {isAdmin && displayMode === "internal" && (
            <>
              {hasAction("C17") && !expediente.is_blocked && (
                <button onClick={() => setActiveModal({ commandKey: "C17" })}
                  className="px-3 py-1.5 text-xs border border-red-300 text-red-600 rounded-lg hover:bg-red-50">
                  <Lock size={11} className="inline mr-1" />Bloquear
                </button>
              )}
              {hasAction("C18") && expediente.is_blocked && (
                <button onClick={() => setActiveModal({ commandKey: "C18" })}
                  className="px-3 py-1.5 text-xs border border-emerald-300 text-emerald-600 rounded-lg hover:bg-emerald-50">
                  <Lock size={11} className="inline mr-1" />Desbloquear
                </button>
              )}
              <button
                onClick={() => setActiveModal({ commandKey: "C15" })}
                className="px-3 py-1.5 text-xs border border-border text-text-secondary rounded-lg hover:bg-bg-alt transition-colors"
              >
                + Costo
              </button>
              <button
                onClick={() => setActiveModal({ commandKey: "C21" })}
                className="px-4 py-1.5 text-xs bg-[#0f2d25] hover:bg-[#1a6b5a] text-white rounded-lg font-semibold transition-all shadow-sm active:scale-95"
              >
                + Pago
              </button>
              {hasAction("C16") && (
                <button onClick={() => setActiveModal({ commandKey: "C16" })}
                  className="px-3 py-1.5 text-xs border border-red-300 text-red-600 rounded-lg hover:bg-red-50">
                  Cancelar
                </button>
              )}
            </>
          )}

          <button
            onClick={() => fetchBundle(true)} disabled={refreshing}
            className="p-1.5 border border-border rounded-lg hover:bg-bg-alt text-text-tertiary hover:text-text-primary"
          >
            <RefreshCw size={15} className={cn(refreshing && "animate-spin")} />
          </button>
        </div>
      </div>

      {/* ─── Family Banner ─────────────────────────────────────────────── */}
      {(expediente.parent_expediente || (expediente.child_expedientes?.length ?? 0) > 0) && (
        <FamilyBanner
          currentId={expedienteId}
          parentExpediente={expediente.parent_expediente ?? null}
          childExpedientes={expediente.child_expedientes ?? []}
          isInvertedChild={expediente.is_inverted_child ?? false}
          lang={lang}
        />
      )}

      {/* ─── Timeline ──────────────────────────────────────────────────── */}
      <TimelineBar currentState={currentState} />

      {/* ─── KPI Row ───────────────────────────────────────────────────── */}
      <KPIRow
        expediente={expediente}
        artifactsCount={artifactsCount}
        creditDays={creditDays}
        creditBand={creditBand}
      />

      {/* ─── CreditBar (admin internal only) ───────────────────────────── */}
      {displayMode === "internal" && isAdmin && (
        <CreditBar
          paymentCoverage={paymentCoverage}
          coveragePct={coveragePct}
          totalReleased={totalReleased}
          expedienteTotal={expediente.total_cost}
          creditReleased={creditReleased}
          isCeo={isAdmin}
        />
      )}

      {/* ─── Advance gating errors ─────────────────────────────────────── */}
      {displayMode === "internal" && !canAdvance && advanceErrors.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start gap-3">
          <Info size={16} className="text-amber-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-xs font-semibold text-amber-900 mb-1">Pendiente para avanzar</p>
            <div className="flex flex-wrap gap-1.5">
              {advanceErrors.map((err, i) => (
                <span key={i} className="text-[10px] px-2 py-0.5 bg-amber-100 text-amber-700 rounded-full border border-amber-200">{err}</span>
              ))}
            </div>
          </div>
        </div>
      )}

      {displayMode === "internal" && canAdvance && (
        <button
          className="w-full bg-[#1a6b5a] hover:bg-[#155448] text-white rounded-xl py-2.5 text-sm font-semibold flex items-center justify-center gap-2 shadow-sm transition-all active:scale-95"
          onClick={() => setActiveModal({ commandKey: STATE_TO_ADVANCE_COMMAND[currentState]! })}
        >
          Avanzar a la siguiente fase <ArrowRight size={15} />
        </button>
      )}

      {/* ═══════════════════════════════════════════════════════════════════
          3-COLUMN LAYOUT (admin internal)
      ═══════════════════════════════════════════════════════════════════ */}
      {displayMode === "internal" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

          {/* ── Left: Artifact Accordion ── */}
          <div className="space-y-4">
            <AdminArtifactAccordion
              artifacts={bundle.artifacts}
              currentState={currentState}
              onActionClick={(cmd, art) => {
                if (cmd === "VIEW") {
                  // "Ver detalle" for a completed artifact → open ArtifactModal in view mode
                  setActiveModal({ commandKey: "VIEW", artifact: art });
                } else {
                  setActiveModal({ commandKey: cmd, artifact: art });
                }
              }}
              availableActions={bundle.available_actions}
            />
          </div>

          {/* ── Center: Costs + Actions + Pagos ── */}
          <div>
            <CostActionsCenter
              bundle={bundle}
              expedienteId={expedienteId}
              currentState={currentState}
              isAdmin={isAdmin}
              onActionClick={(cmd, art) => setActiveModal({ commandKey: cmd, artifact: art })}
              hasAction={hasAction}
              onRefresh={() => fetchBundle(true)}
            />
          </div>

          {/* ── Right: Deferred + Notif + Events ── */}
          <div>
            <RightPanel
              bundle={bundle}
              expedienteId={expedienteId}
              isAdmin={isAdmin}
              onRefresh={() => fetchBundle(true)}
            />
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════════════
          3-COLUMN LAYOUT (client view)
      ═══════════════════════════════════════════════════════════════════ */}
      {displayMode === "client" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

          {/* Left: Documentos */}
          <div>
            <ClientDocumentsAccordion artifacts={bundle.artifacts} />
          </div>

          {/* Center: Costos (solo visibles) + Portal Pagos */}
          <div className="space-y-4">
            <div className="bg-surface border border-border rounded-xl overflow-hidden shadow-sm">
              <div className="px-5 py-3 border-b border-border bg-[#0f2d25]">
                <h3 className="text-sm font-semibold text-white">Detalle de Costos ({currentState})</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead>
                    <tr className="bg-bg-alt/60 text-[10px] uppercase text-text-tertiary tracking-wide border-b border-border">
                      <th className="px-4 py-2.5">Tipo</th>
                      <th className="px-4 py-2.5">Descripción</th>
                      <th className="px-4 py-2.5 text-right">Monto</th>
                    </tr>
                  </thead>
                  <tbody>
                    {bundle.costs.filter(c => c.visible_to_client).length === 0 ? (
                      <tr><td colSpan={3} className="px-4 py-6 text-center text-xs text-text-tertiary">Sin costos visibles</td></tr>
                    ) : bundle.costs.filter(c => c.visible_to_client).map(c => (
                      <tr key={c.id} className="border-b border-border/50 last:border-0 hover:bg-bg-alt/30">
                        <td className="px-4 py-2.5 text-xs font-medium text-text-secondary">{c.cost_type}</td>
                        <td className="px-4 py-2.5 text-xs text-text-secondary">{c.description}</td>
                        <td className="px-4 py-2.5 text-xs font-semibold text-right">
                          {c.currency} ${Number(c.amount).toLocaleString("en-US", { minimumFractionDigits: 2 })}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            <div className="bg-surface border border-border rounded-xl p-5 shadow-sm">
              <h3 className="text-sm font-semibold text-text-primary mb-4">Registro de Pagos</h3>
              <PortalPagosTab expedienteMeta={portalMeta} />
            </div>
          </div>

          {/* Right: Credit + Events */}
          <div>
            <RightPanel bundle={bundle} expedienteId={expedienteId} isAdmin={false} onRefresh={() => fetchBundle(true)} />
          </div>
        </div>
      )}

      {/* ─── Modals ────────────────────────────────────────────────────── */}
      {activeModal?.commandKey === "C2" ? (
        <CreateProformaModal
          open={true}
          expedienteId={expedienteId}
          brandSlug={bundle.expediente.brand_slug}
          orphanLines={(bundle.product_lines || []).filter(l => l.proforma_id === null)}
          onClose={() => setActiveModal(null)}
          onRefresh={() => fetchBundle(true)}
        />
      ) : activeModal && activeModal.commandKey !== "VIEW" && (
        <ArtifactModal
          open={true}
          expedienteId={expedienteId}
          commandKey={activeModal.commandKey}
          artifact={activeModal.artifact}
          onClose={() => setActiveModal(null)}
          onSuccess={() => { setActiveModal(null); fetchBundle(true); }}
          isAdmin={isAdmin}
          builderContext={builderContext}
        />
      )}

      {reassignLineId && (
        <ReassignLineModal
          open={true}
          expedienteId={expedienteId}
          lineId={reassignLineId}
          proformas={(bundle.artifacts || []).filter(a => a.artifact_type === "ART-02")}
          onClose={() => setReassignLineId(null)}
          onSuccess={() => { setReassignLineId(null); fetchBundle(true); }}
        />
      )}
    </div>
  );
}
