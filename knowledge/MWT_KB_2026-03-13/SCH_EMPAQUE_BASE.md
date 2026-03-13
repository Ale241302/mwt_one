# SCH_EMPAQUE_BASE — v1.0 ACTIVO

## Elementos comunes a todo empaque
- slot: [Logo]
- slot: [Nombre → entity.A2]
- slot: [Sticker tallas+barcode → entity.E13-E16]
- slot: [Footer legal → ensamblado desde ENT_MARCA_IP + entity trademarks + ENT_COMP_ROGERS(condicional)]
- slot: [Línea origen → ENT_MERCADO_{M} según destino]

## Policies
POL_ROGERS, POL_STAMP, POL_ANTI_CONFUSION, POL_ORIGEN_LOCAL
