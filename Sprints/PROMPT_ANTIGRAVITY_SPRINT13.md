# PROMPT_ANTIGRAVITY_SPRINT13 — CostLine v2 + Caso 2391 Learnings
## Para: Claude Code (Antigravity) — AG-02 Backend
## Sprint: 13 · Auditoría: R3 9.6/10

---

## TU ROL

Eres AG-02 Backend Builder para el proyecto MWT.ONE. Implementas los items de Sprint 13 en código Django. El CEO (Alejandro) te da contexto y aprueba. Vos escribís código, no tomas decisiones de negocio.

---

## CONTEXTO DEL PROYECTO

- **Stack:** Django 5.x + DRF + PostgreSQL 16 + Celery + Redis + MinIO + Docker Compose
- **Repo:** mwt.one, branch `main`
- **Sprint 13 objetivo:** Incorporar aprendizajes del primer expediente real (PF 2391-2025) al modelo CostLine y lógica de negocio
- **Prerequisito:** Sprint 12 DONE (services.py refactorizado en `services/` directory)

---

## HARD RULES — NUNCA VIOLAR

1. **ENT_OPS_STATE_MACHINE es FROZEN.** No edites `knowledge/ENT_OPS_STATE_MACHINE.md` bajo ninguna circunstancia. Las referencias a "F2", "C4", "C15", "T4" son coordenadas de lectura, no instrucciones de edición. Los cambios se implementan solo en código Python.

2. **No inventar datos.** Si necesitas un valor de negocio (DAI%, FLETE_PCT, pricing), busca en el LOTE spec o pregunta al CEO. Nunca hardcodear un número inventado. Usar `settings.py` o lookup tables para configuración.

3. **No romper la state machine.** Los 22 commands C1-C22 deben seguir funcionando exactamente igual post-migración. Mismos inputs → mismos outputs. Si un test existente falla, tu código tiene un bug.

4. **Migraciones additive only.** Solo agregar campos (nullable o con default). Nunca ALTER destructivo, rename, ni DROP. Cada migración debe ser reversible con `RemoveField`.

5. **No tocar archivos fuera de tu scope.** Tu scope es:
   - `backend/apps/expedientes/models.py` (extend)
   - `backend/apps/expedientes/services/financial.py` (C15)
   - `backend/apps/expedientes/services/commands_registro.py` (C4)
   - `backend/apps/expedientes/serializers.py` (extend)
   - `backend/apps/expedientes/admin.py` (register new fields)
   - `backend/apps/expedientes/enums.py` (new TextChoices)
   - `backend/tests/` (new tests)
   
   NO tocar: `knowledge/`, `CLAUDE.md`, `docker-compose.yml`, `nginx/`, `config/settings/` (excepto agregar config keys nuevas).

6. **Tests antes y después.** Antes de tocar un archivo, correr tests existentes. Después de modificar, los mismos tests deben pasar sin cambios. Tests nuevos van en archivos separados.

7. **Conventional Commits.** `feat:`, `fix:`, `refactor:`, `test:`. Nunca commits genéricos como "update" o "changes".

---

## ITEMS A IMPLEMENTAR

### Orden de ejecución

```
S13-02 (cost_category) ──┐
S13-03 (cost_behavior) ──┤── Fase 1: pueden ir en paralelo o secuencial
S13-04 (multi-moneda) ───┘       una sola migración consolidada preferible

S13-05 (viabilidad C4) ─────── Fase 2: después de Fase 1

S13-06 (artefactos ART-13/14) ── Fase 2: independiente de S13-05

S13-07 (aforo expediente) ───── Fase 3: independiente

S13-08 (tests) ──────────────── después de todo
```

---

### S13-02: Agregar cost_category a CostLine

**Archivo:** `models.py` (CostLine model)

```python
class CostCategory(models.TextChoices):
    LANDED_COST = 'landed_cost', 'Landed Cost'
    TAX_CREDIT = 'tax_credit', 'Tax Credit (recuperable)'
    RECOVERABLE = 'recoverable', 'Recoverable (otro)'
    NON_DEDUCTIBLE = 'non_deductible', 'Non-Deductible'

# En CostLine:
cost_category = models.CharField(
    max_length=20,
    choices=CostCategory.choices,
    default=CostCategory.LANDED_COST,
)
```

**Archivo:** `services/financial.py` — actualizar `register_cost` para aceptar `cost_category` (opcional, default `landed_cost`)

**Regla de negocio:** `financial-summary` endpoint calcula margen solo sobre registros con `cost_category='landed_cost'`. Los `tax_credit` se muestran como línea separada.

**Migración:** default='landed_cost'. Todos los rows existentes quedan como landed_cost (correcto para datos pre-v2).

---

### S13-03: Agregar cost_behavior a CostLine

**Archivo:** `models.py`

