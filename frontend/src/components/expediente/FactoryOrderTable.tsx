"use client";

import { useState } from "react";
import { Plus, Pencil, Trash2, Check, X, AlertTriangle } from "lucide-react";
import api from "@/lib/api";
import toast from "react-hot-toast";
import UrlField from "@/components/UrlField";
import { useOperadoPor, OperadoPor } from "@/hooks/useOperadoPor";

export interface FactoryOrder {
  id: number;
  supplier_name: string;
  // CLIENTE fields
  url_proforma_client?: string | null;
  url_orden_compra_client?: string | null;
  // MWT fields
  url_proforma_mwt?: string | null;
  tracking_fabrica?: string | null;
  // DESPACHO fields
  url_packing_list_client?: string | null;
  url_bl_client?: string | null;
  url_packing_list_mwt?: string | null;
  url_bl_mwt?: string | null;
  [key: string]: unknown;
}

interface Props {
  expedienteId: number | string;
  factoryOrders: FactoryOrder[];
  operadoPor: OperadoPor;
  onRefresh: () => void;
  readOnly?: boolean;
  showDespachoFields?: boolean;
}

export default function FactoryOrderTable({
  expedienteId,
  factoryOrders,
  operadoPor,
  onRefresh,
  readOnly = false,
  showDespachoFields = false,
}: Props) {
  const { showClientFields, showMwtFields } = useOperadoPor(operadoPor);
  const [creating, setCreating] = useState(false);
  const [newSupplier, setNewSupplier] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editingSupplier, setEditingSupplier] = useState("");
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const BASE = `expedientes/${expedienteId}/factory-orders/`;

  const handleCreate = async () => {
    if (!newSupplier.trim()) return;
    setSubmitting(true);
    try {
      await api.post(BASE, { supplier_name: newSupplier.trim() });
      toast.success("Fabricante creado");
      setNewSupplier("");
      setCreating(false);
      onRefresh();
    } catch {
      toast.error("Error al crear fabricante");
    } finally {
      setSubmitting(false);
    }
  };

  const handleUpdate = async (id: number, data: Partial<FactoryOrder>) => {
    setSubmitting(true);
    try {
      await api.patch(`${BASE}${id}/`, data);
      toast.success("Actualizado");
      onRefresh();
    } catch {
      toast.error("Error al actualizar");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: number) => {
    setSubmitting(true);
    try {
      await api.delete(`${BASE}${id}/`);
      toast.success("Fabricante eliminado");
      setDeletingId(null);
      onRefresh();
    } catch {
      toast.error("Error al eliminar");
    } finally {
      setSubmitting(false);
    }
  };

  const handleEditStart = (fo: FactoryOrder) => {
    setEditingId(fo.id);
    setEditingSupplier(fo.supplier_name);
  };

  const handleEditConfirm = async () => {
    if (editingId === null) return;
    await handleUpdate(editingId, { supplier_name: editingSupplier });
    setEditingId(null);
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">Fabricantes</h3>
        {!readOnly && (
          <button
            type="button"
            onClick={() => setCreating(true)}
            className="flex items-center gap-1.5 text-xs bg-[var(--color-navy)] text-white rounded-lg px-3 py-1.5 hover:opacity-80 transition-opacity"
          >
            <Plus className="w-3.5 h-3.5" /> Agregar Fabricante
          </button>
        )}
      </div>

      {/* Create row */}
      {creating && (
        <div className="flex items-center gap-2 bg-[var(--color-bg-alt)] border border-[var(--color-border)] rounded-lg p-3">
          <input
            type="text"
            value={newSupplier}
            onChange={(e) => setNewSupplier(e.target.value)}
            placeholder="Nombre del fabricante"
            className="flex-1 bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm text-[var(--color-text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-navy)]/30"
            autoFocus
            onKeyDown={(e) => {
              if (e.key === "Enter") handleCreate();
              if (e.key === "Escape") setCreating(false);
            }}
          />
          <button
            type="button"
            onClick={handleCreate}
            disabled={submitting}
            className="p-2 rounded bg-[var(--color-navy)] text-white hover:opacity-80 disabled:opacity-50 transition-opacity"
          >
            <Check className="w-4 h-4" />
          </button>
          <button
            type="button"
            onClick={() => setCreating(false)}
            className="p-2 rounded hover:bg-[var(--color-bg)] text-[var(--color-text-tertiary)] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Table */}
      {factoryOrders.length === 0 && !creating ? (
        <p className="text-xs text-[var(--color-text-tertiary)] italic px-1">
          Sin fabricantes registrados.
        </p>
      ) : (
        <div className="border border-[var(--color-border)] rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-[var(--color-bg-alt)]">
              <tr>
                <th className="text-left px-4 py-2.5 text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">Fabricante</th>
                {showClientFields && <th className="text-left px-4 py-2.5 text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">Docs (Cliente)</th>}
                {showMwtFields && <th className="text-left px-4 py-2.5 text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">Docs (MWT)</th>}
                {showDespachoFields && showClientFields && <th className="text-left px-4 py-2.5 text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">Despacho (Cliente)</th>}
                {showDespachoFields && showMwtFields && <th className="text-left px-4 py-2.5 text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">Despacho (MWT)</th>}
                {!readOnly && <th className="px-4 py-2.5" />}
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--color-border)]">
              {factoryOrders.map((fo) => (
                <tr key={fo.id} className="hover:bg-[var(--color-bg-alt)]/50 transition-colors">
                  <td className="px-4 py-3">
                    {editingId === fo.id ? (
                      <div className="flex items-center gap-2">
                        <input
                          type="text"
                          value={editingSupplier}
                          onChange={(e) => setEditingSupplier(e.target.value)}
                          className="flex-1 bg-[var(--color-bg)] border border-[var(--color-border)] rounded px-2 py-1 text-sm focus:outline-none"
                          autoFocus
                          onKeyDown={(e) => {
                            if (e.key === "Enter") handleEditConfirm();
                            if (e.key === "Escape") setEditingId(null);
                          }}
                        />
                        <button type="button" onClick={handleEditConfirm} className="p-1 rounded bg-[var(--color-navy)] text-white"><Check className="w-3 h-3" /></button>
                        <button type="button" onClick={() => setEditingId(null)} className="p-1 rounded hover:bg-[var(--color-bg-alt)] text-[var(--color-text-tertiary)]"><X className="w-3 h-3" /></button>
                      </div>
                    ) : (
                      <span className="text-[var(--color-text-primary)]">{fo.supplier_name}</span>
                    )}
                  </td>

                  {showClientFields && (
                    <td className="px-4 py-3 space-y-2">
                      <UrlField
                        url={fo.url_proforma_client ?? null}
                        label="Proforma"
                        readOnly={readOnly}
                        onUpdate={(url) => handleUpdate(fo.id, { url_proforma_client: url })}
                        onDelete={() => handleUpdate(fo.id, { url_proforma_client: null })}
                      />
                      <UrlField
                        url={fo.url_orden_compra_client ?? null}
                        label="Orden Compra"
                        readOnly={readOnly}
                        onUpdate={(url) => handleUpdate(fo.id, { url_orden_compra_client: url })}
                        onDelete={() => handleUpdate(fo.id, { url_orden_compra_client: null })}
                      />
                    </td>
                  )}

                  {showMwtFields && (
                    <td className="px-4 py-3 space-y-2">
                      <UrlField
                        url={fo.url_proforma_mwt ?? null}
                        label="Proforma MWT"
                        readOnly={readOnly}
                        onUpdate={(url) => handleUpdate(fo.id, { url_proforma_mwt: url })}
                        onDelete={() => handleUpdate(fo.id, { url_proforma_mwt: null })}
                      />
                      <UrlField
                        url={fo.tracking_fabrica ?? null}
                        label="Tracking Fábrica"
                        readOnly={readOnly}
                        onUpdate={(url) => handleUpdate(fo.id, { tracking_fabrica: url })}
                        onDelete={() => handleUpdate(fo.id, { tracking_fabrica: null })}
                      />
                    </td>
                  )}

                  {showDespachoFields && showClientFields && (
                    <td className="px-4 py-3 space-y-2">
                      <UrlField
                        url={fo.url_packing_list_client ?? null}
                        label="Packing List"
                        readOnly={readOnly}
                        onUpdate={(url) => handleUpdate(fo.id, { url_packing_list_client: url })}
                        onDelete={() => handleUpdate(fo.id, { url_packing_list_client: null })}
                      />
                      <UrlField
                        url={fo.url_bl_client ?? null}
                        label="BL"
                        readOnly={readOnly}
                        onUpdate={(url) => handleUpdate(fo.id, { url_bl_client: url })}
                        onDelete={() => handleUpdate(fo.id, { url_bl_client: null })}
                      />
                    </td>
                  )}

                  {showDespachoFields && showMwtFields && (
                    <td className="px-4 py-3 space-y-2">
                      <UrlField
                        url={fo.url_packing_list_mwt ?? null}
                        label="Packing List MWT"
                        readOnly={readOnly}
                        onUpdate={(url) => handleUpdate(fo.id, { url_packing_list_mwt: url })}
                        onDelete={() => handleUpdate(fo.id, { url_packing_list_mwt: null })}
                      />
                      <UrlField
                        url={fo.url_bl_mwt ?? null}
                        label="BL MWT"
                        readOnly={readOnly}
                        onUpdate={(url) => handleUpdate(fo.id, { url_bl_mwt: url })}
                        onDelete={() => handleUpdate(fo.id, { url_bl_mwt: null })}
                      />
                    </td>
                  )}

                  {!readOnly && (
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1.5 justify-end">
                        <button
                          type="button"
                          onClick={() => handleEditStart(fo)}
                          className="p-1.5 rounded hover:bg-[var(--color-bg-alt)] text-[var(--color-text-tertiary)] hover:text-[var(--color-text-primary)] transition-colors"
                        >
                          <Pencil className="w-3.5 h-3.5" />
                        </button>
                        {deletingId === fo.id ? (
                          <div className="flex items-center gap-1 bg-[var(--color-bg-alt)] border border-[var(--color-border)] rounded-lg px-2 py-1">
                            <AlertTriangle className="w-3.5 h-3.5 text-[var(--color-coral)]" />
                            <span className="text-xs text-[var(--color-text-secondary)]">¿Eliminar?</span>
                            <button type="button" onClick={() => handleDelete(fo.id)} className="text-xs text-[var(--color-coral)] font-medium hover:underline">Sí</button>
                            <button type="button" onClick={() => setDeletingId(null)} className="text-xs text-[var(--color-text-tertiary)] hover:underline">No</button>
                          </div>
                        ) : (
                          <button
                            type="button"
                            onClick={() => setDeletingId(fo.id)}
                            className="p-1.5 rounded hover:bg-[var(--color-bg-alt)] text-[var(--color-text-tertiary)] hover:text-[var(--color-coral)] transition-colors"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
