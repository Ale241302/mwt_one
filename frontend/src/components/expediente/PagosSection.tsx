"use client";

import { useState, useEffect, useCallback } from "react";
import { CheckCircle, Clock, Plus } from "lucide-react";
import api from "@/lib/api";
import toast from "react-hot-toast";
import ModalRegistrarPago from "@/components/expediente/ModalRegistrarPago";

interface Pago {
  id: number;
  amount: number;
  currency?: string;
  status: "PENDING" | "CONFIRMED";
  payment_date?: string;
  reference?: string;
  notes?: string;
  confirmed_at?: string;
}

interface Props {
  expedienteId: number | string;
  onCreditRefresh?: () => void;
}

export default function PagosSection({ expedienteId, onCreditRefresh }: Props) {
  const [pagos, setPagos] = useState<Pago[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [confirming, setConfirming] = useState<number | null>(null);

  const fetchPagos = useCallback(async () => {
    try {
      setLoading(true);
      const res = await api.get(`expedientes/${expedienteId}/pagos/`);
      const list: Pago[] = Array.isArray(res.data) ? res.data : res.data?.results ?? [];
      setPagos(list);
    } catch {
      toast.error("Error al cargar pagos");
    } finally {
      setLoading(false);
    }
  }, [expedienteId]);

  useEffect(() => { fetchPagos(); }, [fetchPagos]);

  const handleConfirm = async (pagoId: number) => {
    setConfirming(pagoId);
    try {
      await api.patch(`expedientes/${expedienteId}/pagos/${pagoId}/confirmar/`, {});
      toast.success("Pago confirmado");
      await fetchPagos();
      onCreditRefresh?.();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      toast.error(e.response?.data?.detail ?? "Error al confirmar pago");
    } finally {
      setConfirming(null);
    }
  };

  const totalPending = pagos.filter((p) => p.status === "PENDING").reduce((s, p) => s + p.amount, 0);
  const totalConfirmed = pagos.filter((p) => p.status === "CONFIRMED").reduce((s, p) => s + p.amount, 0);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">Pagos</h3>
        <button
          type="button"
          onClick={() => setShowModal(true)}
          className="flex items-center gap-1.5 text-xs bg-[var(--color-navy)] text-white rounded-lg px-3 py-1.5 hover:opacity-80 transition-opacity"
        >
          <Plus className="w-3.5 h-3.5" /> Registrar pago
        </button>
      </div>

      {/* Summary pills */}
      <div className="flex flex-wrap gap-3">
        <div className="flex items-center gap-1.5 text-xs bg-[var(--color-bg-alt)] border border-[var(--color-border)] rounded-lg px-3 py-1.5">
          <Clock className="w-3.5 h-3.5 text-[var(--color-text-tertiary)]" />
          <span className="text-[var(--color-text-secondary)]">Pendiente:</span>
          <span className="font-semibold text-[var(--color-text-primary)]">${totalPending.toLocaleString()}</span>
        </div>
        <div className="flex items-center gap-1.5 text-xs bg-[var(--color-bg-alt)] border border-[var(--color-border)] rounded-lg px-3 py-1.5">
          <CheckCircle className="w-3.5 h-3.5 text-[var(--color-success)]" />
          <span className="text-[var(--color-text-secondary)]">Confirmado:</span>
          <span className="font-semibold text-[var(--color-text-primary)]">${totalConfirmed.toLocaleString()}</span>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center gap-2 py-4">
          <div className="w-4 h-4 border-2 border-[var(--color-navy)] border-t-transparent rounded-full animate-spin" />
          <span className="text-xs text-[var(--color-text-tertiary)]">Cargando pagos...</span>
        </div>
      ) : pagos.length === 0 ? (
        <p className="text-xs text-[var(--color-text-tertiary)] italic">Sin pagos registrados.</p>
      ) : (
        <div className="border border-[var(--color-border)] rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-[var(--color-bg-alt)]">
              <tr>
                <th className="text-left px-4 py-2.5 text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">Fecha</th>
                <th className="text-left px-4 py-2.5 text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">Monto</th>
                <th className="text-left px-4 py-2.5 text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">Ref</th>
                <th className="text-left px-4 py-2.5 text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">Estado</th>
                <th className="px-4 py-2.5" />
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--color-border)]">
              {pagos.map((pago) => (
                <tr key={pago.id} className="hover:bg-[var(--color-bg-alt)]/50 transition-colors">
                  <td className="px-4 py-3 text-[var(--color-text-secondary)] tabular-nums">
                    {pago.payment_date ?? "—"}
                  </td>
                  <td className="px-4 py-3 font-semibold text-[var(--color-text-primary)] tabular-nums">
                    ${pago.amount.toLocaleString()} {pago.currency ?? ""}
                  </td>
                  <td className="px-4 py-3 text-[var(--color-text-tertiary)] font-mono text-xs">
                    {pago.reference ?? "—"}
                  </td>
                  <td className="px-4 py-3">
                    {pago.status === "CONFIRMED" ? (
                      <span className="flex items-center gap-1 text-xs text-[var(--color-success)] font-medium">
                        <CheckCircle className="w-3.5 h-3.5" /> Confirmado
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-xs text-[var(--color-text-tertiary)]">
                        <Clock className="w-3.5 h-3.5" /> Pendiente
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {pago.status === "PENDING" && (
                      <button
                        type="button"
                        onClick={() => handleConfirm(pago.id)}
                        disabled={confirming === pago.id}
                        className="text-xs bg-[var(--color-success)]/10 text-[var(--color-success)] border border-[var(--color-success)]/30 rounded-lg px-3 py-1.5 hover:bg-[var(--color-success)]/20 disabled:opacity-50 transition-colors font-medium"
                      >
                        {confirming === pago.id ? (
                          <div className="w-3 h-3 border-2 border-[var(--color-success)] border-t-transparent rounded-full animate-spin" />
                        ) : (
                          "Confirmar"
                        )}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showModal && (
        <ModalRegistrarPago
          expedienteId={expedienteId}
          onClose={() => setShowModal(false)}
          onSuccess={() => {
            setShowModal(false);
            fetchPagos();
            onCreditRefresh?.();
          }}
        />
      )}
    </div>
  );
}