```python
class CostBehavior(models.TextChoices):
    FIXED_PER_OPERATION = 'fixed_per_operation', 'Fixed per Operation'
    VARIABLE_PER_UNIT = 'variable_per_unit', 'Variable per Unit'
    VARIABLE_PER_WEIGHT = 'variable_per_weight', 'Variable per Weight'
    SEMI_VARIABLE = 'semi_variable', 'Semi-Variable'

# En CostLine:
cost_behavior = models.CharField(
    max_length=25,
    choices=CostBehavior.choices,
    null=True,
    blank=True,
)
```

**Migración:** nullable. No backfill.

---

### S13-04: Agregar multi-moneda a CostLine

**Archivo:** `models.py`

```python
# En CostLine:
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

**Contrato técnico:**
- `currency` (campo existente) = moneda original del costo
- `exchange_rate` = TC de currency → base_currency. Dirección: 1 currency = X base_currency (ej: 1 BRL = 0.18 USD)
- `amount_base_currency` = amount × exchange_rate. Calculado automáticamente en C15 si exchange_rate es proporcionado.
- Si `currency == base_currency`: auto-fill `exchange_rate=1.0`, `amount_base_currency=amount`
- Si `exchange_rate is null` y `currency != base_currency`: `amount_base_currency` queda null
- Precisión: 6 decimales para exchange_rate, 2 para amounts

**Archivo:** `services/financial.py` — actualizar `register_cost`:
```python
# Dentro de register_cost:
if data.get('exchange_rate') and data.get('currency'):
    if data['currency'] == (data.get('base_currency') or 'USD'):
        cost.exchange_rate = Decimal('1.0')
        cost.amount_base_currency = cost.amount
    else:
        cost.exchange_rate = data['exchange_rate']
        cost.amount_base_currency = cost.amount * cost.exchange_rate
elif data.get('currency') == (data.get('base_currency') or 'USD'):
    cost.exchange_rate = Decimal('1.0')
    cost.amount_base_currency = cost.amount
```

**financial-summary:** Usar `amount_base_currency` cuando disponible, `amount` cuando es null (legacy).

**Migración:** exchange_rate y amount_base_currency nullable. base_currency default='USD'.

---

### S13-05: Validación viabilidad Modelo C en C4

**Archivo:** `services/commands_registro.py` — dentro de `decide_mode_bc` (C4)

```python
def pre_check_viability(expediente, mode, fob_mwt, fob_cliente, qty):
    """WARNING advisory — no bloquea, solo informa."""
    if mode != 'FULL':
        return None
    
    # Verificar que todos los inputs están disponibles
    missing_inputs = []
    
    partida = getattr(expediente, 'partida_arancelaria', None)
    dai_pct = get_dai_rate(partida, expediente.destination_country) if partida else None
    if dai_pct is None:
        missing_inputs.append('lookup_arancelario')
    
    flete_pct = getattr(settings, 'VIABILITY_FLETE_PCT', None)
    if flete_pct is None:
        missing_inputs.append('FLETE_PCT')
    
    fixed_costs = get_estimated_fixed_costs(qty)
    if fixed_costs is None:
        missing_inputs.append('baseline_costos_fijos')
    
    if missing_inputs:
        return {
            'warning': True,
            'degraded': True,
            'message': f'Config incompleta — cálculo de viabilidad no disponible',
            'missing_inputs': missing_inputs,
        }
    
    costo_landed_est = fob_mwt * (1 + flete_pct) * (1 + dai_pct) + fixed_costs
    
    if costo_landed_est > fob_cliente:
        delta = costo_landed_est - fob_cliente
        return {
            'warning': True,
            'degraded': False,
            'message': f'Modelo C genera pérdida estimada de ${delta:.2f}/par',
            'costo_landed_est': float(costo_landed_est),
            'fob_cliente': float(fob_cliente),
            'delta_per_unit': float(delta),
        }
    return None
