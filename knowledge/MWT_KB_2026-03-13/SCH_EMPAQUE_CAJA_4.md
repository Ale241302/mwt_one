# SCH_EMPAQUE_CAJA_4 — v1.0 ACTIVO (inherits: SCH_EMPAQUE_BASE)

## Caras: Frontal, Lateral izq, Lateral der, Posterior

| Cara | Slots |
|------|-------|
| Frontal | [BASE.Logo] + [entity.A2] + [loc.B1 claim] + [loc.B2 subhead] + [entity.B4 sello si != N/A] + [BASE.Sticker] |
| Lateral izq | [loc.C3 specs] + [entity.C2 íconos] + [BASE.Logo] |
| Lateral der | [pendiente definir por producto] |
| Posterior | [loc.B3 tagline] + [BASE.Footer] + [BASE.Línea origen] |

## Colores
entity.E1-E5 por cara + entity.E6-E7 slogan cromático

## Sticker
Continuo frente-lateral-back (ref → SCH_STICKER_CAJA)

## Requires
ENT_PROD_{X}, LOC_{X}_{LANG}, ENT_MERCADO_{M}, ENT_MARCA_IP, ENT_MARCA_ORIGEN, ENT_COMP_ROGERS(si PORON)
