'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import {
  LayoutDashboard, Kanban, Package, DollarSign,
  Receipt, MapPin, ArrowLeftRight, Users, Tag, UserCog, Settings,
  ChevronLeft, ChevronRight,
} from 'lucide-react';

interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
  disabled?: boolean;
  badge?: string;
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard',     href: '/',              icon: LayoutDashboard },
  { label: 'Pipeline',      href: '/pipeline',      icon: Kanban },
  { label: 'Expedientes',   href: '/expedientes',   icon: Package },
  { label: 'Financiero',    href: '/dashboard/financial', icon: DollarSign },
  { label: 'Liquidaciones', href: '/liquidaciones', icon: Receipt },
  { label: 'Nodos',         href: '/nodos',         icon: MapPin },
  { label: 'Transfers',     href: '/transfers',     icon: ArrowLeftRight },
  { label: 'Clientes',      href: '/clientes',      icon: Users },
  { label: 'Brands',        href: '/brands',        icon: Tag },
  { label: 'Usuarios',      href: '/usuarios',      icon: UserCog },
  { label: 'Configuraci\u00f3n', href: '#',          icon: Settings, disabled: true, badge: 'Sprint 10' },
];

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={`flex flex-col h-full bg-[#013A57] text-white transition-sidebar ${
        collapsed ? 'w-16' : 'w-60'
      }`}
      aria-label="Navegaci\u00f3n principal"
    >
      {/* Logo area */}
      <div className="flex items-center justify-between px-4 py-4 border-b border-white/10">
        {!collapsed && (
          <span className="font-semibold text-sm tracking-wide text-white/90">MWT ONE</span>
        )}
        <button
          onClick={() => setCollapsed(prev => !prev)}
          className="ml-auto p-1 rounded hover:bg-white/10 transition-colors"
          aria-label={collapsed ? 'Expandir sidebar' : 'Colapsar sidebar'}
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      {/* Nav items */}
      <nav className="flex-1 overflow-y-auto py-2">
        {NAV_ITEMS.map(item => {
          const isActive = item.href !== '#' && (
            item.href === '/' ? pathname === '/' : pathname.startsWith(item.href)
          );
          const Icon = item.icon;

          const inner = (
            <span
              className={[
                'flex items-center gap-3 px-4 py-2.5 text-sm font-medium rounded-none',
                'border-l-[3px] transition-colors',
                item.disabled
                  ? 'opacity-40 cursor-not-allowed border-transparent'
                  : isActive
                  ? 'border-[#75CBB3] bg-white/8 text-white'
                  : 'border-transparent text-white/70 hover:bg-white/6 hover:text-white',
              ].join(' ')}
            >
              <Icon
                size={18}
                aria-hidden={!collapsed}
                aria-label={collapsed ? item.label : undefined}
              />
              {!collapsed && (
                <>
                  <span className="flex-1">{item.label}</span>
                  {item.badge && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/10 text-white/50 font-medium">
                      {item.badge}
                    </span>
                  )}
                </>
              )}
            </span>
          );

          if (item.disabled) {
            return (
              <div key={item.label} title={collapsed ? item.label : undefined}>
                {inner}
              </div>
            );
          }

          return (
            <Link
              key={item.label}
              href={item.href}
              aria-label={collapsed ? item.label : undefined}
              title={collapsed ? item.label : undefined}
              aria-current={isActive ? 'page' : undefined}
            >
              {inner}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
