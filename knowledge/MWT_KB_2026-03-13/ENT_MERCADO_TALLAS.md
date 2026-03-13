# ENT_MERCADO_TALLAS
id: ENT_MERCADO_TALLAS
version: 2.0
domain: MERCADOS
status: DRAFT
visibility: [INTERNAL]
stamp: DRAFT — pendiente aprobación CEO
fuente: Research sesión 2026-03-01
fuente_primaria: Volumental 1.2M scans (Nature Scientific Reports 2019) · Viakix 100K órdenes · estudios académicos de distribución de tallas

---

## ADVERTENCIA DE DATOS [POL_VACIO]

Los datos de distribución para LATAM son **estimaciones derivadas** de la correlación entre estatura promedio y talla de calzado. No existe estudio estadístico oficial publicado para mercados latinoamericanos. Ningún gobierno registra tallas como estadística vital. Los campos marcados con `[EST]` son estimaciones — no deben usarse como dato confirmado en documentos externos ni en cálculos de inventario críticos sin validación adicional.

Datos confirmados: USA (retail data + estudios académicos con n > 100,000) · Europa (Volumental 1.2M scans)

---

## PARÁMETROS ESTADÍSTICOS — POBLACIÓN ADULTA MASCULINA

La distribución de tallas sigue una curva normal (validado en USA y Europa).

| Región | Media EU | Desviación estándar | N muestra | Confianza |
|--------|---------|--------------------|-----------|---------  |
| USA hombres | 44–45 | ~1.9 | >100,000 | Alta |
| Europa hombres | 43–44 | ~1.8 | 1,200,000 (Volumental) | Muy alta |
| LATAM hombres | 42–43 [EST] | ~1.9 [EST] | Sin estudio propio | Baja — estimación |
| USA mujeres | 38.5–39 EU | ~1.5 | >100,000 | Alta |
| LATAM mujeres | 37–38 EU [EST] | ~1.5 [EST] | Sin estudio propio | Baja — estimación |

Justificación estimación LATAM: correlación estatura promedio → talla de pie. Hombre promedio LATAM ~5 cm más bajo que USA → diferencia estimada de 1–2 tallas EU.

---

## DISTRIBUCIÓN MASCULINA — MODELO ESTADÍSTICO

Modelo basado en normal(μ=43, σ=1.9) para LATAM · normal(μ=44, σ=1.9) para USA

| Talla EU | % en talla | % acumulado LATAM | % acumulado USA | Excluidos si tope = esta talla |
|----------|-----------|-------------------|-----------------|-------------------------------|
| 38 | 0.5% | 0.5% | — | >99% |
| 39 | 1.8% | 2.3% | — | ~99% |
| 40 | 4.8% | 7.1% | — | ~93% |
| 41 | 9.2% | 16.3% | — | ~84% |
| 42 | 15.0% | 31.3% | ~10% | ~69% |
| **43** | **19.1%** | **50.4%** | ~25% | ~50% |
| 44 | 15.0% | 65.4% | **50%** | ~35% |
| 45 | 9.2% | 74.6% | ~69% | ~25% |
| 46 | 4.8% | 79.4% | ~79% | ~21% |
| **47** | **2.5%** | **81.9% [EST]** | **~87%** | **~18%** |
| 48 | 0.9% | 82.8% [EST] | ~92% | ~8% |
| 49 | 0.4% | 83.2% [EST] | ~96% | ~4% |
| 50 | 0.07% | 83.3% [EST] | ~98.5% | ~1.5% |

### Cobertura por tope de diseño del mat
| Tope diseño | Cobertura LATAM [EST] | Cobertura USA | Excluidos LATAM |
|-------------|----------------------|---------------|-----------------|
| EU 45 | ~74% | ~69% | ~26% |
| EU 46 | ~85% | ~79% | ~15% |
| **EU 47 — RW-SCANNER-01** | **~94%** | **~87%** | **~6%** |
| EU 48 | ~97% | ~92% | ~3% |
| EU 49 | ~98.5% | ~96% | ~1.5% |
| EU 50 | ~99.5% | ~98.5% | ~0.5% |

**Decisión de diseño adoptada:** EU 47 como talla de diseño. EU 49 funcional con clearance 4.95 cm. EU 50 con guía de posicionamiento. Ref especificación → ENT_PROD_SCANNER.

---

## DISTRIBUCIÓN FEMENINA

| Talla EU | Rango | % aproximado USA | % LATAM [EST] |
|----------|-------|-----------------|----------------|
| 35–36 | Pequeña | ~5% | ~8% |
| 37–38 | Debajo promedio | ~20% | ~25% |
| **39–40** | **Promedio — moda** | **~40%** | **~40%** |
| 41–42 | Arriba promedio | ~25% | ~20% |
| 43+ | Grande | ~10% | ~7% |

Fuente USA: Viakix 100,000 órdenes — talla más vendida US 8 = EU 39 (29% del volumen) · US 9 = EU 40 (22–27%)

---

## DATOS POR MERCADO

### USA
| Parámetro | Hombres | Mujeres |
|-----------|---------|---------|
| Talla media US | 10–11 | 8.5 |
| Talla media EU equiv. | 44–45 | 38.5–39 |
| Moda (talla más vendida) | US 10 = EU 44 | US 8 = EU 39 |
| P25 | EU 43 | EU 38 |
| P50 | EU 44 | EU 39 |
| P75 | EU 45 | EU 40 |
| Tendencia | +1.5 tallas en 30 años | Similar |

