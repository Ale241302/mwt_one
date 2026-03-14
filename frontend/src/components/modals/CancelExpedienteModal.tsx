"use client";
import { useState } from 'react';
import { XCircle, X, AlertTriangle } from 'lucide-react';
import api from '@/lib/api';
import toast from 'react-hot-toast';

const CANCELLABLE_STATUSES = ['REGISTRO', 'PRODUCCION', 'PREPARACION'];

interface CancelExpedienteModalProps {
  open: boolean;
  onClose: () => void;
  expedienteId: string;
  currentStatus: string;
  onSuccess: () => void;
}

export default function CancelExpedienteModal({
  open, onClose, expedienteId, currentStatus, onSuccess,
}: CancelExpedienteModalProps) {
  const [reason, setReason]         = useState('');
  const [submitting, setSubmitting] = useState(false);
  const MIN_CHARS = 20;

  const canCancel = CANCELLABLE_STATUSES.includes(currentStatus);

  const handleCancel = async () => {
    if (!canCancel) return;
    if (reason.trim().length < MIN_CHARS) {
      toast.error(`La razón debe tener al menos ${MIN_CHARS} caracteres`);
      return;
    }
    setSubmitting(true);
    try {
      await api.post(`expedientes/${expedienteId}/cancel/`, { cancel_reason: reason });
      toast.success('Expediente cancelado');
      onSuccess();
      onClose();
      setReason('');
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      toast.error(e.response?.data?.detail || 'Error al cancelar');
    } finally {
      setSubmitting(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 flex items-center justify-center z-50">
      <div className="fixed inset-0 bg-black/40 backdrop-blur-sm" onClick={() => !submitting && onClose()} />
      <div className="relative bg-[var(--surface)] rounded-2xl border border-[var(--border)] shadow-[var(--shadow-xl)] p-6 w-full max-w-md mx-4 z-10">

        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base font-bold text-[var(--text-primary)] flex items-center gap-2">
            <XCircle className="w-5 h-5 text-[var(--coral)]" />
            Cancelar Expediente
          </h3>
          <button
            onClick={onClose}
            disabled={submitting}
            aria-label="Cerrar modal"
            className="p-1.5 rounded-lg text-[var(--text-tertiary)] hover:bg-[var(--surface-hover)] transition-colors"
          >
            <X size={16} />
          </button>
        </div>

        {/* Estado no cancelable */}
        {!canCancel ? (
          <div
            className="rounded-lg px-4 py-4 mb-5 flex items-start gap-3 border"
            style={{
              background: 'var(--coral-soft)',
              borderColor: 'color-mix(in srgb, var(--coral) 30%, transparent)',
            }}
          >
            <AlertTriangle className="w-5 h-5 mt-0.5 shrink-0" style={{ color: 'var(--coral)' }} />
            <div>
              <p className="text-sm font-semibold mb-1" style={{ color: 'var(--coral)' }}>
                No se puede cancelar en estado <span className="font-bold">{currentStatus}</span>
              </p>
              <p className="text-xs" style={{ color: 'color-mix(in srgb, var(--coral) 80%, black)' }}>
                La cancelación solo está permitida en:{' '}
                <span className="font-medium">{CANCELLABLE_STATUSES.join(', ')}</span>.
              </p>
            </div>
          </div>
        ) : (
          /* Warning irreversible */
          <div
            className="rounded-lg px-4 py-3 mb-5 border"
            style={{
              background: 'var(--amber-soft)',
              borderColor: 'color-mix(in srgb, var(--amber) 30%, transparent)',
            }}
          >
            <p className="text-sm font-medium" style={{ color: 'var(--amber)' }}>
              \u26A0\uFE0F Esta acción es irreversible. El expediente será marcado como CANCELADO.
            </p>
          </div>
        )}

        {/* Formulario cancelación */}
        {canCancel && (
          <div className="mb-5">
            <label className="block text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-1.5">
              Razón de cancelación <span className="text-[var(--coral)]">*</span>
            </label>
            <textarea
              value={reason}
              onChange={e => setReason(e.target.value)}
              rows={4}
              placeholder="Describe el motivo de cancelación del expediente..."
              className="w-full bg-[var(--bg)] border border-[var(--border)] rounded-lg px-3 py-2.5 text-sm text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--coral)]/40 resize-none placeholder:text-[var(--text-disabled)] transition"
            />
            <div className="flex justify-between items-center mt-1">
              <span className="text-xs text-[var(--text-tertiary)]">Mínimo {MIN_CHARS} caracteres</span>
              <span
                className="text-xs font-medium"
                style={{ color: reason.length < MIN_CHARS ? 'var(--coral)' : 'var(--mint)' }}
              >
                {reason.length} / {MIN_CHARS}
              </span>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-3">
          <button
            onClick={onClose}
            disabled={submitting}
            className="bg-[var(--surface)] border border-[var(--border)] text-[var(--text-secondary)] hover:bg-[var(--surface-hover)] px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            {canCancel ? 'Volver' : 'Cerrar'}
          </button>
          {canCancel && (
            <button
              onClick={handleCancel}
              disabled={submitting || reason.trim().length < MIN_CHARS}
              className="bg-[var(--coral)] hover:bg-[var(--coral-dark)] text-[var(--text-inverse)] px-4 py-2 rounded-lg text-sm font-semibold transition-all active:scale-95 flex items-center gap-2 disabled:opacity-50"
            >
              {submitting ? (
                <><span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> Cancelando...</>
              ) : (
                <><XCircle size={15} /> Cancelar Expediente</>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
