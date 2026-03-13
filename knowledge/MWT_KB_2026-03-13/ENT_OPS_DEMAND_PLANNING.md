# ENT_OPS_DEMAND_PLANNING — Demand Planning & Forecasting
status: DRAFT — Pendiente aprobación CEO
visibility: [INTERNAL]
domain: Operaciones (IDX_OPS)
version: 1.1

---

## A — MODELO DE MADUREZ

### A1. Fase actual: F1 MANUAL
- 1 producto activo (Goliath), 6 SKUs, 1 canal (Amazon FBA), 1 mercado (USA)
- Historial: <12 meses
- Método: reglas manuales (ref → ENT_OPS_INVENTARIO)

### A2. Fases y triggers de activación

| Fase | Trigger | Método forecast | Herramientas |
|------|---------|----------------|--------------|
| F1: Manual | 1-10 SKUs, <12 meses, 1 mercado | Reglas fijas + SMA 4-6 semanas | Google Sheets, Seller Central |
| F2: Semi-auto | 10+ SKUs, 12+ meses, 1-2 mercados | Holt-Winters, Prophet baseline | Python + Prophet + SQLite |
| F3: Automático | 25+ SKUs, 2+ mercados, 18+ meses | Multi-modelo con selección automática | Python + sktime + PostgreSQL |
| F4: Inteligente | 50+ SKUs, 3 mercados, 24+ meses | ML (LightGBM/XGBoost) + reconciliación jerárquica | Data warehouse + ML pipeline |

### A3. Lógica toggle (igual que productos)
- F2 toggle: APAGADO. Se enciende cuando trigger A2 se cumple.
- F3 toggle: APAGADO. Se enciende cuando trigger A2 se cumple.
- F4 toggle: APAGADO. Se enciende cuando trigger A2 se cumple.
- Transición NO es automática. Sistema sugiere, CEO aprueba.

### A4. Qué NO hacer por fase

| Fase | NO hacer | Razón |
|------|----------|-------|
| F1 | Software enterprise (>$200/mes) | ROI negativo con 6 SKUs |
| F1 | ML / modelos estacionales | Datos insuficientes, resultados inestables |
| F2 | ML "black box" sin benchmark naive | Sin baseline no sabés si el modelo aporta |
| F3 | Forecast sin reconciliación jerárquica | Suma de partes ≠ total → decisiones inconsistentes |

---

## B — DATOS MÍNIMOS POR MODELO

### B1. Requisitos verificados

| Modelo | Datos mínimos | MAPE esperable | Fuente |
|--------|--------------|----------------|--------|
| Naïve / SMA | 4-8 semanas | 30-40% | [EVIDENCIA] M1 Competition, Makridakis 1982 |
| SES (α=0.3) | 8-12 puntos | 30-40% | [EVIDENCIA] Hyndman & Athanasopoulos 2021 |
| Holt-Winters | 17+ obs mensuales | 22-32% | [EVIDENCIA] Hyndman et al. 2002: m+4 parámetros, m=12 |
| Prophet | 50+ obs diarias (~2 meses) | 20-28% | [HEURÍSTICA] Meta docs, no paper peer-reviewed |
| ARIMA/SARIMA | 50-100 obs | 20-30% | [EVIDENCIA] Box-Jenkins methodology |
| LightGBM/XGBoost | 1000+ obs/SKU | 10-20% | [EVIDENCIA] M5 Competition, Makridakis 2020 |

### B2. Hallazgos M-Competitions (referencia base)

| Competencia | Hallazgo clave | Implicación MWT |
|-------------|---------------|-----------------|
| M1 (1982) | Métodos simples superaron complejos | Con <12 meses, usar SMA/SES |
| M4 (2018) | Combinaciones > ML puro. Híbrido ganó por solo 9.4% | No apostar todo a un modelo |
| M5 (2020) | ML puro superó estadísticos por primera vez (LightGBM, +22.4%) | Viable solo con 1000+ obs/SKU |

Clasificación: [EVIDENCIA] — papers peer-reviewed, competencias abiertas reproducibles.

### B3. Cuándo un promedio móvil supera a un modelo complejo
[EVIDENCIA] Makridakis et al. 2018:
- Menos de 100 observaciones por serie
- Señal-ruido baja
- Alta volatilidad sin patrones claros
- Datos con muchos outliers

