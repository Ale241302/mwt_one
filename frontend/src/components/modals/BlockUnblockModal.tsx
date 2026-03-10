"use client";

import { useState } from 'react';
import { Ban, X } from 'lucide-react';
import api from '@/lib/api';
import toast from 'react-hot-toast';

interface BlockUnblockModalProps {
  open: boolean;
  onClose: () => void;
  expedienteId: string;
  isBlocked: boolean;
  blockReason?: string;
  blockedByType?: string;
  onSuccess: () => void;
}

export default function BlockUnblockModal({
  open, onClose, expedienteId, isBlocked, blockReason, blockedByType, onSuccess
}: BlockUnblockModalProps) {
  const [reason, setReason] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const isSystemBlock = blockedByType === 'SYSTEM';
  const minChars = 10;

  const handleBlock = async () => {
    if (reason.trim().length < minChars) {
      toast.error(`La razón debe tener al menos ${minChars} caracteres`);
      return;
    }
    setSubmitting(true);
    try {
      await api.post(`expedientes/${expedienteId}/block/`, {
        block_reason: reason,
        blocked_by_type: 'CEO',
      });
      toast.success('Expediente bloqueado');
      onSuccess();
      onClose();
      setReason('');
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      toast.error(e.response?.data?.detail || 'Error al bloquear');
    } finally {
      setSubmitting(false);
    }
  };

  const handleUnblock = async () => {
    setSubmitting(true);
    try {
      await api.post(`expedientes/${expedienteId}/unblock/`);
      toast.success('Expediente desbloqueado');
      onSuccess();
      onClose();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      toast.error(e.response?.data?.detail || 'Error al desbloquear');
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
            <Ban className="w-5 h-5 text-red-600" />
            {isBlocked ? '🔓 Desbloquear Expediente' : '⚠️ Bloquear Expediente'}
          </h3>
          <button onClick={onClose} disabled={submitting} className="text-text-tertiary hover:text-text-primary">
            <X size={18} />
          </button>
        </div>

        {isBlocked ? (
          isSystemBlock ? (
            /* SYSTEM block — read only */
            <div>
              <p className="text-sm text-text-secondary mb-3">Este expediente fue bloqueado automáticamente por el sistema.</p>
              <div className="bg-slate-100 border border-border rounded-lg p-3 text-sm text-text-secondary">
                {blockReason || 'Sin razón registrada'}
              </div>
              <p className="text-xs text-text-tertiary mt-3">El bloqueo de sistema no puede ser revertido desde la UI.</p>
            </div>
          ) : (
            /* Manual unblock */
            <div>
              <p className="text-sm text-text-secondary mb-3">Razón del bloqueo actual:</p>
              <div className="bg-slate-100 border border-border rounded-lg p-3 text-sm text-text-secondary mb-5">
                {blockReason || 'Sin razón registrada'}
              </div>
              <div className="flex justify-end gap-3">
                <button onClick={onClose} disabled={submitting}
                  className="bg-surface border border-border text-text-secondary hover:bg-bg-alt px-4 py-2 rounded-lg text-sm font-medium">
                  Cancelar
                </button>
                <button onClick={handleUnblock} disabled={submitting}
                  className="bg-mint hover:bg-emerald-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all active:scale-95 flex items-center gap-2 disabled:opacity-60">
                  {submitting
                    ? <><span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> Desbloqueando...</>
                    : 'Desbloquear'}
                </button>
              </div>
            </div>
          )
        ) : (
          /* Block form */
          <div>
            <div className="mb-4">
              <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5">
                Razón de bloqueo <span className="text-coral">*</span> (mínimo {minChars} caracteres)
              </label>
              <textarea
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                rows={4}
                placeholder="Describe la razón del bloqueo..."
                className="w-full bg-bg border border-border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-red-300 resize-none"
              />
              <div className="text-right text-xs text-text-tertiary mt-1">
                <span className={reason.length < minChars ? 'text-coral' : 'text-mint'}>
                  {reason.length}
                </span> / {minChars} mín.
              </div>
            </div>
            <div className="flex justify-end gap-3">
              <button onClick={onClose} disabled={submitting}
                className="bg-surface border border-border text-text-secondary hover:bg-bg-alt px-4 py-2 rounded-lg text-sm font-medium">
                Cancelar
              </button>
              <button
                onClick={handleBlock}
                disabled={submitting || reason.trim().length < minChars}
                className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all active:scale-95 flex items-center gap-2 disabled:opacity-50"
              >
                {submitting
                  ? <><span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> Bloqueando...</>
                  : 'Bloquear Expediente'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
