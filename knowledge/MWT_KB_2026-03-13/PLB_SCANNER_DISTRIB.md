# PLB_SCANNER_DISTRIB
id: PLB_SCANNER_DISTRIB
version: 2.0
domain: COMERCIAL
status: DRAFT
visibility: [INTERNAL] excepto sección PRICING [CEO-ONLY]
stamp: DRAFT — pendiente aprobación CEO
fuente: Research sesión 2026-03-01

---

## OBJETIVO

Protocolo operativo de distribución del Rana Walk Pressure Scanner a zapaterías y distribuidores de calzado industrial. Define modelo comercial, criterios de selección de canal, protocolo de onboarding, KPIs de éxito y gestión de riesgos.

Ref hardware → ENT_PROD_SCANNER
Ref tallas → ENT_MERCADO_TALLAS

---

## LÓGICA DE VALOR — EL MECANISMO CENTRAL

El scanner no vende plantillas directamente. **Elimina la objeción de compra.** El cliente deja de decidir si necesita una plantilla y pasa a decidir cuál. La transición es de venta transaccional a venta consultiva con dato biomecánico que el cliente no puede rebatir.

### Tres capas de ingreso para MWT
1. **Hardware** — venta única del scanner al distribuidor
2. **Plantillas** — recurrente por consumo. Demanda pull desde punto de venta.
3. **Calzado Marluvas** — pull desde fit matching cuando catálogo del distribuidor no cubre la morfología del pie

### Efecto estratégico del módulo catálogo
Cuando el distribuidor carga su catálogo de calzado, el sistema puede recomendar Marluvas como alternativa cuando la morfología del pie calza mejor con la horma brasileña. El scanner se convierte en el sistema de prescripción del distribuidor con Rana Walk y Marluvas como marcas recomendadas por defecto cuando la biomecánica lo justifica.

---

## BENCHMARKS DE MERCADO [INTERNAL]

Datos de industria — no son proyecciones MWT confirmadas.

| Métrica | Sin scanner | Con scanner | Fuente |
|---------|------------|-------------|--------|
| Attach rate plantilla / calzado | 5–8% | 25–40% | Jalas FootStopService deployment data |
| Conversión scan→compra | — | 15–20% | BusinessPlanSuite fit-first retail |
| Reducción de devoluciones | baseline | 40–50% | Eclo + Fortune 2022 |
| AOV por cliente con fitting | $80–120 | $150–400 | Footwear retail KPI studies |

---

## CANALES DE DISTRIBUCIÓN

### Canal A — Zapatería retail

**Perfil ideal:**
- Tienda especializada en calzado de trabajo o deportivo
- 200–500 clientes / mes
- Staff de 2–5 personas con disposición a venta consultiva

**Modelo:** venta del scanner + reposición de plantillas mensual

**Proyección de impacto [EST — no confirmado]:**
Basado en benchmarks de industria (attach rate 25%, 150 scans/mes):
- Plantillas adicionales estimadas: ~37 unidades/mes
- Revenue adicional estimado: ~$1,110/mes
- Payback estimado del scanner: 2–4 semanas

[PENDIENTE — NO INVENTAR: validar con datos reales del primer piloto antes de usar estas proyecciones en propuestas comerciales]

### Canal B — Distribuidor de calzado industrial / EPP

**Perfil ideal:**
- Acceso a cuentas corporativas de 100–500 trabajadores
- Ya vende EPP o calzado de seguridad como línea principal
- Hace visitas de campo (no solo despacho)

**Modelo:** scanner como herramienta de campo para visitas corporativas

**Proyección de impacto [EST — no confirmado]:**
Basado en benchmarks (attach rate 35%, 200 scans/mes en campo):
- Plantillas adicionales estimadas: ~70 unidades/mes
- Revenue adicional estimado: ~$1,680/mes
- Payback estimado del scanner: 1–2 semanas en cuenta corporativa grande

[PENDIENTE — NO INVENTAR: validar con primer distribuidor B antes de escalar]

---

## MERCADO DIRECCIONABLE [EST] [INTERNAL]

Estimaciones de research. No son proyecciones confirmadas.

| Segmento | Puntos de venta est. LATAM | Penetración realista Y1 | Plantillas/mes est. c/u |
|---------|---------------------------|------------------------|------------------------|
| Zapaterías calzado trabajo | 8,000 | 2% = 160 | 35 |
| Distribuidores EPP industrial | 1,200 | 5% = 60 | 250 |
| **Total Y1** | | **220 puntos** | — |

Impacto total estimado Y1: ~247,200 unidades adicionales de plantilla
A $8–12 margen neto/unidad [CEO-ONLY]: ~$2.0–3.0M USD impacto en línea plantillas

[PENDIENTE — NO INVENTAR: estos números son estimaciones de research. Validar con piloto antes de usar en proyecciones financieras oficiales]

