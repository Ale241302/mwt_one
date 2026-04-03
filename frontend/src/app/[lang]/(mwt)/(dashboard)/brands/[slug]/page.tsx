"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { Layers, FileText, ShoppingCart, Box, DollarSign, Settings, CreditCard, Link2, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { PricingTab } from "@/components/brand-console/PricingTab";
import { OperationsTab } from "@/components/brand-console/OperationsTab";
import { PaymentTermsTab } from "@/components/brand-console/PaymentTermsTab";
import { AssignmentsTab } from "@/components/brand-console/AssignmentsTab";
import { CatalogTab } from "@/components/brand-console/CatalogTab";

export default function BrandDetailPage() {
  const params = useParams();
  const lang = (params?.lang as string) || "es";
  const slug = params?.slug as string;
  const [activeTab, setActiveTab] = useState("overview");

  const TABS = [
    { id: "overview",      label: "Resumen",            icon: Layers },
    { id: "agreements",    label: "Acuerdos y Políticas", icon: FileText },
    { id: "orders",        label: "Pedidos",             icon: ShoppingCart },
    { id: "catalog",       label: "Catálogo",            icon: Box },
    { id: "pricing",       label: "Precios",             icon: DollarSign },
    { id: "operations",    label: "Operaciones",         icon: Settings },
    // S22-16
    { id: "payment-terms", label: "Términos de Pago",    icon: CreditCard },
    // S22-17
    { id: "assignments",   label: "Assignments",         icon: Link2 },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4 mb-2">
        <Link href={`/${lang}/brands`} className="btn btn-sm btn-ghost p-2">
          <ArrowLeft size={16} />
        </Link>
        <div>
          <h1 className="page-title leading-tight">Brand Console: <span className="text-brand font-mono capitalize">{slug}</span></h1>
          <p className="page-subtitle text-xs">Gestiona operaciones comerciales y pedidos de clientes para esta marca.</p>
        </div>
      </div>

      <div className="flex border-b border-border overflow-x-auto hide-scrollbar bg-white/50 sticky top-0 z-10">
        {TABS.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-5 py-3.5 text-xs font-semibold border-b-2 transition-all whitespace-nowrap ${
                isActive
                  ? "border-brand text-brand bg-brand/5"
                  : "border-transparent text-text-tertiary hover:text-text-secondary"
              }`}
            >
              <Icon size={14} />
              {tab.label}
            </button>
          );
        })}
      </div>

      <div className="tab-content py-2 animate-in fade-in slide-in-from-bottom-2 duration-300">
        {activeTab === "overview" && (
           <div className="card p-8 text-center text-text-tertiary">
             <Layers size={40} className="mx-auto mb-3 opacity-20" />
             <p className="text-sm">Métricas de la marca y alertas recientes aparecerán aquí.</p>
           </div>
        )}
        {activeTab === "agreements" && (
           <div className="card p-8 text-center text-text-tertiary">
             <FileText size={40} className="mx-auto mb-3 opacity-20" />
             <p className="text-sm">Listado de acuerdos Brand-Client y políticas de surtido.</p>
           </div>
        )}
        {activeTab === "orders" && (
           <div className="card p-8 text-center text-text-tertiary">
             <ShoppingCart size={40} className="mx-auto mb-3 opacity-20" />
             <p className="text-sm">Consulta pedidos entrantes y su estado de procesamiento.</p>
           </div>
        )}
        {/* S22-15 — CatalogTab con precio base, MOQ y tallas */}
        {activeTab === "catalog"       && <CatalogTab />}
        {activeTab === "pricing"       && <PricingTab />}
        {activeTab === "operations"    && <OperationsTab />}
        {activeTab === "payment-terms" && <PaymentTermsTab />}
        {activeTab === "assignments"   && <AssignmentsTab />}
      </div>
    </div>
  );
}
