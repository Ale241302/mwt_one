// S22-16 — Tab 8: Payment Terms — CRUD EarlyPaymentPolicy + EarlyPaymentTier inline
"use client";

import React, { useState, useEffect } from 'react';
import { Plus, Trash2, Save, ChevronDown, ChevronUp, Percent } from 'lucide-react';
import { getEarlyPaymentPolicies, updateEarlyPaymentPolicy, EarlyPaymentPolicy, EarlyPaymentTier } from '@/api/pricing';

export function PaymentTermsTab({ brandId }: { brandId?: string | number }) {
  const [policies, setPolicies] = useState<EarlyPaymentPolicy[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [savingId, setSavingId] = useState<number | null>(null);

  const fetchPolicies = React.useCallback(async () => {
    if (!brandId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const data = await getEarlyPaymentPolicies(brandId);
      setPolicies(data);
    } catch (error) {
      console.error("Error fetching policies:", error);
    } finally {
      setLoading(false);
    }
  }, [brandId]);

  useEffect(() => {
    fetchPolicies();
  }, [fetchPolicies]);

  const handleTierChange = (policyId: number, tierId: number, field: keyof EarlyPaymentTier, value: string | number) => {
    setPolicies((prev) =>
      prev.map((p) =>
        p.id === policyId
          ? { ...p, tiers: p.tiers.map((t) => t.id === tierId ? { ...t, [field]: value } : t) }
          : p
      )
    );
  };

  const handleAddTier = (policyId: number) => {
    setPolicies((prev) =>
      prev.map((p) =>
        p.id === policyId
          ? { ...p, tiers: [...p.tiers, { id: Date.now(), payment_days: 0, discount_pct: '0.00' }] }
          : p
      )
    );
  };

  const handleRemoveTier = (policyId: number, tierId: number) => {
    setPolicies((prev) =>
      prev.map((p) =>
        p.id === policyId
          ? { ...p, tiers: p.tiers.filter((t) => t.id !== tierId) }
          : p
      )
    );
  };

  const handlePolicyChange = (policyId: number, field: keyof EarlyPaymentPolicy, value: any) => {
    setPolicies((prev) => prev.map((p) => p.id === policyId ? { ...p, [field]: value } : p));
  };

  const handleSave = async (policyId: number) => {
    setSavingId(policyId);
    try {
      const policy = policies.find(p => p.id === policyId);
      if (policy) {
        await updateEarlyPaymentPolicy(policyId, {
          base_payment_days: policy.base_payment_days,
          base_commission_pct: policy.base_commission_pct,
          is_active: policy.is_active
        });
        await fetchPolicies();
      }
    } catch (error) {
      console.error("Error saving policy:", error);
    } finally {
      setSavingId(null);
    }
  };

  if (!brandId) {
    return (
      <div className="card p-12 text-center text-text-tertiary">
        <p className="text-sm">No se ha seleccionado una marca.</p>
      </div>
    );
  }

  if (loading) {
    return <div className="p-10 text-center text-text-tertiary animate-pulse text-xs">Cargando términos de pago...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="heading-lg">Términos de Pago</h2>
          <p className="text-xs text-text-tertiary mt-0.5">Políticas de pronto pago por cliente. Los cambios se registran en ConfigChangeLog.</p>
        </div>
        <button className="btn btn-primary btn-sm flex items-center gap-2 opacity-50 cursor-not-allowed">
          <Plus size={14} /> Nueva política
        </button>
      </div>

      {policies.length === 0 && (
        <div className="card p-8 text-center text-text-tertiary">
          <Percent size={36} className="mx-auto mb-3 opacity-20" />
          <p className="text-sm">No hay políticas de pronto pago para esta marca.</p>
        </div>
      )}

      {policies.map((policy) => (
        <div key={policy.id} className="card overflow-hidden">
          <div className="flex items-center justify-between px-5 py-4">
            <div className="flex items-center gap-3">
              <div className={`w-2 h-2 rounded-full ${policy.is_active ? 'bg-emerald-500' : 'bg-text-tertiary'}`} />
              <div>
                <p className="text-sm font-semibold text-text-primary">{policy.client_subsidiary_name}</p>
                <p className="text-xs text-text-tertiary">
                  Base: {policy.base_payment_days}d · Comisión: {policy.base_commission_pct}% · {policy.tiers.length} tramos
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => handleSave(policy.id)}
                disabled={savingId === policy.id}
                className="btn btn-sm btn-secondary flex items-center gap-1.5 disabled:opacity-60"
              >
                <Save size={12} />
                {savingId === policy.id ? 'Guardando...' : 'Guardar'}
              </button>
              <button
                onClick={() => setExpandedId(expandedId === policy.id ? null : policy.id)}
                className="btn btn-ghost btn-sm p-2"
              >
                {expandedId === policy.id ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              </button>
            </div>
          </div>

          {expandedId === policy.id && (
            <div className="border-t border-border px-5 py-4 space-y-5">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-text-secondary mb-1">Días base de pago</label>
                  <input
                    type="number"
                    value={policy.base_payment_days}
                    onChange={(e) => handlePolicyChange(policy.id, 'base_payment_days', e.target.value)}
                    className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-text-secondary mb-1">Comisión base (%)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={policy.base_commission_pct}
                    onChange={(e) => handlePolicyChange(policy.id, 'base_commission_pct', e.target.value)}
                    className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30"
                  />
                </div>
              </div>

              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  id={`active-${policy.id}`}
                  checked={policy.is_active}
                  onChange={(e) => handlePolicyChange(policy.id, 'is_active', e.target.checked)}
                  className="w-4 h-4 accent-brand"
                />
                <label htmlFor={`active-${policy.id}`} className="text-sm text-text-primary">Política activa</label>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <p className="text-xs font-semibold text-text-secondary">Tramos de descuento</p>
                  <button onClick={() => handleAddTier(policy.id)} className="btn btn-ghost btn-sm text-brand flex items-center gap-1 text-xs">
                    <Plus size={12} /> Agregar tramo
                  </button>
                </div>
                <div className="space-y-2">
                  {policy.tiers.map((tier) => (
                    <div key={tier.id} className="flex items-center gap-3">
                      <div className="flex-1">
                        <label className="block text-[11px] text-text-tertiary mb-0.5">Si paga en ≤ X días</label>
                        <input
                          type="number"
                          value={tier.payment_days}
                          onChange={(e) => handleTierChange(policy.id, tier.id, 'payment_days', e.target.value)}
                          className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30"
                        />
                      </div>
                      <div className="flex-1">
                        <label className="block text-[11px] text-text-tertiary mb-0.5">Descuento (%)</label>
                        <input
                          type="number"
                          step="0.01"
                          value={tier.discount_pct}
                          onChange={(e) => handleTierChange(policy.id, tier.id, 'discount_pct', e.target.value)}
                          className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30"
                        />
                      </div>
                      <button onClick={() => handleRemoveTier(policy.id, tier.id)} className="mt-5 btn btn-ghost btn-sm p-2 text-red-500 hover:bg-red-50">
                        <Trash2 size={13} />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
