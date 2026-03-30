# PROMPT_ANTIGRAVITY_SPRINT20 — Proformas + ArtifactPolicy Backend

## TU ROL
Eres AG-02 (backend developer). Ejecutás el Sprint 20 del proyecto MWT.ONE. Tu trabajo es implementar exactamente lo que dice el LOTE_SM_SPRINT20 v1.6. No diseñás, no proponés alternativas, no expandís scope. Si algo no está claro, preguntás al CEO — no adivinás.

## CONTEXTO
Sprint 20 introduce el modelo de **proformas como unidad operativa**. Cada proforma (ART-02) tiene su propio mode (B/C), su propia cadena de artefactos, y sus propias líneas. El backend calcula qué artefactos aplican (ArtifactPolicy) y el frontend solo renderiza lo que recibe.

**Estado del código (post Sprint 18+19 DONE):**
- State machine 8 estados, 28+ commands
- ExpedienteProductLine con FK a ProductMaster + BrandSKU
- FactoryOrder, ExpedientePago funcionales
- Motor dimensional plataforma (app sizing/)
- Hook post_command_hooks en dispatcher
- 5 endpoints PATCH por estado, CRUD FactoryOrder, merge/split, pagos
- Bundle detalle con product_lines + factory_orders + pagos

## HARD RULES

1. **State machine FROZEN.** NO tocar handlers de transición en `services/state_machine/`. Solo modificar `c_create.py` (relajar C1) y la validación de C5.
2. **Backward compat.** POST a C1 con payload viejo (sin proformas) DEBE seguir funcionando.
3. **Migración additive-only.** Solo `AddField`. Verificar con `sqlmigrate` antes de aplicar. Si aparece `AlterField` o `RemoveField` → PARAR.
4. **BRAND_ALLOWED_MODES** vive en `artifact_policy.py`. Importar en endpoints. NO duplicar.
5. **Locking obligatorio.** Todo endpoint mutante: `transaction.atomic()` + `select_for_update()` en expediente + recurso mutado.
6. **line_ids strict.** `isinstance` checks: list → no bool → solo int → dedup. Sin casts.
7. **Relación línea→proforma** vive SOLO en `EPL.proforma` FK. Payload de ART-02 NO almacena líneas.

## VERIFICACIÓN PREVIA (antes de escribir código)

```bash
# Verificar que Sprint 18+19 están limpios
python manage.py check
python manage.py test
python manage.py showmigrations | grep "\[ \]"  # 0 migraciones pendientes

# Verificar modelos existentes
python manage.py shell -c "from apps.expedientes.models import ExpedienteProductLine; print([f.name for f in ExpedienteProductLine._meta.get_fields()])"
python manage.py shell -c "from apps.expedientes.models import ArtifactInstance; print([f.name for f in ArtifactInstance._meta.get_fields()])"

# Verificar que no hay hardcoded artifacts en backend
grep -rn "STATE_ARTIFACTS\|ARTIFACT_COMMAND_MAP" backend/
```

## ITEMS

### FASE 0 — Modelo de datos

#### S20-01: FK proforma en ExpedienteProductLine

```python
# apps/expedientes/models.py — agregar a ExpedienteProductLine:
proforma = models.ForeignKey(
    'ArtifactInstance',
    null=True, blank=True,
    limit_choices_to={'artifact_type': 'ART-02'},
    on_delete=models.SET_NULL,
    related_name='proforma_lines',
    help_text="Proforma (ART-02) a la que pertenece esta línea."
)
```

#### S20-02: FK parent_proforma en ArtifactInstance

```python
# apps/expedientes/models.py — agregar a ArtifactInstance:
parent_proforma = models.ForeignKey(
    'self',
    null=True, blank=True,
    limit_choices_to={'artifact_type': 'ART-02'},
    on_delete=models.SET_NULL,
    related_name='child_artifacts',
    help_text="Proforma padre. Null = artefacto a nivel expediente."
)
```

#### S20-03: ART-05 multi-proforma
Validar en serializer que `payload.linked_proformas` contiene IDs de ART-02 del mismo expediente.

#### S20-04: Mode en payload de ART-02
Validar en serializer: `payload.mode` requerido (mode_b, mode_c, default). `payload.operated_by` siempre presente con default "muito_work_limitada".

**MIGRACIÓN:**
```bash
python manage.py makemigrations expedientes
python manage.py sqlmigrate expedientes XXXX  # SOLO AddField ×2
python manage.py migrate
```

### FASE 1 — ArtifactPolicy engine

#### S20-05: Crear artifact_policy.py

