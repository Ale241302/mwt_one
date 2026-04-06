"use client";

import { useState, useEffect, useCallback } from "react";
import { Plus, RefreshCw, ChevronDown, ChevronUp, CheckCircle, XCircle, Clock, AlertCircle, Trash2 } from "lucide-react";
import api from "@/lib/api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
interface Brand {
  id: string;
  name: string;
  slug: string;
}

interface RebateProgram {
  id: string;
  name: string;
  brand: string;
  period_type: string;
  valid_from: string;
  valid_to: string | null;
  rebate_type: string;
  rebate_value: string;
  calculation_base: string | null;
  threshold_type: string;
  threshold_value: string | null;
  is_active: boolean;
}

interface RebateLedger {
  id: string;
  rebate_assignment: string;
  period_start: string;
  period_end: string;
  status: string;
  accrued_amount: string;
  qualifying_amount: string;
  qualifying_units: number;
  threshold_met: boolean;
  liquidation_type: string | null;
  liquidated_at: string | null;
  entries_count: number;
}

const EMPTY_PROGRAM = {
  name: "",
  brand: "",
  period_type: "quarterly",
  valid_from: "",
  valid_to: "",
  rebate_type: "percentage",
  rebate_value: "",
  calculation_base: "",
  threshold_type: "amount",
  threshold_value: "",
  is_active: true,
};

