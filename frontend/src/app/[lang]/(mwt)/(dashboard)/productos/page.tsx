"use client";

import { useState, useEffect, useCallback } from "react";
import { Package, Plus, Search, Pencil, Trash2, Filter } from "lucide-react";
import api from "@/lib/api";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import FormModal from "@/components/ui/FormModal";

interface Brand {
  slug: string;
  name: string;
}

interface Product {
  id: number;
  name: string;
  sku_base: string;
  brand: string; // Brand slug/id
  brand_name: string;
  category: string;
  description: string;
}

const emptyForm = { name: "", sku_base: "", brand: "", category: "", description: "" };

export default function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [brands, setBrands] = useState<Brand[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [brandFilter, setBrandFilter] = useState("all");
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Product | null>(null);
  const [deleting, setDeleting] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [resProducts, resBrands] = await Promise.all([
        api.get("/productos/"),
        api.get("/brands/")
      ]);
      setProducts(resProducts.data?.results || []);
      setBrands(resBrands.data?.results || []);
    } catch (err) {
      console.error("Error fetching data:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const filtered = products.filter((p) => {
    if (search) {
      const q = search.toLowerCase();
      if (!p.name.toLowerCase().includes(q) && !p.sku_base.toLowerCase().includes(q) && !p.brand_name.toLowerCase().includes(q)) return false;
    }
    if (brandFilter !== "all" && p.brand !== brandFilter) return false;
    return true;
  });

  const openCreate = () => { setForm(emptyForm); setEditingId(null); setShowForm(true); };
  const openEdit = (p: Product) => {
    setForm({
      name: p.name,
      sku_base: p.sku_base,
      brand: p.brand,
      category: p.category || "",
      description: p.description || ""
    });
    setEditingId(p.id);
    setShowForm(true);
  };

  const handleSave = async () => {
    if (!form.name.trim() || !form.sku_base.trim() || !form.brand) return;
    setSaving(true);
    try {
      if (editingId) {
        await api.put(`/productos/${editingId}/`, form);
      } else {
        await api.post("/productos/", form);
      }
      setShowForm(false);
      setEditingId(null);
      await fetchData();
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await api.delete(`/productos/${deleteTarget.id}/`);
      setDeleteTarget(null);
      await fetchData();
    } catch (err) {
      console.error(err);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Productos</h1>
          <p className="page-subtitle">Gestión de SKUs base y catálogo de productos.</p>
        </div>
        <button className="btn btn-md btn-primary" onClick={openCreate}>
          <Plus size={18} /> Nuevo producto
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-3 mb-6">
        <div className="relative" style={{ minWidth: 280 }}>
          <label htmlFor="products-search" className="sr-only">Buscar productos</label>
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: "var(--text-tertiary)" }} />
          <input
            id="products-search"
            type="text"
            placeholder="Buscar por nombre, SKU o marca..."
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
            value={brandFilter}
            onChange={(e) => setBrandFilter(e.target.value)}
          >
            <option value="all">Todas las marcas</option>
            {brands.map(b => (
              <option key={b.slug} value={b.slug}>{b.name}</option>
            ))}
          </select>
        </div>
      </div>

      {loading ? (
        <div className="empty-state"><p>Cargando productos...</p></div>
      ) : filtered.length === 0 ? (
        <div className="empty-state">
          <Package size={48} style={{ color: "var(--text-tertiary)", marginBottom: "var(--space-4)" }} />
          <p>No se encontraron productos.</p>
        </div>
      ) : (
        <div className="grid gap-4" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))" }}>
          {filtered.map((p) => (
            <div key={p.id} className="card p-4">
              <div className="flex items-start justify-between gap-2 mb-3">
                <div>
                  <h3 className="heading-md">{p.name}</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="mono-sm px-1.5 py-0.5 rounded bg-surface-active" style={{ color: "var(--text-secondary)" }}>
                      {p.sku_base}
                    </span>
                    <span className="caption" style={{ color: "var(--text-tertiary)" }}>
                      {p.brand_name}
                    </span>
                  </div>
                </div>
                {p.category && (
                  <span className="badge badge-outline">{p.category}</span>
                )}
              </div>
              
              {p.description && (
                <p className="body-sm mb-4 line-clamp-2" style={{ color: "var(--text-secondary)" }}>
                  {p.description}
                </p>
              )}

              <div className="flex items-center gap-2 pt-3 mt-auto" style={{ borderTop: "1px solid var(--divider)" }}>
                <button className="btn btn-sm btn-ghost" onClick={() => openEdit(p)}>
                  <Pencil size={14} /> Editar
                </button>
                <button className="btn btn-sm btn-danger-outline ml-auto" onClick={() => setDeleteTarget(p)}>
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <FormModal
        open={showForm}
        title={editingId ? "Editar producto" : "Nuevo producto"}
        titleId="product-form-title"
        onClose={() => setShowForm(false)}
        footer={
          <>
            <button className="btn btn-md btn-secondary" onClick={() => setShowForm(false)}>Cancelar</button>
            <button 
              className="btn btn-md btn-primary" 
              onClick={handleSave} 
              disabled={saving || !form.name.trim() || !form.sku_base.trim() || !form.brand}
            >
              {saving ? "Guardando..." : editingId ? "Guardar cambios" : "Crear producto"}
            </button>
          </>
        }
      >
        <div className="grid gap-4">
          <div>
            <label htmlFor="prod-name" className="th-label block mb-1">Nombre del producto</label>
            <input 
              id="prod-name" 
              type="text" 
              className="input" 
              placeholder="Ej: Bota de Seguridad" 
              value={form.name} 
              onChange={(e) => setForm({ ...form, name: e.target.value })} 
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="prod-sku" className="th-label block mb-1">SKU Base</label>
              <input 
                id="prod-sku" 
                type="text" 
                className="input" 
                placeholder="Ej: BOTA-SEC-01" 
                value={form.sku_base} 
                onChange={(e) => setForm({ ...form, sku_base: e.target.value })} 
              />
            </div>
            <div>
              <label htmlFor="prod-brand" className="th-label block mb-1">Marca</label>
              <select 
                id="prod-brand" 
                className="input"
                value={form.brand}
                onChange={(e) => setForm({ ...form, brand: e.target.value })}
              >
                <option value="">Seleccionar marca</option>
                {brands.map(b => (
                  <option key={b.slug} value={b.slug}>{b.name}</option>
                ))}
              </select>
            </div>
          </div>
          <div>
            <label htmlFor="prod-cat" className="th-label block mb-1">Categoría</label>
            <input 
              id="prod-cat" 
              type="text" 
              className="input" 
              placeholder="Ej: Calzado" 
              value={form.category} 
              onChange={(e) => setForm({ ...form, category: e.target.value })} 
            />
          </div>
          <div>
            <label htmlFor="prod-desc" className="th-label block mb-1">Descripción</label>
            <textarea 
              id="prod-desc" 
              className="input min-h-[100px]" 
              placeholder="Descripción opcional..."
              value={form.description} 
              onChange={(e) => setForm({ ...form, description: e.target.value })} 
            />
          </div>
        </div>
      </FormModal>

      <ConfirmDialog
        open={!!deleteTarget}
        title="Eliminar producto"
        message={`¿Estás seguro de eliminar "${deleteTarget?.name}"? Esta acción no se puede deshacer.`}
        confirmLabel="Eliminar producto"
        variant="danger"
        loading={deleting}
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}
