// S22-14 — Modal Upload → Preview → Confirm
"use client";

import React, { useRef, useState } from 'react';
import { X, Upload, CheckCircle, AlertTriangle, FileText } from 'lucide-react';
import type { PriceListVersion } from '@/components/brand-console/PricingTab';

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
  onClose: () => void;
  onConfirm: (version: PriceListVersion) => void;
}

export function UploadPreviewModal({ onClose, onConfirm }: Props) {
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
    // TODO: reemplazar mock con llamada real a POST /api/pricing/pricelists/upload/
    await new Promise((r) => setTimeout(r, 1200));
    const mockPreview: UploadPreviewResponse = {
      valid_lines: 142,
      warnings: ['Referencia MRL-0045: sin NCM asignado', 'Referencia MRL-0091: talla 47/48 sin multiplicador'],
      errors: [],
      preview: [
        { reference_code: 'MRL-0001', unit_price_usd: '28.50', grade_label: 'G1 (33-38)', moq_total: 12, available_sizes: ['33/34','35/36','37/38'] },
        { reference_code: 'MRL-0002', unit_price_usd: '31.00', grade_label: 'G2 (39-44)', moq_total: 12, available_sizes: ['39/40','41/42','43/44'] },
        { reference_code: 'MRL-0003', unit_price_usd: '34.75', grade_label: 'G3 (45-48)', moq_total: 6,  available_sizes: ['45/46','47/48'] },
        { reference_code: 'MRL-0004', unit_price_usd: '29.20', grade_label: 'G1 (33-38)', moq_total: 12, available_sizes: ['33/34','35/36','37/38'] },
        { reference_code: 'MRL-0005', unit_price_usd: '32.10', grade_label: 'G2 (39-44)', moq_total: 12, available_sizes: ['39/40','41/42','43/44'] },
      ],
      session_id: 'sess_abc123',
    };
    setPreview(mockPreview);
    setStep('preview');
    setUploading(false);
  };

  const handleConfirm = async () => {
    if (!preview) return;
    setStep('confirming');
    // TODO: llamar POST /api/pricing/pricelists/confirm/ con session_id
    await new Promise((r) => setTimeout(r, 900));
    const newVersion: PriceListVersion = {
      id: Date.now(),
      version_label: versionLabel,
      is_active: false,
      activated_at: null,
      deactivated_at: null,
      deactivation_reason: null,
      uploaded_by: 'usuario@mwt.com',
      notes,
      items_count: preview.valid_lines,
    };
    onConfirm(newVersion);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <h2 className="heading-lg">
            {step === 'upload' && 'Subir nueva pricelist'}
            {step === 'preview' && 'Vista previa antes de confirmar'}
            {step === 'confirming' && 'Creando versión...'}
          </h2>
          <button onClick={onClose} className="btn btn-ghost btn-sm p-2"><X size={16} /></button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5">
          {step === 'upload' && (
            <>
              <div>
                <label className="block text-xs font-medium text-text-secondary mb-1.5">Nombre de versión *</label>
                <input
                  type="text"
                  value={versionLabel}
                  onChange={(e) => setVersionLabel(e.target.value)}
                  placeholder="Ej: Marluvas Q2-2026"
                  className="w-full border border-border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-text-secondary mb-1.5">Notas (opcional)</label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={2}
                  className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 resize-none"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-text-secondary mb-1.5">Archivo CSV o Excel *</label>
                <div
                  onClick={() => fileRef.current?.click()}
                  className="border-2 border-dashed border-border rounded-xl p-8 text-center cursor-pointer hover:border-brand/50 hover:bg-brand/5 transition-all"
                >
                  <FileText size={28} className="mx-auto mb-2 text-text-tertiary" />
                  {file ? (
                    <p className="text-sm font-medium text-text-primary">{file.name}</p>
                  ) : (
                    <p className="text-sm text-text-tertiary">Haz clic para seleccionar CSV o .xlsx</p>
                  )}
                  <input ref={fileRef} type="file" accept=".csv,.xlsx,.xls" onChange={handleFileChange} className="hidden" />
                </div>
              </div>
              {error && (
                <p className="text-xs text-red-600 flex items-center gap-1">
                  <AlertTriangle size={12} /> {error}
                </p>
              )}
            </>
          )}

          {(step === 'preview' || step === 'confirming') && preview && (
            <>
              {/* Stats */}
              <div className="grid grid-cols-3 gap-3">
                <div className="rounded-lg bg-emerald-50 border border-emerald-200 p-3 text-center">
                  <p className="text-lg font-bold text-emerald-700">{preview.valid_lines}</p>
                  <p className="text-xs text-emerald-600">Líneas válidas</p>
                </div>
                <div className="rounded-lg bg-amber-50 border border-amber-200 p-3 text-center">
                  <p className="text-lg font-bold text-amber-700">{preview.warnings.length}</p>
                  <p className="text-xs text-amber-600">Warnings</p>
                </div>
                <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-center">
                  <p className="text-lg font-bold text-red-700">{preview.errors.length}</p>
                  <p className="text-xs text-red-600">Errores</p>
                </div>
              </div>

              {/* Warnings */}
              {preview.warnings.length > 0 && (
                <div className="rounded-lg bg-amber-50 border border-amber-200 p-3 space-y-1">
                  <p className="text-xs font-semibold text-amber-700">Warnings ({preview.warnings.length})</p>
                  {preview.warnings.map((w, i) => (
                    <p key={i} className="text-xs text-amber-700">• {w}</p>
                  ))}
                </div>
              )}

              {/* Preview table */}
              <div>
                <p className="text-xs font-medium text-text-secondary mb-2">Primeras 5 líneas:</p>
                <div className="table-container rounded-lg overflow-hidden">
                  <table className="text-xs">
                    <thead>
                      <tr>
                        <th>Referencia</th>
                        <th>Precio USD</th>
                        <th>Grade</th>
                        <th>MOQ</th>
                        <th>Tallas</th>
                      </tr>
                    </thead>
                    <tbody>
                      {preview.preview.map((row) => (
                        <tr key={row.reference_code}>
                          <td className="font-mono">{row.reference_code}</td>
                          <td className="font-mono">${row.unit_price_usd}</td>
                          <td>{row.grade_label}</td>
                          <td>{row.moq_total}</td>
                          <td className="text-text-tertiary">{row.available_sizes.join(', ')}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-border">
          {step === 'upload' && (
            <>
              <button onClick={onClose} className="btn btn-secondary btn-sm">Cancelar</button>
              <button onClick={handleUpload} disabled={uploading} className="btn btn-primary btn-sm flex items-center gap-2 disabled:opacity-60">
                <Upload size={13} />
                {uploading ? 'Subiendo...' : 'Subir y previsualizar'}
              </button>
            </>
          )}
          {step === 'preview' && (
            <>
              <button onClick={() => setStep('upload')} className="btn btn-secondary btn-sm">← Volver</button>
              <button
                onClick={handleConfirm}
                disabled={preview?.errors.length ? preview.errors.length > 0 : false}
                className="btn btn-primary btn-sm flex items-center gap-2 disabled:opacity-60"
              >
                <CheckCircle size={13} />
                Confirmar y crear versión
              </button>
            </>
          )}
          {step === 'confirming' && (
            <button disabled className="btn btn-primary btn-sm opacity-60">Creando versión...</button>
          )}
        </div>
      </div>
    </div>
  );
}
