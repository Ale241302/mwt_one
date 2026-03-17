"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { Network, Plus, Search, Pencil, Trash2, MapPin } from "lucide-react";
import api from "@/lib/api";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import FormModal from "@/components/ui/FormModal";

interface Node {
  id: number;
  name: string;
  node_type: string;
  city: string | null;
  country: string | null;
  legal_entity_name: string | null;
  is_active: boolean;
}

const NODE_TYPES = [
  { value: "FISCAL", label: "Fiscal" },
  { value: "DESTINATION", label: "Destino" },
  { value: "LOGISTICS_HUB", label: "Hub logístico" },
  { value: "WAREHOUSE", label: "Almacén" },
  { value: "PORT", label: "Puerto" },
  { value: "AIRPORT", label: "Aeropuerto" },
];

/* S9.1-07: TYPE_STYLES usa CSS vars semánticos (no concatenación inválida de Tailwind) */
const TYPE_STYLES: Record<string, { bg: string; color: string; border: string }> = {
  FISCAL:        { bg: "var(--warning-bg)",       color: "var(--warning)",       border: "var(--warning)" },
  DESTINATION:   { bg: "var(--info-bg)",          color: "var(--info)",          border: "var(--info)" },
  LOGISTICS_HUB: { bg: "var(--success-bg)",       color: "var(--success)",       border: "var(--success)" },
  WAREHOUSE:     { bg: "var(--brand-accent-soft)", color: "var(--brand-primary)", border: "var(--brand-primary)" },
  PORT:          { bg: "var(--brand-ice-soft)",   color: "var(--info)",          border: "var(--info)" },
  AIRPORT:       { bg: "var(--critical-bg)",      color: "var(--critical)",      border: "var(--critical)" },
};

const emptyForm = { name: "", node_type: "WAREHOUSE", city: "", country: "", is_active: true };

