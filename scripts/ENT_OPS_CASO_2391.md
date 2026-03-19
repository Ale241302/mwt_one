# ENT_OPS_CASO_2391 — Aprendizajes del Primer Expediente Real
id: ENT_OPS_CASO_2391
version: 1.0
status: VIGENTE
stamp: VIGENTE — 2026-03-19
visibility: [CEO-ONLY]
domain: Operaciones (IDX_OPS)

---

## A. Propósito

Este documento registra los hallazgos del primer expediente real procesado de punta a punta: PF 2391-2025 (Marluvas → MWT → Sondel, Modelo C FULL, 80 pares 75BPR29-CLI-MM-CPAP-EXP). Cada hallazgo incluye: qué dice la KB hoy, qué reveló la realidad, y qué debe cambiar.

Fuentes documentales: PO 504649, PF 2391-2025, SAP Doc. 256056, INV 2391-2025, DANFE 269037, DU-E 26BR000357079-5, AWB 729-91524801, DUA 005-2026-179055, Liquidación DUA, TSM 1105295, GJ Cargo Invoice 003533.

---

## B. Hallazgos — 9 mejoras concretas

### H1. ENT_COMERCIAL_COSTOS — arancel incorrecto y estructura inadecuada

**KB dice:** "Arancel CR 0%"
**Realidad:** DAI 14% para partida 6403.99.90 (calzado suela plástico, parte superior cuero/microfibra). DUA 005-2026-179055 confirma $465.81 de DAI sobre CIF $3,327.20.

**Problema de fondo:** ENT_COMERCIAL_COSTOS mezcla datos Rana Walk (plantillas, Amazon FBA) con datos Marluvas (calzado) en 15 líneas sin estructura. El arancel depende de la partida arancelaria, no de la marca.

**Acción:** Reestructurar ENT_COMERCIAL_COSTOS por partida arancelaria (6403.99.90 calzado, 6406.90.90 plantillas, etc.). Cada partida con su DAI, IVA, y fuente documental.

**Impacto:** Sin esta corrección, toda simulación de Modelo C produce márgenes falsos. Afecta ENT_COMERCIAL_CANAL, ART-03 (Decisión B/C), y simulaciones de contribución por canal.

**Prioridad:** ALTA — dato incorrecto en producción.
**Archivo afectado:** ENT_COMERCIAL_COSTOS

---

### H2. CostLine necesita separar costo real de crédito fiscal (IVA)

**KB dice:** ART-11 / C15 (RegisterCostLine) tiene `cost_type, amount, currency, phase, description`. No distingue costo de crédito fiscal.

**Realidad:** En PF 2391-2025, el IVA total es $678.66 (aduana $616.39 + TSM $9.55 + GJ Cargo $46.60 + transporte $6.12). Este IVA es crédito fiscal recuperable — no es costo del producto. Si se registra como costo, el margen calculado está distorsionado en $678.66 (8.48/par).

**Acción:** Agregar campo a CostLine:
```
cost_category: enum [landed_cost | tax_credit | recoverable | non_deductible]
```
Regla: landed_cost suma al costo del producto. tax_credit se registra para contabilidad pero no suma al costo. El sistema calcula margen solo sobre landed_cost.

**Impacto:** Sin esto, el dashboard de contribución por canal (AUT-041) y el P&L por expediente reportan márgenes incorrectos.

**Prioridad:** ALTA — afecta cálculos financieros.
**Archivo afectado:** ENT_OPS_STATE_MACHINE (sección F2, C15), ENT_PLAT_ARTEFACTOS (ART-11)

---

### H3. CostLine necesita clasificar fijo vs variable

**KB dice:** CostLine es append-only con `cost_type` genérico. No clasifica comportamiento del costo.

**Realidad:** Los $479 de servicios de internación (almacén TSM $73.44, agencia GJ Cargo $358.48, transporte $47.08 — todos sin IVA) son fijos por operación. A 80 pares cuestan $5.99/par. A 500 pares cuestan $0.96/par. Sin esta clasificación, las simulaciones de escala y el análisis de punto de retorno por canal (ENT_COMERCIAL_CANAL.D2) no pueden funcionar.

**Acción:** Agregar campo:
```
cost_behavior: enum [fixed_per_operation | variable_per_unit | variable_per_weight | semi_variable]
```

**Impacto:** Habilita simulaciones de escala, punto de retorno, y optimización de volumen por canal.

**Prioridad:** MEDIA — diseño para Sprint 11+.
**Archivo afectado:** ENT_OPS_STATE_MACHINE (F2), ENT_COMERCIAL_CANAL (D1, D2)

---

### H4. SONDEL-CR completado con datos reales

**KB decía:** SONDEL-CR con todo `[PENDIENTE — NO INVENTAR]`.

**Realidad (PO 504649):** SonDel S.A., cédula 3-101-095926-01, Alajuela CR, código Marluvas SI0063, CXC 90 días, SAP Business One, contactos Javier Bonilla (compras) y Stephanie Guerrero (abastecimiento).

