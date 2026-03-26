"use client";

import { useState } from 'react';
import { Ban } from 'lucide-react';
import api from '@/lib/api';
import toast from 'react-hot-toast';
import { cn } from '@/lib/utils';

const COMMAND_ENDPOINTS: Record<string, string> = {
  'C6':  'confirm-production',
  'C7':  'start-preparation',
  'C8':  'confirm-preparation',
  'C9':  'register-dispatch',
  'C10': 'confirm-arrival',
  'C11': 'register-nationalization',
  'C12': 'register-delivery',
  'C13': 'close',
  'C14': 'close',
  'C21': 'reopen',
};

const COMMAND_LABELS: Record<string, string> = {
  'C2':  'Registrar Proforma',
  'C6':  'Registrar Producción',
  'C7':  'Iniciar Preparación',
  'C8':  'Confirmar Preparación',
  'C9':  'Registrar Despacho',
  'C10': 'Aprobar Despacho',
  'C11B': 'Confirmar Salida China',
  'C12': 'Confirmar Arribo CR',
  'C13': 'Liquidar Expediente',
  'C14': 'Cerrar Expediente',
  'C21': 'Reabrir Expediente',
};

interface PipelineActionsPanelProps {
  expedienteId: string;
  availableActions: string[];
  isBlocked: boolean;
  status: string;
  onActionSuccess: () => void;
}

export default function PipelineActionsPanel({
  expedienteId,
  availableActions,
  isBlocked,
  status,
  onActionSuccess,
}: PipelineActionsPanelProps) {
  const [confirmCmd, setConfirmCmd] = useState<string | null>(null);
  const [executing, setExecuting] = useState(false);

  // S17-10: Solo CERRADO permite Reabrir. CANCELADO no permite acciones.
  if (status === 'CANCELADO') return null;

  if (isBlocked) {
    return (
      <div className="flex items-center gap-2">
        <span className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold rounded-full bg-red-100 text-red-700 border border-red-200 shadow-sm animate-pulse">
          <Ban className="w-3.5 h-3.5" /> BLOQUEADO — Desbloquea para continuar
        </span>
      </div>
    );
  }

  const executeAction = async (cmd: string) => {
    const slug = COMMAND_ENDPOINTS[cmd];
    if (!slug) {
      toast('Acción no implementada', { icon: '🚧' });
      return;
    }
    setExecuting(true);
    try {
      await api.post(`expedientes/${expedienteId}/${slug}/`);
      toast.success(`${COMMAND_LABELS[cmd] || cmd} ejecutado`);
      onActionSuccess();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } }, message?: string };
      toast.error(e.response?.data?.detail || 'Error al ejecutar');
    } finally {
      setExecuting(false);
      setConfirmCmd(null);
    }
  };

  return (
    <>
      <div className="flex flex-wrap gap-3">
        {status === 'CERRADO' ? (
          <button
            onClick={() => setConfirmCmd('C21')}
            disabled={executing}
            className="bg-amber-500 hover:bg-amber-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all shadow-sm active:scale-95 disabled:opacity-60 flex items-center gap-2"
          >
            Reabrir Expediente
          </button>
        ) : (
          availableActions.length > 0 ? (
            availableActions.map(cmd => (
              <button
                key={cmd}
                onClick={() => setConfirmCmd(cmd)}
                disabled={executing}
                className="bg-navy hover:bg-slate-800 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all shadow-sm active:scale-95 disabled:opacity-60"
              >
                {COMMAND_LABELS[cmd] || cmd}
              </button>
            ))
          ) : (
            <p className="text-sm text-text-tertiary">No hay acciones disponibles en el estado actual.</p>
          )
        )}
      </div>
      ...

      {/* Confirmation Modal */}
      {confirmCmd && (
        <div className="fixed inset-0 flex items-center justify-center z-50">
          <div className="fixed inset-0 bg-black/40" onClick={() => !executing && setConfirmCmd(null)} />
          <div className="relative bg-surface rounded-2xl border border-border shadow-xl p-6 w-full max-w-sm mx-4 z-10">
            <h3 className="text-base font-bold text-text-primary mb-2">Confirmar acción</h3>
            <p className="text-sm text-text-secondary mb-6">
              ¿Confirmar <span className="font-semibold text-navy">{COMMAND_LABELS[confirmCmd] || confirmCmd}</span>?
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setConfirmCmd(null)}
                disabled={executing}
                className="bg-surface border border-border text-text-secondary hover:bg-bg-alt px-4 py-2 rounded-lg text-sm font-medium transition-all"
              >
                Cancelar
              </button>
              <button
                onClick={() => executeAction(confirmCmd)}
                disabled={executing}
                className={cn(
                  "bg-navy hover:bg-slate-800 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all shadow-sm active:scale-95",
                  executing && "opacity-60 cursor-not-allowed"
                )}
              >
                {executing ? (
                  <span className="flex items-center gap-2">
                    <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Ejecutando...
                  </span>
                ) : 'Confirmar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
