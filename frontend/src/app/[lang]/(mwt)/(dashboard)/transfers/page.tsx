"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeftRight, Plus, ChevronRight,
  Clock, CheckCircle, Truck, Package, AlertTriangle, XCircle
} from "lucide-react";
import { cn } from "@/lib/utils";
import api from "@/lib/api";

// ─── Types ────────────────────────────────────────────────────────────────────
// Shape que devuelve TransferListSerializer
interface Transfer {
  transfer_id: string;
  status: "planned" | "approved" | "in_transit" | "received" | "reconciled" | "cancelled";
  legal_context: string;
  ownership_changes: boolean;
  customs_required: boolean;
  created_at: string;
  from_node: string | { node_id: string; name: string; legal_entity_name?: string };
  to_node:   string | { node_id: string; name: string; legal_entity_name?: string };
}

function nodeName(n: Transfer["from_node"]): string {
  if (!n) return "—";
  if (typeof n === "object") return n.name ?? String(n.node_id);
  return String(n);
}

// ─── Status badge ─────────────────────────────────────────────────────────────
const STATUS_CONFIG: Record<string, { label: string; classes: string; icon: React.ReactNode }> = {
  planned:     { label: "Planeado",    classes: "bg-[#F1F5F9] text-[#475569]",   icon: <Clock size={12} /> },
  approved:    { label: "Aprobado",    classes: "bg-[#FFF7ED] text-[#B45309]",   icon: <CheckCircle size={12} /> },
  in_transit:  { label: "En tránsito", classes: "bg-[#EFF6FF] text-[#1D4ED8]",  icon: <Truck size={12} /> },
  received:    { label: "Recibido",    classes: "bg-[#F5F3FF] text-[#7C3AED]",   icon: <Package size={12} /> },
  reconciled:  { label: "Reconciliado",classes: "bg-[#F0FAF6] text-[#0E8A6D]",  icon: <CheckCircle size={12} /> },
  cancelled:   { label: "Cancelado",   classes: "bg-[#FEF2F2] text-[#DC2626]",   icon: <XCircle size={12} /> },
};

const STATUS_KEYS = Object.keys(STATUS_CONFIG);
const FILTERS = ["todos", ...STATUS_KEYS] as const;

function StatusBadge({ status }: { status: string }) {
  const cfg = STATUS_CONFIG[status] ?? STATUS_CONFIG["planned"];
  return (
    <span className={cn(
      "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold uppercase tracking-[0.5px]",
      cfg.classes
    )}>
      {cfg.icon} {cfg.label}
    </span>
  );
}

// ─── Page ───────────────────────────────────────────────────────────────────────
export default function TransfersPage() {
  const params = useParams();
  const lang = (params?.lang as string) || "es";

  const [transfers, setTransfers] = useState<Transfer[]>([]);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState<string | null>(null);
  const [filtro, setFiltro]       = useState("todos");

  useEffect(() => {
    let cancelled = false;
    async function fetchTransfers() {
      setLoading(true);
      setError(null);
      try {
        const endpoint = filtro !== "todos"
          ? `ui/transfers/?estado=${filtro}`
          : `ui/transfers/`;
        const res = await api.get(endpoint);
        if (cancelled) return;
        // API devuelve { transfers: [...], nodes: [...] }
        // Nunca llamar .map sobre el objeto completo
        const raw = res.data;
        const list: Transfer[] = Array.isArray(raw)
          ? raw
          : Array.isArray(raw?.transfers)
          ? raw.transfers
          : Array.isArray(raw?.results)
          ? raw.results
          : [];
        setTransfers(list);
      } catch (e: unknown) {
        if (!cancelled) {
          const msg = (e as { message?: string })?.message ?? "Error al cargar transfers";
          setError(msg);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    fetchTransfers();
    return () => { cancelled = true; };
  }, [filtro]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-display font-bold text-navy">Transfers</h1>
          <p className="text-sm text-text-secondary mt-0.5">Movimientos de mercancía entre nodos.</p>
        </div>
        <Link
          href={`/${lang}/transfers/nuevo`}
          className="inline-flex items-center gap-2 px-4 py-2 bg-navy text-white rounded-xl text-sm font-medium hover:bg-navy-dark transition-colors"
        >
          <Plus size={16} /> Nuevo transfer
        </Link>
      </div>

      {/* Filter pills */}
      <div className="flex flex-wrap gap-2">
        {FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => setFiltro(f)}
            className={cn(
              "px-3 py-1 rounded-full text-xs font-semibold transition-colors",
              filtro === f
                ? "bg-navy text-white"
                : "bg-white border border-border text-text-secondary hover:border-navy"
            )}
          >
            {f === "todos" ? "Todos" : (STATUS_CONFIG[f]?.label ?? f)}
          </button>
        ))}
      </div>

      {/* Table */}
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
                  {["ID Transfer", "Origen → Destino", "Contexto Legal", "Aduana", "Fecha", "Estado", ""].map((h) => (
                    <th key={h} className="text-left px-6 py-3 text-xs font-semibold uppercase tracking-[0.5px] text-text-secondary">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {transfers.map((t) => (
                  <tr key={t.transfer_id} className="hover:bg-bg transition-colors">
                    <td className="px-6 py-4 font-mono text-xs font-medium text-navy">{t.transfer_id}</td>
                    <td className="px-6 py-4 text-text-secondary">
                      {nodeName(t.from_node)} → {nodeName(t.to_node)}
                    </td>
                    <td className="px-6 py-4 text-text-secondary capitalize">{t.legal_context ?? "—"}</td>
                    <td className="px-6 py-4">
                      {t.customs_required ? (
                        <span className="text-xs text-[#B45309] bg-[#FFF7ED] px-2 py-0.5 rounded-full font-semibold">Sí</span>
                      ) : (
                        <span className="text-xs text-text-secondary">No</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-text-secondary text-xs">
                      {t.created_at ? new Date(t.created_at).toLocaleDateString("es-CO") : "—"}
                    </td>
                    <td className="px-6 py-4"><StatusBadge status={t.status} /></td>
                    <td className="px-6 py-4">
                      <Link href={`/${lang}/transfers/${t.transfer_id}`} className="text-navy hover:text-mint transition-colors">
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
