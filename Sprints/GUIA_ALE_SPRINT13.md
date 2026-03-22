# GUÍA ALEJANDRO — Sprint 13: CostLine v2 + Caso 2391
## Para: Alejandro (AG-02 Backend) · Fecha: 2026-03-19

---

## Qué es este sprint

El primer expediente real (PF 2391-2025, Marluvas → Sondel, 80 pares) nos enseñó 9 cosas que el sistema no sabía hacer. Este sprint implementa las 7 más importantes. En resumen: le estamos enseñando al sistema a entender costos de verdad.

---

## Contexto del caso real (para que entiendas el "por qué")

Importamos 80 pares de calzado de seguridad Marluvas desde Brasil a Costa Rica. El expediente PF 2391-2025 reveló que:

1. **El IVA no es costo** — $678 de IVA que pagamos en aduana es crédito fiscal recuperable. Si lo registramos como costo, el margen calculado está inflado en $8.48/par. El sistema necesita saber qué es costo real y qué es crédito fiscal.

2. **Hay costos fijos y variables** — Los $479 de servicios de internación (almacén, agencia, transporte) son fijos por operación. A 80 pares cuestan $5.99/par. A 500 pares serían $0.96/par. El sistema necesita clasificar esto para poder simular escala.

3. **Tres monedas diferentes** — USD, BRL (Real brasileño) y CRC (Colón). Con tipos de cambio que varían entre documentos (DUA ₡473.47 vs TSM ₡469.94). Sin registrar el TC, no podemos recalcular ni auditar.

4. **El arancel estaba mal en la KB** — Decía 0%, la realidad es 14%. Esto significa que toda simulación de Modelo C producía márgenes falsos.

5. **Faltan documentos en el registro** — El Certificado de Origen y la DU-E (exportación Brasil) no estaban como artefactos del sistema.

6. **El sistema no valida si Modelo C es viable** — En este caso, si vendíamos al precio de Sondel ($47.74/par), perdíamos $5.78/par. El CEO lo sabe intuitivamente pero el sistema no lo calculaba.

---

## Prerequisito

Sprint 12 DONE. Necesitás que `services.py` ya esté dividido en `services/` directory (especialmente `services/financial.py` y `services/commands_registro.py`). Si Sprint 12 no está terminado, solo podés trabajar en S13-07 (aforo — es independiente).

---

## Qué vas a implementar (8 items, en orden)

### Fase 1 — Tres campos nuevos en CostLine (models.py + financial.py)

Estos tres van juntos. Idealmente una sola migración.

**S13-02: cost_category**
- Nuevo enum `CostCategory`: landed_cost, tax_credit, recoverable, non_deductible
- Campo en CostLine con default='landed_cost' (backwards compat)
- Actualizar `register_cost` en services/financial.py para aceptarlo
- financial-summary: margen se calcula SOLO sobre landed_cost. Tax credits aparte.

**S13-03: cost_behavior**  
- Nuevo enum `CostBehavior`: fixed_per_operation, variable_per_unit, variable_per_weight, semi_variable
- Campo nullable en CostLine (no todos los costos tienen clasificación desde el inicio)
- Actualizar `register_cost` para aceptarlo (opcional)

**S13-04: multi-moneda**
- 3 campos nuevos: `exchange_rate` (decimal 12,6 nullable), `amount_base_currency` (decimal 12,2 nullable), `base_currency` (char 3, default 'USD')
- Lógica en `register_cost`:
  - Si currency == base_currency → auto-fill TC=1.0 y amount_base_currency = amount
  - Si exchange_rate proporcionado → calcular amount_base_currency = amount × exchange_rate
  - Si exchange_rate es null y currency ≠ base_currency → amount_base_currency queda null (dashboard mostrará warning)
- Dirección del TC: 1 unidad de moneda original = X USD (ej: 1 BRL = 0.18 USD)

### Fase 2 — Lógica de negocio

**S13-05: Validación viabilidad Modelo C**
- Función `pre_check_viability()` que se llama en C4 (DecideModeBC) cuando mode=FULL
- Calcula costo landed estimado vs precio del cliente
- Si pérdida → WARNING en response (no blocking)
- Si falta algún input (lookup arancelario, FLETE_PCT, baseline costos fijos) → warning degradado "config incompleta" con lista de qué falta
- Resultado se registra en event_log
- **⚠️ FLETE_PCT viene de settings. Si no está configurado, no inventar un número. Retornar warning degradado.**

