# GUIA_ALE_SPRINT20 — Sprint 20: Modelo Proformas + ArtifactPolicy

Ale, este sprint cambia cómo funciona el expediente. Hasta ahora el expediente era una cosa plana — un modo, unos artefactos, unas líneas. A partir de Sprint 20, el expediente es un **contenedor de proformas**. Cada proforma tiene su propio modo (B o C), sus propias líneas, y su propia cadena de artefactos.

---

## El cambio en una frase

**Antes:** 1 expediente = 1 modo = artefactos fijos
**Después:** 1 expediente = N proformas, cada una con su modo y artefactos calculados por el backend

---

## Qué vas a construir (en orden)

### Fase 0 — Modelo de datos (migración)

1. **FK `proforma` en ExpedienteProductLine** — nullable, apunta a ArtifactInstance con artifact_type='ART-02'. Las líneas legacy quedan con proforma=NULL (correcto).

2. **FK `parent_proforma` en ArtifactInstance** — nullable, self-referential. Para vincular ART-04/05/09/10 a su proforma padre. ART-01, ART-11, ART-12 quedan NULL (son a nivel expediente).

3. **Validación mode en payload de ART-02** — cuando se crea una proforma, el payload DEBE tener `mode` (mode_b, mode_c, o default). El `operated_by` siempre va con default "muito_work_limitada".

4. **ART-05 multi-proforma** — un embarque puede combinar líneas de varias proformas. Se registra en `payload.linked_proformas` (array de IDs).

### Fase 1 — ArtifactPolicy engine

5. **Crear `services/artifact_policy.py`** — contiene dos constantes (`ARTIFACT_POLICY` y `BRAND_ALLOWED_MODES`) y una función `resolve_artifact_policy()`. La función mira qué proformas tiene el expediente, qué modo tiene cada una, y calcula qué artefactos aplican. El frontend ya no decide esto.

6. **Agregar `artifact_policy` al bundle** — el GET del detalle del expediente ahora retorna un campo más con la policy calculada.

### Fase 2 — C1 y C5 actualizados

7. **C1 flexible** — ahora solo requiere `client_id` + `brand_id`. Todo lo demás (OC, líneas) es opcional. NO reescribas el handler — solo relajá las validaciones de campos requeridos.

8. **C5 actualizado** — ahora valida: (a) ART-01 existe, (b) al menos 1 proforma, (c) todas las líneas asignadas a proforma, (d) cada proforma tiene mode.

9. **Endpoint reassign-line/** — mover una línea de una proforma a otra. Solo en REGISTRO.

### Fase 3 — Void y crear proforma

10. **change_proforma_mode** — servicio que cambia el modo de una proforma. Si cambia de B→C, void ART-10. Si C→B, void ART-09. Requiere confirmación (`confirm_void=true`).

11. **Endpoint crear proforma** — POST que crea ART-02 con mode, valida por brand, y opcionalmente asigna líneas.

12. **35 tests** — ver lista completa en el LOTE.

---

## Reglas que no podés romper

1. **State machine FROZEN** — no toques los handlers de transición. Solo estás extendiendo cómo se resuelven artefactos y cómo se valida C1/C5.

2. **Backward compat** — un POST a C1 con el payload viejo (sin proformas) tiene que seguir funcionando exactamente igual. Probalo.

3. **Migración additive-only** — solo `AddField`. Verificá con `sqlmigrate` que no haya `AlterField` ni `RemoveField`.

4. **BRAND_ALLOWED_MODES** — marluvas solo acepta mode_b/mode_c. rana_walk y tecmater solo aceptan default. Brand desconocida → error. La constante vive en `artifact_policy.py` y se importa en los endpoints.

5. **Locking** — todos los endpoints que mutan (reassign-line, create_proforma, change_mode) deben usar `transaction.atomic()` + `select_for_update()` en el expediente Y en el recurso que mutan.

6. **line_ids strict** — validar que sea `list[int]`. Rechazar bool, string, null (null→[]). No hacer casts mágicos.

7. **Relación línea→proforma** — vive SOLO en `EPL.proforma` FK. El payload de ART-02 NO almacena líneas.

---

## Archivos que vas a tocar

| Archivo | Qué hacer |
|---------|-----------|
| `apps/expedientes/models.py` | +FK proforma en EPL, +FK parent_proforma en ArtifactInstance |
| `apps/expedientes/services/artifact_policy.py` | CREAR — ARTIFACT_POLICY, BRAND_ALLOWED_MODES, resolve_artifact_policy() |
| `apps/expedientes/services/proforma_mode.py` | CREAR — change_proforma_mode() |
| `apps/expedientes/serializers.py` | Validación mode en ART-02 payload, linked_proformas en ART-05, BundleSerializer +artifact_policy |
| `apps/expedientes/views.py` | +create_proforma, +reassign-line, +change-mode endpoints |
| `apps/expedientes/urls.py` | Registrar nuevos endpoints |
| `apps/expedientes/admin.py` | Actualizar inlines |
| `apps/expedientes/services/state_machine/c_create.py` | Relajar validación C1 (solo client_id + brand_id requeridos) |
| `apps/expedientes/services/state_machine/` | Actualizar validate_c5_gate |
| `apps/expedientes/tests/test_proformas.py` | CREAR — 35 tests |
| `apps/expedientes/tests/test_artifact_policy.py` | CREAR |

## Archivos que NO podés tocar

- `apps/expedientes/services/state_machine/` handlers de transición (FROZEN)
- `docker-compose.yml`
- Nada en `apps/sizing/` (ese sprint ya pasó)

---

## Verificación antes de hacer PR

```bash
# 1. Migración limpia
python manage.py makemigrations expedientes
python manage.py sqlmigrate expedientes XXXX  # solo AddField ×2
python manage.py migrate
python manage.py check

# 2. Tests
python manage.py test  # TODO verde, 0 failures

# 3. Seguridad
bandit -ll backend/  # 0 high/critical

# 4. Lint
npm run lint && npm run typecheck  # verde (cambios frontend = 0)

# 5. Grep de sanidad
grep -rn "STATE_ARTIFACTS\|ARTIFACT_COMMAND_MAP" backend/  # debe ser 0
grep -rn "payload.*lines" backend/apps/expedientes/services/  # debe ser 0 (excepto linked_proformas en ART-05)
```

---

## Si tenés dudas

- Sobre el modelo de proformas: lee DIRECTRIZ_ARTEFACTOS_MODULARES (está en el proyecto)
- Sobre la state machine: lee ENT_OPS_STATE_MACHINE (FROZEN, no cambiar)
- Sobre cualquier decisión marcada DEC-*: ya está resuelta, no preguntar de nuevo
- Sobre algo no cubierto: preguntale al CEO, no adivines
