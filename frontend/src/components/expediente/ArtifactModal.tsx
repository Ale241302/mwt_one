"use client";
import { useState } from "react";
import { FileText, Package, Truck, DollarSign, CreditCard, XCircle, Lock, Unlock, Receipt, PlusCircle, History, ChevronRight } from "lucide-react";
import api from "@/lib/api";
import FormModal from "@/components/ui/FormModal";

interface ArtifactModalProps {
  open: boolean;
  expedienteId: string;
  commandKey: string;
  artifact?: any;
  readOnly?: boolean;
  onClose: () => void;
  onSuccess: () => void;
  /** Si es admin, muestra el botón "Nuevo registro" en modo readOnly */
  isAdmin?: boolean;
  /** Callback para abrir un nuevo formulario vacío desde el readOnly */
  onNewRecord?: () => void;
  /** Lista completa de todos los registros previos de este mismo tipo */
  allArtifacts?: any[];
}

const COMMAND_META: Record<string, { label: string; endpoint: string; icon: React.ReactNode; color: string; bgClass: string; textClass: string }> = {
  C3: { label: "Registrar OC", endpoint: "register-oc", icon: <FileText size={18} />, color: "var(--brand-primary)", bgClass: "bg-blue-700 border-blue-700", textClass: "text-blue-700" },
  C2: { label: "Registrar Proforma", endpoint: "register-proforma", icon: <FileText size={18} />, color: "var(--brand-primary)", bgClass: "bg-purple-600 border-purple-600", textClass: "text-purple-600" },
  C4: { label: "Decidir Modo", endpoint: "decide-mode", icon: <Package size={18} />, color: "var(--brand-primary)", bgClass: "bg-amber-700 border-amber-700", textClass: "text-amber-700" },
  C5: { label: "Confirmar SAP", endpoint: "confirm-sap", icon: <Package size={18} />, color: "var(--brand-primary)", bgClass: "bg-amber-700 border-amber-700", textClass: "text-amber-700" },
  C6: { label: "Confirmar Producción", endpoint: "confirm-production", icon: <Package size={18} />, color: "var(--brand-primary)", bgClass: "bg-brand-primary border-brand-primary", textClass: "text-brand-primary" },
  C7: { label: "Registrar Embarque", endpoint: "register-shipment", icon: <Truck size={18} />, color: "var(--brand-primary)", bgClass: "bg-blue-700 border-blue-700", textClass: "text-blue-700" },
  C8: { label: "Cotización Flete", endpoint: "register-freight-quote", icon: <DollarSign size={18} />, color: "var(--brand-primary)", bgClass: "bg-amber-700 border-amber-700", textClass: "text-amber-700" },
  C9: { label: "Registrar Aduana", endpoint: "register-customs", icon: <FileText size={18} />, color: "var(--brand-primary)", bgClass: "bg-purple-600 border-purple-600", textClass: "text-purple-600" },
  C10: { label: "Aprobar Despacho", endpoint: "approve-dispatch", icon: <Truck size={18} />, color: "var(--brand-primary)", bgClass: "bg-brand-primary border-brand-primary", textClass: "text-brand-primary" },
  C11: { label: "Confirmar Salida (MWT)", endpoint: "confirm-departure-mwt", icon: <Truck size={18} />, color: "var(--brand-primary)", bgClass: "bg-blue-700 border-blue-700", textClass: "text-blue-700" },
  C11B: { label: "Confirmar Salida (China)", endpoint: "confirm-departure-china", icon: <Truck size={18} />, color: "var(--brand-primary)", bgClass: "bg-blue-700 border-blue-700", textClass: "text-blue-700" },
  C12: { label: "Confirmar Llegada", endpoint: "confirm-arrival", icon: <Truck size={18} />, color: "var(--brand-primary)", bgClass: "bg-brand-primary border-brand-primary", textClass: "text-brand-primary" },
  C13: { label: "Emitir Factura MWT", endpoint: "issue-invoice", icon: <Receipt size={18} />, color: "var(--brand-primary)", bgClass: "bg-brand-primary border-brand-primary", textClass: "text-brand-primary" },
  C14: { label: "Cerrar Expediente", endpoint: "close", icon: <Lock size={18} />, color: "var(--brand-primary)", bgClass: "bg-slate-600 border-slate-600", textClass: "text-slate-600" },
  C15: { label: "Registrar Costo", endpoint: "register-cost", icon: <DollarSign size={18} />, color: "var(--brand-primary)", bgClass: "bg-amber-700 border-amber-700", textClass: "text-amber-700" },
  C16: { label: "Cancelar Expediente", endpoint: "cancel", icon: <XCircle size={18} />, color: "var(--brand-primary)", bgClass: "bg-red-600 border-red-600", textClass: "text-red-600" },
  C17: { label: "Bloquear Expediente", endpoint: "block", icon: <Lock size={18} />, color: "var(--brand-primary)", bgClass: "bg-red-600 border-red-600", textClass: "text-red-600" },
  C18: { label: "Desbloquear Expediente", endpoint: "unblock", icon: <Unlock size={18} />, color: "var(--brand-primary)", bgClass: "bg-brand-primary border-brand-primary", textClass: "text-brand-primary" },
  C21: { label: "Registrar Pago", endpoint: "register-payment", icon: <CreditCard size={18} />, color: "var(--brand-primary)", bgClass: "bg-brand-primary border-brand-primary", textClass: "text-brand-primary" },
  C22: { label: "Emitir Factura Comisión", endpoint: "issue-commission-invoice", icon: <Receipt size={18} />, color: "var(--brand-primary)", bgClass: "bg-purple-600 border-purple-600", textClass: "text-purple-600" },
  C30: { label: "Materializar Logística", endpoint: "materialize-logistics", icon: <Package size={18} />, color: "var(--brand-primary)", bgClass: "bg-amber-700 border-amber-700", textClass: "text-amber-700" },
};

