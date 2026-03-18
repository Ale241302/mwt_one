"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeftRight, Plus, ChevronRight,
  Clock, CheckCircle, Truck, Package, XCircle, Pencil, Trash2
} from "lucide-react";
import { cn } from "@/lib/utils";
import api from "@/lib/api";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import FormModal from "@/components/ui/FormModal";

// ─── Types ─────────────────────────────────────────────────────────────────────
interface Transfer {
  transfer_id: string;
  status: "planned" | "approved" | "in_transit" | "received" | "reconciled" | "cancelled";
  legal_context: string;
  ownership_changes: boolean;
  customs_required: boolean;
  notes?: string;
  created_at: string;
  from_node: string | { node_id: string; name: string; legal_entity_name?: string };
  to_node:   string | { node_id: string; name: string; legal_entity_name?: string };
}

function nodeName(n: Transfer["from_node"]): string {
  if (!n) return "—";
  if (typeof n === "object") return n.name ?? String(n.node_id);
  return String(n);
}

function nodeId(n: Transfer["from_node"]): string {
  if (!n) return "";
  if (typeof n === "object") return n.node_id;
  return String(n);
}

// ─── Status config ─────────────────────────────────────────────────────────────
const STATUS_CONFIG: Record<string, { label: string; classes: string; icon: React.ReactNode }> = {
  planned:     { label: "Planeado",     classes: "bg-[#F1F5F9] text-[#475569]",  icon: <Clock size={12} /> },
  approved:    { label: "Aprobado",     classes: "bg-[#FFF7ED] text-[#B45309]",  icon: <CheckCircle size={12} /> },
  in_transit:  { label: "En tránsito",  classes: "bg-[#EFF6FF] text-[#1D4ED8]",  icon: <Truck size={12} /> },
  received:    { label: "Recibido",     classes: "bg-[#F5F3FF] text-[#7C3AED]",  icon: <Package size={12} /> },
  reconciled:  { label: "Reconciliado", classes: "bg-[#F0FAF6] text-[#0E8A6D]",  icon: <CheckCircle size={12} /> },
  cancelled:   { label: "Cancelado",    classes: "bg-[#FEF2F2] text-[#DC2626]",  icon: <XCircle size={12} /> },
};

const STATUS_KEYS = Object.keys(STATUS_CONFIG);
const FILTERS = ["todos", ...STATUS_KEYS] as const;

function StatusBadge({ status }: { status: string }) {
  const cfg = STATUS_CONFIG[status] ?? STATUS_CONFIG["planned"];
  return (
    <span className={cn(
      "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold uppercase tracking-[0.5px]",
      cfg.classes
    )}>
      {cfg.icon} {cfg.label}
    </span>
  );
}

const emptyEditForm = {
  legal_context: "intracompany",
  ownership_changes: false,
  customs_required: false,
  notes: "",
  from_node: "",
  to_node: "",
};

