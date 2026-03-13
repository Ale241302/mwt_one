# ENT_PROD_SCANNER — Rana Walk Pressure Scanner
id: ENT_PROD_SCANNER
version: 3.0
domain: PRODUCTO
status: DRAFT
visibility: [INTERNAL] — sección PRICING [CEO-ONLY]
stamp: DRAFT — pendiente aprobación CEO
fuente: Research sesión 2026-03-01

---

## A. IDENTIDAD

- Nombre comercial: Rana Walk Pressure Scanner
- Código interno: RW-SCANNER-01
- Spec de referencia: RW-HW-SPEC-004
- Tipo: Mat de sensores de presión plantar bilateral estático
- Posicionamiento: Herramienta de prescripción en punto de venta. No dispositivo médico.
- Mercados target: CR, BR, USA

---

## B. ESPECIFICACIÓN TÉCNICA — TARGET MÍNIMO IDEAL

### B1. Dimensiones físicas
| Parámetro | Valor |
|-----------|-------|
| Área activa | 41 × 41 cm |
| Área total | 1,681 cm² |
| Factor de forma | Mat plano rectangular |
| Grosor | < 12 mm preferido · límite duro 20 mm |
| Peso | < 2.5 kg |
| Superficie | Antideslizante, limpiable, marcas de posicionamiento impresas |
| IP rating | IP42 mínimo |
| Cable mínimo | 1.5 m incluido |

### B2. Array de sensores
| Parámetro | Valor | Justificación |
|-----------|-------|---------------|
| Sensores totales | 1,681 | Mínimo ideal |
| Grid | 41 × 41 | Cuadrado uniforme |
| Densidad | 1.00 sensor/cm² | 3 sensores mínimo en Z7/Z8 (zona de 3 cm²) |
| Celda por sensor | 1.0 × 1.0 cm | 1 sensor = 1 cm² → estimación peso sin conversión |
| Tecnología preferida | Capacitiva | Menor histéresis, mejor linealidad |
| Tecnología aceptable | FSR / piezoresistiva | — |
| Tecnología rechazada | Piezoeléctrica | Carga se disipa en modo estático |

Por qué 1,681 y no menos:
- Con 1,024: Z7/Z8 tienen 2 sensores → detección booleana, PP no confiable
- Con 1,681: Z7/Z8 tienen 3 sensores → PP válido en todas las zonas
- Con 2,048+: mejora marginal, duplica costo — no justificado

### B3. Cobertura por talla
| Talla EU | Cobertura | Clearance longitudinal |
|----------|-----------|----------------------|
| EU 35–47 | Garantizado | 6+ cm |
| EU 48 | Funcional | 5.25 cm |
| EU 49 | Funcional | 4.95 cm |
| EU 50 | Ajustado | 4.60 cm |

Población cubierta: ~94% masculina LATAM · ~87% masculina USA

### B4. Zonas anatómicas (EU 47 — caso de diseño)
| Zona | Región | Sensores | Estado |
|------|--------|---------|--------|
| Z1 | Talón medial | 18 | ✅ PP + PTI + simetría L/R |
| Z2 | Talón lateral | 14 | ✅ |
| Z3 | Arco / mediopié | 15 | ✅ midfoot_contact_pct confiable |
| Z4 | MTH1 — 1er metatarso | 6 | ✅ |
| Z5 | MTH2 — 2do metatarso | 5 | ✅ |
| Z6 | MTH3 — 3er metatarso | 4 | ✅ |
| Z7 | MTH4 — 4to metatarso | 3 | ✅ Mínimo funcional |
| Z8 | MTH5 — 5to metatarso | 3 | ✅ Mínimo funcional |
| Z9 | Hallux | 4 | ✅ |
| Z10 | Dedos menores 2–5 | 6 | ✅ |

Z1–Z5 determinan el 85% del score de recomendación.

### B5. Adquisición
| Parámetro | Valor |
|-----------|-------|
| Frecuencia | 50 Hz (óptimo) · 25 Hz (aceptable) |
| Modo | Estático bilateral simultáneo |
| Frames por captura | 50 (1 segundo) |
| Frames descartados | Primeros 5 (asentamiento) |
| Frames útiles promediados | 45 |
| Throughput | 1,681 × 2B × 50 Hz = 168 KB/s |
| Tiempo de calentamiento | ≤ 60 segundos |

### B6. Comunicación
| Interfaz | Estado | Especificación |
|---------|--------|---------------|
| USB-C | PRIMARIA requerida | USB 2.0 FS + carga PD en un conector |
| BLE | SECUNDARIA requerida | Mínimo 5.0 — BLE 4.2 satura a 168 KB/s |
| Driver propietario | RECHAZADO | Sin SDK abierto = descalificado |

