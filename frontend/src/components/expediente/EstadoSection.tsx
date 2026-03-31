"use client";

import { useState } from "react";
import { Pencil, Check, X, ExternalLink } from "lucide-react";
import api from "@/lib/api";
import toast from "react-hot-toast";
import UrlField from "@/components/UrlField";
import { useOperadoPor, OperadoPor } from "@/hooks/useOperadoPor";
import FactoryOrderTable, { FactoryOrder } from "@/components/expediente/FactoryOrderTable";
import { ARTIFACT_UI_REGISTRY } from "@/constants/artifact-ui-registry";

// State machine FROZEN v1.2.2 — never add states here
const READONLY_STATES = ["PI_SOLICITADA", "EN_DESTINO", "CERRADO", "CANCELADO"];

interface ExpedienteFields {
  id: number | string;
  status: string;
  ref_number?: string;
  purchase_order_number?: string;
  client?: string;
  operado_por?: OperadoPor;
  credit_days?: number;
  credit_limit?: number;
  order_value?: number;
  url_orden_compra?: string | null;
  // CONFIRMADO
  product_lines?: unknown[];
  currency?: string;
  incoterms?: string;
  notes?: string;
  // PRODUCCION
  factory_orders?: FactoryOrder[];
  production_status?: string;
  quality_notes?: string;
  // PREPARACION
  estimated_production_date?: string;
  // DESPACHO
  shipping_date?: string;
  tracking_url?: string | null;
  dispatch_notes?: string;
  weight_kg?: number;
  packages_count?: number;
  // TRANSITO
  intermediate_airport_or_port?: string;
  transit_arrival_date?: string;
  url_packing_list_detallado?: string | null;
  // MERGE
  merged_with?: Array<{ id: number | string; ref_number?: string; custom_ref?: string; is_master?: boolean }>;
  [key: string]: unknown;
}

interface Props {
  expediente: ExpedienteFields;
  onRefresh: () => void;
}

