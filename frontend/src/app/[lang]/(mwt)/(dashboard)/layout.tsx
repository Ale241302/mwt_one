"use client";

import { useAuth } from "@/contexts/AuthContext";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const { user, loading } = useAuth();
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const router = useRouter();

    // ✅ Redirect explícito cuando no hay sesión
    useEffect(() => {
        if (!loading && !user) {
            router.push('/login');
        }
    }, [loading, user, router]);

    if (loading) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center bg-bg">
                <svg className="animate-spin h-8 w-8 text-mint mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <p className="text-text-secondary">Verificando sesión...</p>
            </div>
        );
    }

    if (!user) {
        return null; // ← router.push('/login') ya fue llamado arriba
    }

    return (
        <div className="flex min-h-screen bg-bg">
            <Sidebar isOpen={sidebarOpen} setIsOpen={setSidebarOpen} />
            <div className={cn(
                "flex-1 flex flex-col min-w-0 transition-all-custom",
                sidebarOpen ? "ml-60" : "ml-16"
            )}>
                <Header />
                <main className="flex-1 p-6 md:p-8 overflow-x-hidden">
                    <div className="max-w-7xl mx-auto">
                        {children}
                    </div>
                </main>
            </div>
        </div>
    );
}
