# SCH_STICKER_BASE — v1.0 ACTIVO

## Elementos comunes
- slot: [Header → entity.E15 + "ARCH PROFILE: " + entity.F4]
- slot: [TRIM column → entity.E13 + datos talla desde ENT_OPS_TALLAS]
- slot: [EXACT FIT column → entity.E14 + datos talla desde ENT_OPS_TALLAS]
- slot: [Barcode]
- slot: [Bloque regulatorio → ENT_MERCADO_{M} (origen, unidades, importador)]

## Labels
Desde LOC_TALLAS_{LANG} según mercado destino

## Policies
POL_NUNCA_TRADUCIR (labels talla), POL_ANTI_CONFUSION, POL_ORIGEN_LOCAL