**Hallazgo adicional:** Sondel compra directo a Marluvas con su propio código de proveedor. No necesita a MWT. La relación MWT-Sondel se basa en arbitraje de precio (MWT compra más barato), no en dependencia logística.

**Acción:** ✅ APLICADO en ENT_PLAT_LEGAL_ENTITY v1.1 (esta sesión). Z1 resuelto.

**Prioridad:** ✅ HECHO.
**Archivo afectado:** ENT_PLAT_LEGAL_ENTITY

---

### H5. Faltan artefactos en ARTIFACT_REGISTRY

**KB dice:** ART-01 a ART-12 cubren el flujo del expediente.

**Realidad:** PF 2391-2025 generó 14 documentos. Dos no están en el registry:

1. **Certificado de Origen (CO):** Emitido por FIEMG/ICC Brasil. Obligatorio para aduana CR. Puede afectar DAI por acuerdos comerciales. En este caso: CO 2391-2025, firmado 10-feb-2026, acredita origen brasileño.

2. **DU-E (Declaración Única de Exportación Brasil):** Documento fiscal RFB obligatorio para salida de mercancía de Brasil. En este caso: 26BR000357079-5, registrada 02-mar-2026.

Adicionalmente, DANFE (NF-e) y Carta de Corrección son documentos fiscales brasileños que el expediente debe referenciar aunque no sean artefactos MWT.

**Acción:** Agregar al ARTIFACT_REGISTRY:
- ART-19: Certificado de Origen (document, DRAFT)
- ART-20: DU-E Exportación Brasil (document, DRAFT)
Agregar campo `external_fiscal_refs[]` al expediente para DANFE, CC, DU-E.

**Prioridad:** MEDIA — no bloquea MVP pero mejora trazabilidad.
**Archivo afectado:** ARTIFACT_REGISTRY, ENT_OPS_EXPEDIENTE

---

### H6. Tiempos reales — primer baseline para forecast (F4)

**KB dice:** ENT_OPS_EXPEDIENTE.F4 menciona "base histórica para forecast" pero no tiene datos reales.

**Realidad — PF 2391-2025 (primer registro):**

| Fase | Días | Acumulado | Evento inicio | Evento fin |
|------|------|-----------|---------------|------------|
| Registro (PO→SAP) | 3 | 3 | PO 504649 (09-dic) | SAP 256056 (12-dic) |
| Producción (MTO) | 60 | 63 | SAP confirmado | Factura comercial (10-feb) |
| Preparación/Despacho BR | 27 | 90 | Factura → DANFE → DU-E → Embarque | Vuelo VCP (09-mar) |
| Tránsito (VCP→SJO) | 2 | 92 | QT4052 (09-mar) | AV0692 llegada (10-mar) |
| Aduana CR (ingreso→levante) | 8 | 100 | DUA ingreso (13-mar) | Levante (18-mar) |
| Total PO→Retiro | **100 días** | | | |

**Insight:** El cuello de botella es producción MTO (60 días = 60% del tiempo total). La alerta credit_clock en día 60 marca apenas el fin de producción — no es anomalía sino baseline normal para pedidos MTO Marluvas.

**Acción:** Registrar como primer datapoint de F4. Estos tiempos aplican para: marca Marluvas, producto 75BPR29 (calzado seguridad), transporte aéreo, ruta VCP-BOG-SJO, aduana Santamaría.

**Prioridad:** BAJA — informativo pero valioso para calibrar alertas.
**Archivo afectado:** ENT_OPS_EXPEDIENTE (F4)

---

### H7. Decisión B/C necesita validación de viabilidad automática

**KB dice:** ART-03 (Decisión B/C) es un documento que registra la decisión del CEO. C4 (DecideModeBC) solo requiere que ART-02 exista.

**Realidad:** En este caso, el Modelo C genera pérdida si se vende a $47.74/par (el precio FOB de Sondel). El costo landed MWT es $60.29/par. El DAI 14% + IVA cascada eliminan el delta aparente de $10.40 y lo convierten en -$5.78/par de pérdida. El CEO lo sabe intuitivamente, pero el sistema no lo valida.

**Acción:** Agregar validación en C4 (DecideModeBC) o como pre-check de ART-03:
```
Si mode=FULL:
  fob_mwt = precio_proforma
  fob_cliente = precio_po_cliente
  dai_pct = lookup(partida_arancelaria, pais_destino)
  iva_pct = lookup(pais_destino)
  costos_fijos_estimados = promedio(ultimas_5_operaciones) o default
  
  costo_landed_estimado = fob_mwt × (1 + flete_pct) × (1 + dai_pct) × (1 + iva_pct) + costos_fijos / qty
  
  Si costo_landed_estimado > fob_cliente:
    WARNING: "Modelo C genera pérdida estimada de ${delta}/par. ¿Confirmar?"
```

**Prioridad:** ALTA — previene pérdidas operativas.
**Archivo afectado:** ENT_OPS_STATE_MACHINE (C4), ENT_PLAT_ARTEFACTOS (ART-03)

---

### H8. CostLine necesita tipo de cambio y equivalente en moneda base

