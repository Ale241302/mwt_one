"use client";
/**
 * S10-03 — Detalle Expediente con acordeón de artefactos.
 * Refactor del bundle view para incluir ExpedienteAccordion.
 */
import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft, RefreshCw, AlertTriangle, Lock, Unlock,
  CheckCircle, XCircle, Clock
} from "lucide-react";
import { cn } from "@/lib/utils";
import api from "@/lib/api";
import ExpedienteAccordion from "@/components/expediente/ExpedienteAccordion";

// ─── Types ─────────────────────────────────────────────────────────────────────
interface ExpedienteBundle {
  expediente_id: string;
  status: string;
  payment_status: string;
  is_blocked: boolean;
  brand?: string;
  client?: { legal_name: string; entity_id: string };
  credit_band?: "MINT" | "AMBER" | "RED";
  credit_days_elapsed?: number;
  artifacts: Array<{
    artifact_id: string;
    artifact_type: string;
    status: string;
    created_at: string;
    payload: Record<string, unknown>;
  }>;
  available_actions: string[];
  events: Array<{
    id: string;
    event_type: string;
    occurred_at: string;
    emitted_by: string;
    payload: Record<string, unknown>;
  }>;
}

const STATUS_COLORS: Record<string, string> = {
  ABIERTO:    "bg-[#EFF6FF] text-[#1D4ED8]",
  EN_PROCESO: "bg-[#FFF7ED] text-[#B45309]",
  CERRADO:    "bg-[#F0FAF6] text-[#0E8A6D]",
  CANCELADO:  "bg-[#FEF2F2] text-[#DC2626]",
  BLOQUEADO:  "bg-[#F1F5F9] text-[#475569]",
};

const CREDIT_BAND_COLORS = {
  MINT:  "bg-[#F0FAF6] text-[#0E8A6D] border-[#BBF7D0]",
  AMBER: "bg-[#FFF7ED] text-[#B45309] border-[#FDE68A]",
  RED:   "bg-[#FEF2F2] text-[#DC2626] border-[#FECACA]",
};

// ─── Page ─────────────────────────────────────────────────────────────────────
export default function ExpedienteDetailPage() {
  const params = useParams();
  const router = useRouter();
  const lang = (params?.lang as string) || "es";
  const id = params?.id as string;

  const [bundle, setBundle] = useState<ExpedienteBundle | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchBundle = useCallback(async (quiet = false) => {
    if (!quiet) setLoading(true);
    else setRefreshing(true);
    setError(null);
    try {
      const res = await api.get(`/ui/expedientes/${id}/`);
      setBundle(res.data);
    } catch (e: unknown) {
      const msg = (e as { message?: string })?.message ?? "Error al cargar expediente";
      setError(msg);
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

  const creditCls = CREDIT_BAND_COLORS[bundle.credit_band ?? "MINT"];

  return (
    <div className="space-y-6">
      {/* ─── Top bar ─── */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link href={`/${lang}/expedientes`} className="btn btn-sm btn-ghost p-2">
            <ArrowLeft size={16} />
          </Link>
          <div>
            <h1 className="page-title">Expediente #{String(bundle.expediente_id).slice(0, 8)}</h1>
            <p className="page-subtitle">{bundle.client?.legal_name ?? "—"} · {bundle.brand ?? "—"}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            className="btn btn-sm btn-ghost"
            onClick={() => fetchBundle(true)}
            disabled={refreshing}
            aria-label="Actualizar"
          >
            <RefreshCw size={15} className={cn(refreshing && "animate-spin")} />
          </button>
          {/* Status badge */}
          <span className={cn(
            "badge text-xs font-semibold px-3 py-1",
            STATUS_COLORS[bundle.status] ?? "bg-bg text-text-secondary"
          )}>
            {bundle.status}
          </span>
          {bundle.is_blocked && (
            <span className="badge bg-[#FEF2F2] text-[#DC2626] flex items-center gap-1 text-xs">
              <Lock size={11} /> Bloqueado
            </span>
          )}
        </div>
      </div>

      {/* ─── KPI row ─── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card p-4">
          <p className="caption text-text-tertiary mb-1">Estado pago</p>
          <p className="heading-sm font-semibold">{bundle.payment_status ?? "—"}</p>
        </div>
        <div className="card p-4">
          <p className="caption text-text-tertiary mb-1">Artefactos</p>
          <p className="heading-sm font-semibold">{bundle.artifacts.length}</p>
        </div>
        <div className="card p-4">
          <p className="caption text-text-tertiary mb-1">Acciones disponibles</p>
          <p className="heading-sm font-semibold">{bundle.available_actions.length}</p>
        </div>
        <div className={cn("card p-4 border", creditCls)}>
          <p className="caption mb-1">Crédito ({bundle.credit_band})</p>
          <p className="heading-sm font-semibold">{bundle.credit_days_elapsed ?? 0} días</p>
        </div>
      </div>

      {/* ─── Main content: Accordion + Events ─── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Accordion */}
        <div className="lg:col-span-2">
          <h2 className="heading-sm font-semibold mb-3 text-navy">Artefactos del expediente</h2>
          <ExpedienteAccordion
            expedienteId={bundle.expediente_id}
            artifacts={bundle.artifacts}
            availableActions={bundle.available_actions}
            onRefresh={() => fetchBundle(true)}
          />
        </div>

        {/* Event log */}
        <div>
          <h2 className="heading-sm font-semibold mb-3 text-navy">Historial de eventos</h2>
          <div className="card overflow-hidden">
            {bundle.events.length === 0 ? (
              <div className="p-6 text-center text-text-tertiary text-sm">Sin eventos aún.</div>
            ) : (
              <div className="divide-y divide-divider">
                {bundle.events.map((ev) => (
                  <div key={ev.id} className="px-4 py-3">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-mono text-[11px] font-semibold text-navy bg-brand-accent-soft px-1.5 py-0.5 rounded">
                        {ev.event_type}
                      </span>
                    </div>
                    <p className="caption text-text-tertiary">
                      {ev.emitted_by} · {ev.occurred_at ? new Date(ev.occurred_at).toLocaleString("es-CO") : "—"}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
