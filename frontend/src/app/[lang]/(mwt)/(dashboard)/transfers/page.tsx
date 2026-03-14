"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeftRight, Plus, ChevronRight, Clock, CheckCircle, Truck, Package, AlertTriangle, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import api from "@/lib/api";

// ─── Types ────────────────────────────────────────────────────────────────────
interface Transfer {
  id: string;
  referencia: string;
  estado: "PENDIENTE" | "EN_TRANSITO" | "EN_DESTINO" | "ENTREGADO" | "BLOQUEADO" | "CANCELADO";
  origen: string;
  destino: string;
  fecha_estimada?: string;
  expediente_ref?: string;
  brand?: string;
}

const ESTADO_CONFIG: Record<string, { label: string; classes: string; icon: React.ReactNode }> = {
  PENDIENTE:    { label: "Pendiente",    classes: "bg-[#FFF7ED] text-[#B45309]",  icon: <Clock size={12} /> },
  EN_TRANSITO:  { label: "En tránsito",  classes: "bg-[#EFF6FF] text-[#1D4ED8]", icon: <Truck size={12} /> },
  EN_DESTINO:   { label: "En destino",   classes: "bg-[#F5F3FF] text-[#7C3AED]", icon: <Package size={12} /> },
  ENTREGADO:    { label: "Entregado",    classes: "bg-[#F0FAF6] text-[#0E8A6D]",  icon: <CheckCircle size={12} /> },
  BLOQUEADO:    { label: "Bloqueado",    classes: "bg-[#FEF9C3] text-[#854D0E]",  icon: <AlertTriangle size={12} /> },
  CANCELADO:    { label: "Cancelado",    classes: "bg-[#FEF2F2] text-[#DC2626]",  icon: <XCircle size={12} /> },
};

function EstadoBadge({ estado }: { estado: string }) {
  const cfg = ESTADO_CONFIG[estado] ?? ESTADO_CONFIG["PENDIENTE"];
  return (
    <span className={cn("inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold uppercase tracking-[0.5px]", cfg.classes)}>
      {cfg.icon} {cfg.label}
    </span>
  );
}

// Estado filter pills
const FILTERS = ["TODOS", ...Object.keys(ESTADO_CONFIG)] as const;

export default function TransfersPage() {
  const { lang } = useParams<{ lang: string }>();
  const [transfers, setTransfers] = useState<Transfer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filtro, setFiltro] = useState("TODOS");

  useEffect(() => {
    async function fetchTransfers() {
      try {
        const url = filtro !== "TODOS"
          ? `transfers/?estado=${filtro}`
          : `transfers/`;
        const res = await api.get(url);
        const data = res.data;
        setTransfers(data.results ?? data);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Error");
      } finally {
        setLoading(false);
      }
    }
    fetchTransfers();
  }, [filtro]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-display font-bold text-navy">Transfers</h1>
          <p className="text-sm text-text-secondary mt-0.5">Movimientos de mercancía entre nodos.</p>
        </div>
        <Link
          href={`/${lang}/transfers/nuevo`}
          className="inline-flex items-center gap-2 px-4 py-2 bg-navy text-white rounded-xl text-sm font-medium hover:bg-navy-dark transition-colors"
        >
          <Plus size={16} />
          Nuevo transfer
        </Link>
      </div>

      {/* Filter pills */}
      <div className="flex flex-wrap gap-2">
        {FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => { setFiltro(f); setLoading(true); }}
            className={cn(
              "px-3 py-1 rounded-full text-xs font-semibold transition-colors",
              filtro === f ? "bg-navy text-white" : "bg-white border border-border text-text-secondary hover:border-navy"
            )}
          >
            {f === "TODOS" ? "Todos" : ESTADO_CONFIG[f]?.label ?? f}
          </button>
        ))}
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-border">
        {loading ? (
          <div className="p-12 text-center text-text-secondary text-sm">Cargando transfers…</div>
        ) : error ? (
          <div className="p-12 text-center text-[#DC2626] text-sm">{error}</div>
        ) : transfers.length === 0 ? (
          <div className="p-12 text-center">
            <ArrowLeftRight size={40} className="mx-auto text-text-secondary opacity-40 mb-3" />
            <p className="text-text-secondary text-sm">Sin transfers registrados.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  {["Referencia", "Origen → Destino", "Brand", "Expediente", "Fecha est.", "Estado", ""].map((h) => (
                    <th key={h} className="text-left px-6 py-3 text-xs font-semibold uppercase tracking-[0.5px] text-text-secondary">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {transfers.map((t) => (
                  <tr key={t.id} className="hover:bg-bg transition-colors">
                    <td className="px-6 py-4 font-mono text-xs font-medium text-navy">{t.referencia}</td>
                    <td className="px-6 py-4 text-text-secondary">{t.origen} → {t.destino}</td>
                    <td className="px-6 py-4 text-text-secondary">{t.brand ?? "—"}</td>
                    <td className="px-6 py-4">
                      {t.expediente_ref ? (
                        <Link href={`/${lang}/expedientes`} className="text-navy hover:text-mint underline text-xs">{t.expediente_ref}</Link>
                      ) : "—"}
                    </td>
                    <td className="px-6 py-4 text-text-secondary">
                      {t.fecha_estimada ? new Date(t.fecha_estimada).toLocaleDateString("es-CO") : "—"}
                    </td>
                    <td className="px-6 py-4"><EstadoBadge estado={t.estado} /></td>
                    <td className="px-6 py-4">
                      <Link href={`/${lang}/transfers/${t.id}`} className="text-navy hover:text-mint transition-colors">
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
