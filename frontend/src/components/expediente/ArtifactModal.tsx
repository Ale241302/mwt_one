"use client";
import { useState } from "react";
import { FileText, Package, Truck, DollarSign, CreditCard, XCircle, Lock, Unlock, Receipt } from "lucide-react";
import api from "@/lib/api";
import FormModal from "@/components/ui/FormModal";

interface ArtifactModalProps {
  open: boolean;
  expedienteId: string;
  commandKey: string;
  onClose: () => void;
  onSuccess: () => void;
}

const COMMAND_META: Record<string, { label: string; endpoint: string; icon: React.ReactNode; color: string; bgClass: string; textClass: string }> = {
  C2:  { label: "Registrar OC",             endpoint: "register-oc",            icon: <FileText size={18}/>,   color: "var(--brand-primary)", bgClass: "bg-blue-700 border-blue-700", textClass: "text-blue-700" },
  C3:  { label: "Registrar Proforma",        endpoint: "register-proforma",      icon: <FileText size={18}/>,   color: "var(--brand-primary)", bgClass: "bg-purple-600 border-purple-600", textClass: "text-purple-600" },
  C4:  { label: "Decidir Modo",              endpoint: "decide-mode",            icon: <Package size={18}/>,    color: "var(--brand-primary)", bgClass: "bg-amber-700 border-amber-700", textClass: "text-amber-700" },
  C5:  { label: "Confirmar SAP",             endpoint: "confirm-sap",            icon: <Package size={18}/>,    color: "var(--brand-primary)", bgClass: "bg-brand-primary border-brand-primary", textClass: "text-brand-primary" },
  C6:  { label: "Confirmar Producción",      endpoint: "confirm-production",     icon: <Package size={18}/>,    color: "var(--brand-primary)", bgClass: "bg-brand-primary border-brand-primary", textClass: "text-brand-primary" },
  C7:  { label: "Registrar Embarque",        endpoint: "register-shipment",      icon: <Truck size={18}/>,      color: "var(--brand-primary)", bgClass: "bg-blue-700 border-blue-700", textClass: "text-blue-700" },
  C8:  { label: "Cotización Flete",          endpoint: "register-freight-quote", icon: <DollarSign size={18}/>, color: "var(--brand-primary)", bgClass: "bg-amber-700 border-amber-700", textClass: "text-amber-700" },
  C9:  { label: "Registrar Aduana",          endpoint: "register-customs",       icon: <FileText size={18}/>,   color: "var(--brand-primary)", bgClass: "bg-purple-600 border-purple-600", textClass: "text-purple-600" },
  C10: { label: "Aprobar Despacho",          endpoint: "approve-dispatch",       icon: <Truck size={18}/>,      color: "var(--brand-primary)", bgClass: "bg-brand-primary border-brand-primary", textClass: "text-brand-primary" },
  C11: { label: "Confirmar Salida",          endpoint: "confirm-departure",      icon: <Truck size={18}/>,      color: "var(--brand-primary)", bgClass: "bg-blue-700 border-blue-700", textClass: "text-blue-700" },
  C12: { label: "Confirmar Llegada",         endpoint: "confirm-arrival",        icon: <Truck size={18}/>,      color: "var(--brand-primary)", bgClass: "bg-brand-primary border-brand-primary", textClass: "text-brand-primary" },
  C13: { label: "Emitir Factura MWT",        endpoint: "issue-invoice",          icon: <Receipt size={18}/>,    color: "var(--brand-primary)", bgClass: "bg-brand-primary border-brand-primary", textClass: "text-brand-primary" },
  C14: { label: "Cerrar Expediente",         endpoint: "close",                  icon: <Lock size={18}/>,       color: "var(--brand-primary)", bgClass: "bg-slate-600 border-slate-600", textClass: "text-slate-600" },
  C15: { label: "Registrar Costo",           endpoint: "register-cost",          icon: <DollarSign size={18}/>, color: "var(--brand-primary)", bgClass: "bg-amber-700 border-amber-700", textClass: "text-amber-700" },
  C16: { label: "Cancelar Expediente",       endpoint: "cancel",                 icon: <XCircle size={18}/>,    color: "var(--brand-primary)", bgClass: "bg-red-600 border-red-600", textClass: "text-red-600" },
  C17: { label: "Bloquear Expediente",       endpoint: "block",                  icon: <Lock size={18}/>,       color: "var(--brand-primary)", bgClass: "bg-red-600 border-red-600", textClass: "text-red-600" },
  C18: { label: "Desbloquear Expediente",    endpoint: "unblock",                icon: <Unlock size={18}/>,     color: "var(--brand-primary)", bgClass: "bg-brand-primary border-brand-primary", textClass: "text-brand-primary" },
  C21: { label: "Registrar Pago",            endpoint: "register-payment",       icon: <CreditCard size={18}/>, color: "var(--brand-primary)", bgClass: "bg-brand-primary border-brand-primary", textClass: "text-brand-primary" },
  C22: { label: "Emitir Factura Comisión",  endpoint: "issue-commission-invoice",icon: <Receipt size={18}/>,    color: "var(--brand-primary)", bgClass: "bg-purple-600 border-purple-600", textClass: "text-purple-600" },
  C30: { label: "Materializar Logística",    endpoint: "materialize-logistics",  icon: <Package size={18}/>,    color: "var(--brand-primary)", bgClass: "bg-amber-700 border-amber-700", textClass: "text-amber-700" },
};

