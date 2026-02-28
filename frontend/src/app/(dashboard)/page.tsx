"use client";

import { useState, useEffect } from "react";
import api from "@/lib/api";
import { AlertCircle, Clock, FileText, DollarSign, ArrowRight, ShieldAlert } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

interface DashboardData {
    active_count: number;
    alert_count: number;
    blocked_count: number;
    total_cost: number;
    top_risk: Array<{
        id: number;
        custom_ref: string;
        brand_name: string;
        client_name: string;
        credit_days_elapsed: number;
        credit_band: string;
    }>;
    blocked_list: Array<{
        id: number;
        custom_ref: string;
        brand_name: string;
        is_blocked: boolean;
        block_reason: string;
    }>;
    alerts_list: Array<{
        id: number;
        custom_ref: string;
        credit_days_elapsed: number;
        credit_band: string;
    }>;
}

export default function DashboardPage() {
    const [data, setData] = useState<DashboardData | null>(null);
    const [loading, setLoading] = useState(true);

    const fetchDashboardData = async () => {
        try {
            const res = await api.get('/ui/dashboard/');
            setData(res.data);
        } catch (error) {
            console.error("Error fetching dashboard data", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchDashboardData();
        // Refresh every 60s
        const interval = setInterval(fetchDashboardData, 60000);
        return () => clearInterval(interval);
    }, []);

    if (loading && !data) {
        return (
            <div className="flex justify-center items-center h-64">
                <svg className="animate-spin h-8 w-8 text-mint" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
            </div>
        );
    }

    // Formatting currency
    const formatter = new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
    });

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center mb-8">
                <h1 className="text-2xl font-display font-bold">Dashboard</h1>
                <p className="text-sm text-text-tertiary">
                    Última actualización: {new Date().toLocaleTimeString()}
                </p>
            </div>

            {/* STAT CARDS */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Card 1: Activos */}
                <div className="p-6 bg-surface rounded-xl shadow-sm border border-border flex flex-col justify-between">
                    <div className="flex items-center space-x-3 mb-4">
                        <div className="p-2 bg-ice-soft text-navy rounded-lg">
                            <FileText size={20} />
                        </div>
                        <h3 className="font-medium text-text-secondary">Expedientes Activos</h3>
                    </div>
                    <p className="text-4xl font-display font-semibold text-text-primary">
                        {data?.active_count ?? 0}
                    </p>
                </div>

                {/* Card 2: Alertas */}
                <div className={cn(
                    "p-6 bg-surface rounded-xl shadow-sm border flex flex-col justify-between transition-colors",
                    (data?.alert_count && data.alert_count > 0) ? "border-coral bg-coral-soft/10" : "border-border"
                )}>
                    <div className="flex items-center space-x-3 mb-4">
                        <div className={cn(
                            "p-2 rounded-lg",
                            (data?.alert_count && data.alert_count > 0) ? "bg-coral-soft text-coral" : "bg-bg-alt text-text-secondary"
                        )}>
                            <Clock size={20} />
                        </div>
                        <h3 className="font-medium text-text-secondary">Alertas Crédito</h3>
                    </div>
                    <p className={cn(
                        "text-4xl font-display font-semibold",
                        (data?.alert_count && data.alert_count > 0) ? "text-coral" : "text-text-primary"
                    )}>
                        {data?.alert_count ?? 0}
                    </p>
                </div>

                {/* Card 3: Bloqueados */}
                <div className={cn(
                    "p-6 bg-surface rounded-xl shadow-sm border flex flex-col justify-between transition-colors",
                    (data?.blocked_count && data.blocked_count > 0) ? "border-coral bg-coral-soft/10" : "border-border"
                )}>
                    <div className="flex items-center space-x-3 mb-4">
                        <div className={cn(
                            "p-2 rounded-lg",
                            (data?.blocked_count && data.blocked_count > 0) ? "bg-coral-soft text-coral" : "bg-bg-alt text-text-secondary"
                        )}>
                            <ShieldAlert size={20} />
                        </div>
                        <h3 className="font-medium text-text-secondary">Bloqueados</h3>
                    </div>
                    <p className={cn(
                        "text-4xl font-display font-semibold",
                        (data?.blocked_count && data.blocked_count > 0) ? "text-coral" : "text-text-primary"
                    )}>
                        {data?.blocked_count ?? 0}
                    </p>
                </div>

                {/* Card 4: Costo Total */}
                <div className="p-6 bg-surface rounded-xl shadow-sm border border-border flex flex-col justify-between">
                    <div className="flex items-center space-x-3 mb-4">
                        <div className="p-2 bg-success-soft text-success rounded-lg">
                            <DollarSign size={20} />
                        </div>
                        <h3 className="font-medium text-text-secondary">Costo Total</h3>
                    </div>
                    <p className="text-3xl font-display font-semibold text-text-primary tabular-nums">
                        {formatter.format(data?.total_cost ?? 0)}
                    </p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
                {/* Top Riesgo Table */}
                <div className="bg-surface rounded-xl shadow-sm border border-border overflow-hidden flex flex-col">
                    <div className="p-5 border-b border-border bg-bg-alt/50">
                        <h2 className="font-semibold text-text-primary flex items-center">
                            <AlertCircle size={18} className="mr-2 text-amber" />
                            Top Riesgo (Días de Crédito)
                        </h2>
                    </div>
                    <div className="p-0 overflow-x-auto flex-1">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="bg-bg text-xs uppercase text-text-tertiary font-semibold tracking-wider">
                                    <th className="px-5 py-3 border-b border-divider">Ref</th>
                                    <th className="px-5 py-3 border-b border-divider">Cliente</th>
                                    <th className="px-5 py-3 border-b border-divider text-right">Días</th>
                                    <th className="px-5 py-3 border-b border-divider"></th>
                                </tr>
                            </thead>
                            <tbody>
                                {data?.top_risk?.length === 0 ? (
                                    <tr>
                                        <td colSpan={4} className="px-5 py-8 text-center text-text-tertiary">
                                            No hay expedientes en riesgo.
                                        </td>
                                    </tr>
                                ) : (
                                    data?.top_risk?.map((item) => (
                                        <tr key={item.id} className="hover:bg-surface-hover transition-colors group">
                                            <td className="px-5 py-3 border-b border-divider font-mono text-sm text-text-primary">
                                                {item.custom_ref}
                                            </td>
                                            <td className="px-5 py-3 border-b border-divider text-sm text-text-secondary max-w-[150px] truncate">
                                                {item.client_name}
                                            </td>
                                            <td className="px-5 py-3 border-b border-divider text-right">
                                                <span className={cn(
                                                    "inline-flex font-semibold px-2 py-0.5 rounded-md text-xs",
                                                    item.credit_band === "CORAL" ? "bg-coral-soft text-coral" :
                                                        item.credit_band === "AMBER" ? "bg-amber-soft text-amber" :
                                                            "bg-success-soft text-success"
                                                )}>
                                                    {item.credit_days_elapsed}d
                                                </span>
                                            </td>
                                            <td className="px-5 py-3 border-b border-divider text-right">
                                                <Link href={`/expedientes/${item.id}`} className="inline-flex items-center justify-center w-8 h-8 rounded-full text-text-tertiary hover:bg-bg hover:text-mint transition-colors">
                                                    <ArrowRight size={16} />
                                                </Link>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Expedientes Bloqueados */}
                <div className="bg-surface rounded-xl shadow-sm border border-border overflow-hidden flex flex-col">
                    <div className="p-5 border-b border-border bg-bg-alt/50">
                        <h2 className="font-semibold text-text-primary flex items-center">
                            <ShieldAlert size={18} className="mr-2 text-coral" />
                            Expedientes Bloqueados
                        </h2>
                    </div>
                    <div className="p-0 overflow-x-auto flex-1">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="bg-bg text-xs uppercase text-text-tertiary font-semibold tracking-wider">
                                    <th className="px-5 py-3 border-b border-divider">Ref</th>
                                    <th className="px-5 py-3 border-b border-divider">Razón</th>
                                    <th className="px-5 py-3 border-b border-divider"></th>
                                </tr>
                            </thead>
                            <tbody>
                                {data?.blocked_list?.length === 0 ? (
                                    <tr>
                                        <td colSpan={3} className="px-5 py-8 text-center text-text-tertiary">
                                            No hay expedientes bloqueados.
                                        </td>
                                    </tr>
                                ) : (
                                    data?.blocked_list?.map((item) => (
                                        <tr key={item.id} className="hover:bg-surface-hover transition-colors group">
                                            <td className="px-5 py-3 border-b border-divider font-mono text-sm text-coral">
                                                {item.custom_ref}
                                            </td>
                                            <td className="px-5 py-3 border-b border-divider text-sm text-text-secondary max-w-[200px] truncate" title={item.block_reason}>
                                                {item.block_reason || "Sin razón especificada"}
                                            </td>
                                            <td className="px-5 py-3 border-b border-divider text-right">
                                                <Link href={`/expedientes/${item.id}`} className="inline-flex items-center justify-center w-8 h-8 rounded-full text-text-tertiary hover:bg-bg hover:text-coral transition-colors">
                                                    <ArrowRight size={16} />
                                                </Link>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
}
