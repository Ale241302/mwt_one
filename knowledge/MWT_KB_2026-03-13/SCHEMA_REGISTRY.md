# SCHEMA_REGISTRY — Catálogo de Schemas Disponibles

Principio: schema existe = yo puedo ensamblarlo. Schema no existe = primero se crea.

## FÍSICOS

| Schema | Archivo | Hereda de | Status |
|--------|---------|-----------|--------|
| SCH_EMPAQUE_BASE | SCH_EMPAQUE_BASE.md | — | ACTIVO |
| SCH_EMPAQUE_CAJA_4 | SCH_EMPAQUE_CAJA_4.md | SCH_EMPAQUE_BASE | ACTIVO |
| SCH_EMPAQUE_BOLSA_2 | SCH_EMPAQUE_BOLSA_2.md | SCH_EMPAQUE_BASE | ACTIVO |
| SCH_STICKER_BASE | SCH_STICKER_BASE.md | — | ACTIVO |
| SCH_STICKER_CAJA | SCH_STICKER_CAJA.md | SCH_STICKER_BASE | ACTIVO |
| SCH_STICKER_BOLSA | SCH_STICKER_BOLSA.md | SCH_STICKER_BASE | ACTIVO |

## MARKETPLACE

| Schema | Archivo | Hereda de | Status |
|--------|---------|-----------|--------|
| SCH_LISTING_AMAZON | SCH_LISTING_AMAZON.md | — | ACTIVO |
| SCH_APLUS_CONTENT | SCH_APLUS_CONTENT.md | — | ACTIVO |
| SCH_LLMS_TXT | SCH_LLMS_TXT.md | — | ACTIVO |

## WEB/DIGITAL

| Schema | Archivo | Hereda de | Status |
|--------|---------|-----------|--------|
| SCH_PAGINA_PRODUCTO | SCH_PAGINA_PRODUCTO.md | — | ACTIVO |
| SCH_FICHA_TECNICA | SCH_FICHA_TECNICA.md | — | ACTIVO |

## OPERATIVOS

| Schema | Archivo | Hereda de | Status |
|--------|---------|-----------|--------|
| SCH_BRIEF_PROVEEDOR | SCH_BRIEF_PROVEEDOR.md | — | ACTIVO |
| SCH_PROFORMA_MWT | SCH_PROFORMA_MWT.md | — | DRAFT |

## PLATAFORMA

| Schema | Archivo | Hereda de | Status |
|--------|---------|-----------|--------|
| SCH_CONTRATO_NODO | SCH_CONTRATO_NODO.md | — | DRAFT |
| SCH_ISO_AUDIT_PACK | SCH_ISO_AUDIT_PACK.md | — | DRAFT |

Total: 15 schemas (12 ACTIVO + 3 DRAFT)
