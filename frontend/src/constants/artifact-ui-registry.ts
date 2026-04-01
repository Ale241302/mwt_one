/**
 * S20B-02 / S21: Registro único de UI y comandos para cada artefacto.
 * Fuente de verdad para etiquetas y comandos en el frontend.
 * Sincronizado con ARTIFACT_LABELS en artifact_policy.py (backend).
 *
 * Convención de comandos:
 *   command = código del comando Django que CREA este artefacto
 */
export const ARTIFACT_UI_REGISTRY: Record<string, { label: string; command: string }> = {
  // REGISTRO
  "ART-01": { label: "Orden de Compra (OC)",        command: "C3"   }, // Updated to C3 (Sync S21)
  "ART-02": { label: "Proforma",                    command: "C2"   }, // Updated to C2 (Sync S21)

  // PRODUCCION / PREPARACION
  "ART-03": { label: "Decisión Modal",               command: "C4"   },
  "ART-04": { label: "SAP Confirmado",               command: "C5"   },
  "ART-05": { label: "Embarque",                    command: "C7"   }, // Updated to C7
  "ART-06": { label: "Confirmación Producción",      command: "C6"   }, // Updated to C6

  // DESPACHO
  "ART-07": { label: "Despacho Aprobado",            command: "C10"  },
  "ART-08": { label: "Cotización Flete",             command: "C8"   },
  "ART-09": { label: "Despacho Aduanal",             command: "C9"   },
  "ART-12": { label: "Nota de Compensación",         command: "C29"  },

  // TRANSITO
  "ART-10": { label: "BL Registrado",               command: "C11"  },
  "ART-36": { label: "Actualización Tracking",       command: "C36"  },

  // EN DESTINO
  "ART-11": { label: "Nota de Entrega",              command: "C12"  },
  "ART-13": { label: "Factura MWT",                 command: "C13"  },

  // OPS / ADMIN
  "ART-16": { label: "Motivo Cancelación",           command: "C16"  },
  "ART-19": { label: "Materialización Logística",    command: "C30"  },

  // LEGACY (para compatibilidad con expedientes pre-S20)
  "ART-22": { label: "Factura Comisión",             command: "C22"  },
};
