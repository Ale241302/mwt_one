# LOTE_SM_SPRINT13 — CostLine v2 + Caso 2391 Learnings
id: LOTE_SM_SPRINT13
status: DRAFT — corregido post-auditoría, pendiente aprobación CEO
stamp: DRAFT — 2026-03-19
visibility: INTERNAL
domain: Plataforma (IDX_PLATAFORMA)
version: 1.2
sprint: 13
priority: P0
agente_principal: AG-02 Backend (Alejandro)
depends_on: LOTE_SM_SPRINT12 (actualmente DRAFT v2.1 — gating: Sprint 13 no inicia implementación en código hasta Sprint 12 DONE)
refs: ENT_OPS_CASO_2391 (VIGENTE v1.0), ENT_OPS_STATE_MACHINE (FROZEN v1.2.2), LOTE_SM_SPRINT12 (DRAFT v2.1)

---

## Objetivo Sprint 13

Incorporar los aprendizajes del primer expediente real (PF 2391-2025) al modelo de datos y lógica de negocio. CostLine pasa de registro plano a registro inteligente (categoría, comportamiento, multi-moneda). Se agrega validación de viabilidad Modelo C y artefactos faltantes.

**Fuente:** ENT_OPS_CASO_2391 (9 hallazgos priorizados del caso real PF 2391-2025 / PO 504649 / Sondel)

**Cobertura:** 8 de 9 hallazgos. H4 (Sondel completado) ya HECHO en ENT_PLAT_LEGAL_ENTITY v1.1. H6+H9 consolidados en S13-07 (misma zona del modelo: ENT_OPS_EXPEDIENTE).

**Reasignación scope:** CEO-26 (ENT_GOB_PENDIENTES) pedía evaluar hallazgos para Sprint 11. Se asignan a Sprint 13 porque: (a) Sprint 11 está en formulación con scope propio, (b) Sprint 12 es prerequisito técnico (refactorización services/financial.py donde vive CostLine), (c) los hallazgos requieren Sprint 12 DONE para implementarse sin conflicto. CEO-26 se marca como EVALUADO → Sprint 13 al materializar.

---

## Nota operativa — FROZEN compliance

**ENT_OPS_STATE_MACHINE v1.2.2 es FROZEN.** Ningún item de este sprint modifica ese archivo. Todos los cambios se implementan como:
1. Delta spec en este LOTE (define qué cambia)
2. Código derivado en `backend/apps/expedientes/` (implementa el cambio)
3. Migraciones Django (altera el schema de BD)

Las referencias a "F2", "C4", "C15", "T4" son coordenadas de lectura en la spec FROZEN, no instrucciones de edición.

---

## Items (8)

### FASE 0 — Datos correctivos (KB + config, P0)

#### Item S13-01: Corregir arancel y reestructurar ENT_COMERCIAL_COSTOS
- **Agente:** CEO (decisión de datos) + AG-01 Architect (estructura)
- **Hallazgo:** H1 — DAI 0% → 14% para partida 6403.99.90
- **Qué hacer:**
  1. Reestructurar ENT_COMERCIAL_COSTOS por partida arancelaria
  2. Partida 6403.99.90 (calzado seguridad, suela plástico, parte superior cuero/microfibra): DAI 14%, IVA 13%, fuente DUA 005-2026-179055
  3. Partida 6406.90.90 (plantillas): DAI [PENDIENTE — NO INVENTAR], IVA 13%
  4. Crear lookup table para validación automática de S13-05
  5. Marcar CEO-25 como DONE en ENT_GOB_PENDIENTES
- **Archivo KB a modificar:** ENT_COMERCIAL_COSTOS
- **Prioridad:** P0 — dato incorrecto en producción. S13-05 (validación viabilidad) depende de este lookup.
- **Criterio de done:**
  - [ ] ENT_COMERCIAL_COSTOS reestructurado por partida arancelaria
  - [ ] DAI 14% para 6403.99.90 con fuente documental
  - [ ] Datos ausentes marcados [PENDIENTE — NO INVENTAR]
  - [ ] CEO-25 marcado DONE

