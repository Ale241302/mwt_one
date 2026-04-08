"use client";

/**
 * S25-13 — PortalPagosTab: Vista portal pagos para clientes (CLIENT_* tier).
 * NUNCA muestra: rejection_reason, verified_by, credit_released_by.
 * El cliente ve: fecha, monto, payment_status (badge informativo).
 * Datos vienen de PagoClienteSerializer (serializer tiered).
 * Incluye CreditBar en modo compacto y DeferredPricePanel (solo-lectura).
 */

import { useState, useEffect, useCallback } from "react";
import {
  CreditCard, Clock, CheckCircle2, ShieldCheck, XCircle,
  RefreshCw, AlertCircle, Lock,
} from "lucide-react";
import api from "@/lib/api";
import toast from "react-hot-toast";
import CreditBar from "@/components/expediente/CreditBar";
import DeferredPricePanel from "@/components/expediente/DeferredPricePanel";

// ─── CLIENT_* tier — restricted fields (PagoClienteSerializer) ────────────────

type PaymentStatus = "pending" | "verified" | "credit_released" | "rejected";

interface PagoCliente {
  id: number;
  payment_date?: string;
  amount_paid: number;
  payment_status: PaymentStatus;
}

interface PortalExpedienteMeta {
  expediente_id: string;
  payment_coverage?: "none" | "partial" | "complete";
  coverage_pct?: number;
  credit_released?: boolean;
  deferred_total_price?: number | null;
  deferred_visible?: boolean;
  total_lines_value?: number;
}

interface Props {
  expedienteMeta: PortalExpedienteMeta;
}

// ─── Status badge (CLIENT version — no internals) ─────────────────────────────

const STATUS_UI: Record<
  PaymentStatus,
  { label: string; icon: React.ReactNode; bg: string; text: string }
> = {
  pending: {
    label: "En revisión",
    icon: <Clock className="w-3.5 h-3.5" />,
    bg: "bg-amber-50",
    text: "text-amber-700",
  },
  verified: {
    label: "Verificado",
    icon: <ShieldCheck className="w-3.5 h-3.5" />,
    bg: "bg-blue-50",
    text: "text-blue-700",
  },
  credit_released: {
    label: "Procesado",
    icon: <CheckCircle2 className="w-3.5 h-3.5" />,
    bg: "bg-emerald-50",
    text: "text-emerald-700",
  },
  rejected: {
    label: "Requiere atención",
    icon: <XCircle className="w-3.5 h-3.5" />,
    bg: "bg-red-50",
    text: "text-red-600",
  },
};

