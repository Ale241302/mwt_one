// S22-17 — Modal Bulk Assign por product_key
"use client";

import React, { useState } from 'react';
import { X, Package, CheckCircle, AlertTriangle } from 'lucide-react';

interface BulkAssignResult {
  created: number;
  skipped: number;
  errors: string[];
}

interface Props {
  onClose: () => void;
  onCreated: (count: number) => void;
}

export function BulkAssignModal({ onClose, onCreated }: Props) {
  const [productKey, setProductKey] = useState('');
  const [clientSubsidiaryId, setClientSubsidiaryId] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<BulkAssignResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!productKey.trim()) {
      setError('Ingresa un product_key válido.');
      return;
    }
    setLoading(true);
    setError(null);
    // TODO: POST /api/pricing/client-assignments/bulk/
    // body: { product_key, client_subsidiary_id: clientSubsidiaryId || undefined }
    await new Promise((r) => setTimeout(r, 900));
    const mockResult: BulkAssignResult = {
      created: 4,
      skipped: 1,
      errors: [],
    };
    setResult(mockResult);
    setLoading(false);
  };

  const handleDone = () => {
    if (result) onCreated(result.created);
    else onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <h2 className="heading-lg">Bulk Assign por Product Key</h2>
          <button onClick={onClose} className="btn btn-ghost btn-sm p-2"><X size={16} /></button>
        </div>

        <div className="px-6 py-5 space-y-4">
          {!result ? (
            <>
              <p className="text-xs text-text-secondary">
                Asigna todos los SKUs de un <code className="bg-[var(--bg-alt)] px-1 rounded">product_key</code> a uno o todos los clientes activos de esta marca. Si un CPA ya existe, se salta sin error.
              </p>
              <div>
                <label className="block text-xs font-medium text-text-secondary mb-1.5">Product Key *</label>
                <input
                  type="text"
                  value={productKey}
                  onChange={(e) => { setProductKey(e.target.value); setError(null); }}
                  placeholder="Ej: MRL-BOTA-COMPOSITE"
                  className="w-full border border-border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 font-mono"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-text-secondary mb-1.5">
                  ID Subsidiaria cliente <span className="text-text-tertiary">(vacío = todos los clientes activos)</span>
                </label>
                <input
                  type="number"
                  value={clientSubsidiaryId}
                  onChange={(e) => setClientSubsidiaryId(e.target.value)}
                  placeholder="Ej: 101"
                  className="w-full border border-border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30"
                />
              </div>
              {error && (
                <p className="text-xs text-red-600 flex items-center gap-1">
                  <AlertTriangle size={12} /> {error}
                </p>
              )}
            </>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center gap-3 p-4 rounded-xl bg-emerald-50 border border-emerald-200">
                <CheckCircle size={20} className="text-emerald-600 shrink-0" />
                <div>
                  <p className="text-sm font-semibold text-emerald-800">Bulk assign completado</p>
                  <p className="text-xs text-emerald-700 mt-0.5">
                    {result.created} CPAs creados · {result.skipped} saltados (ya existían)
                  </p>
                </div>
              </div>
              {result.errors.length > 0 && (
                <div className="rounded-xl bg-red-50 border border-red-200 p-3">
                  <p className="text-xs font-semibold text-red-700 mb-1">Errores ({result.errors.length})</p>
                  {result.errors.map((e, i) => (
                    <p key={i} className="text-xs text-red-600">• {e}</p>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-border">
          {!result ? (
            <>
              <button onClick={onClose} className="btn btn-secondary btn-sm">Cancelar</button>
              <button
                onClick={handleSubmit}
                disabled={loading}
                className="btn btn-primary btn-sm flex items-center gap-2 disabled:opacity-60"
              >
                <Package size={13} />
                {loading ? 'Asignando...' : 'Ejecutar Bulk Assign'}
              </button>
            </>
          ) : (
            <button onClick={handleDone} className="btn btn-primary btn-sm">Cerrar</button>
          )}
        </div>
      </div>
    </div>
  );
}
