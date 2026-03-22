"use client";

import { useState } from 'react';
import { useCRUD } from '@/hooks/useCRUD';
import { useFormSubmit } from '@/hooks/useFormSubmit';
import DrawerShell from '@/components/layout/DrawerShell';
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
  const [fields, setFields] = useState<Record<string, string | File | null>>({});
  const { create } = useCRUD(`expedientes/${expedienteId}/artifacts/${ARTIFACT_ENDPOINTS[artifactType]}/`);
  
  const { handleSubmit, submitting } = useFormSubmit(async (data) => {
    const isMultipart = artifactType === 'ART-01' || artifactType === 'ART-08';
    let payload = data;
    
    if (isMultipart) {
      const formData = new FormData();
      Object.entries(data).forEach(([k, v]) => {
        if (v !== null && v !== undefined) formData.append(k, v as string | Blob);
      });
      payload = formData;
    }

    return create(payload, { multipart: isMultipart });
  }, {
    onSuccess: (res: any) => {
      if (!res.success) return; // Hook handles error toast if needed
      if (artifactType === 'ART-05') {
        toast('Artefacto registrado. ⏱ Reloj de crédito iniciado', { icon: '🕐' });
      } else {
        toast.success('Artefacto registrado');
      }
      onSuccess();
      onClose();
      setFields({});
    },
    onError: () => {} // handled by hook
  });

  const art05 = artifacts.find(a => a.artifact_type === 'ART-05');
  const art06 = artifacts.find(a => a.artifact_type === 'ART-06');
  const art07Blocked = artifactType === 'ART-07' &&
    (art05?.status !== 'COMPLETED' || art06?.status !== 'COMPLETED');

  const set = (key: string, val: string | File | null) =>
    setFields(prev => ({ ...prev, [key]: val }));

  return (
    <DrawerShell
      open={open}
      onClose={onClose}
      title={ARTIFACT_LABELS[artifactType]}
      loading={submitting}
      footer={
        <div className="flex justify-end gap-3">
          <button onClick={onClose} disabled={submitting} className="btn btn-md btn-secondary">
            Cancelar
          </button>
          <button
            onClick={() => handleSubmit(fields)}
            disabled={submitting || art07Blocked}
            className="btn btn-md btn-primary grow"
          >
            {submitting ? 'Registrando...' : 'Registrar Artefacto'}
          </button>
        </div>
      }
    >
      <div className="space-y-5">
        {art07Blocked && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 text-sm text-amber-800">
            Requiere ART-05 y ART-06 completados antes de aprobar despacho.
          </div>
        )}

        {/* ART-01: Orden de Compra */}
        {artifactType === 'ART-01' && (
          <>
            <Field label="Número PO" id="po_number" required>
              <input id="po_number" type="text" className={inputCls} onChange={e => set('po_number', e.target.value)} />
            </Field>
            <Field label="Nombre cliente" id="client_name" required>
              <input id="client_name" type="text" className={inputCls} onChange={e => set('client_name', e.target.value)} />
            </Field>
            <Field label="Monto total" id="total_amount" required>
              <input id="total_amount" type="number" min="0" step="0.01" className={inputCls} onChange={e => set('total_amount', e.target.value)} />
            </Field>
            <Field label="Moneda" id="currency" required>
              <select id="currency" className={inputCls} onChange={e => set('currency', e.target.value)}>
                <option value="">Seleccionar...</option>
                {['USD','COP','EUR'].map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </Field>
            <Field label="Fecha PO" id="po_date" required>
              <input id="po_date" type="date" className={inputCls} onChange={e => set('po_date', e.target.value)} />
            </Field>
            <Field label="Notas" id="notes">
              <textarea id="notes" rows={3} className={inputCls + ' resize-none'} onChange={e => set('notes', e.target.value)} />
            </Field>
            <Field label="Archivo PDF (opcional)" id="file">
              <input id="file" type="file" accept=".pdf" className={inputCls}
                onChange={e => set('file', e.target.files?.[0] ?? null)} />
            </Field>
          </>
        )}

        {/* ART-02: Proforma */}
        {artifactType === 'ART-02' && (
          <>
            <Field label="Monto total" id="total_amount" required>
              <input id="total_amount" type="number" min="0" step="0.01" className={inputCls} onChange={e => set('total_amount', e.target.value)} />
            </Field>
            <Field label="Moneda" id="currency" required>
              <select id="currency" className={inputCls} onChange={e => set('currency', e.target.value)}>
                <option value="">Seleccionar...</option>
                {['USD','COP','EUR'].map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </Field>
            <Field label="Fecha proforma" id="proforma_date" required>
              <input id="proforma_date" type="date" className={inputCls} onChange={e => set('proforma_date', e.target.value)} />
            </Field>
            <Field label="Válido hasta" id="valid_until" required>
              <input id="valid_until" type="date" className={inputCls} onChange={e => set('valid_until', e.target.value)} />
            </Field>
            {expedienteMode === 'COMISION' && (
              <Field label="Comisión pactada (%)" id="comision_pactada" required>
                <input id="comision_pactada" type="number" min="0" step="0.01" className={inputCls}
                  onChange={e => set('comision_pactada', e.target.value)} />
              </Field>
            )}
            <Field label="Notas" id="notes">
              <textarea id="notes" rows={3} className={inputCls + ' resize-none'} onChange={e => set('notes', e.target.value)} />
            </Field>
          </>
        )}

        {/* ART-05: AWB / BL */}
        {artifactType === 'ART-05' && (
          <>
            <Field label={freightMode === 'AEREO' ? 'AWB Number' : 'BL Number'} id="tracking_number" required>
              <input id="tracking_number" type="text" className={inputCls} onChange={e => set('tracking_number', e.target.value)} />
            </Field>
            <Field label="Transportista" id="carrier" required>
              <input id="carrier" type="text" className={inputCls} onChange={e => set('carrier', e.target.value)} />
            </Field>
            <Field label="Fecha salida" id="departure_date" required>
              <input id="departure_date" type="date" className={inputCls} onChange={e => set('departure_date', e.target.value)} />
            </Field>
            <Field label="ETA" id="eta" required>
              <input id="eta" type="date" className={inputCls} onChange={e => set('eta', e.target.value)} />
            </Field>
          </>
        )}

        {/* ART-06: Cotización Flete */}
        {artifactType === 'ART-06' && (
          <>
            <Field label="Transportista" id="carrier" required>
              <input id="carrier" type="text" className={inputCls} onChange={e => set('carrier', e.target.value)} />
            </Field>
            <Field label="Costo flete" id="freight_cost" required>
              <input id="freight_cost" type="number" min="0" step="0.01" className={inputCls} onChange={e => set('freight_cost', e.target.value)} />
            </Field>
            <Field label="Días tránsito" id="transit_days" required>
              <input id="transit_days" type="number" min="0" className={inputCls} onChange={e => set('transit_days', e.target.value)} />
            </Field>
            <Field label="ETA" id="eta" required>
              <input id="eta" type="date" className={inputCls} onChange={e => set('eta', e.target.value)} />
            </Field>
            <Field label="Puerto origen" id="origin_port" required>
              <input id="origin_port" type="text" className={inputCls} onChange={e => set('origin_port', e.target.value)} />
            </Field>
            <Field label="Puerto destino" id="destination_port" required>
              <input id="destination_port" type="text" className={inputCls} onChange={e => set('destination_port', e.target.value)} />
            </Field>
            <Field label="Tipo contenedor" id="container_type">
              <input id="container_type" type="text" className={inputCls} onChange={e => set('container_type', e.target.value)} />
            </Field>
            <Field label="Incoterm" id="incoterm">
              <input id="incoterm" type="text" className={inputCls} onChange={e => set('incoterm', e.target.value)} />
            </Field>
          </>
        )}

        {/* ART-07: Aprobación Despacho */}
        {artifactType === 'ART-07' && (
          <>
            <Field label="Aprobado por" id="approved_by" required>
              <input id="approved_by" type="text" className={inputCls} onChange={e => set('approved_by', e.target.value)} />
            </Field>
            <Field label="Fecha aprobación" id="approval_date" required>
              <input id="approval_date" type="date" className={inputCls} onChange={e => set('approval_date', e.target.value)} />
            </Field>
            <Field label="Notas" id="notes">
              <textarea id="notes" rows={3} className={inputCls + ' resize-none'} onChange={e => set('notes', e.target.value)} />
            </Field>
          </>
        )}

        {/* ART-08: Documentos Aduanal */}
        {artifactType === 'ART-08' && (
          <>
            <Field label="Agente aduanal" id="customs_agent" required>
              <input id="customs_agent" type="text" className={inputCls} onChange={e => set('customs_agent', e.target.value)} />
            </Field>
            <Field label="Costo aduanal" id="customs_cost" required>
              <input id="customs_cost" type="number" min="0" step="0.01" className={inputCls} onChange={e => set('customs_cost', e.target.value)} />
            </Field>
            <Field label="Número declaración" id="customs_declaration" required>
              <input id="customs_declaration" type="text" className={inputCls} onChange={e => set('customs_declaration', e.target.value)} />
            </Field>
            <Field label="Código arancelario" id="tariff_code" required>
              <input id="tariff_code" type="text" className={inputCls} onChange={e => set('tariff_code', e.target.value)} />
            </Field>
            <Field label="Monto impuesto" id="tax_amount" required>
              <input id="tax_amount" type="number" min="0" step="0.01" className={inputCls} onChange={e => set('tax_amount', e.target.value)} />
            </Field>
            <Field label="Modo despacho" id="dispatch_mode">
              <input id="dispatch_mode" type="text" className={inputCls + ' bg-bg-alt text-text-secondary'}
                value={dispatchMode} readOnly />
            </Field>
            <Field label="Archivo PDF" id="file_aduanal">
              <input id="file_aduanal" type="file" accept=".pdf" className={inputCls}
                onChange={e => set('file', e.target.files?.[0] ?? null)} />
            </Field>
          </>
        )}
      </div>
    </DrawerShell>
  );
}

function Field({ label, id, required, children }: { label: string; id?: string; required?: boolean; children: React.ReactNode }) {
  return (
    <div>
      <label htmlFor={id} className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5">
        {label} {required && <span className="text-critical">*</span>}
      </label>
      {children}
    </div>
  );
}

const inputCls = 'w-full bg-bg border border-border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-navy/30 transition-shadow';
