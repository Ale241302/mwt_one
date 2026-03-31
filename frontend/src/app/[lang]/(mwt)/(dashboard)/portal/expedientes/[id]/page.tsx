"use client";

import { useState, useEffect, useCallback } from "react";
import { ArrowLeft, FileText, CheckCircle2, Package, Info } from "lucide-react";
import Link from "next/link";
import api from "@/lib/api";
import { useParams } from "next/navigation";
import { StateBadge } from "@/components/ui/StateBadge";
import { cn } from "@/lib/utils";

interface ProductLine {
  product_name: string;
  size: string;
  quantity: number;
  unit_price: number;
}

interface Artifact {
  artifact_id: string;
  artifact_type: string;
  status: string;
  created_at: string;
}

interface Expediente {
  expediente_id: string;
  status: string;
  created_at: string;
  updated_at: string;
  brand_name: string;
  is_operated_by_mwt: boolean;
  product_lines: ProductLine[];
  purchase_order_number: string;
}

export default function PortalExpedienteDetail() {
  const params = useParams();
  const lang = (params?.lang as string) || "es";
  const expedienteId = params?.id as string;
  
  const [expediente, setExpediente] = useState<Expediente | null>(null);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [expRes, artRes] = await Promise.all([
        api.get(`/portal/expedientes/${expedienteId}/`),
        api.get(`/portal/expedientes/${expedienteId}/artifacts/`),
      ]);
      setExpediente(expRes.data);
      setArtifacts(artRes.data || []);
    } catch (err) {
      console.error("Error fetching expediente detail:", err);
    } finally {
      setLoading(false);
    }
  }, [expedienteId]);

  useEffect(() => {
    if (expedienteId) fetchData();
  }, [expedienteId, fetchData]);

  if (loading) return <div className="empty-state">Cargando...</div>;
  if (!expediente) return <div className="empty-state">Expediente no encontrado.</div>;

  const basePath = `/${lang}/dashboard/portal`;

  return (
    <div className="max-w-4xl mx-auto py-6 px-4">
      <Link href={basePath} className="btn btn-ghost btn-sm mb-6">
        <ArrowLeft size={16} className="mr-2" /> Volver al portal
      </Link>

      <div className="card mb-6 overflow-hidden">
        {expediente.is_operated_by_mwt && (
          <div className="bg-primary/5 border-b border-primary/10 px-6 py-2 flex items-center gap-2">
            <CheckCircle2 size={14} className="text-primary" />
            <span className="caption font-bold text-primary">Operado logísticamente por Muito Work</span>
          </div>
        )}
        <div className="flex flex-wrap items-center justify-between gap-4 p-6">
          <div>
            <h1 className="body-lg font-bold mono" style={{ color: "var(--text-primary)" }}>
              EXPEDIENTE {expediente.expediente_id.substring(0, 8).toUpperCase()}
            </h1>
            <p className="body-sm text-secondary">
              Iniciado el {new Date(expediente.created_at).toLocaleDateString()}
              {expediente.purchase_order_number && (
                <span className="ml-3 px-2 py-0.5 bg-bg rounded border border-divider text-xs font-mono">
                  PO: {expediente.purchase_order_number}
                </span>
              )}
            </p>
          </div>
          <StateBadge state={expediente.status as any} />
        </div>
      </div>

      <div className="space-y-8">
        {/* Productos Section */}
        <section>
          <div className="flex items-center gap-2 mb-4">
            <Package size={20} className="text-secondary" />
            <h2 className="heading-sm font-bold">Detalle de Productos</h2>
          </div>
          <div className="card overflow-hidden">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-bg border-b border-divider">
                  <th className="px-4 py-3 caption font-bold text-secondary">Producto</th>
                  <th className="px-4 py-3 caption font-bold text-secondary text-center">Talla</th>
                  <th className="px-4 py-3 caption font-bold text-secondary text-center">Cant.</th>
                  <th className="px-4 py-3 caption font-bold text-secondary text-right">Precio Unit.</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-divider">
                {expediente.product_lines?.length > 0 ? (
                  expediente.product_lines.map((line, i) => (
                    <tr key={i} className="hover:bg-surface-hover transition-colors">
                      <td className="px-4 py-3 body-sm font-medium">{line.product_name}</td>
                      <td className="px-4 py-3 body-sm text-center font-mono">{line.size}</td>
                      <td className="px-4 py-3 body-sm text-center">{line.quantity}</td>
                      <td className="px-4 py-3 body-sm text-right font-mono">${line.unit_price}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={4} className="px-4 py-8 text-center text-secondary italic">
                      No hay líneas de producto registradas.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        {/* Documentos Section */}
        <section>
          <div className="flex items-center gap-2 mb-4">
            <FileText size={20} className="text-secondary" />
            <h2 className="heading-sm font-bold">Documentación Relacionada</h2>
          </div>
          
          <div className="grid gap-3">
            {artifacts.length === 0 ? (
              <div className="card p-8 text-center text-secondary">
                <Info size={32} className="mx-auto mb-3 opacity-20" />
                <p>No hay documentos públicos disponibles actualmente.</p>
              </div>
            ) : (
              artifacts.map((art) => (
                <div key={art.artifact_id} className="card p-4 flex items-center justify-between hover:bg-surface-hover transition-colors">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-full bg-surface border border-divider flex items-center justify-center text-text-secondary">
                      <FileText size={20} />
                    </div>
                    <div>
                      <p className="body-sm font-bold">{art.artifact_type}</p>
                      <p className="body-xs text-secondary">
                        Actualizado el {new Date(art.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={cn(
                      "badge",
                      art.status === "COMPLETED" || art.status === "APPROVED" ? "badge-success" : 
                      art.status === "DRAFT" || art.status === "PENDING" ? "badge-warning" : "badge-neutral"
                    )}>
                      {art.status}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
