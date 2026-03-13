# PLB_INVESTIGACION — Protocolo de Investigación Hardware OEM
id: PLB_INVESTIGACION
version: 1.0
status: DRAFT
visibility: [INTERNAL]
domain: Producto (IDX_PRODUCTO)
classification: PLAYBOOK — Instrucciones operativas
stamp: DRAFT — Pendiente aprobación CEO
creado: 2026-03-11 — resuelve ref rota en ENT_PROD_SCANNER §G (MANIFIESTO_CAMBIOS decisión)

---

## A. PROPÓSITO

Este playbook define el protocolo para investigar, evaluar y seleccionar proveedores de hardware OEM para el pressure scanner Rana Walk.

Aplica principalmente a: Bangni PCSsole C1 (candidato principal), Maxrays ZRX-503B (secundario), y cualquier proveedor Shenzhen custom.

Ref producto: ENT_PROD_SCANNER
Ref glosario técnico: ENT_PROD_SCANNER_GLOSARIO
Ref modelo comercial distribuidor: PLB_SCANNER_DISTRIB
Ref evaluación proveedores (general): PLB_SUPPLIER_EVAL

---

## B. FASES DEL PROTOCOLO

### Fase 1 — DESKTOP RESEARCH

**Objetivo:** descartar proveedores con información pública insuficiente antes de contacto directo.

| Paso | Acción | Criterio de pase |
|------|--------|-----------------|
| 1.1 | Buscar en Alibaba, Made-in-China, web propia: modelo exacto, ficha técnica, grid de sensores | Ficha técnica pública disponible |
| 1.2 | Verificar certificaciones públicas: CE, RoHS, FCC (si BLE) | Al menos CE visible o declaración |
| 1.3 | Buscar videos o demos de software OEM — ¿parecen datos crudos o solo dashboard? | No descartatorio, solo indica riesgo OQ-01/02 |
| 1.4 | Buscar reviews de integradores en foros (Reddit, GitHub, Hackaday) | Indicador de apertura del protocolo |
| 1.5 | Registrar BOM estimado y precio público de referencia | Baseline para negociación |

> Datos de precio y BOM registrados en paso 1.5 son [CEO-ONLY] — no aparecen en outputs externos ni briefings de distribuidores.

---

### Fase 2 — CONTACTO INICIAL AL OEM

**Objetivo:** obtener respuestas a preguntas OQ-01 a OQ-10 antes de pedir muestras.

**Regla:** no pedir muestra hasta tener respuesta afirmativa a OQ-01 (datos crudos) y OQ-02 (protocolo transferible). Muestra sin protocolo = gasto sin retorno.

#### Preguntas obligatorias (OQ-01 a OQ-10)

| # | Pregunta | Idioma sugerido | Riesgo si negativo |
|---|---------|----------------|-------------------|
| OQ-01 | ¿El hardware puede enviar datos de presión crudos (raw pressure matrix) sin requerir el software OEM activo en el host? | EN / ZH | BLOQUEANTE — descartar si no |
| OQ-02 | ¿Pueden compartir el protocolo de comunicación (BLE o USB) con MWT bajo NDA? ¿Qué términos? | EN / ZH | BLOQUEANTE — sin protocolo no se integra |
| OQ-03 | ¿Cuál es el número exacto de sensores activos y la disposición del grid en el modelo actual? | EN | Importante para validar AC-03 |
| OQ-04 | ¿Cuál es la frecuencia máxima de muestreo configurable desde el host? | EN | Importante para AC-05 (≥50 Hz requerido) |
| OQ-05 | ¿Cuál es el consumo de corriente a 25 Hz y 50 Hz en modo USB y en modo batería? | EN | Importante para AC-10 (≥8 horas) |
| OQ-06 | ¿Pueden personalizar el color/branding de la unidad con el logo Rana Walk? ¿Cuál es el MOQ para personalización? | EN | Comercial — no bloqueante técnico |
| OQ-07 | ¿Tienen CE Declaration of Conformity disponible? ¿FCC ID si usa BLE? | EN | OBLIGATORIO para comercialización |
| OQ-08 | ¿Cuál es el precio para qty 1 / 5 / 10 / 50 incluyendo flete a Costa Rica (CRC)? [CEO-ONLY] | EN | Dato CEO-ONLY — para decisión compra |
| OQ-09 | ¿Cuál es el lead time para 1 muestra sin branding? ¿Y para qty 5 y 50? [CEO-ONLY] | EN | Dato CEO-ONLY — para planeación |
| OQ-10 | ¿El hardware ha sido validado para uso con calcetín? ¿Tienen datos de atenuación documentados? | EN | Importante para Capa 2 software (modo calcetín) |

**Nota OQ-08 y OQ-09:** Son datos [CEO-ONLY]. No aparecen en outputs externos ni briefings de distribuidores.

