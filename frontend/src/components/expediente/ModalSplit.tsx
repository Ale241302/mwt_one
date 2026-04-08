"use client";

import { useState } from "react";
import { X, Scissors, Search, AlertTriangle, ArrowUpDown } from "lucide-react";
import api from "@/lib/api";
import toast from "react-hot-toast";

interface ProductLine {
  id: number | string;
  product_master_name?: string;
  brand_sku_code?: string;
  quantity?: number;
  [key: string]: unknown;
}

interface ExpedienteResult {
  id: number | string;
  ref_number?: string;
  custom_ref?: string;
  status: string;
  client_name?: string;
}

interface Props {
  expedienteId: number | string;
  productLines: ProductLine[];
  /** Si el expediente ya tiene parent, invert_parent no está disponible */
  hasParent?: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export default function ModalSplit({ expedienteId, productLines, hasParent = false, onClose, onSuccess }: Props) {
  const [selectedIds, setSelectedIds] = useState<Set<number | string>>(new Set());
  const [destMode, setDestMode] = useState<"new" | "existing">("new");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<ExpedienteResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [destExpediente, setDestExpediente] = useState<ExpedienteResult | null>(null);
  const [submitting, setSubmitting] = useState(false);
  /** S25-12: invert_parent — el nuevo expediente pasa a ser el padre */
  const [invertParent, setInvertParent] = useState(false);

  const toggleLine = (id: number | string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const isValidSelection =
    selectedIds.size >= 1 && selectedIds.size < productLines.length;

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setSearching(true);
    try {
      const res = await api.get(`expedientes/?search=${encodeURIComponent(searchQuery)}`);
      const list: ExpedienteResult[] = Array.isArray(res.data) ? res.data : res.data?.results ?? [];
      setSearchResults(list.filter((e) => String(e.id) !== String(expedienteId)));
    } catch {
      toast.error("Error al buscar expedientes");
    } finally {
      setSearching(false);
    }
  };

  const handleSplit = async () => {
    if (!isValidSelection) return;
    if (destMode === "existing" && !destExpediente) {
      toast.error("Seleccioná un expediente destino");
      return;
    }
    setSubmitting(true);
    try {
      const payload: Record<string, unknown> = {
        product_line_ids: Array.from(selectedIds),
        invert_parent: invertParent,
      };
      if (destMode === "existing" && destExpediente) {
        payload.destino = destExpediente.id;
      }
      await api.post(`expedientes/${expedienteId}/separate-products/`, payload);
      toast.success("Líneas separadas correctamente");
      onSuccess();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      toast.error(e.response?.data?.detail ?? "Error al separar líneas");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <div className="bg-[var(--color-surface)] rounded-2xl border border-[var(--color-border)] shadow-xl w-full max-w-lg max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--color-border)] flex-shrink-0">
          <div className="flex items-center gap-2">
            <Scissors className="w-5 h-5 text-[var(--color-navy)]" />
            <h2 className="text-base font-semibold text-[var(--color-text-primary)]">Separar productos</h2>
          </div>
          <button onClick={onClose} className="p-1.5 rounded hover:bg-[var(--color-bg-alt)] text-[var(--color-text-tertiary)] transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5">
          {/* Product line checkboxes */}
          <div>
            <p className="text-sm text-[var(--color-text-secondary)] mb-3">
              Seleccioná las líneas a separar <span className="text-[var(--color-text-tertiary)]">(mínimo 1, no todas)</span>:
            </p>
            <div className="space-y-2">
              {productLines.map((line) => (
                <label
                  key={String(line.id)}
                  className={`flex items-center gap-3 border rounded-xl px-4 py-3 cursor-pointer transition-colors ${
                    selectedIds.has(line.id)
                      ? "border-[var(--color-navy)] bg-[var(--color-navy)]/5"
                      : "border-[var(--color-border)] hover:bg-[var(--color-bg-alt)]"
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={selectedIds.has(line.id)}
                    onChange={() => toggleLine(line.id)}
                    className="accent-[var(--color-navy)] w-4 h-4 flex-shrink-0"
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-[var(--color-text-primary)] truncate">
                      {line.product_master_name ?? String(line.id)}
                    </p>
                    {line.brand_sku_code && (
                      <p className="text-xs text-[var(--color-text-tertiary)]">{line.brand_sku_code}</p>
                    )}
                  </div>
                  {line.quantity !== undefined && (
                    <span className="text-xs text-[var(--color-text-tertiary)] flex-shrink-0">x{line.quantity}</span>
                  )}
                </label>
              ))}
            </div>

            {selectedIds.size >= productLines.length && (
              <div className="flex items-center gap-2 mt-2 text-xs text-[var(--color-coral)]">
                <AlertTriangle className="w-3.5 h-3.5" />
                No podés separar todas las líneas.
              </div>
            )}
          </div>

          {/* S25-12: Invert parent */}
          {destMode === "new" && (
            <div className="space-y-2">
              <label
                className={`flex items-start gap-3 border rounded-xl px-4 py-3 cursor-pointer transition-colors ${
                  invertParent
                    ? "border-violet-400 bg-violet-50"
                    : "border-[var(--color-border)] hover:bg-[var(--color-bg-alt)]"
                } ${hasParent ? "opacity-50 cursor-not-allowed" : ""}`}
              >
                <input
                  type="checkbox"
                  checked={invertParent}
                  disabled={hasParent}
                  onChange={() => !hasParent && setInvertParent((v) => !v)}
                  className="accent-violet-600 w-4 h-4 flex-shrink-0 mt-0.5"
                />
                <div className="flex-1">
                  <div className="flex items-center gap-1.5">
                    <ArrowUpDown className="w-3.5 h-3.5 text-violet-500" />
                    <p className="text-sm font-medium text-[var(--color-text-primary)]">
                      Invertir jerarquía
                    </p>
                  </div>
                  <p className="text-xs text-[var(--color-text-tertiary)] mt-0.5">
                    El nuevo expediente creado pasá a ser el <strong>padre</strong> y el
                    actual pasa a ser hijo.
                  </p>
                  {hasParent && (
                    <p className="text-xs text-amber-600 mt-1 flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" />
                      No disponible: este expediente ya tiene un padre.
                    </p>
                  )}
                </div>
              </label>
            </div>
          )}

          {/* Destination */}
          <div>
            <p className="text-sm font-semibold text-[var(--color-text-primary)] mb-2">Destino:</p>
            <div className="flex gap-3">
              {(["new", "existing"] as const).map((mode) => (
                <label key={mode} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="destMode"
                    value={mode}
                    checked={destMode === mode}
                    onChange={() => setDestMode(mode)}
                    className="accent-[var(--color-navy)]"
                  />
                  <span className="text-sm text-[var(--color-text-secondary)]">
                    {mode === "new" ? "Crear nuevo expediente" : "Mover a existente"}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Existing expediente search */}
          {destMode === "existing" && (
            <div className="space-y-3">
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[var(--color-text-tertiary)]" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                    placeholder="Ref o cliente..."
                    className="w-full pl-8 pr-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-navy)]/30"
                  />
                </div>
                <button
                  type="button"
                  onClick={handleSearch}
                  disabled={searching}
                  className="px-4 py-2 bg-[var(--color-navy)] text-white text-sm rounded-lg hover:opacity-80 disabled:opacity-50 transition-opacity"
                >
                  {searching ? <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> : "Buscar"}
                </button>
              </div>

              {searchResults.length > 0 && (
                <ul className="border border-[var(--color-border)] rounded-xl overflow-hidden">
                  {searchResults.map((r) => (
                    <li
                      key={r.id}
                      onClick={() => setDestExpediente(r)}
                      className={`px-4 py-3 cursor-pointer border-b last:border-b-0 border-[var(--color-border)] transition-colors ${
                        String(destExpediente?.id) === String(r.id)
                          ? "bg-[var(--color-navy)]/5 border-l-2 border-l-[var(--color-navy)]"
                          : "hover:bg-[var(--color-bg-alt)]"
                      }`}
                    >
                      <p className="text-sm font-mono font-medium text-[var(--color-navy)]">{r.ref_number ?? r.custom_ref ?? `#${r.id}`}</p>
                      <p className="text-xs text-[var(--color-text-tertiary)]">{r.client_name} · {r.status}</p>
                    </li>
                  ))}
                </ul>
              )}
              {destExpediente && (
                <p className="text-xs text-[var(--color-navy)] font-medium">
                  ✓ Destino: {destExpediente.ref_number ?? destExpediente.custom_ref ?? `#${destExpediente.id}`}
                </p>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-[var(--color-border)] flex justify-end gap-2 flex-shrink-0">
          <button onClick={onClose} className="px-4 py-2 border border-[var(--color-border)] text-[var(--color-text-secondary)] text-sm rounded-lg hover:bg-[var(--color-bg-alt)] transition-colors">
            Cancelar
          </button>
          <button
            type="button"
            onClick={handleSplit}
            disabled={submitting || !isValidSelection}
            className="flex items-center gap-1.5 px-4 py-2 bg-[var(--color-navy)] text-white text-sm rounded-lg hover:opacity-80 disabled:opacity-50 transition-opacity"
          >
            {submitting ? <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> : <Scissors className="w-4 h-4" />}
            Separar ({selectedIds.size} línea{selectedIds.size !== 1 ? "s" : ""})
          </button>
        </div>
      </div>
    </div>
  );
}
