"use client";

import { useState } from "react";
import {
  LayoutDashboard,
  Store,
  ShoppingBag,
  Activity,
  History,
  DollarSign,
  Settings,
  TrendingUp,
} from "lucide-react";

// S23-14 — Componente de incentivos para el portal cliente
import { RebateProgressBar, type RebateProgressItem } from "@/components/commercial/RebateProgressBar";

// Mock data — reemplazar con fetch a /api/commercial/rebates/portal/progress/
// IMPORTANTE: este serializer NUNCA devuelve rebate_value, accrued_rebate ni umbrales absolutos
const MOCK_PROGRESS: RebateProgressItem[] = [
  {
    program_name: "Q1 Volume Rebate 2026",
    period: "Q1 2026",
    threshold_type: "amount",
    progress_percentage: 72,
    threshold_met: false,
  },
  {
    program_name: "Annual Fixed Rebate",
    period: "Año 2026",
    threshold_type: "units",
    progress_percentage: 100,
    threshold_met: true,
  },
  {
    program_name: "Bono especial sin umbral",
    period: "Semestre 1 · 2026",
    threshold_type: "none",
    progress_percentage: 100,
    threshold_met: true,
  },
];

export default function ClientConsolePage() {
  const [activeTab, setActiveTab] = useState("dashboard");

  const TABS = [
    { id: "dashboard",    label: "Dashboard",      icon: LayoutDashboard },
    { id: "catalog",      label: "Catalog",        icon: Store },
    { id: "cart",         label: "Cart/Checkout",  icon: ShoppingBag },
    { id: "active-orders",label: "Active Orders",  icon: Activity },
    { id: "history",      label: "Order History",  icon: History },
    { id: "financials",   label: "Financials",     icon: DollarSign },
    { id: "settings",     label: "Settings/Profile",icon: Settings },
    // S23-14 — Tab Incentivos (rebates portal)
    { id: "incentivos",   label: "Incentivos",     icon: TrendingUp },
  ];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Client Console</h1>
          <p className="page-subtitle">Draft orders, view pricing, and track your active expedientes</p>
        </div>
      </div>

      <div className="flex flex-wrap border-b border-[var(--border)] mb-6">
        {TABS.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                isActive
                  ? "border-[var(--mwt-primary)] text-[var(--mwt-primary)]"
                  : "border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-hover)]"
              }`}
            >
              <Icon size={16} />
              {tab.label}
            </button>
          );
        })}
      </div>

      <div className="tab-content py-4">
        {activeTab === "dashboard"     && <p>Summary of active activities and credit status.</p>}
        {activeTab === "catalog"       && <p>Secure catalog viewing with negotiated pricing.</p>}
        {activeTab === "cart"          && <p>Draft and submit new client orders.</p>}
        {activeTab === "active-orders" && <p>Track current order progress.</p>}
        {activeTab === "history"       && <p>Past completed orders.</p>}
        {activeTab === "financials"    && <p>Invoices, credit limits, and payments.</p>}
        {activeTab === "settings"      && <p>Organization details and profile settings.</p>}

        {/* S23-14 — Tab Incentivos */}
        {activeTab === "incentivos" && (
          <div className="space-y-5">
            <div>
              <h2 className="text-base font-bold text-[var(--text-primary)] mb-1">Tus Incentivos</h2>
              <p className="text-xs text-[var(--text-secondary)] mb-4">
                Progreso de tus programas de rebate activos. Los montos exactos se
                comunican al momento de la liquidación.
              </p>
            </div>
            <RebateProgressBar items={MOCK_PROGRESS} />
          </div>
        )}
      </div>
    </div>
  );
}
