"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft, Clock, Truck, Package, CheckCircle, XCircle, AlertTriangle,
  MapPin, Building2, Calendar, Hash
} from "lucide-react";
import { cn } from "@/lib/utils";
import api from "@/lib/api";

// ─── Types ──────────────────────────────────────────────────────────────────
interface NodeDetail {
  node_id: string;
  name: string;
  node_type: string;
  location: string;
  legal_entity_name: string;
}

interface TransferLine {
  id: number;
  sku: string;
  quantity_dispatched: number;
  quantity_received: number | null;
  condition: string | null;
  discrepancy: number | null;
  has_discrepancy: boolean;
}

interface TransferDetail {
  transfer_id: string;
  status: string;
  legal_context: string;
  ownership_changes: boolean;
  customs_required: boolean;
  created_at: string;
  updated_at: string;
  from_node: NodeDetail;
  to_node: NodeDetail;
  lines: TransferLine[];
  cancel_reason: string;
  exception_reason: string;
  source_expediente?: string | null;
}

const STATUS_CONFIG: Record<string, { label: string; classes: string; icon: React.ReactNode }> = {
  planned:     { label: "Planeado",     classes: "bg-[#F1F5F9] text-[#475569]",  icon: <Clock size={14} /> },
  approved:    { label: "Aprobado",     classes: "bg-[#FFF7ED] text-[#B45309]",  icon: <CheckCircle size={14} /> },
  in_transit:  { label: "En tránsito",  classes: "bg-[#EFF6FF] text-[#1D4ED8]",  icon: <Truck size={14} /> },
  received:    { label: "Recibido",     classes: "bg-[#F5F3FF] text-[#7C3AED]",  icon: <Package size={14} /> },
  reconciled:  { label: "Reconciliado", classes: "bg-[#F0FAF6] text-[#0E8A6D]",  icon: <CheckCircle size={14} /> },
  cancelled:   { label: "Cancelado",    classes: "bg-[#FEF2F2] text-[#DC2626]",  icon: <XCircle size={14} /> },
};

function StatusBadge({ status }: { status: string }) {
  const cfg = STATUS_CONFIG[status] ?? STATUS_CONFIG["planned"];
  return (
    <span className={cn(
      "inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-semibold uppercase tracking-wide",
      cfg.classes
    )}>
      {cfg.icon} {cfg.label}
    </span>
  );
}

function InfoRow({ icon, label, value }: { icon: React.ReactNode; label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-start gap-3">
      <div className="text-text-secondary mt-0.5">{icon}</div>
      <div>
        <p className="text-xs text-text-secondary uppercase tracking-wider font-semibold mb-0.5">{label}</p>
        <p className="text-sm text-text-primary">{value || "—"}</p>
      </div>
    </div>
  );
}

// ─── Page ────────────────────────────────────────────────────────────────────
export default function TransferDetailPage() {
  const params = useParams();
  const router = useRouter();
  const lang = (params?.lang as string) || "es";
  const transferId = params?.transferId as string;

  const [transfer, setTransfer] = useState<TransferDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!transferId) return;
    let cancelled = false;
    async function load() {
      try {
        const res = await api.get(`transfers/${transferId}/`);
        if (!cancelled) setTransfer(res.data);
      } catch (e: unknown) {
        if (!cancelled) {
          const status = (e as { response?: { status?: number } })?.response?.status;
          setError(status === 404 ? "Transfer no encontrado." : "Error al cargar el transfer.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, [transferId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-navy border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !transfer) {
    return (
      <div className="text-center py-20">
        <AlertTriangle size={40} className="mx-auto text-text-secondary opacity-40 mb-3" />
        <p className="text-text-secondary">{error ?? "Transfer no encontrado."}</p>
        <Link href={`/${lang}/transfers`} className="text-navy hover:underline text-sm mt-4 inline-block">
          ← Volver a Transfers
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Back */}
      <button
        onClick={() => router.back()}
        className="text-sm text-text-secondary hover:text-navy flex items-center gap-1 transition-colors"
      >
        <ArrowLeft size={15} /> Volver
      </button>

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-display font-bold text-navy font-mono">{transfer.transfer_id}</h1>
          <p className="text-sm text-text-secondary mt-0.5 capitalize">{transfer.legal_context}</p>
        </div>
        <StatusBadge status={transfer.status} />
      </div>

      {/* Nodes card */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {[{ label: "Nodo Origen", node: transfer.from_node }, { label: "Nodo Destino", node: transfer.to_node }].map(({ label, node }) => (
          <div key={label} className="bg-white rounded-xl border border-border p-5 shadow-sm space-y-3">
            <p className="text-xs font-semibold uppercase tracking-wider text-text-secondary">{label}</p>
            <p className="font-semibold text-text-primary">{node.name}</p>
            <div className="space-y-1.5 text-sm text-text-secondary">
              <div className="flex items-center gap-2"><Building2 size={13} /> {node.legal_entity_name}</div>
              {node.location && <div className="flex items-center gap-2"><MapPin size={13} /> {node.location}</div>}
              <div className="flex items-center gap-2"><Hash size={13} /> {node.node_type}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Meta */}
      <div className="bg-white rounded-xl border border-border p-5 shadow-sm grid grid-cols-2 md:grid-cols-4 gap-5">
        <InfoRow icon={<Calendar size={15} />} label="Creado" value={new Date(transfer.created_at).toLocaleDateString("es-CO")} />
        <InfoRow icon={<CheckCircle size={15} />} label="Cambia propietario" value={transfer.ownership_changes ? "Sí" : "No"} />
        <InfoRow icon={<AlertTriangle size={15} />} label="Requiere aduana" value={transfer.customs_required ? "Sí" : "No"} />
        {transfer.source_expediente && (
          <InfoRow icon={<Hash size={15} />} label="Expediente" value={String(transfer.source_expediente)} />
        )}
      </div>

      {/* Lines */}
      <div className="bg-white rounded-xl border border-border shadow-sm">
        <div className="px-6 py-4 border-b border-border">
          <h2 className="font-semibold text-text-primary">Líneas del Transfer</h2>
        </div>
        {transfer.lines.length === 0 ? (
          <p className="px-6 py-8 text-text-secondary text-sm text-center">Sin líneas registradas.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  {["SKU", "Despachado", "Recibido", "Discrepancia", "Condición"].map((h) => (
                    <th key={h} className="text-left px-6 py-3 text-xs font-semibold uppercase tracking-wider text-text-secondary">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {transfer.lines.map((line) => (
                  <tr key={line.id} className={cn("hover:bg-bg transition-colors", line.has_discrepancy && "bg-red-50")}>
                    <td className="px-6 py-3 font-mono text-xs font-medium">{line.sku}</td>
                    <td className="px-6 py-3">{line.quantity_dispatched}</td>
                    <td className="px-6 py-3">{line.quantity_received ?? "—"}</td>
                    <td className="px-6 py-3">
                      {line.discrepancy !== null ? (
                        <span className={cn("font-semibold", line.has_discrepancy ? "text-red-500" : "text-green-600")}>
                          {line.has_discrepancy ? `−${line.discrepancy}` : "OK"}
                        </span>
                      ) : "—"}
                    </td>
                    <td className="px-6 py-3 text-text-secondary capitalize">{line.condition ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Cancel / exception reason */}
      {(transfer.cancel_reason || transfer.exception_reason) && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">
          {transfer.cancel_reason && <p><strong>Motivo cancelación:</strong> {transfer.cancel_reason}</p>}
          {transfer.exception_reason && <p><strong>Excepción:</strong> {transfer.exception_reason}</p>}
        </div>
      )}
    </div>
  );
}