export default function NodosPage() {
  const params = useParams();
  const router = useRouter();
  const lang = (params?.lang as string) || "es";

  const [nodes, setNodes] = useState<Node[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Node | null>(null);
  const [deleting, setDeleting] = useState(false);

  const fetchNodes = useCallback(async () => {
    try {
      setNodes((await api.get("/api/transfers/nodes/")).data?.results || []);
    } catch (err) {
      console.error("Error fetching nodes:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchNodes(); }, [fetchNodes]);

  const filtered = nodes.filter((n) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      n.name.toLowerCase().includes(q) ||
      n.node_type.toLowerCase().includes(q) ||
      n.city?.toLowerCase().includes(q)
    );
  });

  const openCreate = () => { setForm(emptyForm); setEditingId(null); setShowForm(true); };
  const openEdit = (node: Node) => {
    setForm({ name: node.name, node_type: node.node_type, city: node.city || "", country: node.country || "", is_active: node.is_active });
    setEditingId(node.id);
    setShowForm(true);
  };

  const handleSave = async () => {
    if (!form.name.trim()) return;
    setSaving(true);
    try {
      if (editingId) {
        await api.put(`/api/transfers/nodes/${editingId}/`, form);
      } else {
        await api.post("/api/transfers/nodes/create/", form);
      }
      setShowForm(false);
      setEditingId(null);
      setForm(emptyForm);
      await fetchNodes();
    } catch (err) {
      console.error("Error saving node:", err);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await api.delete(`/api/transfers/nodes/${deleteTarget.id}/`);
      setDeleteTarget(null);
      await fetchNodes();
    } catch (err) {
      console.error("Error deleting node:", err);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Nodos</h1>
          <p className="page-subtitle">Puntos de origen, destino e intermedios de la red logística.</p>
        </div>
        <button className="btn btn-md btn-primary" onClick={openCreate}>
          <Plus size={18} /> Nuevo nodo
        </button>
      </div>

      <div className="relative mb-6" style={{ maxWidth: 400 }}>
        <label htmlFor="nodos-search" className="sr-only">Buscar nodos</label>
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: "var(--text-tertiary)" }} />
        <input
          id="nodos-search"
          type="text"
          placeholder="Buscar por nombre o tipo..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="input"
          style={{ paddingLeft: 36 }}
        />
      </div>

      {loading ? (
        <div className="empty-state"><p>Cargando nodos...</p></div>
      ) : filtered.length === 0 ? (
        <div className="empty-state">
          <Network size={48} />
          <p>{searchQuery ? "Sin resultados." : "No hay nodos registrados."}</p>
        </div>
      ) : (
        <div className="grid gap-4" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))" }}>
          {filtered.map((node) => {
            const st = TYPE_STYLES[node.node_type] || TYPE_STYLES.WAREHOUSE;
            return (
              <div key={node.id} className="card" style={{ padding: "var(--space-4)" }}>
                <div className="flex items-start justify-between gap-2 mb-3">
                  <div className="flex-1 min-w-0">
                    <h3 className="heading-md truncate">{node.name}</h3>
                    {node.city && (
                      <div className="flex items-center gap-1 mt-1" style={{ color: "var(--text-tertiary)" }}>
                        <MapPin size={12} />
                        <span className="caption">{[node.city, node.country].filter(Boolean).join(", ")}</span>
                      </div>
                    )}
                  </div>
                  <span
                    className="badge"
                    style={{ background: st.bg, color: st.color, border: `1px solid ${st.border}` }}
                  >
                    {NODE_TYPES.find((t) => t.value === node.node_type)?.label || node.node_type}
                  </span>
                </div>
                <div className="flex items-center gap-2 mb-3">
                  <span className={`badge ${node.is_active ? "badge-success" : "badge-outline"}`}>
                    {node.is_active ? "Activo" : "Inactivo"}
                  </span>
                  {node.legal_entity_name && (
                    <span className="caption truncate">{node.legal_entity_name}</span>
                  )}
                </div>
                <div className="flex items-center gap-2 pt-3" style={{ borderTop: "1px solid var(--divider)" }}>
                  <button className="btn btn-sm btn-ghost" onClick={() => openEdit(node)} aria-label={`Editar ${node.name}`}>
                    <Pencil size={14} /> Editar
                  </button>
                  <button className="btn btn-sm btn-danger-outline" onClick={() => setDeleteTarget(node)} aria-label={`Eliminar ${node.name}`}>
                    <Trash2 size={14} /> Eliminar
                  </button>
                  <button
                    className="btn btn-sm btn-secondary ml-auto"
                    onClick={() => router.push(`/${lang}/dashboard/nodos/${node.id}`)}
                  >
                    Ver detalle
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      <FormModal
        open={showForm}
        title={editingId ? "Editar nodo" : "Nuevo nodo"}
        titleId="node-form-title"
        onClose={() => setShowForm(false)}
        footer={
          <>
            <button className="btn btn-md btn-secondary" onClick={() => setShowForm(false)}>Cancelar</button>
            <button className="btn btn-md btn-primary" onClick={handleSave} disabled={saving || !form.name.trim()}>
              {saving ? "Guardando..." : editingId ? "Guardar cambios" : "Crear nodo"}
            </button>
          </>
        }
      >
        <div>
          <label htmlFor="node-name" className="th-label block mb-1">Nombre</label>
          <input id="node-name" type="text" className="input" placeholder="Ej: Almacén Fiscal CR" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        </div>
        <div>
          <label htmlFor="node-type" className="th-label block mb-1">Tipo de nodo</label>
          <select id="node-type" className="input" value={form.node_type} onChange={(e) => setForm({ ...form, node_type: e.target.value })}>
            {NODE_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
          </select>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label htmlFor="node-city" className="th-label block mb-1">Ciudad</label>
            <input id="node-city" type="text" className="input" placeholder="San José" value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} />
          </div>
          <div>
            <label htmlFor="node-country" className="th-label block mb-1">País</label>
            <input id="node-country" type="text" className="input" placeholder="Costa Rica" value={form.country} onChange={(e) => setForm({ ...form, country: e.target.value })} />
          </div>
        </div>
        <label htmlFor="node-active" className="flex items-center gap-2 cursor-pointer">
          <input id="node-active" type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} className="rounded" />
          <span className="body-md">Nodo activo</span>
        </label>
      </FormModal>

      <ConfirmDialog
        open={!!deleteTarget}
        title="Eliminar nodo"
        message={`¿Estás seguro de eliminar "${deleteTarget?.name}"?`}
        confirmLabel="Eliminar nodo"
        variant="danger"
        loading={deleting}
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}