**S13-06: Artefactos ART-13 y ART-14**
- Agregar 2 entries a ArtifactType choices: `certificate_of_origin` y `due_export_br`
- ART-13 (Certificado Origen): precondición soft en T4 si dispatch_mode=mwt y origin=BR. Warning si falta, no blocking.
- ART-14 (DU-E): evidence-only. Se registra pero no bloquea nada.
- Nuevo campo en Expediente: `external_fiscal_refs = JSONField(default=list)` para DANFE, Carta de Corrección, etc.

### Fase 3 — Expediente

**S13-07: Aforo aduanero**
- 2 campos nuevos en Expediente: `aforo_type` (verde/amarillo/rojo, nullable) y `aforo_date` (date, nullable)
- Registrar en admin
- Este item es independiente — podés hacerlo aunque Sprint 12 no esté DONE

### Tests

**S13-08:** Archivo `backend/tests/test_sprint13.py`
- Tests para cada campo nuevo de CostLine (con/sin valor, cada enum)
- Tests de financial-summary filtrando por cost_category
- Tests de multi-moneda (USD auto-fill, BRL con TC, CRC con TC, sin TC)
- Tests de viabilidad (5 escenarios: rentable, pérdida, sin lookup, sin FLETE_PCT, sin baseline)
- Tests de artefactos (ART-13 precondición soft, ART-14 evidence)
- Tests de aforo (nullable)
- **Regresión: correr toda la suite existente y verificar 0 failures**

---

## Migración — todo en una

Generá una sola migración que agregue los 8 campos. Todos son additive:

| Campo | Modelo | Default/Null | Nota |
|-------|--------|-------------|------|
| cost_category | CostLine | default='landed_cost' | Rows existentes = landed_cost |
| cost_behavior | CostLine | null=True | Rows existentes = null |
| exchange_rate | CostLine | null=True | Rows existentes = null |
| amount_base_currency | CostLine | null=True | Rows existentes = null |
| base_currency | CostLine | default='USD' | Rows existentes = USD |
| aforo_type | Expediente | null=True | |
| aforo_date | Expediente | null=True | |
| external_fiscal_refs | Expediente | default=list | Lista vacía |

Si algo sale mal: `python manage.py migrate expedientes [última_migración_sprint12]` revierte todo.

---

## Lo que NO tenés que hacer

- ❌ Editar `knowledge/ENT_OPS_STATE_MACHINE.md` (FROZEN)
- ❌ Inventar valores de FLETE_PCT, DAI%, o cualquier dato de negocio
- ❌ Crear nuevas URLs de API (solo extender contratos existentes)
- ❌ Hacer ALTER destructivo o rename de campos
- ❌ Tocar docker-compose.yml, nginx, o settings de infra

---

## Lo que sí tenés que hacer si te trabás

- Si necesitás FLETE_PCT y no está en settings → dejá `# TODO: CEO_INPUT_REQUIRED` y seguí
- Si un test existente falla después de tu cambio → tu cambio tiene un bug, no el test
- Si algo del spec no queda claro → preguntale al CEO antes de asumir

---

## Checklist de entrega

```
ANTES DE EMPEZAR
[ ] Sprint 12 está DONE (services/ directory existe)
[ ] Tests existentes pasan (correr suite completa)

DURANTE
[ ] Migración única con los 8 campos
[ ] Enums como TextChoices (no strings sueltos)
[ ] register_cost acepta cost_category, cost_behavior, exchange_rate
[ ] financial-summary filtra por landed_cost
[ ] pre_check_viability en C4 con fallback degradado
[ ] ART-13/14 en ArtifactType + precondición soft T4
[ ] external_fiscal_refs en Expediente
[ ] aforo_type/aforo_date en Expediente

DESPUÉS
[ ] Tests existentes siguen pasando (0 failures)
[ ] test_sprint13.py completo y passing
[ ] financial-summary retorna mismo resultado para datos pre-v2
[ ] Conventional commits (feat:, fix:, test:)
[ ] Reporte de ejecución al CEO (formato PLB_ORCHESTRATOR §I)
```

---

## Reporte de ejecución (entregá esto al terminar)

```markdown
## Resultado de ejecución
- **Agente:** AG-02 Alejandro
- **Lote:** LOTE_SM_SPRINT13
- **Status:** DONE / PARTIAL / BLOCKED
- **Archivos creados:** [lista]
- **Archivos modificados:** [lista]
- **Archivos NO tocados (fuera de scope):** [confirmar]
- **Decisiones asumidas:** [lista — cualquier cosa que decidiste sin spec explícita]
- **Blockers:** [lista o "ninguno"]
- **Tests ejecutados:** [resumen]
- **TODO CEO_INPUT_REQUIRED:** [si quedó alguno]
```
