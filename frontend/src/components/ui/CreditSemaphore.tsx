/**
 * S9-04/05 — CreditSemaphore
 * Versión visual ampliada del CreditBadge.
 * Muestra color + ícono + label + descripción expandida.
 * REGLA: nunca mostrar solo color — siempre acompañar con texto e ícono.
 */
"use client";
import { CheckCircle, AlertTriangle, AlertOctagon } from "lucide-react";
import { cn } from "@/lib/utils";
import { CreditBand, CREDIT_BAND_CONFIG } from "@/lib/constants/creditBands";

interface CreditSemaphoreProps {
  band: CreditBand;
  /** Muestra descripción expandida (para panel lateral o ficha de expediente) */
  expanded?: boolean;
  className?: string;
}

const ICONS = {
  "check-circle":   CheckCircle,
  "alert-triangle": AlertTriangle,
  "alert-octagon":  AlertOctagon,
} as const;

const DESCRIPTIONS: Record<CreditBand, string> = {
  GREEN: "Cliente al día — sin alertas de riesgo crediticio",
  AMBER: "Riesgo moderado — revisar historial de pagos",
  RED:   "Situación crítica — requiere atención inmediata",
};

export function CreditSemaphore({ band, expanded = false, className }: CreditSemaphoreProps) {
  const cfg  = CREDIT_BAND_CONFIG[band];
  const Icon = ICONS[cfg.icon as keyof typeof ICONS];

  if (!expanded) {
    // ── Compact (same as CreditBadge but from single source) ──
    return (
      <span
        className={cn(
          "inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold tracking-[0.5px] uppercase",
          className
        )}
        style={{ backgroundColor: cfg.bg, color: cfg.text }}
        aria-label={`Semáforo crédito: ${cfg.label}`}
      >
        <Icon size={12} aria-hidden />
        {cfg.label}
      </span>
    );
  }

  // ── Expanded panel variant ──
  return (
    <div
      className={cn("flex items-start gap-3 p-3 rounded-xl border", className)}
      style={{
        backgroundColor: cfg.bg,
        borderColor: `${cfg.text}30`,
      }}
      role="status"
      aria-label={`Semáforo crédito: ${cfg.label}`}
    >
      <span
        className="flex items-center justify-center w-8 h-8 rounded-full flex-shrink-0"
        style={{ backgroundColor: `${cfg.text}18`, color: cfg.text }}
      >
        <Icon size={18} aria-hidden />
      </span>
      <div>
        <p className="text-xs font-bold uppercase tracking-[0.5px]" style={{ color: cfg.text }}>
          {cfg.label}
        </p>
        <p className="text-xs mt-0.5" style={{ color: `${cfg.text}CC` }}>
          {DESCRIPTIONS[band]}
        </p>
      </div>
    </div>
  );
}
