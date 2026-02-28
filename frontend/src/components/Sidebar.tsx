"use client";

import { useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, FolderOpen, PieChart, Users, Settings, LogOut, ChevronLeft, ChevronRight } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { cn } from "@/lib/utils";

export default function Sidebar({
    isOpen,
    setIsOpen,
}: {
    isOpen: boolean;
    setIsOpen: (open: boolean) => void;
}) {
    const pathname = usePathname();
    const { logout } = useAuth();

    // Auto-collapse on small screens
    useEffect(() => {
        const handleResize = () => {
            if (window.innerWidth < 1024) {
                setIsOpen(false);
            } else {
                setIsOpen(true);
            }
        };

        handleResize(); // Initial check
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, [setIsOpen]);

    const navItems = [
        { label: "Dashboard", href: "/", icon: <LayoutDashboard size={20} /> },
        { label: "Expedientes", href: "/expedientes", icon: <FolderOpen size={20} /> },
    ];

    const placeholderItems = [
        { label: "Reportes", icon: <PieChart size={20} /> },
        { label: "Usuarios", icon: <Users size={20} /> },
        { label: "Configuración", icon: <Settings size={20} /> },
    ];

    return (
        <aside
            className={cn(
                "fixed inset-y-0 left-0 z-50 bg-navy text-text-inverse transition-all-custom flex flex-col border-r border-navy-dark",
                isOpen ? "w-60" : "w-16" // 240px or 64px
            )}
        >
            {/* Brand */}
            <div className="h-header flex items-center justify-between px-4 border-b border-[rgba(255,255,255,0.06)]">
                {isOpen && (
                    <Link href="/" className="font-display font-extrabold text-lg tracking-tight">
                        mwt<span className="text-mint">.one</span>
                    </Link>
                )}
                <button
                    onClick={() => setIsOpen(!isOpen)}
                    className={cn(
                        "p-1.5 rounded-full hover:bg-[rgba(255,255,255,0.1)] transition-colors",
                        !isOpen && "mx-auto"
                    )}
                >
                    {isOpen ? <ChevronLeft size={18} /> : <ChevronRight size={18} />}
                </button>
            </div>

            {/* Navigation */}
            <nav className="flex-1 overflow-y-auto py-4">
                <ul className="space-y-1">
                    {navItems.map((item) => {
                        // Check if active: exact match for /, or starts with for others
                        const isActive = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);

                        return (
                            <li key={item.label}>
                                <Link
                                    href={item.href}
                                    className={cn(
                                        "flex items-center px-4 py-2.5 mx-2 rounded-md transition-colors",
                                        isActive
                                            ? "bg-[rgba(117,203,179,0.08)] text-mint border-l-4 border-mint"
                                            : "text-[rgba(255,255,255,0.6)] hover:bg-[rgba(255,255,255,0.06)] hover:text-white border-l-4 border-transparent"
                                    )}
                                    title={!isOpen ? item.label : undefined}
                                >
                                    <span className={cn("flex-shrink-0", !isOpen && "mx-auto")}>{item.icon}</span>
                                    {isOpen && <span className="ml-3 font-medium text-sm">{item.label}</span>}
                                </Link>
                            </li>
                        );
                    })}

                    <li className="pt-4 pb-2 px-6">
                        {isOpen && <span className="text-xs font-semibold text-[rgba(255,255,255,0.3)] uppercase tracking-wider">Próximamente</span>}
                        {!isOpen && <hr className="border-[rgba(255,255,255,0.1)] mx-2" />}
                    </li>

                    {placeholderItems.map((item) => (
                        <li key={item.label}>
                            <div
                                className="flex items-center px-4 py-2.5 mx-2 rounded-md text-[rgba(255,255,255,0.3)] cursor-not-allowed"
                                title={!isOpen ? `${item.label} (Próximamente)` : undefined}
                            >
                                <span className={cn("flex-shrink-0", !isOpen && "mx-auto")}>{item.icon}</span>
                                {isOpen && <span className="ml-3 font-medium text-sm">{item.label}</span>}
                            </div>
                        </li>
                    ))}
                </ul>
            </nav>

            {/* Footer / Logout */}
            <div className="p-4 border-t border-[rgba(255,255,255,0.06)]">
                <button
                    onClick={logout}
                    className={cn(
                        "flex items-center w-full px-4 py-2 rounded-md text-[rgba(255,255,255,0.6)] hover:bg-coral-soft hover:text-coral transition-colors border-l-4 border-transparent",
                        !isOpen && "justify-center px-0"
                    )}
                    title={!isOpen ? "Cerrar sesión" : undefined}
                >
                    <LogOut size={20} className="flex-shrink-0" />
                    {isOpen && <span className="ml-3 font-medium text-sm text-left">Cerrar sesión</span>}
                </button>
            </div>
        </aside>
    );
}
