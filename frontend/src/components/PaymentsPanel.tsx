"use client";

import { useState } from 'react';
import { cn } from '@/lib/utils';
import api from '@/lib/api';
import toast from 'react-hot-toast';
import { DollarSign, CreditCard, CheckCircle2, Clock, AlertTriangle } from 'lucide-react';

interface PaymentLine {
    payment_line_id: string;
    amount: number;
    currency: string;
    method: string;
    reference: string;
    created_at: string;
}

interface PaymentsPanelProps {
    expedienteId: string;
    payments: PaymentLine[];
    paymentStatus: string;     // 'pending' | 'partial' | 'paid'
    totalInvoiced: number;     // total de ART-09
    totalPaid: number;         // sum of PaymentLines
    currency: string;
    onPaymentRegistered?: () => void;
}

const STATUS_CONFIG = {
    pending: { label: 'Pendiente', color: 'text-amber', bg: 'bg-amber-soft', icon: Clock },
    partial: { label: 'Parcial', color: 'text-amber', bg: 'bg-amber-soft', icon: AlertTriangle },
    paid: { label: 'Pagado', color: 'text-mint', bg: 'bg-emerald-50', icon: CheckCircle2 },
};

export default function PaymentsPanel({
    expedienteId,
    payments,
    paymentStatus,
    totalInvoiced,
    totalPaid,
    currency,
    onPaymentRegistered,
}: PaymentsPanelProps) {
    const [showForm, setShowForm] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [form, setForm] = useState({ amount: '', method: 'transferencia', reference: '' });

    const statusCfg = STATUS_CONFIG[paymentStatus as keyof typeof STATUS_CONFIG] || STATUS_CONFIG.pending;
    const StatusIcon = statusCfg.icon;
    const percent = totalInvoiced > 0 ? Math.min((totalPaid / totalInvoiced) * 100, 100) : 0;
    const remaining = Math.max(totalInvoiced - totalPaid, 0);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!form.amount || parseFloat(form.amount) <= 0) {
            toast.error('Monto debe ser mayor a 0');
            return;
        }
        setSubmitting(true);
        try {
            await api.post(`expedientes/${expedienteId}/commands/register-payment/`, {
                amount: form.amount,
                currency,
                method: form.method,
                reference: form.reference,
            });
            toast.success('Pago registrado');
            setForm({ amount: '', method: 'transferencia', reference: '' });
            setShowForm(false);
            onPaymentRegistered?.();
        } catch (err: unknown) {
            const e = err as { response?: { data?: { detail?: string } } };
            toast.error(e.response?.data?.detail || 'Error al registrar pago');
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="bg-surface rounded-2xl border border-border shadow-sm overflow-hidden">
            {/* Header */}
            <div className="px-6 py-4 border-b border-border bg-slate-50/50 flex items-center justify-between">
                <h4 className="text-sm font-semibold text-text-primary flex items-center gap-2">
                    <DollarSign className="w-4 h-4 text-mint" />
                    Pagos
                </h4>
                <div className="flex items-center gap-3">
                    <span className={cn(
                        "flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold rounded-full border",
                        statusCfg.bg, statusCfg.color
                    )}>
                        <StatusIcon className="w-3.5 h-3.5" />
                        {statusCfg.label}
                    </span>
                    {paymentStatus !== 'paid' && (
                        <button
                            onClick={() => setShowForm(!showForm)}
                            className="bg-navy hover:bg-navy-dark text-white px-3 py-1.5 rounded-lg text-xs font-medium transition-all shadow-sm active:scale-95"
                        >
                            + Registrar Pago
                        </button>
                    )}
                </div>
            </div>

            {/* Progress Bar */}
            <div className="px-6 py-5">
                <div className="flex justify-between text-xs text-text-tertiary mb-2">
                    <span>Pagado: <strong className="text-text-primary">{currency} {totalPaid.toLocaleString('es-CR', { minimumFractionDigits: 2 })}</strong></span>
                    <span>Total: <strong className="text-text-primary">{currency} {totalInvoiced.toLocaleString('es-CR', { minimumFractionDigits: 2 })}</strong></span>
                </div>
                <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden">
                    <div
                        className={cn(
                            "h-full rounded-full transition-all duration-700 ease-out",
                            percent >= 100 ? "bg-gradient-to-r from-mint to-emerald-400" :
                                percent >= 50 ? "bg-gradient-to-r from-navy to-navy-light" :
                                    "bg-gradient-to-r from-amber to-amber"
                        )}
                        style={{ width: `${percent}%` }}
                    />
                </div>
                <div className="flex justify-between mt-2 text-xs">
                    <span className="text-mint font-semibold">{percent.toFixed(1)}%</span>
                    {remaining > 0 && (
                        <span className="text-text-tertiary">
                            Pendiente: {currency} {remaining.toLocaleString('es-CR', { minimumFractionDigits: 2 })}
                        </span>
                    )}
                </div>
            </div>

            {/* Payment Form (collapsible) */}
            {showForm && (
                <div className="px-6 pb-5 border-t border-border pt-4">
                    <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                            <label className="block text-xs font-semibold text-text-secondary mb-1.5">Monto ({currency})</label>
                            <input
                                type="number"
                                step="0.01"
                                value={form.amount}
                                onChange={(e) => setForm({ ...form, amount: e.target.value })}
                                placeholder={remaining.toFixed(2)}
                                className="w-full px-3 py-2 border border-border rounded-lg text-sm focus:ring-2 focus:ring-mint focus:border-mint outline-none bg-bg"
                                required
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-semibold text-text-secondary mb-1.5">Método</label>
                            <select
                                value={form.method}
                                onChange={(e) => setForm({ ...form, method: e.target.value })}
                                className="w-full px-3 py-2 border border-border rounded-lg text-sm focus:ring-2 focus:ring-mint focus:border-mint outline-none bg-bg"
                            >
                                <option value="transferencia">Transferencia</option>
                                <option value="cheque">Cheque</option>
                                <option value="efectivo">Efectivo</option>
                                <option value="tarjeta">Tarjeta</option>
                                <option value="otro">Otro</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-xs font-semibold text-text-secondary mb-1.5">Referencia</label>
                            <input
                                type="text"
                                value={form.reference}
                                onChange={(e) => setForm({ ...form, reference: e.target.value })}
                                placeholder="Ej: TRF-2026-001"
                                className="w-full px-3 py-2 border border-border rounded-lg text-sm focus:ring-2 focus:ring-mint focus:border-mint outline-none bg-bg"
                            />
                        </div>
                        <div className="md:col-span-3 flex gap-3 justify-end">
                            <button
                                type="button"
                                onClick={() => setShowForm(false)}
                                className="px-4 py-2 text-sm text-text-secondary border border-border rounded-lg hover:bg-surface-hover transition-colors"
                            >
                                Cancelar
                            </button>
                            <button
                                type="submit"
                                disabled={submitting}
                                className="bg-navy hover:bg-navy-dark text-white px-5 py-2 rounded-lg text-sm font-medium transition-all shadow-sm disabled:opacity-50 active:scale-95"
                            >
                                {submitting ? 'Guardando...' : 'Registrar Pago'}
                            </button>
                        </div>
                    </form>
                </div>
            )}

            {/* Payment History */}
            {payments.length > 0 && (
                <div className="border-t border-border">
                    <table className="w-full text-sm">
                        <thead className="bg-slate-50 text-xs text-text-tertiary uppercase font-semibold">
                            <tr>
                                <th className="px-6 py-3 text-left">Fecha</th>
                                <th className="px-6 py-3 text-left">Método</th>
                                <th className="px-6 py-3 text-left">Referencia</th>
                                <th className="px-6 py-3 text-right">Monto</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border">
                            {payments.map((p) => (
                                <tr key={p.payment_line_id} className="hover:bg-slate-50/50 transition-colors">
                                    <td className="px-6 py-3 text-text-secondary">
                                        {new Date(p.created_at).toLocaleDateString('es-CR')}
                                    </td>
                                    <td className="px-6 py-3">
                                        <span className="inline-flex items-center gap-1.5 text-text-secondary">
                                            <CreditCard className="w-3.5 h-3.5" />
                                            {p.method}
                                        </span>
                                    </td>
                                    <td className="px-6 py-3 text-text-tertiary font-mono text-xs">{p.reference || '—'}</td>
                                    <td className="px-6 py-3 text-right font-semibold text-text-primary">
                                        {p.currency} {Number(p.amount).toLocaleString('es-CR', { minimumFractionDigits: 2 })}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {payments.length === 0 && !showForm && (
                <div className="px-6 pb-6 pt-2 text-center text-text-tertiary text-sm">
                    No hay pagos registrados
                </div>
            )}
        </div>
    );
}