Regla para MWT:
```
< 3 meses      → Naïve únicamente
3-6 meses      → SMA (4-6 semanas) o SES
6-12 meses     → Holt (si hay tendencia) o Seasonal Naïve
12-18 meses    → Holt-Winters o Prophet
18-24 meses    → Prophet o XGBoost básico
24+ meses      → LightGBM/XGBoost avanzado
```

---

## C — BENCHMARKS DE PRECISIÓN

### C1. MAPE por industria

| Industria | Excelente | Aceptable | Crítico | Fuente |
|-----------|-----------|-----------|---------|--------|
| FMCG | <10% | 10-20% | >25% | [HEURÍSTICA] Industry reports |
| Apparel/Footwear | <25% | 25-35% | >40% | [HEURÍSTICA] EasyReplenish 2025 |
| Health & Personal Care | <18% | 18-30% | >35% | [HEURÍSTICA] Industry benchmarks |

### C2. Targets MWT por fase

| Fase | MAPE target | Justificación |
|------|------------|---------------|
| F1 (6 SKUs, <12m) | <40% aceptable | Datos insuficientes para más |
| F2 (12+ meses) | <30% | Benchmark Apparel aceptable |
| F3 (18+ meses) | <25% | Benchmark Apparel excelente |
| F4 (24+ meses) | <20% | Target competitivo |

### C3. Métricas operativas Amazon FBA

| Métrica | F1 target | F2 target | Fuente |
|---------|-----------|-----------|--------|
| Stockout rate | <5% | <2% | [HEURÍSTICA] Industry standard |
| IPI Score | >400 | >450 | [EVIDENCIA] Amazon Seller Central guidelines |
| Sell-through rate | >40% | >60% | [HEURÍSTICA] Financial Models Lab 2025 |

---

## D — AMAZON FBA: VARIABLES DE DEMANDA

### D1. Estacionalidad categoría insoles
[EVIDENCIA] Journal of Foot & Ankle Research, 2014 (peer-reviewed):
- "Heel Pain" búsquedas: +57.9% en verano (p=0.004)
- "Foot Pain": +35.4% en verano (p=0.004)
- "INSOLE" como término: SIN estacionalidad significativa
- "INSOLE" es 13.7x más buscado que "FOOT ORTHOTIC"

Implicación: demanda de plantillas es más estable que dolor de pie. Picos de oportunidad (no de demanda base):
- Marzo-Mayo: preparación verano
- Agosto-Sept: Back-to-School
- Enero: resoluciones año nuevo

### D2. Efecto de reviews en conversión
[EVIDENCIA] PowerReviews 2023 (31,900 marcas, 12M reviews):
- 0→10 reviews: +270% conversión
- 10→50 reviews: +160% conversión
- 50+ reviews: 2-3x conversión vs <10
- 4.5→4.0 estrellas: -20% a -30% ventas [HEURÍSTICA: AMZigo 2025]
- Rating promedio Amazon: 4.23 estrellas

Meta Goliath: 50+ reviews en 3-6 meses, 100+ en 6-12 meses, mantener 4.3+ estrellas.

### D3. Efecto de stockouts en ranking
[EVIDENCIA] Trellis/8fig 2024 (524 productos):
- 1-2 semanas OOS → 2-4 semanas recuperación + PPC agresivo
- 30+ días OOS → 60-90 días recuperación
- 28+ días sin ventas → "esencialmente empezás de cero" [HEURÍSTICA: Onramp Funds]

Regla MWT: nunca bajar de 30 días de inventario. ref → ENT_OPS_INVENTARIO.

### D4. Eventos y multiplicadores
[HEURÍSTICA] Compilado de múltiples fuentes vendor:

| Evento | Multiplicador estimado | Timing preparación |
|--------|----------------------|-------------------|
| Prime Day (julio) | 1.5-2x | Enviar mayo-junio |
| Back-to-School (ago-sept) | 1.5-2x | Enviar junio-julio |
| Black Friday (nov) | 2-4x | Enviar sept-oct |

### D5. Canibalización entre productos propios
[HEURÍSTICA] Autron.ai 2026:
- Amazon NO permite competencia interna en subasta PPC (no hay keyword cannibalization en ads)
- SÍ existe sales cannibalization cuando productos comparten keywords orgánicos

Indicadores de alerta:
- Shared keywords >70%
- Cross-purchase rate >15%
- Caída conversión ASIN >20% al lanzar nuevo producto

