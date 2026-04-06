"use client";

/**
 * S23-13 — CommercialTab
 *
 * Tab compuesto para BrandConsole.
 * Orquesta las 3 secciones: Rebates, Comisiones (CEO only), ArtifactPolicy.
 *
 * REGLA: CommissionsSection NUNCA se monta si role !== 'CEO'.
 * No se muestra ningún mensaje de error ni bloqueo visible para otros roles.
 */

import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { RebatesSection } from "./RebatesSection";
import { CommissionsSection } from "./CommissionsSection";
import { ArtifactPolicySection } from "./ArtifactPolicySection";
import { TrendingUp, DollarSign, FileJson } from "lucide-react";

interface Props {
  slug: string;
}

type SubTab = "rebates" | "commissions" | "policy";

export function CommercialTab({ slug }: Props) {
  const { user } = useAuth();
  const isCEO = user?.role === "CEO";

  const SUB_TABS: { id: SubTab; label: string; icon: React.ElementType; ceoOnly?: boolean }[] = [
    { id: "rebates",     label: "Rebates",         icon: TrendingUp },
    { id: "commissions", label: "Comisiones",       icon: DollarSign, ceoOnly: true },
    { id: "policy",      label: "Artifact Policy",  icon: FileJson },
  ];

  // Filtrar tabs según role — si no es CEO, commissions no aparece en absoluto
  const visibleTabs = SUB_TABS.filter(t => !t.ceoOnly || isCEO);
  const [activeSubTab, setActiveSubTab] = useState<SubTab>("rebates");

  return (
    <div className="space-y-5">
      {/* Sub-tab nav */}
      <div className="flex gap-1 border-b border-border">
        {visibleTabs.map(tab => {
          const Icon = tab.icon;
          const isActive = activeSubTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveSubTab(tab.id)}
              className={`flex items-center gap-1.5 px-4 py-2.5 text-xs font-semibold border-b-2 transition-all ${
                isActive
                  ? "border-brand text-brand bg-brand/5"
                  : "border-transparent text-text-tertiary hover:text-text-secondary"
              }`}
            >
              <Icon size={13} />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Content */}
      <div className="animate-in fade-in slide-in-from-bottom-2 duration-200">
        {activeSubTab === "rebates"     && <RebatesSection />}
        {/* CommissionsSection NUNCA se monta si no es CEO */}
        {activeSubTab === "commissions" && isCEO && <CommissionsSection />}
        {activeSubTab === "policy"      && <ArtifactPolicySection brandId={slug} />}
      </div>
    </div>
  );
}
