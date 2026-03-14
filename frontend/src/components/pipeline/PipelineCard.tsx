"use client";
import Link from "next/link";
import { AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";
import { ExpedienteCard } from "./PipelineView";
import { CreditBadge } from "@/components/ui/CreditBadge";

interface PipelineCardProps {
  card: ExpedienteCard;
}

export function PipelineCard({ card }: PipelineCardProps) {
  return (
    <Link href={`/expedientes/${card.id}`} aria-label={`Ver expediente ${card.ref}`}>
      <div
        className={cn(
          "card-mwt p-3 cursor-pointer hover:shadow-md transition-shadow",
          // S9-03B fix: border-l-[3px] en lugar de border-l-4
          card.is_blocked
            ? "border-l-[3px] border-l-[var(--coral)]"
            : "border-l-[3px] border-l-transparent"
        )}
      >
        {/* ── Ref + badge bloqueado ── */}
        <div className="flex items-center justify-between mb-1.5">
          <span className="font-mono text-xs font-medium text-[var(--navy)]">{card.ref}</span>
          {card.is_blocked && (
            <span className="inline-flex items-center gap-0.5 text-[10px] font-semibold uppercase tracking-[0.5px] text-[var(--coral)] bg-[var(--coral-soft)] px-1.5 py-0.5 rounded">
              <AlertTriangle size={9} aria-hidden />
              Bloqueado
            </span>
          )}
        </div>

        {/* ── Cliente ── */}
        <p className="text-xs text-[var(--text-secondary)] mb-1 truncate">{card.client}</p>

        {/* ── Brand pill ── */}
        <span
          className="inline-block text-[10px] font-semibold px-2 py-0.5 rounded-full uppercase tracking-[0.5px] mb-2"
          style={{
            background: card.brand_color ? `${card.brand_color}20` : "var(--bg-alt)",
            color: card.brand_color ?? "var(--text-tertiary)",
          }}
        >
          {card.brand}
        </span>

        {/* ── Semáforo crédito: SIEMPRE color + texto + ícono ── */}
        <CreditBadge band={card.credit_band} />

        {/* ── Dots de avance de artefactos ── */}
        <div className="flex items-center gap-1 mt-2" aria-label={`${card.artifacts_done} de ${card.artifacts_total} artefactos completados`}>
          {Array.from({ length: card.artifacts_total }).map((_, i) => (
            <span
              key={i}
              className={cn(
                "inline-block w-2 h-2 rounded-full",
                i < card.artifacts_done ? "bg-[var(--mint)]" : "bg-[var(--border)]"
              )}
              aria-hidden
            />
          ))}
          <span className="text-[10px] text-[var(--text-disabled)] ml-1">
            {card.artifacts_done}/{card.artifacts_total}
          </span>
        </div>

        {/* ── Acción pendiente ── */}
        {card.pending_action && (
          <p className="text-[11px] italic text-[var(--text-tertiary)] mt-1.5 truncate">
            {card.pending_action}
          </p>
        )}
      </div>
    </Link>
  );
}
