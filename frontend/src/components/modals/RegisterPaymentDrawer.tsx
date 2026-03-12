"use client";

import { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { X, AlertTriangle } from 'lucide-react';
import api from '@/lib/api';
import toast from 'react-hot-toast';
import { cn } from '@/lib/utils';

interface FinancialSummary {
  total_billed_client: number;
  total_paid: number;
  balance_pending: number;
  payment_status: string;
  currency?: string;
}

interface RegisterPaymentDrawerProps {
  open: boolean;
  onClose: () => void;
  expedienteId: string;
  expedienteCurrency?: string;
  financialSummary?: FinancialSummary | null;
  onSuccess: () => void;
}

const PAYMENT_METHODS = ['TRANSFERENCIA', 'EFECTIVO', 'CHEQUE', 'CRYPTO'];
const CURRENCIES = ['USD', 'COP', 'EUR'];

const PAYMENT_STATUS_STYLES: Record<string, string> = {
  'PAID': 'bg-emerald-50 text-mint border-emerald-200',
  'PARTIAL': 'bg-amber-50 text-amber-700 border-amber-200',
  'PENDING': 'bg-slate-100 text-slate-600 border-slate-200',
};

export default function RegisterPaymentDrawer({
  open, onClose, expedienteId, expedienteCurrency = 'USD',
  financialSummary = null,
  onSuccess,
}: RegisterPaymentDrawerProps) {
  const [submitting, setSubmitting] = useState(false);
  const today = new Date().toISOString().split('T')[0];

  const [form, setForm] = useState({
    amount: '',
    currency: expedienteCurrency,
    method: '',
    reference: '',
    payment_date: today,
  });

  // Resetea moneda y fecha cada vez que se abre
  useEffect(() => {
    if (open) {
      setForm(prev => ({
        ...prev,
        currency: expedienteCurrency,
        payment_date: new Date().toISOString().split('T')[0],
      }));
    }
  }, [open, expedienteCurrency]);

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
      await api.post(`expedientes/${expedienteId}/register-payment/`, {
        amount: parseFloat(form.amount),
        currency: form.currency,
        method: form.method,
        reference: form.reference || undefined,
        payment_date: form.payment_date,
      });
      toast.success('Pago registrado');
      onSuccess();
      onClose();
      setForm({ amount: '', currency: expedienteCurrency, method: '', reference: '', payment_date: today });
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      toast.error(e.response?.data?.detail || 'Error al registrar pago');
    } finally {
      setSubmitting(false);
    }
  };

  if (!open) return null;

  const formatter = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' });

  return createPortal(
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 px-4"
      onClick={onClose}
    >
      <div
        className="bg-surface w-full max-w-lg rounded-xl shadow-2xl flex flex-col overflow-hidden"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <h2 className="text-base font-bold text-text-primary">💳 Registrar Pago</h2>
          <button onClick={onClose} className="text-text-tertiary hover:text-text-primary transition-colors">
            <X size={20} />
          </button>
        </div>

        {/* Resumen financiero — viene del prop, sin fetch */}
        <div className="px-6 py-3 bg-bg-alt border-b border-border">
          {financialSummary ? (
            <div className="flex flex-wrap items-center gap-4 text-sm">
              <div>
                <span className="text-text-tertiary">Total Facturado: </span>
                <span className="font-semibold text-text-primary">
                  {financialSummary.total_billed_client > 0
                    ? formatter.format(financialSummary.total_billed_client)
                    : 'Pendiente de factura'}
                </span>
              </div>
              <div>
                <span className="text-text-tertiary">Total Pagado: </span>
                <span className="font-semibold text-text-primary">
                  {formatter.format(financialSummary.total_paid)}
                </span>
              </div>
              <div>
                <span className="text-text-tertiary">Saldo Pendiente: </span>
                <span className="font-semibold text-text-primary">
                  {formatter.format(financialSummary.balance_pending ?? 0)}
                </span>
              </div>
              <span className={cn(
                'px-2.5 py-1 text-xs font-semibold rounded-full border',
                PAYMENT_STATUS_STYLES[financialSummary.payment_status] ?? 'bg-slate-100 text-slate-600 border-slate-200'
              )}>
                {financialSummary.payment_status}
              </span>
            </div>
          ) : (
            <p className="text-sm text-text-tertiary italic">Resumen financiero no disponible</p>
          )}
        </div>

        {/* Form — 2 columnas */}
        <form onSubmit={handleSubmit} className="p-6">
          <div className="grid grid-cols-2 gap-x-4 gap-y-4">

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
                <div className="mt-1.5 flex items-center gap-1.5 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-2 py-1.5">
                  <AlertTriangle size={12} />
                  Difiere del expediente ({expedienteCurrency})
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

            {/* Referencia — 2 columnas */}
            <div className="col-span-2">
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
          </div>

          {/* Footer */}
          <div className="mt-6 flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="bg-surface border border-border text-text-secondary hover:bg-bg-alt px-4 py-2 rounded-lg text-sm font-medium transition-all"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="bg-navy hover:bg-slate-800 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all shadow-sm active:scale-95 flex items-center gap-2 disabled:opacity-60"
            >
              {submitting
                ? <><span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> Registrando...</>
                : 'Registrar Pago'}
            </button>
          </div>
        </form>
      </div>
    </div>,
    document.body
  );
}
