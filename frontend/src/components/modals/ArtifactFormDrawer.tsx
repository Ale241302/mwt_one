"use client";

import { useState } from 'react';
import { X } from 'lucide-react';
import api from '@/lib/api';
import toast from 'react-hot-toast';

type ArtifactType = 'ART-01' | 'ART-02' | 'ART-05' | 'ART-06' | 'ART-07' | 'ART-08';

interface Artifact {
  artifact_type: string;
  status: string;
  payload?: Record<string, unknown>;
}

interface ArtifactFormDrawerProps {
  open: boolean;
  onClose: () => void;
  expedienteId: string;
  artifactType: ArtifactType;
  expedienteMode: string;
  freightMode: string;
  dispatchMode: string;
  artifacts: Artifact[];
  onSuccess: () => void;
}

const ARTIFACT_LABELS: Record<ArtifactType, string> = {
  'ART-01': 'Orden de Compra',
  'ART-02': 'Proforma MWT',
  'ART-05': 'AWB / BL',
  'ART-06': 'Cotización Flete',
  'ART-07': 'Aprobación Despacho',
  'ART-08': 'Documentos Aduanal',
};

const ARTIFACT_ENDPOINTS: Record<ArtifactType, string> = {
  'ART-01': 'purchase-order',
  'ART-02': 'proforma',
  'ART-05': 'shipment',
  'ART-06': 'freight-quote',
  'ART-07': 'dispatch-approval',
  'ART-08': 'customs',
};