**KB dice:** CostLine tiene `amount, currency`. No tiene tipo de cambio.

**Realidad:** PF 2391-2025 maneja 3 monedas: USD (principal), BRL (DANFE R$15,347.04 a R$191.84/par), CRC (TSM ₡39,000.58, transporte ₡25,000, impuestos ₡473,303.55). Con 2 tipos de cambio diferentes: DUA ₡473.47 y TSM ₡469.94. Sin registrar el TC al momento de cada costo, los totales no se pueden recalcular ni auditar.

**Acción:** Agregar campos a CostLine:
```
exchange_rate: decimal | null       # TC usado en conversión
amount_base_currency: decimal       # Monto equivalente en USD
base_currency: string               # "USD" (configuración del expediente)
```

**Prioridad:** ALTA — sin esto, los reportes multi-moneda son inconsistentes.
**Archivo afectado:** ENT_OPS_STATE_MACHINE (F2, CostLine)

---

### H9. Aforo aduanero impacta costos y tiempos

**KB dice:** No modela el tipo de aforo.

**Realidad:** DUA 179055 fue aforo ROJO (revisión física). Impacto: GJ Cargo cobró $50 extra por "Revisión DUA rojo". TSM cobró 8 días de estadía (vs ~3 días estimados en aforo verde). Total impacto estimado: ~$50 (servicio extra) + ~$40 (5 días adicionales almacén) = ~$90 por operación.

**Acción:** Agregar al expediente:
```
aforo_type: enum [verde | amarillo | rojo] | null
aforo_date: date | null
```
Y alimentar el forecast (F4) con estadísticas de aforo por aduana para estimar tiempos y costos más precisos.

**Prioridad:** BAJA — mejora estimaciones pero no bloquea operación.
**Archivo afectado:** ENT_OPS_EXPEDIENTE (campos base), ENT_OPS_STATE_MACHINE (EN_DESTINO)

---

## C. Matriz de prioridad

| ID | Hallazgo | Prioridad | Archivo principal | Sprint sugerido |
|----|----------|-----------|-------------------|-----------------|
| H1 | Arancel incorrecto + estructura | ALTA | ENT_COMERCIAL_COSTOS | Inmediato (corrección dato) |
| H2 | IVA no es costo (cost_category) | ALTA | ENT_OPS_STATE_MACHINE | Sprint 11 (modelo datos) |
| H3 | Fijo vs variable (cost_behavior) | MEDIA | ENT_OPS_STATE_MACHINE | Sprint 11 |
| H4 | Sondel completado | ✅ HECHO | ENT_PLAT_LEGAL_ENTITY | — |
| H5 | Artefactos faltantes (CO, DU-E) | MEDIA | ARTIFACT_REGISTRY | Sprint 11 |
| H6 | Baseline tiempos F4 | BAJA | ENT_OPS_EXPEDIENTE | Post-Sprint 11 |
| H7 | Validación viabilidad Modelo C | ALTA | ENT_OPS_STATE_MACHINE | Sprint 11 |
| H8 | Tipo de cambio en CostLine | ALTA | ENT_OPS_STATE_MACHINE | Sprint 11 |
| H9 | Aforo aduanero | BAJA | ENT_OPS_EXPEDIENTE | Post-Sprint 11 |

---

## D. Datos financieros del caso (referencia CEO-ONLY)

| Métrica | MWT (FOB $37.34) | Sondel hip. (FOB $47.74) |
|---------|-----------------|------------------------|
| FOB total | $2,987.20 | $3,819.20 |
| CIP | $3,282.20 | $4,114.20 |
| DAI 14% | $465.81 | $582.29 |
| IVA 13% (crédito fiscal) | $497.42 | $616.39 |
| Landed sin IVA | $4,326.49 | $5,211.91 |
| Landed + servicios sin IVA | $4,805.49 | $5,211.91 + $479.00 = $5,690.91 |
| $/par landed (sin IVA) | $60.07 | $71.14 |
| Delta landed | — | $11.07/par = $885.42 total |

Nota: servicios de internación ($479.00 sin IVA) son fijos — mismos para ambos escenarios.

---

## Z. Relación con otros documentos

| Documento | Impacto |
|-----------|---------|
| ENT_COMERCIAL_COSTOS | H1: corregir DAI 0% → 14% para partida 6403.99.90 |
| ENT_OPS_STATE_MACHINE | H2, H3, H7, H8: CostLine fields + validación C4 (FROZEN — cambios van a Sprint spec) |
| ARTIFACT_REGISTRY | H5: +ART-19, +ART-20 |
| ENT_OPS_EXPEDIENTE | H6, H9: F4 baseline + aforo_type |
| ENT_PLAT_LEGAL_ENTITY | H4: ✅ APLICADO v1.1 |
| ENT_COMERCIAL_CANAL | H3: depende de cost_behavior para simulaciones |
| ENT_COMERCIAL_MODELOS | H7: validación viabilidad Modelo C |

---

Stamp: VIGENTE — 2026-03-19
Origen: Sesión de análisis caso real PF 2391-2025 — primer expediente de punta a punta
