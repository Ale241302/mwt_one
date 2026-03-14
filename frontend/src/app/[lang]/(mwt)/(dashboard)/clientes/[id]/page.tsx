"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Mail, Phone, Globe, CreditCard, FolderOpen, Building2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface ClienteDetalle {
  id: string;
  nombre: string;
  entidad_legal: string;
  pais: string;
  ciudad?: string;
  email?: string;
  telefono?: string;
  sitio_web?: string;
  credito_aprobado: number;
  credito_utilizado: number;
  moneda_credito: string;
  activo: boolean;
  expedientes_activos: Array<{
    id: string;
    referencia: string;
    estado: string;
    fecha_creacion: string;
  }>;
}

export default function ClienteDetallePage() {
  const { id } = useParams() as { id: string };
  const router = useRouter();
  const [cliente, setCliente] = useState<ClienteDetalle | null>(null);
  const [loading, setLoading] = useState(true);

  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : "";
  const BASE = process.env.NEXT_PUBLIC_API_URL;

  const fetchCliente = useCallback(async () => {
    try {
      const res = await fetch(`${BASE}/api/clientes/${id}/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`Error ${res.status}`);
      setCliente(await res.json());
    } catch {
      setCliente(null);
    } finally {
      setLoading(false);
    }
  }, [id, token, BASE]);

  useEffect(() => { fetchCliente(); }, [fetchCliente]);

  const creditoPct = cliente
    ? Math.min(100, Math.round((cliente.credito_utilizado / Math.max(cliente.credito_aprobado, 1)) * 100))
    : 0;

  return (
    <div className="space-y-6">
      <div>
        <button onClick={() => router.back()} className="flex items-center gap-1 text-sm text-text-secondary hover:text-navy mb-3">
          <ArrowLeft size={14} /> Volver a clientes
        </button>
        {loading ? (
          <div className="h-8 w-48 bg-bg rounded animate-pulse" />
        ) : (
          <h1 className="text-2xl font-display font-bold text-navy">{cliente?.nombre ?? "Cliente"}</h1>
        )}
      </div>

      {!loading && cliente && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Info card */}
          <div className="lg:col-span-1 space-y-4">
            <div className="bg-white rounded-xl border border-border p-5">
              <h2 className="text-sm font-semibold text-navy mb-4 flex items-center gap-2">
                <Building2 size={16} /> Información
              </h2>
              <dl className="space-y-3 text-sm">
                <div>
                  <dt className="text-xs text-text-secondary uppercase tracking-[0.5px]">Entidad legal</dt>
                  <dd className="font-medium text-navy mt-0.5">{cliente.entidad_legal}</dd>
                </div>
                <div>
                  <dt className="text-xs text-text-secondary uppercase tracking-[0.5px]">País / Ciudad</dt>
                  <dd className="text-text mt-0.5">{cliente.pais}{cliente.ciudad ? ` / ${cliente.ciudad}` : ""}</dd>
                </div>
                {cliente.email && (
                  <div className="flex items-center gap-2 text-text">
                    <Mail size={14} className="text-text-secondary" />
                    <a href={`mailto:${cliente.email}`} className="hover:text-mint">{cliente.email}</a>
                  </div>
                )}
                {cliente.telefono && (
                  <div className="flex items-center gap-2 text-text">
                    <Phone size={14} className="text-text-secondary" />
                    <span>{cliente.telefono}</span>
                  </div>
                )}
                {cliente.sitio_web && (
                  <div className="flex items-center gap-2">
                    <Globe size={14} className="text-text-secondary" />
                    <a href={cliente.sitio_web} target="_blank" rel="noreferrer" className="text-navy hover:text-mint">{cliente.sitio_web}</a>
                  </div>
                )}
              </dl>
            </div>

            {/* Credit card */}
            <div className="bg-white rounded-xl border border-border p-5">
              <h2 className="text-sm font-semibold text-navy mb-4 flex items-center gap-2">
                <CreditCard size={16} /> Línea de crédito
              </h2>
              <p className="text-xs text-text-secondary mb-1">
                Utilizado: {cliente.moneda_credito} {Number(cliente.credito_utilizado).toLocaleString("es-CO")} / {Number(cliente.credito_aprobado).toLocaleString("es-CO")}
              </p>
              <div className="w-full bg-bg rounded-full h-2 overflow-hidden">
                <div
                  className={cn("h-2 rounded-full transition-all", creditoPct >= 90 ? "bg-[#DC2626]" : creditoPct >= 70 ? "bg-[#B45309]" : "bg-mint")}
                  style={{ width: `${creditoPct}%` }}
                />
              </div>
              <p className={cn("text-xs mt-1 font-semibold", creditoPct >= 90 ? "text-[#DC2626]" : "text-text-secondary")}>
                {creditoPct}% utilizado
              </p>
            </div>
          </div>

          {/* Expedientes activos */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl border border-border">
              <div className="px-6 py-4 border-b border-border">
                <h2 className="text-sm font-semibold text-navy flex items-center gap-2">
                  <FolderOpen size={16} /> Expedientes activos ({cliente.expedientes_activos.length})
                </h2>
              </div>
              {cliente.expedientes_activos.length === 0 ? (
                <div className="p-8 text-center text-text-secondary text-sm">Sin expedientes activos.</div>
              ) : (
                <div className="divide-y divide-border">
                  {cliente.expedientes_activos.map((exp) => (
                    <div key={exp.id} className="flex items-center justify-between px-6 py-3 hover:bg-bg transition-colors">
                      <div>
                        <p className="text-sm font-medium text-navy">{exp.referencia}</p>
                        <p className="text-xs text-text-secondary">{new Date(exp.fecha_creacion).toLocaleDateString("es-CO")}</p>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-bg text-text-secondary">{exp.estado}</span>
                        <Link href={`/expedientes/${exp.id}`} className="text-navy hover:text-mint transition-colors">
                          <ArrowLeft size={14} className="rotate-180" />
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
