"use client";

import { useState } from 'react';
import { FileText, X } from 'lucide-react';
import api from '@/lib/api';
import toast from 'react-hot-toast';
import { format } from 'date-fns';

interface Artifact {
  artifact_type: string;
  status: string;
  payload?: {
    total_amount?: number;
    total_usd?: number;
    currency?: string;
    comision_pactada?: number;
    incoterm?: string;
  };
}

interface InvoiceModalProps {
  open: boolean;
  onClose: () => void;
  expedienteId: string;
  clientName: string;
  expedienteMode: string;
  dispatchMode: string;
  artifacts: Artifact[];
  onSuccess: () => void;
}

export default function InvoiceModal({
  open, onClose, expedienteId, clientName, expedienteMode, dispatchMode, artifacts, onSuccess
}: InvoiceModalProps) {
  const today = format(new Date(), 'yyyy-MM-dd');
  const [invoiceNumber, setInvoiceNumber] = useState('');
  const [issuedDate, setIssuedDate] = useState(today);
  const [ivaRate, setIvaRate] = useState(19);
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // ✅ BUG 2 FIX: status en minúsculas 'completed'
  const art02 = artifacts.find(a => a.artifact_type === 'ART-02' && a.status === 'completed');
  const totalAmount = art02?.payload?.total_amount ?? art02?.payload?.total_usd ?? 0;
  const currency = art02?.payload?.currency ?? 'USD';
  const incoterm = art02?.payload?.incoterm ?? '—';
  const comision = art02?.payload?.comision_pactada;
  const isMWT = dispatchMode === 'mwt';

  const handleSubmit = async () => {
    if (!invoiceNumber.trim()) {
      toast.error('El número de factura es obligatorio');
      return;
    }
    setSubmitting(true);
    try {
      // ✅ BUG 1 FIX: URL corregida a issue-invoice/
      await api.post(`expedientes/${expedienteId}/issue-invoice/`, {
        invoice_number: invoiceNumber,
        issued_date: issuedDate,
        notes,
        ...(isMWT ? { iva_rate: ivaRate } : {}),
      });
      toast.success('Factura emitida correctamente');
      onSuccess();
      onClose();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      toast.error(e.response?.data?.detail || 'Error al emitir factura');
    } finally {
      setSubmitting(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 flex items-center justify-center z-50">
      <div className="fixed inset-0 bg-black/40" onClick={() => !submitting && onClose()} />
      <div className="relative bg-surface rounded-2xl border border-border shadow-xl p-6 w-full max-w-lg mx-4 z-10">
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-base font-bold text-text-primary flex items-center gap-2">
            <FileText className="w-5 h-5 text-navy" />
            Emitir Factura MWT
          </h3>
          <button onClick={onClose} disabled={submitting} className="text-text-tertiary hover:text-text-primary">
            <X size={18} />
          </button>
        </div>

        {/* Preview card */}
        <div className="bg-bg-alt border border-border rounded-xl p-4 mb-5 space-y-2">
          <h4 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3">Vista previa</h4>
          <Row label="Cliente" value={clientName} />
          <Row label="Total" value={`${currency} ${totalAmount.toLocaleString('es-CO', { minimumFractionDigits: 2 })}`} />
          <Row label="Incoterm" value={incoterm} />
          {expedienteMode === 'COMISION' && comision != null && (
            <Row label="Comisión pactada" value={`${comision}%`} />
          )}
        </div>

        {/* Editable fields */}
        <div className="space-y-4 mb-5">
          <div>
            <label className={labelCls}>Número de factura <span className="text-coral">*</span></label>
            <input
              type="text"
              value={invoiceNumber}
              onChange={e => setInvoiceNumber(e.target.value)}
              placeholder="Ej: MWT-2026-001"
              className={inputCls}
            />
          </div>
          <div>
            <label className={labelCls}>Fecha de emisión</label>
            <input
              type="date"
              value={issuedDate}
              onChange={e => setIssuedDate(e.target.value)}
              className={inputCls}
            />
          </div>
          {isMWT && (
            <div>
              <label className={labelCls}>IVA (%)</label>
              <input
                type="number"
                min="0"
                max="100"
                value={ivaRate}
                onChange={e => setIvaRate(Number(e.target.value))}
                className={inputCls}
              />
            </div>
          )}
          <div>
            <label className={labelCls}>Notas (opcional)</label>
            <textarea
              rows={3}
              value={notes}
              onChange={e => setNotes(e.target.value)}
              className={inputCls + ' resize-none'}
            />
          </div>
        </div>

        <div className="flex justify-end gap-3">
          <button
            onClick={onClose}
            disabled={submitting}
            className="bg-surface border border-border text-text-secondary hover:bg-bg-alt px-4 py-2 rounded-lg text-sm font-medium"
          >
            Cancelar
          </button>
          <button
            onClick={handleSubmit}
            disabled={submitting || !invoiceNumber.trim()}
            className="bg-navy hover:bg-slate-800 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all shadow-sm active:scale-95 flex items-center gap-2 disabled:opacity-50"
          >
            {submitting ? (
              <><span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> Emitiendo...</>
            ) : (
              <><FileText size={14} /> Emitir Factura</>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between text-sm">
      <span className="text-text-secondary">{label}</span>
      <span className="font-medium text-text-primary">{value}</span>
    </div>
  );
}

const labelCls = 'block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5';
const inputCls = 'w-full bg-bg border border-border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-navy/30';
