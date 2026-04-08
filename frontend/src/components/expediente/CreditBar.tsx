"use client";

/**
 * S25-10 — CreditBar actualizada con payment_coverage + coverage_pct (SSOT compute_coverage).
 * Tiered: CEO ve amount + desglose; CLIENT ve solo barra + estado.
 * Usa compute_coverage() enums: 'none' | 'partial' | 'complete'.
 */

import { cn } from "@/lib/utils";
import { ShieldCheck, ShieldAlert, Shield, TrendingUp } from "lucide-react";

type CoverageState = "none" | "partial" | "complete";

interface Props {
  /** Del API: total pagado con payment_status='credit_released' */
  totalReleased?: number;
  /** Del API: total pedido (precio expediente) */
  expedienteTotal?: number;
  /** compute_coverage() SSOT: 'none' | 'partial' | 'complete' */
  paymentCoverage?: CoverageState;
  /** compute_coverage() SSOT: 0.00–100.00 */
  coveragePct?: number;
  /** credit_exposure del expediente */
  creditExposure?: number;
  /** credit_released flag */
  creditReleased?: boolean;
  /** CEO ve detalle de montos */
  isCeo?: boolean;
  /** Modo compacto para uso en listados */
  compact?: boolean;
}

const COVERAGE_CONFIG: Record<
  CoverageState,
  { label: string; barColor: string; icon: React.ReactNode; textColor: string; bgColor: string }
> = {
  none: {
    label: "Sin pagos liberados",
    barColor: "bg-gray-200",
    icon: <Shield className="w-4 h-4" />,
    textColor: "text-gray-500",
    bgColor: "bg-gray-50",
  },
  partial: {
    label: "Cobertura parcial",
    barColor: "bg-amber-400",
    icon: <ShieldAlert className="w-4 h-4" />,
    textColor: "text-amber-700",
    bgColor: "bg-amber-50",
  },
  complete: {
    label: "Cobertura completa",
    barColor: "bg-emerald-500",
    icon: <ShieldCheck className="w-4 h-4" />,
    textColor: "text-emerald-700",
    bgColor: "bg-emerald-50",
  },
};

const fmt = (n: number) =>
  `$${n.toLocaleString("es-CR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

export default function CreditBar({
  totalReleased = 0,
  expedienteTotal,
  paymentCoverage = "none",
  coveragePct = 0,
  creditExposure,
  creditReleased = false,
  isCeo = false,
  compact = false,
}: Props) {
  const cfg = COVERAGE_CONFIG[paymentCoverage];
  const pct = Math.min(100, Math.max(0, coveragePct));

  if (compact) {
    return (
      <div className="space-y-1">
        <div className="flex items-center justify-between text-xs">
          <span className={cn("font-semibold", cfg.textColor)}>{cfg.label}</span>
          <span className="tabular-nums text-[var(--color-text-tertiary)]">{pct.toFixed(0)}%</span>
        </div>
        <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
          <div
            className={cn("h-full rounded-full transition-all duration-500", cfg.barColor)}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
    );
  }

  return (
    <div className={cn("rounded-xl border p-4 space-y-3", cfg.bgColor, "border-[var(--color-border)]")}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={cfg.textColor}>{cfg.icon}</span>
          <span className={cn("text-sm font-semibold", cfg.textColor)}>{cfg.label}</span>
        </div>
        <div className="flex items-center gap-1.5">
          {creditReleased && (
            <span className="text-xs bg-emerald-100 text-emerald-700 border border-emerald-200 rounded-full px-2.5 py-0.5 font-semibold flex items-center gap-1">
              <TrendingUp className="w-3 h-3" />
              Crédito liberado
            </span>
          )}
          <span className={cn("text-lg font-bold tabular-nums", cfg.textColor)}>
            {pct.toFixed(1)}%
          </span>
        </div>
      </div>

      {/* Progress bar */}
      <div className="h-3 bg-white/60 rounded-full overflow-hidden border border-[var(--color-border)]">
        <div
          className={cn(
            "h-full rounded-full transition-all duration-700 ease-out",
            cfg.barColor
          )}
          style={{ width: `${pct}%` }}
        />
      </div>

      {/* CEO detail */}
      {isCeo && (
        <dl className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-1">
          <div>
            <dt className="text-[10px] uppercase tracking-wider text-[var(--color-text-tertiary)] mb-0.5">
              Liberado
            </dt>
            <dd className="text-sm font-bold text-emerald-700 tabular-nums">
              {fmt(totalReleased)}
            </dd>
          </div>
          {expedienteTotal !== undefined && (
            <div>
              <dt className="text-[10px] uppercase tracking-wider text-[var(--color-text-tertiary)] mb-0.5">
                Total pedido
              </dt>
              <dd className="text-sm font-semibold text-[var(--color-text-primary)] tabular-nums">
                {fmt(expedienteTotal)}
              </dd>
            </div>
          )}
          {creditExposure !== undefined && (
            <div>
              <dt className="text-[10px] uppercase tracking-wider text-[var(--color-text-tertiary)] mb-0.5">
                Exposición
              </dt>
              <dd
                className={cn(
                  "text-sm font-semibold tabular-nums",
                  creditExposure > 0
                    ? "text-amber-700"
                    : "text-emerald-700"
                )}
              >
                {fmt(creditExposure)}
              </dd>
            </div>
          )}
        </dl>
      )}
    </div>
  );
}
