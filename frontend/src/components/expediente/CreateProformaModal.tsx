"use client";

import { useState, useEffect } from "react";
import { AlertCircle, Plus, Minus, Search, X, Package } from "lucide-react";
import api from "@/lib/api";
import FormModal from "@/components/ui/FormModal";
import { BRAND_ALLOWED_MODES, DEFAULT_ALLOWED_MODES } from "@/constants/brand-modes";
import { MODE_LABELS } from "@/constants/mode-labels";

interface Product {
  id: string;
  name: string;
  sku_base: string;
  brand_name: string;
  category: string;
}

interface ProductLine {
  product: Product;
  quantity: number;
  unit_price: number;
}

interface CreateProformaModalProps {
  open: boolean;
  expedienteId: string;
  brandSlug: string;
  /** Legacy: orphan lines from the expediente (still accepted by backend) */
  orphanLines?: any[];
  onClose: () => void;
  onRefresh: () => void;
}

export default function CreateProformaModal({
  open, expedienteId, brandSlug, orphanLines = [], onClose, onRefresh
}: CreateProformaModalProps) {
  const allowedModes = BRAND_ALLOWED_MODES[brandSlug] || DEFAULT_ALLOWED_MODES;

  const [proformaNumber, setProformaNumber] = useState("");
  const [selectedMode, setSelectedMode] = useState(allowedModes[0] || "");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Product catalog state
  const [products, setProducts] = useState<Product[]>([]);
  const [loadingProducts, setLoadingProducts] = useState(false);
  const [search, setSearch] = useState("");
  const [addedLines, setAddedLines] = useState<ProductLine[]>([]);

  // Orphan lines (existing product lines not yet in any proforma)
  const [selectedOrphanIds, setSelectedOrphanIds] = useState<number[]>(
    orphanLines.map((l: any) => l.id)
  );

  useEffect(() => {
    if (!open) return;
    setLoadingProducts(true);
    api.get("/productos/")
      .then(res => {
        const data = res.data;
        setProducts(Array.isArray(data) ? data : Array.isArray(data?.results) ? data.results : []);
      })
      .catch(() => setProducts([]))
      .finally(() => setLoadingProducts(false));
  }, [open]);

  const filtered = products.filter(p =>
    !search ||
    p.name.toLowerCase().includes(search.toLowerCase()) ||
    p.sku_base.toLowerCase().includes(search.toLowerCase())
  );

  const addProduct = (product: Product) => {
    if (addedLines.find(l => l.product.id === product.id)) return;
    setAddedLines(prev => [...prev, { product, quantity: 1, unit_price: 0 }]);
  };

  const removeProduct = (productId: string) => {
    setAddedLines(prev => prev.filter(l => l.product.id !== productId));
  };

  const updateLine = (productId: string, field: "quantity" | "unit_price", value: number) => {
    setAddedLines(prev =>
      prev.map(l => l.product.id === productId ? { ...l, [field]: value } : l)
    );
  };

  const toggleOrphan = (id: number) => {
    setSelectedOrphanIds(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const handleSubmit = async () => {
    if (!proformaNumber.trim()) {
      setError("El número de proforma es requerido");
      return;
    }
    if (addedLines.length === 0 && selectedOrphanIds.length === 0) {
      setError("Debes agregar al menos un producto o línea");
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      await api.post(`/expedientes/${expedienteId}/proformas/`, {
        proforma_number: proformaNumber,
        mode: selectedMode,
        line_ids: selectedOrphanIds,
        new_lines: addedLines.map(l => ({
          product_id: l.product.id,
          quantity: l.quantity,
          unit_price: l.unit_price,
        })),
      });
      onRefresh();
      onClose();
    } catch (err: any) {
      const detail = err?.response?.data?.detail || err?.response?.data?.error || "Error al crear la proforma";
      setError(detail);
    } finally {
      setSubmitting(false);
    }
  };

  if (!open) return null;

  return (
    <FormModal
      open={open}
      onClose={onClose}
      title="Nueva Proforma (C3)"
      size="lg"
      footer={
        <div className="flex justify-end gap-3 p-4">
          <button className="btn btn-secondary" onClick={onClose} disabled={submitting}>
            Cancelar
          </button>
          <button className="btn btn-primary" onClick={handleSubmit} disabled={submitting}>
            {submitting ? "Creando..." : "Crear Proforma"}
          </button>
        </div>
      }
    >
      <div className="space-y-6">
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 text-red-600 text-sm rounded flex items-center gap-2">
            <AlertCircle size={16} /> {error}
          </div>
        )}

        {/* Header fields */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="caption font-bold text-secondary mb-1 block uppercase tracking-wider">
              Número de Proforma
            </label>
            <input
              type="text"
              className="input w-full"
              placeholder="Ej: PRF-001"
              value={proformaNumber}
              onChange={e => setProformaNumber(e.target.value)}
              disabled={submitting}
            />
          </div>
          <div>
            <label className="caption font-bold text-secondary mb-1 block uppercase tracking-wider">
              Modo Logístico
            </label>
            <select
              className="input w-full"
              value={selectedMode}
              onChange={e => setSelectedMode(e.target.value)}
              disabled={submitting}
            >
              {allowedModes.map(m => (
                <option key={m} value={m}>{MODE_LABELS[m] || m}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Product catalog picker */}
        <div>
          <label className="caption font-bold text-secondary mb-2 block uppercase tracking-wider">
            Agregar Productos al Pedido
          </label>
          <div className="relative mb-2">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-tertiary" />
            <input
              type="text"
              className="input w-full pl-9"
              placeholder="Buscar por nombre o SKU…"
              value={search}
              onChange={e => setSearch(e.target.value)}
              disabled={submitting}
            />
          </div>
          <div className="border border-divider rounded overflow-hidden max-h-[200px] overflow-y-auto bg-surface divide-y divide-divider">
            {loadingProducts ? (
              <div className="p-4 text-center text-sm text-text-secondary">Cargando productos…</div>
            ) : filtered.length === 0 ? (
              <div className="p-4 text-center text-sm text-text-secondary italic">
                {search ? "Sin resultados." : "No hay productos disponibles."}
              </div>
            ) : (
              filtered.map(p => {
                const alreadyAdded = addedLines.some(l => l.product.id === p.id);
                return (
                  <div
                    key={p.id}
                    className="flex items-center justify-between px-3 py-2 hover:bg-bg transition-colors"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <Package size={13} className="shrink-0 text-text-tertiary" />
                      <div className="min-w-0">
                        <p className="text-sm font-medium truncate">{p.name}</p>
                        <p className="text-xs text-text-tertiary font-mono">{p.sku_base}</p>
                      </div>
                    </div>
                    <button
                      type="button"
                      className="btn btn-sm btn-ghost text-[var(--interactive)] text-xs shrink-0 ml-2 disabled:opacity-40"
                      onClick={() => addProduct(p)}
                      disabled={alreadyAdded || submitting}
                    >
                      {alreadyAdded ? "Agregado" : <><Plus size={12} /> Agregar</>}
                    </button>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Lines added */}
        {addedLines.length > 0 && (
          <div>
            <label className="caption font-bold text-secondary mb-2 block uppercase tracking-wider">
              Líneas del Pedido ({addedLines.length})
            </label>
            <div className="border border-divider rounded overflow-hidden divide-y divide-divider">
              {addedLines.map(line => (
                <div key={line.product.id} className="px-3 py-2 grid grid-cols-[1fr_90px_110px_32px] gap-2 items-center">
                  <div className="min-w-0">
                    <p className="text-sm font-medium truncate">{line.product.name}</p>
                    <p className="text-xs text-text-tertiary font-mono">{line.product.sku_base}</p>
                  </div>
                  <div>
                    <label className="text-[10px] text-text-tertiary block mb-0.5">Cantidad</label>
                    <div className="flex items-center border border-divider rounded overflow-hidden">
                      <button
                        type="button"
                        className="px-1.5 py-1 text-text-secondary hover:bg-bg"
                        onClick={() => updateLine(line.product.id, "quantity", Math.max(1, line.quantity - 1))}
                        disabled={submitting}
                      >
                        <Minus size={10} />
                      </button>
                      <input
                        type="number"
                        className="w-10 text-center text-sm border-0 focus:outline-none bg-transparent"
                        value={line.quantity}
                        min={1}
                        onChange={e => updateLine(line.product.id, "quantity", Math.max(1, Number(e.target.value)))}
                        disabled={submitting}
                      />
                      <button
                        type="button"
                        className="px-1.5 py-1 text-text-secondary hover:bg-bg"
                        onClick={() => updateLine(line.product.id, "quantity", line.quantity + 1)}
                        disabled={submitting}
                      >
                        <Plus size={10} />
                      </button>
                    </div>
                  </div>
                  <div>
                    <label className="text-[10px] text-text-tertiary block mb-0.5">Precio unit. (USD)</label>
                    <input
                      type="number"
                      className="input w-full text-sm py-1"
                      min={0}
                      step="0.01"
                      value={line.unit_price}
                      onChange={e => updateLine(line.product.id, "unit_price", Number(e.target.value))}
                      disabled={submitting}
                    />
                  </div>
                  <button
                    type="button"
                    className="text-red-400 hover:text-red-600 mt-4"
                    onClick={() => removeProduct(line.product.id)}
                    disabled={submitting}
                  >
                    <X size={14} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Orphan lines (if any) */}
        {orphanLines.length > 0 && (
          <div>
            <label className="caption font-bold text-secondary mb-2 block uppercase tracking-wider">
              Líneas existentes sin proforma ({orphanLines.length})
            </label>
            <div className="border border-divider rounded overflow-hidden divide-y divide-divider max-h-[150px] overflow-y-auto bg-surface">
              {orphanLines.map((line: any) => (
                <label key={line.id} className="flex items-center gap-3 p-3 hover:bg-bg transition-colors cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedOrphanIds.includes(line.id)}
                    onChange={() => toggleOrphan(line.id)}
                    disabled={submitting}
                    className="rounded border-divider"
                  />
                  <div className="flex-1">
                    <div className="body-sm font-medium">{line.product_name}</div>
                    <div className="caption text-secondary">Cant: {line.quantity}</div>
                  </div>
                  <div className="body-sm font-mono text-secondary">${Number(line.unit_price || 0).toFixed(2)}</div>
                </label>
              ))}
            </div>
          </div>
        )}
      </div>
    </FormModal>
  );
}
