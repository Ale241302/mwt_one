"use client";

import { useState } from 'react';
import { RefreshCw, X } from 'lucide-react';
import api from '@/lib/api';
import toast from 'react-hot-toast';

interface SupersederModalProps {
  open: boolean;
  onClose: () => void;
  expedienteId: string;
  artifactId: string;
  artifactType: string;
  onSuccess: () => void;
}

export default function SupersederModal({
  open, onClose, expedienteId, artifactId, artifactType, onSuccess
}: SupersederModalProps) {
  const [submitting, setSubmitting] = useState(false);

  const handleSupersede = async () => {
    setSubmitting(true);
    try {
      await api.post(`expedientes/${expedienteId}/artifacts/${artifactId}/supersede/`);
      toast.success(`Artefacto ${artifactType} supersedido`);
      onSuccess();
      onClose();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      toast.error(e.response?.data?.detail || 'Error al superseder artefacto');
    } finally {
      setSubmitting(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 flex items-center justify-center z-50">
      <div className="fixed inset-0 bg-black/40" onClick={() => !submitting && onClose()} />
      <div className="relative bg-surface rounded-2xl border border-border shadow-xl p-6 w-full max-w-sm mx-4 z-10">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base font-bold text-text-primary flex items-center gap-2">
            <RefreshCw className="w-5 h-5 text-amber-500" />
            Superseder Artefacto
          </h3>
          <button onClick={onClose} disabled={submitting} className="text-text-tertiary hover:text-text-primary">
            <X size={18} />
          </button>
        </div>

        <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 mb-5">
          <p className="text-sm text-amber-800">
            El artefacto <strong>{artifactType}</strong> actual quedará en estado{' '}
            <span className="font-semibold">SUPERSEDED</span>. Podrás registrar una nueva versión.
          </p>
        </div>

        <div className="flex justify-end gap-3">
          <button onClick={onClose} disabled={submitting}
            className="bg-surface border border-border text-text-secondary hover:bg-bg-alt px-4 py-2 rounded-lg text-sm font-medium">
            Cancelar
          </button>
          <button
            onClick={handleSupersede}
            disabled={submitting}
            className="bg-red-50 hover:bg-red-100 text-red-700 border border-red-200 px-4 py-2 rounded-lg text-sm font-medium transition-all active:scale-95 flex items-center gap-2 disabled:opacity-50"
          >
            {submitting ? (
              <><span className="w-4 h-4 border-2 border-red-700 border-t-transparent rounded-full animate-spin" /> Procesando...</>
            ) : (
              <><RefreshCw size={14} /> Confirmar Superseder</>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
