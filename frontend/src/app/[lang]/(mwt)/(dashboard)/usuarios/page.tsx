"use client";

import { useState, useEffect } from "react";
import { Users, Search, ShieldCheck, ShieldAlert } from "lucide-react";
import { cn } from "@/lib/utils";
import api from "@/lib/api";

// Types
interface MWTUser {
  id: string;
  username: string;
  email: string;
  nombre: string;
  apellido: string;
  rol: "CEO" | "ADMIN" | "OPERADOR" | "VIEWER";
  permisos: string[];
  activo: boolean;
  ultimo_acceso?: string;
  fecha_creacion: string;
}

const ROL_CONFIG: Record<string, { classes: string; icon: React.ReactNode }> = {
  CEO:      { classes: "bg-[#FDF4FF] text-[#7E22CE]", icon: <ShieldCheck size={12} /> },
  ADMIN:    { classes: "bg-[#EFF6FF] text-[#1D4ED8]", icon: <ShieldCheck size={12} /> },
  OPERADOR: { classes: "bg-[#F0FAF6] text-[#0E8A6D]", icon: <ShieldAlert size={12} /> },
  VIEWER:   { classes: "bg-bg text-text-secondary",    icon: <ShieldAlert size={12} /> },
};

function RolBadge({ rol }: { rol: string }) {
  const cfg = ROL_CONFIG[rol] ?? ROL_CONFIG["VIEWER"];
  return (
    <span className={cn("inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold", cfg.classes)}>
      {cfg.icon} {rol}
    </span>
  );
}

export default function UsuariosPage() {
  const [usuarios, setUsuarios] = useState<MWTUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");

  useEffect(() => {
    async function fetchUsuarios() {
      try {
        const url = query
          ? `admin/users/?search=${encodeURIComponent(query)}`
          : `admin/users/`;
        const res = await api.get(url);
        const data = res.data;
        setUsuarios(data.results ?? data);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Error");
      } finally {
        setLoading(false);
      }
    }
    const timer = setTimeout(fetchUsuarios, 300);
    return () => clearTimeout(timer);
  }, [query]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-display font-bold text-navy">Usuarios</h1>
          <p className="text-sm text-text-secondary mt-0.5">Miembros del equipo y sus permisos.</p>
        </div>
      </div>

      {/* Search */}
      <div className="relative max-w-sm">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary" />
        <input
          type="text"
          placeholder="Buscar por nombre, email o username..."
          value={query}
          onChange={(e) => { setQuery(e.target.value); setLoading(true); }}
          className="w-full pl-9 pr-4 py-2 border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-mint"
        />
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-border">
        {loading ? (
          <div className="p-12 text-center text-text-secondary text-sm">Cargando usuarios...</div>
        ) : error ? (
          <div className="p-12 text-center text-[#DC2626] text-sm">{error}</div>
        ) : usuarios.length === 0 ? (
          <div className="p-12 text-center">
            <Users size={40} className="mx-auto text-text-secondary opacity-40 mb-3" />
            <p className="text-text-secondary text-sm">{query ? `Sin resultados para ${query}` : "Sin usuarios registrados."}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  {["Usuario", "Email", "Rol", "Permisos", "Ultimo acceso", "Estado"].map((h) => (
                    <th key={h} className="text-left px-6 py-3 text-xs font-semibold uppercase tracking-[0.5px] text-text-secondary">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {usuarios.map((u) => (
                  <tr key={u.id} className="hover:bg-bg transition-colors">
                    <td className="px-6 py-4">
                      <p className="font-medium text-navy">{u.nombre} {u.apellido}</p>
                      <p className="text-xs text-text-secondary">@{u.username}</p>
                    </td>
                    <td className="px-6 py-4 text-text-secondary">{u.email}</td>
                    <td className="px-6 py-4"><RolBadge rol={u.rol} /></td>
                    <td className="px-6 py-4">
                      <div className="flex flex-wrap gap-1">
                        {(u.permisos ?? []).slice(0, 3).map((p) => (
                          <span key={p} className="px-1.5 py-0.5 bg-bg rounded text-[10px] font-mono text-text-secondary">{p}</span>
                        ))}
                        {(u.permisos ?? []).length > 3 && (
                          <span className="px-1.5 py-0.5 bg-bg rounded text-[10px] text-text-secondary">+{u.permisos.length - 3}</span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-text-secondary text-xs">
                      {u.ultimo_acceso ? new Date(u.ultimo_acceso).toLocaleString("es-CO", { dateStyle: "short", timeStyle: "short" }) : "Nunca"}
                    </td>
                    <td className="px-6 py-4">
                      <span className={cn("px-2 py-0.5 rounded-full text-xs font-semibold",
                        u.activo ? "bg-[#F0FAF6] text-[#0E8A6D]" : "bg-[#FEF2F2] text-[#DC2626]"
                      )}>
                        {u.activo ? "Activo" : "Inactivo"}
                      </span>
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