---

### FASE 1 — Modelo de datos CostLine v2 (backend, P0)

**Nota de priorización:** H3 (cost_behavior, fuente MEDIA) y H5 (artefactos faltantes, fuente MEDIA) escalan a P0 en Sprint 13 por: (a) costo marginal mínimo — S13-03 es un campo nullable adicional en la misma migración que S13-02, (b) coherencia de release — los 3 campos de CostLine v2 se despliegan juntos, y (c) S13-06/H5 (artefactos) habilita trazabilidad para el siguiente expediente real.

#### Item S13-02: Agregar cost_category a CostLine
- **Agente:** AG-02 Backend
- **Hallazgo:** H2 — IVA no es costo
- **Command ref (lectura):** ENT_OPS_STATE_MACHINE F2 (CostLine model), C15 (RegisterCostLine)
- **Archivos a tocar:** `backend/apps/expedientes/models.py` (CostLine model), `backend/apps/expedientes/services/financial.py` (C15 RegisterCostLine)
- **Archivos prohibidos:** ENT_OPS_STATE_MACHINE.md
- **Qué hacer:**
  1. Agregar campo al modelo CostLine:
     ```python
     class CostCategory(models.TextChoices):
         LANDED_COST = 'landed_cost', 'Landed Cost'
         TAX_CREDIT = 'tax_credit', 'Tax Credit (recuperable)'
         RECOVERABLE = 'recoverable', 'Recoverable (otro)'
         NON_DEDUCTIBLE = 'non_deductible', 'Non-Deductible'
     
     cost_category = models.CharField(
         max_length=20,
         choices=CostCategory.choices,
         default=CostCategory.LANDED_COST,  # backwards compat
     )
     ```
  2. Actualizar C15 RegisterCostLine para aceptar cost_category en input
  3. Regla de negocio: dashboard/financial-summary calcula margen solo sobre `landed_cost`. `tax_credit` se muestra separado.
  4. **Migración:** additive, default='landed_cost' para rows existentes (backwards compat). No backfill destructivo.
- **Criterio de done:**
  - [ ] Campo cost_category en CostLine model con enum TextChoices
  - [ ] Migración generada, default='landed_cost'
  - [ ] C15 RegisterCostLine acepta cost_category (opcional, default landed_cost)
  - [ ] financial-summary endpoint filtra por landed_cost para cálculo de margen
  - [ ] Rows existentes no se rompen (default applied)
  - [ ] Tests: crear CostLine con cada categoría, verificar que financial-summary excluye tax_credit

#### Item S13-03: Agregar cost_behavior a CostLine
- **Agente:** AG-02 Backend
- **Hallazgo:** H3 — Fijo vs variable
- **Command ref (lectura):** ENT_OPS_STATE_MACHINE F2
- **Archivos a tocar:** `backend/apps/expedientes/models.py`, `backend/apps/expedientes/services/financial.py`
- **Archivos prohibidos:** ENT_OPS_STATE_MACHINE.md
- **Qué hacer:**
  1. Agregar campo:
     ```python
     class CostBehavior(models.TextChoices):
         FIXED_PER_OPERATION = 'fixed_per_operation', 'Fixed per Operation'
         VARIABLE_PER_UNIT = 'variable_per_unit', 'Variable per Unit'
         VARIABLE_PER_WEIGHT = 'variable_per_weight', 'Variable per Weight'
         SEMI_VARIABLE = 'semi_variable', 'Semi-Variable'
     
     cost_behavior = models.CharField(
         max_length=25,
         choices=CostBehavior.choices,
         null=True,
         blank=True,  # opcional — no todos los costos tienen clasificación inicial
     )
     ```
  2. C15 acepta cost_behavior (opcional)
  3. **Migración:** additive, nullable. No requiere backfill.
