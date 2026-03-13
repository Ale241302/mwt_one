# COM-07 / COM-08 — Nomenclatura Tokens Marluvas v1.0
status: VIGENTE
visibility: [INTERNAL]
domain: Comercial (IDX_COMERCIAL)
version: 1.1
last_updated: 2026-03-11
resuelve: COM-07 (motor JSON descripciones) + COM-08 (nomenclatura tokens)
fuente: Tabela COMEX v6 (514 SKUs) + marluvas.com.br + validación CEO

---

## Reglas Globales

| Regla | Descripción |
|-------|-------------|
| **Token A** | Puntera Acero SOLO como token independiente post-modelo. El `A` dentro del nombre `100AWORK` no es puntera. |
| **CPAP** | Puntera Composite + Antiperforante Textil simultáneamente. No separar. `CPAPPAD` (sin guion) = typo de `CPAP-PAD`. |
| **Prefijo CN-** | En familia 75 indica color Nubuck: `CNG`=Gris, `CNP`=Putty/Beige, `CNV`=Verde Musgo, `CNPT`=Putty+Textil. |
| **Forro PVC** | Se lee en el modelo base: `100AWORKF`=Con forro, `100AWORK`=Sin forro. No es token. |
| **IGNORAR** | `(CX)` `(SC)` `(PRETO)` `MARLUVAS` — ruido editorial. No usar como referencia técnica. |

---

## PUNTERA (Bico)

| Token | Español | Notas |
|-------|---------|-------|
| `A` | Puntera Acero | token independiente post-modelo |
| `CPAP` | Puntera Composite | incluye antiperforante textil |
| `BP` | Puntera Plástica | |
| *(sin token)* | Sin puntera | líneas 20S29, 100AWORK sin A, clean room |

## ANTIPERFORANTE (Palmilha)

| Token | Español | Notas |
|-------|---------|-------|
| `PA` | Antiperforante Acero | |
| `PAD` | Antiperforante Textil estándar | PAD = padrão (BR) |
| `PAZ` | Antiperforante Textil especial | |
| `CPAP` | Textil incluido en CPAP | no separar |
| *(sin token)* | Sin antiperforante | |

## COLOR — Línea PVC 100AWORK / 100AWORKF

| Token | Color | Notas |
|-------|-------|-------|
| `BR` | Blanco | |
| `PR` | Negro | |
| `PRA` | Negro suela amarilla | variante de PR |

## COLOR — Línea Clean Room (101/102/103FCLEAN)

| Token | Color |
|-------|-------|
| `AZ` | Azul |
| `VD` | Verde |
| `AM` | Amarillo |
| `BR` | Café/Castaño |
| `PR` | Negro |

## CAÑA — Línea PVC 100AWORK

| Token | Español |
|-------|---------|
| `CA` | Caña Alta |
| `CM` | Caña Media |

## MATERIAL ESPECIAL

| Token | Español | Notas |
|-------|---------|-------|
| `PET` | Bota tipo Petrolero — cuero Pólvora/Hidrofugado Parafinado | línea C32, uso petroquímico |
| `SELVA` | Bota militar — lona en laterales, uso selva/campo | línea C32 |
| `CRD` | Cuero especial contra llamas (flame-resistant) | línea B26V |
| `TXT` | Material textil exterior hidrofugado | |
| `MARRON` | Color Marrón (escrito completo) | solo 50C32-PET-A-MARRON |

## COLOR NUBUCK — Familia 75BPR / 75TPR

| Token | Español |
|-------|---------|
| `CNG` | Nubuck Gris |
| `CNP` | Nubuck Putty/Beige |
| `CNV` | Nubuck Verde Musgo |
| `CNPT` | Nubuck Putty + Textil |
| `CNTR` | Nubuck Narrow Toe |


## PROPIEDADES TÉCNICAS

| Token | Español |
|-------|---------|
| `HIDRO` | Resistente al agua (hidrorepelente) |
| `ANT` | Antiestático |
| `CFR` | Resistente al calor por contacto |
| `TNC` | Puntera no conductora |
| `TNC3` | Puntera no conductora clase 3 |
| `IPX` | Impermeable (rating IPX) |
| `WP` | Waterproof |
| `SRV` | Resistente a ácidos/químicos |
| `FRI` | Resistente al frío |
| `EXP` | Acabado exportación |
| `RDN` | Reflectante nocturno |
| `NT` | Non-Toxic |
| `CO` | Conductivo (ESD) |
| `DRB` | Drenaje / bota de agua |
| `AOM` | Accesorio/ortesis AOM |