Matriz de canibalización real: [PENDIENTE — NO INVENTAR. Requiere datos de ventas simultáneas de 2+ productos. Trigger: cuando ORB esté activo junto a GOL]

### D6. Halo effect PPC → orgánico
[HEURÍSTICA] Pattern.com: "5% to 60% lift over 12 months"
[HEURÍSTICA] Fospha 2024 (caso Nécessaire): Prime Day 7x revenue, 65% orgánico

Fórmula sugerida (NO verificada, usar como estimación inicial):
```
Organic Lift = Base Organic × (1 + PPC Spend Factor × Halo Coefficient)
Halo Coefficient: Launch 0.30-0.40 | Growth 0.20-0.30 | Mature 0.10-0.20
```
Clasificación: [HEURÍSTICA] — calibrar con datos propios cuando haya 6+ meses de PPC.

### D7. Demanda censurada
Cuando un SKU está Out-of-Stock, las ventas registradas = 0. Ese 0 NO es demanda real, es demanda censurada.
Si se usa ese historial sin corregir, todo modelo futuro subestima la demanda.

Solución: registrar campo `in_stock: true/false` por SKU/día desde día uno.
Modelos futuros excluyen o interpolan días con `in_stock = false`.

---

## E — DATA CONTRACT (campos mínimos por SKU/día)

### E1. Registro diario obligatorio (Fase 1)

| Campo | Tipo | Fuente | Ejemplo |
|-------|------|--------|---------|
| date | DATE | Sistema | 2026-02-24 |
| sku | STRING | ENT_OPS_TALLAS | RW-GOL-MED-S3 |
| units_sold | INT | Seller Central | 4 |
| units_returned | INT | Seller Central | 0 |
| in_stock | BOOL | Seller Central / manual | true |
| price | DECIMAL | Seller Central | 37.99 |
| sessions | INT | Seller Central | 120 |
| conversion_rate | DECIMAL | Seller Central | 0.033 |
| ppc_spend | DECIMAL | Advertising Console | 15.50 |
| ppc_sales | DECIMAL | Advertising Console | 45.00 |
| reviews_count | INT | Seller Central | 23 |
| rating_avg | DECIMAL | Seller Central | 4.4 |
| bsr | INT | Seller Central / scrape | 18500 |
| fba_inventory | INT | Seller Central | 340 |

### E2. Registro semanal (calculado)

| Campo | Fórmula | Uso |
|-------|---------|-----|
| weekly_velocity | SUM(units_sold) últimos 7 días | Safety stock, reposición |
| days_of_stock | fba_inventory / (weekly_velocity / 7) | Semáforo inventario |
| tacos | ppc_spend / (ppc_sales + organic_sales) | ref → PLB_ADS |
| size_curve_actual | units_sold por talla / total | Comparar vs curva fija |

### E3. Campos futuros (cuando haya 2+ productos)

| Campo | Cuándo activar | Uso |
|-------|---------------|-----|
| cross_purchase_rate | 2+ productos activos | Detectar canibalización |
| shared_keywords_pct | 2+ productos activos | Alerta canibalización |
| competitor_bsr | Cuando se implemente tracking | Contexto competitivo |

---

## F — REGLAS DE DECISIÓN (tipo semáforo)

### F1. Cuándo recalcular la curva de tallas
Curva actual fija: S1:5%, S2:10%, S3:20%, S4:25%, S5:30%, S6:10% (ref → ENT_OPS_TALLAS)

```
SI: |%Ventas_real - %Curva_fija| > 5% para cualquier talla
Y: se mantiene por 2 meses consecutivos
ENTONCES: recalcular curva completa con últimos 6 meses de datos

SI: |%Ventas_real - %Curva_fija| entre 3-5%
ENTONCES: MONITOREAR — revisión quincenal

SI: |%Ventas_real - %Curva_fija| < 3%
ENTONCES: MANTENER — revisión mensual
```

### F2. Cuándo ajustar safety stock
Actual: 35 días fijo (ref → ENT_OPS_INVENTARIO)

```
Calcular CV = σ(ventas diarias) / μ(ventas diarias) con últimos 30 días

SI: CV < 0.2 (demanda estable)
ENTONCES: reducir safety stock a 25-30 días

SI: CV 0.2-0.5 (demanda variable)
ENTONCES: mantener 35 días

SI: CV > 0.5 (demanda errática)
ENTONCES: aumentar a 40-50 días

Fórmula completa (cuando haya datos suficientes):
SS = Z × √[(LT × σD²) + (μD² × σLT²)]
donde Z=1.65 (95% service level), LT=lead time días, σD=desv ventas, σLT=desv lead time
```

