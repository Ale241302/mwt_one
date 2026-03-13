# ENT_PROD_SCANNER_GLOSARIO — Glosario Técnico del Pressure Scanner
id: ENT_PROD_SCANNER_GLOSARIO
version: 1.0
domain: PRODUCTO
status: DRAFT
visibility: [INTERNAL]
stamp: DRAFT — pendiente aprobación CEO
refs: ENT_PROD_SCANNER, ENT_MERCADO_TALLAS

---

## Métricas biomecánicas

| Término | Definición | Unidad |
|---------|-----------|--------|
| PP | Peak Pressure — presión máxima registrada en una zona | kPa |
| PTI | Pressure-Time Integral — acumulación de presión durante la captura | kPa·s |
| COP | Center of Pressure — coordenada (x,y) del centroide de presión | mm |
| midfoot_contact_pct | Porcentaje del área del mediopié con presión > umbral | % |
| peso_estimado | Suma de fuerza total (presión × área de celda) convertida a kg | kg |
| longitud_pie | Distancia entre el punto más posterior y más anterior del blob | mm |
| ancho_pie | Distancia medial-lateral máxima del blob | mm |

## Procesamiento de señal

| Término | Definición |
|---------|-----------|
| Blob detection | Algoritmo que identifica la huella del pie separándola del fondo (sensores sin carga) |
| PCA | Principal Component Analysis — determina orientación del pie en el mat |
| Heel detection | Localización del centroide del talón para anclar el mapa de zonas |
| Zone mapping | Asignación de cada sensor a una zona anatómica Z1–Z10 |
| TARE | Comando de zerificación — establece la lectura actual como baseline |
| Frame | Una lectura completa de todos los sensores en un instante |
| Throughput | Volumen de datos por segundo: sensores × 2B × frecuencia |

## Zonas anatómicas Z1–Z10

| Zona | Región anatómica | Relevancia clínica |
|------|-----------------|-------------------|
| Z1 | Talón medial | Pronación, impacto inicial |
| Z2 | Talón lateral | Supinación, estabilidad |
| Z3 | Arco / mediopié | Tipo de arco (plano, normal, cavo) |
| Z4 | MTH1 — 1er metatarso | Distribución de carga anterior |
| Z5 | MTH2 — 2do metatarso | Punto de mayor presión frecuente |
| Z6 | MTH3 — 3er metatarso | Transición medial-lateral |
| Z7 | MTH4 — 4to metatarso | Carga lateral anterior |
| Z8 | MTH5 — 5to metatarso | Carga lateral extrema |
| Z9 | Hallux | Propulsión, balance |
| Z10 | Dedos menores 2–5 | Agarre, estabilidad final |

## Hardware

| Término | Definición |
|---------|-----------|
| FSR | Force Sensing Resistor — sensor piezoresistivo |
| Capacitiva | Tecnología de sensor basada en cambio de capacitancia con presión |
| Crosstalk | Interferencia entre sensores adyacentes, medida como % del fondo de escala |
| Drift cero | Cambio en la lectura baseline sin carga durante un período |
| Gain/offset | Coeficientes de calibración por sensor (fábrica) |
| Modo calcetín | Lectura con calcetín puesto — requiere datos de atenuación del OEM |
| Datos de atenuación | Coeficientes de corrección que compensan la absorción del calcetín |

## Fit Matching

| Término | Definición |
|---------|-----------|
| long_interna_calzado | Longitud interna medida de un calzado específico | 
| Regla de holgura | `long_interna ≥ long_pie_mm + 10 mm` (mín 7, ópt 12–15) |
| Horma | Forma interna del calzado que determina el ajuste |

---

Stamp: DRAFT — pendiente aprobación CEO
Origen: Extraído de ENT_PROD_SCANNER v3.0 — sesión 2026-03-01
