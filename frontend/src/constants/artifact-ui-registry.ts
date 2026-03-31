/**
 * S20B-02: Registro único de UI y comandos para cada artefacto (reemplaza ARTIFACT_LABELS / MAP)
 */
export const ARTIFACT_UI_REGISTRY: Record<string, { label: string; command: string }> = {
  "ART-01": { label: "Orden de Compra", command: "C2" },
  "ART-02": { label: "Proforma", command: "C3" },
  "ART-03": { label: "Booking / Reserva", command: "C4" },
  "ART-04": { label: "SAP Confirmado", command: "C5" },
  "ART-05": { label: "Confirmación Producción", command: "C6" },
  "ART-06": { label: "Embarque (BL/AWB)", command: "C7" },
  "ART-07": { label: "Lista de Empaque", command: "C7B" },
  "ART-08": { label: "Certificado de Origen", command: "C9" },
  "ART-09": { label: "Factura MWT", command: "C13" },
  "ART-10": { label: "Factura Comisión", command: "C22" },
  "ART-11": { label: "Inspección de Calidad", command: "C11B" },
  "ART-19": { label: "Materialización Logística", command: "C30" },
};
