"use client";

/**
 * S23-14 — RebateProgressBar
 *
 * REGLAS DE SEGURIDAD:
 * - NUNCA mostrar: rebate_value, accrued_rebate, accrued_amount,
 *   threshold_amount, threshold_units, ni datos de comisiones.
 * - Solo consume los campos del RebateProgressPortalSerializer:
 *   id, program_name, period, threshold_type, progress_percentage, threshold_met.
 *
 * Soporta los 3 threshold_type:
 *   - amount → barra con progress_percentage del servidor
 *   - units  → barra con progress_percentage del servidor
 *   - none   → barra 100% siempre (threshold no aplica)
 */

export interface RebateProgress {
  id: string;
  program_name: string;
  period: { start: string | null; end: string | null };
  threshold_type: "amount" | "units" | "none";
  progress_percentage: number;
  threshold_met: boolean;
}

interface Props {
  progress: RebateProgress;
}

const THRESHOLD_LABEL: Record<string, string> = {
  amount: "Por monto",
  units:  "Por unidades",
  none:   "Sin threshold",
};

export function RebateProgressBar({ progress }: Props) {
  const pct = progress.threshold_type === "none" ? 100 : Math.min(progress.progress_percentage, 100);
  const met = progress.threshold_type === "none" ? true : progress.threshold_met;

  const barColor = met
    ? "bg-green-500"
    : pct >= 75
    ? "bg-brand"
    : pct >= 40
    ? "bg-amber-400"
    : "bg-gray-300";

  return (
    <div className="card p-4 space-y-3">
      {/* Program header */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-bold text-navy">{progress.program_name}</p>
          {progress.period.start && (
            <p className="text-[10px] text-text-tertiary mt-0.5">
              {progress.period.start} → {progress.period.end ?? "en curso"}
            </p>
          )}
        </div>
        <div className="text-right">
          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold ${
            met ? "bg-green-50 text-green-700" : "bg-gray-100 text-text-tertiary"
          }`}>
            {met ? "✓ Alcanzado" : "En progreso"}
          </span>
        </div>
      </div>

      {/* Progress bar */}
      <div>
        <div className="flex items-center justify-between mb-1">
          <span className="text-[10px] text-text-tertiary">
            {THRESHOLD_LABEL[progress.threshold_type] ?? progress.threshold_type}
          </span>
          <span className="text-[10px] font-bold text-navy">
            {progress.threshold_type === "none" ? "N/A" : `${pct}%`}
          </span>
        </div>
        <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
          <div
            className={`h-2 rounded-full transition-all duration-500 ${barColor}`}
            style={{ width: `${pct}%` }}
            role="progressbar"
            aria-valuenow={pct}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`Progreso ${progress.program_name}: ${pct}%`}
          />
        </div>
      </div>
    </div>
  );
}