### F3. Cuándo el modelo forecast ya no sirve

```
SI: MAPE del modelo > MAPE del forecast naïve
ENTONCES: modelo no aporta valor → cambiar inmediatamente
[EVIDENCIA] Principio básico de forecasting

SI: MAPE > 35% durante 3 meses consecutivos (en F2+)
Y: se tienen 12+ meses de datos
ENTONCES: evaluar modelo alternativo

Semáforo MAPE (Fase actual F1):
🟢 < 35%    → aceptable
🟡 35-50%   → monitorear
🔴 > 50%    → investigar
```

### F4. Cuándo activar forecast sugerido (auto-trigger)

```
MODO 1 → MODO 2 (transición):

Paso 1: Sistema acumula datos según data contract (sección E)
Paso 2: A partir de mes 6, sistema calcula SMA en background (no muestra)
Paso 3: Sistema compara SMA vs ventas reales, calcula su propio MAPE
Paso 4: SI MAPE < 35% por 3 meses consecutivos
         Y datos_días >= 180
         ENTONCES: alerta al CEO
         "Forecast estadístico disponible. MAPE histórico: X%. ¿Activar sugeridos?"
Paso 5: CEO aprueba → sistema muestra forecast junto a reglas manuales
         CEO rechaza → sistema sigue en Modo 1, re-evalúa en 30 días
```

### F5. Reglas PPC extendidas (complementan ref → PLB_ADS)

```
YA EXISTENTE: Nunca escalar PPC si stock < 21 días

EXTENSIONES:
SI: 21d ≤ stock < 35d Y ventas > 150% del forecast
ENTONCES: escalar PPC moderadamente (1.2x-1.5x budget)

SI: stock ≥ 35d Y ventas > 120% del forecast
ENTONCES: escalar PPC agresivamente (1.5x-2x budget)

SI: stock < 14d
ENTONCES: pausar PPC + evaluar pedido urgente
```

### F6. Trigger lanzamiento siguiente producto

```
SI: SKU actual ≥ 6 meses de datos
Y: MAPE < 40%
Y: stock ≥ 30 días estable
Y: reviews ≥ 50 (ref → D2)
ENTONCES: condiciones operativas para siguiente producto cumplidas
NOTA: decisión de lanzamiento sigue siendo del CEO (ref → ENT_PROD_LANZAMIENTO)
```

### F7. Fórmula de restock automatizado (AUT-004, fase F1)

Origen: Sesión Swarm 2026-03-13. Ref → ENT_PLAT_AUTOMATIONS AUT-004.

```
velocity = sum(units_sold últimos 30 días WHERE in_stock=true) / count(días WHERE in_stock=true)
punto_pedido = lead_time + safety_stock   # ej Goliath: 30 + 35 = 65 días
necesita_restock = days_remaining < punto_pedido
demanda_cobertura = velocity × (lead_time + safety_stock + horizonte_forecast)
cajas_necesarias = ceil(demanda_cobertura / MOQ_caja_master)
```

Reglas aplicadas:
- Velocity excluye días OOS (in_stock=false). Ref → ENT_PLAT_DECISIONES.AUT-D11.
- Safety stock = 35 días (ref → ENT_OPS_INVENTARIO). Parametrizable en Windmill.
- MOQ desde product_master. Si NULL → skip SKU + alerta CEO. Nunca hardcoded. Ref → AUT-D10.
- Cálculo agregado por familia (caja master con curva fija). No por SKU individual. Ref → AUT-D9.
- Prophet no activo en F1. Solo SMA. Ref → AUT-D3.

Ejemplo Goliath:
- Velocity total: 3 ud/día (todas tallas)
- Lead time: 30 días, safety: 35 días, horizonte: 60 días → período 125 días
- Demanda total: 375 unidades
- MOQ caja master: 12 unidades
- Cajas necesarias: ceil(375/12) = 32 cajas (384 unidades)
- Curva por caja (12 ud): S1:5% S2:10% S3:20% S4:25% S5:30% S6:10%
- Recomendación: "Pedir 32 cajas master (384 unidades)"

---

