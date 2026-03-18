"use client";

import { useState, useEffect, useCallback } from "react";
import { Users, Plus, Search, Pencil, Trash2, ShieldCheck, ShieldOff } from "lucide-react";
import api from "@/lib/api";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import FormModal from "@/components/ui/FormModal";

// ─── Types ─────────────────────────────────────────────────────────────────────

interface MWTUser {
  id: number;
  username: string;
  email: string;
  role: string;
  is_api_user: boolean;
  legal_entity_id: string | null;
  whatsapp_number: string | null;
  is_active: boolean;
}

const ROLES = [
  { value: "INTERNAL",  label: "Interno" },
  { value: "EXTERNAL",  label: "Externo" },
  { value: "API",       label: "API" },
  { value: "SUPERUSER", label: "Superusuario" },
];

const ROLE_COLORS: Record<string, { bg: string; color: string }> = {
  SUPERUSER: { bg: "var(--warning-bg)",        color: "var(--warning)" },
  INTERNAL:  { bg: "var(--brand-accent-soft)", color: "var(--brand-primary)" },
  EXTERNAL:  { bg: "var(--bg-alt)",            color: "var(--text-secondary)" },
  API:       { bg: "var(--info-bg)",           color: "var(--info)" },
};

const emptyForm = {
  username: "",
  email: "",
  password: "",
  role: "INTERNAL",
  whatsapp_number: "",
  legal_entity_id: "",
  is_api_user: false,
  is_active: true,
};

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function UsuariosPage() {
  const [users, setUsers] = useState<MWTUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<MWTUser | null>(null);
  const [deleting, setDeleting] = useState(false);

  const fetchUsers = useCallback(async () => {
    try {
      const res = await api.get("/admin/users/");
      const raw = res.data;
      setUsers(Array.isArray(raw) ? raw : raw?.users ?? []);
    } catch (err) {
      console.error("Error fetching users:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchUsers(); }, [fetchUsers]);

  const filtered = users.filter((u) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      u.username.toLowerCase().includes(q) ||
      u.email.toLowerCase().includes(q) ||
      u.role.toLowerCase().includes(q)
    );
  });

  const openCreate = () => {
    setForm(emptyForm);
    setEditingId(null);
    setSaveError(null);
    setShowForm(true);
  };

  const openEdit = (user: MWTUser) => {
    setForm({
      username: user.username,
      email: user.email,
      password: "",
      role: user.role,
      whatsapp_number: user.whatsapp_number ?? "",
      legal_entity_id: user.legal_entity_id ?? "",
      is_api_user: user.is_api_user,
      is_active: user.is_active,
    });
    setEditingId(user.id);
    setSaveError(null);
    setShowForm(true);
  };

  const handleSave = async () => {
    if (!form.username.trim()) return;
    if (!editingId && !form.password.trim()) {
      setSaveError("La contraseña es requerida al crear un usuario.");
      return;
    }
    setSaving(true);
    setSaveError(null);
    try {
      const payload: Record<string, unknown> = {
        username: form.username.trim(),
        email: form.email.trim(),
        role: form.role,
        whatsapp_number: form.whatsapp_number.trim() || null,
        legal_entity_id: form.legal_entity_id.trim() || null,
        is_api_user: form.is_api_user,
        is_active: form.is_active,
      };
      if (form.password.trim()) payload.password = form.password.trim();

      if (editingId) {
        await api.patch(`/admin/users/${editingId}/`, payload);
      } else {
        await api.post("/admin/users/", payload);
      }
      setShowForm(false);
      setEditingId(null);
      setForm(emptyForm);
      await fetchUsers();
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: Record<string, unknown> } };
      const errData = axiosErr?.response?.data;
      if (errData) {
        const msg = Object.entries(errData)
          .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(", ") : v}`)
          .join(" | ");
        setSaveError(msg);
      } else {
        setSaveError("Error al guardar el usuario.");
      }
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await api.delete(`/admin/users/${deleteTarget.id}/`);
      setDeleteTarget(null);
      await fetchUsers();
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      const detail = axiosErr?.response?.data?.detail ?? "Error al eliminar el usuario.";
      setSaveError(detail);
      setDeleteTarget(null);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Usuarios</h1>
          <p className="page-subtitle">Gestión de accesos y roles del sistema MWT.</p>
        </div>
        <button className="btn btn-md btn-primary" onClick={openCreate}>
          <Plus size={18} /> Nuevo usuario
        </button>
      </div>

      {saveError && (
        <div className="p-3 rounded-lg bg-coral-soft/20 border border-coral/30 text-sm text-coral mb-4">
          {saveError}
          <button className="ml-2 underline" onClick={() => setSaveError(null)}>Cerrar</button>
        </div>
      )}

      <div className="relative mb-6" style={{ maxWidth: 400 }}>
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: "var(--text-tertiary)" }} />
        <input
          type="text"
          placeholder="Buscar por nombre, email o rol..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="input"
          style={{ paddingLeft: 36 }}
        />
      </div>

      {loading ? (
        <div className="empty-state"><p>Cargando usuarios...</p></div>
      ) : filtered.length === 0 ? (
        <div className="empty-state">
          <Users size={48} />
          <p>{searchQuery ? "Sin resultados." : "No hay usuarios registrados."}</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-border">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  {["Usuario", "Email", "Rol", "Estado", "WhatsApp", "Acciones"].map((h) => (
                    <th key={h} className="text-left px-5 py-3 text-xs font-semibold uppercase tracking-[0.5px] text-text-secondary">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filtered.map((u) => {
                  const roleStyle = ROLE_COLORS[u.role] ?? ROLE_COLORS.EXTERNAL;
                  return (
                    <tr key={u.id} className="hover:bg-bg transition-colors">
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-2">
                          <div className="w-7 h-7 rounded-full bg-brand-primary/10 flex items-center justify-center text-xs font-bold text-brand-primary">
                            {u.username[0]?.toUpperCase()}
                          </div>
                          <span className="font-medium text-navy">{u.username}</span>
                          {u.is_api_user && (
                            <span className="text-[10px] bg-info-bg text-info px-1.5 py-0.5 rounded font-semibold">API</span>
                          )}
                        </div>
                      </td>
                      <td className="px-5 py-3 text-text-secondary">{u.email || "—"}</td>
                      <td className="px-5 py-3">
                        <span className="badge" style={{ background: roleStyle.bg, color: roleStyle.color }}>
                          {ROLES.find((r) => r.value === u.role)?.label ?? u.role}
                        </span>
                      </td>
                      <td className="px-5 py-3">
                        {u.is_active ? (
                          <span className="inline-flex items-center gap-1 text-xs text-success"><ShieldCheck size={13} /> Activo</span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-xs text-text-tertiary"><ShieldOff size={13} /> Inactivo</span>
                        )}
                      </td>
                      <td className="px-5 py-3 text-text-secondary text-xs">{u.whatsapp_number || "—"}</td>
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-2">
                          <button
                            className="btn btn-sm btn-ghost"
                            onClick={() => openEdit(u)}
                            aria-label={`Editar ${u.username}`}
                          >
                            <Pencil size={13} /> Editar
                          </button>
                          <button
                            className="btn btn-sm btn-danger-outline"
                            onClick={() => setDeleteTarget(u)}
                            aria-label={`Eliminar ${u.username}`}
                          >
                            <Trash2 size={13} /> Eliminar
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ─── Form Modal ─── */}
      <FormModal
        open={showForm}
        title={editingId ? "Editar usuario" : "Nuevo usuario"}
        titleId="user-form-title"
        onClose={() => setShowForm(false)}
        footer={
          <>
            <button className="btn btn-md btn-secondary" onClick={() => setShowForm(false)}>Cancelar</button>
            <button
              className="btn btn-md btn-primary"
              onClick={handleSave}
              disabled={saving || !form.username.trim()}
            >
              {saving ? "Guardando..." : editingId ? "Guardar cambios" : "Crear usuario"}
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
          <label className="th-label block mb-1">Nombre de usuario *</label>
          <input
            type="text" className="input" placeholder="john.doe"
            value={form.username}
            onChange={(e) => setForm({ ...form, username: e.target.value })}
          />
        </div>
        <div>
          <label className="th-label block mb-1">Email</label>
          <input
            type="email" className="input" placeholder="john@mwt.com"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
          />
        </div>
        <div>
          <label className="th-label block mb-1">
            Contraseña {editingId && <span className="text-text-tertiary font-normal">(dejar vacío para no cambiar)</span>}
          </label>
          <input
            type="password" className="input" placeholder={editingId ? "••••••••" : "Mínimo 8 caracteres"}
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
          />
        </div>
        <div>
          <label className="th-label block mb-1">Rol</label>
          <select className="input" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
            {ROLES.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
          </select>
        </div>
        <div>
          <label className="th-label block mb-1">WhatsApp</label>
          <input
            type="text" className="input" placeholder="+506 8888 0000"
            value={form.whatsapp_number}
            onChange={(e) => setForm({ ...form, whatsapp_number: e.target.value })}
          />
        </div>
        <div>
          <label className="th-label block mb-1">Legal Entity ID</label>
          <input
            type="text" className="input" placeholder="MWT-CR"
            value={form.legal_entity_id}
            onChange={(e) => setForm({ ...form, legal_entity_id: e.target.value })}
          />
        </div>
        <div className="flex items-center gap-3">
          <input
            id="is_api_user"
            type="checkbox"
            checked={form.is_api_user}
            onChange={(e) => setForm({ ...form, is_api_user: e.target.checked })}
            className="w-4 h-4 rounded"
          />
          <label htmlFor="is_api_user" className="th-label cursor-pointer">Es usuario API</label>
        </div>
        <div className="flex items-center gap-3">
          <input
            id="is_active"
            type="checkbox"
            checked={form.is_active}
            onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
            className="w-4 h-4 rounded"
          />
          <label htmlFor="is_active" className="th-label cursor-pointer">Activo</label>
        </div>
      </FormModal>

      {/* ─── Confirm Delete ─── */}
      <ConfirmDialog
        open={!!deleteTarget}
        title="Eliminar usuario"
        message={`¿Estás seguro de eliminar a "${deleteTarget?.username}"? Esta acción es irreversible.`}
        confirmLabel="Eliminar usuario"
        variant="danger"
        loading={deleting}
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}
