"use client";

import { cn } from '@/lib/utils';
import {
    TrendingUp, TrendingDown, DollarSign, Receipt,
    CreditCard, BarChart3, Building2
} from 'lucide-react';

interface FinancialCard {
    label: string;
    value: number;
    currency: string;
    trend?: number;        // percentage change
    icon: 'cost' | 'invoice' | 'payment' | 'margin' | 'receivable';
}

interface BrandBreakdown {
    brand: string;
    count: number;
    total_cost: number;
    total_invoiced: number;
}

interface FinancialCardsProps {
    cards: {
        active_count: number;
        total_cost: number;
        total_invoiced: number;
        total_paid: number;
        total_receivables: number;
        margin: number;
        currency: string;
    };
    brandBreakdown: BrandBreakdown[];
}

const ICON_MAP = {
    cost: DollarSign,
    invoice: Receipt,
    payment: CreditCard,
    margin: BarChart3,
    receivable: TrendingUp,
};

function formatCurrency(value: number, currency: string = 'USD') {
    return `${currency} ${value.toLocaleString('es-CR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export default function FinancialCards({ cards, brandBreakdown }: FinancialCardsProps) {
    const metrics: (FinancialCard & { key: string })[] = [
        { key: 'cost', label: 'Costo Total', value: cards.total_cost, currency: cards.currency, icon: 'cost' },
        { key: 'invoiced', label: 'Facturado', value: cards.total_invoiced, currency: cards.currency, icon: 'invoice' },
        { key: 'paid', label: 'Cobrado', value: cards.total_paid, currency: cards.currency, icon: 'payment' },
        { key: 'receivable', label: 'Por Cobrar', value: cards.total_receivables, currency: cards.currency, icon: 'receivable' },
        { key: 'margin', label: 'Margen', value: cards.margin, currency: cards.currency, icon: 'margin', trend: cards.total_invoiced > 0 ? (cards.margin / cards.total_invoiced) * 100 : 0 },
    ];

    return (
        <div className="space-y-6">
            {/* KPI Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
                {metrics.map((m) => {
                    const Icon = ICON_MAP[m.icon];
                    const isPositive = m.value >= 0;
                    return (
                        <div
                            key={m.key}
                            className="bg-surface rounded-2xl border border-border shadow-sm p-5 hover:shadow-md transition-shadow group"
                        >
                            <div className="flex items-center justify-between mb-3">
                                <span className="text-xs font-semibold text-text-tertiary uppercase tracking-wider">{m.label}</span>
                                <div className={cn(
                                    "w-8 h-8 rounded-lg flex items-center justify-center transition-colors",
                                    m.key === 'margin' && isPositive ? "bg-emerald-50 text-mint" :
                                        m.key === 'margin' && !isPositive ? "bg-red-50 text-coral" :
                                            "bg-ice-soft text-navy"
                                )}>
                                    <Icon className="w-4 h-4" />
                                </div>
                            </div>
                            <div className="text-lg font-bold text-text-primary tracking-tight">
                                {formatCurrency(m.value, m.currency)}
                            </div>
                            {m.trend !== undefined && (
                                <div className={cn(
                                    "flex items-center gap-1 mt-2 text-xs font-semibold",
                                    m.trend >= 0 ? "text-mint" : "text-coral"
                                )}>
                                    {m.trend >= 0 ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                                    {Math.abs(m.trend).toFixed(1)}% margen
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>

            {/* Active Expedientes counter */}
            <div className="bg-gradient-to-r from-navy to-navy-light rounded-2xl p-6 text-white flex items-center justify-between">
                <div>
                    <p className="text-sm font-medium opacity-80">Expedientes Activos</p>
                    <p className="text-4xl font-bold mt-1">{cards.active_count}</p>
                </div>
                <div className="w-14 h-14 rounded-full bg-white/10 flex items-center justify-center">
                    <Building2 className="w-7 h-7 text-mint" />
                </div>
            </div>

            {/* Brand Breakdown */}
            {brandBreakdown.length > 0 && (
                <div className="bg-surface rounded-2xl border border-border shadow-sm overflow-hidden">
                    <div className="px-6 py-4 border-b border-border bg-slate-50/50">
                        <h4 className="text-sm font-semibold text-text-primary">Desglose por Marca</h4>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead className="bg-slate-50 text-xs text-text-tertiary uppercase font-semibold border-b border-border">
                                <tr>
                                    <th className="px-6 py-3 text-left">Marca</th>
                                    <th className="px-6 py-3 text-center">Expedientes</th>
                                    <th className="px-6 py-3 text-right">Costo</th>
                                    <th className="px-6 py-3 text-right">Facturado</th>
                                    <th className="px-6 py-3 text-right">Margen</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border">
                                {brandBreakdown.map((b) => {
                                    const margin = b.total_invoiced - b.total_cost;
                                    const marginPct = b.total_invoiced > 0 ? (margin / b.total_invoiced) * 100 : 0;
                                    return (
                                        <tr key={b.brand} className="hover:bg-slate-50/50 transition-colors">
                                            <td className="px-6 py-3 font-semibold text-text-primary">{b.brand}</td>
                                            <td className="px-6 py-3 text-center">
                                                <span className="bg-ice-soft text-navy px-2 py-0.5 rounded-full text-xs font-bold">
                                                    {b.count}
                                                </span>
                                            </td>
                                            <td className="px-6 py-3 text-right text-text-secondary">
                                                {formatCurrency(b.total_cost)}
                                            </td>
                                            <td className="px-6 py-3 text-right text-text-secondary">
                                                {formatCurrency(b.total_invoiced)}
                                            </td>
                                            <td className="px-6 py-3 text-right">
                                                <span className={cn(
                                                    "font-semibold",
                                                    margin >= 0 ? "text-mint" : "text-coral"
                                                )}>
                                                    {formatCurrency(margin)} ({marginPct.toFixed(1)}%)
                                                </span>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
}