const STATUS_CONFIG: Record<string, { label: string; icon: React.ElementType; cls: string }> = {
  accruing:       { label: "Accruing",       icon: Clock,         cls: "text-blue-600 bg-blue-50" },
  pending_review: { label: "Pend. Review",   icon: AlertCircle,   cls: "text-amber-600 bg-amber-50" },
  liquidated:     { label: "Liquidated",     icon: CheckCircle,   cls: "text-green-600 bg-green-50" },
  cancelled:      { label: "Cancelled",      icon: XCircle,       cls: "text-red-600 bg-red-50" },
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------
export function RebatesSection() {
  const [programs, setPrograms]       = useState<RebateProgram[]>([]);
  const [ledgers, setLedgers]         = useState<RebateLedger[]>([]);
  const [brands, setBrands]           = useState<Brand[]>([]);
  const [loading, setLoading]         = useState(true);
  const [filter, setFilter]           = useState("");
  const [showForm, setShowForm]       = useState(false);
  const [form, setForm]               = useState({ ...EMPTY_PROGRAM });
  const [saving, setSaving]           = useState(false);
  const [error, setError]             = useState<string | null>(null);
  const [expandedLedger, setExpandedLedger] = useState<string | null>(null);
  const [approvingId, setApprovingId] = useState<string | null>(null);
  const [approveType, setApproveType] = useState("credit_note");

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [pRes, lRes, bRes] = await Promise.all([
        api.get("/commercial/rebate-programs/"),
        api.get("/commercial/rebate-ledgers/"),
        api.get("/brands/"),
      ]);
      setPrograms(pRes.data?.results ?? pRes.data ?? []);
      setLedgers(lRes.data?.results ?? lRes.data ?? []);
      setBrands(bRes.data?.results ?? bRes.data ?? []);
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? "Error cargando datos.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const filtered = programs.filter(p =>
    !filter ||
    p.name.toLowerCase().includes(filter.toLowerCase()) ||
    p.period_type.includes(filter.toLowerCase())
  );

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const payload: Record<string, any> = {
        name:             form.name,
        brand:            form.brand,
        period_type:      form.period_type,
        valid_from:       form.valid_from,
        valid_to:         form.valid_to || null,
        rebate_type:      form.rebate_type,
        rebate_value:     form.rebate_value,
        calculation_base: form.calculation_base || null,
        threshold_type:   form.threshold_type,
        threshold_value:  form.threshold_type !== "none" ? (form.threshold_value || null) : null,
        is_active:        form.is_active,
      };
      await api.post("/commercial/rebate-programs/", payload);
      setShowForm(false);
      setForm({ ...EMPTY_PROGRAM });
      fetchAll();
    } catch (e: any) {
      const data = e?.response?.data;
      setError(typeof data === "object" ? JSON.stringify(data) : "Error al crear programa.");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("¿Eliminar este programa de rebate?")) return;
    try {
      await api.delete(`/commercial/rebate-programs/${id}/`);
      fetchAll();
    } catch {
      alert("Error al eliminar.");
    }
  };

  const handleApprove = async (ledgerId: string) => {
    setApprovingId(ledgerId);
    setError(null);
    try {
      await api.post(`/commercial/rebate-ledgers/${ledgerId}/approve/`, {
        liquidation_type: approveType,
      });
      fetchAll();
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? "Error al aprobar liquidación.");
    } finally {
      setApprovingId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-navy">Programas de Rebate</h3>
          <p className="text-xs text-text-tertiary mt-0.5">Gestión de incentivos por volumen para marcas.</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={fetchAll} className="btn btn-sm btn-ghost p-2" title="Refrescar">
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          </button>
          <button onClick={() => setShowForm(v => !v)} className="btn btn-sm btn-primary flex items-center gap-1.5">
            <Plus size={14} />
            Nuevo Programa
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 text-red-700 text-xs px-4 py-3">
          {error}
        </div>
      )}

      {/* Create Form */}
      {showForm && (
        <form onSubmit={handleCreate} className="card p-5 border-2 border-brand/20 space-y-4">
          <h4 className="text-xs font-bold text-brand uppercase tracking-wide">Nuevo Programa de Rebate</h4>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-[10px] font-semibold text-text-tertiary uppercase">Nombre *</label>
              <input required className="input text-xs" value={form.name}
                onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
            </div>
            <div className="space-y-1">
              <label className="text-[10px] font-semibold text-text-tertiary uppercase">Marca *</label>
              <select required className="input text-xs" value={form.brand}
                onChange={e => setForm(f => ({ ...f, brand: e.target.value }))}>
                <option value="">— Seleccionar marca —</option>
                {brands.map(b => (
                  <option key={b.id} value={b.id}>{b.name}</option>
                ))}
              </select>
            </div>
            <div className="space-y-1">
              <label className="text-[10px] font-semibold text-text-tertiary uppercase">Período</label>
              <select className="input text-xs" value={form.period_type}
                onChange={e => setForm(f => ({ ...f, period_type: e.target.value }))}>
                <option value="quarterly">Quarterly</option>
                <option value="annual">Annual</option>
              </select>
            </div>
            <div className="space-y-1">
              <label className="text-[10px] font-semibold text-text-tertiary uppercase">Tipo Rebate</label>
              <select className="input text-xs" value={form.rebate_type}
                onChange={e => setForm(f => ({ ...f, rebate_type: e.target.value }))}>
                <option value="percentage">Percentage</option>
                <option value="fixed_amount">Fixed Amount</option>
              </select>
            </div>
            <div className="space-y-1">
              <label className="text-[10px] font-semibold text-text-tertiary uppercase">Valor Rebate *</label>
              <input required type="number" step="0.0001" className="input text-xs" value={form.rebate_value}
                onChange={e => setForm(f => ({ ...f, rebate_value: e.target.value }))} />
            </div>
            <div className="space-y-1">
              <label className="text-[10px] font-semibold text-text-tertiary uppercase">Base Cálculo</label>
              <select className="input text-xs" value={form.calculation_base}
                onChange={e => setForm(f => ({ ...f, calculation_base: e.target.value }))}>
                <option value="">— Pendiente DEC-S23-01 —</option>
                <option value="invoiced">Invoiced Price</option>
                <option value="list_price">List Price</option>
              </select>
            </div>
            <div className="space-y-1">
              <label className="text-[10px] font-semibold text-text-tertiary uppercase">Vigencia Desde *</label>
              <input required type="date" className="input text-xs" value={form.valid_from}
                onChange={e => setForm(f => ({ ...f, valid_from: e.target.value }))} />
            </div>
            <div className="space-y-1">
              <label className="text-[10px] font-semibold text-text-tertiary uppercase">Vigencia Hasta</label>
              <input type="date" className="input text-xs" value={form.valid_to}
                onChange={e => setForm(f => ({ ...f, valid_to: e.target.value }))} />
            </div>
            <div className="space-y-1">
              <label className="text-[10px] font-semibold text-text-tertiary uppercase">Tipo Threshold</label>
              <select className="input text-xs" value={form.threshold_type}
                onChange={e => setForm(f => ({ ...f, threshold_type: e.target.value }))}>
                <option value="amount">Amount</option>
                <option value="units">Units</option>
                <option value="none">None</option>
              </select>
            </div>
            {form.threshold_type !== "none" && (
              <div className="space-y-1">
                <label className="text-[10px] font-semibold text-text-tertiary uppercase">
                  Threshold {form.threshold_type === "units" ? "Unidades" : "Monto"}
                </label>
                <input
                  type="number"
                  step={form.threshold_type === "units" ? "1" : "0.01"}
                  className="input text-xs"
                  value={form.threshold_value}
                  onChange={e => setForm(f => ({ ...f, threshold_value: e.target.value }))}
                />
              </div>
            )}
          </div>
          <div className="flex items-center gap-3 pt-2">
            <button type="submit" disabled={saving} className="btn btn-sm btn-primary">
              {saving ? "Guardando..." : "Crear Programa"}
            </button>
            <button type="button" onClick={() => setShowForm(false)} className="btn btn-sm btn-ghost">Cancelar</button>
          </div>
        </form>
      )}

      {/* Filter */}
      <div className="flex items-center gap-3">
        <input
          className="input text-xs w-64"
          placeholder="Filtrar por nombre o período..."
          value={filter}
          onChange={e => setFilter(e.target.value)}
        />
        <span className="text-xs text-text-tertiary">{filtered.length} programa{filtered.length !== 1 ? "s" : ""}</span>
      </div>

      {/* Programs Table */}
      {loading ? (
        <div className="card p-8 text-center text-xs text-text-tertiary">Cargando programas...</div>
      ) : filtered.length === 0 ? (
        <div className="card p-8 text-center text-text-tertiary">
          <p className="text-sm">No hay programas de rebate{filter ? " que coincidan" : " creados"}.</p>
        </div>
      ) : (
        <div className="card shadow-sm overflow-hidden border-border/60">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-bg-alt/30 border-b border-border">
                {["Nombre","Período","Tipo","Valor","Threshold","Vigencia","Estado",""].map(h => (
                  <th key={h} className="px-4 py-3 font-semibold text-text-tertiary text-[10px] uppercase">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-border/50">
              {filtered.map(p => (
                <tr key={p.id} className="hover:bg-brand/[0.02] transition-colors">
                  <td className="px-4 py-3 font-medium text-navy">{p.name}</td>
                  <td className="px-4 py-3 text-text-secondary capitalize">{p.period_type.replace("_", " ")}</td>
                  <td className="px-4 py-3 text-text-secondary capitalize">{p.rebate_type.replace("_", " ")}</td>
                  <td className="px-4 py-3 font-mono">
                    {p.rebate_type === "percentage" ? `${p.rebate_value}%` : `$${p.rebate_value}`}
                  </td>
                  <td className="px-4 py-3 text-text-secondary capitalize">
                    {p.threshold_type === "none" ? "—" : `${p.threshold_type}: ${p.threshold_value ?? "—"}`}
                  </td>
                  <td className="px-4 py-3 text-text-tertiary">
                    {p.valid_from}{p.valid_to ? ` → ${p.valid_to}` : " →"}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                      p.is_active ? "bg-green-50 text-green-700" : "bg-gray-100 text-gray-500"
                    }`}>
                      {p.is_active ? "Activo" : "Inactivo"}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <button onClick={() => handleDelete(p.id)} className="btn btn-sm btn-ghost p-1.5 text-red-400 hover:text-red-600">
                      <Trash2 size={13} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Ledgers Section */}
      <div className="mt-8">
        <h3 className="text-sm font-bold text-navy mb-3">Ledgers de Rebate</h3>
        {ledgers.length === 0 ? (
          <div className="card p-6 text-center text-xs text-text-tertiary">No hay ledgers registrados.</div>
        ) : (
          <div className="space-y-2">
            {ledgers.map(l => {
              const cfg = STATUS_CONFIG[l.status] ?? STATUS_CONFIG["accruing"];
              const Icon = cfg.icon;
              const isExpanded = expandedLedger === l.id;
              return (
                <div key={l.id} className="card border border-border/60">
                  <button
                    className="w-full flex items-center justify-between px-4 py-3 text-left"
                    onClick={() => setExpandedLedger(isExpanded ? null : l.id)}
                  >
                    <div className="flex items-center gap-3">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold ${cfg.cls}`}>
                        <Icon size={11} />{cfg.label}
                      </span>
                      <span className="text-xs font-mono text-text-secondary">
                        {l.period_start} → {l.period_end}
                      </span>
                      <span className="text-xs text-text-tertiary">{l.entries_count} entrada{l.entries_count !== 1 ? "s" : ""}</span>
                    </div>
                    {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                  </button>

                  {isExpanded && (
                    <div className="border-t border-border/40 px-4 py-3 space-y-3">
                      <div className="grid grid-cols-3 gap-4 text-xs">
                        <div>
                          <p className="text-[10px] text-text-tertiary uppercase font-semibold">Monto Acumulado</p>
                          <p className="font-mono font-bold text-navy">${l.accrued_amount}</p>
                        </div>
                        <div>
                          <p className="text-[10px] text-text-tertiary uppercase font-semibold">Monto Calificante</p>
                          <p className="font-mono text-text-secondary">${l.qualifying_amount}</p>
                        </div>
                        <div>
                          <p className="text-[10px] text-text-tertiary uppercase font-semibold">Unidades</p>
                          <p className="font-mono text-text-secondary">{l.qualifying_units}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                          l.threshold_met ? "bg-green-50 text-green-700" : "bg-gray-100 text-gray-500"
                        }`}>
                          Threshold {l.threshold_met ? "✓ Alcanzado" : "No alcanzado"}
                        </span>
                        {l.liquidation_type && (
                          <span className="text-[10px] text-text-tertiary capitalize">
                            Liquidación: {l.liquidation_type.replace("_", " ")}
                          </span>
                        )}
                      </div>

                      {/* Approve action — solo si status === pending_review */}
                      {l.status === "pending_review" && (
                        <div className="flex items-center gap-2 pt-1">
                          <select
                            className="input text-xs w-40"
                            value={approveType}
                            onChange={e => setApproveType(e.target.value)}
                          >
                            <option value="credit_note">Credit Note</option>
                            <option value="bank_transfer">Bank Transfer</option>
                            <option value="product_credit">Product Credit</option>
                          </select>
                          <button
                            onClick={() => handleApprove(l.id)}
                            disabled={approvingId === l.id}
                            className="btn btn-sm btn-primary"
                          >
                            {approvingId === l.id ? "Aprobando..." : "Aprobar Liquidación"}
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
