"use client";

/**
 * S23-13 — CommissionsSection
 *
 * REGLA DE SEGURIDAD:
 * Este componente SOLO se renderiza si user.role === 'CEO'.
 * El componente padre (CommercialTab) es responsable de este guard.
 * Si el role no es CEO, el padre no monta este componente — nunca
 * se muestra un mensaje de error 403 ni ningún indicio de que
 * la sección existe para otros roles.
 */

import { useState, useEffect, useCallback } from "react";
import { Plus, RefreshCw, Trash2 } from "lucide-react";
import api from "@/lib/api";

interface Brand {
  id: string;
  name: string;
  slug: string;
}

interface CommissionRule {
  id: string;
  brand: string | null;
  client: string | null;
  subsidiary: string | null;
  product_key: string | null;
  rule_type: string;
  rule_value: string;
  commission_base: string | null;
  is_active: boolean;
  created_at: string;
}

const EMPTY_RULE = {
  scope: "brand" as "brand" | "client" | "subsidiary",
  scope_id: "",
  product_key: "",
  rule_type: "percentage",
  rule_value: "",
  commission_base: "",
  is_active: true,
};

export function CommissionsSection() {
  const [rules, setRules]       = useState<CommissionRule[]>([]);
  const [brands, setBrands]     = useState<Brand[]>([]);
  const [loading, setLoading]   = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm]         = useState({ ...EMPTY_RULE });
  const [saving, setSaving]     = useState(false);
  const [error, setError]       = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [rRes, bRes] = await Promise.all([
        api.get("/commercial/commission-rules/"),
        api.get("/brands/"),
      ]);
      setRules(rRes.data?.results ?? rRes.data ?? []);
      setBrands(bRes.data?.results ?? bRes.data ?? []);
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? "Error cargando datos.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  // Reset scope_id when scope changes to avoid sending stale UUID
  const handleScopeChange = (scope: "brand" | "client" | "subsidiary") => {
    setForm(f => ({ ...f, scope, scope_id: "" }));
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const payload: Record<string, any> = {
        rule_type:       form.rule_type,
        rule_value:      form.rule_value,
        commission_base: form.commission_base || null,
        is_active:       form.is_active,
        product_key:     form.product_key || null,
        brand:           form.scope === "brand"      ? form.scope_id : null,
        client:          form.scope === "client"     ? form.scope_id : null,
        subsidiary:      form.scope === "subsidiary" ? form.scope_id : null,
      };
      await api.post("/commercial/commission-rules/", payload);
      setShowForm(false);
      setForm({ ...EMPTY_RULE });
      fetchAll();
    } catch (e: any) {
      const data = e?.response?.data;
      setError(typeof data === "object" ? JSON.stringify(data) : "Error al crear regla.");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("¿Eliminar esta regla de comisión?")) return;
    try {
      await api.delete(`/commercial/commission-rules/${id}/`);
      fetchAll();
    } catch {
      alert("Error al eliminar.");
    }
  };

  const scopeLabel = (r: CommissionRule) => {
    if (r.brand) {
      const b = brands.find(b => b.id === r.brand);
      return `Brand: ${b ? b.name : r.brand.substring(0, 8) + "…"}`;
    }
    if (r.client)     return `Client: ${r.client.substring(0, 8)}…`;
    if (r.subsidiary) return `Subsidiary: ${r.subsidiary.substring(0, 8)}…`;
    return "—";
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-navy">Reglas de Comisión</h3>
          <p className="text-xs text-text-tertiary mt-0.5">Solo visible para CEO.</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={fetchAll} className="btn btn-sm btn-ghost p-2" title="Refrescar">
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          </button>
          <button onClick={() => setShowForm(v => !v)} className="btn btn-sm btn-primary flex items-center gap-1.5">
            <Plus size={14} />
            Nueva Regla
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 text-red-700 text-xs px-4 py-3">{error}</div>
      )}

      {/* Create Form */}
      {showForm && (
        <form onSubmit={handleCreate} className="card p-5 border-2 border-brand/20 space-y-4">
          <h4 className="text-xs font-bold text-brand uppercase tracking-wide">Nueva Regla de Comisión</h4>
          <div className="grid grid-cols-2 gap-4">
            {/* Scope selector */}
            <div className="space-y-1">
              <label className="text-[10px] font-semibold text-text-tertiary uppercase">Scope</label>
              <select className="input text-xs" value={form.scope}
                onChange={e => handleScopeChange(e.target.value as any)}>
                <option value="brand">Brand</option>
                <option value="client">Client</option>
                <option value="subsidiary">Subsidiary</option>
              </select>
            </div>

            {/* Scope ID — brand uses select, client/subsidiary use UUID input */}
            <div className="space-y-1">
              <label className="text-[10px] font-semibold text-text-tertiary uppercase">
                {form.scope === "brand" ? "Marca" : `${form.scope} UUID`} *
              </label>
              {form.scope === "brand" ? (
                <select required className="input text-xs" value={form.scope_id}
                  onChange={e => setForm(f => ({ ...f, scope_id: e.target.value }))}>
                  <option value="">— Seleccionar marca —</option>
                  {brands.map(b => (
                    <option key={b.id} value={b.id}>{b.name}</option>
                  ))}
                </select>
              ) : (
                <input required className="input text-xs font-mono" placeholder="uuid" value={form.scope_id}
                  onChange={e => setForm(f => ({ ...f, scope_id: e.target.value }))} />
              )}
            </div>

            <div className="space-y-1">
              <label className="text-[10px] font-semibold text-text-tertiary uppercase">Product Key</label>
              <input className="input text-xs" placeholder="vacío = default scope" value={form.product_key}
                onChange={e => setForm(f => ({ ...f, product_key: e.target.value }))} />
            </div>
            <div className="space-y-1">
              <label className="text-[10px] font-semibold text-text-tertiary uppercase">Tipo</label>
              <select className="input text-xs" value={form.rule_type}
                onChange={e => setForm(f => ({ ...f, rule_type: e.target.value }))}>
                <option value="percentage">Percentage</option>
                <option value="fixed_amount">Fixed Amount</option>
              </select>
            </div>
            <div className="space-y-1">
              <label className="text-[10px] font-semibold text-text-tertiary uppercase">Valor *</label>
              <input required type="number" step="0.0001" className="input text-xs" value={form.rule_value}
                onChange={e => setForm(f => ({ ...f, rule_value: e.target.value }))} />
            </div>
            <div className="space-y-1">
              <label className="text-[10px] font-semibold text-text-tertiary uppercase">Base Comisión</label>
              <select className="input text-xs" value={form.commission_base}
                onChange={e => setForm(f => ({ ...f, commission_base: e.target.value }))}>
                <option value="">— Pendiente DEC-S23-03 —</option>
                <option value="sale_price">Sale Price</option>
                <option value="gross_margin">Gross Margin</option>
              </select>
            </div>
          </div>
          <div className="flex items-center gap-3 pt-2">
            <button type="submit" disabled={saving} className="btn btn-sm btn-primary">
              {saving ? "Guardando..." : "Crear Regla"}
            </button>
            <button type="button" onClick={() => setShowForm(false)} className="btn btn-sm btn-ghost">Cancelar</button>
          </div>
        </form>
      )}

      {/* Table */}
      {loading ? (
        <div className="card p-8 text-center text-xs text-text-tertiary">Cargando reglas...</div>
      ) : rules.length === 0 ? (
        <div className="card p-8 text-center text-text-tertiary">
          <p className="text-sm">No hay reglas de comisión creadas.</p>
        </div>
      ) : (
        <div className="card shadow-sm overflow-hidden border-border/60">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-bg-alt/30 border-b border-border">
                {["Scope","Product Key","Tipo","Valor","Base","Estado",""].map(h => (
                  <th key={h} className="px-4 py-3 font-semibold text-text-tertiary text-[10px] uppercase">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-border/50">
              {rules.map(r => (
                <tr key={r.id} className="hover:bg-brand/[0.02] transition-colors">
                  <td className="px-4 py-3 text-text-secondary">{scopeLabel(r)}</td>
                  <td className="px-4 py-3 text-text-tertiary">{r.product_key ?? <span className="italic">default</span>}</td>
                  <td className="px-4 py-3 capitalize">{r.rule_type.replace("_", " ")}</td>
                  <td className="px-4 py-3 font-mono">
                    {r.rule_type === "percentage" ? `${r.rule_value}%` : `$${r.rule_value}`}
                  </td>
                  <td className="px-4 py-3 text-text-tertiary capitalize">
                    {r.commission_base?.replace("_", " ") ?? <span className="text-amber-500">Pendiente</span>}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                      r.is_active ? "bg-green-50 text-green-700" : "bg-gray-100 text-gray-500"
                    }`}>
                      {r.is_active ? "Activo" : "Inactivo"}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <button onClick={() => handleDelete(r.id)} className="btn btn-sm btn-ghost p-1.5 text-red-400 hover:text-red-600">
                      <Trash2 size={13} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