Estructura del frame binario:
```
HEADER: 2B · TIMESTAMP: 4B · FRAME_ID: 4B · SENSOR_COUNT: 2B
DATA: 3,362B · CHECKSUM: 2B
Total por frame: 3,376 bytes @ 50 Hz = 168 KB/s
```

Comandos requeridos: START_STREAM · STOP_STREAM · SET_RATE · TARE · GET_INFO · GET_COORD_MAP · PING

### B7. Alimentación
| Parámetro | Valor |
|-----------|-------|
| Batería | 2,000 mAh LiPo |
| Consumo activo | 60–100 mA a 3.7V |
| Duración estimada | 20–30 horas continuas |
| Carga | USB-C PD 18W → ~90 min |
| Bus power sin batería | 5V ≤ 500 mA |

### B8. Calibración
| Parámetro | Especificación |
|-----------|---------------|
| TARE | Comando host ≤ 5 seg |
| Calibración fábrica | Coeficientes gain/offset por sensor en certificado por unidad |
| Intervalo recalibración | ≥ 6 meses |
| Crosstalk máximo | < 8% FS |
| Drift cero (1 hora) | ±5 kPa target |
| Drift por temperatura | < 0.1% FS/°C documentado |

### B9. Especificaciones eléctricas del sensor
| Parámetro | Mínimo | Target |
|-----------|--------|--------|
| Rango de presión | 0–600 kPa | 0–1,000 kPa |
| Resolución ADC | 10 bits | 10 bits |
| Precisión absoluta (peso total) | ±10% | ±8% |
| Histéresis | < 15% FS | < 12% FS |
| Repetibilidad CV (10 cargas) | < 20% | < 15% |
| Tiempo de respuesta (90%) | < 15 ms | < 10 ms |
| Vida útil | 500,000 ciclos | 1,000,000 ciclos |

### B10. Certificaciones
| Certificación | Estado | Mercado |
|--------------|--------|---------|
| CE (LVD + EMC) | REQUERIDA | Global |
| RoHS | REQUERIDA | Global |
| FCC Part 15 | REQUERIDA si BLE | USA |
| ANATEL | REQUERIDA | Brasil |
| FDA / ISO 13485 | NO requerida | Wellness, no médico |

---

## C. ARQUITECTURA SOFTWARE — 4 CAPAS

MWT es propietario de todas las capas. OEM provee solo hardware y protocolo.

**Capa 1 — Driver (Python / MWT)**
Conecta BLE/USB · TARE · SET_RATE 50 · START_STREAM · Parsea frames → float[41][41] @ 50 Hz

**Capa 2 — Motor Biomecánico (Python / MWT)**
Blob detection · PCA · Heel detection · Zone mapping Z1–Z10
Métricas: PP · PTI · COP · midfoot_contact_pct · peso estimado · longitud/ancho pie
Nota: requiere datos_de_atenuación del OEM para modo calcetín → ref ENT_PROD_SCANNER_GLOSARIO

**Capa 3 — Motor de Recomendación (Python / MWT)**
Árbol determinístico → línea Rana Walk: Goliath / Bison / Velox / Orbis / Leopard
Talla en EU/US/BR según mercado activo · cruce con catálogo del distribuidor

**Capa 4 — UI (Electron / React / MWT)**
Mapa de calor bilateral · Comparación pre/post plantilla · Cadena biomecánica visual · Módulo catálogo

---

## D. MÓDULO FIT MATCHING

El distribuidor carga su catálogo una vez. Sistema cruza perfil biomecánico con dimensiones internas.

Regla: `long_interna_calzado ≥ long_pie_mm + 10 mm` (mínimo 7 mm · óptimo 12–15 mm)
Ref longitudes por talla → ENT_MERCADO_TALLAS

Campos requeridos por SKU:
```
marca, modelo, talla_eu, long_interna_mm, ancho_interno_mm, horma
```

---

## E. ENTREGABLES OBLIGATORIOS DEL OEM

| Entregable | Estado |
|-----------|--------|
| Protocolo de comunicación documentado (PDF o MD) | OBLIGATORIO |
| Mapa coordenadas índice → (x_mm, y_mm) en JSON/CSV | OBLIGATORIO |
| Referencia comandos con encoding byte a byte | OBLIGATORIO |
| Estructura frame binario con offsets de campo | OBLIGATORIO |
| Certificado de calibración por unidad (con coeficientes) | OBLIGATORIO |
| Procedimiento de recalibración de campo | OBLIGATORIO |
| Datasheet eléctrico y mecánico completo | OBLIGATORIO |
| Driver Python funcional de ejemplo | FUERTEMENTE PREFERIDO |

---

## F. CRITERIOS DE ACEPTACIÓN

