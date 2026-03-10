"use client";

import { useState, useEffect } from 'react';
import { X, AlertTriangle } from 'lucide-react';
import api from '@/lib/api';
import toast from 'react-hot-toast';
import { cn } from '@/lib/utils';

interface FinancialSummary {
  total_billed_client: number;
  total_paid: number;
  payment_status: string;
  currency?: string;
}

interface RegisterPaymentDrawerProps {
  open: boolean;
  onClose: () => void;
  expedienteId: string;
  expedienteCurrency?: string;
  onSuccess: () => void;
}

const PAYMENT_METHODS = ['TRANSFERENCIA', 'EFECTIVO', 'CHEQUE', 'CRYPTO'];
const CURRENCIES = ['USD', 'COP', 'EUR'];

const PAYMENT_STATUS_STYLES: Record<string, string> = {
  'PAID':    'bg-emerald-50 text-mint border-emerald-200',
  'PARTIAL': 'bg-amber-50 text-amber-700 border-amber-200',
  'PENDING': 'bg-slate-100 text-slate-600 border-slate-200',
};

export default function RegisterPaymentDrawer({
  open, onClose, expedienteId, expedienteCurrency = 'USD', onSuccess
}: RegisterPaymentDrawerProps) {
  const [summary, setSummary] = useState<FinancialSummary | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const today = new Date().toISOString().split('T')[0];

  const [form, setForm] = useState({
    amount: '',
    currency: expedienteCurrency,
    method: '',
    reference: '',
    payment_date: today,
  });

  useEffect(() => {
    if (open) {
      setSummaryLoading(true);
      api.get(`expedientes/${expedienteId}/financial-summary/`)
        .then(res => setSummary(res.data))
        .catch(() => toast.error('No se pudo cargar resumen financiero'))
        .finally(() => setSummaryLoading(false));
      setForm(prev => ({ ...prev, currency: expedienteCurrency, payment_date: today }));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.amount || !form.method || !form.payment_date) {
      toast.error('Completa todos los campos obligatorios');
      return;
    }
    setSubmitting(true);
    try {
      await api.post(`expedientes/${expedienteId}/payments/`, {
        amount: parseFloat(form.amount),
        currency: form.currency,
        method: form.method,
        reference: form.reference || undefined,
        payment_date: form.payment_date,
      });
      toast.success('Pago registrado');
      onSuccess();
      onClose();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      toast.error(e.response?.data?.detail || 'Error al registrar pago');
    } finally {
      setSubmitting(false);
    }
  };

  if (!open) return null;

  const formatter = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' });

  return (
    <>
      <div className="fixed inset-0 bg-black/40 z-40" onClick={onClose} />
      <div className="fixed inset-y-0 right-0 w-full max-w-md bg-surface shadow-xl z-50 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-border">
          <h2 className="text-base font-bold text-text-primary">💳 Registrar Pago</h2>
          <button onClick={onClose} className="text-text-tertiary hover:text-text-primary">
            <X size={20} />
          </button>
        </div>

        {/* Financial Summary Header */}
        <div className="px-6 py-4 bg-bg-alt border-b border-border">
          {summaryLoading ? (
            <div className="flex gap-4 animate-pulse">
              <div className="h-4 bg-border rounded w-32"></div>
              <div className="h-4 bg-border rounded w-32"></div>
            </div>
          ) : summary ? (
            <div className="flex flex-wrap gap-4 text-sm">
              <div>
                <span className="text-text-tertiary">Total Facturado: </span>
                <span className="font-semibold text-text-primary">
                  {summary.total_billed_client > 0
                    ? formatter.format(summary.total_billed_client)
                    : 'Pendiente de factura'}
                </span>
              </div>
              <div>
                <span className="text-text-tertiary">Total Pagado: </span>
                <span className="font-semibold text-text-primary">{formatter.format(summary.total_paid)}</span>
              </div>
              <span className={cn(
                'px-2.5 py-1 text-xs font-semibold rounded-full border shadow-sm',
                PAYMENT_STATUS_STYLES[summary.payment_status] || 'bg-slate-100 text-slate-600 border-slate-200'
              )}>
                {summary.payment_status}
              </span>
            </div>
          ) : (
            <p className="text-sm text-text-tertiary">No se pudo cargar resumen financiero</p>
          )}
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-5">
          {/* Monto */}
          <div>
            <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5">
              Monto <span className="text-coral">*</span>
            </label>
            <input
              type="number"
              name="amount"
              value={form.amount}
              onChange={handleChange}
              min="0"
              step="0.01"
              required
              placeholder="0.00"
              className="w-full bg-bg border border-border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-navy/30"
            />
          </div>

          {/* Moneda */}
          <div>
            <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5">
              Moneda <span className="text-coral">*</span>
            </label>
            <select
              name="currency"
              value={form.currency}
              onChange={handleChange}
              className="w-full bg-bg border border-border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-navy/30"
            >
              {CURRENCIES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
            {form.currency !== expedienteCurrency && (
              <div className="mt-1.5 flex items-center gap-1.5 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
                <AlertTriangle size={14} />
                La moneda seleccionada difiere de la del expediente ({expedienteCurrency})
              </div>
            )}
          </div>

          {/* Método */}
          <div>
            <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5">
              Método <span className="text-coral">*</span>
            </label>
            <select
              name="method"
              value={form.method}
              onChange={handleChange}
              required
              className="w-full bg-bg border border-border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-navy/30"
            >
              <option value="">Seleccionar...</option>
              {PAYMENT_METHODS.map(m => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>

          {/* Referencia */}
          <div>
            <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5">
              Número de Referencia
            </label>
            <input
              type="text"
              name="reference"
              value={form.reference}
              onChange={handleChange}
              placeholder="REF-001"
              className="w-full bg-bg border border-border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-navy/30"
            />
          </div>

          {/* Fecha de Pago */}
          <div>
            <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5">
              Fecha de Pago <span className="text-coral">*</span>
            </label>
            <input
              type="date"
              name="payment_date"
              value={form.payment_date}
              onChange={handleChange}
              required
              className="w-full bg-bg border border-border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-navy/30"
            />
          </div>
        </form>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-border flex justify-end gap-3">
          <button type="button" onClick={onClose}
            className="bg-surface border border-border text-text-secondary hover:bg-bg-alt px-4 py-2 rounded-lg text-sm font-medium transition-all">
            Cancelar
          </button>
          <button onClick={handleSubmit as unknown as React.MouseEventHandler} disabled={submitting}
            className="bg-navy hover:bg-slate-800 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all shadow-sm active:scale-95 flex items-center gap-2 disabled:opacity-60">
            {submitting
              ? <><span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> Registrando...</>
              : 'Registrar Pago'}
          </button>
        </div>
      </div>
    </>
  );
}
