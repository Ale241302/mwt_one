"use client";

import { useState } from 'react';
import { AlertTriangle, X } from 'lucide-react';
import api from '@/lib/api';
import toast from 'react-hot-toast';

interface VoidArtifactModalProps {
  open: boolean;
  onClose: () => void;
  expedienteId: string;
  onSuccess: () => void;
}

export default function VoidArtifactModal({
  open, onClose, expedienteId, onSuccess
}: VoidArtifactModalProps) {
  const [reason, setReason] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const MIN_CHARS = 15;

  const handleVoid = async () => {
    if (reason.trim().length < MIN_CHARS) {
      toast.error(`La razón debe tener al menos ${MIN_CHARS} caracteres`);
      return;
    }
    setSubmitting(true);
    try {
      await api.post(`expedientes/${expedienteId}/void-artifact/`, {
        artifact_type: 'ART-09',
        void_reason: reason,
      });
      toast.success('Factura anulada. Ya puede emitir una nueva.');
      onSuccess();
      onClose();
      setReason('');
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      toast.error(e.response?.data?.detail || 'Error al anular factura');
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
            <AlertTriangle className="w-5 h-5 text-red-600" />
            Anular Factura (ART-09)
          </h3>
          <button onClick={onClose} disabled={submitting} className="text-text-tertiary hover:text-text-primary">
            <X size={18} />
          </button>
        </div>

        {/* Strong warning */}
        <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 mb-5">
          <p className="text-sm text-red-800 font-semibold">
            ⚠️ Anular la factura tendrá consecuencias en el pipeline.
          </p>
          <p className="text-xs text-red-700 mt-1">
            El status del expediente regresará al estado previo. Esta acción queda auditada.
          </p>
        </div>

        <div className="mb-5">
          <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5">
            Razón de anulación <span className="text-coral">*</span>
          </label>
          <textarea
            value={reason}
            onChange={e => setReason(e.target.value)}
            rows={4}
            placeholder="Describe el motivo de la anulación..."
            className="w-full bg-bg border border-border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-red-300 resize-none"
          />
          <div className="flex justify-between mt-1">
            <span className="text-xs text-text-tertiary">Mínimo {MIN_CHARS} caracteres</span>
            <span className={`text-xs font-medium ${
              reason.length < MIN_CHARS ? 'text-coral' : 'text-mint'
            }`}>
              {reason.length} / {MIN_CHARS}
            </span>
          </div>
        </div>

        <div className="flex justify-end gap-3">
          <button onClick={onClose} disabled={submitting}
            className="bg-surface border border-border text-text-secondary hover:bg-bg-alt px-4 py-2 rounded-lg text-sm font-medium">
            Cancelar
          </button>
          <button
            onClick={handleVoid}
            disabled={submitting || reason.trim().length < MIN_CHARS}
            className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all active:scale-95 flex items-center gap-2 disabled:opacity-50"
          >
            {submitting ? (
              <><span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> Anulando...</>
            ) : (
              <><AlertTriangle size={14} /> Anular Factura</>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
