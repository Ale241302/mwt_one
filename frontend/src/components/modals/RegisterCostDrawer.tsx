"use client";

import { useState } from 'react';
import { useCRUD } from '@/hooks/useCRUD';
import { useFormSubmit } from '@/hooks/useFormSubmit';
import DrawerShell from '@/components/layout/DrawerShell';

interface RegisterCostDrawerProps {
  open: boolean;
  onClose: () => void;
  expedienteId: string;
  onSuccess: () => void;
}

const COST_TYPES = ['FLETE', 'ADUANA', 'ALMACENAJE', 'SEGURO', 'HONORARIOS', 'OTRO'];
const CURRENCIES = ['USD', 'COP', 'EUR'];
const PHASES = ['REGISTRO', 'PRODUCCION', 'PREPARACION', 'DESPACHO', 'TRANSITO', 'EN_DESTINO'];

export default function RegisterCostDrawer({ open, onClose, expedienteId, onSuccess }: RegisterCostDrawerProps) {
  const [form, setForm] = useState({
    cost_type: '',
    amount: '',
    currency: 'USD',
    phase: '',
    description: '',
    visibility: 'internal' as 'internal' | 'client',
  });

  const { create } = useCRUD(`expedientes/${expedienteId}/register-cost/`);

  const { handleSubmit, submitting } = useFormSubmit(async (data) => {
    return create({
      ...data,
      amount: parseFloat(data.amount),
      description: data.description || undefined,
    });
  }, {
    successMessage: 'Costo registrado',
    onSuccess: () => {
      onSuccess();
      onClose();
      setForm({ cost_type: '', amount: '', currency: 'USD', phase: '', description: '', visibility: 'internal' });
    }
  });

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement | HTMLTextAreaElement | HTMLInputElement>) => {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  return (
    <DrawerShell
      open={open}
      onClose={onClose}
      title="🔥 Registrar Costo"
      loading={submitting}
      maxWidth="md"
      footer={
        <div className="flex justify-end gap-3">
          <button type="button" onClick={onClose} disabled={submitting} className="btn btn-md btn-secondary">
            Cancelar
          </button>
          <button
            type="button"
            onClick={() => handleSubmit(form)}
            disabled={submitting || !form.cost_type || !form.amount || !form.phase}
            className="btn btn-md btn-primary grow"
          >
            {submitting ? 'Registrando...' : 'Registrar Costo'}
          </button>
        </div>
      }
    >
      <div className="grid grid-cols-2 gap-x-4 gap-y-5">
        {/* Tipo de Costo */}
        <Field label="Tipo de Costo" required>
          <select
            name="cost_type"
            value={form.cost_type}
            onChange={handleChange}
            className={inputCls}
          >
            <option value="">Seleccionar...</option>
            {COST_TYPES.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </Field>

        {/* Fase */}
        <Field label="Fase" required>
          <select
            name="phase"
            value={form.phase}
            onChange={handleChange}
            className={inputCls}
          >
            <option value="">Seleccionar...</option>
            {PHASES.map(p => <option key={p} value={p}>{p}</option>)}
          </select>
        </Field>

        {/* Monto */}
        <Field label="Monto" required>
          <input
            type="number"
            name="amount"
            value={form.amount}
            onChange={handleChange}
            min="0"
            step="0.01"
            placeholder="0.00"
            className={inputCls}
          />
        </Field>

        {/* Moneda */}
        <Field label="Moneda" required>
          <select
            name="currency"
            value={form.currency}
            onChange={handleChange}
            className={inputCls}
          >
            {CURRENCIES.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </Field>

        {/* Descripción */}
        <div className="col-span-2">
          <Field label="Descripción">
            <textarea
              name="description"
              value={form.description}
              onChange={handleChange}
              rows={3}
              placeholder="Descripción del costo..."
              className={inputCls + ' resize-none'}
            />
          </Field>
        </div>

        {/* Visibilidad */}
        <div className="col-span-2">
          <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-2.5">
            Visibilidad
          </label>
          <div className="flex items-center gap-8 bg-bg-alt/40 p-3 rounded-lg border border-border/50">
            <label className="flex items-center gap-2.5 cursor-pointer group">
              <input
                type="radio"
                name="visibility"
                value="internal"
                checked={form.visibility === 'internal'}
                onChange={handleChange}
                className="w-4 h-4 text-navy focus:ring-navy border-gray-300"
              />
              <span className="text-sm text-text-secondary group-hover:text-text-primary transition-colors">Interno (CEO)</span>
            </label>
            <label className="flex items-center gap-2.5 cursor-pointer group">
              <input
                type="radio"
                name="visibility"
                value="client"
                checked={form.visibility === 'client'}
                onChange={handleChange}
                className="w-4 h-4 text-navy focus:ring-navy border-gray-300"
              />
              <span className="text-sm text-text-secondary group-hover:text-text-primary transition-colors">Cliente</span>
            </label>
          </div>
        </div>
      </div>
    </DrawerShell>
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
