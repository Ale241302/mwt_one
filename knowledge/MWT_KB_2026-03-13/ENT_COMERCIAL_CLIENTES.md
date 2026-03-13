# ENT_COMERCIAL_CLIENTES — Registro de Clientes
status: DRAFT
visibility: [CEO-ONLY]
domain: Comercial (IDX_COMERCIAL)
version: 1.0
classification: ENTITY — Data pura inyectable.
refs: ENT_PLAT_LEGAL_ENTITY, ENT_MERCADO_{X}, COM-01 (ENT_GOB_PENDIENTES)

---

## A. Propósito

Registro canónico de clientes B2B. Actualmente solo canal Marluvas. Se expande con Rana Walk y Tecmater cuando aplique.

El campo `codigo_marluvas` es un identificador interno del sistema SAP de Marluvas. No es un código MWT. Clientes de otros canales tendrán sus propios identificadores externos.

---

## B. Registro — Canal Marluvas

| codigo_marluvas | cliente | pais |
|-----------------|---------|------|
| 4000000100 | SONDEL S.A. | Costa Rica |
| 4000000145 | MUITO WORK LIMITADA | Costa Rica |
| 4000000102 | DISTRIBUIDORA COMTEK S.A.S. | Colombia |
| 4000000116 | MELEXA S.A.S. | Colombia |
| 4000000402 | SONEPAR COLOMBIA S.A.S. | Colombia |
| 4000000115 | IMPORCOMP S.A. | Guatemala |
| 4000000400 | COMERCIALIZADORA UMMIE, S.A. | Guatemala |
| 4000000484 | GRUPO SOLUCIONES DE INGENIERIA Y AUTOMATIZACION S.A. | Guatemala |
| 4000000501 | EQUIPOS Y GUANTES INDUSTRIALES S.A. | Guatemala |
| 4000000126 | PRO CUSTOMER CORP. | Panama |
| 4000000128 | IMPORTACIONES Y COMPRAS S. DE R.L. | Honduras |

---

## C. Reglas

1. El nombre del cliente en proformas DEBE ser exactamente como aparece en §B. No abreviar, no reformatear.
2. El código Marluvas DEBE aparecer visible junto al nombre en toda proforma (ref SCH_PROFORMA_MWT §D2).
3. Nuevos clientes se agregan solo cuando Marluvas confirma el código SAP asignado.
4. Campo `pais` determina qué ENT_MERCADO_{X} aplica.
5. MUITO WORK LIMITADA (4000000145) es autoconsumo — proformas para stock propio o Rana Walk.

---

## D. Campos pendientes (ref COM-01)

Cuando se materialice COM-01 completo, cada cliente necesitará:
- cedula_juridica: string
- contacto: { nombre, telefono, email }
- condiciones_default: { credito_dias, medio_pago, incoterm }
- direccion_entrega: string
- canal: enum [directo, distribuidor]
- estado: enum [activo, inactivo]

Estos campos son [PENDIENTE — NO INVENTAR] hasta que se recopilen.

---

Stamp: DRAFT — Pendiente aprobación CEO