```

**Integración con C4:** Llamar `pre_check_viability` al inicio de `decide_mode_bc`. El resultado se incluye en la response body como `viability_check`. Se registra en event_log como `viability_check_result`. NO bloquea la transición — CEO decide.

**Lookup arancelario:** Implementar `get_dai_rate(partida, pais)` como lookup desde una tabla de configuración o dict en settings. El CEO provee los datos en S13-01. Si la partida no está en la tabla, retornar None (no inventar).

**`get_estimated_fixed_costs(qty)`:** Busca promedio de las últimas 5 operaciones con `cost_behavior='fixed_per_operation'`. Si no hay data, retorna None.

---

### S13-06: Agregar artefactos ART-13 y ART-14

**Archivo:** `enums.py` — agregar a ArtifactType:
```python
CERTIFICATE_OF_ORIGIN = 'certificate_of_origin', 'Certificado de Origen'  # ART-13
DUE_EXPORT_BR = 'due_export_br', 'DU-E Exportación Brasil'  # ART-14
```

**Archivo:** `models.py` — agregar campo en Expediente:
```python
external_fiscal_refs = models.JSONField(
    default=list,
    blank=True,
    help_text="Referencias fiscales externas: DANFE, Carta de Corrección, DU-E"
)
```

**Lógica ART-13 (Certificado de Origen):** Precondición soft en T4 (ApproveDispatch). Si `dispatch_mode='mwt'` y `origin_country='BR'` y no existe ART-13 instance → incluir warning en response "Certificado de Origen no registrado". No blocking en MVP.

**Lógica ART-14 (DU-E):** Evidence-only. Se puede registrar como ArtifactInstance pero no es precondición de ninguna transición. Es referencia fiscal del exportador.

---

### S13-07: Aforo en expediente

**Archivo:** `models.py` — agregar en Expediente:
```python
class AforoType(models.TextChoices):
    VERDE = 'verde', 'Verde'
    AMARILLO = 'amarillo', 'Amarillo'
    ROJO = 'rojo', 'Rojo'

aforo_type = models.CharField(
    max_length=10,
    choices=AforoType.choices,
    null=True, blank=True,
)
aforo_date = models.DateField(null=True, blank=True)
```

**Admin:** Registrar los campos nuevos en ExpedienteAdmin.

---

### S13-08: Tests

Crear `backend/tests/test_sprint13.py` con:

**CostLine v2:**
- Crear CostLine con cada cost_category → verificar financial-summary solo suma landed_cost
- Crear CostLine con/sin cost_behavior → nullable funciona
- CostLine en USD → auto-fill TC=1.0 y amount_base_currency=amount
- CostLine en BRL con exchange_rate → amount_base_currency calculado
- CostLine en CRC con exchange_rate → amount_base_currency calculado
- CostLine sin exchange_rate y currency!=USD → amount_base_currency=null
- CostLine pre-v2 (legacy) → defaults no rompen dashboard
- Migración forward/backward sin data loss

**Viabilidad Modelo C:**
- mode=FULL rentable → no warning
- mode=FULL pérdida → warning con delta correcto
- mode=FULL sin lookup arancelario → warning degradado "config incompleta" con missing_inputs=['lookup_arancelario']
- mode=FULL sin FLETE_PCT → warning degradado con missing_inputs=['FLETE_PCT']
- mode=FULL sin baseline costos fijos → warning degradado con missing_inputs=['baseline_costos_fijos']
- mode=B → skip check (None returned)
- Event log registra viability_check_result

**Artefactos:**
- ART-13 registrable como ArtifactInstance
- T4 con dispatch_mode=mwt y origin=BR sin ART-13 → warning en response
- ART-14 registrable como evidence
- external_fiscal_refs acepta lista de strings

**Expediente:**
- aforo_type y aforo_date nullable y funcionales
- Admin muestra campos nuevos

**Regresión:**
- Los 22 commands C1-C22 siguen funcionando (correr test suite existente completa)
- financial-summary retorna mismos resultados para datos pre-v2
- Tests de state machine pasan sin modificación

---

## MIGRATION PLAN

Una sola migración consolidada para todos los campos nuevos:

| Campo | Modelo | Default/Nullable |
|-------|--------|-----------------|
| cost_category | CostLine | default='landed_cost' |
| cost_behavior | CostLine | null=True |
| exchange_rate | CostLine | null=True |
| amount_base_currency | CostLine | null=True |
| base_currency | CostLine | default='USD' |
| aforo_type | Expediente | null=True |
| aforo_date | Expediente | null=True |
| external_fiscal_refs | Expediente | default=list |

**Rollback:** `python manage.py migrate expedientes [last_sprint12_migration]`

---

## CHECKLIST PRE-COMMIT

```
[ ] Tests existentes pasan ANTES de cambios
[ ] Migración generada sin errores
[ ] python manage.py migrate sin errores
[ ] Tests existentes pasan DESPUÉS de cambios
[ ] Tests nuevos (test_sprint13.py) pasan
[ ] 0 nuevos paths de API creados (solo extensión de contratos existentes)
[ ] financial-summary sigue retornando mismos resultados para datos legacy
[ ] Conventional commit messages
```

---

## PREGUNTAS PARA EL CEO (no inventar respuestas)

Si encuentras que necesitas alguno de estos datos y no están en el spec:
- FLETE_PCT estimado para cálculo de viabilidad
- Lookup arancelario completo (partidas + tasas por país)
- Partidas arancelarias adicionales más allá de 6403.99.90
- Decisión sobre si external_fiscal_refs necesita schema definido o es free-form

**Marcar como `# TODO: CEO_INPUT_REQUIRED` en el código y seguir con el resto.**
