"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import toast from "react-hot-toast";
import { ArrowLeft, Plus, Trash2, Search } from "lucide-react";

interface LegalEntityOption {
  entity_id: string;
  legal_name: string;
}

interface ProductMaster {
  id: number;
  name: string;
}

interface BrandSKU {
  id: number;
  sku_code: string;
  sizing_entry_code?: string;
  sizing_system_name?: string;
}

interface ProductLine {
  product_master_id: number | null;
  product_master_name: string;
  brand_sku_id: number | null;
  quantity: number | string;
  unit_price: number | string;
  // UI state
  brandSkus: BrandSKU[];
  loadingSkus: boolean;
  loadingPrice: boolean;
  pmQuery: string;
  pmResults: ProductMaster[];
  pmOpen: boolean;
}

const BRAND_OPTIONS = ["SKECHERS", "ON", "SPEEDO", "TOMS", "ASICS", "VIVAIA", "TECMATER"];
const MODE_OPTIONS = [
  { value: "FULL", label: "IMPORTACION / FULL" },
  { value: "COMISION", label: "COMISION" },
];
const FREIGHT_MODE_OPTIONS = ["MARITIMO", "AEREO", "TERRESTRE"];
const DISPATCH_MODE_OPTIONS = [
  { value: "MWT", label: "MWT" },
  { value: "directo", label: "Directo" },
];
const PRICE_BASIS_OPTIONS = ["CIF", "FOB", "EXW"];
const DESTINATION_OPTIONS = [
  { value: "CR", label: "Costa Rica" },
  { value: "USA", label: "United States" },
];

const MWT_LEGAL_ENTITY_ID = "MWT-CR";

function emptyLine(): ProductLine {
  return {
    product_master_id: null,
    product_master_name: "",
    brand_sku_id: null,
    quantity: "",
    unit_price: "",
    brandSkus: [],
    loadingSkus: false,
    loadingPrice: false,
    pmQuery: "",
    pmResults: [],
    pmOpen: false,
  };
}

