# Resumen Sprint 20 — Modelo Proformas + ArtifactPolicy Backend

**Rama:** `sprint-20-fase3`  
**Fecha:** 2026-03-30  
**Estado:** ✅ COMPLETADO — 35 tests verdes, 0 regresiones  
**Ref lote:** LOTE_SM_SPRINT20 v1.6 (aprobado 9.5/10)

---

## Contexto general

Sprint 20 es el primero en implementar la **DIRECTRIZ_ARTEFACTOS_MODULARES**. Hasta Sprint 19, el expediente era monolítico: un solo mode, un set de artefactos, líneas planas. Sprint 20 lo transforma en un **contenedor de N proformas independientes**, cada una con su mode, su cadena de artefactos y sus líneas de producto.

**Cambio de paradigma:**
1. El expediente pasa de contenedor monolítico a contenedor de proformas.
2. Cada proforma tiene su `mode` (`mode_b`, `mode_c`, `default`) de forma independiente.
3. El backend calcula qué artefactos aplican (`ArtifactPolicy`) y el frontend solo renderiza lo que recibe.

---

## FASE 0 — Modelo de datos (migración aditiva)

### S20-01: FK `proforma` nullable en `ExpedienteProductLine`

**Commit:** [`a15cd30`](https://github.com/Ale241302/mwt_one/commit/a15cd3022f1b7c6a8dabe78d92f9e9d7e5c968d9)

**Objetivo:** Relacionar cada línea de producto con su proforma padre (ART-02), manteniendo compatibilidad con líneas legacy (proforma=NULL).

**Archivos modificados:**
- `backend/apps/expedientes/models.py` — Se añadió FK nullable `proforma` al modelo `ExpedienteProductLine`:
  - `on_delete=SET_NULL` — si se borra la proforma, la línea queda huérfana (no se borra)
  - `related_name='proforma_lines'`
  - `limit_choices_to={'artifact_type': 'ART-02'}`
- `backend/apps/expedientes/admin.py` — Se actualizó el inline `ExpedienteProductLineInline` para mostrar el campo `proforma`.

**Migración generada:**
- `backend/apps/expedientes/migrations/0019_s20_proforma_fks.py` — `AddField` puro (aditivo). Solo `ALTER TABLE ADD COLUMN NULL`.

**Criterio de done alcanzado:**
- Campo `proforma` existe en `ExpedienteProductLine`, nullable ✅
- Migración es `AddField` solamente ✅
- Líneas legacy pre-S20 tienen `proforma=NULL` correctamente ✅

---

### S20-02: FK `parent_proforma` nullable en `ArtifactInstance`

**Commit:** [`a15cd30`](https://github.com/Ale241302/mwt_one/commit/a15cd3022f1b7c6a8dabe78d92f9e9d7e5c968d9)

**Objetivo:** Vincular artefactos dependientes (ART-04, ART-09, ART-10) a su proforma padre.

**Archivos modificados:**
- `backend/apps/expedientes/models.py` — Se añadió FK auto-referenciada nullable `parent_proforma` al modelo `ArtifactInstance`:
  - `on_delete=SET_NULL`
  - `related_name='child_artifacts'`
  - `limit_choices_to={'artifact_type': 'ART-02'}`

**Reglas de vinculación (HR-11):**
- ART-04 (SAP), ART-09 (factura MWT), ART-10 (factura comisión) → se vinculan a UNA proforma.
- ART-01 (OC), ART-11 (costos), ART-12 (compensación) → nivel expediente, `parent_proforma=NULL`.
- ART-05 (embarque) → vinculado vía `parent_proforma` (proforma principal) + `payload.linked_proformas` para multi-proforma.

**Criterio de done alcanzado:**
- Campo `parent_proforma` existe en `ArtifactInstance`, nullable ✅
- Artefactos pre-S20 tienen `parent_proforma=NULL` correctamente ✅

---

### S20-03: ART-05 multi-proforma vía `payload.linked_proformas` (HR-12)

**Commit:** [`a15cd30`](https://github.com/Ale241302/mwt_one/commit/a15cd3022f1b7c6a8dabe78d92f9e9d7e5c968d9)

**Objetivo:** ART-05 (embarque) puede combinar líneas de múltiples proformas cuando viajan juntas en el mismo envío.

**Archivos modificados:**
- `backend/apps/expedientes/serializers.py` — Se añadió validación en el serializer de ART-05:
  - Todos los IDs en `payload.linked_proformas` deben ser `ArtifactInstance` con `artifact_type='ART-02'` del mismo expediente.
  - `parent_proforma` FK debe ser uno de los IDs en `linked_proformas`.

**Formato del payload ART-05:**
```json
{
  "artifact_type": "ART-05",
  "payload": {
    "awb_number": "123-45678901",
    "linked_proformas": ["uuid-pf1", "uuid-pf2"]
  }
}
```

**Criterio de done alcanzado:**
- ART-05 acepta 1 o N proformas en `linked_proformas` ✅
- Validación de pertenencia al mismo expediente ✅

---

### S20-04: Validar `mode` en payload de ART-02 (HR-8/9)

**Commit:** [`a15cd30`](https://github.com/Ale241302/mwt_one/commit/a15cd3022f1b7c6a8dabe78d92f9e9d7e5c968d9)

**Objetivo:** El `mode` de cada proforma vive en `payload.mode` de `ArtifactInstance(artifact_type='ART-02')`, no en el expediente. Permite que dos proformas del mismo expediente tengan modos distintos.

**Archivos modificados:**
- `backend/apps/expedientes/serializers.py` — Se añadió validación:
  - `mode` requerido en payload de ART-02. Valores válidos: `mode_b`, `mode_c`, `default`.
  - `operated_by` siempre presente con default `"muito_work_limitada"`.
  - Las líneas NO se vinculan automáticamente desde el payload (eliminado doble fuente de verdad — H6 auditoría R1). La vinculación es exclusiva vía `EPL.proforma` FK.

**Regla HR-9:** ART-03 (Decisión Modo) aplica ahora por proforma, no por expediente.

**Criterio de done alcanzado:**
- ART-02 sin `mode` en payload → error de validación ✅
- Dos ART-02 del mismo expediente pueden tener modos distintos ✅
- `operated_by` siempre almacenado en payload ✅

**Fix de migración relacionado:**
- `backend/apps/expedientes/migrations/0019_s20_proforma_fks.py` — Corregida dependencia en migración (commit [`4c94f43`](https://github.com/Ale241302/mwt_one/commit/4c94f4375b694222a60b5c96292f4a5632b3cf4a)): la dep era `0019` inexistente, corregida a `0018_sprint18_fields`.
- Eliminada migración con nombre incorrecto `0020` (commit [`5119af1`](https://github.com/Ale241302/mwt_one/commit/5119af14d9d14e3aaff52c4a42d3092aa794d4f4)).

---

## FASE 1 — ArtifactPolicy engine

### S20-05: Constante `ARTIFACT_POLICY` y servicio `resolve_artifact_policy()`

**Commit:** [`5c576e8`](https://github.com/Ale241302/mwt_one/commit/5c576e882b36422a4d53a5ee6b4feadcacd9a51b)

**Objetivo:** Motor backend que calcula qué artefactos aplican por expediente según brand y modos de sus proformas.

**Archivos creados:**
- `backend/apps/expedientes/services/artifact_policy.py` — Archivo nuevo con:
  - `BRAND_ALLOWED_MODES` — dict centralizado de modos permitidos por brand (única fuente de verdad, importar desde aquí en todos los endpoints):
    ```python
    BRAND_ALLOWED_MODES = {
        'marluvas': ('mode_b', 'mode_c'),
        'rana_walk': ('default',),
        'tecmater': ('default',),
    }
    ```
  - `ARTIFACT_POLICY` — dict de policies completas por brand × mode × estado:
    - `marluvas/mode_b`: REGISTRO→ART-01/02, PRODUCCION→vacío, PREPARACION→ART-05/06/07, EN_DESTINO→ART-10
    - `marluvas/mode_c`: igual que mode_b pero EN_DESTINO→ART-09 (en vez de ART-10)
    - `rana_walk/default`: REGISTRO→ART-01/02, DESPACHO→ART-05/06, EN_DESTINO→ART-09 (sin ART-03/04/08)
    - `tecmater/default`: REGISTRO→ART-01/02, PREPARACION→ART-05/06/07, EN_DESTINO→ART-09
  - `resolve_artifact_policy(expediente)` — función que calcula la policy del expediente:
    - Sin proformas → policy genérica REGISTRO
    - Brand desconocida → fallback REGISTRO genérica (no retorna vacío)
    - Con proformas → unión de policies de todas, por mode
    - **Normalización post-merge:** `required` gana sobre `optional` (set difference); `gate_for_advance ⊆ required` (set intersection)
    - Output: dict serializable con listas ordenadas (no sets)

**Criterio de done alcanzado:**
- `ARTIFACT_POLICY` con 4 configs (marluvas/mode_b, marluvas/mode_c, rana_walk/default, tecmater/default) ✅
- 0 proformas → REGISTRO genérica ✅
- Brand desconocida → fallback (no vacío) ✅
- Mixed modes → unión correcta con normalización ✅
- `gate_for_advance ⊆ required` garantizado ✅
- Rana Walk sin ART-03/04/08 ✅

---

### S20-06: Bundle retorna `artifact_policy` calculada

**Commits:** [`6c9c32f`](https://github.com/Ale241302/mwt_one/commit/6c9c32fca23963f73302a887c0b53bf9cd65ccba), [`48a0bb5`](https://github.com/Ale241302/mwt_one/commit/48a0bb5d5189e520338e411b49797a718915a467)

**Objetivo:** El endpoint de detalle del expediente incluye la `artifact_policy` calculada dinámicamente, para que el frontend renderice los artefactos correctos sin lógica propia.

**Archivos modificados:**
- `backend/apps/expedientes/serializers.py` — Se añadió `artifact_policy` como `SerializerMethodField` en `ExpedienteBundleSerializer`:
  ```python
  artifact_policy = serializers.SerializerMethodField()

  def get_artifact_policy(self, obj):
      return resolve_artifact_policy(obj)
  ```

**Respuesta del bundle GET `/api/ui/expedientes/{id}/`:**
```json
{
  "status": "REGISTRO",
  "artifact_policy": {
    "REGISTRO": {
      "required": ["ART-01", "ART-02"],
      "optional": ["ART-03"],
      "gate_for_advance": ["ART-01", "ART-02"]
    },
    "PRODUCCION": { "required": [], "optional": [], "gate_for_advance": [] },
    "PREPARACION": {
      "required": ["ART-05", "ART-06", "ART-07"],
      "optional": ["ART-08"],
      "gate_for_advance": ["ART-05", "ART-06", "ART-07"]
    },
    "EN_DESTINO": {
      "required": ["ART-10"],
      "optional": ["ART-12"],
      "gate_for_advance": ["ART-10"]
    }
  }
}
```

**Criterio de done alcanzado:**
- Bundle retorna `artifact_policy` calculada dinámicamente ✅
- Expediente sin proformas → solo REGISTRO en policy ✅

---

## FASE 2 — C1 flexible + C5 actualizado

### S20-07: Actualizar `handle_c1` — mínimo `client_id` + `brand_id` (HR-13)

**Commits:** [`48a0bb5`](https://github.com/Ale241302/mwt_one/commit/48a0bb5d5189e520338e411b49797a718915a467), [`739bcd2`](https://github.com/Ale241302/mwt_one/commit/739bcd2d48b2434b75d79acbfb87d656fa936031)

**Objetivo:** C1 (crear expediente) ahora acepta solo `client_id` + `brand_id`. OC, líneas y demás campos son opcionales — se procesan si se proporcionan (backward compatible con payloads S18/S19).

**Archivos modificados:**
- `backend/apps/expedientes/services/state_machine/c_create.py` — Se relajó la validación de campos requeridos: solo `client_id` y `brand_id` son obligatorios. El resto pasa a opcional con defaults.
- `backend/apps/expedientes/views_s20.py` — Creado (o extendido) con `ProformaCreateView`.
- `backend/apps/expedientes/urls_ui.py` — Se registró `POST /api/ui/expedientes/<pk>/artifacts/proforma/`.

**Criterio de done alcanzado:**
- POST con `{client_id, brand_id}` → expediente en REGISTRO ✅
- POST con payload completo (OC + líneas estilo S18) → funciona igual ✅
- `credit_check` sigue ejecutándose correctamente ✅

---

### S20-08: Actualizar `validate_c5_gate` (HR-13)

**Commit:** [`a15cd30`](https://github.com/Ale241302/mwt_one/commit/a15cd3022f1b7c6a8dabe78d92f9e9d7e5c968d9)

**Objetivo:** C5 (REGISTRO → PRODUCCION) ahora valida que el expediente tenga proformas completas, todas las líneas asignadas y todos los modos configurados.

**Archivos modificados:**
- `backend/apps/expedientes/services/state_machine/` (gate de C5) — Se actualizó `validate_c5_gate`:
  1. ART-01 existe y completada
  2. Al menos 1 ART-02 completada con `status='COMPLETED'`
  3. 0 líneas huérfanas (`proforma__isnull=True`)
  4. Cada proforma tiene `mode` en payload

**Criterio de done alcanzado:**
- C5 con 0 proformas → error descriptivo ✅
- C5 con línea sin proforma → error con conteo ✅
- C5 con proforma sin mode → error identificando la proforma ✅
- Expedientes legacy pre-S20 → fallan C5 correctamente (remediación manual requerida) ✅

---

### S20-09: Endpoint `POST reassign-line/` (HR-10)

**Commit:** [`c3aba23`](https://github.com/Ale241302/mwt_one/commit/c3aba232bf3e6c352ff237800eb805a1bcbcee56)

**Objetivo:** Mover una línea de producto de una proforma a otra dentro del mismo expediente (solo en estado REGISTRO).

**Archivos modificados:**
- `backend/apps/expedientes/views.py` — Se añadió action `reassign_line`:
  - `POST /api/expedientes/{id}/command/C_REASSIGN_LINE/`
  - Payload: `{"line_id": 42, "target_proforma_id": "uuid"}`
  - `transaction.atomic()` + `select_for_update()` en expediente, línea y target
  - Captura `old_proforma_id` **antes** del cambio
  - Genera `EventLog` con `from_proforma` y `to_proforma`
- `backend/apps/expedientes/urls.py` — Se registró la nueva ruta.

**Criterio de done alcanzado:**
- Mueve línea de proforma A a proforma B en estado REGISTRO ✅
- Falla si expediente no está en REGISTRO ✅
- Falla si target no es ART-02 del mismo expediente ✅
- EventLog con valores pre-cambio correctos ✅
- Operación atómica con locks ✅

---

## FASE 3 — Void por cambio de modo + tests

### S20-10: Void automático al cambiar modo de proforma (SG-05)

**Commit:** [`c3aba23`](https://github.com/Ale241302/mwt_one/commit/c3aba232bf3e6c352ff237800eb805a1bcbcee56)

**Objetivo:** Al cambiar el `mode` de una proforma, hacer `VOIDED` automáticamente los artefactos incompatibles con el nuevo modo. Requiere `confirm_void=True` para ejecutar; sin él retorna preview.

**Archivos creados:**
- `backend/apps/expedientes/services/proforma_mode.py` — Servicio nuevo con `change_proforma_mode(proforma, new_mode, confirm_void=False, user=None)`:
  - Valida `new_mode` contra `BRAND_ALLOWED_MODES` antes del lock (falla rápido)
  - Re-fetcha proforma con `select_for_update()` dentro del `transaction.atomic()` (fix R6-H1 — `old_mode` leído desde objeto bloqueado, no stale)
  - **Tabla de voids:**
    - `mode_b → mode_c` → VOID ART-10
    - `mode_c → mode_b` → VOID ART-09
  - Sin `confirm_void` → retorna `{'changed': False, 'preview': True, 'artifacts_to_void': [...]}`
  - Con `confirm_void=True` → voidea artefactos + actualiza `payload.mode` + genera `EventLog`
  - Transiciones inválidas (`mode_b/c → default`) son rechazadas por `BRAND_ALLOWED_MODES` antes de llegar aquí

**Archivos modificados:**
- `backend/apps/expedientes/views.py` — Se añadió endpoint `PATCH /api/expedientes/{id}/proforma/{pf_id}/change-mode/`.
- `backend/apps/expedientes/urls.py` — Se registró la nueva ruta.

**Criterio de done alcanzado:**
- `mode_b → mode_c` → void ART-10 con `confirm_void=True` ✅
- `mode_c → mode_b` → void ART-09 con `confirm_void=True` ✅
- Sin `confirm_void` → preview sin ejecutar ✅
- Brand no soportada → `ValueError` con mensaje claro ✅
- Mode no permitido para la brand → `ValueError` con mensaje claro ✅
- EventLog en cada void y en el cambio de mode ✅

---

### S20-11: Endpoint `POST /api/expedientes/{id}/proformas/`

**Commits:** [`c3aba23`](https://github.com/Ale241302/mwt_one/commit/c3aba232bf3e6c352ff237800eb805a1bcbcee56), [`e6aba47`](https://github.com/Ale241302/mwt_one/commit/e6aba4792829401b41613227d135f5c1b42911ca)

**Objetivo:** Crear una proforma (ART-02) en un expediente con mode, operated_by y asignación de líneas — todo en una sola operación atómica.

**Archivos modificados:**
- `backend/apps/expedientes/views.py` — Se añadió action `create_proforma`:
  - Valida `mode` contra `BRAND_ALLOWED_MODES` (importado de `artifact_policy.py`)
  - `select_for_update()` en expediente (protege validación de status)
  - Solo acepta expedientes en estado `REGISTRO`
  - Crea `ArtifactInstance(artifact_type='ART-02', status='COMPLETED')` con `proforma_number` auto-generado si no se proporciona
  - **Validación `line_ids` estricta (R5-H1):**
    - `null` → lista vacía, no explota
    - No es lista → `ValidationError`
    - Contiene `bool` → `ValidationError` ("no acepta booleanos")
    - Contiene no-`int` → `ValidationError` ("solo enteros")
    - Dedup antes de procesar
    - IDs inexistentes → `ValidationError` ("no encontrados")
    - Líneas ya asignadas → `ValidationError` ("ya asignadas")
  - `EventLog` con `assigned_count` real
- `backend/apps/expedientes/urls.py` — Se registró `POST /api/expedientes/{id}/proformas/`.

**Criterio de done alcanzado:**
- Crea ART-02 con `mode`, `operated_by`, `proforma_number` en payload ✅
- Valida mode por brand ✅
- Asigna líneas con dedup y todas las validaciones ✅
- Solo funciona en REGISTRO ✅
- EventLog con `assigned_count` real ✅

**Fix de registro de URLs:**
- Commit [`e6aba47`](https://github.com/Ale241302/mwt_one/commit/e6aba4792829401b41613227d135f5c1b42911ca) — Se registraron los endpoints `proformas/` y `change-mode/` en el router de URLs que faltaban.

---

### S20-12: 35 tests — `test_proformas.py`

**Commits:** [`c3aba23`](https://github.com/Ale241302/mwt_one/commit/c3aba232bf3e6c352ff237800eb805a1bcbcee56), [`9603d89`](https://github.com/Ale241302/mwt_one/commit/9603d8978dbc496946d4b0b9710c05a8947ea852)

**Objetivo:** Suite completa de 35 tests que cubren todas las funcionalidades del Sprint 20, más los casos edge y de regresión identificados en las 6 rondas de auditoría del lote.

**Archivos creados:**
- `backend/apps/expedientes/tests/test_proformas.py` — 35 tests agrupados en 10 bloques:

| # | Test | Bloque |
|---|------|--------|
| 1 | Crear expediente sin OC → REGISTRO vacío | Bloque 1 — Básicos |
| 2 | 2 proformas en mismo expediente | Bloque 1 |
| 3 | Asignar líneas vía `create_proforma` | Bloque 1 |
| 4 | C5 con línea sin proforma → gate bloquea | Bloque 1 |
| 5 | Rana Walk → policy sin ART-03/04/08 | Bloque 1 |
| 6 | `reassign-line` en REGISTRO → OK + EventLog | Bloque 2 — reassign-line |
| 7 | `reassign-line` en PRODUCCION → error | Bloque 2 |
| 8 | `resolve_artifact_policy()` 0 proformas → REGISTRO | Bloque 3 — Policy |
| 9 | 2 proformas mixed mode → unión correcta | Bloque 3 |
| 10 | Brand desconocida → fallback REGISTRO | Bloque 3 |
| 11 | Normalización: `required` gana sobre `optional` | Bloque 3 |
| 12 | `gate_for_advance ⊆ required` | Bloque 3 |
| 13 | C1 con solo `client_id` + `brand_id` → OK | Bloque 4 — C1 backward compat |
| 14 | C1 con payload completo (estilo S18) → OK | Bloque 4 |
| 15 | ART-05 con `linked_proformas` de 2 proformas | Bloque 5 — ART-05 |
| 16 | ART-05 con proforma de otro expediente → error | Bloque 5 |
| 17 | `mode_b → mode_c` → void ART-10 | Bloque 6 — change_mode |
| 18 | Marluvas `mode_b → default` → rechazado | Bloque 6 |
| 19 | Sin `confirm_void` → preview, no ejecuta | Bloque 6 |
| 20 | `line_id` inexistente → error | Bloque 7 — line_ids edge cases |
| 21 | Línea ya asignada → error | Bloque 7 |
| 22 | `line_ids` duplicados → dedup, asigna 1 vez | Bloque 7 |
| 23 | Bundle incluye `artifact_policy` | Bloque 8 — Bundle |
| 24 | `parent_proforma` FK en ART-04/09/10 | Bloque 8 |
| 25 | Expediente legacy → C5 falla con mensaje claro | Bloque 8 |
| 26 | `mode_b` para Rana Walk → error | Bloque 9 — BRAND_ALLOWED_MODES |
| 27 | Rana Walk `default → mode_c` → rechazado | Bloque 9 |
| 28 | Brand desconocida CON proformas → fallback | Bloque 9 |
| 29 | `line_ids=null` → lista vacía, no explota | Bloque 10 — Edge cases |
| 30 | `line_ids="string"` → error de tipo | Bloque 10 |
| 31 | `mode_c → mode_b` → void ART-09 | Bloque 10 |
| 32 | `line_ids=[True]` → error booleanos | Bloque 10 |
| 33 | `line_ids=["1"]` → error solo enteros | Bloque 10 |
| 34 | Brand desconocida → `create_proforma` error | Bloque 10 |
| 35 | Brand desconocida → `change_mode` error | Bloque 10 |

**Fix final:**
- Commit [`9603d89`](https://github.com/Ale241302/mwt_one/commit/9603d8978dbc496946d4b0b9710c05a8947ea852) — Corregido `sku='SKU-001'` → `sku_base='SKU-001'` y añadido `brand=cls.brand_marluvas` en `ProductMaster.objects.create()` del `setUpTestData`.

**Fix btree_gist:**
- Commit [`df6f123`](https://github.com/Ale241302/mwt_one/commit/df6f123e3a3084636b523247519a01ecc6c8526b) — Se añadió extensión `btree_gist` en migración de `agreements` para soportar `ExclusionConstraints` sobre `CharField` en el test runner.

**Criterio de done alcanzado:**
- 35 tests ✅
- Todos verdes ✅
- 0 regresiones en tests legacy ✅

---

## Resumen de archivos por acción

### Archivos creados
| Archivo | Tarea | Descripción |
|---------|-------|-------------|
| `backend/apps/expedientes/services/artifact_policy.py` | S20-05 | `BRAND_ALLOWED_MODES`, `ARTIFACT_POLICY`, `resolve_artifact_policy()` |
| `backend/apps/expedientes/services/proforma_mode.py` | S20-10 | `change_proforma_mode()` con void automático |
| `backend/apps/expedientes/views_s20.py` | S20-07/11 | `ProformaCreateView` |
| `backend/apps/expedientes/tests/test_proformas.py` | S20-12 | 35 tests completos |
| `backend/apps/expedientes/migrations/0019_s20_proforma_fks.py` | S20-01/02 | Migración aditiva: 2 FK nullables |

### Archivos modificados
| Archivo | Tareas | Qué cambió |
|---------|--------|------------|
| `backend/apps/expedientes/models.py` | S20-01, S20-02 | FK `proforma` en EPL; FK `parent_proforma` en ArtifactInstance |
| `backend/apps/expedientes/serializers.py` | S20-03, S20-04, S20-06 | Validación ART-05 linked_proformas; validación mode ART-02; `artifact_policy` en BundleSerializer |
| `backend/apps/expedientes/views.py` | S20-09, S20-10, S20-11 | Actions `reassign_line`, `create_proforma`; endpoint `change-mode` |
| `backend/apps/expedientes/urls.py` | S20-09, S20-11 | Rutas `proformas/` y `change-mode/` registradas |
| `backend/apps/expedientes/urls_ui.py` | S20-07 | Ruta `artifacts/proforma/` registrada |
| `backend/apps/expedientes/admin.py` | S20-01 | Inline EPL muestra campo `proforma` |
| `backend/apps/expedientes/services/state_machine/c_create.py` | S20-07 | C1 solo requiere `client_id` + `brand_id` |
| `backend/apps/expedientes/services/state_machine/` (C5 gate) | S20-08 | Validación proformas + líneas asignadas + modos |

### Archivos eliminados
| Archivo | Razón |
|---------|-------|
| Migración `0020` (nombre incorrecto) | Reemplazada por `0019_s20_proforma_fks` |

---

## Decisiones técnicas tomadas en Sprint 20

| Ref | Decisión | Razón |
|-----|----------|-------|
| SG-01 | `ArtifactPolicy` como constante Python en `artifact_policy.py` | Iterar rápido sin UI de configuración. Migra a DB (`BrandWorkflowPolicy`) en Sprint 23. |
| SG-04 | ART-05 multi-proforma vía array en payload JSON | No se crea modelo M2M explícito — el payload ya es `JSONField`. |
| SG-05 | Void automático por cambio de modo con `confirm_void` | Evitar accidental data loss. El preview muestra qué se voidea antes de confirmar. |
| SG-06 | `operated_by` = siempre `"muito_work_limitada"` por ahora | Si aparece otra subsidiaria, se migra. |
| HR-13 | C1 flexible: solo `client_id` + `brand_id` | OC, líneas y proformas son opcionales en creación. |
| HR-8/9 | Mode a nivel proforma (`payload.mode` de ART-02) | Permite proformas mixtas en el mismo expediente. |

---

## Excluido de Sprint 20 (diferido)

| Feature | Sprint objetivo |
|---------|-----------------|
| Frontend de proformas (vista CEO) | Sprint 20B |
| Vista portal cliente (OC → líneas) | Sprint 20B |
| Eliminar `STATE_ARTIFACTS` del frontend | Sprint 20B |
| Emails/notificaciones | Sprint 21 |
| `BrandWorkflowPolicy` en DB con UI admin | Sprint 23 |
| Flujo B completo (portal → ART-01 auto) | Sprint 24 |

---

## Lecciones aplicadas de sprints anteriores

1. **Migración additive-only:** Verificada con `sqlmigrate` antes de aplicar. 0 `AlterField`, 0 `RemoveField`.
2. **`transaction.atomic()` + `select_for_update()`** en todos los endpoints mutantes de proformas.
3. **Una sola fuente de verdad:** `BRAND_ALLOWED_MODES` centralizada en `artifact_policy.py` — no duplicada en endpoints.
4. **Backward compat como test:** Tests 13 y 14 explícitamente validan que payloads de S18 siguen funcionando.
5. **EventLog en todo:** `reassign-line`, `create_proforma`, `change_proforma_mode` generan EventLog.
6. **`old_mode`/`old_proforma_id` capturados ANTES del cambio** (no después del `save()`).
