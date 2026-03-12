"use client";

import { useState } from 'react';
import { createPortal } from 'react-dom';
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

  // ✅ createPortal monta el modal directamente en <body>,
  //    saltando el stacking context del Header sticky z-40
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
          <h2 className="text-base font-bold text-text-primary">🔥 Registrar Costo</h2>
          <button onClick={onClose} className="text-text-tertiary hover:text-text-primary transition-colors">
            <X size={20} />
          </button>
        </div>

        {/* Body — 2 columnas */}
        <form onSubmit={handleSubmit} className="p-6">
          <div className="grid grid-cols-2 gap-x-4 gap-y-4">

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

            {/* Descripción — 2 columnas */}
            <div className="col-span-2">
              <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5">
                Descripción <span className="text-text-tertiary font-normal">(opcional)</span>
              </label>
              <textarea
                name="description"
                value={form.description}
                onChange={handleChange}
                rows={2}
                placeholder="Descripción del costo..."
                className="w-full bg-bg border border-border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-navy/30 resize-none"
              />
            </div>

            {/* Visibilidad — 2 columnas */}
            <div className="col-span-2">
              <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-2">
                Visibilidad
              </label>
              <div className="flex items-center gap-6">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="visibility"
                    value="internal"
                    checked={form.visibility === 'internal'}
                    onChange={handleChange}
                    className="accent-navy"
                  />
                  <span className="text-sm text-text-secondary">Interno (CEO)</span>
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
              {submitting ? (
                <><span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> Registrando...</>
              ) : 'Registrar Costo'}
            </button>
          </div>
        </form>
      </div>
    </div>,
    document.body  // ← monta fuera del árbol del layout
  );
}
