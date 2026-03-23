"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Lock, Edit3 } from "lucide-react";
import { CreditBar } from "@/components/ui/CreditBar";

export default function ClienteCreditoPage() {
  const router = useRouter();
  const params = useParams();
  const lang = (params?.lang as string) || "es";
  
  // Mock data for CEO view
  const clientName = "Tech Solutions Inc.";
  const [creditLimit, setCreditLimit] = useState(250000);
  const [creditUsed, setCreditUsed] = useState(210000);
  const [isFrozen, setIsFrozen] = useState(false);
  const [showAdjustModal, setShowAdjustModal] = useState(false);

  const getClientRiskLevel = (used: number, total: number) => {
    if (total === 0) return 'high';
    const ratio = used / total;
    if (ratio >= 0.9) return 'high';
    if (ratio >= 0.7) return 'medium';
    return 'low';
  };

  const riskLevel = getClientRiskLevel(creditUsed, creditLimit);
  const riskColor = riskLevel === 'high' ? 'var(--critical)' : riskLevel === 'medium' ? 'var(--warning)' : 'var(--success)';

  const handleFreezeToggle = () => {
    setIsFrozen(!isFrozen);
  };

  return (
    <div className="space-y-6">
      <div className="mb-2">
        <button type="button" className="btn btn-sm btn-ghost mb-4" onClick={() => router.back()}>
          <ArrowLeft size={16} /> Volver a cliente
        </button>
        <div className="page-header flex justify-between items-start flex-wrap gap-4">
          <div>
            <h1 className="page-title leading-tight">Perfil de Crédito y Riesgo <span className="text-brand">(CEO)</span></h1>
            <p className="page-subtitle">{clientName}</p>
          </div>
          <div className="flex gap-2">
            <button 
              className={`btn btn-sm ${isFrozen ? 'btn-secondary' : 'btn-danger-outline'}`}
              onClick={handleFreezeToggle}
            >
              <Lock size={14} /> {isFrozen ? "Descongelar crédito" : "Congelar crédito"}
            </button>
            <button 
              className="btn btn-sm btn-primary"
              onClick={() => setShowAdjustModal(true)}
            >
              <Edit3 size={14} /> Ajustar límite
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card p-6 shadow-sm">
          <h2 className="heading-sm mb-4 font-semibold text-navy">Utilización de Crédito</h2>
          <CreditBar used={creditUsed} total={creditLimit} currency="USD" />
          
          <div className="mt-8 p-4 rounded-xl flex justify-between items-center bg-bg-alt/40 border border-border/50">
            <span className="text-xs font-medium text-text-secondary">Nivel de Riesgo (calculado)</span>
            <span 
              className="px-3 py-1 rounded-full text-[10px] font-bold capitalize shadow-sm" 
              style={{ backgroundColor: `${riskColor}10`, color: riskColor, border: `1px solid ${riskColor}30` }}
            >
              {riskLevel}
            </span>
          </div>
        </div>

        <div className="card p-6 shadow-sm">
          <h2 className="heading-sm mb-4 font-semibold text-navy">Cartera Vencida (Aging)</h2>
          <div className="space-y-4">
            <div className="flex justify-between pb-3 border-b border-divider">
              <span className="text-xs text-text-tertiary">Al día (0-30 días)</span>
              <span className="font-mono text-xs font-semibold text-navy">$150,000</span>
            </div>
            <div className="flex justify-between pb-3 border-b border-divider">
              <span className="text-xs text-text-tertiary">31-60 días</span>
              <span className="font-mono text-xs font-semibold text-navy">$45,000</span>
            </div>
            <div className="flex justify-between pb-3 border-b border-divider">
              <span className="text-xs text-text-tertiary">61-90 días</span>
              <span className="font-mono text-xs font-semibold text-warning">$15,000</span>
            </div>
            <div className="flex justify-between">
              <span className="text-xs font-bold text-text-secondary">90+ días</span>
              <span className="font-mono text-xs font-bold text-critical">$0</span>
            </div>
          </div>
        </div>
      </div>

      {isFrozen && (
        <div className="flex items-start gap-4 p-5 rounded-2xl bg-critical/5 border border-critical/20 animate-in zoom-in-95 duration-300">
          <div className="p-2 rounded-lg bg-critical/10 text-critical">
            <Lock size={20} />
          </div>
          <div>
            <p className="font-bold text-critical">Línea de crédito congelada</p>
            <p className="text-sm text-critical/80 mt-1">Este cliente no puede procesar nuevos expedientes hasta que se levante el bloqueo comercial por parte de finanzas.</p>
          </div>
        </div>
      )}

      {showAdjustModal && (
        <div className="fixed inset-0 bg-navy/60 backdrop-blur-md flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-8 w-full max-w-md shadow-2xl border border-border animate-in fade-in zoom-in-95 duration-200">
            <h3 className="text-xl font-bold text-navy mb-2">Ajustar límite de crédito</h3>
            <p className="text-sm text-text-tertiary mb-6">Define el nuevo límite máximo de crédito para {clientName}. Esta acción quedará registrada en el historial.</p>
            
            <div className="space-y-4">
              <div>
                <label className="block text-[10px] font-bold uppercase text-text-tertiary mb-1.5 ml-1">Nuevo límite (USD)</label>
                <input 
                  type="number" 
                  className="input w-full text-lg font-mono font-bold py-3" 
                  value={creditLimit}
                  onChange={(e) => setCreditLimit(Number(e.target.value))}
                />
              </div>
            </div>
            
            <div className="flex gap-3 mt-8">
              <button className="flex-1 btn btn-md btn-secondary font-semibold" onClick={() => setShowAdjustModal(false)}>Cancelar</button>
              <button className="flex-1 btn btn-md btn-primary font-semibold" onClick={() => setShowAdjustModal(false)}>Guardar cambios</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
