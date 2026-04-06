"use client";

import { useState, useEffect, useCallback } from "react";
import { Box, ChevronDown, ChevronRight, RefreshCw, Search, AlertTriangle } from "lucide-react";
import api from "@/lib/api";
import { SizeMultipliersExpand } from "@/components/catalog/SizeMultipliersExpand";

interface GradeConstraint {
  grade_label: string;
  moq_total: number;
  size_multipliers: Record<string, number> | null;
}

interface PriceResolved {
  price: string | null;
  source: string | null;
  base_price: string | null;
  grade_moq: number | null;
  size_multipliers: Record<string, number> | null;
  grade_label: string | null;
  pricelist_version: string | null;
}

interface BrandSKU {
  id: number;
  sku_code: string;
  reference_code: string;
  description: string;
  tip_type?: string;
  insole_type?: string;
  is_active: boolean;
  price_resolved?: PriceResolved;
}

interface GroupedProduct {
  product_key: string;
  description: string;
  skus: BrandSKU[];
}

export function CatalogTab({ brandId }: { brandId?: number }) {
  const [products, setProducts] = useState<GroupedProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [expandedSizes, setExpandedSizes] = useState<Set<number>>(new Set());
  const [error, setError] = useState<string | null>(null);

  const fetchCatalog = useCallback(async () => {
    if (!brandId) {
      setLoading(false);
      setError("No se ha seleccionado una marca.");
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const res = await api.get(`/pricing/catalog/brand-skus/?brand_id=${brandId}`);
      const raw: BrandSKU[] = res.data?.results || res.data || [];

      // Group by product_key (reference_code prefix before last 2 chars)
      const grouped: Record<string, GroupedProduct> = {};
      raw.forEach((sku) => {
        const key = sku.reference_code?.slice(0, -2) || sku.reference_code || "SIN_GRUPO";
        if (!grouped[key]) {
          grouped[key] = { product_key: key, description: sku.description, skus: [] };
        }
        grouped[key].skus.push(sku);
      });
      setProducts(Object.values(grouped));
    } catch (err) {
      setError("No se pudo cargar el catálogo. Verifica que el endpoint /pricing/catalog/brand-skus/ esté disponible.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [brandId]);

  useEffect(() => { fetchCatalog(); }, [fetchCatalog]);

  const toggleProduct = (key: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
  };

  const toggleSizes = (skuId: number) => {
    setExpandedSizes((prev) => {
      const next = new Set(prev);
      next.has(skuId) ? next.delete(skuId) : next.add(skuId);
      return next;
    });
  };

  const sourceLabel: Record<string, string> = {
    assignment: "CPA",
    agreement: "Acuerdo",
    pricelist_grade: "Pricelist Grade",
    pricelist_legacy: "Pricelist v1",
    manual: "Manual",
  };

  const sourceColor: Record<string, string> = {
    assignment: "bg-blue-100 text-blue-700",
    agreement: "bg-purple-100 text-purple-700",
    pricelist_grade: "bg-green-100 text-green-700",
    pricelist_legacy: "bg-yellow-100 text-yellow-700",
    manual: "bg-gray-100 text-gray-600",
  };

  const filtered = products.filter((p) =>
    !search ||
    p.product_key.toLowerCase().includes(search.toLowerCase()) ||
    p.description.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) {
    return (
      <div className="space-y-3 animate-pulse">
        {[1, 2, 3].map((i) => (
          <div key={i} className="card p-4 h-14 bg-bg-alt/40" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-semibold text-navy text-sm">Catálogo de Productos</h2>
          <p className="text-xs text-text-tertiary mt-0.5">
            {products.length} grupos · Precio base, MOQ y tallas disponibles
          </p>
        </div>
        <button
          onClick={fetchCatalog}
          className="btn btn-sm btn-ghost gap-1.5 text-xs"
        >
          <RefreshCw size={13} /> Actualizar
        </button>
      </div>

      {/* Search */}
      <div className="relative w-80">
        <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-tertiary" />
        <input
          type="text"
          placeholder="Buscar referencia o descripción..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="input pl-9 text-xs w-full"
        />
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-xs text-yellow-700">
          <AlertTriangle size={14} />
          {error}
        </div>
      )}

      {filtered.length === 0 && !error && (
        <div className="card p-12 text-center text-text-tertiary">
          <Box size={40} className="mx-auto mb-3 opacity-20" />
          <p className="text-sm">No se encontraron productos.</p>
        </div>
      )}

      {/* Product Groups */}
      <div className="space-y-2">
        {filtered.map((group) => {
          const isOpen = expanded.has(group.product_key);
          const minPrice = group.skus
            .map((s) => parseFloat(s.price_resolved?.price || "0"))
            .filter(Boolean);
          const displayPrice = minPrice.length > 0 ? Math.min(...minPrice) : null;
          const totalSKUs = group.skus.length;
          const activeSKUs = group.skus.filter((s) => s.is_active).length;

          return (
            <div key={group.product_key} className="card border border-border/60 overflow-hidden">
              {/* Group Header */}
              <button
                onClick={() => toggleProduct(group.product_key)}
                className="w-full flex items-center gap-3 px-4 py-3.5 hover:bg-navy/[0.02] transition-colors text-left"
              >
                <span className="text-text-tertiary">
                  {isOpen ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-semibold text-navy">
                      {group.product_key}
                    </span>
                    <span className="text-xs text-text-tertiary truncate">{group.description}</span>
                  </div>
                </div>
                {/* Summary columns */}
                <div className="flex items-center gap-6 shrink-0">
                  <div className="text-right">
                    <p className="text-[10px] text-text-tertiary uppercase tracking-wide">Precio base</p>
                    <p className="text-xs font-semibold text-navy">
                      {displayPrice ? `$${displayPrice.toFixed(2)}` : <span className="text-text-tertiary">—</span>}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-[10px] text-text-tertiary uppercase tracking-wide">SKUs</p>
                    <p className="text-xs font-semibold text-navy">
                      {activeSKUs}<span className="text-text-tertiary font-normal">/{totalSKUs}</span>
                    </p>
                  </div>
                </div>
              </button>

              {/* SKU Rows */}
              {isOpen && (
                <div className="border-t border-border/40">
                  <table className="w-full text-left">
                    <thead>
                      <tr className="bg-bg-alt/40">
                        <th className="px-4 py-2 text-[10px] uppercase text-text-tertiary font-semibold">Referencia</th>
                        <th className="px-4 py-2 text-[10px] uppercase text-text-tertiary font-semibold">Descripción</th>
                        <th className="px-4 py-2 text-[10px] uppercase text-text-tertiary font-semibold">Precio Base</th>
                        <th className="px-4 py-2 text-[10px] uppercase text-text-tertiary font-semibold">Grade / MOQ</th>
                        <th className="px-4 py-2 text-[10px] uppercase text-text-tertiary font-semibold">Fuente</th>
                        <th className="px-4 py-2 text-[10px] uppercase text-text-tertiary font-semibold">Tallas</th>
                        <th className="px-4 py-2 text-[10px] uppercase text-text-tertiary font-semibold">Estado</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/30">
                      {group.skus.map((sku) => {
                        const pr = sku.price_resolved;
                        const hasSizes =
                          pr?.size_multipliers && Object.keys(pr.size_multipliers).length > 0;
                        const isSizeOpen = expandedSizes.has(sku.id);

                        return (
                          <>
                            <tr
                              key={sku.id}
                              className="hover:bg-navy/[0.02] transition-colors"
                            >
                              <td className="px-4 py-3 font-mono text-xs text-navy">{sku.reference_code}</td>
                              <td className="px-4 py-3 text-xs text-text-secondary max-w-[200px] truncate">
                                {sku.description}
                              </td>
                              <td className="px-4 py-3 text-xs font-semibold text-navy tabular-nums">
                                {pr?.price ? `$${parseFloat(pr.price).toFixed(2)}` : <span className="text-text-tertiary">—</span>}
                              </td>
                              <td className="px-4 py-3 text-xs text-text-secondary">
                                {pr?.grade_label ? (
                                  <div>
                                    <span className="font-medium">{pr.grade_label}</span>
                                    {pr.grade_moq && (
                                      <span className="ml-1 text-text-tertiary">· MOQ {pr.grade_moq}</span>
                                    )}
                                  </div>
                                ) : <span className="text-text-tertiary">—</span>}
                              </td>
                              <td className="px-4 py-3">
                                {pr?.source ? (
                                  <span
                                    className={`inline-flex px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                                      sourceColor[pr.source] || "bg-gray-100 text-gray-600"
                                    }`}
                                  >
                                    {sourceLabel[pr.source] || pr.source}
                                  </span>
                                ) : <span className="text-text-tertiary text-xs">—</span>}
                              </td>
                              <td className="px-4 py-3">
                                {hasSizes ? (
                                  <button
                                    onClick={() => toggleSizes(sku.id)}
                                    className="flex items-center gap-1 text-xs text-mint hover:underline"
                                  >
                                    {isSizeOpen ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                                    {Object.keys(pr!.size_multipliers!).length} tallas
                                  </button>
                                ) : (
                                  <span className="text-text-tertiary text-xs">—</span>
                                )}
                              </td>
                              <td className="px-4 py-3">
                                <span
                                  className={`inline-flex px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                                    sku.is_active
                                      ? "bg-green-100 text-green-700"
                                      : "bg-gray-100 text-gray-500"
                                  }`}
                                >
                                  {sku.is_active ? "Activo" : "Inactivo"}
                                </span>
                              </td>
                            </tr>
                            {isSizeOpen && hasSizes && (
                              <tr key={`${sku.id}-sizes`}>
                                <td colSpan={7} className="px-4 py-0 bg-bg-alt/30">
                                    <SizeMultipliersExpand
                                      sizeMultipliers={pr?.size_multipliers || {}}
                                      gradeLabel={pr?.grade_label}
                                      moqTotal={pr?.grade_moq || undefined}
                                      gradePriceUsd={pr?.price}
                                    />
                                </td>
                              </tr>
                            )}
                          </>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
