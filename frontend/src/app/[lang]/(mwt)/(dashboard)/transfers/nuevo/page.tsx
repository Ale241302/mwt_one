"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import api from "@/lib/api";
import toast from "react-hot-toast";
import { ArrowLeft, Plus, Trash2 } from "lucide-react";

// ─── Types ────────────────────────────────────────────────────────────────────
interface NodeOption {
  node_id: string;
  name: string;
  node_type: string;
  legal_entity_name: string;
}

interface LineItem {
  sku: string;
  quantity_dispatched: number;
}

const LEGAL_CONTEXT_OPTIONS = [
  { value: "internal", label: "Interno" },
  { value: "nationalization", label: "Nacionalización" },
  { value: "reexport", label: "Re-exportación" },
  { value: "distribution", label: "Distribución" },
  { value: "consignment", label: "Consignación" },
];

// ─── Component ────────────────────────────────────────────────────────────────
export default function NuevoTransferPage() {
  const router = useRouter();
  const params = useParams();
  const lang = (params?.lang as string) || "es";

  const [nodes, setNodes] = useState<NodeOption[]>([]);
  const [nodesLoading, setNodesLoading] = useState(true);
  const [nodesError, setNodesError] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [form, setForm] = useState({
    from_node: "",
    to_node: "",
    legal_context: "",
    source_expediente: "",
  });

  const [lines, setLines] = useState<LineItem[]>([{ sku: "", quantity_dispatched: 1 }]);

  // ── Load nodes ──────────────────────────────────────────────────────────────
  useEffect(() => {
    const fetchNodes = async () => {
      try {
        setNodesLoading(true);
        setNodesError(false);
        const res = await api.get("ui/transfers/");
        const data = res.data;
        // El backend ui/transfers/ devuelve paginado: results: { transfers, nodes }
        const nodesList = Array.isArray(data.nodes)
          ? data.nodes
          : Array.isArray(data?.results?.nodes)
          ? data.results.nodes
          : [];
        setNodes(nodesList);
      } catch {
        setNodesError(true);
        toast.error("No se pudieron cargar los nodos");
      } finally {
        setNodesLoading(false);
      }
    };
    fetchNodes();
  }, []);

  // ── Form handlers ────────────────────────────────────────────────────────────
  const handleChange = (
    e: React.ChangeEvent<HTMLSelectElement | HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleLineChange = (idx: number, field: keyof LineItem, value: string | number) => {
    setLines((prev) =>
      prev.map((l, i) => (i === idx ? { ...l, [field]: field === "quantity_dispatched" ? Number(value) : value } : l))
    );
  };

  const addLine = () => setLines((prev) => [...prev, { sku: "", quantity_dispatched: 1 }]);

  const removeLine = (idx: number) => {
    if (lines.length === 1) return;
    setLines((prev) => prev.filter((_, i) => i !== idx));
  };

  // ── Submit ──────────────────────────────────────────────────────────────────
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!form.from_node || !form.to_node || !form.legal_context) {
      toast.error("Completa todos los campos obligatorios");
      return;
    }
    if (form.from_node === form.to_node) {
      toast.error("El nodo origen y destino no pueden ser el mismo");
      return;
    }
    const invalidLines = lines.some((l) => !l.sku.trim() || l.quantity_dispatched < 1);
    if (invalidLines) {
      toast.error("Cada línea debe tener SKU y cantidad válida");
      return;
    }

    setSubmitting(true);
    try {
      const payload: Record<string, unknown> = {
        from_node: form.from_node,
        to_node: form.to_node,
        legal_context: form.legal_context,
        items: lines.map((l) => ({ sku: l.sku.trim(), quantity_dispatched: l.quantity_dispatched })),
      };
      if (form.source_expediente.trim()) {
        payload.source_expediente = form.source_expediente.trim();
      }

      const res = await api.post("transfers/create/", payload);

      if (res.status === 201) {
        toast.success("Transfer creado exitosamente");
        const newId = res.data?.transfer_id || res.data?.id;
        router.push(newId ? `/${lang}/transfers/${newId}` : `/${lang}/transfers`);
      }
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string; message?: string } } };
      const msg =
        e.response?.data?.detail ||
        e.response?.data?.message ||
        "Error al crear el transfer";
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  // ── Render ──────────────────────────────────────────────────────────────────
  const inputClass =
    "w-full bg-bg border border-border rounded-lg px-3 py-2.5 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-navy/30";
  const labelClass =
    "block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5";

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <button
        onClick={() => router.back()}
        className="text-sm text-text-secondary hover:text-navy flex items-center transition-colors"
      >
        <ArrowLeft className="w-4 h-4 mr-1" /> Volver
      </button>

      <div className="bg-surface rounded-2xl border border-border shadow-sm p-8">
        <h1 className="text-2xl font-display font-bold text-text-primary mb-1">Nuevo Transfer</h1>
        <p className="text-sm text-text-tertiary mb-8">Registra un movimiento de mercancía entre nodos.</p>

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Nodo Origen */}
          <div>
            <label className={labelClass}>Nodo Origen <span className="text-coral">*</span></label>
            {nodesLoading ? (
              <div className="flex items-center gap-2 h-10 px-3 bg-bg-alt border border-border rounded-lg">
                <div className="w-4 h-4 border-2 border-navy border-t-transparent rounded-full animate-spin" />
                <span className="text-sm text-text-tertiary">Cargando nodos...</span>
              </div>
            ) : nodesError ? (
              <div className="text-sm text-coral px-3 py-2 bg-red-50 border border-red-200 rounded-lg">
                Error al cargar nodos.{" "}
                <button type="button" className="underline" onClick={() => window.location.reload()}>Recargar</button>
              </div>
            ) : (
              <select name="from_node" value={form.from_node} onChange={handleChange} required className={inputClass}>
                <option value="">Seleccionar nodo origen...</option>
                {nodes.map((n) => (
                  <option key={n.node_id} value={n.node_id}>
                    {n.name} — {n.legal_entity_name} ({n.node_type})
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Nodo Destino */}
          <div>
            <label className={labelClass}>Nodo Destino <span className="text-coral">*</span></label>
            <select name="to_node" value={form.to_node} onChange={handleChange} required className={inputClass} disabled={nodesLoading}>
              <option value="">Seleccionar nodo destino...</option>
              {nodes
                .filter((n) => n.node_id !== form.from_node)
                .map((n) => (
                  <option key={n.node_id} value={n.node_id}>
                    {n.name} — {n.legal_entity_name} ({n.node_type})
                  </option>
                ))}
            </select>
          </div>

          {/* Contexto Legal */}
          <div>
            <label className={labelClass}>Contexto Legal <span className="text-coral">*</span></label>
            <select name="legal_context" value={form.legal_context} onChange={handleChange} required className={inputClass}>
              <option value="">Seleccionar contexto...</option>
              {LEGAL_CONTEXT_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>

          {/* Expediente fuente (opcional) */}
          <div>
            <label className={labelClass}>
              Expediente Asociado{" "}
              <span className="text-text-tertiary font-normal">(opcional)</span>
            </label>
            <input
              type="text"
              name="source_expediente"
              value={form.source_expediente}
              onChange={handleChange}
              placeholder="Ej: EXP-20250317-001"
              className={inputClass}
            />
          </div>

          {/* Líneas / Items */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className={labelClass + " mb-0"}>Líneas de Productos <span className="text-coral">*</span></label>
              <button
                type="button"
                onClick={addLine}
                className="text-xs text-navy hover:text-mint font-medium flex items-center gap-1 transition-colors"
              >
                <Plus size={13} /> Agregar línea
              </button>
            </div>

            <div className="space-y-2">
              {lines.map((line, idx) => (
                <div key={idx} className="flex gap-2 items-center">
                  <input
                    type="text"
                    value={line.sku}
                    onChange={(e) => handleLineChange(idx, "sku", e.target.value)}
                    placeholder="SKU"
                    required
                    className="flex-1 bg-bg border border-border rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-navy/30"
                  />
                  <input
                    type="number"
                    value={line.quantity_dispatched}
                    onChange={(e) => handleLineChange(idx, "quantity_dispatched", e.target.value)}
                    min={1}
                    required
                    className="w-24 bg-bg border border-border rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-navy/30"
                  />
                  <button
                    type="button"
                    onClick={() => removeLine(idx)}
                    disabled={lines.length === 1}
                    className="text-text-tertiary hover:text-coral transition-colors disabled:opacity-30"
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
              ))}
              <p className="text-xs text-text-tertiary mt-1">SKU · Cantidad despachada</p>
            </div>
          </div>

          {/* Submit */}
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={() => router.back()}
              className="bg-surface border border-border text-text-secondary hover:bg-bg-alt px-4 py-2 rounded-lg text-sm font-medium transition-all"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={submitting || nodesLoading}
              className="bg-navy hover:bg-slate-800 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all shadow-sm active:scale-95 flex items-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {submitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Creando...
                </>
              ) : (
                <><Plus size={16} /> Crear Transfer</>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
