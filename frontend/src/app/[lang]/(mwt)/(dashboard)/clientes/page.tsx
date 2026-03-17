"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { Users2, Plus, Search, Pencil, Trash2, ChevronRight } from "lucide-react";
import api from "@/lib/api";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import FormModal from "@/components/ui/FormModal";

interface Client {
  id: number;
  name: string;
  contact_name: string | null;
  email: string | null;
  phone: string | null;
  country: string | null;
  legal_entity: number | null;
  legal_entity_name: string | null;
  credit_approved: string | null;
  active_expedientes: number;
  is_active: boolean;
}

interface LegalEntity {
  id: number;
  name: string;
}

const emptyForm = {
  name: "",
  contact_name: "",
  email: "",
  phone: "",
  country: "",
  legal_entity: "" as string,
  is_active: true,
};

export default function ClientesPage() {
  const params = useParams();
  const router = useRouter();
  const lang = (params?.lang as string) || "es";

  const [clients, setClients] = useState<Client[]>([]);
  const [legalEntities, setLegalEntities] = useState<LegalEntity[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Client | null>(null);
  const [deleting, setDeleting] = useState(false);

  const fetchClients = useCallback(async () => {
    try {
      const [cr, er] = await Promise.all([
        api.get("/clientes/"),
        api.get("/core/legal-entities/").catch(() => ({ data: [] })),
      ]);
      setClients(cr.data?.results || cr.data || []);
      setLegalEntities(er.data?.results || er.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchClients(); }, [fetchClients]);

  const filtered = clients.filter((c) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      c.name.toLowerCase().includes(q) ||
      c.legal_entity_name?.toLowerCase().includes(q) ||
      c.email?.toLowerCase().includes(q)
    );
  });

  const openCreate = () => { setForm(emptyForm); setEditingId(null); setShowForm(true); };
  const openEdit = (c: Client) => {
    setForm({
      name: c.name,
      contact_name: c.contact_name || "",
      email: c.email || "",
      phone: c.phone || "",
      country: c.country || "",
      legal_entity: c.legal_entity?.toString() || "",
      is_active: c.is_active,
    });
    setEditingId(c.id);
    setShowForm(true);
  };

  const handleSave = async () => {
    if (!form.name.trim()) return;
    setSaving(true);
    const payload = { ...form, legal_entity: form.legal_entity ? parseInt(form.legal_entity) : null };
    try {
      if (editingId) {
        await api.put(`/clientes/${editingId}/`, payload);
      } else {
        await api.post("/clientes/", payload);
      }
      setShowForm(false);
      setEditingId(null);
      await fetchClients();
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
      await api.delete(`/clientes/${deleteTarget.id}/`);
      setDeleteTarget(null);
      await fetchClients();
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
          <h1 className="page-title">Clientes</h1>
          <p className="page-subtitle">Empresas y personas con expedientes activos.</p>
        </div>
        <button className="btn btn-md btn-primary" onClick={openCreate}>
          <Plus size={18} /> Nuevo cliente
        </button>
      </div>

      <div className="relative mb-6" style={{ maxWidth: 400 }}>
        <label htmlFor="clientes-search" className="sr-only">Buscar clientes</label>
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: "var(--text-tertiary)" }} />
        <input
          id="clientes-search"
          type="text"
          placeholder="Buscar por nombre o entidad..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="input"
          style={{ paddingLeft: 36 }}
        />
      </div>

      {loading ? (
        <div className="empty-state"><p>Cargando clientes...</p></div>
      ) : filtered.length === 0 ? (
        <div className="empty-state"><Users2 size={48} /><p>Sin clientes registrados.</p></div>
      ) : (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Cliente</th>
                <th>Entidad legal</th>
                <th>País</th>
                <th>Crédito aprobado</th>
                <th style={{ textAlign: "right" }}>Exped. activos</th>
                <th>Estado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((c) => (
                <tr key={c.id}>
                  <td>
                    <span className="heading-sm" style={{ color: "var(--text-primary)" }}>{c.name}</span>
                    {c.email && <div className="caption">{c.email}</div>}
                  </td>
                  <td>{c.legal_entity_name || "—"}</td>
                  <td>{c.country || "—"}</td>
                  <td>{c.credit_approved || "—"}</td>
                  <td className="cell-number">{c.active_expedientes || 0}</td>
                  <td>
                    <span className={`badge ${c.is_active ? "badge-success" : "badge-outline"}`}>
                      {c.is_active ? "Activo" : "Inactivo"}
                    </span>
                  </td>
                  <td>
                    <div className="flex items-center gap-1">
                      <button className="btn btn-sm btn-ghost" onClick={() => openEdit(c)} aria-label={`Editar ${c.name}`}><Pencil size={14} /></button>
                      <button className="btn btn-sm btn-ghost" onClick={() => setDeleteTarget(c)} aria-label={`Eliminar ${c.name}`} style={{ color: "var(--critical)" }}><Trash2 size={14} /></button>
                      <button className="btn btn-sm btn-ghost" onClick={() => router.push(`/${lang}/dashboard/clientes/${c.id}`)} aria-label={`Ver detalle de ${c.name}`}><ChevronRight size={14} /></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <FormModal
        open={showForm}
        title={editingId ? "Editar cliente" : "Nuevo cliente"}
        titleId="client-form-title"
        onClose={() => setShowForm(false)}
        footer={
          <>
            <button className="btn btn-md btn-secondary" onClick={() => setShowForm(false)}>Cancelar</button>
            <button className="btn btn-md btn-primary" onClick={handleSave} disabled={saving || !form.name.trim()}>
              {saving ? "Guardando..." : editingId ? "Guardar cambios" : "Crear cliente"}
            </button>
          </>
        }
      >
        <div>
          <label htmlFor="client-name" className="th-label block mb-1">Nombre</label>
          <input id="client-name" type="text" className="input" placeholder="Nombre del cliente" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label htmlFor="client-contact" className="th-label block mb-1">Contacto</label>
            <input id="client-contact" type="text" className="input" placeholder="Persona de contacto" value={form.contact_name} onChange={(e) => setForm({ ...form, contact_name: e.target.value })} />
          </div>
          <div>
            <label htmlFor="client-email" className="th-label block mb-1">Email</label>
            <input id="client-email" type="email" className="input" placeholder="email@empresa.com" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label htmlFor="client-phone" className="th-label block mb-1">Teléfono</label>
            <input id="client-phone" type="text" className="input" placeholder="+506 8888-8888" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          </div>
          <div>
            <label htmlFor="client-country" className="th-label block mb-1">País</label>
            <input id="client-country" type="text" className="input" placeholder="Costa Rica" value={form.country} onChange={(e) => setForm({ ...form, country: e.target.value })} />
          </div>
        </div>
        <div>
          <label htmlFor="client-entity" className="th-label block mb-1">Entidad legal</label>
          <select id="client-entity" className="input" value={form.legal_entity} onChange={(e) => setForm({ ...form, legal_entity: e.target.value })}>
            <option value="">Sin entidad</option>
            {legalEntities.map((le) => <option key={le.id} value={le.id}>{le.name}</option>)}
          </select>
        </div>
        <label htmlFor="client-active" className="flex items-center gap-2 cursor-pointer">
          <input id="client-active" type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} className="rounded" />
          <span className="body-md">Cliente activo</span>
        </label>
      </FormModal>

      <ConfirmDialog
        open={!!deleteTarget}
        title="Eliminar cliente"
        message={`¿Eliminar "${deleteTarget?.name}"? Los expedientes no se eliminarán.`}
        confirmLabel="Eliminar cliente"
        variant="danger"
        loading={deleting}
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}
