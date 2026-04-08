"use client";

/**
 * S25-11 — DeferredPricePanel: Toggle y display precio diferido.
 * CEO: puede editar deferred_total_price y togglear deferred_visible.
 * Validación inline según M1-R6 del spec:
 *   1. null → deferred_visible se auto-corrige a false (no error)
 *   2. deferred_visible=true sin precio → 400 duro (mostrar error)
 *   3. Nunca auto-corrección silenciosa ante contradicción explícita
 */

import { useState } from "react";
import { DollarSign, Eye, EyeOff, Edit3, Check, X, AlertTriangle } from "lucide-react";
import api from "@/lib/api";
import toast from "react-hot-toast";
import { cn } from "@/lib/utils";

interface Props {
  expedienteId: string;
  /** Precio diferido actual (null si no está definido) */
  deferredTotalPrice?: number | null;
  /** Si el precio es visible para el cliente */
  deferredVisible?: boolean;
  /** Solo CEO puede editar */
  isCeo?: boolean;
  /** Callback para refrescar el estado padre */
  onUpdate?: () => void;
}

const fmt = (n: number) =>
  `$${n.toLocaleString("es-CR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

export default function DeferredPricePanel({
  expedienteId,
  deferredTotalPrice,
  deferredVisible = false,
  isCeo = false,
  onUpdate,
}: Props) {
  const [editing, setEditing] = useState(false);
  const [priceInput, setPriceInput] = useState(
    deferredTotalPrice != null ? String(deferredTotalPrice) : ""
  );
  const [visibleInput, setVisibleInput] = useState(deferredVisible);
  const [saving, setSaving] = useState(false);

  const hasPrice = deferredTotalPrice != null;

  const handleSave = async () => {
    const isNullPrice = priceInput.trim() === "" || priceInput === "null";
    const resolvedPrice = isNullPrice ? null : parseFloat(priceInput);

    // Validación frontend M1-R6 paso 2: visible=true sin precio → error duro
    if (visibleInput && (isNullPrice || resolvedPrice === null)) {
      toast.error("No puedes activar 'visible al cliente' sin definir un precio diferido.");
      return;
    }

    // Si precio negativo → error
    if (!isNullPrice && resolvedPrice !== null && resolvedPrice < 0) {
      toast.error("El precio diferido no puede ser negativo.");
      return;
    }

    setSaving(true);
    try {
      const body: Record<string, unknown> = {
        deferred_total_price: resolvedPrice,
        deferred_visible: isNullPrice ? false : visibleInput, // auto-correct si null
      };
      await api.patch(`expedientes/${expedienteId}/deferred-price/`, body);
      toast.success("Precio diferido actualizado");
      setEditing(false);
      onUpdate?.();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { error?: string; detail?: string } } };
      toast.error(
        e.response?.data?.error ??
          e.response?.data?.detail ??
          "Error al actualizar precio diferido"
      );
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setEditing(false);
    setPriceInput(deferredTotalPrice != null ? String(deferredTotalPrice) : "");
    setVisibleInput(deferredVisible);
  };

  // Toggle visible sin editar precio (requiere que ya haya precio)
  const handleToggleVisible = async () => {
    if (!hasPrice && !deferredVisible) {
      toast.error("Primero define un precio diferido antes de hacerlo visible.");
      return;
    }
    setSaving(true);
    try {
      await api.patch(`expedientes/${expedienteId}/deferred-price/`, {
        deferred_visible: !deferredVisible,
      });
      toast.success(
        !deferredVisible ? "Precio visible para el cliente" : "Precio ocultado al cliente"
      );
      onUpdate?.();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { error?: string } } };
      toast.error(e.response?.data?.error ?? "Error al cambiar visibilidad");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      className={cn(
        "rounded-xl border p-4 space-y-3 transition-colors",
        hasPrice
          ? deferredVisible
            ? "bg-indigo-50 border-indigo-200"
            : "bg-[var(--color-bg-alt)] border-[var(--color-border)]"
          : "bg-[var(--color-bg-alt)] border-dashed border-[var(--color-border)]"
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <DollarSign
            className={cn(
              "w-4 h-4",
              hasPrice ? "text-indigo-600" : "text-[var(--color-text-tertiary)]"
            )}
          />
          <span className="text-sm font-semibold text-[var(--color-text-primary)]">
            Precio diferido
          </span>
          {deferredVisible && hasPrice && (
            <span className="text-[10px] bg-indigo-100 text-indigo-700 border border-indigo-200 rounded-full px-2 py-0.5 font-semibold uppercase tracking-wider">
              Visible al cliente
            </span>
          )}
        </div>

        {isCeo && !editing && (
          <div className="flex items-center gap-1.5">
            {/* Toggle visibility button */}
            {hasPrice && (
              <button
                onClick={handleToggleVisible}
                disabled={saving}
                title={deferredVisible ? "Ocultar al cliente" : "Mostrar al cliente"}
                className={cn(
                  "p-1.5 rounded-lg border transition-colors text-xs flex items-center gap-1",
                  deferredVisible
                    ? "bg-indigo-50 text-indigo-600 border-indigo-200 hover:bg-indigo-100"
                    : "bg-[var(--color-bg)] text-[var(--color-text-tertiary)] border-[var(--color-border)] hover:bg-[var(--color-bg-alt)]"
                )}
              >
                {saving ? (
                  <span className="w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin" />
                ) : deferredVisible ? (
                  <Eye className="w-3.5 h-3.5" />
                ) : (
                  <EyeOff className="w-3.5 h-3.5" />
                )}
              </button>
            )}
            {/* Edit button */}
            <button
              onClick={() => setEditing(true)}
              className="p-1.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] text-[var(--color-text-tertiary)] hover:bg-[var(--color-bg-alt)] transition-colors"
              title="Editar precio diferido"
            >
              <Edit3 className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
      </div>

      {/* Display (no edit mode) */}
      {!editing && (
        <div>
          {hasPrice ? (
            <p className="text-2xl font-bold tabular-nums text-[var(--color-text-primary)]">
              {fmt(deferredTotalPrice!)}
            </p>
          ) : (
            <p className="text-sm text-[var(--color-text-tertiary)] italic">
              {isCeo
                ? "Sin precio diferido definido. Haz clic en editar para agregar uno."
                : "Precio a confirmar por el equipo comercial."}
            </p>
          )}
        </div>
      )}

      {/* Edit mode (CEO only) */}
      {editing && isCeo && (
        <div className="space-y-3">
          <div>
            <label className="text-xs font-medium text-[var(--color-text-secondary)] mb-1 block">
              Precio diferido (USD)
            </label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-text-tertiary)] text-sm">
                $
              </span>
              <input
                type="number"
                step="0.01"
                min="0"
                value={priceInput}
                onChange={(e) => setPriceInput(e.target.value)}
                placeholder="0.00  (vacío = sin precio)"
                className="w-full pl-7 pr-3 py-2 border border-[var(--color-border)] rounded-lg text-sm bg-[var(--color-bg)] focus:outline-none focus:ring-2 focus:ring-indigo-400/30 focus:border-indigo-400"
              />
            </div>
            <p className="text-[10px] text-[var(--color-text-tertiary)] mt-1">
              Deja vacío para quitar el precio diferido.
            </p>
          </div>

          {/* Visible toggle */}
          <label className="flex items-center gap-2.5 cursor-pointer group">
            <div
              className={cn(
                "relative w-9 h-5 rounded-full transition-colors border",
                visibleInput
                  ? "bg-indigo-500 border-indigo-500"
                  : "bg-gray-200 border-gray-300"
              )}
              onClick={() => setVisibleInput((v) => !v)}
            >
              <span
                className={cn(
                  "absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform",
                  visibleInput && "translate-x-4"
                )}
              />
            </div>
            <span className="text-sm text-[var(--color-text-secondary)]">
              Visible al cliente
            </span>
            {visibleInput && !priceInput.trim() && (
              <span className="flex items-center gap-1 text-xs text-amber-600">
                <AlertTriangle className="w-3 h-3" />
                Requiere precio
              </span>
            )}
          </label>

          {/* Actions */}
          <div className="flex justify-end gap-2 pt-1">
            <button
              onClick={handleCancel}
              disabled={saving}
              className="flex items-center gap-1 px-3 py-1.5 text-xs border border-[var(--color-border)] rounded-lg text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-alt)] transition-colors"
            >
              <X className="w-3 h-3" />
              Cancelar
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex items-center gap-1 px-3 py-1.5 text-xs bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
            >
              {saving ? (
                <span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <Check className="w-3 h-3" />
              )}
              Guardar
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
