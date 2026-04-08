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

  const inputCls = "w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-500 transition-all shadow-sm";
  const labelCls = "block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl w-full max-w-md overflow-hidden transform animate-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between px-6 py-5 border-b border-slate-100 bg-slate-50/50">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-red-50 flex items-center justify-center">
              <DollarSign className="w-4 h-4 text-red-600" />
            </div>
            <h2 className="text-base font-bold text-slate-800">Registrar pago</h2>
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
              className="flex items-center gap-1.5 px-6 py-2 bg-red-600 text-white font-semibold text-sm rounded-lg hover:bg-red-700 disabled:opacity-50 transition-all shadow-md active:scale-95"
            >
              {submitting ? <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> : <DollarSign className="w-4 h-4" />}
              Registrar pago
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