function ClientStatusBadge({ status }: { status: PaymentStatus }) {
  const ui = STATUS_UI[status] ?? STATUS_UI.pending;
  return (
    <span
      className={`inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full ${ui.bg} ${ui.text}`}
    >
      {ui.icon}
      {ui.label}
    </span>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

export function PortalPagosTab({ expedienteMeta }: Props) {
  const [pagos, setPagos] = useState<PagoCliente[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPagos = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      // Portal endpoint: usa PagoClienteSerializer internamente
      const res = await api.get(`/portal/expedientes/${expedienteMeta.expediente_id}/pagos/`);
      const list: PagoCliente[] = Array.isArray(res.data)
        ? res.data
        : res.data?.results ?? [];
      setPagos(list);
    } catch {
      setError("No se pudo cargar la información de pagos.");
      toast.error("Error al cargar pagos");
    } finally {
      setLoading(false);
    }
  }, [expedienteMeta.expediente_id]);

  useEffect(() => { fetchPagos(); }, [fetchPagos]);

  const fmt = (n: number) =>
    `$${n.toLocaleString("es-CR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

  const hasRejected = pagos.some((p) => p.payment_status === "rejected");

  return (
    <div className="space-y-5">
      {/* Credit Bar (compacto, CLIENT no ve montos internos) */}
      {expedienteMeta.payment_coverage && (
        <div className="card p-4 space-y-2">
          <h3 className="text-xs font-semibold text-text-primary uppercase tracking-wider">
            Cobertura de pago
          </h3>
          <CreditBar
            paymentCoverage={expedienteMeta.payment_coverage}
            coveragePct={expedienteMeta.coverage_pct ?? 0}
            creditReleased={expedienteMeta.credit_released}
            isCeo={false}
          />
        </div>
      )}

      {/* Deferred price (solo visible si deferred_visible=true) */}
      {expedienteMeta.deferred_visible && expedienteMeta.deferred_total_price != null && (
        <DeferredPricePanel
          expedienteId={expedienteMeta.expediente_id}
          deferredTotalPrice={expedienteMeta.deferred_total_price}
          deferredVisible={true}
          isCeo={false}
        />
      )}

      {/* Rejected attention banner */}
      {hasRejected && (
        <div className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-xl px-4 py-3">
          <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-red-700">Atención requerida</p>
            <p className="text-xs text-red-600 mt-0.5">
              Uno o más pagos requieren seguimiento. Contacta a tu ejecutivo de cuenta
              para más información.
            </p>
          </div>
        </div>
      )}

      {/* Payments list */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-semibold text-text-primary uppercase tracking-wider">
            Registro de pagos
          </h3>
          <button
            onClick={fetchPagos}
            className="btn btn-ghost btn-sm gap-1.5 text-xs"
          >
            <RefreshCw size={12} />
            Actualizar
          </button>
        </div>

        {loading ? (
          <div className="space-y-2 animate-pulse">
            {[1, 2, 3].map((i) => (
              <div key={i} className="card p-4 h-16 bg-bg-alt/40" />
            ))}
          </div>
        ) : error ? (
          <div className="card p-6 text-center text-text-tertiary">
            <AlertCircle className="w-8 h-8 mx-auto mb-2 opacity-30" />
            <p className="text-sm">{error}</p>
          </div>
        ) : pagos.length === 0 ? (
          <div className="card p-10 text-center text-text-tertiary">
            <CreditCard className="w-10 h-10 mx-auto mb-3 opacity-20" />
            <p className="text-sm">Sin pagos registrados en este expediente.</p>
            <p className="text-xs mt-1 opacity-70">
              Contacta a tu ejecutivo de cuenta para registrar un pago.
            </p>
          </div>
        ) : (
          <div className="card border border-border/60 overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="bg-bg-alt/40 border-b border-border/30">
                  <th className="px-4 py-2.5 text-left text-[10px] uppercase font-semibold text-text-tertiary">
                    Fecha
                  </th>
                  <th className="px-4 py-2.5 text-right text-[10px] uppercase font-semibold text-text-tertiary">
                    Monto
                  </th>
                  <th className="px-4 py-2.5 text-center text-[10px] uppercase font-semibold text-text-tertiary">
                    Estado
                  </th>
                  {/* Privacy lock column header */}
                  <th className="px-3 py-2.5 text-[10px] text-text-tertiary text-right opacity-40">
                    <Lock className="w-3 h-3 inline-block" />
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/30">
                {pagos.map((pago) => (
                  <tr key={pago.id} className="hover:bg-brand/[0.02] transition-colors">
                    <td className="px-4 py-3 text-xs text-text-secondary tabular-nums">
                      {pago.payment_date
                        ? new Date(pago.payment_date).toLocaleDateString("es-CR")
                        : "—"}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span className="text-sm font-bold text-text-primary tabular-nums">
                        {fmt(pago.amount_paid)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <ClientStatusBadge status={pago.payment_status} />
                    </td>
                    {/* Privacy indicator — internals hidden */}
                    <td className="px-3 py-3 text-right">
                      <span
                        title="Los detalles internos de verificación son confidenciales"
                        className="opacity-20 cursor-help"
                      >
                        <Lock className="w-3.5 h-3.5 text-text-tertiary inline-block" />
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Privacy note */}
        <p className="text-[10px] text-text-tertiary text-center opacity-60 flex items-center justify-center gap-1">
          <Lock className="w-3 h-3" />
          Los detalles operativos de verificación son confidenciales y gestionados internamente.
        </p>
      </div>
    </div>
  );
}
