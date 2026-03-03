"use client";

import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import api from '@/lib/api';
import toast from 'react-hot-toast';
import { ShieldAlert } from 'lucide-react';
import FinancialCards from '@/components/FinancialCards';

interface DashboardData {
    cards: {
        active_count: number;
        total_cost: number;
        total_invoiced: number;
        total_paid: number;
        total_receivables: number;
        margin: number;
        currency: string;
    };
    brand_breakdown: {
        brand: string;
        count: number;
        total_cost: number;
        total_invoiced: number;
    }[];
}

export default function FinancialDashboardPage() {
    const { user, loading: authLoading } = useAuth();
    const [data, setData] = useState<DashboardData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (authLoading || !user) return;

        const fetchDashboard = async () => {
            try {
                setLoading(true);
                const { data } = await api.get('/api/ui/expedientes/dashboard/financial/');
                setData(data);
            } catch (err: unknown) {
                const e = err as { response?: { status?: number; data?: { detail?: string } } };
                if (e.response?.status === 403) {
                    setError('Acceso restringido');
                } else {
                    setError(e.response?.data?.detail || 'Error al cargar dashboard');
                    toast.error('Error al cargar dashboard financiero');
                }
            } finally {
                setLoading(false);
            }
        };

        fetchDashboard();
    }, [user, authLoading]);

    if (loading) {
        return (
            <div className="space-y-6">
                <div className="h-8 w-72 bg-slate-200 animate-pulse rounded" />
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
                    {[...Array(5)].map((_, i) => (
                        <div key={i} className="h-28 bg-slate-200 animate-pulse rounded-2xl" />
                    ))}
                </div>
                <div className="h-24 bg-slate-200 animate-pulse rounded-2xl" />
                <div className="h-48 bg-slate-200 animate-pulse rounded-2xl" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex flex-col items-center justify-center py-24 text-center">
                <ShieldAlert className="w-12 h-12 text-coral mb-4 opacity-60" />
                <h2 className="text-xl font-semibold text-text-primary mb-2">{error}</h2>
                <p className="text-sm text-text-tertiary">Intenta de nuevo más tarde o contacta soporte.</p>
            </div>
        );
    }

    if (!data) return null;

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-display font-medium text-text-primary tracking-tight">
                    📊 Dashboard Financiero
                </h1>
                <p className="text-sm text-text-tertiary mt-1">
                    Vista consolidada de costos, facturación y cobros
                </p>
            </div>

            <FinancialCards
                cards={data.cards}
                brandBreakdown={data.brand_breakdown}
            />
        </div>
    );
}
