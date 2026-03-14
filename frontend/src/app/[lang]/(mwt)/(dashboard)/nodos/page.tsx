"use client";

import { useState, useEffect } from "react";
import { Network, Plus, ChevronRight } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { cn } from "@/lib/utils";
import api from "@/lib/api";

// ─── Types ────────────────────────────────────────────────────────────────────
interface Nodo {
  id: string;
  nombre: string;
  tipo: string;
  pais: string;
  ciudad: string;
  activo: boolean;
  expedientes_activos?: number;
}

const TIPO_COLORS: Record<string, string> = {
  ORIGEN:    "bg-[#EFF6FF] text-[#1D4ED8]",
  DESTINO:   "bg-[#F0FAF6] text-[#0E8A6D]",
  INTERMEDIO: "bg-[#FFF7ED] text-[#B45309]",
};

export default function NodosPage() {
  const { lang } = useParams<{ lang: string }>();
  const [nodos, setNodos] = useState<Nodo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchNodos() {
      try {
        const res = await api.get("core/nodes/");
        const data = res.data;
        setNodos(data.results ?? data);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Error");
      } finally {
        setLoading(false);
      }
    }
    fetchNodos();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-display font-bold text-navy">Nodos</h1>
          <p className="text-sm text-text-secondary mt-0.5">Puntos de origen, destino e intermedios de la red logística.</p>
        </div>
        <Link
          href={`/${lang}/nodos/nuevo`}
          className="inline-flex items-center gap-2 px-4 py-2 bg-navy text-white rounded-xl text-sm font-medium hover:bg-navy-dark transition-colors"
        >
          <Plus size={16} />
          Nuevo nodo
        </Link>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-border">
        {loading ? (
          <div className="p-12 text-center text-text-secondary text-sm">Cargando nodos…</div>
        ) : error ? (
          <div className="p-12 text-center text-[#DC2626] text-sm">{error}</div>
        ) : nodos.length === 0 ? (
          <div className="p-12 text-center">
            <Network size={40} className="mx-auto text-text-secondary opacity-40 mb-3" />
            <p className="text-text-secondary text-sm">Sin nodos registrados todavía.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  {["Nombre", "Tipo", "País / Ciudad", "Expedientes activos", "Estado", ""].map((h) => (
                    <th key={h} className="text-left px-6 py-3 text-xs font-semibold uppercase tracking-[0.5px] text-text-secondary">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {nodos.map((n) => (
                  <tr key={n.id} className="hover:bg-bg transition-colors">
                    <td className="px-6 py-4 font-medium text-navy">{n.nombre}</td>
                    <td className="px-6 py-4">
                      <span className={cn("px-2 py-0.5 rounded-full text-xs font-semibold", TIPO_COLORS[n.tipo] ?? "bg-bg text-text-secondary")}>
                        {n.tipo}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-text-secondary">{n.pais} / {n.ciudad}</td>
                    <td className="px-6 py-4 text-text-secondary">{n.expedientes_activos ?? 0}</td>
                    <td className="px-6 py-4">
                      <span className={cn("px-2 py-0.5 rounded-full text-xs font-semibold", n.activo ? "bg-[#F0FAF6] text-[#0E8A6D]" : "bg-bg text-text-secondary")}>
                        {n.activo ? "Activo" : "Inactivo"}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <Link href={`/${lang}/nodos/${n.id}`} className="text-navy hover:text-mint transition-colors">
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
