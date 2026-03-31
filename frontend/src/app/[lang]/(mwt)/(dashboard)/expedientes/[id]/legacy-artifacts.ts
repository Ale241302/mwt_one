export const LEGACY_STATE_ARTIFACTS: Record<string, string[]> = {
  "REGISTRO": ["ART-01", "ART-02"],
  "PREPARACION": ["ART-03", "ART-07", "ART-08"],
  "PRODUCCION": ["ART-04", "ART-19"],
  "DESPACHO": ["ART-05", "ART-06"],
  "TRANSITO": ["ART-10"],
  "EN_DESTINO": ["ART-09"],
  "CERRADO": []
};

export const LEGACY_ARTIFACT_COMMAND_MAP: Record<string, string> = {
  "ART-01": "C2", "ART-02": "C3", "ART-03": "C4",
  "ART-04": "C5", "ART-05": "C6", "ART-06": "C7",
  "ART-07": "C8", "ART-08": "C9", "ART-09": "C13",
  "ART-10": "C22", "ART-19": "C30",
};

export const LEGACY_ARTIFACT_LABELS: Record<string, string> = {
  "ART-01": "Orden de Compra", "ART-02": "Proforma", "ART-03": "Decisión Modal",
  "ART-04": "SAP Confirmado",  "ART-05": "Confirmación Producción", "ART-06": "Embarque",
  "ART-07": "Cotización Flete","ART-08": "Aduana", "ART-09": "Factura MWT",
  "ART-10": "Factura Comisión", "ART-19": "Materialización Logística",
};
