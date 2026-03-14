"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Users2, Plus, ChevronRight, Search } from "lucide-react";
import { cn } from "@/lib/utils";

// ─── Types ────────────────────────────────────────────────────────────────────
interface Cliente {
  id: string;
  nombre: string;
  entidad_legal: string;
  pais: string;
  credito_aprobado: number;
  moneda_credito: string;
  expedientes_activos: number;
  activo: boolean;
}

export default function ClientesPage() {
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");

  useEffect(() => {
    async function fetchClientes() {
      try {
        const token = localStorage.getItem("access_token");
        const url = query
          ? `${process.env.NEXT_PUBLIC_API_URL}/api/clientes/?search=${encodeURIComponent(query)}`
          : `${process.env.NEXT_PUBLIC_API_URL}/api/clientes/`;
        const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
        if (!res.ok) throw new Error(`Error ${res.status}`);
        const data = await res.json();
        setClientes(data.results ?? data);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Error");
      } finally {
        setLoading(false);
      }
    }
    const timer = setTimeout(fetchClientes, 300);
    return () => clearTimeout(timer);
  }, [query]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-display font-bold text-navy">Clientes</h1>
          <p className="text-sm text-text-secondary mt-0.5">Empresas y personas con expedientes activos.</p>
        </div>
        <Link
          href="/clientes/nuevo"
          className="inline-flex items-center gap-2 px-4 py-2 bg-navy text-white rounded-xl text-sm font-medium hover:bg-navy-dark transition-colors"
        >
          <Plus size={16} />
          Nuevo cliente
        </Link>
      </div>

      {/* Search */}
      <div className="relative max-w-sm">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary" />
        <input
          type="text"
          placeholder="Buscar por nombre o entidad…"
          value={query}
          onChange={(e) => { setQuery(e.target.value); setLoading(true); }}
          className="w-full pl-9 pr-4 py-2 border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-mint"
        />
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm border border-border">
        {loading ? (
          <div className="p-12 text-center text-text-secondary text-sm">Cargando clientes…</div>
        ) : error ? (
          <div className="p-12 text-center text-[#DC2626] text-sm">{error}</div>
        ) : clientes.length === 0 ? (
          <div className="p-12 text-center">
            <Users2 size={40} className="mx-auto text-text-secondary opacity-40 mb-3" />
            <p className="text-text-secondary text-sm">{query ? `Sin resultados para «${query}»` : "Sin clientes registrados todavía."}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  {["Cliente", "Entidad legal", "País", "Crédito aprobado", "Exped. activos", "Estado", ""].map((h) => (
                    <th key={h} className="text-left px-6 py-3 text-xs font-semibold uppercase tracking-[0.5px] text-text-secondary">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {clientes.map((c) => (
                  <tr key={c.id} className="hover:bg-bg transition-colors">
                    <td className="px-6 py-4">
                      <p className="font-medium text-navy">{c.nombre}</p>
                    </td>
                    <td className="px-6 py-4 text-text-secondary">{c.entidad_legal}</td>
                    <td className="px-6 py-4 text-text-secondary">{c.pais}</td>
                    <td className="px-6 py-4 font-mono text-sm">
                      {c.moneda_credito} {Number(c.credito_aprobado).toLocaleString("es-CO")}
                    </td>
                    <td className="px-6 py-4 text-text-secondary">{c.expedientes_activos}</td>
                    <td className="px-6 py-4">
                      <span className={cn("px-2 py-0.5 rounded-full text-xs font-semibold",
                        c.activo ? "bg-[#F0FAF6] text-[#0E8A6D]" : "bg-bg text-text-secondary"
                      )}>
                        {c.activo ? "Activo" : "Inactivo"}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <Link href={`/clientes/${c.id}`} className="text-navy hover:text-mint transition-colors">
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
