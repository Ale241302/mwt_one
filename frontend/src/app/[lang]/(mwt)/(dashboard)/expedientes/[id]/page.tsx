"use client";
/**
 * S10-03 — Detalle Expediente con acordeón de artefactos.
 * S19-12 — Barrido hex: todos los colores reemplazados por CSS vars.
 * S21    — isAdmin desde bundle.is_admin (is_superuser Django) → panel admin.
 * FIX-2026-04-08  — expedienteId con triple fallback.
 * S25 WIRING      — conecta PagosSection, CreditBar (S25-10), DeferredPricePanel,
 *                   FamilyBanner y PortalPagosTab al detalle del expediente.
 * FIX-2026-04-08b — CostTable recibe costs desde el bundle; CreditBar desde credit_snapshot.
 * REDESIGN-2026-04-16 — Layout renovado: vista admin (3col) vs vista cliente (sidebar crédito circular).
 */
import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft, RefreshCw, AlertTriangle, Lock,
  CheckCircle, XCircle, ArrowRight, Truck,
  Package, Info, Download, Eye, EyeOff
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
  MINT: "bg-emerald-50 text-emerald-700 border-emerald-200",
  AMBER: "bg-amber-50 text-amber-700 border-amber-200",
  RED: "bg-red-50 text-red-700 border-red-200",
};

const CREDIT_BAND_RING = {
  MINT: "#059669",
  AMBER: "#d97706",
  RED: "#dc2626",
};

const STATE_TO_ADVANCE_COMMAND: Record<string, string> = {
  'REGISTRO': 'C5',
  'PRODUCCION': 'C11B',
  'PREPARACION': 'C10',
  'DESPACHO': 'C11',
  'TRANSITO': 'C12',
  'EN_DESTINO': 'C14',
};

// ─── Credit Ring (for client view) ────────────────────────────────────────────

function CreditRing({ days, band }: { days: number; band: "MINT" | "AMBER" | "RED" }) {
  const r = 44;
  const circ = 2 * Math.PI * r;
  // 0 = full credit (mint), 90 = red
  const pct = Math.min(1, days / 90);
  const dash = circ * (1 - pct);
  const color = CREDIT_BAND_RING[band];

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width="120" height="120" viewBox="0 0 120 120">
        <circle cx="60" cy="60" r={r} fill="none" stroke="var(--border)" strokeWidth="10" />
        <circle
          cx="60" cy="60" r={r}
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeDasharray={circ}
          strokeDashoffset={dash}
          strokeLinecap="round"
          transform="rotate(-90 60 60)"
          style={{ transition: "stroke-dashoffset 0.8s ease" }}
        />
        <text x="60" y="56" textAnchor="middle" fontSize="22" fontWeight="bold" fill="currentColor" className="fill-[var(--text-primary)]">
          {days}
        </text>
        <text x="60" y="72" textAnchor="middle" fontSize="10" fill="currentColor" className="fill-[var(--text-tertiary)]">
          Días
        </text>
        <text x="60" y="84" textAnchor="middle" fontSize="9" fill="currentColor" className="fill-[var(--text-tertiary)]">
          Restantes
        </text>
      </svg>
    </div>
  );
}

// ─── Timeline Bar ────────────────────────────────────────────────────────────

