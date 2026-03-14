/**
 * S9-07 — ArtifactFormModal
 * Modal con schemas específicos por tipo de artefacto.
 *
 * Cubre: ART-01 (BL), ART-02 (Factura comercial), ART-03 (Packing List),
 *        ART-04 (Certificado de origen), ART-05 (Seguro), ART-06 (Permisos/DIAN),
 *        ART-09 (Observaciones/notas libres).
 *
 * Uso: reemplaza o complementa ArtifactModal.tsx para schemas complejos.
 *   <ArtifactFormModal
 *     artifactTypeId="ART-01"
 *     artifactName="Bill of Lading"
 *     expedienteId="42"
 *     onClose={() => {}}
 *     onSuccess={() => {}}
 *   />
 */
"use client";
import { useState } from "react";
import { X, Loader2, CheckCircle, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

// ─── Tipos ─────────────────────────────────────────────────────────────────────
export type ArtifactTypeId =
  | "ART-01" | "ART-02" | "ART-03" | "ART-04"
  | "ART-05" | "ART-06" | "ART-09";

type FieldType = "text" | "date" | "number" | "select" | "textarea";

interface FieldDef {
  name: string;
  label: string;
  type: FieldType;
  placeholder?: string;
  required?: boolean;
  options?: string[];
  hint?: string;
}

// ─── Schemas por tipo ───────────────────────────────────────────────────────────────
const SCHEMAS: Record<ArtifactTypeId, { title: string; fields: FieldDef[] }> = {
  /** ART-01 — Bill of Lading */
  "ART-01": {
    title: "Bill of Lading",
    fields: [
      { name: "bl_number",         label: "Número de BL",             type: "text",   required: true,  placeholder: "Ej: HLBU1234567" },
      { name: "issuing_carrier",   label: "Naviera / Transportista",   type: "text",   required: true,  placeholder: "Ej: Hapag-Lloyd" },
      { name: "port_of_loading",   label: "Puerto de carga",           type: "text",   required: true,  placeholder: "Ej: Shanghai" },
      { name: "port_of_discharge", label: "Puerto de descarga",        type: "text",   required: true,  placeholder: "Ej: Buenaventura" },
      { name: "vessel_name",       label: "Nombre del buque",          type: "text",   placeholder: "Ej: MSC MAYA" },
      { name: "bl_date",           label: "Fecha de emisión",          type: "date",   required: true },
      { name: "container_count",   label: "Número de contenedores",    type: "number", placeholder: "Ej: 2" },
      { name: "notes",             label: "Notas adicionales",         type: "textarea", placeholder: "Observaciones..." },
    ],
  },

  /** ART-02 — Factura comercial */
  "ART-02": {
    title: "Factura Comercial",
    fields: [
      { name: "invoice_number",   label: "Número de factura",   type: "text",   required: true,  placeholder: "Ej: INV-2026-001" },
      { name: "invoice_date",     label: "Fecha de factura",     type: "date",   required: true },
      { name: "seller",           label: "Vendedor (empresa)",   type: "text",   required: true },
      { name: "buyer",            label: "Comprador (empresa)",  type: "text",   required: true },
      { name: "total_amount",     label: "Monto total",          type: "number", required: true,  placeholder: "0.00" },
      { name: "currency",         label: "Moneda",               type: "select", required: true,  options: ["USD", "EUR", "COP"] },
      { name: "incoterm",         label: "Incoterm",             type: "select", options: ["FOB", "CIF", "EXW", "DAP", "DDP", "CFR"] },
      { name: "notes",            label: "Notas",                type: "textarea" },
    ],
  },

  /** ART-03 — Packing List */
  "ART-03": {
    title: "Packing List",
    fields: [
      { name: "pl_number",         label: "Número de packing list", type: "text",   required: true,  placeholder: "Ej: PL-2026-001" },
      { name: "pl_date",           label: "Fecha",                  type: "date",   required: true },
      { name: "total_packages",    label: "Total de bultos",         type: "number", required: true },
      { name: "total_weight_kg",   label: "Peso bruto total (kg)",   type: "number", placeholder: "0.00" },
      { name: "total_volume_m3",   label: "Volumen total (m³)",      type: "number", placeholder: "0.00" },
      { name: "hs_code",           label: "Código HS principal",     type: "text",   placeholder: "Ej: 6203.42" },
      { name: "notes",             label: "Notas",                  type: "textarea" },
    ],
  },

  /** ART-04 — Certificado de origen */
  "ART-04": {
    title: "Certificado de Origen",
    fields: [
      { name: "cert_number",   label: "Número de certificado",    type: "text",   required: true },
      { name: "cert_date",     label: "Fecha de emisión",         type: "date",   required: true },
      { name: "origin_country",label: "País de origen",           type: "text",   required: true,  placeholder: "Ej: China" },
      { name: "cert_type",     label: "Tipo de certificado",      type: "select", options: ["Forma A", "EUR.1", "COÓ", "Otro"] },
      { name: "issuing_entity",label: "Entidad emisora",           type: "text",   placeholder: "Ej: Cámara de Comercio" },
      { name: "notes",         label: "Notas",                    type: "textarea" },
    ],
  },

  /** ART-05 — Póliza de seguro */
  "ART-05": {
    title: "Póliza de Seguro",
    fields: [
      { name: "policy_number",  label: "Número de póliza",        type: "text",   required: true },
      { name: "insurer",        label: "Aseguradora",              type: "text",   required: true },
      { name: "policy_date",    label: "Fecha de póliza",         type: "date",   required: true },
      { name: "coverage_value", label: "Valor asegurado",          type: "number", required: true,  placeholder: "0.00" },
      { name: "currency",       label: "Moneda",                   type: "select", required: true,  options: ["USD", "EUR", "COP"] },
      { name: "risk_type",      label: "Tipo de cobertura",        type: "select", options: ["Todo riesgo", "Básica", "CAR"] },
      { name: "expiry_date",    label: "Fecha de vencimiento",     type: "date" },
      { name: "notes",          label: "Notas",                    type: "textarea" },
    ],
  },

  /** ART-06 — Permisos / DIAN */
  "ART-06": {
    title: "Permisos / DIAN",
    fields: [
      { name: "permit_number",  label: "Número de documento",     type: "text",   required: true },
      { name: "permit_type",    label: "Tipo de permiso",          type: "select", required: true,
        options: ["Declaración de importación", "Licencia previa", "Visto bueno ICA",
                  "Visto bueno INVIMA", "Certificado fitosanitario", "Otro"] },
      { name: "issue_date",     label: "Fecha de emisión",         type: "date",   required: true },
      { name: "expiry_date",    label: "Fecha de vencimiento",     type: "date" },
      { name: "issuing_entity", label: "Entidad emisora",           type: "text",   placeholder: "Ej: DIAN" },
      { name: "reference",      label: "Referencia adicional",     type: "text" },
      { name: "notes",          label: "Notas",                    type: "textarea" },
    ],
  },

  /** ART-09 — Observaciones / Notas libres */
  "ART-09": {
    title: "Observaciones",
    fields: [
      { name: "category",  label: "Categoría",     type: "select",
        options: ["Incidencia", "Coordinación", "Seguimiento", "Cliente", "Otro"] },
      { name: "notes",     label: "Descripción",   type: "textarea", required: true,
        placeholder: "Describe la observación o incidencia…" },
      { name: "date",      label: "Fecha",          type: "date" },
    ],
  },
};

// ─── Renderer de campo ──────────────────────────────────────────────────────────────────
const baseInput = [
  "w-full border border-[var(--border)] rounded-lg px-3 py-2 text-sm",
  "bg-[var(--surface)] text-[var(--text-primary)]",
  "focus:outline-none focus:ring-2 focus:ring-[var(--navy)] focus:border-transparent",
  "placeholder:text-[var(--text-disabled)] transition",
].join(" ");

function Field({ field, value, onChange }: {
  field: FieldDef;
  value: string;
  onChange: (v: string) => void;
}) {
  const id = `artifact-field-${field.name}`;
  return (
    <div>
      <label htmlFor={id} className="block text-xs font-medium text-[var(--text-secondary)] mb-1">
        {field.label}{field.required && <span className="text-[var(--coral)] ml-0.5">*</span>}
      </label>
      {field.type === "textarea" ? (
        <textarea
          id={id}
          name={field.name}
          required={field.required}
          placeholder={field.placeholder}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          rows={3}
          className={cn(baseInput, "resize-none")}
        />
      ) : field.type === "select" ? (
        <select
          id={id}
          name={field.name}
          required={field.required}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className={baseInput}
        >
          <option value="">Seleccionar…</option>
          {field.options?.map((o) => (
            <option key={o} value={o}>{o}</option>
          ))}
        </select>
      ) : (
        <input
          id={id}
          name={field.name}
          type={field.type}
          required={field.required}
          placeholder={field.placeholder}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className={baseInput}
        />
      )}
      {field.hint && <p className="text-[10px] text-[var(--text-muted)] mt-0.5">{field.hint}</p>}
    </div>
  );
}

// ─── Modal principal ────────────────────────────────────────────────────────────────────
export interface ArtifactFormModalProps {
  artifactTypeId: ArtifactTypeId;
  artifactName?: string;
  expedienteId: string;
  onClose: () => void;
  onSuccess: () => void;
}

export function ArtifactFormModal({
  artifactTypeId,
  artifactName,
  expedienteId,
  onClose,
  onSuccess,
}: ArtifactFormModalProps) {
  const schema = SCHEMAS[artifactTypeId];
  const displayName = artifactName ?? schema?.title ?? artifactTypeId;

  // Estado inicial: un campo por cada field del schema
  const [values, setValues] = useState<Record<string, string>>(
    () => Object.fromEntries((schema?.fields ?? []).map((f) => [f.name, ""]))
  );
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState<string | null>(null);
  const [success, setSuccess]   = useState(false);

  function setField(name: string, val: string) {
    setValues((prev) => ({ ...prev, [name]: val }));
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/expedientes/${expedienteId}/artifacts/${artifactTypeId}/register/`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ type: artifactTypeId, ...values }),
        }
      );
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail ?? data.message ?? `Error ${res.status}`);
      }
      setSuccess(true);
      setTimeout(() => { onSuccess(); onClose(); }, 900);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error inesperado");
    } finally {
      setLoading(false);
    }
  }

  if (!schema) {
    return null; // tipo no soportado — fallback al ArtifactModal genérico
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="artifact-form-modal-title"
    >
      <div className="bg-[var(--surface)] rounded-2xl shadow-[var(--shadow-lg)] w-full max-w-lg mx-4 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border)]">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.5px] text-[var(--text-tertiary)] mb-0.5">
              {artifactTypeId}
            </p>
            <h2
              id="artifact-form-modal-title"
              className="text-base font-semibold text-[var(--navy)]"
            >
              {displayName}
            </h2>
          </div>
          <button
            onClick={onClose}
            aria-label="Cerrar modal"
            className="p-1.5 rounded-lg hover:bg-[var(--surface-hover)] transition-colors"
          >
            <X size={16} className="text-[var(--text-tertiary)]" />
          </button>
        </div>

        {/* Body */}
        <div className="max-h-[70vh] overflow-y-auto px-6 py-4">
          {success ? (
            <div className="flex flex-col items-center gap-3 py-8">
              <CheckCircle size={44} className="text-[var(--success)]" />
              <p className="text-sm font-semibold text-[var(--text-primary)]">Artefacto registrado</p>
            </div>
          ) : (
            <form id="artifact-form" onSubmit={handleSubmit} className="space-y-3">
              {schema.fields.map((field) => (
                <Field
                  key={field.name}
                  field={field}
                  value={values[field.name] ?? ""}
                  onChange={(v) => setField(field.name, v)}
                />
              ))}

              {error && (
                <div className="flex items-center gap-2 bg-[var(--coral-soft)] border border-[var(--coral)]/30 rounded-lg px-3 py-2 text-xs text-[var(--coral)]">
                  <AlertCircle size={12} className="flex-shrink-0" />
                  {error}
                </div>
              )}
            </form>
          )}
        </div>

        {/* Footer */}
        {!success && (
          <div className="flex justify-end gap-2 px-6 py-4 border-t border-[var(--border)] bg-[var(--bg-alt)]">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-[var(--text-secondary)] hover:bg-[var(--surface-hover)] rounded-lg transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              form="artifact-form"
              disabled={loading}
              className="px-4 py-2 text-sm font-semibold bg-[var(--navy)] text-[var(--text-inverse)] rounded-lg hover:bg-[var(--navy-light)] transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              {loading && <Loader2 size={14} className="animate-spin" aria-hidden />}
              Registrar
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
