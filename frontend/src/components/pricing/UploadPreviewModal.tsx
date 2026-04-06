// S22-14 — Modal Upload → Preview → Confirm
"use client";

import React, { useRef, useState } from 'react';
import { X, Upload, CheckCircle, AlertTriangle, FileText } from 'lucide-react';
import type { PriceListVersion } from '@/api/pricing';
import api from '@/lib/api';

interface PreviewLine {
  reference_code: string;
  unit_price_usd: string;
  grade_label: string;
  moq_total: number;
  available_sizes: string[];
}

interface UploadPreviewResponse {
  valid_lines: number;
  warnings: string[];
  errors: string[];
  preview: PreviewLine[];
  session_id: string;
}

interface Props {
  brandId: number | string;
  onClose: () => void;
  onConfirm: (version: PriceListVersion) => void;
}

export function UploadPreviewModal({ brandId, onClose, onConfirm }: Props) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [versionLabel, setVersionLabel] = useState('');
  const [notes, setNotes] = useState('');
  const [step, setStep] = useState<'upload' | 'preview' | 'confirming'>('upload');
  const [preview, setPreview] = useState<UploadPreviewResponse | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] ?? null;
    setFile(f);
    setError(null);
  };

  const handleUpload = async () => {
    if (!file || !versionLabel.trim()) {
      setError('Debes seleccionar un archivo y escribir un nombre de versión.');
      return;
    }
    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('brand_id', String(brandId));

    try {
      const res = await api.post<UploadPreviewResponse>('pricing/pricelists/upload/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setPreview(res.data);
      setStep('preview');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al procesar el archivo. Revisa el formato.');
      console.error(err);
    } finally {
      setUploading(false);
    }
  };

  const handleConfirm = async () => {
    if (!preview) return;
    setStep('confirming');
    
    try {
      const res = await api.post('pricing/pricelists/confirm/', {
        session_id: preview.session_id,
        brand_id: brandId,
        version_label: versionLabel,
        notes: notes
      });
      // El backend retorna la nueva versión creada
      onConfirm(res.data as any);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al confirmar la versión.');
      setStep('preview');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4 text-left">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <h2 className="text-lg font-bold text-navy">
            {step === 'upload' && 'Subir nueva pricelist'}
            {step === 'preview' && 'Vista previa'}
            {step === 'confirming' && 'Confirmando...'}
          </h2>
          <button onClick={onClose} className="btn btn-ghost btn-sm p-2"><X size={16} /></button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5">
          {step === 'upload' && (
            <>
              <div>
                <label className="block text-xs font-semibold text-text-secondary mb-1.5 uppercase tracking-wider">Nombre de versión *</label>
                <input
                  type="text"
                  value={versionLabel}
                  onChange={(e) => setVersionLabel(e.target.value)}
                  placeholder="Ej: Marluvas Q2-2026"
                  className="w-full border border-border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-navy/30"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-text-secondary mb-1.5 uppercase tracking-wider">Notas (opcional)</label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={2}
                  className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-navy/30 resize-none"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-text-secondary mb-1.5 uppercase tracking-wider">Archivo CSV o Excel *</label>
                <div
                  onClick={() => fileRef.current?.click()}
                  className="border-2 border-dashed border-border rounded-xl p-8 text-center cursor-pointer hover:border-navy/50 hover:bg-navy/5 transition-all"
                >
                  <FileText size={28} className="mx-auto mb-2 text-text-tertiary" />
                  {file ? (
                    <p className="text-sm font-medium text-navy">{file.name}</p>
                  ) : (
                    <p className="text-sm text-text-tertiary">Seleccionar archivo (.csv, .xlsx)</p>
                  )}
                  <input ref={fileRef} type="file" accept=".csv,.xlsx,.xls" onChange={handleFileChange} className="hidden" />
                </div>
              </div>
            </>
          )}

          {(step === 'preview' || step === 'confirming') && preview && (
            <>
              <div className="grid grid-cols-3 gap-3">
                <div className="rounded-lg bg-emerald-50 border border-emerald-100 p-3 text-center">
                  <p className="text-lg font-bold text-emerald-700">{preview.valid_lines}</p>
                  <p className="text-[10px] text-emerald-600 uppercase font-semibold">Válidas</p>
                </div>
                <div className="rounded-lg bg-amber-50 border border-amber-100 p-3 text-center">
                  <p className="text-lg font-bold text-amber-700">{preview.warnings.length}</p>
                  <p className="text-[10px] text-amber-600 uppercase font-semibold">Warnings</p>
                </div>
                <div className="rounded-lg bg-red-50 border border-red-100 p-3 text-center">
                  <p className="text-lg font-bold text-red-700">{preview.errors.length}</p>
                  <p className="text-[10px] text-red-600 uppercase font-semibold">Errores</p>
                </div>
              </div>

              {preview.warnings.length > 0 && (
                <div className="rounded-lg bg-amber-50 border border-amber-100 p-3">
                  <p className="text-[11px] font-bold text-amber-800 uppercase mb-1">Warnings</p>
                  <div className="max-h-20 overflow-y-auto space-y-1">
                    {preview.warnings.map((w, i) => (
                      <p key={i} className="text-[11px] text-amber-700 leading-tight">• {w}</p>
                    ))}
                  </div>
                </div>
              )}

              <div>
                <p className="text-[11px] font-bold text-text-secondary uppercase mb-2">Vista previa (primeras 5):</p>
                <div className="table-container rounded-lg overflow-hidden border border-border">
                  <table className="text-[11px]">
                    <thead className="bg-bg-alt/40 font-bold">
                      <tr>
                        <th className="px-3 py-2">REF</th>
                        <th className="px-3 py-2">PRECIO</th>
                        <th className="px-3 py-2">GRADE</th>
                        <th className="px-3 py-2">MOQ</th>
                        <th className="px-3 py-2">TALLAS</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {preview.preview.map((row) => (
                        <tr key={row.reference_code}>
                          <td className="px-3 py-2 font-mono text-navy font-semibold">{row.reference_code}</td>
                          <td className="px-3 py-2 font-mono text-mint font-bold">${row.unit_price_usd}</td>
                          <td className="px-3 py-2">{row.grade_label}</td>
                          <td className="px-3 py-2">{row.moq_total}</td>
                          <td className="px-3 py-2 text-text-tertiary truncate max-w-[150px]">{row.available_sizes.join(', ')}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}

          {error && (
            <div className="p-3 bg-red-50 border border-red-100 rounded-lg flex items-start gap-2">
               <AlertTriangle size={14} className="text-red-600 mt-0.5 shrink-0" />
               <p className="text-xs text-red-700">{error}</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-border bg-bg-alt/10">
          {step === 'upload' && (
            <>
              <button onClick={onClose} className="btn btn-secondary btn-sm">Cancelar</button>
              <button onClick={handleUpload} disabled={uploading} className="btn btn-primary btn-sm flex items-center gap-2">
                <Upload size={13} />
                {uploading ? 'Procesando...' : 'Previsualizar'}
              </button>
            </>
          )}
          {step === 'preview' && (
            <>
              <button onClick={() => setStep('upload')} className="btn btn-ghost btn-sm text-xs font-semibold">← Volver</button>
              <button
                onClick={handleConfirm}
                disabled={preview?.errors.length ? preview.errors.length > 0 : false}
                className="btn btn-primary btn-sm flex items-center gap-2"
              >
                <CheckCircle size={13} />
                Confirmar
              </button>
            </>
          )}
          {step === 'confirming' && (
             <button disabled className="btn btn-primary btn-sm opacity-60">Creando...</button>
          )}
        </div>
      </div>
    </div>
  );
}