## PROTECCIONES ADICIONALES

| Token | Español |
|-------|---------|
| `MEX` | Protector de metatarso externo |
| `M` | Protector de metatarso (guard independiente) |
| `CP` | Protección de caña |
| `PDG` | Protección adicional empeine |
| `ZP` | Protección contra aplastamiento |
| `GI` | Suela antiderrapante GI |
| `OSE` | Outsole especial |

## CONSTRUCCIÓN / CIERRE

| Token | Español |
|-------|---------|
| `E` | Elástico (cierre elástico lateral) |
| `C` | Cuero liso / costura lisa |
| `CB` | Caña Baja |
| `VEL` / `VELCRO` | Cierre velcro |
| `SC` | Sin caña (sapato/zapato bajo) |
| `CX` | Empaque especial |
| `ILHP` | Ojales plásticos |
| `ILH` | Ojales metálicos |
| `TPU` | Entresuela TPU |
| `PL` | Palmilla larga |

## FORRO

| Token | Español | Aplica |
|-------|---------|--------|
| `CLI` | Forro Climate liner | familia 75 |
| `BS` | Bota Social — forro Outlast Climatech (NASA) | 20S29-BS-T |

## LÍNEA 20S29 LONDON SAFE — Color + Cierre

| Token | Color | Cierre | CA |
|-------|-------|--------|----|
| `T` | Negro | Cordón | 33698 |
| `P` | Negro | Cordón | 41864 |
| `S` | Marrón | Elástico | 41864 |
| `BS` | Negro | Cordón + forro Outlast | — |

## VARIANTES FAMILIA 75

| Token | Español |
|-------|---------|
| `MSMC` | Midsole Molded Composite |
| `MM` | Midsole Montada |
| `MSC/MSNP/MSRO/MSP/MSPN` | Variantes de midsole (especificación técnica Marluvas) |
| `MP` | Mid Profile |
| `CLP` | Cierre lateral/plaqueta |
| `NPF/NPM/NPP/NPMF` | Variantes Non-Perforated |

## CLIENT_SPECIFIC — Pedidos a medida

> Estos tokens identifican productos fabricados específicamente para un cliente o proyecto. No describir técnicamente — indicar "Pedido especial [cliente]".

| Token | Cliente | SKU referencia |
|-------|---------|----------------|
| `ST` | **Sondel** | 75BPR29-MSMC-CPAP-ST |
| `FV` | N/I | 103FCLEAN-PR-FV |
| `ERAM` | ERAM | 50B22-M-A-ERAM / 50S29-M-A-ERAM |
| `NATCO` | NATCO | 20S29-T-NATCO |
| `LIBUS` | LIBUS | 95B22-LIBUS-A |
| `CNFL` | **CNFL — Compañía Nacional de Fuerza y Luz (Costa Rica)** | 60B22V-CPAP-PAD-CNFL — etiqueta cosida secuencial numérica por talla |
| `RENEE` | N/I | 70B22-C-PAD-RENEE |
| `SUZ` | N/I | 70C32-MAT-CPAP-SUZ |
| `LA` | N/I | 70B22-CPAP-PAD-LA |
| `LB` | N/I | 70B22-A-LB |
| `LR` | N/I | 72B29-TXT-E-BP-LR |

## ACCESORIOS (no calzado)

No aplican reglas de tokens. Descripción libre.

| SKU | Descripción |
|-----|-------------|
| 801048 | Palmilla Marluvas Softbed PU |
| 200190 | Palmilla Higiénica |
| Grupo CADARCO | Cordones (colores/materiales/longitudes varios) |

---

## Changelog
| Versión | Cambio |
|---------|--------|
| v1.0 | Creación — extracción exhaustiva 514 SKUs v6 + validación web Marluvas. Resuelve COM-07 y COM-08. |
| v1.1 | CNFL: movido de COLOR_NUBUCK a CLIENT_SPECIFIC. Modelo para CNFL Costa Rica, etiqueta cosida secuencial numérica por talla. 0 tokens sin resolver. |

Stamp: VIGENTE — Aprobado CEO 2026-03-11 | v1.1
