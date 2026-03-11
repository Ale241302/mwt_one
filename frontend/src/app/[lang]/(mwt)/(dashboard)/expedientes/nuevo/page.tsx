"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import toast from "react-hot-toast";
import { ArrowLeft, Plus } from "lucide-react";

interface LegalEntityOption {
  entity_id: string;
  legal_name: string;
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

// entity_id de la entidad MWT emisora — ajusta si es diferente en tu DB
const MWT_LEGAL_ENTITY_ID = "MWT-CR";

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
  });

  useEffect(() => {
    const fetchClients = async () => {
      try {
        setClientsLoading(true);
        setClientsError(false);
        // Endpoint que devuelve LegalEntities con role=CLIENT
        const res = await api.get("ui/legal-entities/?role=CLIENT");
        const entities: LegalEntityOption[] = Array.isArray(res.data)
          ? res.data
          : res.data?.results ?? [];
        setClients(entities);
      } catch {
        // Fallback: extraer clientes únicos desde expedientes existentes
        try {
          const res2 = await api.get("ui/expedientes/");
          const expedientes: Array<{ client_name: string; client_entity_id?: string }> =
            Array.isArray(res2.data) ? res2.data : [];
          const unique = Array.from(
            new Map(
              expedientes
                .filter((e) => e.client_entity_id) // solo si viene el entity_id
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
    e: React.ChangeEvent<HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
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
      const res = await api.post("expedientes/create/", {
        legal_entity_id: MWT_LEGAL_ENTITY_ID, // entidad MWT emisora
        client: form.client_id,               // entity_id del cliente (ej: "SKECHERS-CR")
        brand: form.brand,
        mode: form.mode,
        freight_mode: form.freight_mode,
        dispatch_mode: form.dispatch_mode.toUpperCase(), // backend espera "MWT" en mayús
        price_basis: form.price_basis,
        destination: form.destination,
        ...(form.notes ? { notes: form.notes } : {}),
      });

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

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <button
        onClick={() => router.back()}
        className="text-sm text-text-secondary hover:text-navy flex items-center transition-colors"
      >
        <ArrowLeft className="w-4 h-4 mr-1" /> Volver
      </button>

      <div className="bg-surface rounded-2xl border border-border shadow-sm p-8">
        <h1 className="text-2xl font-display font-bold text-text-primary mb-1">
          Nuevo Expediente
        </h1>
        <p className="text-sm text-text-tertiary mb-8">
          Completa los datos para registrar el expediente.
        </p>

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Cliente */}
          <div>
            <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5">
              Cliente <span className="text-coral">*</span>
            </label>
            {clientsLoading ? (
              <div className="flex items-center gap-2 h-10 px-3 bg-bg-alt border border-border rounded-lg">
                <div className="w-4 h-4 border-2 border-navy border-t-transparent rounded-full animate-spin" />
                <span className="text-sm text-text-tertiary">Cargando clientes...</span>
              </div>
            ) : clientsError ? (
              <div className="text-sm text-coral px-3 py-2 bg-red-50 border border-red-200 rounded-lg">
                Error al cargar clientes.{" "}
                <button
                  type="button"
                  className="underline"
                  onClick={() => window.location.reload()}
                >
                  Recargar
                </button>
              </div>
            ) : (
              <select
                name="client_id"
                value={form.client_id}
                onChange={handleChange}
                required
                className="w-full bg-bg border border-border rounded-lg px-3 py-2.5 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-navy/30"
              >
                <option value="">Seleccionar cliente...</option>
                {clients.map((c) => (
                  <option key={c.entity_id} value={c.entity_id}>
                    {c.legal_name}
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Marca */}
          <div>
            <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5">
              Marca <span className="text-coral">*</span>
            </label>
            <select
              name="brand"
              value={form.brand}
              onChange={handleChange}
              required
              className="w-full bg-bg border border-border rounded-lg px-3 py-2.5 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-navy/30"
            >
              <option value="">Seleccionar marca...</option>
              {BRAND_OPTIONS.map((b) => (
                <option key={b} value={b}>
                  {b}
                </option>
              ))}
            </select>
          </div>

          {/* Modo */}
          <div>
            <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5">
              Modo <span className="text-coral">*</span>
            </label>
            <select
              name="mode"
              value={form.mode}
              onChange={handleChange}
              required
              className="w-full bg-bg border border-border rounded-lg px-3 py-2.5 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-navy/30"
            >
              <option value="">Seleccionar modo...</option>
              {MODE_OPTIONS.map((m) => (
                <option key={m.value} value={m.value}>
                  {m.label}
                </option>
              ))}
            </select>
            {form.brand === "TECMATER" && form.mode === "COMISION" && (
              <p className="text-xs text-coral mt-1">
                ⚠ TECMATER no soporta modo COMISION.
              </p>
            )}
          </div>

          {/* Destino */}
          <div>
            <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5">
              Destino <span className="text-coral">*</span>
            </label>
            <select
              name="destination"
              value={form.destination}
              onChange={handleChange}
              required
              className="w-full bg-bg border border-border rounded-lg px-3 py-2.5 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-navy/30"
            >
              {DESTINATION_OPTIONS.map((d) => (
                <option key={d.value} value={d.value}>
                  {d.label}
                </option>
              ))}
            </select>
          </div>

          {/* Modo de Flete */}
          <div>
            <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5">
              Modo de Flete <span className="text-coral">*</span>
            </label>
            <select
              name="freight_mode"
              value={form.freight_mode}
              onChange={handleChange}
              required
              className="w-full bg-bg border border-border rounded-lg px-3 py-2.5 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-navy/30"
            >
              <option value="">Seleccionar modo de flete...</option>
              {FREIGHT_MODE_OPTIONS.map((f) => (
                <option key={f} value={f}>
                  {f}
                </option>
              ))}
            </select>
          </div>

          {/* Modo de Despacho */}
          <div>
            <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5">
              Modo de Despacho <span className="text-coral">*</span>
            </label>
            <select
              name="dispatch_mode"
              value={form.dispatch_mode}
              onChange={handleChange}
              required
              className="w-full bg-bg border border-border rounded-lg px-3 py-2.5 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-navy/30"
            >
              <option value="">Seleccionar modo de despacho...</option>
              {DISPATCH_MODE_OPTIONS.map((d) => (
                <option key={d.value} value={d.value}>
                  {d.label}
                </option>
              ))}
            </select>
          </div>

          {/* Base de Precio */}
          <div>
            <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5">
              Base de Precio <span className="text-coral">*</span>
            </label>
            <select
              name="price_basis"
              value={form.price_basis}
              onChange={handleChange}
              required
              className="w-full bg-bg border border-border rounded-lg px-3 py-2.5 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-navy/30"
            >
              <option value="">Seleccionar base de precio...</option>
              {PRICE_BASIS_OPTIONS.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </div>

          {/* Notas */}
          <div>
            <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5">
              Notas{" "}
              <span className="text-text-tertiary font-normal">(opcional)</span>
            </label>
            <textarea
              name="notes"
              value={form.notes}
              onChange={handleChange}
              rows={3}
              placeholder="Observaciones adicionales..."
              className="w-full bg-bg border border-border rounded-lg px-3 py-2.5 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-navy/30 resize-none"
            />
          </div>

          {/* Submit */}
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={() => router.back()}
              className="bg-surface border border-border text-text-secondary hover:bg-bg-alt px-4 py-2 rounded-lg text-sm font-medium transition-all"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={submitting || clientsLoading}
              className="bg-navy hover:bg-slate-800 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all shadow-sm active:scale-95 flex items-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {submitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Creando...
                </>
              ) : (
                <>
                  <Plus size={16} /> Crear Expediente
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
