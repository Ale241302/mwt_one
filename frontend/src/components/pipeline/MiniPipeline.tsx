/**
 * S9-06 — MiniPipeline
 * Barra horizontal con 6 segmentos de estado + conteo por estado
 * + sección "Próximas acciones" (pending_action por expediente).
 *
 * Uso en Dashboard:
 *   <MiniPipeline byStatus={data.by_status} nextActions={data.next_actions} />
 */
"use client";
import { cn } from "@/lib/utils";
import { PIPELINE_STATES, STATE_LABELS, CanonicalState } from "@/lib/constants/states";
import Link from "next/link";
import { ArrowRight, Zap } from "lucide-react";

// ─── Colores por estado ───────────────────────────────────────────────────────
const SEGMENT_COLORS: Record<CanonicalState, { bar: string; text: string; bg: string }> = {
  REGISTRO:    { bar: "bg-[#94A3B8]", text: "text-[#475569]", bg: "bg-[#F1F5F9]" },
  PRODUCCION:  { bar: "bg-[#60A5FA]", text: "text-[#1D4ED8]", bg: "bg-[#EFF6FF]" },
  PREPARACION: { bar: "bg-[#A78BFA]", text: "text-[#7C3AED]", bg: "bg-[#F5F3FF]" },
  DESPACHO:    { bar: "bg-[#34D399]", text: "text-[#059669]", bg: "bg-[#F0FAF6]" },
  TRANSITO:    { bar: "bg-[#FBBF24]", text: "text-[#B45309]", bg: "bg-[#FFF7ED]" },
  EN_DESTINO:  { bar: "bg-[#0E8A6D]", text: "text-[#0E8A6D]", bg: "bg-[#E6F7F3]" },
  CERRADO:     { bar: "bg-[#CBD5E1]", text: "text-[#94A3B8]", bg: "bg-[#F8FAFC]" },
  CANCELADO:   { bar: "bg-[#FCA5A5]", text: "text-[#DC2626]", bg: "bg-[#FEF2F2]" },
};

export interface ByStatusEntry {
  status: CanonicalState;
  count: number;
}

export interface NextAction {
  expediente_id: string;
  custom_ref: string;
  action: string;
  status: CanonicalState;
}

interface MiniPipelineProps {
  byStatus?: ByStatusEntry[];
  nextActions?: NextAction[];
  /** Total de expedientes activos para calcular porcentajes */
  total?: number;
  loading?: boolean;
}

export function MiniPipeline({
  byStatus = [],
  nextActions = [],
  total,
  loading = false,
}: MiniPipelineProps) {
  const activeStates = PIPELINE_STATES; // 6 estados activos
  const computedTotal =
    total ??
    byStatus.reduce((acc, s) => acc + (activeStates.includes(s.status) ? s.count : 0), 0);

  const countFor = (s: CanonicalState): number =>
    byStatus.find((b) => b.status === s)?.count ?? 0;

  // Calcular ancho proporcional de cada segmento (mínimo 4% para que siempre sea visible)
  const pctFor = (s: CanonicalState): number => {
    if (!computedTotal) return Math.floor(100 / activeStates.length);
    const raw = (countFor(s) / computedTotal) * 100;
    return Math.max(raw, countFor(s) > 0 ? 4 : 0);
  };

  if (loading) {
    return (
      <div className="rounded-[var(--radius-xl)] border border-[var(--border)] bg-[var(--surface)] p-5 space-y-4 animate-pulse">
        <div className="h-4 w-32 bg-[var(--border)] rounded" />
        <div className="h-3 w-full bg-[var(--border)] rounded-full" />
        <div className="flex gap-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-8 flex-1 bg-[var(--border)] rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-[var(--radius-xl)] border border-[var(--border)] bg-[var(--surface)] overflow-hidden">
      {/* ── Header ── */}
      <div className="flex items-center justify-between px-5 pt-4 pb-3 border-b border-[var(--divider)]">
        <div>
          <h2 className="text-sm font-semibold text-[var(--text-primary)]">Pipeline de expedientes</h2>
          <p className="text-xs text-[var(--text-tertiary)] mt-0.5">
            {computedTotal} expediente{computedTotal !== 1 ? "s" : ""} en curso
          </p>
        </div>
        <Link
          href="/expedientes"
          className="text-xs text-[var(--navy)] hover:text-[var(--mint)] font-medium flex items-center gap-1 transition-colors"
        >
          Ver pipeline <ArrowRight size={12} />
        </Link>
      </div>

      {/* ── Barra de segmentos ── */}
      <div className="px-5 pt-4">
        <div
          className="flex h-2.5 w-full rounded-full overflow-hidden gap-px bg-[var(--border)]"
          role="img"
          aria-label="Distribución de expedientes por estado"
        >
          {activeStates.map((s) => {
            const pct = pctFor(s);
            if (pct === 0) return null;
            return (
              <div
                key={s}
                className={cn("h-full transition-all duration-500", SEGMENT_COLORS[s].bar)}
                style={{ width: `${pct}%` }}
                title={`${STATE_LABELS[s]}: ${countFor(s)}`}
              />
            );
          })}
        </div>
      </div>

      {/* ── Leyenda de conteos ── */}
      <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 px-5 py-4">
        {activeStates.map((s) => {
          const count = countFor(s);
          const colors = SEGMENT_COLORS[s];
          return (
            <div
              key={s}
              className={cn(
                "rounded-lg px-2.5 py-2 text-center",
                count > 0 ? colors.bg : "bg-[var(--bg-alt)]"
              )}
            >
              <p
                className={cn(
                  "text-lg font-bold leading-none",
                  count > 0 ? colors.text : "text-[var(--text-disabled)]"
                )}
              >
                {count}
              </p>
              <p className="text-[10px] font-medium text-[var(--text-muted)] mt-0.5 truncate">
                {STATE_LABELS[s]}
              </p>
            </div>
          );
        })}
      </div>

      {/* ── Próximas acciones ── */}
      {nextActions.length > 0 && (
        <div className="border-t border-[var(--divider)] px-5 pb-4 pt-3">
          <div className="flex items-center gap-1.5 mb-2.5">
            <Zap size={13} className="text-[var(--amber)]" />
            <h3 className="text-xs font-semibold text-[var(--text-primary)] uppercase tracking-[0.5px]">
              Próximas acciones
            </h3>
          </div>
          <div className="space-y-1.5">
            {nextActions.slice(0, 5).map((na) => {
              const colors = SEGMENT_COLORS[na.status];
              return (
                <div
                  key={na.expediente_id}
                  className="flex items-center gap-3 rounded-lg px-3 py-2 bg-[var(--bg-alt)] hover:bg-[var(--surface-hover)] transition-colors"
                >
                  <span
                    className={cn(
                      "text-[10px] font-bold uppercase tracking-[0.5px] px-1.5 py-0.5 rounded flex-shrink-0",
                      colors.bg,
                      colors.text
                    )}
                  >
                    {STATE_LABELS[na.status]}
                  </span>
                  <span className="font-mono text-xs font-semibold text-[var(--navy)] flex-shrink-0">
                    {na.custom_ref}
                  </span>
                  <span className="text-xs text-[var(--text-secondary)] truncate flex-1">
                    {na.action}
                  </span>
                  <Link
                    href={`/expedientes/${na.expediente_id}`}
                    className="text-[var(--text-tertiary)] hover:text-[var(--mint)] flex-shrink-0 transition-colors"
                    aria-label={`Ver ${na.custom_ref}`}
                  >
                    <ArrowRight size={13} />
                  </Link>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
