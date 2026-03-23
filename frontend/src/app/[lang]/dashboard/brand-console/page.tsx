"use client";

import { useState } from "react";
import { Layers, FileText, ShoppingCart, Box, DollarSign, Settings } from "lucide-react";
import { PricingTab } from "@/components/brand-console/PricingTab";
import { OperationsTab } from "@/components/brand-console/OperationsTab";

export default function BrandConsolePage() {
  const [activeTab, setActiveTab] = useState("overview");

  const TABS = [
    { id: "overview", label: "Overview", icon: Layers },
    { id: "agreements", label: "Agreements & Policies", icon: FileText },
    { id: "orders", label: "Orders", icon: ShoppingCart },
    { id: "catalog", label: "Catalog", icon: Box },
    { id: "pricing", label: "Pricing", icon: DollarSign },
    { id: "operations", label: "Operations", icon: Settings },
  ];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Brand Console</h1>
          <p className="page-subtitle">Manage your brand operations and client orders</p>
        </div>
      </div>

      <div className="flex border-b border-[var(--border)] mb-6">
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
        {activeTab === "overview" && <p>Brand metrics and recent alerts will appear here.</p>}
        {activeTab === "agreements" && <p>List of Brand-Client agreements and assortment policies.</p>}
        {activeTab === "orders" && <p>View incoming client orders and their statuses.</p>}
        {activeTab === "catalog" && <p>Product master catalog and base pricing configuration.</p>}
        {activeTab === "pricing" && <PricingTab />}
        {activeTab === "operations" && <OperationsTab />}
      </div>
    </div>
  );
}
