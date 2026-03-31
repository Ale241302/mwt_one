/**
 * S20B-09: Modos permitidos por marca para la creación de proformas
 */
export const BRAND_ALLOWED_MODES: Record<string, string[]> = {
  'marluvas': ['MARITIMO', 'AEREO'],
  'rana_walk': ['COURIER'],
  'tecmater': ['TERRESTRE', 'MARITIMO'],
};

export const DEFAULT_ALLOWED_MODES = ['MARITIMO', 'AEREO', 'TERRESTRE', 'COURIER'];
