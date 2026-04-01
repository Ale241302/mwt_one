"use client";

import { useAuth } from "@/contexts/AuthContext";
import { UserCircle, Bell, Settings, LogOut } from "lucide-react";
import { useActivityFeed } from "@/hooks/useActivityFeed";
import ActivityBadge from "./activity/ActivityBadge";
import ActivityPanel from "./activity/ActivityPanel";
import { useState } from "react";
import { cn } from "@/lib/utils";

export default function Header() {
    const { user, logout } = useAuth();
    const [isPanelOpen, setIsPanelOpen] = useState(false);
    const { events, unreadCount, loading, markAsSeen } = useActivityFeed();

    return (
        <header className="h-header bg-surface border-b border-border flex items-center justify-between px-6 sticky top-0 z-40 transition-all-custom">
            <div className="flex-1">
                {/* Placeholder for future global search or breadcrumbs */}
            </div>

            <div className="flex items-center space-x-4">
                <ActivityBadge 
                    count={unreadCount} 
                    onClick={() => setIsPanelOpen(true)} 
                />

                <ActivityPanel 
                    isOpen={isPanelOpen}
                    onClose={() => setIsPanelOpen(false)}
                    events={events}
                    loading={loading}
                    onMarkSeen={markAsSeen}
                />

                <div className="h-8 w-px bg-divider mx-2"></div>

                <div className="flex items-center space-x-3">
                    <div className="text-right hidden sm:block">
                        <p className="text-sm font-semibold text-text-primary">{user?.username || 'Usuario'}</p>
                        <p className="text-xs text-text-tertiary capitalize">{user?.role?.toLowerCase() || 'CEO'}</p>
                    </div>
                    <div className="group relative">
                        <div className="w-10 h-10 rounded-full bg-ice-soft text-navy flex items-center justify-center border border-ice shadow-sm cursor-pointer hover:bg-ice transition-colors">
                            <UserCircle size={26} />
                        </div>
                        
                        {/* Simple dropdown simulation if needed, but for now just the profile display */}
                    </div>
                </div>
            </div>
        </header>
    );
}
