"use client";

import { useState, useEffect, useCallback } from "react";
import { Network, Plus, Search, Pencil, Trash2, MapPin } from "lucide-react";
import api from "@/lib/api";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import FormModal from "@/components/ui/FormModal";

interface Node {
  node_id: string;
  name: string;
  node_type: string;
  location: string | null;
  status: string;
  legal_entity_name: string | null;
  legal_entity_id: string | null;
}

// Tipos reales del modelo Node (enums.py NodeType)
const NODE_TYPES = [
  { value: "fiscal",          label: "Fiscal" },
  { value: "owned_warehouse", label: "Almacén propio" },
  { value: "fba",             label: "FBA" },
  { value: "third_party",     label: "Tercero" },
  { value: "factory",         label: "Fábrica" },
];

const TYPE_STYLES: Record<string, { bg: string; color: string; border: string }> = {
  fiscal:          { bg: "var(--warning-bg)",        color: "var(--warning)",       border: "var(--warning)" },
  owned_warehouse: { bg: "var(--brand-accent-soft)", color: "var(--brand-primary)", border: "var(--brand-primary)" },
  fba:             { bg: "var(--info-bg)",           color: "var(--info)",          border: "var(--info)" },
  third_party:     { bg: "var(--bg-alt)",            color: "var(--text-secondary)",border: "var(--border)" },
  factory:         { bg: "var(--success-bg)",        color: "var(--success)",       border: "var(--success)" },
};

const emptyForm = {
  name: "",
  node_type: "owned_warehouse",
  location: "",
  status: "active",
  legal_entity: "",
};

export default function NodosPage() {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Node | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const fetchNodes = useCallback(async () => {
    try {
      const res = await api.get("/transfers/nodes/");
      setNodes(res.data?.results || res.data || []);
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
      n.location?.toLowerCase().includes(q)
    );
  });

  const openCreate = () => {
    setForm(emptyForm);
    setEditingId(null);
    setSaveError(null);
    setShowForm(true);
  };

  const openEdit = (node: Node) => {
    setForm({
      name: node.name,
      node_type: node.node_type,
      location: node.location || "",
      status: node.status,
      legal_entity: node.legal_entity_id || "",
    });
    setEditingId(node.node_id);
    setSaveError(null);
    setShowForm(true);
  };

  const handleSave = async () => {
    if (!form.name.trim()) return;
    setSaving(true);
    setSaveError(null);
    try {
      const payload = {
        name: form.name.trim(),
        node_type: form.node_type,
        location: form.location.trim(),
        status: form.status,
        legal_entity: form.legal_entity.trim(),
      };
      if (editingId) {
        await api.put(`/transfers/nodes/${editingId}/`, payload);
      } else {
        await api.post("/transfers/nodes/create/", payload);
      }
      setShowForm(false);
      setEditingId(null);
      setForm(emptyForm);
      await fetchNodes();
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: Record<string, unknown> } };
      const errData = axiosErr?.response?.data;
      if (errData) {
        const msg = Object.entries(errData)
          .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
          .join(' | ');
        setSaveError(msg);
      } else {
        setSaveError("Error al guardar el nodo.");
      }
      console.error("Error saving node:", err);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await api.delete(`/transfers/nodes/${deleteTarget.node_id}/delete/`);
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
          placeholder="Buscar por nombre, tipo o ubicación..."
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
            const st = TYPE_STYLES[node.node_type] || TYPE_STYLES.third_party;
            return (
              <div key={node.node_id} className="card" style={{ padding: "var(--space-4)" }}>
                <div className="flex items-start justify-between gap-2 mb-3">
                  <div className="flex-1 min-w-0">
                    <h3 className="heading-md truncate">{node.name}</h3>
                    {node.location && (
                      <div className="flex items-center gap-1 mt-1" style={{ color: "var(--text-tertiary)" }}>
                        <MapPin size={12} />
                        <span className="caption">{node.location}</span>
                      </div>
                    )}
                  </div>
                  <span className="badge" style={{ background: st.bg, color: st.color, border: `1px solid ${st.border}` }}>
                    {NODE_TYPES.find((t) => t.value === node.node_type)?.label || node.node_type}
                  </span>
                </div>
                <div className="flex items-center gap-2 mb-3">
                  <span className={`badge ${node.status === 'active' ? 'badge-success' : 'badge-outline'}`}>
                    {node.status === 'active' ? 'Activo' : 'Inactivo'}
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
            <button
              className="btn btn-md btn-primary"
              onClick={handleSave}
              disabled={saving || !form.name.trim()}
            >
              {saving ? "Guardando..." : editingId ? "Guardar cambios" : "Crear nodo"}
            </button>
          </>
        }
      >
        {saveError && (
          <div className="p-3 rounded-lg bg-coral-soft/20 border border-coral/30 text-sm text-coral mb-2">
            {saveError}
          </div>
        )}
        <div>
          <label htmlFor="node-name" className="th-label block mb-1">Nombre *</label>
          <input
            id="node-name" type="text" className="input"
            placeholder="Ej: Almacén Fiscal CR"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
        </div>
        <div>
          <label htmlFor="node-type" className="th-label block mb-1">Tipo de nodo</label>
          <select
            id="node-type" className="input"
            value={form.node_type}
            onChange={(e) => setForm({ ...form, node_type: e.target.value })}
          >
            {NODE_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
          </select>
        </div>
        <div>
          <label htmlFor="node-location" className="th-label block mb-1">Ubicación</label>
          <input
            id="node-location" type="text" className="input"
            placeholder="Ej: San José, Costa Rica"
            value={form.location}
            onChange={(e) => setForm({ ...form, location: e.target.value })}
          />
        </div>
        <div>
          <label htmlFor="node-legal-entity" className="th-label block mb-1">
            Entidad Legal <span className="text-text-tertiary font-normal">(entity_id, ej: MWT-CR)</span>
          </label>
          <input
            id="node-legal-entity" type="text" className="input"
            placeholder="MWT-CR (dejar vacío para usar la primera disponible)"
            value={form.legal_entity}
            onChange={(e) => setForm({ ...form, legal_entity: e.target.value })}
          />
        </div>
        <div>
          <label htmlFor="node-status" className="th-label block mb-1">Estado</label>
          <select
            id="node-status" className="input"
            value={form.status}
            onChange={(e) => setForm({ ...form, status: e.target.value })}
          >
            <option value="active">Activo</option>
            <option value="inactive">Inactivo</option>
          </select>
        </div>
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