Nota regional: Noreste y Oeste promedian ligeramente mayor que Sur. Latinos dentro de USA tienen instep más bajo y talón más estrecho que promedio caucásico.

### LATAM general [EST]
| Parámetro | Hombres | Mujeres |
|-----------|---------|---------|
| Media estimada EU | 42–43 | 37–38 |
| Diferencia vs USA | 1–2 tallas menos | 1–1.5 tallas menos |
| Justificación | Estatura promedio ~5 cm menor | Idem |

### Calzado industrial LATAM — perfil específico [EST]
| Segmento | Talla media EU | Rango stock típico |
|---------|---------------|--------------------|
| Manufactura (hombres) | 41–43 | EU 38–46 |
| Construcción (hombres) | 41–44 | EU 38–47 |
| Logística / distribución | 41–43 | EU 38–45 |
| Industria pesada | 42–44 | EU 39–48 |

Incidencia tallas grandes en fuerza laboral industrial LATAM [EST]:
- EU 47: ~3–4% de trabajadores
- EU 48: ~1.2%
- EU 49: ~0.4%
- EU 50: ~0.1%

En empresa de 500 trabajadores: ~15–20 personas con EU 47+. Cubiertos con clearance + guía de posicionamiento en el mat.

### Brasil — sistema propio
Brasil usa sistema numérico propio (BR). La correlación EU↔BR no es exacta — cada fabricante puede variar hasta medio número. Siempre verificar con horma real del fabricante antes de cruzar tallas en fit matching.

### Costa Rica
Mercado mixto. Usa EU como referencia en calzado industrial. Distribuidores EPP locales manejan EU 38–46 como stock estándar. Tallas > EU 46 son pedido especial en la mayoría de los distribuidores.

---

## LONGITUDES DE PIE POR TALLA

Fórmula: long_pie_mm = (talla_EU × 6.67) − 15

| Talla EU | Longitud pie (mm) | Long. interna calzado típica (mm) |
|----------|------------------|------------------------------------|
| 35 | 218 | 230–235 |
| 36 | 225 | 237–242 |
| 37 | 231 | 243–248 |
| 38 | 238 | 250–255 |
| 39 | 245 | 257–262 |
| 40 | 252 | 264–269 |
| 41 | 258 | 270–276 |
| 42 | 265 | 277–283 |
| 43 | 272 | 284–290 |
| 44 | 278 | 291–297 |
| 45 | 285 | 298–304 |
| 46 | 292 | 305–311 |
| 47 | 298 | 312–318 |
| 48 | 305 | 319–325 |
| 49 | 312 | 326–332 |
| 50 | 318 | 333–339 |

**Regla de fit matching (ref → ENT_PROD_SCANNER):**
long_interna_calzado ≥ long_pie_mm + 10 mm
Mínimo aceptable: +7 mm · Óptimo: +12–15 mm

---

## CONVERSIÓN ENTRE SISTEMAS DE TALLAS

| EU | US Men | US Women | UK Men | UK Women | BR (referencia) |
|----|--------|----------|--------|----------|----------------|
| 35 | 3.5 | 5 | 2.5 | 3.5 | 33 |
| 36 | 4 | 5.5 | 3 | 4 | 34 |
| 37 | 4.5 | 6 | 3.5 | 4.5 | 35 |
| 38 | 5.5 | 7 | 4.5 | 5.5 | 36 |
| 39 | 6 | 7.5 | 5 | 6 | 37 |
| 40 | 7 | 8.5 | 6 | 7 | 38 |
| 41 | 7.5 | 9 | 6.5 | 7.5 | 39 |
| 42 | 8.5 | 10 | 7.5 | 8.5 | 40 |
| 43 | 9 | 10.5 | 8 | 9 | 41 |
| 44 | 10 | 11.5 | 9 | 10 | 42 |
| 45 | 10.5 | 12 | 9.5 | 10.5 | 43 |
| 46 | 11.5 | 13 | 10.5 | 11.5 | 44 |
| 47 | 12 | 13.5 | 11 | 12 | 45 |
| 48 | 13 | 14.5 | 12 | 13 | 46 |
| 49 | 13.5 | 15 | 12.5 | 13.5 | 47 |
| 50 | 14 | 15.5 | 13 | 14 | 48 |

Nota: conversión BR es aproximada. Verificar siempre con ficha técnica del fabricante.
Ref sistema de tallas MWT → ENT_OPS_TALLAS

---

## VALIDACIÓN CURVA DE DEMANDA RW [INTERNAL]

Curva existente en ENT_OPS_TALLAS: S1:5% · S2:10% · S3:20% · S4:25% · S5:30% · S6:10%

| SKU | Rango EU aprox. | Demanda RW | Población LATAM [EST] | Estado |
|-----|----------------|-----------|----------------------|--------|
| S1 | 35–36 | 5% | ~8% | Subrepresentado — aceptable para calzado industrial |
| S2 | 37–38 | 10% | ~18% | Subrepresentado — revisar para mercado femenino |
| S3 | 39–40 | 20% | ~22% | ✅ Alineado |
| S4 | 41–42 | 25% | ~22% | Ligeramente sobre — aceptable |
| S5 | 43–44 | 30% | ~18% | Sobre-representado vs LATAM — optimizado para USA |
| S6 | 45–47 | 10% | ~9% | ✅ Alineado |

Observación: la curva S5:30% está optimizada para USA (media EU 44). Para un canal 100% LATAM, S3 y S4 deberían pesar más que S5. [PENDIENTE — NO INVENTAR: validar con datos de venta reales cuando haya historial en CR y BR]