- **Criterio de done:**
  - [ ] Campo cost_behavior en CostLine model
  - [ ] Migración generada, nullable
  - [ ] C15 acepta cost_behavior opcional
  - [ ] Tests: crear CostLine con/sin cost_behavior

#### Item S13-04: Agregar multi-moneda a CostLine
- **Agente:** AG-02 Backend
- **Hallazgo:** H8 — Tipo de cambio y equivalente en moneda base
- **Command ref (lectura):** ENT_OPS_STATE_MACHINE F2
- **Archivos a tocar:** `backend/apps/expedientes/models.py`, `backend/apps/expedientes/services/financial.py`
- **Archivos prohibidos:** ENT_OPS_STATE_MACHINE.md
- **Qué hacer:**
  1. Agregar campos:
     ```python
     exchange_rate = models.DecimalField(
         max_digits=12, decimal_places=6,
         null=True, blank=True,
         help_text="TC original→base al momento del registro"
     )
     amount_base_currency = models.DecimalField(
         max_digits=12, decimal_places=2,
         null=True, blank=True,
         help_text="Monto equivalente en base_currency"
     )
     base_currency = models.CharField(
         max_length=3, default='USD',
         help_text="Moneda base del expediente"
     )
     ```
  2. **Contrato técnico multi-moneda:**
     - `currency` = moneda original del costo (existente: BRL, CRC, USD)
     - `amount` = monto en moneda original (existente)
     - `exchange_rate` = TC de `currency` → `base_currency` al momento del registro. Dirección: 1 unidad de currency = X base_currency (ej: 1 BRL = 0.18 USD)
     - `amount_base_currency` = `amount × exchange_rate`. Calculado en C15 si exchange_rate proporcionado.
     - Si `currency == base_currency`: `exchange_rate = 1.0`, `amount_base_currency = amount` (auto-fill)
     - Si `exchange_rate is null` y `currency != base_currency`: `amount_base_currency` queda null → dashboard muestra warning "TC pendiente"
     - Precisión: 6 decimales para exchange_rate (cubre CRC/USD ~0.001936), 2 decimales para amounts
     - Fuente del TC: usuario lo ingresa manualmente al registrar costo. No hay API de TC en MVP.
     - Momento del snapshot: TC vigente al momento de registro del costo (no al momento de pago)
  3. **Migración:** additive, todos nullable excepto base_currency (default='USD')
  4. **Legacy rows:** exchange_rate=null, amount_base_currency=null. Dashboard los muestra con flag "pre-v2". No backfill automático — CEO decide si reclasificar manualmente.
- **Criterio de done:**
  - [ ] 3 campos nuevos en CostLine model
  - [ ] Migración generada, nullable + default USD
  - [ ] C15 calcula amount_base_currency automáticamente si exchange_rate provided
  - [ ] C15 auto-fills exchange_rate=1.0 si currency==base_currency
  - [ ] financial-summary usa amount_base_currency cuando disponible, amount cuando no
  - [ ] Tests: CostLine en USD (auto-fill), en BRL (con TC), en CRC (con TC), sin TC (null warning)
  - [ ] Legacy rows no se rompen

---

### FASE 2 — Lógica de negocio (backend, P0)

