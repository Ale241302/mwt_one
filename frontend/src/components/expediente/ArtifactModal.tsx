"use client";
/**
 * S10-04b — ArtifactModal × 10 formularios
 * Renders the correct form based on artifact_type.
 * Commands: C2-C18, C21, C22 (IssueCommissionInvoice).
 */
import { useState } from "react";
import { X, FileText, Package, Truck, DollarSign, CreditCard, XCircle, Lock, Unlock, Receipt } from "lucide-react";
import api from "@/lib/api";

interface ArtifactModalProps {
  open: boolean;
  expedienteId: string;
  commandKey: string;  // C2 – C22
  onClose: () => void;
  onSuccess: () => void;
}

const COMMAND_META: Record<string, { label: string; endpoint: string; icon: React.ReactNode; color: string }> = {
  C2:  { label: "Registrar OC",             endpoint: "register-oc",            icon: <FileText size={18}/>,   color: "#1D4ED8" },
  C3:  { label: "Registrar Proforma",        endpoint: "register-proforma",      icon: <FileText size={18}/>,   color: "#7C3AED" },
  C4:  { label: "Decidir Modo",              endpoint: "decide-mode",            icon: <Package size={18}/>,    color: "#B45309" },
  C5:  { label: "Confirmar SAP",             endpoint: "confirm-sap",            icon: <Package size={18}/>,    color: "#0E8A6D" },
  C6:  { label: "Confirmar Producción",      endpoint: "confirm-production",     icon: <Package size={18}/>,    color: "#0E8A6D" },
  C7:  { label: "Registrar Embarque",        endpoint: "register-shipment",      icon: <Truck size={18}/>,      color: "#1D4ED8" },
  C8:  { label: "Cotización Flete",          endpoint: "register-freight-quote", icon: <DollarSign size={18}/>, color: "#B45309" },
  C9:  { label: "Registrar Aduana",          endpoint: "register-customs",       icon: <FileText size={18}/>,   color: "#7C3AED" },
  C10: { label: "Aprobar Despacho",          endpoint: "approve-dispatch",       icon: <Truck size={18}/>,      color: "#0E8A6D" },
  C11: { label: "Confirmar Salida",          endpoint: "confirm-departure",      icon: <Truck size={18}/>,      color: "#1D4ED8" },
  C12: { label: "Confirmar Llegada",         endpoint: "confirm-arrival",        icon: <Truck size={18}/>,      color: "#0E8A6D" },
  C13: { label: "Emitir Factura",            endpoint: "issue-invoice",          icon: <Receipt size={18}/>,    color: "#0E8A6D" },
  C14: { label: "Cerrar Expediente",         endpoint: "close",                  icon: <Lock size={18}/>,       color: "#475569" },
  C15: { label: "Registrar Costo",           endpoint: "register-cost",          icon: <DollarSign size={18}/>, color: "#B45309" },
  C16: { label: "Cancelar Expediente",       endpoint: "cancel",                 icon: <XCircle size={18}/>,    color: "#DC2626" },
  C17: { label: "Bloquear Expediente",       endpoint: "block",                  icon: <Lock size={18}/>,       color: "#DC2626" },
  C18: { label: "Desbloquear Expediente",    endpoint: "unblock",                icon: <Unlock size={18}/>,     color: "#0E8A6D" },
  C21: { label: "Registrar Pago",            endpoint: "register-payment",       icon: <CreditCard size={18}/>, color: "#0E8A6D" },
  C22: { label: "Emitir Factura Comisión",  endpoint: "issue-commission-invoice",icon: <Receipt size={18}/>,    color: "#7C3AED" },
};

type FormData = Record<string, string | number | boolean>;

