// S22-13 — Línea de producto en proforma/expediente con pre-fill precio, tooltip y MOQ badge
"use client";

import { useEffect, useState } from 'react';
import { X, Info, AlertTriangle } from 'lucide-react';
import { resolveClientPrice, ResolvedPrice } from '@/api/pricing';

interface Producto {
  id: number;
  name: string;
  sku_base?: string;
  brand_sku_id?: number; // id del BrandSKU ligado al producto
}

interface ProductLineRowProps {
  index: number;
  productos: Producto[];
  brandFiltered: boolean;
  clientSubsidiaryId: number | null;
  paymentDays?: number;
  onRemove: () => void;
  onChange: (patch: { producto_id: number | null; quantity: string; unit_price: string }) => void;
  value: { producto_id: number | null; quantity: string; unit_price: string };
  disabled?: boolean;
}

const SOURCE_LABELS: Record<string, string> = {
  assignment: 'Asignación directa (CPA)',
  agreement: 'Acuerdo Brand-Client',
  pricelist_grade: 'Pricelist Grade activo',
  pricelist_legacy: 'Pricelist legado (S14)',
  manual: 'Precio manual',
};

export function ProductLineRow({
  index,
  productos,
  brandFiltered,
  clientSubsidiaryId,
  paymentDays,
  onRemove,
  onChange,
  value,
  disabled,
}: ProductLineRowProps) {
  const [resolving, setResolving] = useState(false);
  const [resolved, setResolved] = useState<ResolvedPrice | null>(null);
  const [showTooltip, setShowTooltip] = useState(false);

  const selectedProducto = productos.find((p) => p.id === value.producto_id);
  const brandSkuId = selectedProducto?.brand_sku_id ?? null;

  // Pre-fill precio cuando cambia el producto o el cliente
  useEffect(() => {
    if (!brandSkuId || !clientSubsidiaryId) {
      setResolved(null);
      return;
    }
    let cancelled = false;
    setResolving(true);
    resolveClientPrice({
      brand_sku_id: brandSkuId,
      client_subsidiary_id: clientSubsidiaryId,
      payment_days: paymentDays,
    }).then((result) => {
      if (cancelled) return;
      setResolved(result);
      // Solo pre-fill si la fuente NO es manual
      if (result && result.source !== 'manual' && result.price) {
        onChange({ ...value, unit_price: result.price });
      }
    }).finally(() => {
      if (!cancelled) setResolving(false);
    });
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [brandSkuId, clientSubsidiaryId, paymentDays, onChange, value.producto_id]);

  const isManual = resolved?.source === 'manual' || !resolved;
  const hasMoqWarning = resolved?.grade_moq != null && Number(value.quantity) > 0 && Number(value.quantity) < resolved.grade_moq;

  const inputCls =
    'w-full bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg px-3 py-2.5 text-sm text-[var(--color-text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-navy)]/30';

  return (
    <div className="grid grid-cols-[1fr_130px_130px_36px] gap-2 items-start">
      {/* Selector de producto */}
      <select
        value={value.producto_id ?? ''}
        onChange={(e) => {
          const id = e.target.value ? Number(e.target.value) : null;
          onChange({ producto_id: id, quantity: value.quantity, unit_price: '' });
          setResolved(null);
        }}
        disabled={disabled || !brandFiltered}
        className={inputCls + ' disabled:opacity-50 disabled:cursor-not-allowed'}
      >
        <option value="">
          {!brandFiltered ? 'Primero seleccioná una marca' : 'Seleccionar producto...'}
        </option>
        {productos.map((p) => (
          <option key={p.id} value={p.id}>
            {p.name}{p.sku_base ? ` — ${p.sku_base}` : ''}
          </option>
        ))}
      </select>

      {/* Cantidad */}
      <div className="relative">
        <input
          type="number"
          min={1}
          value={value.quantity}
          onChange={(e) => onChange({ ...value, quantity: e.target.value })}
          placeholder="0"
          className={inputCls}
        />
        {hasMoqWarning && (
          <div className="absolute -top-5 left-0 flex items-center gap-1 text-amber-600 text-xs font-medium whitespace-nowrap">
            <AlertTriangle size={11} />
            MOQ mín: {resolved!.grade_moq}
          </div>
        )}
      </div>

      {/* Precio unitario con tooltip */}
      <div className="relative">
        <div className="flex items-center gap-1">
          <input
            type="number"
            step="0.0001"
            min={0}
            value={value.unit_price}
            onChange={(e) => onChange({ ...value, unit_price: e.target.value })}
            readOnly={!isManual && !!resolved?.price}
            placeholder={resolving ? 'Calculando...' : '0.0000'}
            className={
              inputCls +
              (resolving ? ' opacity-50 cursor-wait' : '') +
              (!isManual && resolved?.price ? ' bg-emerald-50 border-emerald-300 font-mono text-emerald-800' : '')
            }
          />
          {resolved && (
            <button
              type="button"
              className="flex-shrink-0 text-[var(--color-text-tertiary)] hover:text-[var(--color-navy)] transition-colors"
              onMouseEnter={() => setShowTooltip(true)}
              onMouseLeave={() => setShowTooltip(false)}
              aria-label="Ver desglose de precio"
            >
              <Info size={14} />
            </button>
          )}
        </div>

        {/* Tooltip de desglose */}
        {showTooltip && resolved && (
          <div className="absolute bottom-full left-0 mb-2 z-50 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl shadow-lg p-3 w-64 text-xs">
            <p className="font-semibold text-[var(--color-text-primary)] mb-2">Desglose de precio</p>
            <div className="space-y-1 text-[var(--color-text-secondary)]">
              <div className="flex justify-between">
                <span>Precio base:</span>
                <span className="font-mono">{resolved.base_price ? `$${resolved.base_price}` : '—'}</span>
              </div>
              {resolved.discount_applied && (
                <div className="flex justify-between text-emerald-700">
                  <span>Descuento pronto pago:</span>
                  <span className="font-mono">-{resolved.discount_applied}%</span>
                </div>
              )}
              <div className="flex justify-between font-semibold text-[var(--color-text-primary)] border-t border-[var(--color-border)] pt-1 mt-1">
                <span>Precio final:</span>
                <span className="font-mono">{resolved.price ? `$${resolved.price}` : '—'}</span>
              </div>
              <div className="flex justify-between text-[var(--color-text-tertiary)] mt-1">
                <span>Fuente:</span>
                <span>{SOURCE_LABELS[resolved.source ?? ''] ?? resolved.source ?? '—'}</span>
              </div>
              {resolved.grade_moq != null && (
                <div className="flex justify-between">
                  <span>MOQ Grade:</span>
                  <span className="font-mono">{resolved.grade_moq}</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Eliminar fila */}
      <button
        type="button"
        onClick={onRemove}
        className="flex items-center justify-center w-9 h-9 rounded-lg border border-[var(--color-border)] text-[var(--color-text-tertiary)] hover:border-red-400 hover:text-red-500 hover:bg-red-50 transition-colors"
        aria-label={`Eliminar línea ${index + 1}`}
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}
