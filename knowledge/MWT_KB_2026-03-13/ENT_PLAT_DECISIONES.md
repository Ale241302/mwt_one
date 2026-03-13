# ENT_PLAT_DECISIONES — Registro de Decisiones de Diseño

status: VIGENTE
visibility: INTERNAL
version: 1.0
stamp: VIGENTE — 2026-03-13
domain: Plataforma (IDX_PLATAFORMA)
classification: ENTITY — Decisiones de diseño del sistema, referenciables por ID

---

## Propósito

Registro canónico de decisiones de diseño tomadas durante el desarrollo de la plataforma MWT. Cada decisión tiene un ID único y es referenciable desde cualquier documento del sistema.

Convención de IDs:
- `AUT-D{N}` — decisiones de automatizaciones (ref → ENT_PLAT_AUTOMATIONS)
- Nuevos prefijos se agregan cuando surja un dominio de decisiones distinto

---

## Decisiones de automatización (AUT-D)

| ID | Decisión | Contexto | Fecha | Origen |
|----|----------|----------|-------|--------|
| AUT-D3 | Prophet no activo en Fase F1. Solo SMA (Simple Moving Average) para forecast. | Complejidad innecesaria con <12 meses de historial y 1 producto. Se activa en F2. | 2026-03-13 | Sesión Swarm — ENT_OPS_DEMAND_PLANNING.F7 |
| AUT-D9 | Cálculo de restock agregado por familia (caja master con curva fija), no por SKU individual. | MOQ de Marluvas es por caja master con distribución de tallas fija. Calcular por SKU generaría órdenes incompatibles con el empaque real. | 2026-03-13 | Sesión Swarm — ENT_OPS_DEMAND_PLANNING.F7 |
| AUT-D10 | MOQ siempre desde product_master. Si NULL → skip SKU + alerta CEO. Nunca hardcoded. | Evitar valores magic number en código. Si falta dato, la automatización no asume — escala. | 2026-03-13 | Sesión Swarm — ENT_OPS_DEMAND_PLANNING.F7 |
| AUT-D11 | Velocity excluye días OOS (in_stock=false) del cálculo. | Días sin stock no representan demanda real. Incluirlos subestimaría velocity y generaría restock insuficiente. | 2026-03-13 | Sesión Swarm — ENT_OPS_DEMAND_PLANNING.F7 |

---

## Pendientes

| ID | Decisión pendiente | Trigger |
|----|-------------------|---------|
| [PENDIENTE] | Decisiones AUT-D1, AUT-D2, AUT-D4–D8 no documentadas | Revisar sesiones anteriores de diseño de automatizaciones |

---

## Reglas de este registro

1. Toda decisión de diseño que se referencia desde otro documento DEBE tener entrada aquí.
2. Si se toma una decisión y se referencia como `AUT-D{N}`, el ID se registra en este archivo en el mismo batch.
3. Una decisión documentada aquí no se repite en el documento que la consume — el consumidor usa `ref → ENT_PLAT_DECISIONES.AUT-D{N}`.
4. Decisiones pueden revertirse: se marca la original como REVOCADA y se crea una nueva con el razonamiento.

---

Changelog:
- v0.x: stub vacío (contenido pendiente)
- v1.0 (2026-03-13): Poblado con AUT-D3, AUT-D9, AUT-D10, AUT-D11 desde Sesión Swarm. Reglas de registro definidas.
