"use client";
import { useRouter } from "next/navigation";
import { AlertTriangle } from "lucide-react";
import { ExpedienteCard } from "./PipelineView";
import { CreditBadge } from "@/components/ui/CreditBadge";

interface PipelineCardProps {
  card: ExpedienteCard;
}

export function PipelineCard({ card }: PipelineCardProps) {
  const router = useRouter();

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label={`Ver expediente ${card.ref}`}
      onClick={() => router.push(`/expedientes/${card.id}`)}
      onKeyDown={(e) => e.key === "Enter" && router.push(`/expedientes/${card.id}`)}
      className="cursor-pointer transition-shadow hover:shadow-md rounded-xl p-3"
      style={{
        background: "#FFFFFF",
        border: "1px solid #E2E5EA",
        borderLeft: card.is_blocked ? "3px solid #E85D5D" : "3px solid transparent",
        boxShadow: "0 1px 3px rgba(1,58,87,.06)",
      }}
    >
      {/* Ref + badge bloqueado */}
      <div className="flex items-center justify-between mb-1.5">
        <span className="font-mono text-xs font-semibold" style={{ color: "#013A57" }}>
          {card.ref || "—"}
        </span>
        {card.is_blocked && (
          <span className="inline-flex items-center gap-0.5 text-[10px] font-semibold uppercase tracking-wide px-1.5 py-0.5 rounded"
            style={{ color: "#E85D5D", background: "#FDECEC" }}>
            <AlertTriangle size={9} aria-hidden />
            Bloqueado
          </span>
        )}
      </div>

      {/* Cliente */}
      <p className="text-xs mb-1 truncate" style={{ color: "#3D4F5C" }}>
        {card.client || "Sin cliente"}
      </p>

      {/* Brand pill */}
      <span
        className="inline-block text-[10px] font-semibold px-2 py-0.5 rounded-full uppercase tracking-wide mb-2"
        style={{
          background: card.brand_color ? `${card.brand_color}20` : "#F0F2F5",
          color: card.brand_color ?? "#7A8A96",
        }}
      >
        {card.brand || "—"}
      </span>

      {/* Semaforo credito */}
      <CreditBadge band={card.credit_band} />

      {/* Dots de artefactos */}
      <div className="flex items-center gap-1 mt-2">
        {Array.from({ length: card.artifacts_total }).map((_, i) => (
          <span
            key={i}
            className="inline-block w-2 h-2 rounded-full"
            style={{ background: i < card.artifacts_done ? "#75CBB3" : "#E2E5EA" }}
          />
        ))}
        <span className="text-[10px] ml-1" style={{ color: "#B0BAC4" }}>
          {card.artifacts_done}/{card.artifacts_total}
        </span>
      </div>

      {/* Accion pendiente */}
      {card.pending_action && (
        <p className="text-[11px] italic mt-1.5 truncate" style={{ color: "#7A8A96" }}>
          {card.pending_action}
        </p>
      )}
    </div>
  );
}
