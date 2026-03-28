"use client";

import { useState } from "react";
import { X, DollarSign } from "lucide-react";
import api from "@/lib/api";
import toast from "react-hot-toast";

interface Props {
  expedienteId: number | string;
  onClose: () => void;
  onSuccess: () => void;
}

export default function ModalRegistrarPago({ expedienteId, onClose, onSuccess }: Props) {
  const [form, setForm] = useState({
    amount: "",
    currency: "USD",
    payment_date: "",
    reference: "",
    notes: "",
  });
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.amount || !form.payment_date) {
      toast.error("Monto y fecha son requeridos");
      return;
    }
    setSubmitting(true);
    try {
      await api.post(`expedientes/${expedienteId}/pagos/`, {
        amount: Number(form.amount),
        currency: form.currency,
        payment_date: form.payment_date,
        ...(form.reference ? { reference: form.reference } : {}),
        ...(form.notes ? { notes: form.notes } : {}),
      });
      toast.success("Pago registrado (PENDING)");
      onSuccess();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      toast.error(e.response?.data?.detail ?? "Error al registrar pago");
    } finally {
      setSubmitting(false);
    }
  };

  const inputCls = "w-full bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm text-[var(--color-text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-navy)]/30";
  const labelCls = "block text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider mb-1.5";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <div className="bg-[var(--color-surface)] rounded-2xl border border-[var(--color-border)] shadow-xl w-full max-w-md">
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--color-border)]">
          <div className="flex items-center gap-2">
            <DollarSign className="w-5 h-5 text-[var(--color-navy)]" />
            <h2 className="text-base font-semibold text-[var(--color-text-primary)]">Registrar pago</h2>
          </div>
          <button onClick={onClose} className="p-1.5 rounded hover:bg-[var(--color-bg-alt)] text-[var(--color-text-tertiary)] transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={labelCls}>Monto <span className="text-[var(--color-coral)]">*</span></label>
              <input type="number" name="amount" value={form.amount} onChange={handleChange} min={0} step="0.01" placeholder="0.00" required className={inputCls} />
            </div>
            <div>
              <label className={labelCls}>Moneda</label>
              <select name="currency" value={form.currency} onChange={handleChange} className={inputCls}>
                <option value="USD">USD</option>
                <option value="CRC">CRC</option>
                <option value="EUR">EUR</option>
              </select>
            </div>
          </div>

          <div>
            <label className={labelCls}>Fecha de pago <span className="text-[var(--color-coral)]">*</span></label>
            <input type="date" name="payment_date" value={form.payment_date} onChange={handleChange} required className={inputCls} />
          </div>

          <div>
            <label className={labelCls}>Referencia <span className="text-[var(--color-text-tertiary)] font-normal">(opcional)</span></label>
            <input type="text" name="reference" value={form.reference} onChange={handleChange} placeholder="Ej: TRF-2026-001" className={inputCls} />
          </div>

          <div>
            <label className={labelCls}>Notas <span className="text-[var(--color-text-tertiary)] font-normal">(opcional)</span></label>
            <textarea name="notes" value={form.notes} onChange={handleChange} rows={2} placeholder="Observaciones..." className={inputCls + " resize-none"} />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 border border-[var(--color-border)] text-[var(--color-text-secondary)] text-sm rounded-lg hover:bg-[var(--color-bg-alt)] transition-colors">
              Cancelar
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="flex items-center gap-1.5 px-4 py-2 bg-[var(--color-navy)] text-white text-sm rounded-lg hover:opacity-80 disabled:opacity-50 transition-opacity"
            >
              {submitting ? <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> : <DollarSign className="w-4 h-4" />}
              Registrar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
