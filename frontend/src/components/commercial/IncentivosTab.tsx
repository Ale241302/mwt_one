"use client";

/**
 * S23-14 — IncentivosTab
 *
 * Tab del Portal del Cliente (ClientConsole).
 * REGLAS DE SEGURIDAD:
 *  - NUNCA mostrar: rebate_value, accrued_rebate, accrued_amount,
 *    threshold_amount, threshold_units, ni comisiones.
 *  - Solo consume RebateProgressPortalSerializer fields:
 *    id, program_name, period, threshold_type, progress_percentage, threshold_met.
 *  - Scoping por subsidiary del usuario lo hace el backend — el frontend
 *    no filtra ni aplica lógica de subsidiaries.
 */

import { useState, useEffect, useCallback } from "react";
import { Gift, RefreshCw } from "lucide-react";
import api from "@/lib/api";
import { RebateProgressBar, type RebateProgress } from "./RebateProgressBar";

export function IncentivosTab() {
  const [progresses, setProgresses] = useState<RebateProgress[]>([]);
  const [loading, setLoading]       = useState(true);
  const [error, setError]           = useState<string | null>(null);

  const fetchProgress = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get("/commercial/portal/rebate-progress/");
      setProgresses(res.data?.results ?? res.data ?? []);
    } catch (e: any) {
      // Si es 403, el usuario no tiene subsidiary asignado — mostrar mensaje neutro
      setError("No hay incentivos disponibles para tu cuenta en este momento.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchProgress(); }, [fetchProgress]);

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-navy flex items-center gap-2">
            <Gift size={16} className="text-brand" />
            Mis Incentivos
          </h3>
          <p className="text-xs text-text-tertiary mt-0.5">
            Progreso de tus programas de rebate activos.
          </p>
        </div>
        <button onClick={fetchProgress} className="btn btn-sm btn-ghost p-2" title="Refrescar">
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
        </button>
      </div>

      {/* Error state */}
      {error && !loading && (
        <div className="card p-8 text-center text-text-tertiary">
          <Gift size={36} className="mx-auto mb-3 opacity-20" />
          <p className="text-sm">{error}</p>
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="space-y-3">
          {[1, 2].map(i => (
            <div key={i} className="card p-4 animate-pulse space-y-3">
              <div className="h-3 bg-gray-200 rounded w-1/3" />
              <div className="h-2 bg-gray-100 rounded w-full" />
            </div>
          ))}
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && progresses.length === 0 && (
        <div className="card p-10 text-center text-text-tertiary">
          <Gift size={40} className="mx-auto mb-3 opacity-20" />
          <p className="text-sm font-medium">Sin programas de incentivo activos</p>
          <p className="text-xs mt-1">
            Cuando tu cuenta tenga programas de rebate asignados, aparecerán aquí.
          </p>
        </div>
      )}

      {/* Progress bars — threshold_type: amount, units, none */}
      {!loading && !error && progresses.length > 0 && (
        <div className="space-y-3">
          {progresses.map(p => (
            <RebateProgressBar key={p.id} progress={p} />
          ))}
        </div>
      )}

      {/* Disclaimer — S23-15 check: nunca exponer montos sensibles */}
      {!loading && !error && progresses.length > 0 && (
        <p className="text-[10px] text-text-tertiary text-center pt-2">
          El progreso mostrado es orientativo. Los valores finales son determinados por MWT al cierre del período.
        </p>
      )}
    </div>
  );
}
