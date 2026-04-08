"use client";

/**
 * S25-09 — PagosSection con Payment Status Machine completa.
 * Acciones CEO: verify, reject (con reason), release-credit individual, release-all-verified bulk.
 * Vista no-CEO: solo lee, sin acciones.
 */

import { useState, useEffect, useCallback } from "react";
import {
  CheckCircle2, Clock, ShieldCheck, XCircle, CreditCard,
  Plus, ZapIcon, ChevronDown, ChevronUp, AlertCircle, RefreshCw,
} from "lucide-react";
import api from "@/lib/api";
import toast from "react-hot-toast";
import ModalRegistrarPago from "@/components/expediente/ModalRegistrarPago";

// ─── Types ───────────────────────────────────────────────────────────────────

type PaymentStatus = "pending" | "verified" | "credit_released" | "rejected";

interface Pago {
  id: number;
  amount_paid: number;
  payment_date?: string;
  tipo_pago?: string;
  metodo_pago?: string;
  payment_status: PaymentStatus;
  verified_at?: string;
  verified_by_display?: string;
  credit_released_at?: string;
  credit_released_by_display?: string;
  rejection_reason?: string;
  url_comprobante?: string;
}

interface Props {
  expedienteId: string;
  isCeo?: boolean;
  onCreditRefresh?: () => void;
}

// ─── Status badge ─────────────────────────────────────────────────────────────

const STATUS_CONFIG: Record<
  PaymentStatus,
  { label: string; icon: React.ReactNode; bg: string; text: string }
> = {
  pending: {
    label: "Pendiente",
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
    label: "Crédito liberado",
    icon: <CheckCircle2 className="w-3.5 h-3.5" />,
    bg: "bg-emerald-50",
    text: "text-emerald-700",
  },
  rejected: {
    label: "Rechazado",
    icon: <XCircle className="w-3.5 h-3.5" />,
    bg: "bg-red-50",
    text: "text-red-600",
  },
};

function StatusBadge({ status }: { status: PaymentStatus }) {
  const cfg = STATUS_CONFIG[status] ?? STATUS_CONFIG.pending;
  return (
    <span
      className={`inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full ${cfg.bg} ${cfg.text}`}
    >
      {cfg.icon}
      {cfg.label}
    </span>
  );
}

// ─── Reject reason inline form ────────────────────────────────────────────────

