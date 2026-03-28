"use client";

import { useState, useRef } from "react";
import { Info } from "lucide-react";

interface PricingData {
  price: number;
  source?: string;
  // Nivel 2: desglose opcional (no hardcodeado — se verifica dinámicamente)
  [key: string]: unknown;
}

interface Props {
  unitPrice: number | string | null | undefined;
  pricingData?: PricingData | null;
  currency?: string;
  children?: React.ReactNode;
}

/**
 * S19-15 — Tooltip pricing en fila product_line.
 * Nivel 1 (siempre): price + source del response de /api/pricing/resolve/
 * Nivel 2 (condicional): desglose cost/margin/markup si el backend lo incluye.
 * NO hardcodea campos de nivel 2 — los verifica dinámicamente.
 */
export default function PricingTooltip({ unitPrice, pricingData, currency = "USD", children }: Props) {
  const [visible, setVisible] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const show = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    setVisible(true);
  };

  const hide = () => {
    timeoutRef.current = setTimeout(() => setVisible(false), 120);
  };

  // Campos de nivel 2 — verificados dinámicamente, nunca hardcodeados
  const level2Fields: Array<{ key: string; label: string }> = [
    { key: "cost", label: "Costo" },
    { key: "margin", label: "Margen" },
    { key: "markup", label: "Markup" },
    { key: "markup_pct", label: "Markup %" },
    { key: "margin_pct", label: "Margen %" },
  ];

  const availableLevel2 = pricingData
    ? level2Fields.filter(
        (f) =>
          f.key in pricingData &&
          pricingData[f.key] !== null &&
          pricingData[f.key] !== undefined
      )
    : [];

  const displayPrice =
    pricingData?.price ?? unitPrice ?? null;

  return (
    <div className="relative inline-flex items-center gap-1.5" onMouseEnter={show} onMouseLeave={hide}>
      {children ?? (
        <span className="text-sm font-semibold tabular-nums text-[var(--color-text-primary)]">
          {displayPrice !== null ? `${currency} ${Number(displayPrice).toLocaleString("es-CR", { minimumFractionDigits: 2 })}` : "—"}
        </span>
      )}

      {pricingData && (
        <Info className="w-3.5 h-3.5 text-[var(--color-text-tertiary)] cursor-help flex-shrink-0" />
      )}

      {visible && pricingData && (
        <div
          className="absolute bottom-full left-0 mb-2 z-30 min-w-[180px] bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl shadow-lg px-3 py-2.5 space-y-1.5 pointer-events-none"
          role="tooltip"
        >
          {/* Nivel 1 — siempre */}
          <div className="flex items-center justify-between gap-4">
            <span className="text-xs text-[var(--color-text-tertiary)]">Precio</span>
            <span className="text-xs font-semibold text-[var(--color-text-primary)] tabular-nums">
              {currency} {Number(pricingData.price).toLocaleString("es-CR", { minimumFractionDigits: 2 })}
            </span>
          </div>

          {pricingData.source && (
            <div className="flex items-center justify-between gap-4">
              <span className="text-xs text-[var(--color-text-tertiary)]">Fuente</span>
              <span className="text-xs text-[var(--color-text-secondary)] font-mono">{String(pricingData.source)}</span>
            </div>
          )}

          {/* Nivel 2 — condicional: solo si el backend lo incluye */}
          {availableLevel2.length > 0 && (
            <>
              <div className="border-t border-[var(--color-border)] pt-1.5 mt-1.5" />
              {availableLevel2.map((f) => (
                <div key={f.key} className="flex items-center justify-between gap-4">
                  <span className="text-xs text-[var(--color-text-tertiary)]">{f.label}</span>
                  <span className="text-xs font-semibold text-[var(--color-text-primary)] tabular-nums">
                    {typeof pricingData[f.key] === "number"
                      ? f.key.includes("pct")
                        ? `${(pricingData[f.key] as number).toFixed(1)}%`
                        : `${currency} ${(pricingData[f.key] as number).toLocaleString("es-CR", { minimumFractionDigits: 2 })}`
                      : String(pricingData[f.key])}
                  </span>
                </div>
              ))}
            </>
          )}
        </div>
      )}
    </div>
  );
}