#### Item S13-05: Validación de viabilidad Modelo C en C4
- **Agente:** AG-02 Backend
- **Hallazgo:** H7 — Sistema no valida viabilidad financiera
- **Dependencia:** S13-01 DONE (lookup arancelario correcto necesario para cálculo)
- **Command ref (lectura):** ENT_OPS_STATE_MACHINE C4 (DecideModeBC), ENT_COMERCIAL_MODELOS.C
- **Archivos a tocar:** `backend/apps/expedientes/services/commands_registro.py` (C4 DecideModeBC)
- **Archivos prohibidos:** ENT_OPS_STATE_MACHINE.md
- **Qué hacer:**
  1. Agregar pre-check en C4 cuando `mode=FULL`:
     ```python
     def pre_check_viability(expediente, mode, fob_mwt, fob_cliente, qty):
         """WARNING advisory — no bloquea, solo informa."""
         if mode != 'FULL':
             return None
         
         partida = expediente.partida_arancelaria  # o lookup por producto
         dai_pct = get_dai_rate(partida, expediente.destination_country)  # lookup table S13-01
         iva_pct = get_iva_rate(expediente.destination_country)
         
         # Costos fijos estimados: promedio últimas 5 ops o default config
         fixed_costs_per_unit = get_estimated_fixed_costs(qty)
         
         costo_landed_est = fob_mwt * (1 + FLETE_PCT) * (1 + dai_pct) + fixed_costs_per_unit
         # Nota: IVA no suma al costo (es tax_credit, ref H2)
         
         if costo_landed_est > fob_cliente:
             delta = costo_landed_est - fob_cliente
             return {
                 'warning': True,
                 'message': f'Modelo C genera pérdida estimada de ${delta:.2f}/par',
                 'costo_landed_est': costo_landed_est,
                 'fob_cliente': fob_cliente,
                 'delta_per_unit': delta,
             }
         return None
     ```
  2. **Comportamiento:** WARNING advisory, no blocking. CEO ve el warning y decide si confirmar. El sistema registra `viability_check_result` en event_log.
  3. **Si lookup arancelario no existe para la partida:** warning "DAI desconocido — cálculo de viabilidad no disponible" en vez de inventar tasa.
  4. **Fallback degradado general:** Si falta cualquier input crítico (FLETE_PCT no configurado, get_estimated_fixed_costs sin baseline, lookup arancelario ausente), no calcular costo_landed_est. Devolver warning "config incompleta — cálculo de viabilidad no disponible" con lista de inputs faltantes. Nunca calcular con datos parciales.
  5. **FLETE_PCT:** config parameter, default [PENDIENTE — NO INVENTAR, CEO debe definir estimado inicial]
- **Criterio de done:**
  - [ ] Pre-check ejecuta en C4 si mode=FULL
  - [ ] Warning retornado en response body (no bloquea transición)
  - [ ] Lookup arancelario usado (de S13-01)
  - [ ] Si lookup no existe: warning alternativo, no fallo
  - [ ] Event log registra resultado del check
  - [ ] Tests: mode=FULL rentable (no warning), mode=FULL pérdida (warning), mode=FULL sin lookup (warning degradado), mode=B (skip check)

#### Item S13-06: Agregar artefactos faltantes ART-13 y ART-14
- **Agente:** AG-02 Backend + AG-01 Architect (KB)
- **Hallazgo:** H5 — Faltan Certificado de Origen y DU-E
- **Command ref (lectura):** ENT_OPS_STATE_MACHINE T4 (transición DESPACHO), E (catálogo artefactos)
- **Qué hacer:**
  1. **KB:** Agregar a ARTIFACT_REGISTRY:
     - ART-13: Certificado de Origen (CO)
       - category: document
       - status: DRAFT
       - emitter: FIEMG/ICC Brasil (externo)
       - obligatorio_si: `dispatch_mode=mwt AND origin_country=BR`
       - transición: precondición T4 (ApproveDispatch) cuando aplica
       - owner: AG-02 Backend
     - ART-14: DU-E Exportación Brasil
       - category: document
       - status: DRAFT
       - emitter: RFB Brasil (externo — sistema Siscomex)
       - obligatorio_si: `origin_country=BR` (toda exportación desde Brasil)
       - transición: evidence-only, se registra en expediente pero no bloquea transición. Motivo: DU-E la emite el exportador (Marluvas), MWT la recibe como referencia fiscal.
       - owner: AG-02 Backend
  2. **Código:** Agregar ART-13 y ART-14 como ArtifactType choices. ART-13 como precondición soft en T4 (warning si falta, no blocking en MVP).
  3. **Campo adicional en expediente:** `external_fiscal_refs: JSONField(default=list)` para DANFE, Carta de Corrección, DU-E — referencias fiscales externas que no son artefactos MWT pero se vinculan al expediente.
