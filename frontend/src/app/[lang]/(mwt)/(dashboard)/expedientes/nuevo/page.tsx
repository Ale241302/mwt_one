"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import toast from "react-hot-toast";
import { ArrowLeft, Plus, X } from "lucide-react";

interface ClienteOption {
  id: number;
  name: string;
  legal_entity_name?: string | null;
}

interface BrandOption {
  id: number;
  name: string;
  slug: string;
}

interface Producto {
  id: number;
  name: string;
  sku_base: string;
  brand_name?: string;
}

interface ProductLine {
  producto_id: number | null;
  quantity: string;
}

const MODE_OPTIONS = [
  { value: "FULL", label: "IMPORTACION / FULL" },
  { value: "COMISION", label: "COMISION" },
];
const FREIGHT_MODE_OPTIONS = [
  { value: "MARITIMO", label: "Mar\u00edtimo" },
  { value: "AEREO", label: "A\u00e9reo" },
  { value: "TERRESTRE", label: "Terrestre" },
];
const DISPATCH_MODE_OPTIONS = [
  { value: "MWT", label: "MWT" },
  { value: "DIRECTO", label: "Directo" },
];
const PRICE_BASIS_OPTIONS = [
  { value: "CIF", label: "CIF" },
  { value: "FOB", label: "FOB" },
  { value: "EXW", label: "EXW" },
];
const DESTINATION_OPTIONS = [
  { value: "CR", label: "Costa Rica" },
  { value: "USA", label: "United States" },
];

const MWT_LEGAL_ENTITY_ID = "MWT-CR";

const emptyLine = (): ProductLine => ({ producto_id: null, quantity: "" });

