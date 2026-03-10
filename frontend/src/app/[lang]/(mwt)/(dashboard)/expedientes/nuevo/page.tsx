"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import toast from "react-hot-toast";
import { ArrowLeft, Plus } from "lucide-react";

interface Client {
  id: string;
  name: string;
}

interface ExpedienteListItem {
  client_name: string;
}

const BRAND_OPTIONS = ["SKECHERS", "ON", "SPEEDO", "TOMS", "ASICS", "VIVAIA", "TECMATER"];
const MODE_OPTIONS = ["IMPORTACION", "EXPORTACION", "COMISION"];
const FREIGHT_MODE_OPTIONS = ["MARITIMO", "AEREO", "TERRESTRE"];
const DISPATCH_MODE_OPTIONS = ["mwt", "directo"];
const PRICE_BASIS_OPTIONS = ["CIF", "FOB", "EXW"];

export default function NuevoExpedientePage() {
  const router = useRouter();

  const [clients, setClients] = useState<Client[]>([]);
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
    notes: "",
  });

  useEffect(() => {
    const fetchClients = async () => {
      try {
        setClientsLoading(true);
        setClientsError(false);
        const res = await api.get("ui/expedientes/");
        const expedientes: ExpedienteListItem[] = Array.isArray(res.data) ? res.data : [];
        const uniqueClients = Array.from(
          new Map(
            expedientes.map((e) => [
              e.client_name,
              { id: e.client_name, name: e.client_name },
            ])
          ).values()
        );
        setClients(uniqueClients);
      } catch {
        setClientsError(true);
        toast.error("Error al cargar clientes");
      } finally {
        setClientsLoading(false);
      }
    };
    fetchClients();
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement | HTMLTextAreaElement>) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.client_id || !form.brand || !form.mode || !form.freight_mode || !form.dispatch_mode || !form.price_basis) {
      toast.error("Completa todos los campos obligatorios");
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.post("expedientes/", {
        client: form.client_id,
        brand: form.brand,
        mode: form.mode,
        freight_mode: form.freight_mode,
        dispatch_mode: form.dispatch_mode,
        price_basis: form.price_basis,
        notes: form.notes || undefined,
      });
      if (res.status === 201) {
        toast.success("Expediente creado");
        const newId = res.data?.id || res.data?.expediente_id;
        router.push(`/expedientes/${newId}`);
      }
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      toast.error(e.response?.data?.detail || "Error al crear");
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
        <h1 className="text-2xl font-display font-bold text-text-primary mb-1">Nuevo Expediente</h1>
        <p className="text-sm text-text-tertiary mb-8">Completa los datos para registrar el expediente.</p>

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
                Error al cargar clientes. Recarga la página.
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
                  <option key={c.id} value={c.id}>
                    {c.name}
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
                <option key={b} value={b}>{b}</option>
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
                <option key={m} value={m}>{m}</option>
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
                <option key={f} value={f}>{f}</option>
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
                <option key={d} value={d}>{d}</option>
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
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </div>

          {/* Notas */}
          <div>
            <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5">
              Notas <span className="text-text-tertiary font-normal">(opcional)</span>
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