function RejectForm({
  onSubmit,
  onCancel,
  loading,
}: {
  onSubmit: (reason: string) => void;
  onCancel: () => void;
  loading: boolean;
}) {
  const [reason, setReason] = useState("");
  return (
    <div className="flex flex-col gap-2 mt-2 p-3 bg-red-50 border border-red-200 rounded-xl">
      <p className="text-xs font-semibold text-red-700">Motivo de rechazo:</p>
      <textarea
        value={reason}
        onChange={(e) => setReason(e.target.value)}
        placeholder="Describe el motivo del rechazo..."
        rows={2}
        className="w-full text-xs px-3 py-2 border border-red-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-red-300 resize-none"
      />
      <div className="flex justify-end gap-2">
        <button
          onClick={onCancel}
          className="text-xs px-3 py-1.5 text-red-600 border border-red-200 rounded-lg hover:bg-red-100 transition-colors"
        >
          Cancelar
        </button>
        <button
          onClick={() => reason.trim() && onSubmit(reason.trim())}
          disabled={loading || !reason.trim()}
          className="text-xs px-3 py-1.5 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors"
        >
          {loading ? (
            <span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin inline-block" />
          ) : (
            "Confirmar rechazo"
          )}
        </button>
      </div>
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

export default function PagosSection({ expedienteId, isCeo = false, onCreditRefresh }: Props) {
  const [pagos, setPagos] = useState<Pago[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [rejectingId, setRejectingId] = useState<number | null>(null);
  const [bulkLoading, setBulkLoading] = useState(false);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const fetchPagos = useCallback(async () => {
    try {
      setLoading(true);
      const res = await api.get(`expedientes/${expedienteId}/pagos/`);
      const list: Pago[] = Array.isArray(res.data)
        ? res.data
        : res.data?.results ?? [];
      setPagos(list);
    } catch {
      toast.error("Error al cargar pagos");
    } finally {
      setLoading(false);
    }
  }, [expedienteId]);

  useEffect(() => { fetchPagos(); }, [fetchPagos]);

  // ── Actions ────────────────────────────────────────────────────────────────

  const handleVerify = async (pagoId: number) => {
    setActionLoading(pagoId);
    try {
      await api.post(`expedientes/${expedienteId}/pagos/${pagoId}/verify/`);
      toast.success("Pago verificado");
      await fetchPagos();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { error?: string } } };
      toast.error(e.response?.data?.error ?? "Error al verificar");
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (pagoId: number, reason: string) => {
    setActionLoading(pagoId);
    try {
      await api.post(`expedientes/${expedienteId}/pagos/${pagoId}/reject/`, { reason });
      toast.success("Pago rechazado");
      setRejectingId(null);
      await fetchPagos();
      onCreditRefresh?.();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { error?: string } } };
      toast.error(e.response?.data?.error ?? "Error al rechazar");
    } finally {
      setActionLoading(null);
    }
  };

  const handleRelease = async (pagoId: number) => {
    setActionLoading(pagoId);
    try {
      await api.post(`expedientes/${expedienteId}/pagos/${pagoId}/release-credit/`);
      toast.success("Crédito liberado");
      await fetchPagos();
      onCreditRefresh?.();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { error?: string } } };
      toast.error(e.response?.data?.error ?? "Error al liberar crédito");
    } finally {
      setActionLoading(null);
    }
  };

  const handleBulkRelease = async () => {
    const verifiedCount = pagos.filter((p) => p.payment_status === "verified").length;
    if (verifiedCount === 0) {
      toast("No hay pagos verificados para liberar", { icon: "ℹ️" });
      return;
    }
    setBulkLoading(true);
    try {
      const res = await api.post(`expedientes/${expedienteId}/pagos/release-all-verified/`);
      const { released } = res.data as { released: number; already_released: number };
      toast.success(`${released} pago${released !== 1 ? "s" : ""} liberado${released !== 1 ? "s" : ""}`);
      await fetchPagos();
      onCreditRefresh?.();
    } catch {
      toast.error("Error al liberar créditos en bulk");
    } finally {
      setBulkLoading(false);
    }
  };

  // ── Derived counts ─────────────────────────────────────────────────────────

  const totalReleased = pagos
    .filter((p) => p.payment_status === "credit_released")
    .reduce((s, p) => s + (p.amount_paid ?? 0), 0);

  const totalPending = pagos
    .filter((p) => p.payment_status === "pending")
    .reduce((s, p) => s + (p.amount_paid ?? 0), 0);

  const totalVerified = pagos
    .filter((p) => p.payment_status === "verified")
    .reduce((s, p) => s + (p.amount_paid ?? 0), 0);

  const verifiedCount = pagos.filter((p) => p.payment_status === "verified").length;

  const fmt = (n: number) =>
    `$${n.toLocaleString("es-CR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">
          Pagos
        </h3>
        <div className="flex items-center gap-2 flex-wrap">
          {isCeo && verifiedCount > 0 && (
            <button
              type="button"
              onClick={handleBulkRelease}
              disabled={bulkLoading}
              className="flex items-center gap-1.5 text-xs bg-emerald-600 text-white rounded-lg px-3 py-1.5 hover:bg-emerald-700 disabled:opacity-50 transition-colors"
            >
              {bulkLoading ? (
                <span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <ZapIcon className="w-3.5 h-3.5" />
              )}
              Liberar todos ({verifiedCount})
            </button>
          )}
          <button
            type="button"
            onClick={fetchPagos}
            className="p-1.5 rounded-lg hover:bg-[var(--color-bg-alt)] text-[var(--color-text-tertiary)] transition-colors"
            title="Actualizar"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
          <button
            type="button"
            onClick={() => setShowModal(true)}
            className="flex items-center gap-1.5 text-xs bg-[var(--color-navy)] text-white rounded-lg px-3 py-1.5 hover:opacity-80 transition-opacity"
          >
            <Plus className="w-3.5 h-3.5" /> Registrar pago
          </button>
        </div>
      </div>

      {/* Summary pills */}
      <div className="grid grid-cols-3 gap-3">
        <div className="flex flex-col gap-0.5 bg-amber-50 border border-amber-100 rounded-xl px-3 py-2.5">
          <span className="text-[10px] uppercase tracking-wider text-amber-500 font-semibold">Pendiente</span>
          <span className="text-sm font-bold text-amber-700 tabular-nums">{fmt(totalPending)}</span>
        </div>
        <div className="flex flex-col gap-0.5 bg-blue-50 border border-blue-100 rounded-xl px-3 py-2.5">
          <span className="text-[10px] uppercase tracking-wider text-blue-500 font-semibold">Verificado</span>
          <span className="text-sm font-bold text-blue-700 tabular-nums">{fmt(totalVerified)}</span>
        </div>
        <div className="flex flex-col gap-0.5 bg-emerald-50 border border-emerald-100 rounded-xl px-3 py-2.5">
          <span className="text-[10px] uppercase tracking-wider text-emerald-500 font-semibold">Liberado</span>
          <span className="text-sm font-bold text-emerald-700 tabular-nums">{fmt(totalReleased)}</span>
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex items-center gap-2 py-4">
          <div className="w-4 h-4 border-2 border-[var(--color-navy)] border-t-transparent rounded-full animate-spin" />
          <span className="text-xs text-[var(--color-text-tertiary)]">Cargando pagos...</span>
        </div>
      ) : pagos.length === 0 ? (
        <div className="flex flex-col items-center gap-2 py-8">
          <CreditCard className="w-8 h-8 text-[var(--color-text-tertiary)] opacity-30" />
          <p className="text-xs text-[var(--color-text-tertiary)] italic">Sin pagos registrados.</p>
        </div>
      ) : (
        <div className="border border-[var(--color-border)] rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-[var(--color-bg-alt)]">
              <tr>
                <th className="text-left px-4 py-2.5 text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">
                  Fecha
                </th>
                <th className="text-left px-4 py-2.5 text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">
                  Monto
                </th>
                <th className="text-left px-4 py-2.5 text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">
                  Estado
                </th>
                {isCeo && (
                  <th className="text-right px-4 py-2.5 text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">
                    Acciones
                  </th>
                )}
                <th className="px-2 py-2.5 w-8" />
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--color-border)]">
              {pagos.map((pago) => {
                const isExpanded = expandedId === pago.id;
                const isLoading = actionLoading === pago.id;
                const isRejecting = rejectingId === pago.id;

                return (
                  <>
                    <tr
                      key={pago.id}
                      className="hover:bg-[var(--color-bg-alt)]/50 transition-colors"
                    >
                      <td className="px-4 py-3 text-[var(--color-text-secondary)] tabular-nums text-xs">
                        {pago.payment_date ?? "—"}
                      </td>
                      <td className="px-4 py-3 font-semibold text-[var(--color-text-primary)] tabular-nums">
                        {fmt(pago.amount_paid ?? 0)}
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge status={pago.payment_status} />
                      </td>

                      {/* CEO Actions */}
                      {isCeo && (
                        <td className="px-4 py-3 text-right">
                          <div className="flex items-center justify-end gap-1.5 flex-wrap">
                            {pago.payment_status === "pending" && (
                              <>
                                <button
                                  onClick={() => handleVerify(pago.id)}
                                  disabled={isLoading}
                                  className="text-xs px-2.5 py-1 bg-blue-50 text-blue-700 border border-blue-200 rounded-lg hover:bg-blue-100 disabled:opacity-50 transition-colors font-medium"
                                >
                                  {isLoading ? (
                                    <span className="w-3 h-3 border-2 border-blue-700 border-t-transparent rounded-full animate-spin inline-block" />
                                  ) : (
                                    "Verificar"
                                  )}
                                </button>
                                <button
                                  onClick={() => setRejectingId(pago.id)}
                                  disabled={isLoading}
                                  className="text-xs px-2.5 py-1 bg-red-50 text-red-600 border border-red-200 rounded-lg hover:bg-red-100 disabled:opacity-50 transition-colors font-medium"
                                >
                                  Rechazar
                                </button>
                              </>
                            )}
                            {pago.payment_status === "verified" && (
                              <>
                                <button
                                  onClick={() => handleRelease(pago.id)}
                                  disabled={isLoading}
                                  className="text-xs px-2.5 py-1 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-lg hover:bg-emerald-100 disabled:opacity-50 transition-colors font-medium"
                                >
                                  {isLoading ? (
                                    <span className="w-3 h-3 border-2 border-emerald-700 border-t-transparent rounded-full animate-spin inline-block" />
                                  ) : (
                                    "Liberar crédito"
                                  )}
                                </button>
                                <button
                                  onClick={() => setRejectingId(pago.id)}
                                  disabled={isLoading}
                                  className="text-xs px-2.5 py-1 bg-red-50 text-red-600 border border-red-200 rounded-lg hover:bg-red-100 disabled:opacity-50 transition-colors font-medium"
                                >
                                  Rechazar
                                </button>
                              </>
                            )}
                            {(pago.payment_status === "credit_released" ||
                              pago.payment_status === "rejected") && (
                              <span className="text-xs text-[var(--color-text-tertiary)] italic">—</span>
                            )}
                          </div>
                        </td>
                      )}

                      {/* Expand toggle */}
                      <td className="px-2 py-3">
                        <button
                          onClick={() => setExpandedId(isExpanded ? null : pago.id)}
                          className="p-1 rounded hover:bg-[var(--color-bg-alt)] text-[var(--color-text-tertiary)] transition-colors"
                        >
                          {isExpanded ? (
                            <ChevronUp className="w-3.5 h-3.5" />
                          ) : (
                            <ChevronDown className="w-3.5 h-3.5" />
                          )}
                        </button>
                      </td>
                    </tr>

                    {/* Reject inline form */}
                    {isRejecting && (
                      <tr key={`reject-${pago.id}`}>
                        <td colSpan={isCeo ? 5 : 4} className="px-4 pb-3">
                          <RejectForm
                            onSubmit={(reason) => handleReject(pago.id, reason)}
                            onCancel={() => setRejectingId(null)}
                            loading={isLoading}
                          />
                        </td>
                      </tr>
                    )}

                    {/* Expanded detail row */}
                    {isExpanded && !isRejecting && (
                      <tr
                        key={`detail-${pago.id}`}
                        className="bg-[var(--color-bg-alt)]/30"
                      >
                        <td colSpan={isCeo ? 5 : 4} className="px-6 py-3">
                          <dl className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
                            <div>
                              <dt className="text-[var(--color-text-tertiary)] mb-0.5">Tipo</dt>
                              <dd className="text-[var(--color-text-primary)] font-medium">
                                {pago.tipo_pago ?? "—"}
                              </dd>
                            </div>
                            <div>
                              <dt className="text-[var(--color-text-tertiary)] mb-0.5">Método</dt>
                              <dd className="text-[var(--color-text-primary)] font-medium">
                                {pago.metodo_pago ?? "—"}
                              </dd>
                            </div>
                            {pago.verified_by_display && (
                              <div>
                                <dt className="text-[var(--color-text-tertiary)] mb-0.5">Verificado por</dt>
                                <dd className="text-blue-700 font-medium">
                                  {pago.verified_by_display}
                                  {pago.verified_at && (
                                    <span className="text-[var(--color-text-tertiary)] ml-1">
                                      ({new Date(pago.verified_at).toLocaleDateString()})
                                    </span>
                                  )}
                                </dd>
                              </div>
                            )}
                            {pago.credit_released_by_display && (
                              <div>
                                <dt className="text-[var(--color-text-tertiary)] mb-0.5">Liberado por</dt>
                                <dd className="text-emerald-700 font-medium">
                                  {pago.credit_released_by_display}
                                  {pago.credit_released_at && (
                                    <span className="text-[var(--color-text-tertiary)] ml-1">
                                      ({new Date(pago.credit_released_at).toLocaleDateString()})
                                    </span>
                                  )}
                                </dd>
                              </div>
                            )}
                            {pago.rejection_reason && (
                              <div className="col-span-2 sm:col-span-3">
                                <dt className="text-red-500 mb-0.5 flex items-center gap-1">
                                  <AlertCircle className="w-3 h-3" /> Motivo de rechazo
                                </dt>
                                <dd className="text-red-600 font-medium bg-red-50 rounded-lg px-3 py-2">
                                  {pago.rejection_reason}
                                </dd>
                              </div>
                            )}
                            {pago.url_comprobante && (
                              <div>
                                <dt className="text-[var(--color-text-tertiary)] mb-0.5">Comprobante</dt>
                                <dd>
                                  <a
                                    href={pago.url_comprobante}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-[var(--color-navy)] hover:underline text-xs"
                                  >
                                    Ver archivo →
                                  </a>
                                </dd>
                              </div>
                            )}
                          </dl>
                        </td>
                      </tr>
                    )}
                  </>
                );
              })}
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
