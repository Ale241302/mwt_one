"use client";

import { useState } from "react";
import { LayoutDashboard, Store, ShoppingBag, Activity, History, DollarSign, Settings } from "lucide-react";

export default function ClientConsolePage() {
  const [activeTab, setActiveTab] = useState("dashboard");

  const TABS = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "catalog", label: "Catalog", icon: Store },
    { id: "cart", label: "Cart/Checkout", icon: ShoppingBag },
    { id: "active-orders", label: "Active Orders", icon: Activity },
    { id: "history", label: "Order History", icon: History },
    { id: "financials", label: "Financials", icon: DollarSign },
    { id: "settings", label: "Settings/Profile", icon: Settings },
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
        {activeTab === "dashboard" && <p>Summary of active activities and credit status.</p>}
        {activeTab === "catalog" && <p>Secure catalog viewing with negotiated pricing.</p>}
        {activeTab === "cart" && <p>Draft and submit new client orders.</p>}
        {activeTab === "active-orders" && <p>Track current order progress.</p>}
        {activeTab === "history" && <p>Past completed orders.</p>}
        {activeTab === "financials" && <p>Invoices, credit limits, and payments.</p>}
        {activeTab === "settings" && <p>Organization details and profile settings.</p>}
      </div>
    </div>
  );
}
