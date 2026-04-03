"use client";

import { useState, useEffect, useCallback } from "react";
import { Store, Search, ShoppingCart, AlertTriangle, RefreshCw, Info } from "lucide-react";
import api from "@/lib/api";

// ⚠️  Solo expone price + moq — nunca source, base_price, size_multipliers internos
interface PortalCatalogItem {
  id: number;
  brand_sku_id: number;
  reference_code: string;
  description: string;
  brand_name: string;
  price: string | null;          // precio post-descuento (PricingPortalSerializer)
  moq: number | null;            // MOQ del Grade activo
  tip_type?: string;
  insole_type?: string;
  ncm?: string;
  ca_number?: string;
  is_active: boolean;
}

interface CartItem {
  sku: PortalCatalogItem;
  qty: number;
}

export function PortalCatalogTab() {
  const [items, setItems] = useState<PortalCatalogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [cart, setCart] = useState<CartItem[]>([]);
  const [showMoqInfo, setShowMoqInfo] = useState<number | null>(null);

  const fetchCatalog = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      // Portal endpoint → usa PricingPortalSerializer internamente
      const res = await api.get("/portal/catalog/");
      const raw: PortalCatalogItem[] = res.data?.results || res.data || [];
      setItems(raw.filter((i) => i.is_active));
    } catch (err) {
      setError("No se pudo cargar el catálogo. Intenta de nuevo más tarde.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchCatalog(); }, [fetchCatalog]);

  const filtered = items.filter(
    (item) =>
      !search ||
      item.reference_code.toLowerCase().includes(search.toLowerCase()) ||
      item.description.toLowerCase().includes(search.toLowerCase()) ||
      item.brand_name.toLowerCase().includes(search.toLowerCase())
  );

  // Agrupar por brand
  const byBrand = filtered.reduce<Record<string, PortalCatalogItem[]>>((acc, item) => {
    acc[item.brand_name] = acc[item.brand_name] || [];
    acc[item.brand_name].push(item);
    return acc;
  }, {});

  const addToCart = (sku: PortalCatalogItem) => {
    setCart((prev) => {
      const exists = prev.find((c) => c.sku.id === sku.id);
      if (exists) return prev.map((c) => c.sku.id === sku.id ? { ...c, qty: c.qty + 1 } : c);
      return [...prev, { sku, qty: 1 }];
    });
  };

  const cartTotal = cart.reduce(
    (sum, c) => sum + (parseFloat(c.sku.price || "0") * c.qty), 0
  );

  if (loading) {
    return (
      <div className="space-y-3 animate-pulse">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="card p-4 h-20 bg-bg-alt/40" />
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
            Precios vigentes con descuento por pronto pago aplicado · {items.length} productos
          </p>
        </div>
        <div className="flex items-center gap-2">
          {cart.length > 0 && (
            <div className="flex items-center gap-2 bg-brand/10 text-brand rounded-lg px-3 py-1.5">
              <ShoppingCart size={13} />
              <span className="text-xs font-semibold">
                {cart.length} ítem{cart.length !== 1 ? "s" : ""} · ${cartTotal.toFixed(2)}
              </span>
            </div>
          )}
          <button onClick={fetchCatalog} className="btn btn-sm btn-ghost gap-1.5 text-xs">
            <RefreshCw size={13} /> Actualizar
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="relative w-80">
        <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-tertiary" />
        <input
          type="text"
          placeholder="Buscar por referencia, descripción o marca..."
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
          <Store size={40} className="mx-auto mb-3 opacity-20" />
          <p className="text-sm">No se encontraron productos disponibles.</p>
          <p className="text-xs mt-1">Contacta a tu ejecutivo de cuenta para activar productos.</p>
        </div>
      )}

      {/* Products by brand */}
      {Object.entries(byBrand).map(([brand, skus]) => (
        <div key={brand}>
          <h3 className="text-[10px] uppercase tracking-widest text-text-tertiary font-semibold mb-2 px-1">
            {brand}
          </h3>
          <div className="card border border-border/60 overflow-hidden">
            <table className="w-full text-left">
              <thead>
                <tr className="bg-bg-alt/40">
                  <th className="px-4 py-2.5 text-[10px] uppercase text-text-tertiary font-semibold">Referencia</th>
                  <th className="px-4 py-2.5 text-[10px] uppercase text-text-tertiary font-semibold">Descripción</th>
                  <th className="px-4 py-2.5 text-[10px] uppercase text-text-tertiary font-semibold text-right">Precio (USD)</th>
                  <th className="px-4 py-2.5 text-[10px] uppercase text-text-tertiary font-semibold text-center">
                    <span className="flex items-center justify-center gap-1">
                      MOQ
                      <Info size={11} className="opacity-50" />
                    </span>
                  </th>
                  <th className="px-4 py-2.5 text-[10px] uppercase text-text-tertiary font-semibold text-right">Acción</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/30">
                {skus.map((item) => {
                  const inCart = cart.find((c) => c.sku.id === item.id);
                  const isMoqOpen = showMoqInfo === item.id;

                  return (
                    <tr key={item.id} className="hover:bg-brand/[0.02] transition-colors">
                      <td className="px-4 py-3 font-mono text-xs text-navy font-medium">
                        {item.reference_code}
                      </td>
                      <td className="px-4 py-3 text-xs text-text-secondary">
                        <div>{item.description}</div>
                        {(item.tip_type || item.insole_type) && (
                          <div className="text-[10px] text-text-tertiary mt-0.5">
                            {[item.tip_type, item.insole_type].filter(Boolean).join(" · ")}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        {item.price ? (
                          <span className="text-sm font-bold text-navy tabular-nums">
                            ${parseFloat(item.price).toFixed(2)}
                          </span>
                        ) : (
                          <span className="text-xs text-text-tertiary">A confirmar</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <div className="relative inline-block">
                          <button
                            onClick={() => setShowMoqInfo(isMoqOpen ? null : item.id)}
                            className={`text-xs font-semibold px-2.5 py-1 rounded-full transition-colors ${
                              item.moq
                                ? "bg-blue-50 text-blue-700 hover:bg-blue-100"
                                : "bg-gray-100 text-gray-500"
                            }`}
                          >
                            {item.moq ?? "—"}
                          </button>
                          {isMoqOpen && item.moq && (
                            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 bg-navy text-white text-[10px] rounded-lg p-2.5 shadow-lg z-20">
                              <p className="font-semibold mb-1">MOQ: {item.moq} pares</p>
                              <p className="opacity-80">
                                Pedido mínimo requerido para confirmar este artículo.
                              </p>
                              <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-navy" />
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => addToCart(item)}
                          disabled={!item.price}
                          className={`btn btn-sm gap-1.5 text-xs ${
                            inCart ? "btn-secondary" : "btn-primary"
                          }`}
                        >
                          <ShoppingCart size={12} />
                          {inCart ? `(${inCart.qty}) Agregar` : "Agregar"}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      ))}
    </div>
  );
}