export default function EstadoSection({ expediente, onRefresh }: Props) {
  const status = expediente.status as string;
  const isReadOnly = READONLY_STATES.includes(status);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [draft, setDraft] = useState<Record<string, unknown>>({});

  const operadoPor = (expediente.operado_por ?? null) as OperadoPor;
  const { showClientFields, showMwtFields, showBanner } = useOperadoPor(operadoPor);

  const startEdit = () => {
    setDraft({});
    setEditing(true);
  };

  const cancelEdit = () => {
    setDraft({});
    setEditing(false);
  };

  const field = (key: string): unknown => (key in draft ? draft[key] : expediente[key]);
  const setField = (key: string, val: unknown) => setDraft((d) => ({ ...d, [key]: val }));

  const save = async () => {
    if (Object.keys(draft).length === 0) { setEditing(false); return; }
    setSaving(true);
    try {
      const id = expediente.id;
      const endpointMap: Record<string, string> = {
        REGISTRO: `expedientes/${id}/`,
        CONFIRMADO: `expedientes/${id}/confirmado/`,
        PRODUCCION: `expedientes/${id}/produccion/`,
        PREPARACION: `expedientes/${id}/preparacion/`,
        DESPACHO: `expedientes/${id}/despacho/`,
        TRANSITO: `expedientes/${id}/transito/`,
      };
      const endpoint = endpointMap[status];
      if (!endpoint) { toast.error("Estado sin endpoint PATCH"); setSaving(false); return; }
      await api.patch(endpoint, draft);
      toast.success("Guardado correctamente");
      setEditing(false);
      setDraft({});
      onRefresh();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      toast.error(e.response?.data?.detail ?? "Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  const inputCls = "w-full bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm text-[var(--color-text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-navy)]/30";
  const rowCls = "flex flex-col gap-1";
  const labelCls = "text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider";
  const valueCls = "text-sm text-[var(--color-text-primary)]";

  const renderField = (label: string, key: string, type: "text" | "number" | "date" = "text") => {
    const val = field(key);
    if (!editing || isReadOnly) {
      return (
        <div className={rowCls}>
          <span className={labelCls}>{label}</span>
          <span className={valueCls}>{val !== undefined && val !== null && val !== "" ? String(val) : "—"}</span>
        </div>
      );
    }
    return (
      <div className={rowCls}>
        <label className={labelCls}>{label}</label>
        <input
          type={type}
          value={val !== null && val !== undefined ? String(val) : ""}
          onChange={(e) => setField(key, e.target.value)}
          className={inputCls}
        />
      </div>
    );
  };

  const renderUrlField = (label: string, key: string) => (
    <UrlField
      label={label}
      url={(field(key) as string | null) ?? null}
      readOnly={isReadOnly || !editing}
      onUpdate={(url) => { setField(key, url); if (!editing) save(); }}
      onDelete={() => { setField(key, null); if (!editing) save(); }}
    />
  );

  // ── Operado por banner ──
  const renderOperadorBanner = () => (
    showBanner ? (
      <div className="col-span-2 flex items-center gap-2 text-xs text-[var(--color-text-tertiary)] italic bg-[var(--color-bg-alt)] border border-[var(--color-border)] rounded-lg px-3 py-2">
        &#9888;&#65039; Seleccionar operador para ver campos condicionados
      </div>
    ) : null
  );

  // ── Render by state ──
  const renderContent = () => {
    switch (status) {
      case "REGISTRO":
        return (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {renderField("N\u00b0 Referencia", "ref_number")}
            {renderField(`N\u00ba ${ARTIFACT_UI_REGISTRY["ART-01"].label}`, "purchase_order_number")}
            {renderField("Cliente", "client")}
            <div className={rowCls}>
              <label className={labelCls}>Operado por</label>
              {editing ? (
                <select value={(field("operado_por") as string) ?? ""} onChange={(e) => setField("operado_por", e.target.value || null)} className={inputCls}>
                  <option value="">Sin definir</option>
                  <option value="CLIENTE">CLIENTE</option>
                  <option value="MWT">MWT</option>
                </select>
              ) : (
                <span className={valueCls}>{(expediente.operado_por as string) ?? "—"}</span>
              )}
            </div>
            {renderField("D\u00edas cr\u00e9dito", "credit_days", "number")}
            {renderField("L\u00edmite cr\u00e9dito", "credit_limit", "number")}
            {renderField("Valor orden", "order_value", "number")}
            {renderUrlField(`${ARTIFACT_UI_REGISTRY["ART-01"].label} (URL)`, "url_orden_compra")}
          </div>
        );

      case "PI_SOLICITADA":
        return (
          <p className="text-sm text-[var(--color-text-tertiary)] italic">
            Proforma solicitada — estado de solo lectura.
          </p>
        );

      case "CONFIRMADO":
        return (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {renderField("Moneda", "currency")}
            {renderField("Incoterms", "incoterms")}
            {renderField("Notas", "notes")}
          </div>
        );

      case "PRODUCCION":
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {renderField("Estado producci\u00f3n", "production_status")}
              {renderField("Notas calidad", "quality_notes")}
            </div>
            {renderOperadorBanner()}
            <FactoryOrderTable
              expedienteId={expediente.id}
              factoryOrders={(expediente.factory_orders as FactoryOrder[]) ?? []}
              operadoPor={operadoPor}
              onRefresh={onRefresh}
              readOnly={isReadOnly}
            />
          </div>
        );

      case "PREPARACION":
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {renderField("Fecha estimada producci\u00f3n", "estimated_production_date", "date")}
            </div>
            {renderOperadorBanner()}
            <FactoryOrderTable
              expedienteId={expediente.id}
              factoryOrders={(expediente.factory_orders as FactoryOrder[]) ?? []}
              operadoPor={operadoPor}
              onRefresh={onRefresh}
              readOnly={isReadOnly}
            />
          </div>
        );

      case "DESPACHO":
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {renderField("Fecha despacho", "shipping_date", "date")}
              <div className={rowCls}>
                <span className={labelCls}>Tracking URL</span>
                {editing ? (
                  <input type="url" value={(field("tracking_url") as string) ?? ""} onChange={(e) => setField("tracking_url", e.target.value)} className={inputCls} placeholder="https://..." />
                ) : field("tracking_url") ? (
                  <a href={String(field("tracking_url"))} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-sm text-[var(--color-navy)] hover:underline">
                    <ExternalLink className="w-3.5 h-3.5" /> {String(field("tracking_url"))}
                  </a>
                ) : <span className={valueCls}>{"—"}</span>}
              </div>
              {renderField("Notas despacho", "dispatch_notes")}
              {renderField("Peso (kg)", "weight_kg", "number")}
              {renderField("Bultos", "packages_count", "number")}
            </div>
            {renderOperadorBanner()}
            <FactoryOrderTable
              expedienteId={expediente.id}
              factoryOrders={(expediente.factory_orders as FactoryOrder[]) ?? []}
              operadoPor={operadoPor}
              onRefresh={onRefresh}
              readOnly={isReadOnly}
              showDespachoFields
            />
          </div>
        );

      case "TRANSITO":
        return (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {renderField("Aeropuerto / Puerto intermedio", "intermediate_airport_or_port")}
            {renderField("Fecha llegada tr\u00e1nsito", "transit_arrival_date", "date")}
            <div className={rowCls}>
              <span className={labelCls}>Tracking URL (carry-forward)</span>
              {field("tracking_url") ? (
                <a href={String(field("tracking_url"))} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-sm text-[var(--color-navy)] hover:underline">
                  <ExternalLink className="w-3.5 h-3.5" /> {String(field("tracking_url"))}
                </a>
              ) : <span className={valueCls}>{"—"}</span>}
            </div>
            {renderUrlField("Packing List Detallado", "url_packing_list_detallado")}
          </div>
        );

      case "EN_DESTINO":
      case "CERRADO":
      case "CANCELADO":
        return (
          <p className="text-sm text-[var(--color-text-tertiary)] italic">
            Estado {status} &mdash; solo lectura.
          </p>
        );

      default:
        return null;
    }
  };

  return (
    <div className="space-y-4">
      {!isReadOnly && (
        <div className="flex justify-end gap-2">
          {editing ? (
            <>
              <button
                type="button"
                onClick={cancelEdit}
                disabled={saving}
                className="flex items-center gap-1.5 text-xs border border-[var(--color-border)] text-[var(--color-text-secondary)] rounded-lg px-3 py-1.5 hover:bg-[var(--color-bg-alt)] transition-colors"
              >
                <X className="w-3.5 h-3.5" /> Cancelar
              </button>
              <button
                type="button"
                onClick={save}
                disabled={saving}
                className="flex items-center gap-1.5 text-xs bg-[var(--color-navy)] text-white rounded-lg px-3 py-1.5 hover:opacity-80 disabled:opacity-50 transition-opacity"
              >
                {saving ? (
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Check className="w-3.5 h-3.5" />
                )}
                Guardar
              </button>
            </>
          ) : (
            <button
              type="button"
              onClick={startEdit}
              className="flex items-center gap-1.5 text-xs border border-[var(--color-border)] text-[var(--color-text-secondary)] rounded-lg px-3 py-1.5 hover:bg-[var(--color-bg-alt)] transition-colors"
            >
              <Pencil className="w-3.5 h-3.5" /> Editar
            </button>
          )}
        </div>
      )}

      {renderContent()}
    </div>
  );
}
