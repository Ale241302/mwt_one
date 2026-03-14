"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Receipt, Plus, ChevronRight, CheckCircle, Clock, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";
import api from "@/lib/api";

// ─── Types ────────────────────────────────────────────────────────────────────
interface Liquidacion {
  id: string;
  periodo: string;
  monto_total: number;
  moneda: string;
  expedientes_incluidos: number;
  estado: "PENDIENTE" | "APROBADA" | "PARCIAL" | "RECHAZADA";
  fecha_creacion: string;
  fecha_aprobacion?: string;
}

// ─── Estado badge ─────────────────────────────────────────────────────────────
const ESTADO_CONFIG: Record<string, { label: string; classes: string; icon: React.ReactNode }> = {
  PENDIENTE:  { label: "Pendiente",  classes: "bg-[#FFF7ED] text-[#B45309]",   icon: <Clock size={12} /> },
  APROBADA:   { label: "Aprobada",   classes: "bg-[#F0FAF6] text-[#0E8A6D]",   icon: <CheckCircle size={12} /> },
  PARCIAL:    { label: "Parcial",    classes: "bg-[#FFF7ED] text-[#B45309]",   icon: <AlertTriangle size={12} /> },
  RECHAZADA:  { label: "Rechazada",  classes: "bg-[#FEF2F2] text-[#DC2626]",   icon: <AlertTriangle size={12} /> },
};

function EstadoBadge({ estado }: { estado: string }) {
  const cfg = ESTADO_CONFIG[estado] ?? ESTADO_CONFIG["PENDIENTE"];
  return (
    <span className={cn("inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold uppercase tracking-[0.5px]", cfg.classes)}>
      {cfg.icon}
      {cfg.label}
    </span>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────
export default function LiquidacionesPage() {
  const { lang } = useParams<{ lang: string }>();
  const [liquidaciones, setLiquidaciones] = useState<Liquidacion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchLiquidaciones() {
      try {
        const res = await api.get("liquidations/");
        const data = res.data;
        setLiquidaciones(data.results ?? data);
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : "Error desconocido";
        setError(msg);
      } finally {
        setLoading(false);
      }
    }
    fetchLiquidaciones();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-display font-bold text-navy">Liquidaciones</h1>
          <p className="text-sm text-text-secondary mt-0.5">Reconciliación de pagos Marluvas.</p>
        </div>
        <Link
          href={`/${lang}/liquidaciones/nueva`}
          className="inline-flex items-center gap-2 px-4 py-2 bg-navy text-white rounded-xl text-sm font-medium hover:bg-navy-dark transition-colors"
        >
          <Plus size={16} />
          Nueva liquidación
        </Link>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm border border-border">
        {loading ? (
          <div className="p-12 text-center text-text-secondary text-sm">Cargando liquidaciones…</div>
        ) : error ? (
          <div className="p-12 text-center text-[#DC2626] text-sm">Error al cargar: {error}</div>
        ) : liquidaciones.length === 0 ? (
          <div className="p-12 text-center">
            <Receipt size={40} className="mx-auto text-text-secondary opacity-40 mb-3" />
            <p className="text-text-secondary text-sm">Sin liquidaciones registradas todavía.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left px-6 py-3 text-xs font-semibold uppercase tracking-[0.5px] text-text-secondary">Período</th>
                  <th className="text-left px-6 py-3 text-xs font-semibold uppercase tracking-[0.5px] text-text-secondary">Monto total</th>
                  <th className="text-left px-6 py-3 text-xs font-semibold uppercase tracking-[0.5px] text-text-secondary">Expedientes</th>
                  <th className="text-left px-6 py-3 text-xs font-semibold uppercase tracking-[0.5px] text-text-secondary">Estado</th>
                  <th className="text-left px-6 py-3 text-xs font-semibold uppercase tracking-[0.5px] text-text-secondary">Fecha</th>
                  <th className="px-6 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {liquidaciones.map((liq) => (
                  <tr key={liq.id} className="hover:bg-bg transition-colors">
                    <td className="px-6 py-4 font-medium text-navy">{liq.periodo}</td>
                    <td className="px-6 py-4 font-mono text-sm">
                      {liq.moneda} {Number(liq.monto_total).toLocaleString("es-CO", { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-6 py-4 text-text-secondary">{liq.expedientes_incluidos} expedientes</td>
                    <td className="px-6 py-4"><EstadoBadge estado={liq.estado} /></td>
                    <td className="px-6 py-4 text-text-secondary">
                      {new Date(liq.fecha_creacion).toLocaleDateString("es-CO")}
                    </td>
                    <td className="px-6 py-4">
                      <Link href={`/${lang}/liquidaciones/${liq.id}`} className="text-navy hover:text-mint transition-colors">
                        <ChevronRight size={16} />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
