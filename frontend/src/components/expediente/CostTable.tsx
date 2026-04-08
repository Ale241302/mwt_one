"use client";
import React, { useEffect, useState, useCallback } from "react";
import api from "@/lib/api";
import { Loader2, AlertTriangle, Eye, EyeOff, CheckCircle, XCircle } from "lucide-react";

interface Cost {
  id: string;
  cost_type: string;
  description: string;
  amount: number;
  currency: string;
  phase: string;
  visible_to_client: boolean;
}

interface CostTableProps {
  expedienteId: string;
}

export default function CostTable({ expedienteId }: CostTableProps) {
  const [costs, setCosts] = useState<Cost[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [internalView, setInternalView] = useState(true);

  const fetchCosts = useCallback(async () => {
    // Guard: no hacer fetch si el id no está disponible aún
    if (!expedienteId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.get(`/expedientes/${expedienteId}/costs/`);
      setCosts(res.data);
    } catch (e: any) {
      setError(e.message || "Error cargando costos");
    } finally {
      setLoading(false);
    }
  }, [expedienteId]);

  useEffect(() => {
    fetchCosts();
  }, [fetchCosts]);

  const filteredCosts = internalView ? (Array.isArray(costs) ? costs : []) : (Array.isArray(costs) ? costs : []).filter(c => c.visible_to_client);

  if (loading) {
    return (
      <div className="card p-6 flex justify-center items-center">
        <Loader2 className="animate-spin text-text-tertiary" size={20} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="card p-6 flex flex-col items-center text-coral gap-2">
        <AlertTriangle size={20} />
        <p className="text-sm">{error}</p>
        <button className="btn btn-sm btn-outline mt-2" onClick={fetchCosts}>Reintentar</button>
      </div>
    );
  }

  return (
    <div className="card overflow-hidden">
      <div className="px-5 py-4 border-b border-divider flex items-center justify-between">
        <h3 className="heading-sm font-semibold text-navy">Tabla de Costos</h3>
        <button
          className="btn btn-sm btn-ghost text-xs flex items-center gap-1.5"
          onClick={() => setInternalView(!internalView)}
        >
          {internalView ? (
            <><EyeOff size={14} /> Vista Cliente</>
          ) : (
            <><Eye size={14} /> Vista Interna</>
          )}
        </button>
      </div>
      
      {(filteredCosts || []).length === 0 ? (
        <div className="p-6 text-center text-text-tertiary text-sm">
          No hay costos registrados.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-bg text-xs font-semibold text-text-secondary uppercase tracking-wider">
                <th className="px-5 py-3 border-b border-divider">Tipo</th>
                <th className="px-5 py-3 border-b border-divider">Descripción</th>
                <th className="px-5 py-3 border-b border-divider">Fase</th>
                <th className="px-5 py-3 border-b border-divider text-right">Monto</th>
                {internalView && (
                  <th className="px-5 py-3 border-b border-divider text-center">Vis. Cliente</th>
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-divider text-sm text-navy">
              {(Array.isArray(filteredCosts) ? filteredCosts : []).map(cost => (
                <tr key={cost.id} className="hover:bg-bg/50 transition-colors">
                  <td className="px-5 py-3 font-medium whitespace-nowrap">{cost.cost_type}</td>
                  <td className="px-5 py-3">{cost.description || "—"}</td>
                  <td className="px-5 py-3">
                    <span className="badge bg-slate-100 text-slate-600">{cost.phase}</span>
                  </td>
                  <td className="px-5 py-3 text-right font-mono">
                    {Number(cost.amount).toLocaleString("es-CO", { style: "currency", currency: cost.currency || "USD" })}
                  </td>
                  {internalView && (
                    <td className="px-5 py-3 text-center">
                      {cost.visible_to_client ? (
                        <CheckCircle size={14} className="text-success inline-block" />
                      ) : (
                        <XCircle size={14} className="text-text-tertiary inline-block" />
                      )}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