function TimelineBar({ currentState }: { currentState: string }) {
  return (
    <div className="bg-surface border border-border rounded-xl px-4 py-3 overflow-x-auto">
      <div className="flex items-center min-w-max gap-0">
        {CANONICAL_STATES.map((state, idx) => {
          const stateIdx = CANONICAL_STATES.indexOf(state as any);
          const curIdx = CANONICAL_STATES.indexOf(currentState as any);
          const isPast = stateIdx < curIdx;
          const isCurrent = state === currentState;
          const isLocked = stateIdx > curIdx;
          return (
            <div key={state} className="flex items-center">
              <div className={cn(
                "flex items-center justify-center h-9 px-4 text-[11px] font-semibold whitespace-nowrap transition-all",
                idx === 0 ? "rounded-l-full" : "",
                idx === CANONICAL_STATES.length - 1 ? "rounded-r-full" : "",
                isPast
                  ? "bg-[#1a6b5a] text-white"
                  : isCurrent
                  ? "bg-[#1a3a32] text-white font-bold"
                  : "bg-bg-alt text-text-tertiary"
              )}>
                {isPast && <span className="mr-1.5 text-white/80">✓</span>}
                {isLocked && !isCurrent && <Lock size={10} className="mr-1 opacity-40" />}
                {state}
              </div>
              {idx < CANONICAL_STATES.length - 1 && (
                <div className={cn(
                  "w-0 h-0",
                  "border-t-[18px] border-b-[18px] border-l-[12px]",
                  "border-t-transparent border-b-transparent",
                  isPast ? "border-l-[#1a6b5a]" : isCurrent ? "border-l-[#1a3a32]" : "border-l-bg-alt"
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
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div className="bg-surface border border-border rounded-xl p-4">
        <p className="text-[11px] text-text-tertiary uppercase tracking-wide mb-0.5">Estado pago</p>
        <div className="flex items-center gap-2">
          <p className="text-lg font-bold text-text-primary capitalize">
            {expediente.payment_status === "PAID" ? "Pagado"
              : expediente.payment_status === "PARTIAL" ? "Parcial"
              : expediente.payment_status ?? "—"}
          </p>
          {expediente.payment_status === "PAID" && <CheckCircle size={14} className="text-emerald-500" />}
        </div>
      </div>
      <div className="bg-surface border border-border rounded-xl p-4">
        <p className="text-[11px] text-text-tertiary uppercase tracking-wide mb-0.5">Artefactos</p>
        <p className="text-3xl font-bold text-text-primary">{artifactsCount}</p>
      </div>
      <div className="bg-surface border border-border rounded-xl p-4">
        <p className="text-[11px] text-text-tertiary uppercase tracking-wide mb-0.5">Costo Total</p>
        <p className="text-lg font-bold text-text-primary">
          ${Number(expediente.total_cost || 0).toLocaleString("en-US", { minimumFractionDigits: 2 })}
        </p>
      </div>
      <div className={cn("border rounded-xl p-4", creditCls)}>
        <p className="text-[11px] uppercase tracking-wide mb-0.5 font-medium">Crédito ({creditBand})</p>
        <p className="text-lg font-bold">{creditDays} días restantes</p>
      </div>
    </div>
  );
}

// ─── CLIENT KPI Row (shows Estado de Crédito differently) ─────────────────────

function ClientKPIRow({ expediente, artifactsCount }: {
  expediente: ExpedienteBundle["expediente"];
  artifactsCount: number;
}) {
  return (
    <div className="grid grid-cols-3 gap-4">
      <div className="bg-surface border border-border rounded-xl p-4">
        <p className="text-[11px] text-text-tertiary uppercase tracking-wide mb-0.5">Estado pago</p>
        <p className="text-lg font-bold text-text-primary capitalize">
          {expediente.payment_status === "PAID" ? "Pagado"
            : expediente.payment_status === "PARTIAL" ? "Parcial"
            : expediente.payment_status ?? "—"}
        </p>
      </div>
      <div className="bg-surface border border-border rounded-xl p-4">
        <p className="text-[11px] text-text-tertiary uppercase tracking-wide mb-0.5">Artefactos</p>
        <p className="text-3xl font-bold text-text-primary">{artifactsCount}</p>
      </div>
      <div className="bg-surface border border-border rounded-xl p-4">
        <p className="text-[11px] text-text-tertiary uppercase tracking-wide mb-0.5">Costo Total</p>
        <p className="text-lg font-bold text-text-primary">
          ${Number(expediente.total_cost || 0).toLocaleString("en-US", { minimumFractionDigits: 2 })}
        </p>
      </div>
    </div>
  );
}

// ─── Artifact Phase Map ───────────────────────────────────────────────────────
// Maps artifact types to their workflow phase for grouping in client view.
const ARTIFACT_PHASE_MAP: Record<string, string> = {
  "ART-01": "REGISTRO", "ART-02": "REGISTRO",
  "ART-03": "PRODUCCION", "ART-04": "PRODUCCION",
  "ART-05": "PRODUCCION", "ART-06": "PRODUCCION",
  "ART-07": "PREPARACION", "ART-08": "PREPARACION",
  "ART-09": "PREPARACION", "ART-12": "PREPARACION",
  "ART-10": "TRANSITO", "ART-36": "TRANSITO",
  "ART-11": "EN_DESTINO", "ART-13": "EN_DESTINO",
  "ART-16": "CERRADO", "ART-19": "DESPACHO",
  "ART-22": "REGISTRO",
};

// ─── Client Documents Accordion ───────────────────────────────────────────────

function ClientDocumentsAccordion({
  artifacts,
}: {
  artifacts: ExpedienteBundle["artifacts"];
}) {
  const [openPhases, setOpenPhases] = useState<Record<string, boolean>>({ REGISTRO: true, PRODUCCION: true });

  const byPhase: Record<string, typeof artifacts> = {};
  const PHASE_ORDER = ["REGISTRO", "PRODUCCION", "PREPARACION", "DESPACHO", "TRANSITO", "EN_DESTINO", "CERRADO"];

  for (const art of artifacts) {
    const phase = ARTIFACT_PHASE_MAP[art.artifact_type] ?? "REGISTRO";
    if (!byPhase[phase]) byPhase[phase] = [];
    byPhase[phase].push(art);
  }

  const toggle = (phase: string) =>
    setOpenPhases(p => ({ ...p, [phase]: !p[phase] }));

  return (
    <div className="bg-surface border border-border rounded-xl shadow-sm overflow-hidden">
      <div className="px-5 py-4 border-b border-border">
        <h3 className="text-sm font-semibold text-text-primary">Documentos Confirmados</h3>
      </div>
      <div className="divide-y divide-border">
        {PHASE_ORDER.filter(ph => byPhase[ph]?.length).map(phase => {
          const arts = byPhase[phase] || [];
          const completed = arts.filter(a => a.status === "completed").length;
          const isOpen = openPhases[phase] ?? false;

          return (
            <div key={phase}>
              <button
                onClick={() => toggle(phase)}
                className="w-full flex items-center justify-between px-5 py-3 hover:bg-bg-alt/40 transition-colors text-left"
              >
                <span className="text-xs font-semibold text-text-secondary uppercase tracking-wide">
                  {phase}
                  {completed > 0 && (
                    <span className="ml-2 text-emerald-600 font-normal">({completed}/{arts.length})</span>
                  )}
                </span>
                <span className="text-text-tertiary">{isOpen ? "∧" : "∨"}</span>
              </button>
              {isOpen && (
                <div className="px-5 pb-4 space-y-2.5">
                  {arts.map(art => {
                    const meta = ARTIFACT_UI_REGISTRY[art.artifact_type];
                    const label = meta?.label ?? art.artifact_type;
                    const isCompleted = art.status === "completed";
                    const fileUrl = art.payload?.file_url ?? art.payload?.url ?? null;

                    return (
                      <div key={art.id} className="flex items-center justify-between gap-3">
                        <div className="flex items-center gap-2.5 flex-1 min-w-0">
                          <span className={cn(
                            "w-5 h-5 rounded-full flex-shrink-0 flex items-center justify-center",
                            isCompleted ? "bg-emerald-100" : "bg-border"
                          )}>
                            {isCompleted
                              ? <CheckCircle size={12} className="text-emerald-600" />
                              : <span className="w-2 h-2 rounded-full bg-text-tertiary" />}
                          </span>
                          <div className="min-w-0">
                            <p className={cn("text-xs font-medium truncate", isCompleted ? "text-text-primary" : "text-text-tertiary")}>
                              {label}
                            </p>
                            {art.created_at && (
                              <p className="text-[10px] text-text-tertiary">
                                {new Date(art.created_at).toLocaleDateString("es-CR", {
                                  day: "2-digit", month: "short", year: "numeric"
                                })}
                              </p>
                            )}
                            {art.payload?.proforma_number && (
                              <p className="text-[10px] text-text-tertiary font-mono mt-0.5">
                                PF: {art.payload.proforma_number}
                              </p>
                            )}
                            {art.payload?.count != null && (
                              <span className="inline-block text-[9px] bg-emerald-100 text-emerald-700 px-1.5 py-0.5 rounded mt-0.5">
                                COMPLETADO · {art.payload.count} REGISTRO{art.payload.count !== 1 ? "S" : ""}
                              </span>
                            )}
                          </div>
                        </div>
                        {fileUrl && (
                          <a
                            href={fileUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-1 text-xs text-[#1a6b5a] hover:underline font-medium flex-shrink-0"
                          >
                            <Download size={12} /> Descargar
                          </a>
                        )}
                        {isCompleted && !fileUrl && (
                          <span className="text-[10px] text-emerald-600 font-medium flex-shrink-0">✓ Listo</span>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}

        {/* Locked phases */}
        {["DESPACHO", "TRANSITO", "EN_DESTINO", "CERRADO"]
          .filter(ph => !byPhase[ph]?.length)
          .map(phase => (
            <div key={phase} className="flex items-center gap-2 px-5 py-3 text-text-tertiary">
              <Lock size={12} className="opacity-40" />
              <span className="text-xs font-semibold uppercase tracking-wide">{phase}</span>
            </div>
          ))}
      </div>
    </div>
  );
}

// ─── Admin Events Timeline ────────────────────────────────────────────────────

function EventsPanel({ events, isAdmin }: { events: any[]; isAdmin: boolean }) {
  return (
    <div className="bg-surface border border-border rounded-xl shadow-sm overflow-hidden">
      <div className="px-5 py-4 border-b border-border">
        <h3 className="text-sm font-semibold text-text-primary">
          {isAdmin ? "Historial de eventos" : "Historial de Eventos"}
        </h3>
        {!isAdmin && (
          <p className="text-[11px] text-text-tertiary">Hitos Clave del Expediente</p>
        )}
      </div>
      <div className="overflow-y-auto max-h-[480px]">
        {(!Array.isArray(events) || events.length === 0) ? (
          <div className="px-5 py-8 text-center text-sm text-text-tertiary">Sin eventos aún.</div>
        ) : (
          <div className="px-5 py-4 space-y-4">
            {events.slice(0, isAdmin ? 100 : 10).map((ev, i) => (
              <div key={ev.id ?? i} className="flex gap-3">
                <div className="flex flex-col items-center">
                  <div className={cn(
                    "w-2 h-2 rounded-full flex-shrink-0 mt-1",
                    i === 0 ? "bg-[#1a6b5a]" : "bg-border-strong"
                  )} />
                  {i < Math.min(events.length, isAdmin ? 100 : 10) - 1 && (
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
                  {isAdmin ? (
                    <>
                      <span className="text-[11px] font-mono font-semibold text-[#1a6b5a] bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-100">
                        {ev.event_type}
                      </span>
                      {ev.emitted_by && (
                        <p className="text-[10px] text-text-tertiary mt-0.5 truncate">
                          {ev.emitted_by}
                        </p>
                      )}
                    </>
                  ) : (
                    <p className="text-xs text-text-secondary">
                      {ev.event_type?.replace(".", " → ").replace(/_/g, " ") ?? "—"}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
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
  // Admin can toggle between internal (full) and client (simplified) view
  const [viewMode, setViewMode] = useState<"internal" | "client">("internal");
  const [builderContext, setBuilderContext] = useState<any[]>([]);

  useEffect(() => {
    fetchBuilderArtifacts().then(data => {
      setBuilderContext(data || []);
    }).catch(() => {});
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
        <div className="flex flex-col items-center gap-3 text-text-tertiary">
          <div className="w-8 h-8 border-2 border-[#1a6b5a] border-t-transparent rounded-full animate-spin" />
          <p className="text-sm">Cargando expediente…</p>
        </div>
      </div>
    );
  }

  if (error || !bundle) {
    return (
      <div className="flex flex-col items-center justify-center min-h-64 gap-4">
        <AlertTriangle size={40} className="text-red-400" />
        <p className="text-sm text-text-secondary">{error ?? "Expediente no encontrado."}</p>
        <button className="text-sm text-[#1a6b5a] hover:underline flex items-center gap-1" onClick={() => router.back()}>
          <ArrowLeft size={14} /> Volver
        </button>
      </div>
    );
  }

  const { expediente } = bundle;
  const expedienteId: string = expediente.id || expediente.expediente_id || id || "";
  const isAdmin = bundle.is_admin === true;
  const currentState = expediente.status === "ABIERTO" ? "REGISTRO" : expediente.status;
  const creditBand = bundle.credit_clock?.band ?? "MINT";
  const creditDays = bundle.credit_clock?.days ?? 0;
  const creditCls = CREDIT_BAND_CLASSES[creditBand];

  // The active display mode:
  // - If isAdmin → can toggle between internal (full admin) and client (simplified)
  // - If not isAdmin → always client view
  const displayMode = isAdmin ? viewMode : "client";

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
          .filter(a => a.status?.toUpperCase() === "COMPLETED")
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
      if (orphanLines.length > 0) errors.push(`${orphanLines.length} línea(s) sin proforma`);
      const proformas = (bundle.artifacts || []).filter(
        a => a.artifact_type === "ART-02" && a.status?.toUpperCase() === "COMPLETED"
      );
      const noMode = proformas.filter(p => !p.payload?.mode);
      if (noMode.length > 0) errors.push(`${noMode.length} proforma(s) sin modo`);
    }
    const gateCommand = STATE_TO_ADVANCE_COMMAND[currentState];
    const canAdvance = errors.length === 0 && !!gateCommand && hasAction(gateCommand);
    return { canAdvance, errors };
  };

  const { canAdvance, errors: advanceErrors } = calculateAdvanceValidation();
  const hasArt06 = bundle.artifacts.some(a => a.artifact_type === "ART-06" && a.status?.toUpperCase() === "COMPLETED");
  const showC11B = currentState === "DESPACHO" && hasArt06 && hasAction("C11B");

  // S25 credit snapshot
  const snap = bundle.credit_snapshot;
  const paymentCoverage = snap?.payment_coverage ?? "none";
  const coveragePct = snap?.coverage_pct ?? 0;
  const totalReleased = snap?.total_released ?? 0;
  const creditReleased = snap?.credit_released ?? false;

  const portalMeta = {
    expediente_id: expedienteId,
    payment_coverage: paymentCoverage as "none" | "partial" | "complete",
    coverage_pct: coveragePct,
    credit_released: creditReleased,
    deferred_total_price: expediente.deferred_total_price ?? null,
    deferred_visible: expediente.deferred_visible ?? false,
    total_lines_value: expediente.total_cost,
  };

  const artifactsCount = Array.isArray(bundle.artifacts) ? bundle.artifacts.length : 0;

  return (
    <div className="space-y-5 pb-10">

      {/* ─── Top Bar ────────────────────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link href={`/${lang}/expedientes`} className="p-1.5 rounded-lg hover:bg-bg-alt transition-colors text-text-tertiary hover:text-text-primary">
            <ArrowLeft size={18} />
          </Link>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-xl font-bold text-text-primary">
                {isAdmin
                  ? <>Expediente <span className="font-mono text-[#1a6b5a]">{expediente.custom_ref}</span></>
                  : <>Expediente: <span className="font-mono">{expediente.custom_ref}</span></>
                }
              </h1>
              {/* Status badge */}
              <span className={cn(
                "text-[11px] font-bold px-2.5 py-0.5 rounded-full",
                STATE_BADGE_CLASSES[expediente.status] ?? "bg-gray-100 text-gray-600"
              )}>
                {expediente.status}
              </span>
              {/* Admin badge */}
              {isAdmin && displayMode === "internal" && (
                <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-700 border border-blue-200">
                  ADMIN
                </span>
              )}
              {/* Blocked badge */}
              {expediente.is_blocked && (
                <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-red-100 text-red-700 border flex items-center gap-1">
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
          {/* Toggle Interna/Cliente — only for admin */}
          {isAdmin && (
            <div className="flex items-center gap-2 bg-bg-alt border border-border rounded-lg px-3 py-1.5">
              <span className="text-xs text-text-tertiary font-medium">
                {viewMode === "internal" ? "Interna" : "Cliente"}
              </span>
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
              <span className="text-xs text-text-secondary font-medium">
                {viewMode === "internal" ? "/ Cliente" : "/ Interna"}
              </span>
            </div>
          )}

          {/* Admin action buttons (internal view only) */}
          {isAdmin && displayMode === "internal" && (
            <>
              {hasAction("C17") && !expediente.is_blocked && (
                <button
                  className="px-3 py-1.5 text-xs border border-red-300 text-red-600 rounded-lg hover:bg-red-50 transition-colors"
                  onClick={() => setActiveModal({ commandKey: "C17" })}
                >
                  <Lock size={12} className="inline mr-1" /> Bloquear
                </button>
              )}
              {hasAction("C18") && expediente.is_blocked && (
                <button
                  className="px-3 py-1.5 text-xs border border-emerald-300 text-emerald-600 rounded-lg hover:bg-emerald-50 transition-colors"
                  onClick={() => setActiveModal({ commandKey: "C18" })}
                >
                  <Lock size={12} className="inline mr-1" /> Desbloquear
                </button>
              )}
              <button
                className="px-3 py-1.5 text-xs border border-border text-text-secondary rounded-lg hover:bg-bg-alt transition-colors"
                onClick={() => setActiveModal({ commandKey: "C15" })}
              >
                + Costo
              </button>
              <button
                className="px-4 py-1.5 text-xs bg-[#1a6b5a] hover:bg-[#155448] text-white rounded-lg font-medium transition-all shadow-sm active:scale-95"
                onClick={() => setActiveModal({ commandKey: "C21" })}
              >
                + Pago
              </button>
              {hasAction("C16") && (
                <button
                  className="px-3 py-1.5 text-xs border border-red-300 text-red-600 rounded-lg hover:bg-red-50 transition-colors"
                  onClick={() => setActiveModal({ commandKey: "C16" })}
                >
                  Cancelar
                </button>
              )}
            </>
          )}

          <button
            className="p-1.5 border border-border rounded-lg hover:bg-bg-alt transition-colors text-text-tertiary hover:text-text-primary"
            onClick={() => fetchBundle(true)}
            disabled={refreshing}
          >
            <RefreshCw size={15} className={cn(refreshing && "animate-spin")} />
          </button>
        </div>
      </div>

      {/* ─── Family Banner ───────────────────────────────────────────────────── */}
      {(expediente.parent_expediente || (expediente.child_expedientes && expediente.child_expedientes.length > 0)) && (
        <FamilyBanner
          currentId={expedienteId}
          parentExpediente={expediente.parent_expediente ?? null}
          childExpedientes={expediente.child_expedientes ?? []}
          isInvertedChild={expediente.is_inverted_child ?? false}
          lang={lang}
        />
      )}

      {/* ─── Timeline ───────────────────────────────────────────────────────── */}
      <TimelineBar currentState={currentState} />

      {/* ─── KPI Row ────────────────────────────────────────────────────────── */}
      {displayMode === "internal" ? (
        <KPIRow
          expediente={expediente}
          artifactsCount={artifactsCount}
          creditDays={creditDays}
          creditBand={creditBand}
        />
      ) : (
        <ClientKPIRow expediente={expediente} artifactsCount={artifactsCount} />
      )}

      {/* ─── CreditBar (solo vista interna admin) ───────────────────────────── */}
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

      {/* ═══════════════════════════════════════════════════════════════════════
          LAYOUT ADMIN (vista interna)
      ══════════════════════════════════════════════════════════════════════ */}
      {displayMode === "internal" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {/* ── Left: Artifacts Accordion ── */}
          <div className="space-y-4">
            <GateMessage requiredToAdvance={advanceErrors} currentState={currentState} />

            {!canAdvance && advanceErrors.length > 0 && (
              <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start gap-3">
                <Info size={16} className="text-amber-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-xs font-semibold text-amber-900 mb-1">Pendiente para avanzar</p>
                  <div className="flex flex-wrap gap-1.5">
                    {advanceErrors.map((err, i) => (
                      <span key={i} className="text-[10px] px-2 py-0.5 bg-amber-100 text-amber-700 rounded-full border border-amber-200">
                        {err}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {canAdvance && (
              <button
                className="w-full bg-[#1a6b5a] hover:bg-[#155448] text-white rounded-xl py-2.5 text-sm font-semibold flex items-center justify-center gap-2 shadow-sm transition-all active:scale-95"
                onClick={() => setActiveModal({ commandKey: STATE_TO_ADVANCE_COMMAND[currentState]! })}
              >
                Avanzar a la siguiente fase <ArrowRight size={15} />
              </button>
            )}

            {showC11B && (
              <button
                className="w-full border border-sky-300 text-sky-700 rounded-xl py-2.5 text-sm font-semibold flex items-center justify-center gap-2 hover:bg-sky-50 transition-colors"
                onClick={() => setActiveModal({ commandKey: "C11B" })}
              >
                <Truck size={15} /> Confirmar Salida (China)
              </button>
            )}

            {/* Accordion de artefactos */}
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
              builderContext={builderContext}
            />
          </div>

          {/* ── Center: Proformas + CostTable + PagosSection ── */}
          <div className="space-y-4">
            {/* Proformas (REGISTRO state) */}
            {bundle.product_lines && bundle.product_lines.length > 0 && (
              <section className="space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-sm font-semibold text-text-primary flex items-center gap-2">
                    <Package size={15} className="text-[#1a6b5a]" /> Proformas y Líneas
                  </h2>
                  {currentState === "REGISTRO" && hasAction("C3") && (
                    <button
                      className="text-xs text-[#1a6b5a] hover:underline font-medium flex items-center gap-1"
                      onClick={() => setActiveModal({ commandKey: "C3" })}
                    >
                      + Crear Proforma
                    </button>
                  )}
                </div>
                {(() => {
                  const proformas = (bundle.artifacts || []).filter(a => a.artifact_type === "ART-02");
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
                          isEditable={currentState === "REGISTRO"}
                        />
                      ))}
                      {orphanLines.length > 0 && (
                        <div className="border border-dashed border-red-300 bg-red-50/10 rounded-xl overflow-hidden">
                          <div className="px-4 py-3 flex items-center justify-between bg-red-50/20">
                            <span className="text-xs font-semibold text-red-700 flex items-center gap-1.5">
                              <AlertTriangle size={13} /> {orphanLines.length} línea(s) sin proforma
                            </span>
                          </div>
                          <div className="px-4 py-2 space-y-1">
                            {orphanLines.map(line => (
                              <div key={line.id} className="flex items-center justify-between text-xs py-1">
                                <span className="text-red-600">{line.product_name}</span>
                                <button
                                  className="text-red-700 hover:underline font-medium"
                                  onClick={() => setReassignLineId(line.id)}
                                >
                                  Asignar
                                </button>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </>
                  );
                })()}
              </section>
            )}

            {/* CostTable */}
            <CostTable
              expedienteId={expedienteId}
              costs={bundle.costs}
              onRefresh={() => fetchBundle(true)}
            />

            {/* PagosSection */}
            <div className="bg-surface border border-border rounded-xl overflow-hidden">
              <PagosSection
                expedienteId={expedienteId}
                isCeo={isAdmin}
                onCreditRefresh={() => fetchBundle(true)}
              />
            </div>
          </div>

          {/* ── Right: DeferredPrice + Notifications + Events ── */}
          <div className="space-y-4">
            {isAdmin && (
              <DeferredPricePanel
                expedienteId={expedienteId}
                deferredTotalPrice={expediente.deferred_total_price ?? null}
                deferredVisible={expediente.deferred_visible ?? false}
                isCeo={true}
                onUpdate={() => fetchBundle(true)}
              />
            )}
            {isAdmin && (
              <div className="bg-surface border border-border rounded-xl p-4">
                <NotificationLogsSection expedienteId={expedienteId} isCeo={isAdmin} />
              </div>
            )}
            <EventsPanel events={bundle.events} isAdmin={true} />
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════════════════
          LAYOUT CLIENTE (simplified)
      ══════════════════════════════════════════════════════════════════════ */}
      {displayMode === "client" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {/* ── Left: Documentos Confirmados ── */}
          <div className="space-y-4">
            <ClientDocumentsAccordion artifacts={bundle.artifacts} />
          </div>

          {/* ── Center: Costos + Pagos ── */}
          <div className="space-y-4">
            {/* Cost table (client view: no VIS.CLIENT column, no add button) */}
            <div className="bg-surface border border-border rounded-xl overflow-hidden">
              <div className="px-5 py-4 border-b border-border bg-[#1a3a32]">
                <h3 className="text-sm font-semibold text-white">
                  Detalle de Costos Facturados ({currentState})
                </h3>
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
                      <tr>
                        <td colSpan={3} className="px-4 py-6 text-center text-xs text-text-tertiary">
                          Sin costos visibles
                        </td>
                      </tr>
                    ) : bundle.costs.filter(c => c.visible_to_client).map(c => (
                      <tr key={c.id} className="border-b border-border/50 last:border-0 hover:bg-bg-alt/30 transition-colors">
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

            {/* Pagos Section — cliente view via PortalPagosTab */}
            <div className="bg-surface border border-border rounded-xl p-5">
              <h3 className="text-sm font-semibold text-text-primary mb-4">Registro de Pagos</h3>
              <PortalPagosTab expedienteMeta={portalMeta} />
            </div>
          </div>

          {/* ── Right: Credit Ring + Deferred + Events ── */}
          <div className="space-y-4">
            {/* Estado de Crédito */}
            <div className="bg-surface border border-border rounded-xl p-5 flex flex-col items-center">
              <h3 className="text-sm font-semibold text-text-primary mb-4 self-start">Estado de Crédito</h3>
              <CreditRing days={creditDays} band={creditBand} />
            </div>

            {/* Próximo Vencimiento Diferido */}
            {expediente.deferred_total_price != null && expediente.deferred_total_price > 0 && (
              <div className="bg-surface border border-border rounded-xl p-5">
                <h3 className="text-sm font-semibold text-text-primary mb-3">Próximo Vencimiento Diferido</h3>
                <p className="text-xs text-text-secondary">
                  Monto: <span className="font-semibold text-text-primary">
                    ${Number(expediente.deferred_total_price).toLocaleString("en-US", { minimumFractionDigits: 2 })}
                  </span>
                </p>
                <p className="text-xs text-text-secondary mt-1">
                  Fecha: <span className="font-semibold text-text-primary">30 días restantes</span>
                </p>
              </div>
            )}

            <EventsPanel events={bundle.events} isAdmin={false} />
          </div>
        </div>
      )}

      {/* ─── Modals ─────────────────────────────────────────────────────────── */}
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