function CommandForm({ commandKey, form, setForm }: { commandKey: string; form: FormData; setForm: (f: FormData) => void }) {
  const set = (k: string, v: string | number | boolean) => setForm({ ...form, [k]: v });
  const inp = (label: string, key: string, type: string = "text", placeholder: string = "") => (
    <div key={key}>
      <label className="th-label block mb-1">{label}</label>
      <input
        type={type} className="input" placeholder={placeholder}
        value={String(form[key] ?? "")}
        onChange={(e) => set(key, type === "number" ? Number(e.target.value) : e.target.value)}
      />
    </div>
  );

  switch (commandKey) {
    case "C2": return <>{inp("Número OC", "oc_number", "text", "OC-2024-001")}{inp("Notas", "notes")}  </>;
    case "C3": return <>{inp("Número proforma", "proforma_number", "text", "PRF-001")}{inp("Monto (USD)", "amount", "number", "0")} </>;
    case "C4": return (
      <div>
        <label className="th-label block mb-1">Modo logístico</label>
        <select className="input" value={String(form.mode ?? "maritime")} onChange={(e) => set("mode", e.target.value)}>
          <option value="maritime">Marítimo</option>
          <option value="air">Aéreo</option>
          <option value="land">Terrestre</option>
        </select>
      </div>
    );
    case "C5": return <>{inp("Número SAP", "sap_number", "text", "SAP-00001")}</>;
    case "C6": return <>{inp("Notas de producción", "notes")} </>;
    case "C7": return (
      <>{inp("Número BL", "bl_number", "text", "MSCUXXX")}{inp("Transportista", "carrier")}{inp("Puerto origen", "origin_port")}{inp("Puerto destino", "destination_port")}</>
    );
    case "C8": return <>{inp("Monto flete (USD)", "freight_amount", "number", "0")}{inp("Proveedor", "provider")}</>;
    case "C9": return <>{inp("Agencia aduanal", "customs_agency")}{inp("Número declaración", "declaration_number")}</>;
    case "C10": return <>{inp("Observaciones", "notes")}</>;
    case "C11": return <>{inp("Fecha salida", "departure_date", "date")}{inp("Notas", "notes")}</>;
    case "C12": return <>{inp("Fecha llegada", "arrival_date", "date")}{inp("Notas", "notes")}</>;
    case "C13": return <>{inp("Número factura", "invoice_number", "text", "INV-001")}{inp("Monto cliente (USD)", "total_client_view", "number", "0")}</>;
    case "C14": return <>{inp("Razón de cierre", "reason")}</>;
    case "C15": return (
      <>
        {inp("Tipo de costo", "cost_type", "text", "freight")}
        {inp("Monto (USD)", "amount", "number", "0")}
        <div>
          <label className="th-label block mb-1">Visibilidad</label>
          <select className="input" value={String(form.visibility ?? "internal")} onChange={(e) => set("visibility", e.target.value)}>
            <option value="internal">Interna</option>
            <option value="client">Cliente</option>
          </select>
        </div>
      </>
    );
    case "C16": return <>{inp("Razón de cancelación", "reason")}</>;
    case "C17": return <>{inp("Razón de bloqueo", "reason")}</>;
    case "C18": return <>{inp("Notas de desbloqueo", "notes")}</>;
    case "C21": return (
      <>
        {inp("Monto (USD)", "amount", "number", "0")}
        <div>
          <label className="th-label block mb-1">Método de pago</label>
          <select className="input" value={String(form.method ?? "wire")} onChange={(e) => set("method", e.target.value)}>
            <option value="wire">Wire transfer</option>
            <option value="check">Cheque</option>
            <option value="cash">Efectivo</option>
            <option value="crypto">Cripto</option>
          </select>
        </div>
        {inp("Referencia", "reference", "text", "REF-001")}
      </>
    );
    case "C22": return (
      <>
        {inp("Número factura comisión", "invoice_number", "text", "CINV-001")}
        {inp("Monto comisión (USD)", "commission_amount", "number", "0")}
        {inp("Porcentaje comisión", "commission_pct", "number", "0")}
        {inp("Notas", "notes")}
      </>
    );
    default: return <p className="text-sm text-text-secondary">Formulario no disponible para {commandKey}.</p>;
  }
}

export default function ArtifactModal({ open, expedienteId, commandKey, onClose, onSuccess }: ArtifactModalProps) {
  const [form, setForm] = useState<FormData>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const meta = COMMAND_META[commandKey];

  const handleSubmit = async () => {
    if (!meta) return;
    setLoading(true);
    setError(null);
    try {
      await api.post(`/expedientes/${expedienteId}/${meta.endpoint}/`, form);
      setForm({});
      onSuccess();
      onClose();
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: Record<string, unknown> } };
      const errData = axiosErr?.response?.data;
      setError(
        errData
          ? Object.entries(errData).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(", ") : v}`).join(" | ")
          : "Error al ejecutar el comando."
      );
    } finally {
      setLoading(false);
    }
  };

  if (!open || !meta) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" role="dialog" aria-modal="true">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-md max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <div className="flex items-center gap-2">
            <span style={{ color: meta.color }}>{meta.icon}</span>
            <h2 className="text-base font-semibold text-navy">{meta.label}</h2>
            <span className="text-xs font-mono text-text-tertiary ml-1">{commandKey}</span>
          </div>
          <button
            className="p-1.5 rounded-lg hover:bg-bg transition-colors"
            onClick={onClose}
            aria-label="Cerrar modal"
          >
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-4 space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-coral-soft/20 border border-coral/30 text-sm text-coral">
              {error}
            </div>
          )}
          <CommandForm commandKey={commandKey} form={form} setForm={setForm} />
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-border">
          <button className="btn btn-md btn-secondary" onClick={onClose} disabled={loading}>Cancelar</button>
          <button
            className="btn btn-md btn-primary"
            onClick={handleSubmit}
            disabled={loading}
            style={{ background: meta.color, borderColor: meta.color }}
          >
            {loading ? "Ejecutando..." : meta.label}
          </button>
        </div>
      </div>
    </div>
  );
}