| # | Test | Condición de aprobación |
|---|------|------------------------|
| AC-01 | SDK disponible | Entregado antes o junto con la muestra |
| **AC-02 ★ GATE** | Integración driver | Ingeniero MWT lee frames crudos Python en < 4 horas |
| AC-03 | Cobertura zonas | ≥ 3 sensores en Z7/Z8 para EU 47 |
| AC-04 | Precisión presión | Carga 50 kg: PP dentro de ±10% del esperado |
| AC-05 | Frecuencia | Stream 50 Hz sin drops durante 1 minuto continuo |
| AC-06 | Repetibilidad | 50 kg × 10 repeticiones: CV < 15% |
| AC-07 | TARE | Zerifica en ≤ 5 segundos |
| AC-08 | Modo calcetín | Lectura estable con calcetín industrial estándar |
| AC-09 | Inspección física | ≥ 39×39 cm efectivos · antideslizante · cable ≥ 1.5 m · IP42 · < 2.5 kg |
| AC-10 | Batería | ≥ 8 horas continuas desde carga completa |

**Si AC-02 falla → no se realizan otras pruebas. No comprar el hardware.**
Ref definición AC-08 → ENT_PROD_SCANNER_GLOSARIO

---

## G. PROVEEDORES CANDIDATOS

| Candidato | Código MWT | Estado | Riesgo principal |
|-----------|-----------|--------|-----------------|
| Bangni PCSsole C1 | HW-BANGNI-C1 | CANDIDATO PRINCIPAL | OQ-01/02: protocolo probablemente cerrado |
| Maxrays ZRX-503B | HW-MAXRAYS-503B | CANDIDATO SECUNDARIO | Protocolo desconocido |
| Sourcing Shenzhen custom | HW-SZ-CUSTOM-01 | ALTERNATIVA | Lead time más largo |

### Preguntas abiertas al OEM (ref PLB_INVESTIGACION para protocolo completo)

| # | Pregunta | Estado |
|---|---------|--------|
| OQ-01 | ¿Datos crudos sin software OEM en host? | [PENDIENTE] |
| OQ-02 | ¿Protocolo transferible a MWT? ¿Términos? | [PENDIENTE] |
| OQ-03 | Conteo exacto sensores y grid actual | [PENDIENTE] |
| OQ-04 | Frecuencia máxima configurable vía host | [PENDIENTE] |
| OQ-05 | Consumo corriente 25/50 Hz USB y batería | [PENDIENTE] |
| OQ-06 | ¿Personalización colores Rana Walk? ¿MOQ? | [PENDIENTE] |
| OQ-07 | CE Declaration. FCC ID si BLE. | [PENDIENTE] |
| OQ-08 | Precio qty 1/5/10/50 flete Costa Rica | [PENDIENTE — CEO-ONLY] |
| OQ-09 | Lead time muestra y qty 5/50 | [PENDIENTE — CEO-ONLY] |
| OQ-10 | ¿Modo calcetín validado? ¿Atenuación documentada? | [PENDIENTE] |

---

## H. BENCHMARKS DE REFERENCIA [INTERNAL]

| Sistema | Dimensiones | Sensores | Densidad | Precio mercado |
|---------|-------------|---------|---------|---------------|
| Tekscan MatScan | 43.7×36.8 cm | 2,288 | 1.42/cm² | $8,000–12,000 |
| Novel Emed | 58×42 cm | 2,704 | 1.11/cm² | $15,000–25,000 |
| Bangni PCSsole C1 | ~40×40 cm | ~512–1,024 [EST] | ~0.32–0.64/cm² [EST] | $300–800 [EST] |
| Maxrays ZRX-503B | ~45×40 cm | 2,048 [EST] | ~1.14/cm² [EST] | $1,100–2,495 [EST] |
| **RW-SCANNER-01 (target)** | **41×41 cm** | **1,681** | **1.00/cm²** | [PENDIENTE — cotización OEM] |

---

## I. PRICING OEM [CEO-ONLY]

Estimaciones de research. No son precios confirmados.

### BOM estimado (China, qty 50)
| Componente | USD estimado |
|-----------|-------------|
| Film FSR/capacitivo 41×41 custom | $80–140 |
| MCU + BLE 5.0 (nRF52840 o equiv.) | $8–15 |
| Multiplexores ~26 ICs | $15–30 |
| PCB + ensamble | $25–50 |
| Enclosure rígido + superficie | $15–30 |
| Batería LiPo 2,000 mAh + circuito carga | $8–15 |
| Cable USB-C 1.5 m | $2–4 |
| Calibración por unidad | $10–20 |
| **BOM total estimado** | **$163–304** |

### Precios OEM estimados por volumen
| Cantidad | Precio unitario USD estimado |
|----------|---------------------------|
| 1 muestra | $350–550 |
| 5–10 | $280–420 |
| 50 | $220–320 |
| 200+ | $180–260 |

PENDIENTE — NO CONFIRMADO: cotización real Bangni y proveedor Shenzhen.
Ref modelo comercial y canal → PLB_SCANNER_DISTRIB