- **Criterio de done:**
  - [ ] ARTIFACT_REGISTRY actualizado con ART-13 y ART-14
  - [ ] ArtifactType choices actualizados en modelo
  - [ ] ART-13 como precondición soft en T4 (si dispatch_mode=mwt y origin=BR)
  - [ ] ART-14 registrable como evidence
  - [ ] external_fiscal_refs field en Expediente model
  - [ ] Tests: crear ART-13 y ART-14, verificar precondición T4, verificar external_fiscal_refs

---

### FASE 3 — Datos y calibración (KB + backend, P1)

#### Item S13-07: Baseline tiempos y aforo en expediente
- **Agente:** AG-02 Backend + AG-01 Architect (KB)
- **Hallazgos consolidados:** H6 (baseline tiempos) + H9 (aforo aduanero). Se consolidan porque ambos modifican ENT_OPS_EXPEDIENTE y representan campos de calibración/observación, no lógica de negocio.
- **Qué hacer:**
  1. Agregar campos al modelo Expediente:
     ```python
     aforo_type = models.CharField(
         max_length=10,
         choices=[('verde', 'Verde'), ('amarillo', 'Amarillo'), ('rojo', 'Rojo')],
         null=True, blank=True,
     )
     aforo_date = models.DateField(null=True, blank=True)
     ```
  2. **KB:** Registrar en ENT_OPS_EXPEDIENTE.F4 los tiempos de PF 2391-2025 como primer datapoint:
     - Registro: 3 días, Producción MTO: 60 días, Preparación/Despacho BR: 27 días, Tránsito VCP→SJO: 2 días, Aduana CR: 8 días. Total: 100 días.
     - Condiciones: Marluvas, 75BPR29, aéreo, VCP-BOG-SJO, aduana Santamaría, aforo rojo.
     - **Regla R1:** Solo registrar tiempos con fuente documental. Timestamps sin fuente = [PENDIENTE — NO INVENTAR].
  3. **Migración:** additive, nullable.
- **Excluido de S13-07 (diferido a Sprint 14+):** Parametrización de credit_clock por product_family. Es hipótesis derivada del insight (producción MTO = 60 días), no learning directo del caso. Requiere más datapoints para ser útil.
- **Criterio de done:**
  - [ ] aforo_type y aforo_date en Expediente model
  - [ ] Migración generada
  - [ ] ENT_OPS_EXPEDIENTE.F4 actualizado con primer datapoint (fuentes documentales citadas)
  - [ ] Timestamps sin fuente marcados [PENDIENTE — NO INVENTAR]
  - [ ] Tests: crear expediente con/sin aforo

#### Item S13-08: Tests Sprint 13
- **Agente:** AG-02 Backend
- **Dependencia:** Items S13-01 a S13-07

**CostLine v2 (S13-02/03/04):**
- [ ] cost_category: crear CostLine por cada categoría, verificar financial-summary solo suma landed_cost
- [ ] cost_behavior: crear CostLine con/sin behavior, verificar nullable
- [ ] Multi-moneda: CostLine en USD (auto-fill TC=1.0), BRL con TC, CRC con TC, sin TC (null)
- [ ] Legacy compat: CostLine existentes (pre-v2) funcionan con defaults, no rompen dashboard
- [ ] Migration test: migración forward/backward sin data loss

