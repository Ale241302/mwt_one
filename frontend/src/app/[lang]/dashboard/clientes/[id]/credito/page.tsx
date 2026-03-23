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
    <div>
      <div className="mb-6">
        <button type="button" className="btn btn-sm btn-ghost mb-4" onClick={() => router.back()}>
          <ArrowLeft size={16} /> Volver a cliente
        </button>
        <div className="page-header flex justify-between items-start flex-wrap gap-4">
          <div>
            <h1 className="page-title">Perfil de Crédito y Riesgo (CEO)</h1>
            <p className="page-subtitle">{clientName}</p>
          </div>
          <div className="flex gap-2">
            <button 
              className={`btn btn-md ${isFrozen ? 'btn-secondary' : 'btn-danger-outline'}`}
              onClick={handleFreezeToggle}
            >
              <Lock size={16} /> {isFrozen ? "Descongelar crédito" : "Congelar crédito"}
            </button>
            <button 
              className="btn btn-md btn-primary"
              onClick={() => setShowAdjustModal(true)}
            >
              <Edit3 size={16} /> Ajustar límite
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="card p-6">
          <h2 className="heading-md mb-2">Utilización de Crédito</h2>
          <CreditBar used={creditUsed} total={creditLimit} currency="USD" />
          
          <div className="mt-6 p-4 rounded-lg flex justify-between items-center" style={{ background: "var(--bg-alt)" }}>
            <span className="font-medium" style={{ color: "var(--text-primary)" }}>Nivel de Riesgo (calculado)</span>
            <span 
              className="px-3 py-1 rounded-full text-sm font-bold capitalize" 
              style={{ backgroundColor: `${riskColor}20`, color: riskColor }}
            >
              {riskLevel}
            </span>
          </div>
        </div>

        <div className="card p-6">
          <h2 className="heading-md mb-4">Cartera Vencida (Aging)</h2>
          <div className="space-y-4">
            <div className="flex justify-between pb-2" style={{ borderBottom: '1px solid var(--divider)' }}>
              <span style={{ color: "var(--text-secondary)" }}>Al día (0-30 días)</span>
              <span className="font-mono" style={{ color: "var(--text-primary)" }}>$150,000</span>
            </div>
            <div className="flex justify-between pb-2" style={{ borderBottom: '1px solid var(--divider)' }}>
              <span style={{ color: "var(--text-secondary)" }}>31-60 días</span>
              <span className="font-mono" style={{ color: "var(--text-primary)" }}>$45,000</span>
            </div>
            <div className="flex justify-between pb-2" style={{ borderBottom: '1px solid var(--divider)' }}>
              <span style={{ color: "var(--text-secondary)" }}>61-90 días</span>
              <span className="font-mono" style={{ color: "var(--warning)" }}>$15,000</span>
            </div>
            <div className="flex justify-between pb-2">
              <span className="font-medium" style={{ color: "var(--text-secondary)" }}>90+ días</span>
              <span className="font-mono font-bold" style={{ color: "var(--critical)" }}>$0</span>
            </div>
          </div>
        </div>
      </div>

      {isFrozen && (
        <div className="p-4 rounded-xl mb-4 flex items-center gap-3" style={{ background: "var(--critical-bg)", border: "1px solid var(--critical)", color: "var(--critical)" }}>
          <Lock size={20} />
          <div>
            <p className="font-bold">Línea de crédito congelada</p>
            <p className="text-sm opacity-90">Este cliente no puede procesar nuevos expedientes hasta que se levante el bloqueo comercial.</p>
          </div>
        </div>
      )}

      {showAdjustModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md shadow-xl" style={{ border: '1px solid var(--border)' }}>
            <h3 className="heading-lg mb-4">Ajustar límite de crédito</h3>
            <p className="text-sm mb-4" style={{ color: "var(--text-secondary)" }}>Define el nuevo límite máximo de crédito para {clientName}.</p>
            
            <label className="block text-sm font-medium mb-1">Nuevo límite (USD)</label>
            <input 
              type="number" 
              className="input w-full mb-6" 
              value={creditLimit}
              onChange={(e) => setCreditLimit(Number(e.target.value))}
            />
            
            <div className="flex justify-end gap-2">
              <button className="btn btn-secondary" onClick={() => setShowAdjustModal(false)}>Cancelar</button>
              <button className="btn btn-primary" onClick={() => setShowAdjustModal(false)}>Guardar cambios</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
