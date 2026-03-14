"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Building2, Plus, Globe, Package } from "lucide-react";
import { cn } from "@/lib/utils";

// ─── Types ────────────────────────────────────────────────────────────────────
interface Brand {
  id: string;
  nombre: string;
  slug: string;
  mercados: string[];
  expedientes_activos: number;
  estado: "ACTIVA" | "INACTIVA" | "PAUSADA";
  logo_url?: string;
  descripcion?: string;
}

const ESTADO_CONFIG: Record<string, { classes: string }> = {
  ACTIVA:   { classes: "bg-[#F0FAF6] text-[#0E8A6D]" },
  PAUSADA:  { classes: "bg-[#FFF7ED] text-[#B45309]" },
  INACTIVA: { classes: "bg-bg text-text-secondary" },
};

function BrandCard({ brand }: { brand: Brand }) {
  const cfg = ESTADO_CONFIG[brand.estado] ?? ESTADO_CONFIG["INACTIVA"];
  return (
    <Link
      href={`/brands/${brand.id}`}
      className="bg-white rounded-xl border border-border p-5 hover:shadow-md hover:border-mint transition-all group"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          {brand.logo_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={brand.logo_url} alt={brand.nombre} className="w-10 h-10 rounded-lg object-cover" />
          ) : (
            <div className="w-10 h-10 rounded-lg bg-bg flex items-center justify-center">
              <Building2 size={20} className="text-text-secondary" />
            </div>
          )}
          <div>
            <p className="font-semibold text-navy group-hover:text-mint transition-colors">{brand.nombre}</p>
            <p className="text-xs text-text-secondary">/{brand.slug}</p>
          </div>
        </div>
        <span className={cn("px-2 py-0.5 rounded-full text-xs font-semibold", cfg.classes)}>
          {brand.estado}
        </span>
      </div>

      {brand.descripcion && (
        <p className="text-xs text-text-secondary mb-3 line-clamp-2">{brand.descripcion}</p>
      )}

      <div className="flex items-center gap-4 text-xs text-text-secondary">
        <span className="flex items-center gap-1">
          <Globe size={12} />
          {brand.mercados.length > 0 ? brand.mercados.join(", ") : "Sin mercados"}
        </span>
        <span className="flex items-center gap-1">
          <Package size={12} />
          {brand.expedientes_activos} expedientes
        </span>
      </div>
    </Link>
  );
}

export default function BrandsPage() {
  const [brands, setBrands] = useState<Brand[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filtro, setFiltro] = useState<"TODAS" | "ACTIVA" | "PAUSADA" | "INACTIVA">("TODAS");

  useEffect(() => {
    async function fetchBrands() {
      try {
        const token = localStorage.getItem("access_token");
        const url = filtro !== "TODAS"
          ? `${process.env.NEXT_PUBLIC_API_URL}/api/brands/?estado=${filtro}`
          : `${process.env.NEXT_PUBLIC_API_URL}/api/brands/`;
        const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
        if (!res.ok) throw new Error(`Error ${res.status}`);
        const data = await res.json();
        setBrands(data.results ?? data);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Error");
      } finally {
        setLoading(false);
      }
    }
    fetchBrands();
  }, [filtro]);

  const FILTER_OPTIONS: Array<typeof filtro> = ["TODAS", "ACTIVA", "PAUSADA", "INACTIVA"];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-display font-bold text-navy">Brands</h1>
          <p className="text-sm text-text-secondary mt-0.5">Marcas comerciales gestionadas por MWT.</p>
        </div>
        <Link
          href="/brands/nueva"
          className="inline-flex items-center gap-2 px-4 py-2 bg-navy text-white rounded-xl text-sm font-medium hover:bg-navy-dark transition-colors"
        >
          <Plus size={16} />
          Nueva brand
        </Link>
      </div>

      {/* Filter pills */}
      <div className="flex flex-wrap gap-2">
        {FILTER_OPTIONS.map((f) => (
          <button
            key={f}
            onClick={() => { setFiltro(f); setLoading(true); }}
            className={cn(
              "px-3 py-1 rounded-full text-xs font-semibold transition-colors",
              filtro === f ? "bg-navy text-white" : "bg-white border border-border text-text-secondary hover:border-navy"
            )}
          >
            {f === "TODAS" ? "Todas" : f.charAt(0) + f.slice(1).toLowerCase()}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-36 bg-bg rounded-xl animate-pulse" />
          ))}
        </div>
      ) : error ? (
        <div className="p-12 text-center text-[#DC2626] text-sm">{error}</div>
      ) : brands.length === 0 ? (
        <div className="p-12 text-center bg-white rounded-xl border border-border">
          <Building2 size={40} className="mx-auto text-text-secondary opacity-40 mb-3" />
          <p className="text-text-secondary text-sm">Sin brands registradas todavía.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {brands.map((b) => <BrandCard key={b.id} brand={b} />)}
        </div>
      )}
    </div>
  );
}
