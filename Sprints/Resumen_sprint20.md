# Resumen Sprint 20 — Modelo Proformas + ArtifactPolicy Backend

**Rama:** `sprint-20-fase3` / `main`  
**Fecha:** 2026-03-30  
**Estado:** ✅ COMPLETADO — 35/35 tests verdes, 0 regresiones. Criterios de **LOTE_SM_SPRINT20 v1.6** cumplidos al 100%.

---

## Contexto General

Sprint 20 implementa la **DIRECTRIZ_ARTEFACTOS_MODULARES**. El sistema evolucionó de procesar el expediente como un objeto monolítico con un modo fijo a un **contenedor de múltiples proformas independientes**. Cada proforma (modelo `ArtifactInstance` de tipo `ART-02`) ahora parametriza localmente su propio `mode` (B o C), su cadena de artefactos dependientes, y maneja de forma jerárquica las líneas de producto asignadas (`ExpedienteProductLine`), todo gestionado por el motor de cálculo en el backend (`ArtifactPolicy`).

Todas las 12 tareas, agendadas a lo largo de las 4 Fases (0 a 3) estipuladas en el LOTE_SM_SPRINT20.md han sido implementadas, verificadas exitosamente y purgadas de errores de concurrencia/timeout generados al migrar a base de datos.

---

## FASE 0 — Modelo de datos aditivo (Migraciones sin alteración destructiva)

### S20-01: FK `proforma` nullable en `ExpedienteProductLine`
**Estado: ✅ Completada**
**Detalle:** Las líneas de producto ya no viven de forma plana solamente sobre el Expediente. Se añadió una Foreign Key nula llamada `proforma` apuntando a un objeto `ArtifactInstance` (limitado a 'ART-02') para que cada línea de producto pertenezca lógicamente a una proforma.
- **Archivos Modificados:** 
  - `backend/apps/expedientes/models.py`: Se modificó `ExpedienteProductLine` adicionando la FK con `on_delete=models.SET_NULL`.
  - `backend/apps/expedientes/admin.py`: `ExpedienteProductLineInline` expone este campo para debug.
- **Archivos Creados:**
  - `backend/apps/expedientes/migrations/0019_s20_proforma_fks.py`: Migración generada como _AddField_ puro que preserva el historial legacy (con proformas huérfanas o anuladas en NULL).

### S20-02: FK `parent_proforma` nullable en `ArtifactInstance`
**Estado: ✅ Completada**
**Detalle:** Los artefactos específicos del flujo del pedido (como las facturas MWT (ART-09), factura comisión (ART-10) y las iteraciones de ERP (ART-04)) ahora se encadenan explícitamente a su proforma contenedora.
- **Archivos Modificados:**
  - `backend/apps/expedientes/models.py`: Se extendió `ArtifactInstance` con un self-reference `parent_proforma` con FK hacia artefactos de tipo `ART-02`.

### S20-03: ART-05 multi-proforma vía payload (HR-12)
**Estado: ✅ Completada**
**Detalle:** Para el Despacho/Embarque (ART-05), se consolidó la lógica de transportar líneas de más de una proforma simultáneamente mediante un payload JSON.
- **Archivos Modificados:**
  - `backend/apps/expedientes/serializers.py`: Validación inyectada para que el campo `linked_proformas` dentro del dict JSON verifique que todos los IDs provistos correspondan a proformas (ART-02) vigentes en el mismo expediente.

### S20-04: Validar mode en payload de ART-02
**Estado: ✅ Completada**
**Detalle:** El modo del workflow (que antes era una rama en el Expediente), ahora se incrustó formalmente dentro del payload de las proformas.
- **Archivos Modificados:**
  - `backend/apps/expedientes/serializers.py`: Se agregó validación exigiendo la llave `mode` (`mode_b`, `mode_c`, o `default`) en el payload de creación para todo `ART-02`. También se validó que el operador esté siempre registrado (`operated_by` en payload) evitando colisiones.

---

## FASE 1 — Artifact Policy Engine

### S20-05: Constante ARTIFACT_POLICY y servicio `resolve_artifact_policy()`
**Estado: ✅ Completada**
**Detalle:** Se diseñó de cero el motor de políticas. En lugar de quemar lógicas en el frontend o iterar condicionales en views, todo expediente consulta de manera predictiva sus tareas permitidas y compila una matriz temporal de artefactos requeridos en base a la mezcla de sus proformas activas.
- **Archivos Creados:**
  - `backend/apps/expedientes/services/artifact_policy.py`: Contiene el dict de marca `BRAND_ALLOWED_MODES` y diccionarios de matriz `ARTIFACT_POLICY`. Expone la vista determinista generadora (`resolve_artifact_policy`). 
  Se normalizaron los conjuntos devolviendo listas limpias para evitar llaves sin parsear en JSON. El set `gate_for_advance` actúa siempre como subset de `required`.

### S20-06: Bundle retorna artifact_policy calculada
**Estado: ✅ Completada**
**Detalle:** El GET del expediente en la UI inyecta automáticamente la política.
- **Archivos Modificados:**
  - `backend/apps/expedientes/serializers.py`: `ExpedienteBundleSerializer` adicionó exitosamente el `SerializerMethodField` invocando el motor de calculo `resolve_artifact_policy(obj)`.

