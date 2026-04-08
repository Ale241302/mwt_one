"use client";

import { useState, useEffect } from 'react';
import { useCRUD } from '@/hooks/useCRUD';
import { useFormSubmit } from '@/hooks/useFormSubmit';
import DrawerShell from '@/components/layout/DrawerShell';
import { AlertTriangle } from 'lucide-react';
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
  const today = new Date().toISOString().split('T')[0];

  const [form, setForm] = useState({
    amount: '',
    currency: expedienteCurrency,
    method: '',
    reference: '',
    payment_date: today,
  });

  const { create } = useCRUD(`expedientes/${expedienteId}/commands/register-payment/`);

  const { handleSubmit, submitting } = useFormSubmit(async (data) => {
    return create({
      ...data,
      amount: parseFloat(data.amount),
      reference: data.reference || undefined,
    });
  }, {
    successMessage: 'Pago registrado',
    onSuccess: () => {
      onSuccess();
      onClose();
      setForm({ amount: '', currency: expedienteCurrency, method: '', reference: '', payment_date: today });
    }
  });

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

  const formatter = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' });

  return (
    <DrawerShell
      open={open}
      onClose={onClose}
      title="💳 Registrar Pago"
      loading={submitting}
      footer={
        <div className="flex justify-end gap-3">
          <button type="button" onClick={onClose} disabled={submitting} className="btn btn-md btn-secondary">
            Cancelar
          </button>
          <button
            type="button"
            onClick={() => handleSubmit(form)}
            disabled={submitting || !form.amount || !form.method || !form.payment_date}
            className="btn btn-md btn-primary grow"
          >
            {submitting ? 'Registrando...' : 'Registrar Pago'}
          </button>
        </div>
      }
    >
      <div className="flex flex-col gap-6">
        {/* Resumen financiero */}
        <div className="bg-bg-alt/40 border border-border p-4 rounded-xl space-y-3">
          {financialSummary ? (
            <>
              <div className="flex justify-between items-center pb-2 border-b border-border/50">
                <span className="text-xs font-semibold text-text-tertiary uppercase tracking-wider">Estado de Pago</span>
                <span className={cn(
                  'px-2 py-0.5 text-[10px] font-bold rounded-full border uppercase',
                  PAYMENT_STATUS_STYLES[financialSummary.payment_status] ?? 'bg-slate-100 text-slate-600 border-slate-200'
                )}>
                  {financialSummary.payment_status}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <SummaryItem 
                  label="Total Facturado" 
                  value={financialSummary.total_billed_client > 0 ? formatter.format(financialSummary.total_billed_client) : 'Pendiente'} 
                />
                <SummaryItem label="Total Pagado" value={formatter.format(financialSummary.total_paid)} />
                <SummaryItem 
                  label="Saldo Pendiente" 
                  value={formatter.format(financialSummary.balance_pending ?? 0)} 
                  highlight 
                />
              </div>
            </>
          ) : (
            <p className="text-sm text-text-tertiary italic text-center">Resumen financiero no disponible</p>
          )}
        </div>

        {/* Form */}
        <div className="grid grid-cols-2 gap-x-4 gap-y-5">
          <Field label="Monto" required>
            <input
              type="number"
              name="amount"
              value={form.amount}
              onChange={handleChange}
              min="0"
              step="0.01"
              required
              placeholder="0.00"
              className={inputCls}
            />
          </Field>

          <Field label="Moneda" required>
            <select
              name="currency"
              value={form.currency}
              onChange={handleChange}
              className={inputCls}
            >
              {CURRENCIES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
            {form.currency !== expedienteCurrency && (
              <div className="mt-2 flex items-start gap-1.5 text-[11px] text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-2 py-1.5 leading-tight">
                <AlertTriangle size={12} className="shrink-0 mt-0.5" />
                Difiere del expediente ({expedienteCurrency})
              </div>
            )}
          </Field>

          <Field label="Método" required>
            <select
              name="method"
              value={form.method}
              onChange={handleChange}
              required
              className={inputCls}
            >
              <option value="">Seleccionar...</option>
              {PAYMENT_METHODS.map(m => <option key={m} value={m}>{m}</option>)}
            </select>
          </Field>

          <Field label="Fecha de Pago" required>
            <input
              type="date"
              name="payment_date"
              value={form.payment_date}
              onChange={handleChange}
              required
              className={inputCls}
            />
          </Field>

          <div className="col-span-2">
            <Field label="Número de Referencia">
              <input
                type="text"
                name="reference"
                value={form.reference}
                onChange={handleChange}
                placeholder="Ej: REF-00123"
                className={inputCls}
              />
            </Field>
          </div>
        </div>
      </div>
    </DrawerShell>
  );
}

function SummaryItem({ label, value, highlight = false }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="flex flex-col">
      <span className="text-[10px] text-text-tertiary uppercase font-medium">{label}</span>
      <span className={cn(
        "text-sm font-bold",
        highlight ? "text-navy" : "text-text-primary"
      )}>{value}</span>
    </div>
  );
}

function Field({ label, required, children }: { label: string; required?: boolean; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-xs font-semibold text-text-secondary uppercase tracking-wider">
        {label} {required && <span className="text-critical">*</span>}
      </label>
      {children}
    </div>
  );
}

const inputCls = 'w-full bg-bg border border-border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-navy/30 transition-shadow outline-none';
