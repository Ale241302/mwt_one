"use client";

import { useState, useEffect, useCallback } from "react";
import { LayoutDashboard, Store, ShoppingBag, Activity, History, DollarSign, Settings, Search, ArrowRight, Gift } from "lucide-react";
import Link from "next/link";
import api from "@/lib/api";
import { useParams } from "next/navigation";
import { StateBadge } from "@/components/ui/StateBadge";
import { StateTimelinePortal } from "@/components/portal/StateTimelinePortal";
import { PortalCatalogTab } from "@/components/portal/PortalCatalogTab";
// S23-14 — Tab Incentivos (rebate progress, CLIENT_* only, sin datos sensibles)
import { IncentivosTab } from "@/components/commercial/IncentivosTab";

interface Expediente {
  expediente_id: string;
  brand_name: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export default function PortalPage() {
  const params = useParams();
  const lang = (params?.lang as string) || "es";
  const [activeTab, setActiveTab] = useState("dashboard");
  const [expedientes, setExpedientes] = useState<Expediente[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  const TABS = [
    { id: "dashboard",     label: "General",        icon: LayoutDashboard },
    { id: "catalog",       label: "Catálogo",        icon: Store },
    { id: "cart",          label: "Carrito",         icon: ShoppingBag },
    { id: "active-orders", label: "Pedidos Activos", icon: Activity },
    { id: "history",       label: "Historial",       icon: History },
    { id: "financials",    label: "Finanzas",        icon: DollarSign },
    // S23-14 — Tab de incentivos / rebate progress
    { id: "incentivos",    label: "Incentivos",      icon: Gift },
    { id: "settings",      label: "Perfil",          icon: Settings },
  ];

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const res = await api.get("/portal/expedientes/");
      setExpedientes(res.data?.results || []);
    } catch (err) {
      console.error("Error fetching portal data:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (activeTab === "active-orders") fetchData();
    else setLoading(false);
  }, [activeTab, fetchData]);

  const filtered = expedientes.filter(e => {
    if (search && !e.expediente_id.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title text-2xl font-bold text-navy">Mi Portal B2B</h1>
          <p className="page-subtitle">Gestiona tus pedidos, consulta precios y sigue tus expedientes en tiempo real.</p>
        </div>
      </div>

      <div className="flex border-b border-border overflow-x-auto hide-scrollbar bg-white sticky top-0 z-10">
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
        {activeTab === "dashboard" && (
          <div className="space-y-6">
            <div className="card p-6 bg-gradient-to-r from-brand to-brand-accent text-white border-none relative overflow-hidden">
              <div className="relative z-10">
                <h3 className="text-xl font-bold mb-2">¡Bienvenido de nuevo!</h3>
                <p className="opacity-90 max-w-md text-sm mb-6">Completa tu perfil y descubre todas las herramientas que tenemos para potenciar tu negocio.</p>
                <Link
                  href={`/${lang}/portal/onboarding`}
                  className="btn btn-md bg-white text-brand hover:bg-white/90 border-none px-6"
                >
                  Abrir Asistente de Configuración <ArrowRight size={16} className="ml-2" />
                </Link>
              </div>
              <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl translate-x-1/2 -translate-y-1/2" />
            </div>

            <StateTimelinePortal currentStatus="OPERACION" />

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="card p-5">
                <h3 className="heading-sm mb-2 text-text-tertiary uppercase text-[10px]">Crédito Disponible</h3>
                <p className="text-2xl font-bold text-navy">$45,000 <span className="text-xs font-normal text-text-tertiary">USD</span></p>
              </div>
              <div className="card p-5">
                <h3 className="heading-sm mb-2 text-text-tertiary uppercase text-[10px]">Expedientes en Tránsito</h3>
                <p className="text-2xl font-bold text-navy">12</p>
              </div>
            </div>
          </div>
        )}

        {/* S22-18 — PortalCatalogTab: precio post-descuento + MOQ. NUNCA expone source/base_price */}
        {activeTab === "catalog" && <PortalCatalogTab />}

        {activeTab === "active-orders" && (
          <div className="space-y-4">
            <div className="flex justify-between items-center mb-2">
              <div className="relative w-72">
                <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-tertiary" />
                <input
                  type="text"
                  placeholder="Buscar ID..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="input pl-9 text-xs"
                />
              </div>
            </div>

            {loading ? (
              <div className="empty-state py-12">Cargando expedientes...</div>
            ) : filtered.length === 0 ? (
              <div className="card p-12 text-center text-text-tertiary">
                <Activity size={40} className="mx-auto mb-3 opacity-20" />
                <p className="text-sm">No se encontraron expedientes activos.</p>
              </div>
            ) : (
              <div className="card shadow-sm overflow-hidden border-border/60">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="bg-bg-alt/30 border-b border-border">
                      <th className="px-4 py-3 font-semibold text-text-tertiary text-[10px] uppercase">ID Expediente</th>
                      <th className="px-4 py-3 font-semibold text-text-tertiary text-[10px] uppercase">Estado</th>
                      <th className="px-4 py-3 font-semibold text-text-tertiary text-[10px] uppercase">Actualizado</th>
                      <th className="px-4 py-3 font-semibold text-text-tertiary text-[10px] uppercase text-right">Acciones</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/50">
                    {filtered.map((e) => (
                      <tr key={e.expediente_id} className="hover:bg-brand/[0.02] transition-colors">
                        <td className="px-4 py-4 font-mono text-xs text-navy font-medium">
                          {e.expediente_id.substring(0, 8).toUpperCase()}
                        </td>
                        <td className="px-4 py-4">
                          <StateBadge state={e.status as any} />
                        </td>
                        <td className="px-4 py-4 text-xs text-text-tertiary">
                          {new Date(e.updated_at).toLocaleDateString()}
                        </td>
                        <td className="px-4 py-4 text-right">
                          <Link
                            href={`/${lang}/expedientes/${e.expediente_id}`}
                            className="btn btn-sm btn-ghost text-brand text-xs font-semibold"
                          >
                            Details <ArrowRight size={14} className="ml-1" />
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* S23-14 — IncentivosTab: progreso de rebate, sin datos sensibles */}
        {activeTab === "incentivos" && <IncentivosTab />}

        {["cart", "history", "financials", "settings"].includes(activeTab) && (
          <div className="card p-12 text-center text-text-tertiary">
            <Store size={40} className="mx-auto mb-3 opacity-20" />
            <p className="text-sm">Módulo en desarrollo para la siguiente fase.</p>
          </div>
        )}
      </div>
    </div>
  );
}
