"use client";

import { useState } from "react";
import {
  Layers,
  FileText,
  ShoppingCart,
  Box,
  DollarSign,
  Settings,
  Ruler,
  Percent,
  Users,
  TrendingUp,
} from "lucide-react";

// Componentes de Tab existentes
import { OverviewTab }      from "@/components/brand-console/OverviewTab";
import { AgreementsTab }    from "@/components/brand-console/AgreementsTab";
import { OrdersTab }        from "@/components/brand-console/OrdersTab";
import { CatalogTab }       from "@/components/brand-console/CatalogTab";
import { PricingTab }       from "@/components/brand-console/PricingTab";
import { OperationsTab }    from "@/components/brand-console/OperationsTab";
import { SizeSystemTab }    from "@/components/brand-console/SizeSystemTab";
import { PaymentTermsTab }  from "@/components/brand-console/PaymentTermsTab";
import { AssignmentsTab }   from "@/components/brand-console/AssignmentsTab";

// S23-13 — Nuevos componentes comerciales
import { RebatesSection }        from "@/components/commercial/RebatesSection";
import { CommissionsSection }    from "@/components/commercial/CommissionsSection";
import { ArtifactPolicySection } from "@/components/commercial/ArtifactPolicySection";

// TODO: obtener del contexto de sesión real
const MOCK_USER_ROLE = "CEO";

export default function BrandConsolePage() {
  const [activeTab, setActiveTab] = useState("overview");
  const [commercialSub, setCommercialSub] = useState<"rebates" | "commissions" | "policy">("rebates");

  const TABS = [
    { id: "overview",    label: "Overview",       icon: Layers,     index: 1 },
    { id: "agreements",  label: "Agreements",     icon: FileText,   index: 2 },
    { id: "orders",      label: "Orders",         icon: ShoppingCart, index: 3 },
    { id: "catalog",     label: "Catalog",        icon: Box,        index: 4 },
    { id: "pricing",     label: "Pricing",        icon: DollarSign, index: 5 },
    { id: "operations",  label: "Operations",     icon: Settings,   index: 6 },
    { id: "tallas",      label: "Tallas",         icon: Ruler,      index: 7 },
    { id: "payment",     label: "Payment Terms",  icon: Percent,    index: 8 },
    { id: "assignments", label: "Assignments",    icon: Users,      index: 9 },
    // S23-13 — Tab Reglas Comerciales
    { id: "commercial",  label: "Reglas Comerciales", icon: TrendingUp, index: 10 },
  ];

  const COMMERCIAL_SUBS = [
    { id: "rebates",     label: "Rebates" },
    { id: "commissions", label: "Comisiones" },
    { id: "policy",      label: "ArtifactPolicy" },
  ] as const;

  return (
    <div className="flex flex-col h-full">
      <div className="page-header px-6 py-4 border-b border-[var(--border)]">
        <div>
          <h1 className="page-title text-xl font-bold text-navy">Brand Console</h1>
          <p className="page-subtitle text-xs text-text-tertiary">Gestión comercial y operativa de marca</p>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="flex overflow-x-auto border-b border-[var(--border)] bg-bg-alt/10 px-6 no-scrollbar">
        {TABS.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 text-[11px] font-semibold border-b-2 transition-all whitespace-nowrap uppercase tracking-wider ${
                isActive
                  ? "border-brand text-brand bg-brand/[0.03]"
                  : "border-transparent text-text-tertiary hover:text-text-secondary hover:bg-bg-alt/20"
              }`}
            >
              <Icon size={14} />
              <span>{tab.label}</span>
              <span className="opacity-30 text-[9px] font-mono ml-1">#{tab.index}</span>
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto p-6 bg-gray-50/30">
        <div className="max-w-7xl mx-auto">
          {activeTab === "overview"    && <OverviewTab />}
          {activeTab === "agreements"  && <AgreementsTab />}
          {activeTab === "orders"      && <OrdersTab />}
          {activeTab === "catalog"     && <CatalogTab />}
          {activeTab === "pricing"     && <PricingTab />}
          {activeTab === "operations"  && <OperationsTab />}
          {activeTab === "tallas"      && <SizeSystemTab />}
          {activeTab === "payment"     && <PaymentTermsTab />}
          {activeTab === "assignments" && <AssignmentsTab />}

          {/* S23-13 — Tab Reglas Comerciales con sub-navegación */}
          {activeTab === "commercial" && (
            <div className="space-y-5">
              {/* Sub-tabs */}
              <div className="flex gap-1 border-b border-[var(--border)] pb-0">
                {COMMERCIAL_SUBS.map((sub) => (
                  <button
                    key={sub.id}
                    onClick={() => setCommercialSub(sub.id)}
                    className={`px-4 py-2.5 text-[11px] font-bold border-b-2 transition-all uppercase tracking-wider ${
                      commercialSub === sub.id
                        ? "border-brand text-brand"
                        : "border-transparent text-text-tertiary hover:text-text-secondary"
                    }`}
                  >
                    {sub.label}
                  </button>
                ))}
              </div>

              {/* Sub-contenido */}
              {commercialSub === "rebates"     && <RebatesSection />}
              {commercialSub === "commissions" && <CommissionsSection userRole={MOCK_USER_ROLE} />}
              {commercialSub === "policy"      && <ArtifactPolicySection />}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
