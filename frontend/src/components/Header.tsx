"use client";

import { useAuth } from "@/contexts/AuthContext";
import { UserCircle, Bell } from "lucide-react";

export default function Header() {
    const { user } = useAuth();

    return (
        <header className="h-header bg-surface border-b border-border flex items-center justify-between px-6 sticky top-0 z-40 transition-all-custom">
            <div className="flex-1">
                {/* Placeholder for future global search or breadcrumbs */}
            </div>

            <div className="flex items-center space-x-4">
                <button className="p-2 text-text-tertiary hover:text-text-primary rounded-full hover:bg-bg transition-colors relative">
                    <Bell size={20} />
                    {/* Unread dot placeholder */}
                    <span className="absolute top-1 right-1 w-2 h-2 bg-coral rounded-full border border-surface"></span>
                </button>

                <div className="h-8 w-px bg-divider mx-2"></div>

                <div className="flex items-center space-x-3">
                    <div className="text-right hidden sm:block">
                        <p className="text-sm font-semibold text-text-primary">{user?.username || 'Usuario'}</p>
                        <p className="text-xs text-text-tertiary">{user?.role || 'CEO'}</p>
                    </div>
                    <div className="w-9 h-9 rounded-full bg-ice-soft text-navy flex items-center justify-center border border-ice">
                        <UserCircle size={24} />
                    </div>
                </div>
            </div>
        </header>
    );
}