**Viabilidad Modelo C (S13-05):**
- [ ] mode=FULL rentable → no warning
- [ ] mode=FULL pérdida → warning con delta correcto
- [ ] mode=FULL sin lookup arancelario → warning degradado "config incompleta"
- [ ] mode=FULL sin FLETE_PCT configurado → warning degradado "config incompleta" con FLETE_PCT en lista de inputs faltantes
- [ ] mode=FULL sin baseline costos fijos (get_estimated_fixed_costs sin data) → warning degradado con fixed_costs en lista de inputs faltantes
- [ ] mode=B → skip check
- [ ] Event log registra viability_check_result

**Artefactos (S13-06):**
- [ ] ART-13 registrable y precondición soft en T4 (dispatch_mode=mwt, origin=BR)
- [ ] ART-14 registrable como evidence (no blocking)
- [ ] external_fiscal_refs acepta lista de refs

**Expediente (S13-07):**
- [ ] aforo_type y aforo_date nullable y funcionales
- [ ] Admin muestra campos nuevos

**Regresión:**
- [ ] Los 22 commands C1-C22 siguen funcionando post-migración
- [ ] financial-summary endpoint retorna mismos resultados para datos pre-v2
- [ ] Tests de state machine pasan sin modificación

---

## Dependencias internas

```
S13-01 (arancel/lookup) ──────────── Fase 0 — KB data
    │
    ├── S13-02 (cost_category) ──┐
    ├── S13-03 (cost_behavior) ──┤── Fase 1 — independientes entre sí
    ├── S13-04 (multi-moneda) ───┘
    │
    └── S13-05 (viabilidad) ─────── Fase 2 — depende de S13-01 (lookup)
                                              + puede correr paralelo a Fase 1
    
    S13-06 (artefactos) ────────── Fase 2 — independiente
    S13-07 (baseline + aforo) ──── Fase 3 — independiente

    S13-08 (tests) ─────────────── después de todo
```

**Dependencia funcional crítica:** S13-05 (validación viabilidad) requiere S13-01 (lookup arancelario) DONE. Sin el lookup correcto, la validación calcula con datos falsos. Si S13-01 se retrasa, S13-05 puede implementarse con warning degradado ("DAI desconocido") y activarse cuando el lookup exista.

---

## Gating Sprint 12 → Sprint 13

Sprint 13 depende de Sprint 12 DONE porque:
- S13-02/03/04 modifican CostLine model. Sprint 12 (S12-01) refactoriza services.py → services/financial.py donde vive C15 RegisterCostLine. Modificar CostLine sobre código no refactorizado crea conflictos de merge.
- S13-05 modifica C4 DecideModeBC. Sprint 12 (S12-01) mueve C4 a services/commands_registro.py.
- S13-06 agrega artefactos. Sprint 12 (S12-04) documenta API con drf-spectacular — los nuevos artefactos deben aparecer en docs.

**Regla de gating:** Si Sprint 12 no está DONE cuando Sprint 13 requiere iniciar, solo se permite:
- Preparación de delta spec (este documento)
- S13-01 (corrección KB — no depende de código)
- S13-07 parcial (campos KB de ENT_OPS_EXPEDIENTE — no depende de código)

La implementación en código (S13-02 a S13-06) NO inicia hasta Sprint 12 DONE.

**Carry-over:** Si Sprint 12 tiene items incompletos que afecten services/financial.py o services/commands_registro.py, Sprint 13 absorbe la finalización como pre-requisito antes de Fase 1. No como Fase 0 separada — se resuelve dentro de la dependencia del item afectado.

---

## Impacto KB / Gobernanza (R5)

Al materializar y cerrar Sprint 13, actualizar:

| Archivo | Cambio |
|---------|--------|
| ENT_COMERCIAL_COSTOS | Reestructurado por partida arancelaria (S13-01) |
| ARTIFACT_REGISTRY | +ART-13 (CO), +ART-14 (DU-E) (S13-06) |
| ENT_OPS_EXPEDIENTE | +aforo_type, +aforo_date, +F4 baseline (S13-07) |
| ENT_GOB_PENDIENTES | CEO-25 DONE, CEO-26 EVALUADO → Sprint 13 |
| DEPENDENCY_GRAPH | +S13 dependencias si aplica |
| RW_ROOT | Version bump |
| MANIFIESTO_APPEND_[fecha] | Registro de cambios sesión |