// ─── Page ─────────────────────────────────────────────────────────────────────
export default function TransfersPage() {
  const params = useParams();
  const lang = (params?.lang as string) || "es";

  const [transfers, setTransfers] = useState<Transfer[]>([]);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState<string | null>(null);
  const [filtro, setFiltro]       = useState("todos");

  // Edit state
  const [editTarget, setEditTarget]   = useState<Transfer | null>(null);
  const [editForm, setEditForm]       = useState(emptyEditForm);
  const [saving, setSaving]           = useState(false);
  const [saveError, setSaveError]     = useState<string | null>(null);

  // Delete state
  const [deleteTarget, setDeleteTarget] = useState<Transfer | null>(null);
  const [deleting, setDeleting]         = useState(false);

  const fetchTransfers = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const endpoint = filtro !== "todos"
        ? `ui/transfers/?estado=${filtro}`
        : `ui/transfers/`;
      const res = await api.get(endpoint);
      const raw = res.data;
      const list: Transfer[] = Array.isArray(raw)
        ? raw
        : Array.isArray(raw?.transfers)
        ? raw.transfers
        : Array.isArray(raw?.results)
        ? raw.results
        : [];
      setTransfers(list);
    } catch (e: unknown) {
      const msg = (e as { message?: string })?.message ?? "Error al cargar transfers";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [filtro]);

  useEffect(() => { fetchTransfers(); }, [fetchTransfers]);

  const openEdit = (t: Transfer) => {
    setEditForm({
      legal_context: t.legal_context ?? "intracompany",
      ownership_changes: t.ownership_changes,
      customs_required: t.customs_required,
      notes: t.notes ?? "",
      from_node: nodeId(t.from_node),
      to_node: nodeId(t.to_node),
    });
    setSaveError(null);
    setEditTarget(t);
  };

  const handleSave = async () => {
    if (!editTarget) return;
    setSaving(true);
    setSaveError(null);
    try {
      await api.patch(`/transfers/${editTarget.transfer_id}/edit/`, editForm);
      setEditTarget(null);
      await fetchTransfers();
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: Record<string, unknown> } };
      const errData = axiosErr?.response?.data;
      const msg = errData
        ? Object.entries(errData).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(", ") : v}`).join(" | ")
        : "Error al guardar el transfer.";
      setSaveError(msg);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await api.delete(`/transfers/${deleteTarget.transfer_id}/delete/`);
      setDeleteTarget(null);
      await fetchTransfers();
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      setError(axiosErr?.response?.data?.detail ?? "Error al eliminar transfer.");
      setDeleteTarget(null);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-display font-bold text-navy">Transfers</h1>
          <p className="text-sm text-text-secondary mt-0.5">Movimientos de mercancía entre nodos.</p>
        </div>
        <Link
          href={`/${lang}/transfers/nuevo`}
          className="inline-flex items-center gap-2 px-4 py-2 bg-navy text-white rounded-xl text-sm font-medium hover:bg-navy-dark transition-colors"
        >
          <Plus size={16} /> Nuevo transfer
        </Link>
      </div>

      {/* Filter pills */}
      <div className="flex flex-wrap gap-2">
        {FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => setFiltro(f)}
            className={cn(
              "px-3 py-1 rounded-full text-xs font-semibold transition-colors",
              filtro === f
                ? "bg-navy text-white"
                : "bg-white border border-border text-text-secondary hover:border-navy"
            )}
          >
            {f === "todos" ? "Todos" : (STATUS_CONFIG[f]?.label ?? f)}
          </button>
        ))}
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-coral-soft/20 border border-coral/30 text-sm text-coral">{error}</div>
      )}

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm border border-border">
        {loading ? (
          <div className="p-12 text-center text-text-secondary text-sm">Cargando transfers…</div>
        ) : transfers.length === 0 ? (
          <div className="p-12 text-center">
            <ArrowLeftRight size={40} className="mx-auto text-text-secondary opacity-40 mb-3" />
            <p className="text-text-secondary text-sm">Sin transfers registrados.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  {["ID Transfer", "Origen → Destino", "Contexto Legal", "Aduana", "Fecha", "Estado", "Acciones"].map((h) => (
                    <th key={h} className="text-left px-6 py-3 text-xs font-semibold uppercase tracking-[0.5px] text-text-secondary">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {transfers.map((t) => (
                  <tr key={t.transfer_id} className="hover:bg-bg transition-colors">
                    <td className="px-6 py-4 font-mono text-xs font-medium text-navy">
                      <Link href={`/${lang}/transfers/${t.transfer_id}`} className="hover:underline">
                        {t.transfer_id}
                      </Link>
                    </td>
                    <td className="px-6 py-4 text-text-secondary">
                      {nodeName(t.from_node)} → {nodeName(t.to_node)}
                    </td>
                    <td className="px-6 py-4 text-text-secondary capitalize">{t.legal_context ?? "—"}</td>
                    <td className="px-6 py-4">
                      {t.customs_required ? (
                        <span className="text-xs text-[#B45309] bg-[#FFF7ED] px-2 py-0.5 rounded-full font-semibold">Sí</span>
                      ) : (
                        <span className="text-xs text-text-secondary">No</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-text-secondary text-xs">
                      {t.created_at ? new Date(t.created_at).toLocaleDateString("es-CO") : "—"}
                    </td>
                    <td className="px-6 py-4"><StatusBadge status={t.status} /></td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-1">
                        <Link href={`/${lang}/transfers/${t.transfer_id}`} className="text-navy hover:text-mint transition-colors p-1">
                          <ChevronRight size={16} />
                        </Link>
                        {(t.status === "planned" || t.status === "approved") && (
                          <button
                            className="btn btn-sm btn-ghost p-1"
                            onClick={() => openEdit(t)}
                            aria-label="Editar transfer"
                          >
                            <Pencil size={14} />
                          </button>
                        )}
                        {t.status === "planned" && (
                          <button
                            className="btn btn-sm btn-danger-outline p-1"
                            onClick={() => setDeleteTarget(t)}
                            aria-label="Eliminar transfer"
                          >
                            <Trash2 size={14} />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ─── Edit Modal ─── */}
      <FormModal
        open={!!editTarget}
        title="Editar transfer"
        titleId="transfer-edit-title"
        onClose={() => setEditTarget(null)}
        footer={
          <>
            <button className="btn btn-md btn-secondary" onClick={() => setEditTarget(null)}>Cancelar</button>
            <button className="btn btn-md btn-primary" onClick={handleSave} disabled={saving}>
              {saving ? "Guardando..." : "Guardar cambios"}
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
          <label className="th-label block mb-1">Contexto legal</label>
          <select className="input" value={editForm.legal_context} onChange={(e) => setEditForm({ ...editForm, legal_context: e.target.value })}>
            <option value="intracompany">Intracompany</option>
            <option value="intercompany">Intercompany</option>
            <option value="external">External</option>
          </select>
        </div>
        <div>
          <label className="th-label block mb-1">Nodo origen (UUID)</label>
          <input type="text" className="input" placeholder="UUID del nodo" value={editForm.from_node} onChange={(e) => setEditForm({ ...editForm, from_node: e.target.value })} />
        </div>
        <div>
          <label className="th-label block mb-1">Nodo destino (UUID)</label>
          <input type="text" className="input" placeholder="UUID del nodo" value={editForm.to_node} onChange={(e) => setEditForm({ ...editForm, to_node: e.target.value })} />
        </div>
        <div className="flex items-center gap-3">
          <input id="ownership_changes" type="checkbox" className="w-4 h-4 rounded"
            checked={editForm.ownership_changes}
            onChange={(e) => setEditForm({ ...editForm, ownership_changes: e.target.checked })}
          />
          <label htmlFor="ownership_changes" className="th-label cursor-pointer">Cambio de propiedad</label>
        </div>
        <div className="flex items-center gap-3">
          <input id="customs_required" type="checkbox" className="w-4 h-4 rounded"
            checked={editForm.customs_required}
            onChange={(e) => setEditForm({ ...editForm, customs_required: e.target.checked })}
          />
          <label htmlFor="customs_required" className="th-label cursor-pointer">Requiere aduana</label>
        </div>
        <div>
          <label className="th-label block mb-1">Notas</label>
          <textarea className="input" rows={3} placeholder="Notas internas..."
            value={editForm.notes}
            onChange={(e) => setEditForm({ ...editForm, notes: e.target.value })}
          />
        </div>
      </FormModal>

      {/* ─── Delete Dialog ─── */}
      <ConfirmDialog
        open={!!deleteTarget}
        title="Eliminar transfer"
        message={`¿Seguro que deseas eliminar el transfer ${deleteTarget?.transfer_id}? Solo se pueden eliminar transfers en estado 'Planeado'.`}
        confirmLabel="Eliminar transfer"
        variant="danger"
        loading={deleting}
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}
