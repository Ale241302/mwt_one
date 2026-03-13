# ENT_PLAT_MARCAS — Configuración Multi-Marca en Plataforma
id: ENT_PLAT_MARCAS
version: 1.0
status: DRAFT
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
classification: ENTITY — Data pura inyectable
stamp: DRAFT — Pendiente aprobación CEO
creado: 2026-03-11 (resuelve ref rota en ENT_PLAT_MODULOS M6 + MANIFIESTO_CAMBIOS decisión CEO)

---

## A. PROPÓSITO

Esta entity contiene la configuración operativa de las marcas activas en la plataforma mwt.one.
No duplica identidad de marca — esa vive en ENT_MARCA_IDENTIDAD, ENT_MARCA_ORIGEN, ENT_MARCA_SELLO, ENT_MARCA_EEAT, ENT_MARCA_IP.

Este documento responde a: ¿cómo está configurada cada marca dentro del sistema? Flags, issuing entity, canales activos, features habilitadas por marca.

---

## B. MARCAS REGISTRADAS EN PLATAFORMA

### B1. Rana Walk

| Campo | Valor |
|-------|-------|
| brand_id | RW |
| nombre | Rana Walk |
| tipo | PROPIA |
| issuing_entity | Muito Work Limitada (MWT) |
| status | ACTIVO |
| mercados activos | USA (ACTIVO), CR (EN CONSTRUCCIÓN), BR (EN CONSTRUCCIÓN) |
| canales | Amazon FBA (USA), ranawalk.com, distribuidor |
| features habilitadas | catalog, pricing, inventory_rw, orders, scanner_integration |
| features deshabilitadas | checkout_cr, checkout_br |
| identity_ref | ENT_MARCA_IDENTIDAD |

### B2. Marluvas

| Campo | Valor |
|-------|-------|
| brand_id | MLV |
| nombre | Marluvas |
| tipo | DISTRIBUCIÓN |
| issuing_entity | Muito Work Limitada (MWT) — representante regional |
| status | ACTIVO |
| mercados activos | CR, CO, GT, PA, HN (operaciones B2B) |
| canales | B2B directo (portal.mwt.one), expediente operativo |
| features habilitadas | expediente, proforma, pricing_mlv, clients, orders |
| features deshabilitadas | storefront público, checkout consumidor |
| identity_ref | [PENDIENTE — escalar CEO: ¿crear ENT_MARCA_MARLUVAS o data en ENT_COMERCIAL_MODELOS es suficiente?] |

### B3. Tecmater

| Campo | Valor |
|-------|-------|
| brand_id | TCM |
| nombre | Tecmater |
| tipo | [PENDIENTE — NO INVENTAR] |
| issuing_entity | [PENDIENTE] |
| status | PENDIENTE |
| mercados activos | [PENDIENTE] |
| canales | [PENDIENTE] |
| features habilitadas | [PENDIENTE] |
| identity_ref | [PENDIENTE — por definir con CEO] |

---

## C. FEATURE FLAGS POR MARCA

Flags globales del sistema `brands/` — module M6 en ENT_PLAT_MODULOS.

| Flag | RW | MLV | TCM | Descripción |
|------|----|-----|-----|-------------|
| STOREFRONT_ENABLED | ✅ | ❌ | [P] | Tienda pública con checkout |
| B2B_PORTAL_ENABLED | ✅ | ✅ | [P] | Portal cliente portal.mwt.one |
| EXPEDITION_ENABLED | ❌ | ✅ | [P] | Módulo expedientes Marluvas |
| SCANNER_ENABLED | ✅ | ❌ | [P] | Integración pressure scanner |
| AMAZON_ENABLED | ✅ | ❌ | [P] | Canal Amazon SP-API |
| PROFORMA_ENABLED | ❌ | ✅ | [P] | Generación proformas MWT |
| COMMISSION_ENABLED | ❌ | ✅ | [P] | Cálculo comisiones Marluvas |

[P] = PENDIENTE — decisión CEO sobre Tecmater

> Flags reflejan estado ACTIVO hoy. Revisable por CEO cuando RW active canal B2B.

---

## D. REGLAS DE AISLAMIENTO

- Pricing de marca A nunca aparece en contexto de marca B
- Catálogo de marca A nunca mezcla SKUs con marca B
- Cada brand_id tiene su namespace en MinIO: `rw/`, `mlv/`, `tcm/`
- feature_flag False = módulo no instanciado para esa marca, no solo oculto
- issuing_entity determina qué entidad legal genera documentos (facturas, proformas)

---

## E. RELACIÓN CON OTROS DOCUMENTOS

| Lo que necesito saber | Ir a |
|----------------------|------|
| Identidad visual, colores, claims RW | ENT_MARCA_IDENTIDAD |
| Modelo de negocio por marca (B/C/FULL) | ENT_COMERCIAL_MODELOS |
| Pricing Marluvas | ENT_COMERCIAL_PRICING |
| Pricing Rana Walk | ENT_COMERCIAL_PRICING §A |
| Clientes activos por marca | ENT_COMERCIAL_CLIENTES |
| Módulos plataforma M6 | ENT_PLAT_MODULOS |
| Config por país | ENT_PLAT_PAISES |

---

Stamp: DRAFT — Pendiente aprobación CEO
Aprobador: CEO
Origen: Creado 2026-03-11 — resuelve ref rota ENT_PLAT_MODULOS M6 (MANIFIESTO_CAMBIOS, opción A: crear entity)
