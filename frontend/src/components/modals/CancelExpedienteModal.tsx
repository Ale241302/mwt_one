"use client";

import { useState } from 'react';
import { XCircle, X, AlertTriangle } from 'lucide-react';
import api from '@/lib/api';
import toast from 'react-hot-toast';

// Estados desde los que el backend permite cancelar (C16)
const CANCELLABLE_STATUSES = ['REGISTRO', 'PRODUCCION', 'PREPARACION'];

interface CancelExpedienteModalProps {
  open: boolean;
  onClose: () => void;
  expedienteId: string;
  currentStatus: string; // ✅ nueva prop requerida
  onSuccess: () => void;
}

export default function CancelExpedienteModal({
  open, onClose, expedienteId, currentStatus, onSuccess
}: CancelExpedienteModalProps) {
  const [reason, setReason] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const MIN_CHARS = 20;

  // ✅ Validar si el estado actual permite cancelar
  const canCancel = CANCELLABLE_STATUSES.includes(currentStatus);

  const handleCancel = async () => {
    if (!canCancel) return;
    if (reason.trim().length < MIN_CHARS) {
      toast.error(`La razón debe tener al menos ${MIN_CHARS} caracteres`);
      return;
    }
    setSubmitting(true);
    try {
      await api.post(`expedientes/${expedienteId}/cancel/`, {
        cancel_reason: reason,
      });
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
      <div className="fixed inset-0 bg-black/40" onClick={() => !submitting && onClose()} />
      <div className="relative bg-surface rounded-2xl border border-border shadow-xl p-6 w-full max-w-md mx-4 z-10">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base font-bold text-text-primary flex items-center gap-2">
            <XCircle className="w-5 h-5 text-red-600" />
            Cancelar Expediente
          </h3>
          <button onClick={onClose} disabled={submitting} className="text-text-tertiary hover:text-text-primary">
            <X size={18} />
          </button>
        </div>

        {/* ✅ Bloqueo visual si el estado no permite cancelar */}
        {!canCancel ? (
          <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-4 mb-5 flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5 shrink-0" />
            <div>
              <p className="text-sm font-semibold text-red-800 mb-1">
                No se puede cancelar en estado <span className="font-bold">{currentStatus}</span>
              </p>
              <p className="text-xs text-red-700">
                La cancelación solo está permitida en:{' '}
                <span className="font-medium">{CANCELLABLE_STATUSES.join(', ')}</span>.
              </p>
            </div>
          </div>
        ) : (
          <div className="bg-orange-50 border border-orange-200 rounded-lg px-4 py-3 mb-5">
            <p className="text-sm text-orange-800 font-medium">
              ⚠️ Esta acción es irreversible. El expediente será marcado como CANCELADO.
            </p>
          </div>
        )}

        {/* Formulario solo visible si puede cancelar */}
        {canCancel && (
          <div className="mb-5">
            <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5">
              Razón de cancelación <span className="text-coral">*</span>
            </label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={4}
              placeholder="Describe el motivo de cancelación del expediente..."
              className="w-full bg-bg border border-border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-red-300 resize-none"
            />
            <div className="flex justify-between items-center mt-1">
              <span className="text-xs text-text-tertiary">Mínimo {MIN_CHARS} caracteres</span>
              <span className={`text-xs font-medium ${reason.length < MIN_CHARS ? 'text-coral' : 'text-mint'
                }`}>
                {reason.length} / {MIN_CHARS}
              </span>
            </div>
          </div>
        )}

        <div className="flex justify-end gap-3">
          <button
            onClick={onClose}
            disabled={submitting}
            className="bg-surface border border-border text-text-secondary hover:bg-bg-alt px-4 py-2 rounded-lg text-sm font-medium transition-all"
          >
            {canCancel ? 'Volver' : 'Cerrar'}
          </button>
          {canCancel && (
            <button
              onClick={handleCancel}
              disabled={submitting || reason.trim().length < MIN_CHARS}
              className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all active:scale-95 flex items-center gap-2 disabled:opacity-50"
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
