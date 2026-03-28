import { useMemo } from "react";

export type OperadoPor = "CLIENTE" | "MWT" | null;

export interface OperadoPorFields {
  showClientFields: boolean;
  showMwtFields: boolean;
  showBanner: boolean;
}

/**
 * Hook centralizado para lógica de operado_por.
 * NUNCA muestra ambos conjuntos simultáneamente.
 * REGLA: CLIENTE -> *_client | MWT -> *_mwt | null -> banner
 */
export function useOperadoPor(operadoPor: OperadoPor): OperadoPorFields {
  return useMemo(() => {
    return {
      showClientFields: operadoPor === "CLIENTE",
      showMwtFields: operadoPor === "MWT",
      showBanner: operadoPor === null,
    };
  }, [operadoPor]);
}

/**
 * Helper funcional (sin hook) para uso en server components o fuera de React.
 */
export function resolveOperadoPorFields(operadoPor: OperadoPor): OperadoPorFields {
  return {
    showClientFields: operadoPor === "CLIENTE",
    showMwtFields: operadoPor === "MWT",
    showBanner: operadoPor === null,
  };
}