```python
# apps/expedientes/services/artifact_policy.py

BRAND_ALLOWED_MODES = {
    'marluvas': ('mode_b', 'mode_c'),
    'rana_walk': ('default',),
    'tecmater': ('default',),
}

ARTIFACT_POLICY = {
    "marluvas": {
        "mode_b": {
            "REGISTRO":     {"required": ["ART-01", "ART-02"], "optional": ["ART-03"], "gate_for_advance": ["ART-01", "ART-02"]},
            "PRODUCCION":   {"required": [], "optional": [], "gate_for_advance": []},
            "PREPARACION":  {"required": ["ART-05", "ART-06", "ART-07"], "optional": ["ART-08"], "gate_for_advance": ["ART-05", "ART-06", "ART-07"]},
            "EN_DESTINO":   {"required": ["ART-10"], "optional": ["ART-12"], "gate_for_advance": ["ART-10"]},
        },
        "mode_c": {
            "REGISTRO":     {"required": ["ART-01", "ART-02"], "optional": ["ART-03"], "gate_for_advance": ["ART-01", "ART-02"]},
            "PRODUCCION":   {"required": [], "optional": [], "gate_for_advance": []},
            "PREPARACION":  {"required": ["ART-05", "ART-06", "ART-07"], "optional": ["ART-08"], "gate_for_advance": ["ART-05", "ART-06", "ART-07"]},
            "EN_DESTINO":   {"required": ["ART-09"], "optional": ["ART-12"], "gate_for_advance": ["ART-09"]},
        },
    },
    "rana_walk": {
        "default": {
            "REGISTRO":     {"required": ["ART-01", "ART-02"], "optional": [], "gate_for_advance": ["ART-01", "ART-02"]},
            "DESPACHO":     {"required": ["ART-05", "ART-06"], "optional": [], "gate_for_advance": ["ART-05", "ART-06"]},
            "EN_DESTINO":   {"required": ["ART-09"], "optional": [], "gate_for_advance": ["ART-09"]},
        },
    },
    "tecmater": {
        "default": {
            "REGISTRO":     {"required": ["ART-01", "ART-02"], "optional": [], "gate_for_advance": ["ART-01", "ART-02"]},
            "PREPARACION":  {"required": ["ART-05", "ART-06", "ART-07"], "optional": ["ART-08"], "gate_for_advance": ["ART-05", "ART-06", "ART-07"]},
            "EN_DESTINO":   {"required": ["ART-09"], "optional": [], "gate_for_advance": ["ART-09"]},
        },
    },
}


def resolve_artifact_policy(expediente) -> dict:
    """Ver LOTE S20-05 para implementación completa con:
    - Fallback REGISTRO genérica si sin proformas o brand desconocido
    - Early return si brand_policy vacío
    - Merge de policies por proforma mode
    - Normalización: required gana optional, gate ⊆ required
    - Fallback final si merged vacío
    - sorted lists para determinismo JSON
    """
    # COPIAR implementación completa de LOTE_SM_SPRINT20 v1.6 S20-05
    pass
```

#### S20-06: Bundle retorna artifact_policy
Agregar `artifact_policy = SerializerMethodField()` al BundleSerializer. Llama a `resolve_artifact_policy(obj)`.

### FASE 2 — C1 + C5 + reassign

#### S20-07: C1 flexible
En `c_create.py`: relajar validación. Solo `client_id` + `brand_id` requeridos. OC, líneas, todo lo demás opcional. NO reescribir el handler — solo cambiar qué campos son requeridos.

```bash
# Antes de modificar:
grep -n "required" apps/expedientes/services/state_machine/c_create.py
```

#### S20-08: C5 gate actualizado
```python
# Agregar a la validación de C5:
# 1. ART-01 completada
# 2. ≥1 ART-02 completada
# 3. 0 líneas con proforma=NULL
# 4. Cada proforma tiene mode
```

#### S20-09: POST reassign-line/
**Importante:** `select_for_update()` en expediente + línea + target. Capturar `old_proforma_id` ANTES del cambio para EventLog.

#### S20-10: change_proforma_mode
Crear `services/proforma_mode.py`. **Importante:** early return "mismo modo" va DENTRO del lock, después del re-fetch. Importar BRAND_ALLOWED_MODES desde artifact_policy.py.

#### S20-11: POST crear proforma
**Importante:** `select_for_update()` en expediente. Validar mode por brand (importar BRAND_ALLOWED_MODES). line_ids: isinstance checks (list → no bool → solo int → dedup).

### FASE 3 — Tests

#### S20-12: 35 tests
Crear `tests/test_proformas.py` y `tests/test_artifact_policy.py`. Ver lista completa en LOTE.

## CHECKLIST PRE-PR

```bash
# Migración
python manage.py sqlmigrate expedientes XXXX  # solo AddField
python manage.py migrate
python manage.py check

# Tests
python manage.py test  # 0 failures, 0 errors

# Seguridad
bandit -ll backend/  # 0 high/critical

# Lint
npm run lint && npm run typecheck

# Sanidad
grep -rn "BRAND_ALLOWED_MODES" backend/ | grep -v artifact_policy | grep -v "from.*import"  # 0 (no hay duplicados)
grep -rn "payload.*lines" backend/apps/expedientes/services/ | grep -v linked_proformas  # 0
```

## PREGUNTAS PARA EL CEO

Si algo no está cubierto en este prompt ni en el LOTE, preguntale al CEO. No adivines, no improvises, no expandas scope.
