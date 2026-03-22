"use client";

import { useState, useMemo } from "react";
import { 
  ClipboardList, Plus, Search, Pencil, Trash2, 
  MapPin, Hash, Calendar, Filter
} from "lucide-react";
import { useFetch } from "@/hooks/useFetch";
import { useCRUD } from "@/hooks/useCRUD";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import FormModal from "@/components/ui/FormModal";

interface InventoryEntry {
  id: number;
  product: number;
  product_name: string;
  product_sku: string;
  node: string;
  node_name: string;
  quantity: number;
  reserved: number;
  lot_number: string;
  received_at: string;
}

interface Product {
  id: number;
  name: string;
  sku_base: string;
}

interface Node {
  node_id: string;
  name: string;
}

const emptyForm = {
  product: "",
  node: "",
  quantity: 0,
  reserved: 0,
  lot_number: "",
  received_at: new Date().toISOString().split('T')[0]
};

export default function InventarioPage() {
  const { data: entries, loading: loadingEntries, refetch } = useFetch<InventoryEntry[]>("/inventario/");
  const { data: products } = useFetch<Product[]>("/productos/");
  const { data: nodes } = useFetch<Node[]>("/transfers/nodes/");
  const { create, update, remove, loading: saving } = useCRUD("/inventario/");

  const [search, setSearch] = useState("");
  const [nodeFilter, setNodeFilter] = useState("all");
  const [productFilter, setProductFilter] = useState("all");
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [deleteTarget, setDeleteTarget] = useState<InventoryEntry | null>(null);

  const filtered = useMemo(() => {
    let items = Array.isArray(entries) ? entries : [];
    if (search) {
      const q = search.toLowerCase();
      items = items.filter(e => 
        (e.product_name || "").toLowerCase().includes(q) || 
        (e.product_sku || "").toLowerCase().includes(q) || 
        (e.lot_number || "").toLowerCase().includes(q)
      );
    }
    if (nodeFilter !== "all") {
      items = items.filter(e => e.node === nodeFilter);
    }
    if (productFilter !== "all") {
      items = items.filter(e => String(e.product) === productFilter);
    }
    return items;
  }, [entries, search, nodeFilter, productFilter]);

  const openCreate = () => { setForm(emptyForm); setEditingId(null); setShowForm(true); };
  const openEdit = (e: InventoryEntry) => {
    setForm({
      product: String(e.product),
      node: e.node,
      quantity: e.quantity,
      reserved: e.reserved,
      lot_number: e.lot_number,
      received_at: e.received_at ? e.received_at.split('T')[0] : new Date().toISOString().split('T')[0]
    });
    setEditingId(e.id);
    setShowForm(true);
  };

  const handleSave = async () => {
    if (!form.product || !form.node || !form.received_at) return;
    const res = editingId 
      ? await update(String(editingId), form)
      : await create(form);
    
    if (res.success) {
      setShowForm(false);
      refetch();
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    const res = await remove(String(deleteTarget.id));
    if (res.success) {
      setDeleteTarget(null);
      refetch();
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Inventario</h1>
          <p className="page-subtitle">Existencias por producto, nodo y lote.</p>
        </div>
        <button className="btn btn-md btn-primary" onClick={openCreate}>
          <Plus size={18} /> Nueva entrada
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3 mb-6">
        <div className="relative" style={{ minWidth: 250 }}>
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: "var(--text-tertiary)" }} />
          <input
            type="text"
            placeholder="Buscar por producto o lote..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input"
            style={{ paddingLeft: 36 }}
          />
        </div>
        
        <div className="flex items-center gap-2">
          <Filter size={16} style={{ color: "var(--text-tertiary)" }} />
    <select 
            className="input py-1" 
            style={{ width: 180 }}
            value={nodeFilter}
            onChange={(e) => setNodeFilter(e.target.value)}
          >
            <option value="all">Todos los nodos</option>
            {Array.isArray(nodes) ? nodes.map(n => <option key={n.node_id} value={n.node_id}>{n.name}</option>)
              : (nodes as any)?.nodes && Array.isArray((nodes as any).nodes)
              ? (nodes as any).nodes.map((n: any) => <option key={n.node_id} value={n.node_id}>{n.name}</option>)
              : null
            }
          </select>
          <select 
            className="input py-1" 
            style={{ width: 180 }}
            value={productFilter}
            onChange={(e) => setProductFilter(e.target.value)}
          >
            <option value="all">Todos los productos</option>
            {Array.isArray(products) && products.map(p => <option key={p.id} value={p.id}>{p.sku_base}</option>)}
          </select>
        </div>
      </div>

      {loadingEntries ? (
        <div className="empty-state"><p>Cargando inventario...</p></div>
      ) : filtered.length === 0 ? (
        <div className="empty-state">
          <ClipboardList size={48} style={{ color: "var(--text-tertiary)", marginBottom: "var(--space-4)" }} />
          <p>No se encontraron registros de inventario.</p>
        </div>
      ) : (
        <div className="grid gap-4" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))" }}>
          {filtered.map((e) => (
            <div key={e.id} className="card p-4">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h3 className="heading-md">{e.product_name}</h3>
                  <p className="mono-sm mt-0.5" style={{ color: "var(--text-secondary)" }}>{e.product_sku}</p>
                </div>
                <div className="text-right">
                  <span className="badge badge-brand">{e.quantity} disp.</span>
                  {e.reserved > 0 && (
                    <p className="caption mt-1" style={{ color: "var(--warning)" }}>{e.reserved} reservado</p>
                  )}
                </div>
              </div>

              <div className="space-y-2 mt-4 text-sm">
                <div className="flex items-center gap-2" style={{ color: "var(--text-secondary)" }}>
                  <MapPin size={14} style={{ color: "var(--text-tertiary)" }} />
                  <span>{e.node_name}</span>
                </div>
                <div className="flex items-center gap-2" style={{ color: "var(--text-secondary)" }}>
                  <Hash size={14} style={{ color: "var(--text-tertiary)" }} />
                  <span>Lote: {e.lot_number || "Sin lote"}</span>
                </div>
                <div className="flex items-center gap-2" style={{ color: "var(--text-secondary)" }}>
                  <Calendar size={14} style={{ color: "var(--text-tertiary)" }} />
                  <span>Recibido: {e.received_at ? new Date(e.received_at).toLocaleDateString() : "N/A"}</span>
                </div>
              </div>

              <div className="flex items-center gap-2 pt-4 mt-4" style={{ borderTop: "1px solid var(--divider)" }}>
                <button className="btn btn-sm btn-ghost" onClick={() => openEdit(e)}>
                  <Pencil size={14} /> Editar
                </button>
                <button className="btn btn-sm btn-danger-outline ml-auto" onClick={() => setDeleteTarget(e)}>
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Form Modal */}
      <FormModal
        open={showForm}
        title={editingId ? "Editar entrada" : "Nueva entrada de inventario"}
        onClose={() => setShowForm(false)}
        footer={
          <>
            <button className="btn btn-md btn-secondary" onClick={() => setShowForm(false)}>Cancelar</button>
            <button 
              className="btn btn-md btn-primary" 
              onClick={handleSave} 
              disabled={saving || !form.product || !form.node}
            >
              {saving ? "Guardando..." : editingId ? "Guardar" : "Crear"}
            </button>
          </>
        }
      >
        <div className="grid gap-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="th-label mb-1 block">Producto *</label>
              <select 
                className="input"
                value={form.product}
                onChange={(e) => setForm({ ...form, product: e.target.value })}
              >
                <option value="">Seleccionar...</option>
                {Array.isArray(products) ? products.map(p => <option key={p.id} value={p.id}>{p.sku_base} - {p.name}</option>)
                  : (products as any)?.products && Array.isArray((products as any).products)
                  ? (products as any).products.map((p: any) => <option key={p.id} value={p.id}>{p.sku_base} - {p.name}</option>)
                  : null
                }
              </select>
            </div>
            <div>
              <label className="th-label mb-1 block">Nodo *</label>
              <select 
                className="input"
                value={form.node}
                onChange={(e) => setForm({ ...form, node: e.target.value })}
              >
                <option value="">Seleccionar...</option>
                {Array.isArray(nodes) ? nodes.map(n => <option key={n.node_id} value={n.node_id}>{n.name}</option>)
                  : (nodes as any)?.nodes && Array.isArray((nodes as any).nodes)
                  ? (nodes as any).nodes.map((n: any) => <option key={n.node_id} value={n.node_id}>{n.name}</option>)
                  : null
                }
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="th-label mb-1 block">Cantidad</label>
              <input 
                type="number" className="input"
                value={form.quantity}
                onChange={(e) => setForm({ ...form, quantity: parseInt(e.target.value) || 0 })}
              />
            </div>
            <div>
              <label className="th-label mb-1 block">Reservado</label>
              <input 
                type="number" className="input"
                value={form.reserved}
                onChange={(e) => setForm({ ...form, reserved: parseInt(e.target.value) || 0 })}
              />
            </div>
          </div>

          <div>
            <label className="th-label mb-1 block">Número de Lote</label>
            <input 
              type="text" className="input"
              value={form.lot_number}
              onChange={(e) => setForm({ ...form, lot_number: e.target.value })}
              placeholder="Ej: LOTE-2024-001"
            />
          </div>

          <div>
            <label className="th-label mb-1 block">Fecha de Recepción *</label>
            <input 
              type="date" className="input"
              value={form.received_at}
              onChange={(e) => setForm({ ...form, received_at: e.target.value })}
            />
          </div>
        </div>
      </FormModal>

      <ConfirmDialog
        open={!!deleteTarget}
        title="Eliminar de inventario"
        message={`¿Estás seguro de eliminar este registro?`}
        variant="danger"
        loading={saving}
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}
