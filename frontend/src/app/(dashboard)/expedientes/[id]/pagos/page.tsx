"use client";

import { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import api from '@/lib/api';
import toast from 'react-hot-toast';
import { ArrowLeft, FileText, Download } from 'lucide-react';
import PaymentsPanel from '@/components/PaymentsPanel';

interface PaymentLine {
    payment_line_id: string;
    amount: number;
    currency: string;
    method: string;
    reference: string;
    created_at: string;
}

interface CostLine {
    cost_line_id: string;
    cost_type: string;
    amount: number;
    currency: string;
    phase: string;
    description: string;
    visibility: string;
    created_at: string;
}

interface InvoiceData {
    consecutive: string;
    total_client_view: number;
    currency: string;
    created_at: string;
    exists: boolean;
}

export default function PagosPage() {
    const params = useParams();
    const id = params.id as string;
    const router = useRouter();
    const { user, loading: authLoading } = useAuth();

    const [costs, setCosts] = useState<CostLine[]>([]);
    const [payments, setPayments] = useState<PaymentLine[]>([]);
    const [invoice, setInvoice] = useState<InvoiceData | null>(null);
    const [costsSummary, setCostsSummary] = useState<{ total_internal: number; total_client: number; count: number } | null>(null);
    const [loading, setLoading] = useState(true);

    const fetchData = useCallback(async () => {
        try {
            setLoading(true);
            const [costsRes, bundleRes, invoiceRes, summaryRes] = await Promise.all([
                api.get(`/api/expedientes/${id}/costs/?view=client`),
                api.get(`/api/ui/expedientes/${id}/`),
                api.get(`/api/expedientes/${id}/invoice/?view=client`).catch(() => ({ data: null })),
                api.get(`/api/expedientes/${id}/costs/summary/`).catch(() => ({ data: null })),
            ]);
            setCosts(costsRes.data.costs || []);
            setPayments(bundleRes.data.payments || []);
            setInvoice(invoiceRes.data);
            setCostsSummary(summaryRes.data);
        } catch {
            toast.error('Error al cargar datos financieros');
        } finally {
            setLoading(false);
        }
    }, [id]);

    useEffect(() => {
        if (!authLoading && user) fetchData();
    }, [user, authLoading, fetchData]);

    const handleDownloadMirror = async () => {
        try {
            const { data } = await api.get(`/api/expedientes/${id}/mirror-pdf/`);
            if (data.html) {
                const blob = new Blob([data.html], { type: 'text/html' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `mirror_${id}.html`;
                a.click();
                URL.revokeObjectURL(url);
            } else if (data.pdf_url) {
                window.open(data.pdf_url, '_blank');
            }
            toast.success('Mirror PDF generado');
        } catch {
            toast.error('Error generando mirror PDF');
        }
    };

    if (loading) {
        return (
            <div className="flex flex-col space-y-4 p-8">
                <div className="h-8 w-64 bg-slate-200 animate-pulse rounded" />
                <div className="h-48 bg-slate-200 animate-pulse rounded" />
            </div>
        );
    }

    const totalInvoiced = invoice?.total_client_view || 0;
    const totalPaid = payments.reduce((s, p) => s + Number(p.amount), 0);

    return (
        <div className="max-w-5xl mx-auto space-y-6">
            <button
                onClick={() => router.push(`/expedientes/${id}`)}
                className="text-sm text-text-secondary hover:text-navy flex items-center transition-colors"
            >
                <ArrowLeft className="w-4 h-4 mr-1" />
                Volver al expediente
            </button>

            <div className="flex items-center justify-between flex-wrap gap-4">
                <h1 className="text-2xl font-display font-medium text-text-primary tracking-tight">
                    💰 Pagos &amp; Facturación
                </h1>
                <button
                    onClick={handleDownloadMirror}
                    className="flex items-center gap-2 bg-white border border-border text-navy px-4 py-2 rounded-lg text-sm font-medium hover:bg-slate-50 transition-colors shadow-sm"
                >
                    <Download className="w-4 h-4" />
                    Mirror PDF
                </button>
            </div>

            {/* Invoice Card */}
            {invoice?.exists && (
                <div className="bg-gradient-to-r from-navy to-navy-light rounded-2xl p-6 text-white flex items-center justify-between">
                    <div>
                        <p className="text-sm font-medium opacity-80">Factura</p>
                        <p className="text-2xl font-bold mt-1">{invoice.consecutive}</p>
                        <p className="text-sm opacity-60 mt-1">
                            {invoice.currency} {totalInvoiced.toLocaleString('es-CR', { minimumFractionDigits: 2 })}
                        </p>
                    </div>
                    <div className="w-14 h-14 rounded-full bg-white/10 flex items-center justify-center">
                        <FileText className="w-7 h-7 text-mint" />
                    </div>
                </div>
            )}

            {/* Payments Panel */}
            <PaymentsPanel
                expedienteId={id}
                payments={payments}
                paymentStatus={totalPaid >= totalInvoiced && totalInvoiced > 0 ? 'paid' : totalPaid > 0 ? 'partial' : 'pending'}
                totalInvoiced={totalInvoiced}
                totalPaid={totalPaid}
                currency={invoice?.currency || 'USD'}
                onPaymentRegistered={fetchData}
            />

            {/* Costs Breakdown (Client View) */}
            <div className="bg-surface rounded-2xl border border-border shadow-sm overflow-hidden">
                <div className="px-6 py-4 border-b border-border bg-slate-50/50 flex items-center justify-between">
                    <h4 className="text-sm font-semibold text-text-primary">📊 Costos (Vista Cliente)</h4>
                    {costsSummary && (
                        <span className="text-xs text-text-tertiary">
                            Total: USD {costsSummary.total_client.toLocaleString('es-CR', { minimumFractionDigits: 2 })}
                        </span>
                    )}
                </div>
                {costs.length > 0 ? (
                    <table className="w-full text-sm">
                        <thead className="bg-slate-50 text-xs text-text-tertiary uppercase font-semibold border-b border-border">
                            <tr>
                                <th className="px-6 py-3 text-left">Tipo</th>
                                <th className="px-6 py-3 text-left">Fase</th>
                                <th className="px-6 py-3 text-left">Descripción</th>
                                <th className="px-6 py-3 text-right">Monto</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border">
                            {costs.map((c) => (
                                <tr key={c.cost_line_id} className="hover:bg-slate-50/50 transition-colors">
                                    <td className="px-6 py-3 font-medium text-text-secondary">{c.cost_type}</td>
                                    <td className="px-6 py-3 text-text-tertiary text-xs">{c.phase}</td>
                                    <td className="px-6 py-3 text-text-secondary">{c.description}</td>
                                    <td className="px-6 py-3 text-right font-semibold text-text-primary">
                                        {c.currency} {Number(c.amount).toLocaleString('es-CR', { minimumFractionDigits: 2 })}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                ) : (
                    <div className="p-8 text-center text-text-tertiary text-sm">
                        Sin costos registrados para cliente
                    </div>
                )}
            </div>
        </div>
    );
}
