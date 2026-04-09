"use client";

import { useState, useEffect } from "react";
import api from "@/lib/api";

interface Brand {
  id: string;
  name: string;
}

interface Props {
  onSaved: () => void;
  onClose: () => void;
}

export function TemplateEditor({ onSaved, onClose }: Props) {
  const [brands, setBrands] = useState<Brand[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState({
    name: "",
    template_key: "",
    subject_template: "",
    body_template: "",
    language: "es",
    brand: "",
    is_active: true,
  });

  useEffect(() => {
    api
      .get("/brands/")
      .then((res) => {
        const data = Array.isArray(res.data)
          ? res.data
          : res.data.results ?? [];
        setBrands(data);
        if (data.length > 0 && !form.brand) {
          setForm((f) => ({ ...f, brand: data[0].id }));
        }
      })
      .catch(() => setBrands([]));
  }, []);

  const handleChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    >
  ) => {
    const { name, value, type } = e.target;
    const checked =
      type === "checkbox" ? (e.target as HTMLInputElement).checked : undefined;
    setForm((f) => ({
      ...f,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleSubmit = async () => {
    setError(null);

    if (!form.name.trim() || !form.template_key.trim() || !form.subject_template.trim() || !form.body_template.trim()) {
      setError("Los campos Nombre, Clave, Asunto y Cuerpo son obligatorios.");
      return;
    }

    setSaving(true);
    try {
      await api.post("/notifications/templates/", {
        name: form.name.trim(),
        template_key: form.template_key.trim(),
        subject_template: form.subject_template.trim(),
        body_template: form.body_template.trim(),
        language: form.language,
        brand: form.brand || null,
        is_active: form.is_active,
      });
      onSaved();
    } catch (err: unknown) {
      const anyErr = err as { response?: { data?: unknown } };
      if (anyErr?.response?.data) {
        const data = anyErr.response.data;
        if (typeof data === "object" && data !== null) {
          const msgs = Object.entries(data)
            .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(", ") : v}`)
            .join(" | ");
          setError(msgs);
        } else {
          setError(String(data));
        }
      } else {
        setError("Error inesperado al guardar.");
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50">
      <div className="bg-surface p-6 rounded-xl w-full max-w-2xl border border-border shadow-2xl max-h-[90vh] overflow-y-auto">
        <h2 className="text-xl font-bold text-text-primary mb-1">
          Crear Template
        </h2>
        <p className="text-text-secondary text-sm mb-5">
          Define una nueva plantilla de email transaccional.
        </p>

        {error && (
          <div className="mb-4 px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
            {error}
          </div>
        )}

        <div className="space-y-4">
          {/* Nombre */}
          <div>
            <label className="block text-xs font-semibold text-text-secondary mb-1 uppercase tracking-wide">
              Nombre <span className="text-red-400">*</span>
            </label>
            <input
              name="name"
              value={form.name}
              onChange={handleChange}
              placeholder="Ej. Crédito Liberado ES"
              className="w-full px-3 py-2 rounded-lg bg-bg-alt border border-border text-text-primary text-sm placeholder:text-text-tertiary focus:outline-none focus:ring-2 focus:ring-navy/50"
            />
          </div>

          {/* template_key */}
          <div>
            <label className="block text-xs font-semibold text-text-secondary mb-1 uppercase tracking-wide">
              Clave (template_key) <span className="text-red-400">*</span>
            </label>
            <input
              name="template_key"
              value={form.template_key}
              onChange={handleChange}
              placeholder="Ej. credit.released"
              className="w-full px-3 py-2 rounded-lg bg-bg-alt border border-border text-text-primary text-sm font-mono placeholder:text-text-tertiary focus:outline-none focus:ring-2 focus:ring-navy/50"
            />
            <p className="mt-1 text-xs text-text-tertiary">
              Identificador único usado por el sistema para disparar este template. Usa formato{" "}
              <code className="font-mono bg-bg-alt px-1 rounded">dominio.evento</code>.
            </p>
          </div>

          {/* Idioma y Marca en fila */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-text-secondary mb-1 uppercase tracking-wide">
                Idioma
              </label>
              <select
                name="language"
                value={form.language}
                onChange={handleChange}
                className="w-full px-3 py-2 rounded-lg bg-bg-alt border border-border text-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-navy/50"
              >
                <option value="es">Español (es)</option>
                <option value="en">English (en)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-text-secondary mb-1 uppercase tracking-wide">
                Marca
              </label>
              <select
                name="brand"
                value={form.brand}
                onChange={handleChange}
                className="w-full px-3 py-2 rounded-lg bg-bg-alt border border-border text-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-navy/50"
              >
                <option value="">— Sin marca (Default) —</option>
                {brands.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Asunto */}
          <div>
            <label className="block text-xs font-semibold text-text-secondary mb-1 uppercase tracking-wide">
              Asunto (subject_template) <span className="text-red-400">*</span>
            </label>
            <input
              name="subject_template"
              value={form.subject_template}
              onChange={handleChange}
              placeholder="Ej. Tu crédito {{ expediente_id }} ha sido liberado"
              className="w-full px-3 py-2 rounded-lg bg-bg-alt border border-border text-text-primary text-sm placeholder:text-text-tertiary focus:outline-none focus:ring-2 focus:ring-navy/50"
            />
            <p className="mt-1 text-xs text-text-tertiary">
              Soporta variables Jinja2:{" "}
              <code className="font-mono bg-bg-alt px-1 rounded">{"{{ variable }}"}</code>
            </p>
          </div>

          {/* Cuerpo */}
          <div>
            <label className="block text-xs font-semibold text-text-secondary mb-1 uppercase tracking-wide">
              Cuerpo HTML (body_template) <span className="text-red-400">*</span>
            </label>
            <textarea
              name="body_template"
              value={form.body_template}
              onChange={handleChange}
              rows={8}
              placeholder={`<p>Hola {{ cliente_nombre }},</p>\n<p>Tu crédito {{ expediente_id }} fue liberado el {{ fecha }}.</p>`}
              className="w-full px-3 py-2 rounded-lg bg-bg-alt border border-border text-text-primary text-sm font-mono placeholder:text-text-tertiary focus:outline-none focus:ring-2 focus:ring-navy/50 resize-y"
            />
            <p className="mt-1 text-xs text-text-tertiary">
              HTML completo con variables Jinja2. El sistema renderiza este contenido antes de enviar.
            </p>
          </div>

          {/* is_active */}
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="is_active"
              name="is_active"
              checked={form.is_active}
              onChange={handleChange}
              className="w-4 h-4 accent-navy rounded"
            />
            <label
              htmlFor="is_active"
              className="text-sm text-text-secondary cursor-pointer"
            >
              Template activo (habilitado para envíos)
            </label>
          </div>
        </div>

        <div className="mt-6 flex justify-end space-x-3">
          <button
            onClick={onClose}
            disabled={saving}
            className="px-4 py-2 text-sm text-text-secondary hover:text-text-primary transition-colors border border-border rounded disabled:opacity-50"
          >
            Cancelar
          </button>
          <button
            onClick={handleSubmit}
            disabled={saving}
            className="px-5 py-2 text-sm bg-navy text-white font-bold rounded hover:bg-slate-800 transition-colors disabled:opacity-60 flex items-center gap-2"
          >
            {saving && (
              <svg
                className="animate-spin h-4 w-4"
                viewBox="0 0 24 24"
                fill="none"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8v8H4z"
                />
              </svg>
            )}
            {saving ? "Guardando..." : "Guardar"}
          </button>
        </div>
      </div>
    </div>
  );
}
