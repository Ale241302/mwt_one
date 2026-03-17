"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams } from "next/navigation";
import { Building2, Plus, Search, Pencil, Trash2, Globe, FolderOpen } from "lucide-react";
import api from "@/lib/api";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import FormModal from "@/components/ui/FormModal";

interface Brand {
  slug: string;
  name: string;
  code: string;
  is_active: boolean;
  markets: string[];
  expedientes_count: number;
}

type StatusFilter = "all" | "active" | "inactive";

/* S9.1-08: Filtro 'Pausada' placebo eliminado */
const emptyForm = { name: "", code: "", is_active: true };

export default function BrandsPage() {
  const [brands, setBrands] = useState<Brand[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [showForm, setShowForm] = useState(false);
  const [editingSlug, setEditingSlug] = useState<string | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Brand | null>(null);
  const [deleting, setDeleting] = useState(false);

  const fetchBrands = useCallback(async () => {
    try {
      setBrands((await api.get("/api/brands/")).data?.results || []);
    } catch (err) {
      console.error("Error fetching brands:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchBrands(); }, [fetchBrands]);

  const filtered = brands.filter((b) => {
    if (search) {
      const q = search.toLowerCase();
      if (!b.name.toLowerCase().includes(q) && !b.slug.toLowerCase().includes(q)) return false;
    }
    if (statusFilter === "active" && !b.is_active) return false;
    if (statusFilter === "inactive" && b.is_active) return false;
    return true;
  });

  const openCreate = () => { setForm(emptyForm); setEditingSlug(null); setShowForm(true); };
  const openEdit = (b: Brand) => {
    setForm({ name: b.name, code: b.code || "", is_active: b.is_active });
    setEditingSlug(b.slug);
    setShowForm(true);
  };

  const handleSave = async () => {
    if (!form.name.trim()) return;
    setSaving(true);
    try {
      if (editingSlug) {
        await api.put(`/api/brands/${editingSlug}/`, form);
      } else {
        await api.post("/api/brands/", form);
      }
      setShowForm(false);
      setEditingSlug(null);
      await fetchBrands();
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
      await api.delete(`/api/brands/${deleteTarget.slug}/`);
      setDeleteTarget(null);
      await fetchBrands();
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
          <h1 className="page-title">Brands</h1>
          <p className="page-subtitle">Marcas comerciales gestionadas por MWT.</p>
        </div>
        <button className="btn btn-md btn-primary" onClick={openCreate}>
          <Plus size={18} /> Nueva brand
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-3 mb-6">
        <div className="relative" style={{ minWidth: 240 }}>
          <label htmlFor="brands-search" className="sr-only">Buscar brands</label>
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: "var(--text-tertiary)" }} />
          <input
            id="brands-search"
            type="text"
            placeholder="Buscar por nombre o slug..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input"
            style={{ paddingLeft: 36 }}
          />
        </div>
        {(["all", "active", "inactive"] as StatusFilter[]).map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className="btn btn-sm"
            style={{
              background: statusFilter === s ? "var(--surface-active)" : "transparent",
              color: "var(--text-primary)",
              border: `1px solid ${statusFilter === s ? "var(--border-strong)" : "var(--border)"}`,
            }}
          >
            {s === "all" ? "Todas" : s === "active" ? "Activa" : "Inactiva"}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="empty-state"><p>Cargando marcas...</p></div>
      ) : filtered.length === 0 ? (
        <div className="empty-state"><Building2 size={48} /><p>Sin marcas registradas.</p></div>
      ) : (
        <div className="grid gap-4" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))" }}>
          {filtered.map((b) => (
            <div key={b.slug} className="card" style={{ padding: "var(--space-4)" }}>
              <div className="flex items-start justify-between gap-2 mb-3">
                <div>
                  <div className="flex items-center gap-2">
                    <Building2 size={18} style={{ color: "var(--text-tertiary)" }} />
                    <h3 className="heading-md">{b.name}</h3>
                  </div>
                  <span className="mono-sm" style={{ color: "var(--text-tertiary)" }}>{b.slug}</span>
                </div>
                <span className={`badge ${b.is_active ? "badge-success" : "badge-outline"}`}>
                  {b.is_active ? "Activa" : "Inactiva"}
                </span>
              </div>
              <div className="flex items-center gap-4 mb-3" style={{ color: "var(--text-secondary)" }}>
                <span className="flex items-center gap-1 caption"><Globe size={12} /> {b.markets?.length || 0} mercados</span>
                <span className="flex items-center gap-1 caption"><FolderOpen size={12} /> {b.expedientes_count || 0} expedientes</span>
              </div>
              <div className="flex items-center gap-2 pt-3" style={{ borderTop: "1px solid var(--divider)" }}>
                <button className="btn btn-sm btn-ghost" onClick={() => openEdit(b)} aria-label={`Editar ${b.name}`}>
                  <Pencil size={14} /> Editar
                </button>
                <button className="btn btn-sm btn-danger-outline" onClick={() => setDeleteTarget(b)} aria-label={`Eliminar ${b.name}`}>
                  <Trash2 size={14} /> Eliminar
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <FormModal
        open={showForm}
        title={editingSlug ? "Editar brand" : "Nueva brand"}
        titleId="brand-form-title"
        onClose={() => setShowForm(false)}
        footer={
          <>
            <button className="btn btn-md btn-secondary" onClick={() => setShowForm(false)}>Cancelar</button>
            <button className="btn btn-md btn-primary" onClick={handleSave} disabled={saving || !form.name.trim()}>
              {saving ? "Guardando..." : editingSlug ? "Guardar cambios" : "Crear brand"}
            </button>
          </>
        }
      >
        <div>
          <label htmlFor="brand-name" className="th-label block mb-1">Nombre</label>
          <input id="brand-name" type="text" className="input" placeholder="Ej: Rana Walk" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        </div>
        <div>
          <label htmlFor="brand-code" className="th-label block mb-1">Código</label>
          <input id="brand-code" type="text" className="input" placeholder="Ej: RW" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} />
        </div>
        <label htmlFor="brand-active" className="flex items-center gap-2 cursor-pointer">
          <input id="brand-active" type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} className="rounded" />
          <span className="body-md">Brand activa</span>
        </label>
      </FormModal>

      <ConfirmDialog
        open={!!deleteTarget}
        title="Eliminar brand"
        message={`¿Eliminar "${deleteTarget?.name}"? Afectará expedientes asociados.`}
        confirmLabel="Eliminar brand"
        variant="danger"
        loading={deleting}
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}
