"use client";

import { useState, useEffect, useCallback } from "react";
import { FolderOpen, Search, Filter, ArrowRight } from "lucide-react";
import Link from "next/link";
import api from "@/lib/api";
import { useParams } from "next/navigation";
import { StateBadge } from "@/components/ui/StateBadge";

interface Expediente {
  expediente_id: string;
  brand_name: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export default function PortalPage() {
  const params = useParams();
  const lang = (params?.lang as string) || "es";
  const [expedientes, setExpedientes] = useState<Expediente[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const res = await api.get("/portal/expedientes/");
      setExpedientes(res.data?.results || []);
    } catch (err) {
      console.error("Error fetching portal data:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const filtered = expedientes.filter(e => {
    if (search && !e.expediente_id.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Mi Portal</h1>
          <p className="page-subtitle">Seguimiento de pedidos y expedientes.</p>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3 mb-6">
        <div className="relative" style={{ minWidth: 280 }}>
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: "var(--text-tertiary)" }} />
          <input
            type="text"
            placeholder="Buscar por ID de expediente..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input"
            style={{ paddingLeft: 36 }}
          />
        </div>
      </div>

      {loading ? (
        <div className="empty-state"><p>Cargando información...</p></div>
      ) : filtered.length === 0 ? (
        <div className="empty-state">
          <FolderOpen size={48} style={{ color: "var(--text-tertiary)", marginBottom: "var(--space-4)" }} />
          <p>No se encontraron expedientes activos.</p>
        </div>
      ) : (
        <div className="grid gap-4">
          <div className="card overflow-hidden">
            <table className="w-full text-left">
              <thead>
                <tr className="bg-surface-active" style={{ borderBottom: "1px solid var(--divider)" }}>
                  <th className="px-4 py-3 th-label">ID Expediente</th>
                  <th className="px-4 py-3 th-label">Estado</th>
                  <th className="px-4 py-3 th-label">Fecha Creación</th>
                  <th className="px-4 py-3 th-label">Última Actualización</th>
                  <th className="px-4 py-3 th-label text-right">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((e) => (
                  <tr key={e.expediente_id} style={{ borderBottom: "1px solid var(--divider)" }} className="hover:bg-surface-hover/50 transition-colors">
                    <td className="px-4 py-4 mono-sm">
                      {e.expediente_id.substring(0, 8).toUpperCase()}
                    </td>
                    <td className="px-4 py-4">
                      <StateBadge state={e.status as any} />
                    </td>
                    <td className="px-4 py-4 body-sm" style={{ color: "var(--text-secondary)" }}>
                      {new Date(e.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-4 body-sm" style={{ color: "var(--text-secondary)" }}>
                      {new Date(e.updated_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-4 text-right">
                      <Link 
                        href={`/${lang}/dashboard/portal/expedientes/${e.expediente_id}`}
                        className="btn btn-sm btn-ghost"
                      >
                        Ver detalles <ArrowRight size={14} className="ml-1" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
