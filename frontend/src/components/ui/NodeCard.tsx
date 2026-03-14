/**
 * S9-10 — NodeCard
 * Tarjeta grid para vista de Nodos logísticos.
 */
"use client";
import { cn } from "@/lib/utils";
import { MapPin, Package, Activity } from "lucide-react";
import Link from "next/link";

export interface NodeCardData {
  id: string;
  nombre: string;
  tipo: "ORIGEN" | "DESTINO" | "INTERMEDIO" | string;
  pais: string;
  ciudad: string;
  activo: boolean;
  expedientes_activos?: number;
  transfers_activos?: number;
}

const TIPO_STYLES: Record<string, { label: string; dot: string; badge: string }> = {
  ORIGEN:     { label: "Origen",      dot: "bg-[#1D4ED8]",  badge: "bg-[#EFF6FF] text-[#1D4ED8]" },
  DESTINO:    { label: "Destino",     dot: "bg-[#0E8A6D]",  badge: "bg-[#F0FAF6] text-[#0E8A6D]" },
  INTERMEDIO: { label: "Intermedio",  dot: "bg-[#B45309]",  badge: "bg-[#FFF7ED] text-[#B45309]" },
};

export function NodeCard({ node }: { node: NodeCardData }) {
  const tipo = TIPO_STYLES[node.tipo] ?? { label: node.tipo, dot: "bg-slate-400", badge: "bg-slate-100 text-slate-600" };

  return (
    <Link
      href={`/nodos/${node.id}`}
      className={cn(
        "block rounded-[var(--radius-xl)] border border-[var(--border)] bg-[var(--surface)]",
        "shadow-[var(--shadow-sm)] p-5 space-y-4",
        "hover:shadow-[var(--shadow-md)] hover:border-[var(--mint)] transition-all group"
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className={cn("w-2 h-2 rounded-full flex-shrink-0 mt-0.5", tipo.dot)} />
          <h3 className="font-semibold text-sm text-[var(--text-primary)] truncate group-hover:text-[var(--navy)] transition-colors">
            {node.nombre}
          </h3>
        </div>
        <span className={cn("text-[10px] font-bold uppercase tracking-[0.5px] px-2 py-0.5 rounded-md flex-shrink-0", tipo.badge)}>
          {tipo.label}
        </span>
      </div>

      {/* Location */}
      <div className="flex items-center gap-1.5 text-xs text-[var(--text-secondary)]">
        <MapPin size={12} className="flex-shrink-0" />
        <span className="truncate">{node.ciudad}, {node.pais}</span>
      </div>

      {/* Stats */}
      <div className="flex items-center gap-4 pt-2 border-t border-[var(--border)]">
        <div className="flex items-center gap-1.5 text-xs text-[var(--text-secondary)]">
          <Package size={12} />
          <span><strong className="text-[var(--text-primary)]">{node.expedientes_activos ?? 0}</strong> expedientes</span>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-[var(--text-secondary)]">
          <Activity size={12} />
          <span><strong className="text-[var(--text-primary)]">{node.transfers_activos ?? 0}</strong> transfers</span>
        </div>
      </div>

      {/* Status dot */}
      <div className="flex items-center gap-1.5">
        <span className={cn("w-1.5 h-1.5 rounded-full", node.activo ? "bg-[#0E8A6D]" : "bg-[#94A3B8]")} />
        <span className="text-xs text-[var(--text-muted)]">{node.activo ? "Activo" : "Inactivo"}</span>
      </div>
    </Link>
  );
}