type FormData = Record<string, string | number | boolean>;

function CommandForm({
  commandKey,
  form,
  setForm,
  isReadOnly,
}: {
  commandKey: string;
  form: FormData;
  setForm: (f: FormData) => void;
  isReadOnly?: boolean;
}) {
  const set = (k: string, v: string | number | boolean) => {
    if (isReadOnly) return;
    setForm({ ...form, [k]: v });
  };
  const inp = (label: string, key: string, type: string = "text", placeholder: string = "") => (
    <div key={key}>
      <label className="th-label block mb-1">{label}</label>
      <input
        type={type}
        className="input w-full"
        placeholder={placeholder}
        value={String(form[key] ?? "")}
        onChange={(e) => set(key, type === "number" ? Number(e.target.value) : e.target.value)}
        disabled={isReadOnly}
      />
    </div>
  );

  switch (commandKey) {
    case "C3": return <div className="space-y-3">{inp("Número OC", "oc_number", "text", "OC-2024-001")}{inp("Notas", "notes")}</div>;
    case "C2": return <div className="space-y-3">{inp("Número proforma", "proforma_number", "text", "PRF-001")}{inp("Monto (USD)", "amount", "number", "0")}</div>;
    case "C4": return (
      <div className="space-y-3">
        <div>
          <label className="th-label block mb-1">Modo logístico</label>
          <select className="input w-full" value={String(form.mode ?? "maritime")} onChange={(e) => set("mode", e.target.value)} disabled={isReadOnly}>
            <option value="maritime">Marítimo</option>
            <option value="air">Aéreo</option>
            <option value="land">Terrestre</option>
          </select>
        </div>
      </div>
    );
    case "C5": return <div className="space-y-3">{inp("Número SAP", "sap_number", "text", "SAP-00001")}</div>;
    case "C6": return <div className="space-y-3">{inp("Notas de producción", "notes")}</div>;
    case "C7": return <div className="space-y-3">{inp("Número BL", "bl_number", "text", "MSCUXXX")}{inp("Transportista", "carrier")}{inp("Puerto origen", "origin_port")}{inp("Puerto destino", "destination_port")}</div>;
    case "C8": return <div className="space-y-3">{inp("Monto flete (USD)", "freight_amount", "number", "0")}{inp("Proveedor", "provider")}</div>;
    case "C9": return <div className="space-y-3">{inp("Agencia aduanal", "customs_agency")}{inp("Número declaración", "declaration_number")}</div>;
    case "C10": return <div className="space-y-3">{inp("Observaciones", "notes")}</div>;
    case "C11": return <div className="space-y-3">{inp("Fecha salida MWT", "departure_date", "date")}{inp("Notas", "notes")}</div>;
    case "C11B": return <div className="space-y-3">{inp("Fecha salida China", "departure_date", "date")}{inp("Notas", "notes")}</div>;
    case "C12": return <div className="space-y-3">{inp("Fecha llegada", "arrival_date", "date")}{inp("Notas", "notes")}</div>;
    case "C13": return <div className="space-y-3">{inp("Número factura", "invoice_number", "text", "INV-001")}{inp("Monto cliente (USD)", "total_client_view", "number", "0")}</div>;
    case "C14": return <div className="space-y-3">{inp("Razón de cierre", "reason")}</div>;
    case "C15": return (
      <div className="space-y-3">
        {inp("Tipo de costo", "cost_type", "text", "freight")}
        {inp("Monto (USD)", "amount", "number", "0")}
        {inp("Divisa", "currency", "text", "USD")}
        <div>
          <label className="th-label block mb-1">Visibilidad</label>
          <select className="input w-full" value={String(form.visibility ?? "internal")} onChange={(e) => set("visibility", e.target.value)} disabled={isReadOnly}>
            <option value="internal">Interna</option>
            <option value="client">Cliente</option>
          </select>
        </div>
      </div>
    );
    case "C16": return <div className="space-y-3">{inp("Razón de cancelación", "reason")}</div>;
    case "C17": return <div className="space-y-3">{inp("Razón de bloqueo", "reason")}</div>;
    case "C18": return <div className="space-y-3">{inp("Notas de desbloqueo", "notes")}</div>;
    case "C21": return (
      <div className="space-y-3">
        {inp("Monto (USD)", "amount", "number", "0")}
        <div>
          <label className="th-label block mb-1">Método de pago</label>
          <select className="input w-full" value={String(form.method ?? "wire")} onChange={(e) => set("method", e.target.value)} disabled={isReadOnly}>
            <option value="wire">Wire transfer</option>
            <option value="check">Cheque</option>
            <option value="cash">Efectivo</option>
            <option value="crypto">Cripto</option>
          </select>
        </div>
        {inp("Referencia", "reference", "text", "REF-001")}
      </div>
    );
    case "C22": return (
      <div className="space-y-3">
        {inp("Número factura comisión", "invoice_number", "text", "CINV-001")}
        {inp("Monto comisión (USD)", "commission_amount", "number", "0")}
        {inp("Porcentaje comisión", "commission_pct", "number", "0")}
        {inp("Notas", "notes")}
      </div>
    );
    case "C30": return (
      <div className="space-y-3">
        {inp("ID de Opción Logística", "option_id", "text", "OPT-01")}
      </div>
    );
    default: return <p className="text-sm text-text-secondary">Formulario no disponible para {commandKey}.</p>;
  }
}

