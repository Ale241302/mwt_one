"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname, useParams } from "next/navigation";
import {
  LayoutDashboard, FolderOpen, Kanban, PieChart, Receipt,
  ArrowLeftRight, Network, Users2, Building2, Users,
  LogOut, ChevronLeft, ChevronRight,
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { cn } from "@/lib/utils";

interface NavItem { label: string; href: string; icon: React.ReactNode; group: string; }

const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard",     href: "",              icon: <LayoutDashboard size={20} />, group: "core" },
  { label: "Expedientes",   href: "/expedientes",  icon: <FolderOpen size={20} />,      group: "core" },
  { label: "Pipeline",      href: "/pipeline",     icon: <Kanban size={20} />,          group: "core" },
  { label: "Financiero",    href: "/financial",    icon: <PieChart size={20} />,         group: "financiero" },
  { label: "Liquidaciones", href: "/liquidaciones",icon: <Receipt size={20} />,          group: "financiero" },
  { label: "Transfers",     href: "/transfers",    icon: <ArrowLeftRight size={20} />,   group: "financiero" },
  { label: "Nodos",         href: "/nodos",        icon: <Network size={20} />,          group: "estructura" },
  { label: "Clientes",      href: "/clientes",     icon: <Users2 size={20} />,           group: "estructura" },
  { label: "Brands",        href: "/brands",       icon: <Building2 size={20} />,        group: "estructura" },
  { label: "Usuarios",      href: "/usuarios",     icon: <Users size={20} />,            group: "admin" },
];

const GROUP_LABELS: Record<string, string> = {
  core: "",
  financiero: "Financiero",
  estructura: "Estructura",
  admin: "Administración",
};
const GROUPS = ["core", "financiero", "estructura", "admin"];

export default function Sidebar({ isOpen, setIsOpen }: { isOpen: boolean; setIsOpen: (open: boolean) => void }) {
  const pathname = usePathname();
  const params = useParams();
  const { logout } = useAuth();
  const lang = (params?.lang as string) || "es";
  const basePath = `/${lang}/dashboard`;
  const [isMobile, setIsMobile] = useState(false);
  const [initialized, setInitialized] = useState(false);

  // S9.1-05: detect breakpoint separately, only set isOpen on first mount (no loop)
  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 640);
    check();
    if (!initialized) {
      setIsOpen(window.innerWidth >= 1024);
      setInitialized(true);
    }
    window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
  }, [initialized, setIsOpen]);

  const isActive = (item: NavItem) => {
    const fullHref = basePath + item.href;
    if (item.href === "") return pathname === basePath || pathname === basePath + "/";
    return pathname.startsWith(fullHref);
  };

  return (
    <aside
      className={cn("sidebar", !isOpen && "sidebar-collapsed", isMobile && isOpen && "sidebar-mobile-open")}
      aria-label="Navegación principal"
    >
      <div className="sidebar-brand">
        <Link href={basePath} className="flex items-center gap-3">
          <Image
            src="/logo.png"
            alt="MWT ONE"
            width={120}
            height={32}
            style={{ height: "32px", width: "auto" }}
            priority
          />
        </Link>
        <button
          onClick={() => setIsOpen(!isOpen)}
          style={{
            marginLeft: "auto", padding: 4,
            borderRadius: "var(--radius-md)",
            color: "var(--nav-text)",
            background: "none", border: "none", cursor: "pointer",
          }}
          aria-label={isOpen ? "Colapsar sidebar" : "Expandir sidebar"}
        >
          {isOpen ? <ChevronLeft size={18} /> : <ChevronRight size={18} />}
        </button>
      </div>
      <nav className="sidebar-nav">
        {GROUPS.map((group) => {
          const items = NAV_ITEMS.filter((i) => i.group === group);
          if (!items.length) return null;
          return (
            <div key={group} className={group !== "core" ? "mt-4" : ""}>
              {GROUP_LABELS[group] && isOpen && (
                <div className="sidebar-group-label">{GROUP_LABELS[group]}</div>
              )}
              {items.map((item) => {
                const active = isActive(item);
                return (
                  <Link
                    key={item.label}
                    href={basePath + item.href}
                    className={cn("sidebar-item", active && "sidebar-item-active")}
                    title={!isOpen ? item.label : undefined}
                    aria-current={active ? "page" : undefined}
                  >
                    <span className="flex-shrink-0">{item.icon}</span>
                    {isOpen && <span>{item.label}</span>}
                  </Link>
                );
              })}
            </div>
          );
        })}
      </nav>
      <div style={{ padding: "var(--space-2)", marginTop: "auto" }}>
        <button
          onClick={logout}
          className="sidebar-item"
          style={{ width: "100%", border: "none", background: "none", cursor: "pointer" }}
          aria-label="Cerrar sesión"
        >
          <LogOut size={20} />
          {isOpen && <span>Cerrar sesión</span>}
        </button>
      </div>
    </aside>
  );
}