---

## Criterio Sprint 13 DONE

### Obligatorio
1. ENT_COMERCIAL_COSTOS reestructurado con DAI correcto por partida
2. CostLine v2: cost_category, cost_behavior, multi-moneda — 3 campos nuevos funcionales
3. C15 RegisterCostLine acepta los 3 campos nuevos
4. financial-summary calcula margen solo sobre landed_cost
5. Validación viabilidad Modelo C en C4 (warning advisory)
6. ART-13 y ART-14 en ARTIFACT_REGISTRY + modelo
7. Tests pasan (CostLine v2, viabilidad, artefactos, regresión)
8. Sin regresiones sobre baseline implementado vigente (Sprints 0-9.1 + componentes materializados de Sprint 10/11/12 al momento de ejecución)

### Deseable
9. aforo_type/aforo_date en expediente
10. F4 baseline con primer datapoint documentado
11. external_fiscal_refs field funcional

---

## Migration plan

**Estrategia:** Todas las migraciones son additive (nuevos campos, nullable o con default). No hay ALTER destructivo ni rename.

| Campo | Default/Nullable | Legacy rows |
|-------|-----------------|-------------|
| cost_category | default='landed_cost' | Todos marcados landed_cost (correcto para pre-v2) |
| cost_behavior | null=True | Quedan null (sin clasificación) |
| exchange_rate | null=True | Quedan null |
| amount_base_currency | null=True | Quedan null — dashboard muestra flag "pre-v2" |
| base_currency | default='USD' | Todos USD (correcto — MVP es single-currency) |
| aforo_type | null=True | Quedan null |
| aforo_date | null=True | Quedan null |
| external_fiscal_refs | default=list | Lista vacía |

**Rollback:** Cada migración es reversible (RemoveField). Si Sprint 13 falla, `migrate expedientes [sprint12_last_migration]` revierte todos los campos.

**Test de migración:** Correr migración sobre snapshot de BD con datos reales de PF 2391-2025 (si existe en staging). Verificar que datos pre-existentes no se corrompen.

---

## Retrospectiva
(Completar al cerrar el sprint)

---

Stamp: DRAFT — 2026-03-19. Auditoría triangulada R1 8.4 → R2 9.3 → R3 9.6 (PN1 aplicado). Pendiente aprobación CEO.

Changelog:
- v0.1 (2026-03-19): SEED inicial — 7 items, mapeo H1-H9
- v1.0 (2026-03-19): Post-auditoría R1. 12 fixes aplicados: +id header, +stamp en header, +nota FROZEN compliance, S13-01 (H1/arancel) subido a P0 como Fase 0, ART-19/20 renumerados a ART-13/14, +spec ART-14 (evidence-only), +contrato multi-moneda (dirección FX, precision, nullable, legacy), credit_clock por product_family diferido a Sprint 14+, +R1 guard en timestamps, +sección Impacto KB/Gobernanza, +migration plan con rollback, +dependencia funcional S13-05↔S13-01, gating formalizado.
- v1.1 (2026-03-19): Post-auditoría R2 (9.3/10). 4 fixes: depends_on metadata corregido (no afirma DONE cuando S12 es DRAFT), fallback degradado completo en S13-05, criterio regresión auditable, nota racionalización prioridad H3/H5→P0, changelog S13-06→S13-01 corregido.
- v1.2 (2026-03-19): Post-auditoría R3 (9.6/10). 1 fix (PN1): +2 tests en S13-08 para fallback degradado (FLETE_PCT no configurado, baseline costos fijos sin data).
