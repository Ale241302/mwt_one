"use client";

import { useState } from 'react';
import { X } from 'lucide-react';
import api from '@/lib/api';
import toast from 'react-hot-toast';

interface RegisterCostDrawerProps {
  open: boolean;
  onClose: () => void;
  expedienteId: string;
  onSuccess: () => void;
}

const COST_TYPES = ['FLETE', 'ADUANA', 'ALMACENAJE', 'SEGURO', 'HONORARIOS', 'OTRO'];
const CURRENCIES = ['USD', 'COP', 'EUR'];
const PHASES = ['PRODUCCION', 'TRANSITO', 'DESTINO', 'GENERAL'];

export default function RegisterCostDrawer({ open, onClose, expedienteId, onSuccess }: RegisterCostDrawerProps) {
  const [form, setForm] = useState({
    cost_type: '',
    amount: '',
    currency: 'USD',
    phase: '',
    description: '',
    visibility: 'internal' as 'internal' | 'client',
  });
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement | HTMLTextAreaElement | HTMLInputElement>) => {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.cost_type || !form.amount || !form.phase) {
      toast.error('Completa los campos obligatorios');
      return;
    }
    setSubmitting(true);
    try {
      await api.post(`expedientes/${expedienteId}/costs/`, {
        cost_type: form.cost_type,
        amount: parseFloat(form.amount),
        currency: form.currency,
        phase: form.phase,
        description: form.description || undefined,
        visibility: form.visibility,
      });
      toast.success('Costo registrado');
      onSuccess();
      onClose();
      setForm({ cost_type: '', amount: '', currency: 'USD', phase: '', description: '', visibility: 'internal' });
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      toast.error(e.response?.data?.detail || 'Error al registrar costo');
    } finally {
      setSubmitting(false);
    }
  };

  if (!open) return null;

  return (
    <>
      <div className="fixed inset-0 bg-black/40 z-40" onClick={onClose} />
      <div className="fixed inset-y-0 right-0 w-full max-w-md bg-surface shadow-xl z-50 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-border">
          <h2 className="text-base font-bold text-text-primary">💰 Registrar Costo</h2>
          <button onClick={onClose} className="text-text-tertiary hover:text-text-primary transition-colors">
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-5">
          {/* Tipo de Costo */}
          <div>
            <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5">
              Tipo de Costo <span className="text-coral">*</span>
            </label>
            <select
              name="cost_type"
              value={form.cost_type}
              onChange={handleChange}
              required
              className="w-full bg-bg border border-border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-navy/30"
            >
              <option value="">Seleccionar...</option>
              {COST_TYPES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>

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
          </div>

          {/* Fase */}
          <div>
            <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5">
              Fase <span className="text-coral">*</span>
            </label>
            <select
              name="phase"
              value={form.phase}
              onChange={handleChange}
              required
              className="w-full bg-bg border border-border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-navy/30"
            >
              <option value="">Seleccionar...</option>
              {PHASES.map(p => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>

          {/* Descripción */}
          <div>
            <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5">
              Descripción <span className="text-text-tertiary font-normal">(opcional)</span>
            </label>
            <textarea
              name="description"
              value={form.description}
              onChange={handleChange}
              rows={3}
              placeholder="Descripción del costo..."
              className="w-full bg-bg border border-border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-navy/30 resize-none"
            />
          </div>

          {/* Visibilidad */}
          <div>
            <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-2">
              Visibilidad
            </label>
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="visibility"
                  value="internal"
                  checked={form.visibility === 'internal'}
                  onChange={handleChange}
                  className="accent-navy"
                />
                <span className="text-sm text-text-secondary">Interno</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="visibility"
                  value="client"
                  checked={form.visibility === 'client'}
                  onChange={handleChange}
                  className="accent-navy"
                />
                <span className="text-sm text-text-secondary">Cliente</span>
              </label>
            </div>
          </div>
        </form>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-border flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="bg-surface border border-border text-text-secondary hover:bg-bg-alt px-4 py-2 rounded-lg text-sm font-medium transition-all"
          >
            Cancelar
          </button>
          <button
            onClick={handleSubmit as unknown as React.MouseEventHandler}
            disabled={submitting}
            className="bg-navy hover:bg-slate-800 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all shadow-sm active:scale-95 flex items-center gap-2 disabled:opacity-60"
          >
            {submitting ? (
              <><span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> Registrando...</>
            ) : 'Registrar Costo'}
          </button>
        </div>
      </div>
    </>
  );
}