## G — RECONCILIACIÓN JERÁRQUICA (referencia futura)
status: TOGGLE APAGADO — se activa con F3 (25+ SKUs, 2+ mercados)

### G1. Método recomendado: MinT(Shrink)
[EVIDENCIA] Wickramasuriya et al., JASA 2019: mejor balance de precisión en múltiples niveles.
Implementación: Python `scikit-hts` o `hierarchicalforecast` (Nixtla)

### G2. Estructura jerárquica MWT (futura)
```
Total Global → Mercado (3) → Producto (5) → Talla (6) → Arco (1-3)
Bottom-level series: hasta 162 (3 mercados × 54 SKUs)
```

### G3. Variantes sin historial (LOW/MED/HGH)
Proporciones iniciales sugeridas para Leopard y Bison:
- LOW: 30%, MED: 50%, HGH: 20%
[HEURÍSTICA] Athanasopoulos et al. 2009. Calibrar con datos reales cuando existan.
Trigger: cuando LEO o BIS estén activos.

### G4. Canibalización planificada
Método: generar forecasts independientes → estimar matriz canibalización → reconciliar con MinT.
Matriz real: [PENDIENTE — NO INVENTAR. Trigger: cuando ORB esté activo junto a GOL]

---

## H — FUENTES Y CLASIFICACIÓN

### H1. Taxonomía de confianza

| Tag | Significado | Ejemplo |
|-----|------------|---------|
| [EVIDENCIA] | Paper peer-reviewed, competencia abierta, dato oficial | M-Competitions, Hyndman, JFAR 2014, Amazon guidelines |
| [HEURÍSTICA] | Blog vendor, reporte consultoría, estimación de industria | EasyReplenish, Pattern.com, Autron.ai |
| [PENDIENTE] | No hay dato confiable | Matriz canibalización, MAPE específico insoles |

### H2. Fuentes principales

| Fuente | Tipo | Año | Usado en |
|--------|------|-----|----------|
| M1-M5 Competitions (Makridakis et al.) | [EVIDENCIA] | 1982-2020 | B1, B2, B3 |
| Hyndman & Athanasopoulos, FPP3 | [EVIDENCIA] | 2021 | B1 |
| Wickramasuriya et al., JASA | [EVIDENCIA] | 2019 | G1 |
| Journal of Foot & Ankle Research | [EVIDENCIA] | 2014 | D1 |
| PowerReviews Amazon Report | [EVIDENCIA] | 2023 | D2 |
| Trellis/8fig stockout study | [EVIDENCIA] | 2024 | D3 |
| Amazon Seller Central IPI | [EVIDENCIA] | 2025 | C3 |
| Pattern.com, Fospha, Autron.ai | [HEURÍSTICA] | 2024-2026 | D5, D6 |
| EasyReplenish, ArticSledge | [HEURÍSTICA] | 2025 | C1 |

---

## Z — PENDIENTES

| ID | Pendiente | Desbloquea | Trigger |
|----|-----------|-----------|---------|
| Z1 | Benchmarks MAPE específicos para insoles en Amazon | Calibrar targets C2 | Investigación adicional |
| Z2 | Estacionalidad propietaria (Jungle Scout/Helium 10 data) | Validar/refinar D1 | Suscripción a herramienta |
| Z3 | Elasticidad precio-demanda plantillas biomecánicas | Pricing dinámico futuro | 12+ meses de datos con variación precio |
| Z4 | Matriz canibalización real entre productos | Activar G4 | ORB activo junto a GOL |
| Z5 | Lead times reales por ruta (validar vs ENT_OPS_LOGISTICA) | Calibrar fórmula SS en F2 | Registro de primeros 3 envíos |
| Z6 | Datos comportamiento demanda por talla en health products | Validar curva fija | 6+ meses de data contract E1 |
| Z7 | Proporciones arco LOW/MED/HGH reales | Calibrar G3 | LEO o BIS activos |

---

Stamp: DRAFT — Pendiente aprobación CEO
Fuente: Investigación Kimi (6 sub-agentes, 60+ fuentes) + filtro ChatGPT (10 mejoras) + validación Gemini
Fecha compilación: 2026-02-24
Próxima revisión sugerida: cuando Goliath alcance 12 meses de historial

Changelog:
- v1.0 (2026-02-24): Compilación inicial
- v1.1 (2026-03-13): +F7 fórmula restock automatizado (FRAGMENTO_F7 integrado). +version: field en header.