export default function NuevoExpedientePage() {
  const router = useRouter();

  const [clients, setClients] = useState<LegalEntityOption[]>([]);
  const [clientsLoading, setClientsLoading] = useState(true);
  const [clientsError, setClientsError] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [form, setForm] = useState({
    client_id: "",
    brand: "",
    mode: "",
    freight_mode: "",
    dispatch_mode: "",
    price_basis: "",
    destination: "CR",
    notes: "",
    // S19-01 new fields
    purchase_order_number: "",
    operado_por: "" as "" | "CLIENTE" | "MWT",
  });

  const [productLines, setProductLines] = useState<ProductLine[]>([]);

  // Debounce timers per row
  const pmTimers = useRef<Record<number, ReturnType<typeof setTimeout>>>({});

  useEffect(() => {
    const fetchClients = async () => {
      try {
        setClientsLoading(true);
        setClientsError(false);
        const res = await api.get("ui/expedientes/legal-entities/");
        const entities: LegalEntityOption[] = Array.isArray(res.data)
          ? res.data
          : res.data?.results ?? [];
        setClients(entities);
      } catch {
        try {
          const res2 = await api.get("ui/expedientes/");
          const expedientes: Array<{ client_name: string; client_entity_id?: string }> =
            Array.isArray(res2.data) ? res2.data : [];
          const unique = Array.from(
            new Map(
              expedientes
                .filter((e) => e.client_entity_id)
                .map((e) => [
                  e.client_entity_id!,
                  { entity_id: e.client_entity_id!, legal_name: e.client_name },
                ])
            ).values()
          );
          if (unique.length > 0) {
            setClients(unique);
          } else {
            setClientsError(true);
            toast.error("No se pudieron cargar los clientes");
          }
        } catch {
          setClientsError(true);
          toast.error("Error al cargar clientes");
        }
      } finally {
        setClientsLoading(false);
      }
    };
    fetchClients();
  }, []);

  const handleChange = (
    e: React.ChangeEvent<HTMLSelectElement | HTMLTextAreaElement | HTMLInputElement>
  ) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  // ── Product Lines helpers ──
  const addLine = () => setProductLines((prev) => [...prev, emptyLine()]);

  const removeLine = (idx: number) =>
    setProductLines((prev) => prev.filter((_, i) => i !== idx));

  const updateLine = (idx: number, patch: Partial<ProductLine>) =>
    setProductLines((prev) =>
      prev.map((l, i) => (i === idx ? { ...l, ...patch } : l))
    );

  const handlePmQueryChange = (idx: number, query: string) => {
    updateLine(idx, { pmQuery: query, pmOpen: false, pmResults: [] });
    clearTimeout(pmTimers.current[idx]);
    if (!query.trim()) return;
    pmTimers.current[idx] = setTimeout(async () => {
      try {
        const res = await api.get(`catalog/product-masters/?search=${encodeURIComponent(query)}`);
        const results: ProductMaster[] = Array.isArray(res.data)
          ? res.data
          : res.data?.results ?? [];
        updateLine(idx, { pmResults: results, pmOpen: true });
      } catch {
        // silent
      }
    }, 300);
  };

  const selectProductMaster = async (idx: number, pm: ProductMaster) => {
    updateLine(idx, {
      product_master_id: pm.id,
      product_master_name: pm.name,
      pmQuery: pm.name,
      pmOpen: false,
      pmResults: [],
      brand_sku_id: null,
      brandSkus: [],
      loadingSkus: true,
    });
    try {
      const res = await api.get(`catalog/brand-skus/?product_master=${pm.id}`);
      const skus: BrandSKU[] = Array.isArray(res.data)
        ? res.data
        : res.data?.results ?? [];
      updateLine(idx, { brandSkus: skus, loadingSkus: false });
    } catch {
      updateLine(idx, { loadingSkus: false });
    }
  };

  const handleSkuChange = async (idx: number, skuId: string) => {
    const line = productLines[idx];
    const id = skuId ? Number(skuId) : null;
    updateLine(idx, { brand_sku_id: id, loadingPrice: true, unit_price: "" });
    if (!id || !form.client_id) {
      updateLine(idx, { loadingPrice: false });
      return;
    }
    try {
      const res = await api.get(
        `pricing/resolve/?brand_sku_id=${id}&client_id=${encodeURIComponent(form.client_id)}`
      );
      const price = res.data?.price ?? res.data?.unit_price ?? "";
      updateLine(idx, { unit_price: price, loadingPrice: false });
    } catch {
      // pricing/resolve 404 → leave empty, not blocking
      updateLine(idx, { loadingPrice: false });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (
      !form.client_id ||
      !form.brand ||
      !form.mode ||
      !form.freight_mode ||
      !form.dispatch_mode ||
      !form.price_basis
    ) {
      toast.error("Completa todos los campos obligatorios");
      return;
    }

    setSubmitting(true);
    try {
      const payload: Record<string, unknown> = {
        legal_entity_id: MWT_LEGAL_ENTITY_ID,
        client: form.client_id,
        brand: form.brand,
        mode: form.mode,
        freight_mode: form.freight_mode,
        dispatch_mode: form.dispatch_mode.toUpperCase(),
        price_basis: form.price_basis,
        destination: form.destination,
        ...(form.notes ? { notes: form.notes } : {}),
        // S19-01 new fields
        ...(form.purchase_order_number ? { purchase_order_number: form.purchase_order_number } : {}),
        ...(form.operado_por ? { operado_por: form.operado_por } : {}),
      };

      // Only send product_lines if rows exist and are valid
      const validLines = productLines.filter(
        (l) => l.product_master_id && l.quantity
      );
      if (validLines.length > 0) {
        payload.product_lines = validLines.map((l) => ({
          product_master_id: l.product_master_id,
          ...(l.brand_sku_id ? { brand_sku_id: l.brand_sku_id } : {}),
          quantity: Number(l.quantity),
          ...(l.unit_price !== "" ? { unit_price: Number(l.unit_price) } : {}),
        }));
      }

      const res = await api.post("expedientes/create/", payload);
      if (res.status === 201) {
        toast.success("Expediente creado exitosamente");
        const newId = res.data?.expediente_id || res.data?.id;
        if (newId) {
          router.push(`/expedientes/${newId}`);
        } else {
          router.push("/expedientes");
        }
      }
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string; message?: string } } };
      const msg =
        e.response?.data?.detail ||
        e.response?.data?.message ||
        "Error al crear el expediente";
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const inputCls = "w-full bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg px-3 py-2.5 text-sm text-[var(--color-text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-navy)]/30";
  const labelCls = "block text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider mb-1.5";

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <button
        onClick={() => router.back()}
        className="text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-navy)] flex items-center transition-colors"
      >
        <ArrowLeft className="w-4 h-4 mr-1" /> Volver
      </button>

      <div className="bg-[var(--color-surface)] rounded-2xl border border-[var(--color-border)] shadow-sm p-8">
        <h1 className="text-2xl font-display font-bold text-[var(--color-text-primary)] mb-1">
          Nuevo Expediente
        </h1>
        <p className="text-sm text-[var(--color-text-tertiary)] mb-8">
          Completa los datos para registrar el expediente.
        </p>

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Cliente */}
          <div>
            <label className={labelCls}>Cliente <span className="text-[var(--color-coral)]">*</span></label>
            {clientsLoading ? (
              <div className="flex items-center gap-2 h-10 px-3 bg-[var(--color-bg-alt)] border border-[var(--color-border)] rounded-lg">
                <div className="w-4 h-4 border-2 border-[var(--color-navy)] border-t-transparent rounded-full animate-spin" />
                <span className="text-sm text-[var(--color-text-tertiary)]">Cargando clientes...</span>
              </div>
            ) : clientsError ? (
              <div className="text-sm text-[var(--color-coral)] px-3 py-2 bg-[var(--color-bg-alt)] border border-[var(--color-border)] rounded-lg">
                Error al cargar clientes.{" "}
                <button type="button" className="underline" onClick={() => window.location.reload()}>Recargar</button>
              </div>
            ) : (
              <select name="client_id" value={form.client_id} onChange={handleChange} required className={inputCls}>
                <option value="">Seleccionar cliente...</option>
                {clients.map((c) => (<option key={c.entity_id} value={c.entity_id}>{c.legal_name}</option>))}
              </select>
            )}
          </div>

          {/* Marca */}
          <div>
            <label className={labelCls}>Marca <span className="text-[var(--color-coral)]">*</span></label>
            <select name="brand" value={form.brand} onChange={handleChange} required className={inputCls}>
              <option value="">Seleccionar marca...</option>
              {BRAND_OPTIONS.map((b) => (<option key={b} value={b}>{b}</option>))}
            </select>
          </div>

          {/* Modo */}
          <div>
            <label className={labelCls}>Modo <span className="text-[var(--color-coral)]">*</span></label>
            <select name="mode" value={form.mode} onChange={handleChange} required className={inputCls}>
              <option value="">Seleccionar modo...</option>
              {MODE_OPTIONS.map((m) => (<option key={m.value} value={m.value}>{m.label}</option>))}
            </select>
            {form.brand === "TECMATER" && form.mode === "COMISION" && (
              <p className="text-xs text-[var(--color-coral)] mt-1">⚠ TECMATER no soporta modo COMISION.</p>
            )}
          </div>

          {/* Destino */}
          <div>
            <label className={labelCls}>Destino <span className="text-[var(--color-coral)]">*</span></label>
            <select name="destination" value={form.destination} onChange={handleChange} required className={inputCls}>
              {DESTINATION_OPTIONS.map((d) => (<option key={d.value} value={d.value}>{d.label}</option>))}
            </select>
          </div>

          {/* Modo Flete */}
          <div>
            <label className={labelCls}>Modo de Flete <span className="text-[var(--color-coral)]">*</span></label>
            <select name="freight_mode" value={form.freight_mode} onChange={handleChange} required className={inputCls}>
              <option value="">Seleccionar modo de flete...</option>
              {FREIGHT_MODE_OPTIONS.map((f) => (<option key={f} value={f}>{f}</option>))}
            </select>
          </div>

          {/* Despacho */}
          <div>
            <label className={labelCls}>Modo de Despacho <span className="text-[var(--color-coral)]">*</span></label>
            <select name="dispatch_mode" value={form.dispatch_mode} onChange={handleChange} required className={inputCls}>
              <option value="">Seleccionar modo de despacho...</option>
              {DISPATCH_MODE_OPTIONS.map((d) => (<option key={d.value} value={d.value}>{d.label}</option>))}
            </select>
          </div>

          {/* Precio base */}
          <div>
            <label className={labelCls}>Base de Precio <span className="text-[var(--color-coral)]">*</span></label>
            <select name="price_basis" value={form.price_basis} onChange={handleChange} required className={inputCls}>
              <option value="">Seleccionar base de precio...</option>
              {PRICE_BASIS_OPTIONS.map((p) => (<option key={p} value={p}>{p}</option>))}
            </select>
          </div>

          {/* S19-01 — N° Orden de Compra */}
          <div>
            <label className={labelCls}>N° Orden de Compra <span className="text-[var(--color-text-tertiary)] font-normal">(opcional)</span></label>
            <input
              type="text"
              name="purchase_order_number"
              value={form.purchase_order_number}
              onChange={handleChange}
              placeholder="PO-2026-XXXX"
              className={inputCls}
            />
          </div>

          {/* S19-01 — Operado por */}
          <div>
            <label className={labelCls}>Operado por <span className="text-[var(--color-text-tertiary)] font-normal">(opcional)</span></label>
            <select name="operado_por" value={form.operado_por} onChange={handleChange} className={inputCls}>
              <option value="">Sin definir</option>
              <option value="CLIENTE">CLIENTE</option>
              <option value="MWT">MWT</option>
            </select>
          </div>

          {/* S19-01 — Líneas de producto */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className={labelCls + " mb-0"}>
                Líneas de producto <span className="text-[var(--color-text-tertiary)] font-normal">(opcional)</span>
              </label>
              <button
                type="button"
                onClick={addLine}
                className="flex items-center gap-1.5 text-xs bg-[var(--color-navy)] text-white rounded-lg px-3 py-1.5 hover:opacity-80 transition-opacity"
              >
                <Plus className="w-3.5 h-3.5" /> Agregar producto
              </button>
            </div>

            {productLines.length === 0 ? (
              <p className="text-xs text-[var(--color-text-tertiary)] italic px-1">
                Sin líneas de producto. Podés agregarlas ahora o después.
              </p>
            ) : (
              <div className="space-y-3">
                {productLines.map((line, idx) => (
                  <div
                    key={idx}
                    className="border border-[var(--color-border)] rounded-xl p-4 space-y-3 bg-[var(--color-bg-alt)]/30"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <span className="text-xs font-semibold text-[var(--color-text-tertiary)] mt-1">Fila {idx + 1}</span>
                      <button
                        type="button"
                        onClick={() => removeLine(idx)}
                        className="p-1 rounded hover:bg-[var(--color-bg-alt)] text-[var(--color-text-tertiary)] hover:text-[var(--color-coral)] transition-colors"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>

                    {/* ProductMaster autocomplete */}
                    <div className="relative">
                      <label className={labelCls}>Producto</label>
                      <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[var(--color-text-tertiary)]" />
                        <input
                          type="text"
                          value={line.pmQuery}
                          onChange={(e) => handlePmQueryChange(idx, e.target.value)}
                          placeholder="Buscar producto..."
                          className={inputCls + " pl-8"}
                        />
                      </div>
                      {line.pmOpen && line.pmResults.length > 0 && (
                        <ul className="absolute z-20 mt-1 w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg shadow-lg max-h-48 overflow-y-auto">
                          {line.pmResults.map((pm) => (
                            <li
                              key={pm.id}
                              onClick={() => selectProductMaster(idx, pm)}
                              className="px-4 py-2.5 text-sm text-[var(--color-text-primary)] hover:bg-[var(--color-bg-alt)] cursor-pointer"
                            >
                              {pm.name}
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>

                    {/* BrandSKU */}
                    <div>
                      <label className={labelCls}>Talla (BrandSKU)</label>
                      {line.loadingSkus ? (
                        <div className="flex items-center gap-2 h-10 px-3 bg-[var(--color-bg-alt)] border border-[var(--color-border)] rounded-lg">
                          <div className="w-3.5 h-3.5 border-2 border-[var(--color-navy)] border-t-transparent rounded-full animate-spin" />
                          <span className="text-xs text-[var(--color-text-tertiary)]">Cargando tallas...</span>
                        </div>
                      ) : line.product_master_id && line.brandSkus.length === 0 ? (
                        <p className="text-xs text-[var(--color-text-tertiary)] italic px-1 py-2">
                          Sin tallas — configurar en Brand Console &gt; Tallas
                        </p>
                      ) : (
                        <select
                          value={line.brand_sku_id ?? ""}
                          onChange={(e) => handleSkuChange(idx, e.target.value)}
                          disabled={!line.product_master_id}
                          className={inputCls}
                        >
                          <option value="">{line.product_master_id ? "Seleccionar talla..." : "Primero elegí un producto"}</option>
                          {line.brandSkus.map((sku) => (
                            <option key={sku.id} value={sku.id}>
                              {sku.sizing_system_name
                                ? `${sku.sizing_system_name} — ${sku.sizing_entry_code ?? sku.sku_code}`
                                : sku.sku_code}
                            </option>
                          ))}
                        </select>
                      )}
                    </div>

                    {/* Quantity + Price */}
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className={labelCls}>Cantidad <span className="text-[var(--color-coral)]">*</span></label>
                        <input
                          type="number"
                          min={1}
                          value={line.quantity}
                          onChange={(e) => updateLine(idx, { quantity: e.target.value })}
                          placeholder="0"
                          className={inputCls}
                        />
                      </div>
                      <div>
                        <label className={labelCls}>
                          Precio unitario
                          {line.loadingPrice && (
                            <span className="ml-1.5 text-[var(--color-text-tertiary)] font-normal">(calculando...)</span>
                          )}
                        </label>
                        <input
                          type="number"
                          min={0}
                          step="0.01"
                          value={line.unit_price}
                          onChange={(e) => updateLine(idx, { unit_price: e.target.value })}
                          placeholder="0.00"
                          className={inputCls}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Notas */}
          <div>
            <label className={labelCls}>Notas <span className="text-[var(--color-text-tertiary)] font-normal">(opcional)</span></label>
            <textarea
              name="notes"
              value={form.notes}
              onChange={handleChange}
              rows={3}
              placeholder="Observaciones adicionales..."
              className={inputCls + " resize-none"}
            />
          </div>

          {/* Submit */}
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={() => router.back()}
              className="bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-alt)] px-4 py-2 rounded-lg text-sm font-medium transition-all"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={submitting || clientsLoading}
              className="bg-[var(--color-navy)] hover:opacity-80 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all shadow-sm active:scale-95 flex items-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {submitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Creando...
                </>
              ) : (
                <><Plus size={16} /> Crear Expediente</>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