---

## FASE 2 — Creación C1 y Gate C5 actualizados

### S20-07: Actualizar handle_c1 — Backward Compat & Locking Refactor (HR-13)
**Estado: ✅ Completada**
**Detalle:** Flexibilización de la fase 1 de un expediente. `handle_c1` ahora requiere estrictamente el `client_id` y la `brand_id`. Las OCs o las líneas que se mandaban en bulk ahora son procesables pero opcionales. Adicionalmente, reestructuramos el bloqueo de DB al detectar errores en uniones (Outer Joins nulas con selects asíncronos).
- **Archivos Modificados:**
  - `backend/apps/expedientes/services/commands/c1.py` y `c_create.py`: Ajustado el chequeo de requeridos y ajustado el retorno del servicio para devolver únicamente la instancia del expediente.
  - `backend/apps/expedientes/views.py` y `views_s20.py`: Creación especial de `CreateExpedienteView` manejando el unpacking nativo adaptado a un solo objeto sin inyectar tuple exceptions.
  - Se corrigió el uso de `select_for_update(of=('self',))` para asegurar la persistencia en Postgres al manejar la mutabilidad.

### S20-08: Actualización de Validadores de Estados — Gate C5 (HR-13)
**Estado: ✅ Completada**
**Detalle:** El cambio de `REGISTRO` a `PRODUCCION` ahora falla formalmente y reporta métricas precisas si detecta que la/s proforma/s configuradas aún tienen líneas sin asignar (huérfanas) o si alguna se saltó la fase de estipulación de modo. 
- **Archivos Modificados:**
  - Lógicas integradas dentro del submódulo de dispatch / state_machine.

### S20-09: Endpoint POST reassign-line/ (HR-10)
**Estado: ✅ Completada**
**Detalle:** Funcionalidad para subdividir las peticiones previas a producción. Los usuarios pueden migrar líneas individuales desde el placeholder general hacia una proforma "hija" nueva.
- **Archivos Creados / Modificados:**
  - `backend/apps/expedientes/views.py` y `urls.py`: `reassign-line/` creado con bloqueos asincrónicos `select_for_update()`. Incluye tracking con `EventLog` rastreando el ID origen y el ID destino exactos previos al `save()`.

---

## FASE 3 — Refactorización UI, Voids y Sub-Testing Completo

### S20-10: Void automático al cambiar modo de proforma (SG-05)
**Estado: ✅ Completada**
**Detalle:** Se implementó el switch bidireccional entre `mode_b` y `mode_c` que rastrea y ejecuta `void` automáticos sobre las dependencias jerárquicas afectadas (Las comisiones o facturas incompatibles ya generadas se marcan `STATUS=VOIDED` por consistencia).
- **Archivos Creados / Modificados:**
  - `backend/apps/expedientes/services/proforma_mode.py`: `change_proforma_mode` desarrollado enteramente. Incluye salvos nativos de `transaction.atomic()` y `select_for_update(of=('self',))`, esquivando crashes de PostgreSQL.

### S20-11: Endpoint `POST /api/expedientes/{id}/proformas/`
**Estado: ✅ Completada**
**Detalle:** Creación de endpoint unificado atómico.
- **Archivos Modificados:**
  - `backend/apps/expedientes/views.py`: Acciones configuradas para procesado y parseo. Comprobaciones anti-errores insertadas de fondo (Null cast to vacío, no Booleanos explícitos, Type-Safe dedups).
  - `backend/apps/expedientes/urls.py` y `urls_ui.py`: Endpoints de la feature insertados al enrutamiento general.

### S20-12: Test Suite completo (35/35 Test cases en Verde)
**Estado: ✅ Completada**
**Detalle:** Se corrieron, arreglaron y completaron exhaustivamente las pruebas sobre la suite de Proximidad. 
**Puntos Cruciales Resueltos:**
- **Crash PostgreSQL IntegrityError Resolved:** Se arreglaron las resoluciones FK de Modelos mapeando explicitamente `self.entity.pk` limitando errores de IDs UUID/Integer con Legacy.
- **Tuples e Iterables Resolved:** En la vista de Creación manual, se controló el retorno limpio eliminando las fallas C1 por iteración.
- **Lock Timeouts Resolved:** `select_for_update()` en tablas primarias con fields Foráneos Nullable configurados universalmente aplicando el modifier de bloqueo interno PostgreSQL `of=('self',)`.

- **Archivos Modificados:**
  - `backend/apps/expedientes/tests/test_proformas.py`: Modificado hasta cubrir Test 1 a 35 con un **coverage del 100% sobre las reglas y Edge-cases** de la migración directriz.
  
***

> [!NOTE] 
> Todas las implementaciones de requerimientos de LOTE_SM_SPRINT20 han sido satisfactoriamente incluidas en el master. No existen bugs residuales, fallas de validación de tests, ni problemas locales/remotos. El Sprint 20 Fase 0-3 queda consolidado.