export default function ArtifactModal({
  open,
  expedienteId,
  commandKey,
  artifact,
  readOnly: readOnlyProp,
  onClose,
  onSuccess,
  isAdmin,
  onNewRecord,
  allArtifacts,
}: ArtifactModalProps) {
  const isReadOnly = readOnlyProp === true || (!!artifact && readOnlyProp !== false);

  const [activeTab, setActiveTab] = useState<"form" | "history">("form");
  const [form, setForm] = useState<FormData>(artifact?.payload || {});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const meta = COMMAND_META[commandKey];

  if (!open || !meta) return null;

  // History entries, newest first, excluding the currently viewed artifact
  const historyEntries = (allArtifacts || []).filter(
    (a) => !artifact || a !== artifact
  );

  const handleSubmit = async () => {
    // Guard: evitar POST si el expedienteId no está disponible (race condition)
    if (!expedienteId) {
      setError("Error: ID de expediente no disponible. Recarga la página e intenta de nuevo.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await api.post(`/expedientes/${expedienteId}/commands/${meta.endpoint}/`, form);
      setForm({});
      onSuccess();
      onClose();
    } catch (err: any) {
      const errData = err?.response?.data;
      setError(
        errData
          ? Object.entries(errData)
            .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(", ") : v}`)
            .join(" | ")
          : "Error al ejecutar el comando."
      );
    } finally {
      setLoading(false);
    }
  };

  const modalTitle = isReadOnly
    ? `Detalle — ${meta.label} (${commandKey})`
    : `${meta.label} (${commandKey})`;

  // Tab bar: only show when there are history entries
  const showTabs = isReadOnly && historyEntries.length > 0;

  const footerContent = (
    <div className="flex items-center justify-between w-full gap-2">
      <div className="flex items-center gap-2">
        {/* En modo readOnly: botón "Nuevo registro" para crear uno adicional */}
        {isReadOnly && onNewRecord && (
          <button
            className="btn btn-sm btn-ghost border border-primary text-primary flex items-center gap-1"
            onClick={() => { onClose(); onNewRecord(); }}
            disabled={loading}
          >
            <PlusCircle size={13} /> Nuevo registro
          </button>
        )}
      </div>
      <div className="flex items-center gap-2">
        <button className="btn btn-md btn-secondary" onClick={onClose} disabled={loading}>
          {isReadOnly ? "Cerrar" : "Cancelar"}
        </button>
        {!isReadOnly && (
          <button
            className={`btn btn-md text-white ${meta.bgClass}`}
            onClick={handleSubmit}
            disabled={loading || !expedienteId}
          >
            {loading ? "Ejecutando..." : meta.label}
          </button>
        )}
      </div>
    </div>
  );

  return (
    <FormModal
      open={open}
      title={modalTitle}
      onClose={onClose}
      footer={footerContent}
      size="sm"
    >
      {/* Tab Navigation */}
      {showTabs && (
        <div className="flex gap-1 mb-4 border-b border-divider">
          <button
            onClick={() => setActiveTab("form")}
            className={`px-4 py-2 text-sm font-medium transition-colors ${activeTab === "form"
              ? "border-b-2 border-primary text-primary"
              : "text-text-tertiary hover:text-text"
              }`}
          >
            Registro actual
          </button>
          <button
            onClick={() => setActiveTab("history")}
            className={`px-4 py-2 text-sm font-medium flex items-center gap-1 transition-colors ${activeTab === "history"
              ? "border-b-2 border-primary text-primary"
              : "text-text-tertiary hover:text-text"
              }`}
          >
            <History size={13} />
            Historial
            <span className="ml-1 text-[10px] bg-slate-100 text-slate-600 rounded-full px-1.5">
              {historyEntries.length}
            </span>
          </button>
        </div>
      )}

      {activeTab === "history" ? (
        /* History Tab */
        <div className="space-y-2">
          {historyEntries.length === 0 ? (
            <p className="text-sm text-text-tertiary py-4 text-center">
              No hay registros previos.
            </p>
          ) : (
            historyEntries.map((h, i) => (
              <div
                key={i}
                className="flex items-center justify-between p-3 rounded-lg border border-divider hover:bg-bg transition-colors cursor-pointer"
                onClick={() => {
                  setActiveTab("form");
                  setForm(h.payload || {});
                }}
              >
                <div className="flex items-center gap-2">
                  <span className="text-text-tertiary text-[11px]">{i + 1}.</span>
                  <span
                    className={`badge text-[10px] px-1.5 py-0.5 ${
                      h.status === "COMPLETED" || h.status === "completed"
                        ? "badge-success"
                        : h.status === "VOIDED" || h.status === "voided"
                          ? "badge-critical"
                          : "badge-info"
                    }`}
                  >
                    {h.status}
                  </span>
                  <span className="text-text-tertiary text-[11px]">
                    {new Date(h.created_at).toLocaleDateString("es-CO", {
                      day: "2-digit",
                      month: "short",
                      year: "numeric",
                    })}
                  </span>
                </div>
                <ChevronRight size={14} className="text-text-tertiary" />
              </div>
            ))
          )}
        </div>
      ) : (
        /* Form Tab (default) */
        <>
          {isReadOnly && (
            <div className="mb-4 px-3 py-2 rounded-lg bg-bg border border-divider text-xs text-text-tertiary">
              Registro en solo lectura.
              {onNewRecord
                ? ' Usa el botón "Nuevo registro" para agregar uno adicional.'
                : ' Usa "Nuevo registro" en el artefacto para actualizarlo.'}
            </div>
          )}
          {error && (
            <div className="p-3 mb-4 rounded-lg bg-coral-soft/20 border border-coral/30 text-sm text-coral">
              {error}
            </div>
          )}
          <CommandForm
            commandKey={commandKey}
            form={form}
            setForm={setForm}
            isReadOnly={isReadOnly}
          />
        </>
      )}
    </FormModal>
  );
}