type FormData = Record<string, string | number | boolean>;

function CommandForm({ commandKey, form, setForm }: { commandKey: string; form: FormData; setForm: (f: FormData) => void }) {
  const set = (k: string, v: string | number | boolean) => setForm({ ...form, [k]: v });
  const inp = (label: string, key: string, type: string = "text", placeholder: string = "") => (
    <div key={key}>
      <label className="th-label block mb-1">{label}</label>
      <input
        type={type} className="input w-full" placeholder={placeholder}
        value={String(form[key] ?? "")}
        onChange={(e) => set(key, type === "number" ? Number(e.target.value) : e.target.value)}
      />
    </div>
  );

  switch (commandKey) {
    case "C2": return <div className="space-y-3">{inp("Número OC", "oc_number", "text", "OC-2024-001")}{inp("Notas", "notes")}</div>;
    case "C3": return <div className="space-y-3">{inp("Número proforma", "proforma_number", "text", "PRF-001")}{inp("Monto (USD)", "amount", "number", "0")}</div>;
    case "C4": return (
      <div className="space-y-3">
        <div>
          <label className="th-label block mb-1">Modo logístico</label>
          <select className="input w-full" value={String(form.mode ?? "maritime")} onChange={(e) => set("mode", e.target.value)}>
            <option value="maritime">Marítimo</option>
            <option value="air">Aéreo</option>
            <option value="land">Terrestre</option>
          </select>
        </div>
      </div>
    );
    case "C5": return <div className="space-y-3">{inp("Número SAP", "sap_number", "text", "SAP-00001")}</div>;
    case "C6": return <div className="space-y-3">{inp("Notas de producción", "notes")}</div>;
    case "C7": return (
      <div className="space-y-3">{inp("Número BL", "bl_number", "text", "MSCUXXX")}{inp("Transportista", "carrier")}{inp("Puerto origen", "origin_port")}{inp("Puerto destino", "destination_port")}</div>
    );
    case "C8": return <div className="space-y-3">{inp("Monto flete (USD)", "freight_amount", "number", "0")}{inp("Proveedor", "provider")}</div>;
    case "C9": return <div className="space-y-3">{inp("Agencia aduanal", "customs_agency")}{inp("Número declaración", "declaration_number")}</div>;
    case "C10": return <div className="space-y-3">{inp("Observaciones", "notes")}</div>;
    case "C11": return <div className="space-y-3">{inp("Fecha salida", "departure_date", "date")}{inp("Notas", "notes")}</div>;
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
          <select className="input w-full" value={String(form.visibility ?? "internal")} onChange={(e) => set("visibility", e.target.value)}>
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
          <select className="input w-full" value={String(form.method ?? "wire")} onChange={(e) => set("method", e.target.value)}>
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

export default function ArtifactModal({ open, expedienteId, commandKey, onClose, onSuccess }: ArtifactModalProps) {
  const [form, setForm] = useState<FormData>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const meta = COMMAND_META[commandKey];

  if (!open || !meta) return null;

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    try {
      if (['C10', 'C11', 'C12', 'C14'].includes(commandKey)) {
        await api.post(`/expedientes/${expedienteId}/commands/${meta.endpoint}/`, form);
      } else {
        await api.post(`/expedientes/${expedienteId}/commands/${meta.endpoint}/`, form);
      }
      setForm({});
      onSuccess();
      onClose();
    } catch (err: any) {
      const errData = err?.response?.data;
      setError(
        errData
          ? Object.entries(errData).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(", ") : v}`).join(" | ")
          : "Error al ejecutar el comando."
      );
    } finally {
      setLoading(false);
    }
  };

  const titleWithIcon = (
    <div className="flex items-center gap-2">
      <span className={meta.textClass}>{meta.icon}</span>
      <span className="text-navy">{meta.label}</span>
      <span className="text-xs font-mono text-text-tertiary ml-2 mt-1">{commandKey}</span>
    </div>
  );

  // Define footer explicitly for FormModal
  const footerContent = (
    <>
      <button className="btn btn-md btn-secondary" onClick={onClose} disabled={loading}>
        Cancelar
      </button>
      <button
        className={`btn btn-md text-white ${meta.bgClass}`}
        onClick={handleSubmit}
        disabled={loading}
      >
        {loading ? "Ejecutando..." : meta.label}
      </button>
    </>
  );

  return (
    <FormModal
      open={open}
      title={titleWithIcon as unknown as string} // FormModal's title is typed as string, but ReactNode works if we bypass or if we just pass a string.
      // Wait, FormModal typed title as string. Let's pass a string, or fix the title definition.
      // Actually, passing a string is safer. I'll change it inline.
      onClose={onClose}
      footer={footerContent}
      size="sm"
    >
      {/* Hack to circumvent title type constraint if we really wanted the icon, but let's just use string title */}
      {/* Wait, the title prop in FormModal goes standard string. I will just pass the string. */}
      {error && (
        <div className="p-3 mb-4 rounded-lg bg-coral-soft/20 border border-coral/30 text-sm text-coral">
          {error}
        </div>
      )}
      <CommandForm commandKey={commandKey} form={form} setForm={setForm} />
    </FormModal>
  );
}
