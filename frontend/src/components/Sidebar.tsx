"use client";

import { useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  FolderOpen,
  PieChart,
  Kanban,
  Network,
  ArrowLeftRight,
  Users2,
  Building2,
  LogOut,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { cn } from "@/lib/utils";

// ── Nav item types ────────────────────────────────────────────────────────────
interface NavItem {
  label: string;
  href: string;
  icon: React.ReactNode;
  group?: string;
}

// ── All nav items ─────────────────────────────────────────────────────────────
// NOTE: /usuarios y /liquidaciones fueron eliminados (rutas no implementadas — 404).
const NAV_ITEMS: NavItem[] = [
  // Core
  { label: "Dashboard",   href: "/dashboard",  icon: <LayoutDashboard size={20} />, group: "core" },
  { label: "Expedientes", href: "/expedientes", icon: <FolderOpen size={20} />,      group: "core" },
  { label: "Pipeline",    href: "/pipeline",    icon: <Kanban size={20} />,           group: "core" },
  // Financiero
  { label: "Financiero",  href: "/dashboard/financial", icon: <PieChart size={20} />,       group: "financiero" },
  { label: "Transfers",   href: "/transfers",   icon: <ArrowLeftRight size={20} />,   group: "financiero" },
  // Estructura
  { label: "Nodos",    href: "/nodos",    icon: <Network size={20} />,   group: "estructura" },
  { label: "Clientes", href: "/clientes", icon: <Users2 size={20} />,    group: "estructura" },
  { label: "Brands",   href: "/brands",   icon: <Building2 size={20} />, group: "estructura" },
];

const GROUP_LABELS: Record<string, string> = {
  core:       "",
  financiero: "Financiero",
  estructura: "Estructura",
};

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
    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [setIsOpen]);

  const groups = ["core", "financiero", "estructura"];

  return (
    <aside
      aria-label="Navegación principal"
      className={cn(
        "fixed inset-y-0 left-0 z-50 bg-navy text-text-inverse transition-sidebar flex flex-col border-r border-navy-dark",
        isOpen ? "w-60" : "w-16"
      )}
    >
      {/* ── Brand ──────────────────────────────────────────────────────── */}
      <div className="h-header flex items-center justify-between px-4 border-b border-[rgba(255,255,255,0.06)]">
        {isOpen && (
          <Link href="/dashboard" className="flex items-center" aria-label="Ir al dashboard">
            <Image
              src="/recurso-1logo_foot.png"
              alt="MWT.ONE"
              width={140}
              height={35}
              priority
            />
          </Link>
        )}
        <button
          onClick={() => setIsOpen(!isOpen)}
          aria-label={isOpen ? "Colapsar menú" : "Expandir menú"}
          className={cn(
            "p-1.5 rounded-full hover:bg-[rgba(255,255,255,0.1)] transition-colors",
            !isOpen && "mx-auto"
          )}
        >
          {isOpen ? <ChevronLeft size={18} /> : <ChevronRight size={18} />}
        </button>
      </div>

      {/* ── Navigation ─────────────────────────────────────────────────── */}
      <nav aria-label="Menú lateral" className="flex-1 overflow-y-auto py-4">
        {groups.map((group) => {
          const items = NAV_ITEMS.filter((i) => i.group === group);
          const label = GROUP_LABELS[group];
          return (
            <div key={group}>
              {label && (
                <div className="px-6 pt-4 pb-1">
                  {isOpen ? (
                    <span className="text-[10px] font-semibold text-[rgba(255,255,255,0.28)] uppercase tracking-[0.08em]">
                      {label}
                    </span>
                  ) : (
                    <hr className="border-[rgba(255,255,255,0.1)]" />
                  )}
                </div>
              )}

              <ul className="space-y-0.5">
                {items.map((item) => {
                  const isActive =
                    item.href === "/dashboard"
                      ? pathname === "/dashboard" || pathname === "/"
                      : pathname.startsWith(item.href);

                  return (
                    <li key={item.label}>
                      <Link
                        href={item.href}
                        aria-label={item.label}
                        aria-current={isActive ? "page" : undefined}
                        title={!isOpen ? item.label : undefined}
                        className={cn(
                          "flex items-center px-4 py-2.5 mx-2 rounded-md transition-colors",
                          isActive
                            ? "bg-[rgba(117,203,179,0.08)] text-mint border-l-[3px] border-mint"
                            : "text-[rgba(255,255,255,0.6)] hover:bg-[rgba(255,255,255,0.06)] hover:text-white border-l-[3px] border-transparent"
                        )}
                      >
                        <span className={cn("flex-shrink-0", !isOpen && "mx-auto")}>
                          {item.icon}
                        </span>
                        {isOpen && (
                          <span className="ml-3 font-medium text-sm truncate">
                            {item.label}
                          </span>
                        )}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          );
        })}
      </nav>

      {/* ── Footer / Logout ─────────────────────────────────────────────── */}
      <div className="p-4 border-t border-[rgba(255,255,255,0.06)]">
        <button
          onClick={logout}
          aria-label="Cerrar sesión"
          title={!isOpen ? "Cerrar sesión" : undefined}
          className={cn(
            "flex items-center w-full px-4 py-2 rounded-md text-[rgba(255,255,255,0.6)] hover:bg-coral-soft hover:text-coral transition-colors border-l-[3px] border-transparent",
            !isOpen && "justify-center px-0"
          )}
        >
          <LogOut size={20} className="flex-shrink-0" />
          {isOpen && (
            <span className="ml-3 font-medium text-sm text-left">Cerrar sesión</span>
          )}
        </button>
      </div>
    </aside>
  );
}