export default function ArtifactFormDrawer({
  open, onClose, expedienteId, artifactType,
  expedienteMode, freightMode, dispatchMode, artifacts, onSuccess
}: ArtifactFormDrawerProps) {
  const [submitting, setSubmitting] = useState(false);
  const [fields, setFields] = useState<Record<string, string | File | null>>({});

  const art05 = artifacts.find(a => a.artifact_type === 'ART-05');
  const art06 = artifacts.find(a => a.artifact_type === 'ART-06');
  const art07Blocked = artifactType === 'ART-07' &&
    (art05?.status !== 'COMPLETED' || art06?.status !== 'COMPLETED');

  const set = (key: string, val: string | File | null) =>
    setFields(prev => ({ ...prev, [key]: val }));

  const handleSubmit = async () => {
    if (art07Blocked) return;
    setSubmitting(true);
    try {
      const endpoint = ARTIFACT_ENDPOINTS[artifactType];
      const isMultipart = artifactType === 'ART-01' || artifactType === 'ART-08';

      if (isMultipart) {
        const formData = new FormData();
        Object.entries(fields).forEach(([k, v]) => {
          if (v !== null && v !== undefined) formData.append(k, v as string | Blob);
        });
        await api.post(`expedientes/${expedienteId}/artifacts/${endpoint}/`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
      } else {
        await api.post(`expedientes/${expedienteId}/artifacts/${endpoint}/`, fields);
      }

      if (artifactType === 'ART-05') {
        toast('Artefacto registrado. ⏱ Reloj de crédito iniciado', { icon: '🕐' });
      } else {
        toast.success('Artefacto registrado');
      }
      onSuccess();
      onClose();
      setFields({});
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      toast.error(e.response?.data?.detail || 'Error al registrar artefacto');
    } finally {
      setSubmitting(false);
    }
  };

  if (!open) return null;

  return (
    <>
      <div className="fixed inset-0 bg-black/40 z-40" onClick={() => !submitting && onClose()} />
      <div className="fixed inset-y-0 right-0 w-full max-w-md bg-surface shadow-xl z-50 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <h3 className="text-base font-bold text-text-primary">
            {ARTIFACT_LABELS[artifactType]}
          </h3>
          <button onClick={onClose} disabled={submitting} className="text-text-tertiary hover:text-text-primary">
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-4">
          {art07Blocked && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 text-sm text-amber-800">
              Requiere ART-05 y ART-06 completados antes de aprobar despacho.
            </div>
          )}

          {/* ART-01: Orden de Compra */}
          {artifactType === 'ART-01' && (
            <>
              <Field label="Número PO" required>
                <input type="text" className={inputCls} onChange={e => set('po_number', e.target.value)} />
              </Field>
              <Field label="Nombre cliente" required>
                <input type="text" className={inputCls} onChange={e => set('client_name', e.target.value)} />
              </Field>
              <Field label="Monto total" required>
                <input type="number" min="0" step="0.01" className={inputCls} onChange={e => set('total_amount', e.target.value)} />
              </Field>
              <Field label="Moneda" required>
                <select className={inputCls} onChange={e => set('currency', e.target.value)}>
                  <option value="">Seleccionar...</option>
                  {['USD','COP','EUR'].map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </Field>
              <Field label="Fecha PO" required>
                <input type="date" className={inputCls} onChange={e => set('po_date', e.target.value)} />
              </Field>
              <Field label="Notas">
                <textarea rows={3} className={inputCls + ' resize-none'} onChange={e => set('notes', e.target.value)} />
              </Field>
              <Field label="Archivo PDF (opcional)">
                <input type="file" accept=".pdf" className={inputCls}
                  onChange={e => set('file', e.target.files?.[0] ?? null)} />
              </Field>
            </>
          )}

          {/* ART-02: Proforma */}
          {artifactType === 'ART-02' && (
            <>
              <Field label="Monto total" required>
                <input type="number" min="0" step="0.01" className={inputCls} onChange={e => set('total_amount', e.target.value)} />
              </Field>
              <Field label="Moneda" required>
                <select className={inputCls} onChange={e => set('currency', e.target.value)}>
                  <option value="">Seleccionar...</option>
                  {['USD','COP','EUR'].map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </Field>
              <Field label="Fecha proforma" required>
                <input type="date" className={inputCls} onChange={e => set('proforma_date', e.target.value)} />
              </Field>
              <Field label="Válido hasta" required>
                <input type="date" className={inputCls} onChange={e => set('valid_until', e.target.value)} />
              </Field>
              {expedienteMode === 'COMISION' && (
                <Field label="Comisión pactada (%)" required>
                  <input type="number" min="0" step="0.01" className={inputCls}
                    onChange={e => set('comision_pactada', e.target.value)} />
                </Field>
              )}
              <Field label="Notas">
                <textarea rows={3} className={inputCls + ' resize-none'} onChange={e => set('notes', e.target.value)} />
              </Field>
            </>
          )}

          {/* ART-05: AWB / BL */}
          {artifactType === 'ART-05' && (
            <>
              <Field label={freightMode === 'AEREO' ? 'AWB Number' : 'BL Number'} required>
                <input type="text" className={inputCls} onChange={e => set('tracking_number', e.target.value)} />
              </Field>
              <Field label="Transportista" required>
                <input type="text" className={inputCls} onChange={e => set('carrier', e.target.value)} />
              </Field>
              <Field label="Fecha salida" required>
                <input type="date" className={inputCls} onChange={e => set('departure_date', e.target.value)} />
              </Field>
              <Field label="ETA" required>
                <input type="date" className={inputCls} onChange={e => set('eta', e.target.value)} />
              </Field>
            </>
          )}

          {/* ART-06: Cotización Flete */}
          {artifactType === 'ART-06' && (
            <>
              <Field label="Transportista" required>
                <input type="text" className={inputCls} onChange={e => set('carrier', e.target.value)} />
              </Field>
              <Field label="Costo flete" required>
                <input type="number" min="0" step="0.01" className={inputCls} onChange={e => set('freight_cost', e.target.value)} />
              </Field>
              <Field label="Días tránsito" required>
                <input type="number" min="0" className={inputCls} onChange={e => set('transit_days', e.target.value)} />
              </Field>
              <Field label="ETA" required>
                <input type="date" className={inputCls} onChange={e => set('eta', e.target.value)} />
              </Field>
              <Field label="Puerto origen" required>
                <input type="text" className={inputCls} onChange={e => set('origin_port', e.target.value)} />
              </Field>
              <Field label="Puerto destino" required>
                <input type="text" className={inputCls} onChange={e => set('destination_port', e.target.value)} />
              </Field>
              <Field label="Tipo contenedor">
                <input type="text" className={inputCls} onChange={e => set('container_type', e.target.value)} />
              </Field>
              <Field label="Incoterm">
                <input type="text" className={inputCls} onChange={e => set('incoterm', e.target.value)} />
              </Field>
            </>
          )}

          {/* ART-07: Aprobación Despacho */}
          {artifactType === 'ART-07' && (
            <>
              <Field label="Aprobado por" required>
                <input type="text" className={inputCls} onChange={e => set('approved_by', e.target.value)} />
              </Field>
              <Field label="Fecha aprobación" required>
                <input type="date" className={inputCls} onChange={e => set('approval_date', e.target.value)} />
              </Field>
              <Field label="Notas">
                <textarea rows={3} className={inputCls + ' resize-none'} onChange={e => set('notes', e.target.value)} />
              </Field>
            </>
          )}

          {/* ART-08: Documentos Aduanal */}
          {artifactType === 'ART-08' && (
            <>
              <Field label="Agente aduanal" required>
                <input type="text" className={inputCls} onChange={e => set('customs_agent', e.target.value)} />
              </Field>
              <Field label="Costo aduanal" required>
                <input type="number" min="0" step="0.01" className={inputCls} onChange={e => set('customs_cost', e.target.value)} />
              </Field>
              <Field label="Número declaración" required>
                <input type="text" className={inputCls} onChange={e => set('customs_declaration', e.target.value)} />
              </Field>
              <Field label="Código arancelario" required>
                <input type="text" className={inputCls} onChange={e => set('tariff_code', e.target.value)} />
              </Field>
              <Field label="Monto impuesto" required>
                <input type="number" min="0" step="0.01" className={inputCls} onChange={e => set('tax_amount', e.target.value)} />
              </Field>
              <Field label="Modo despacho">
                <input type="text" className={inputCls + ' bg-bg-alt text-text-secondary'}
                  value={dispatchMode} readOnly />
              </Field>
              <Field label="Archivo PDF">
                <input type="file" accept=".pdf" className={inputCls}
                  onChange={e => set('file', e.target.files?.[0] ?? null)} />
              </Field>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-border flex justify-end gap-3">
          <button onClick={onClose} disabled={submitting}
            className="bg-surface border border-border text-text-secondary hover:bg-bg-alt px-4 py-2 rounded-lg text-sm font-medium">
            Cancelar
          </button>
          <button
            onClick={handleSubmit}
            disabled={submitting || art07Blocked}
            title={art07Blocked ? 'Requiere ART-05 y ART-06 completados' : undefined}
            className="bg-navy hover:bg-slate-800 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all shadow-sm active:scale-95 flex items-center gap-2 disabled:opacity-50"
          >
            {submitting ? (
              <><span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> Registrando...</>
            ) : 'Registrar Artefacto'}
          </button>
        </div>
      </div>
    </>
  );
}

function Field({ label, required, children }: { label: string; required?: boolean; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5">
        {label} {required && <span className="text-coral">*</span>}
      </label>
      {children}
    </div>
  );
}

const inputCls = 'w-full bg-bg border border-border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-navy/30';