#### Cómo enviar la consulta

1. Usar formulario de contacto del proveedor o correo identificado en Alibaba/web
2. Presentarse como: "Rana Walk, brand de insoles biomecánicos, desarrollando herramienta de fitting para distribuidores"
3. NO mencionar precios de venta ni márgenes
4. Adjuntar especificación técnica mínima: frecuencia objetivo (50 Hz), grid mínimo (39×39 cm), uso biomecánico
5. Solicitar NDA si van a compartir protocolo

---

### Fase 3 — EVALUACIÓN DE MUESTRAS

**Prerrequisito:** OQ-01 y OQ-02 respondidas afirmativamente. Sin esto, no se ordena muestra.

**Protocolo de pruebas en lab (criterios de aceptación de ENT_PROD_SCANNER §F):**

| # | Test | Condición aprobación | Quién ejecuta |
|---|------|---------------------|---------------|
| AC-01 | SDK/protocolo disponible antes o junto con muestra | SDK entregado | CEO verifica recepción |
| **AC-02 ★ GATE** | Ingeniero MWT lee frames crudos Python en < 4 horas | Frames leídos exitosamente | Alejandro |
| AC-03 | ≥3 sensores en zona Z7/Z8 para EU 47 | Mapa coordenadas verificado | Alejandro |
| AC-04 | PP dentro de ±10% con carga 50 kg | Medición con pesa calibrada | Alejandro |
| AC-05 | Stream 50 Hz sin drops durante 1 minuto | Log sin gaps | Alejandro |
| AC-06 | CV < 15% en 10 repeticiones a 50 kg | Cálculo estadístico | Alejandro |
| AC-07 | TARE zerifica en ≤5 segundos | Medición cronómetro | Alejandro |
| AC-08 | Lectura estable con calcetín industrial | Comparación con/sin calcetín | Alejandro |
| AC-09 | Inspección física: ≥39×39 cm · antideslizante · cable ≥1.5 m · IP42 · <2.5 kg | Lista visual + cinta métrica | CEO |
| AC-10 | ≥8 horas continuas desde carga completa | Prueba de duración | Alejandro |

**Regla AC-02:** Si falla, se detienen todas las pruebas. No se continúa evaluación. No se compra ese hardware.

---

### Fase 4 — DECISIÓN Y REGISTRO

| Escenario | Acción |
|-----------|--------|
| AC-01 a AC-10 TODOS pasan | Registrar como APROBADO en ENT_GOB_PROVEEDORES · Definir MOQ inicial y condiciones |
| AC-02 falla | Descartar proveedor · Registrar en ENT_GOB_PROVEEDORES como DESCARTADO con razón |
| AC-02 pasa pero otros fallan | Evaluar severidad · Escalar CEO · Decidir si negociar spec con OEM o buscar alternativa |
| OQ-01/02 negativas | Descartar sin muestra · Registrar decisión |

**Registro en ENT_GOB_PROVEEDORES (clase CRÍTICO):**
- Fecha contacto, respuestas OQ, fecha muestra, resultados AC, decisión final, condiciones negociadas [CEO-ONLY]

---

## C. CANDIDATOS ACTIVOS

| Candidato | Código | Fase actual | Riesgo principal |
|-----------|--------|-------------|-----------------|
| Bangni PCSsole C1 | HW-BANGNI-C1 | Fase 1 DESKTOP | OQ-01/02: protocolo probablemente cerrado |
| Maxrays ZRX-503B | HW-MAXRAYS-503B | Fase 1 DESKTOP | Protocolo desconocido |
| OEM Shenzhen custom | HW-SZ-CUSTOM-01 | No iniciada | Mayor flexibilidad de spec, lead time más largo |

Benchmark referencia: Jalas FootStopService (Ejendals, Suecia) — no es un competidor directo, es un referente de posicionamiento.

---

## D. RELACIONES

| Ref | Uso |
|-----|-----|
| ENT_PROD_SCANNER §F | Criterios de aceptación completos (fuente) |
| ENT_PROD_SCANNER §G | Lista proveedores candidatos |
| ENT_PROD_SCANNER_GLOSARIO | Términos técnicos (PP, PTI, COP, etc.) |
| PLB_SCANNER_DISTRIB | Modelo comercial y pricing para distribuidores |
| PLB_SUPPLIER_EVAL | Protocolo general evaluación proveedores |
| ENT_GOB_PROVEEDORES | Registro de proveedores donde se documenta el resultado |
| ENT_COMERCIAL_PRICING | No aplica hasta post-selección hardware |

---

Stamp: DRAFT — Pendiente aprobación CEO
Aprobador: CEO
Origen: Creado 2026-03-11 — resuelve ref rota ENT_PROD_SCANNER §G → "ref → PLB_INVESTIGACION para protocolo completo"
