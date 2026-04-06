"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { Layers, FileText, ShoppingCart, Box, DollarSign, Settings, CreditCard, Link2, ArrowLeft, BarChart2, Loader2 } from "lucide-react";
import Link from "next/link";
import api from "@/lib/api";
import { PricingTab } from "@/components/brand-console/PricingTab";
import { OperationsTab } from "@/components/brand-console/OperationsTab";
import { PaymentTermsTab } from "@/components/brand-console/PaymentTermsTab";
import { AssignmentsTab } from "@/components/brand-console/AssignmentsTab";
import { CatalogTab } from "@/components/brand-console/CatalogTab";
// S23-13 — Tab Reglas Comerciales
import { CommercialTab } from "@/components/commercial/CommercialTab";

export default function BrandDetailPage() {
  const params = useParams();
  const lang = (params?.lang as string) || "es";
  const slug = params?.slug as string;
  const [activeTab, setActiveTab] = useState("overview");
  const [brand, setBrand] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchBrand() {
      try {
        setLoading(true);
        const res = await api.get(`/brands/${slug}/`);
        setBrand(res.data);
      } catch (err) {
        console.error("Error fetching brand:", err);
        setError("No se pudo cargar la información de la marca.");
      } finally {
        setLoading(false);
      }
    }
    if (slug) fetchBrand();
  }, [slug]);

  const TABS = [
    { id: "overview",      label: "Resumen",             icon: Layers },
    { id: "agreements",    label: "Acuerdos y Políticas", icon: FileText },
    { id: "orders",        label: "Pedidos",              icon: ShoppingCart },
    { id: "catalog",       label: "Catálogo",             icon: Box },
    { id: "pricing",       label: "Precios",              icon: DollarSign },
    { id: "operations",    label: "Operaciones",          icon: Settings },
    // S22-16
    { id: "payment-terms", label: "Términos de Pago",     icon: CreditCard },
    // S22-17
    { id: "assignments",   label: "Assignments",          icon: Link2 },
    // S23-13 — Reglas Comerciales (rebates, comisiones, artifact policy)
    { id: "commercial",    label: "Reglas Comerciales",   icon: BarChart2 },
  ];

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-text-tertiary">
        <Loader2 className="animate-spin mb-2" size={32} />
        <p className="text-sm">Cargando consola de marca...</p>
      </div>
    );
  }

  if (error || !brand) {
    return (
      <div className="card p-10 text-center space-y-4">
        <div className="bg-red-50 text-red-600 p-4 rounded-lg inline-block mx-auto text-sm">
          {error || "Marca no encontrada"}
        </div>
        <div>
          <Link href={`/${lang}/brands`} className="btn btn-secondary btn-sm flex items-center gap-2 mx-auto w-fit">
            <ArrowLeft size={14} /> Volver a marcas
          </Link>
        </div>
      </div>
    );
  }

  const brandId = brand.id;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4 mb-2">
        <Link href={`/${lang}/brands`} className="btn btn-sm btn-ghost p-2">
          <ArrowLeft size={16} />
        </Link>
        <div>
          <h1 className="page-title leading-tight">Brand Console: <span className="text-brand font-mono capitalize">{brand.name}</span></h1>
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
        {/* S22-15 — CatalogTab */}
        {activeTab === "catalog"       && <CatalogTab brandId={brandId} />}
        {activeTab === "pricing"       && <PricingTab brandId={brandId} />}
        {activeTab === "operations"    && <OperationsTab />}
        {activeTab === "payment-terms" && <PaymentTermsTab brandId={brandId} />}
        {activeTab === "assignments"   && <AssignmentsTab brandId={brandId} />}
        {/* S23-13 — CommercialTab: Rebates + Comisiones (CEO only) + ArtifactPolicy */}
        {activeTab === "commercial"    && <CommercialTab slug={slug} />}
      </div>
    </div>
  );
}