export default function NuevoExpedientePage() {
  const router = useRouter();

  const [clients, setClients] = useState<ClienteOption[]>([]);
  const [clientsLoading, setClientsLoading] = useState(true);
  const [brands, setBrands] = useState<BrandOption[]>([]);
  const [brandsLoading, setBrandsLoading] = useState(true);
  const [productos, setProductos] = useState<Producto[]>([]);
  const [productosLoading, setProductosLoading] = useState(true);
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
    purchase_order_number: "",
    operado_por: "" as "" | "CLIENTE" | "MWT",
  });

  const [productLines, setProductLines] = useState<ProductLine[]>([emptyLine()]);

  useEffect(() => {
    api
      .get("clientes/?limit=500")
      .then((res) => {
        const data: ClienteOption[] = Array.isArray(res.data) ? res.data : res.data?.results ?? [];
        setClients(data);
      })
      .catch(() => toast.error("Error al cargar clientes"))
      .finally(() => setClientsLoading(false));
  }, []);

  useEffect(() => {
    api
      .get("brands/?limit=200")
      .then((res) => {
        const data: BrandOption[] = Array.isArray(res.data) ? res.data : res.data?.results ?? [];
        setBrands(data);
      })
      .catch(() => toast.error("Error al cargar marcas"))
      .finally(() => setBrandsLoading(false));
  }, []);

  useEffect(() => {
    api
      .get("productos/?limit=500")
      .then((res) => {
        const data: Producto[] = Array.isArray(res.data) ? res.data : res.data?.results ?? [];
        setProductos(data);
      })
      .catch(() => toast.error("Error al cargar productos"))
      .finally(() => setProductosLoading(false));
  }, []);

  const productosFiltrados =
    form.brand
      ? productos.filter(
        (p) => (p.brand_name ?? "").toLowerCase() === form.brand.toLowerCase()
      )
      : productos;

  const handleChange = (
    e: React.ChangeEvent<HTMLSelectElement | HTMLTextAreaElement | HTMLInputElement>
  ) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    if (name === "brand") {
      setProductLines((prev) => prev.map((l) => ({ ...l, producto_id: null })));
    }
  };

  const addLine = () => setProductLines((prev) => [...prev, emptyLine()]);
  const removeLine = (idx: number) => {
    setProductLines((prev) => {
      const next = prev.filter((_, i) => i !== idx);
      return next.length === 0 ? [emptyLine()] : next;
    });
  };
  const updateLine = (idx: number, patch: Partial<ProductLine>) =>
    setProductLines((prev) => prev.map((l, i) => (i === idx ? { ...l, ...patch } : l)));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.client_id || !form.brand || !form.mode || !form.freight_mode || !form.dispatch_mode || !form.price_basis) {
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
        ...(form.purchase_order_number ? { purchase_order_number: form.purchase_order_number } : {}),
        ...(form.operado_por ? { operado_por: form.operado_por } : {}),
      };
      const validLines = productLines.filter((l) => l.producto_id && l.quantity);
      if (validLines.length > 0) {
        payload.product_lines = validLines.map((l) => ({
          producto_id: l.producto_id,
          quantity: Number(l.quantity),
        }));
      }
      const res = await api.post("expedientes/create/", payload);
      if (res.status === 201) {
        toast.success("Expediente creado exitosamente");
        const newId = res.data?.expediente_id || res.data?.id;
        router.push(newId ? `/expedientes/${newId}` : "/expedientes");
      }
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string; message?: string } } };
      toast.error(
        e.response?.data?.detail || e.response?.data?.message || "Error al crear el expediente"
      );
    } finally {
      setSubmitting(false);
    }
  };

  const inputCls =
    "w-full bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg px-3 py-2.5 text-sm text-[var(--color-text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-navy)]/30";
  const labelCls =
    "block text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider mb-1.5";
  const loadingRowCls =
    "flex items-center gap-2 h-10 px-3 bg-[var(--color-bg-alt)] border border-[var(--color-border)] rounded-lg";
  const spinnerCls =
    "w-4 h-4 border-2 border-[var(--color-navy)] border-t-transparent rounded-full animate-spin";

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
              <div className={loadingRowCls}><div className={spinnerCls} /><span className="text-sm text-[var(--color-text-tertiary)]">Cargando clientes...</span></div>
            ) : (
              <select name="client_id" value={form.client_id} onChange={handleChange} required className={inputCls}>
                <option value="">Seleccionar cliente...</option>
                {clients.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}{c.legal_entity_name ? ` \u2014 ${c.legal_entity_name}` : ""}
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Marca */}
          <div>
            <label className={labelCls}>Marca <span className="text-[var(--color-coral)]">*</span></label>
            {brandsLoading ? (
              <div className={loadingRowCls}><div className={spinnerCls} /><span className="text-sm text-[var(--color-text-tertiary)]">Cargando marcas...</span></div>
            ) : (
              <select name="brand" value={form.brand} onChange={handleChange} required className={inputCls}>
                <option value="">Seleccionar marca...</option>
                {brands.map((b) => (
                  <option key={b.id} value={b.name}>{b.name}</option>
                ))}
              </select>
            )}
          </div>

          {/* Modo */}
          <div>
            <label className={labelCls}>Modo <span className="text-[var(--color-coral)]">*</span></label>
            <select name="mode" value={form.mode} onChange={handleChange} required className={inputCls}>
              <option value="">Seleccionar modo...</option>
              {MODE_OPTIONS.map((m) => <option key={m.value} value={m.value}>{m.label}</option>)}
            </select>
          </div>

          {/* Destino */}
          <div>
            <label className={labelCls}>Destino <span className="text-[var(--color-coral)]">*</span></label>
            <select name="destination" value={form.destination} onChange={handleChange} required className={inputCls}>
              {DESTINATION_OPTIONS.map((d) => <option key={d.value} value={d.value}>{d.label}</option>)}
            </select>
          </div>

          {/* Modo de Flete */}
          <div>
            <label className={labelCls}>Modo de Flete <span className="text-[var(--color-coral)]">*</span></label>
            <select name="freight_mode" value={form.freight_mode} onChange={handleChange} required className={inputCls}>
              <option value="">Seleccionar modo de flete...</option>
              {FREIGHT_MODE_OPTIONS.map((f) => <option key={f.value} value={f.value}>{f.label}</option>)}
            </select>
          </div>

          {/* Modo de Despacho */}
          <div>
            <label className={labelCls}>Modo de Despacho <span className="text-[var(--color-coral)]">*</span></label>
            <select name="dispatch_mode" value={form.dispatch_mode} onChange={handleChange} required className={inputCls}>
              <option value="">Seleccionar modo de despacho...</option>
              {DISPATCH_MODE_OPTIONS.map((d) => <option key={d.value} value={d.value}>{d.label}</option>)}
            </select>
          </div>

          {/* Base de Precio */}
          <div>
            <label className={labelCls}>Base de Precio <span className="text-[var(--color-coral)]">*</span></label>
            <select name="price_basis" value={form.price_basis} onChange={handleChange} required className={inputCls}>
              <option value="">Seleccionar base de precio...</option>
              {PRICE_BASIS_OPTIONS.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
            </select>
          </div>

          {/* N\u00b0 Orden de Compra */}
          <div>
            <label className={labelCls}>Orden de Compra <span className="text-[var(--color-text-tertiary)] font-normal">(opcional)</span></label>
            <input type="text" name="purchase_order_number" value={form.purchase_order_number} onChange={handleChange} placeholder="PO-2026-XXXX" className={inputCls} />
          </div>

          {/* Operado por */}
          <div>
            <label className={labelCls}>Operado por <span className="text-[var(--color-text-tertiary)] font-normal">(opcional)</span></label>
            <select name="operado_por" value={form.operado_por} onChange={handleChange} className={inputCls}>
              <option value="">Sin definir</option>
              <option value="CLIENTE">CLIENTE</option>
              <option value="MWT">MWT</option>
            </select>
          </div>

          {/* L\u00cdNEAS DE PRODUCTO */}
          <div>
            <label className={labelCls + " mb-3"}>
              Productos <span className="text-[var(--color-text-tertiary)] font-normal">(opcional)</span>
            </label>

            {productosLoading ? (
              <div className={loadingRowCls}>
                <div className={spinnerCls} />
                <span className="text-sm text-[var(--color-text-tertiary)]">Cargando productos...</span>
              </div>
            ) : (
              <div className="space-y-2">
                {/* Header de columnas */}
                <div className="grid grid-cols-[1fr_120px_36px] gap-2 px-1">
                  <span className="text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">
                    Producto
                  </span>
                  <span className="text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">
                    Cantidad
                  </span>
                  <span />
                </div>

                {/* Filas */}
                {productLines.map((line, idx) => (
                  <div key={idx} className="grid grid-cols-[1fr_120px_36px] gap-2 items-center">
                    <select
                      value={line.producto_id ?? ""}
                      onChange={(e) =>
                        updateLine(idx, {
                          producto_id: e.target.value ? Number(e.target.value) : null,
                        })
                      }
                      disabled={!form.brand || productosFiltrados.length === 0}
                      className={inputCls + " disabled:opacity-50 disabled:cursor-not-allowed"}
                    >
                      <option value="">
                        {!form.brand
                          ? "Primero seleccion\u00e1 una marca"
                          : productosFiltrados.length === 0
                            ? "Sin productos para esta marca"
                            : "Seleccionar producto..."}
                      </option>
                      {productosFiltrados.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name}{p.sku_base ? ` \u2014 ${p.sku_base}` : ""}
                        </option>
                      ))}
                    </select>

                    <input
                      type="number"
                      min={1}
                      value={line.quantity}
                      onChange={(e) => updateLine(idx, { quantity: e.target.value })}
                      placeholder="0"
                      className={inputCls}
                    />

                    <button
                      type="button"
                      onClick={() => removeLine(idx)}
                      className="flex items-center justify-center w-9 h-9 rounded-lg border border-[var(--color-border)] text-[var(--color-text-tertiary)] hover:border-[var(--color-coral)] hover:text-[var(--color-coral)] hover:bg-red-50 transition-colors"
                      title="Eliminar fila"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}

                {/* Bot\u00f3n agregar fila */}
                <button
                  type="button"
                  onClick={addLine}
                  className="mt-1 flex items-center gap-1.5 text-xs text-[var(--color-navy)] border border-dashed border-[var(--color-navy)]/40 rounded-lg px-3 py-2 hover:bg-[var(--color-navy)]/5 transition-colors w-full justify-center"
                >
                  <Plus className="w-3.5 h-3.5" /> Agregar otro producto
                </button>
              </div>
            )}
          </div>

          {/* Notas */}
          <div>
            <label className={labelCls}>Notas <span className="text-[var(--color-text-tertiary)] font-normal">(opcional)</span></label>
            <textarea name="notes" value={form.notes} onChange={handleChange} rows={3} placeholder="Observaciones adicionales..." className={inputCls + " resize-none"} />
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
              disabled={submitting || clientsLoading || brandsLoading}
              className="bg-navy text-white px-4 py-2 rounded-lg text-sm font-medium transition-all shadow-sm active:scale-95 flex items-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {submitting ? (
                <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> Creando...</>
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