---

## CRITERIOS DE SELECCIÓN — EARLY ADOPTERS

El mayor riesgo del modelo no es tecnológico sino conductual. El distribuidor EPP tradicional es transaccional. Seleccionar early adopters con criterios estrictos:

| Criterio | Indicador positivo | Indicador de riesgo |
|---------|-------------------|---------------------|
| Enfoque consultivo | Ya hace visitas de asesoría, no solo despacho | Solo recibe pedidos |
| Incentivo en plantillas | Ya vende plantillas o accesorios EPP | Plantilla = producto ajeno |
| Cuenta corporativa | Tiene cuentas de 100+ trabajadores | Solo retail individual |
| Disponibilidad para capacitación | Compromete 2 horas sin resistencia | "No tengo tiempo" |
| Apertura tecnológica | Usa alguna herramienta digital de ventas | Solo catálogo físico |

**Regla:** si un distribuidor falla 3 o más criterios no es early adopter. Esperar a la segunda ola de adopción cuando haya casos de éxito que mostrar.

---

## PROTOCOLO DE ONBOARDING — 4 FASES

### Fase 1 — Demo (30 min)
1. CEO o vendedor MWT hace scan en vivo al comprador del distribuidor
2. Muestra output: mapa de calor bilateral + recomendación de plantilla + fit de calzado
3. Muestra ROI: "Tus primeras 12 ventas adicionales de plantilla pagan el scanner"
4. **Gate:** si el comprador no pregunta por el precio del scanner en esta sesión, la demo no funcionó — no continuar

### Fase 2 — Carga de catálogo (1–2 horas)
1. Distribuidor entrega CSV o lista de modelos con tallas y dimensiones internas
2. MWT carga el catálogo en MWT.ONE (puede ser self-service con asistencia remota)
3. Verificación: el sistema recomienda correctamente para 3 casos de prueba reales
4. **Gate:** si el distribuidor no puede proveer dimensiones internas de su calzado, el fit matching no funciona — documentar qué modelos quedan sin datos → [PENDIENTE]

### Fase 3 — Capacitación del vendedor (30 min)
1. Script de venta: cómo presentar el scan al cliente final
2. Frase clave: *"Vamos a medir tu pie para ver qué modelo te calza mejor y si necesitás apoyo biomecánico"*
3. Práctica: 3 scans en vivo con retroalimentación en tiempo real
4. **Gate:** el vendedor debe completar un scan sin asistencia antes de terminar la sesión

### Fase 4 — Seguimiento semana 2
1. Revisión de attach rate real en las primeras 2 semanas
2. Si attach rate < 15%: ajustar script de venta antes de declarar fracaso
3. Si attach rate ≥ 20%: caso de éxito — documentar métricas para propuesta al siguiente distribuidor
4. Si attach rate = 0%: el scanner no se está usando — visita de campo urgente

---

## KPIs DE ÉXITO

| KPI | Umbral mínimo | Umbral objetivo | Cuándo medir |
|-----|--------------|----------------|-------------|
| Attach rate plantilla / scan | 15% | 25–35% | Semana 2 y 4 |
| Scans / mes | 50 | 150+ | Mes 1 |
| Payback del hardware | < 8 semanas | < 4 semanas | Mes 2 |
| Reorden plantillas | Mes 2 | Mes 1 | — |
| Distribuidores activos (usan > 20 scans/mes) | — | 80% del piloto | Mes 3 |

**KPI crítico:** el attach rate en las primeras 4 semanas determina si el modelo funciona. No esperar 3 meses para evaluar.

---

## MODELO DE PRECIOS AL CANAL [CEO-ONLY]

[PENDIENTE — NO INVENTAR: precios confirmados al canal pendientes de cotización OEM real]

Referencia de estimaciones → ENT_PROD_SCANNER (sección PRICING [CEO-ONLY])

Nota: el precio de la sesión de escaneo al consumidor final se recomienda como gratuito en fase de adopción. El scan es el gancho — la plantilla es la conversión.

---

## GESTIÓN DE RIESGOS

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|-----------|
| OEM sin protocolo abierto | Media | Crítico | Gate AC-02: no comprar hasta que ingeniero MWT valide SDK |
| Distribuidor no cambia conducta de venta | Alta (30–40%) | Alto | Selección estricta de early adopters por 5 criterios |
| Attach rate real < 15% | Media | Alto | Ajustar script antes de declarar fracaso. Medir semana 1. |
| Distribuidor no tiene dim. internas de calzado | Alta | Medio | Fit matching parcial — funciona con plantilla sola sin cruce de calzado |
| Competidor copia el modelo | Baja Y1 | Medio | Ventaja de primero en mercado + base de catálogos cargados = barrera de datos |
| Hardware OEM insuficiente | Media | Alto | Gate AC-02 obligatorio antes de cualquier orden de producción |

