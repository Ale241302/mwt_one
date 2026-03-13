# PLB_ORCHESTRATOR — Protocolo de Orquestación Multi-Agente MWT
status: FROZEN — Aprobado para Sprint 0-1
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
version: 1.2.2 (FINAL)
tipo: Playbook (instrucción operativa)
refs: ENT_OPS_STATE_MACHINE, MWT_ARCHITECTURE_PACKAGE, ENT_PLAT_MODULOS, ENT_GOB_AGENTES

---

## A. Agentes activos por sprint

### A1. Sprint 0-1 (MVP Expedientes)

| Agente | ID | Playbook | Activo |
|--------|-----|----------|--------|
| Architect | AG-01 | PLB_ARCHITECT | ✅ Sprint 0 |
| DevOps | AG-07 | PLB_DEVOPS | ✅ Sprint 0 |
| API Builder | AG-02 | PLB_API | ✅ Sprint 1 |
| QA | AG-06 | PLB_QA | ✅ Sprint 1 |
| Frontend | AG-03 | PLB_FRONTEND | ❌ Post-MVP |
| Integration | AG-04 | PLB_INTEGRATION | ❌ Post-MVP |
| Migration | AG-05 | PLB_MIGRATION | ❌ Post-MVP (salvo BIZ-06 data histórica) |

### A2. Orquestador

El CEO es el orquestador en MVP. No hay agente Orchestrator automático.

Flujo:
```
CEO decide → crea LOTE con items ruteados → congela versión de docs SSOT → lanza agente(s) → revisa output → aprueba/rechaza → CEO hace merge final
```

**Regla de no-merge:** Ningún agente hace merge final. El agente entrega output/patch. El CEO valida y aprueba integración. Agentes proponen, CEO dispone.

**Regla de freeze:** Un agente trabaja contra la versión de docs SSOT vigente al momento de lanzar el lote. Si un doc SSOT cambia durante ejecución, los items que lo consumían quedan `STALE` y deben revalidarse antes de merge.

Post-MVP: se puede crear AG-00 Orchestrator que descompone decisiones CEO en lotes automáticamente. No invertir en esto ahora.

---

## B. Matriz de dependencias y concurrencia

### B1. Cadena de ejecución (quién va primero)

```
Sprint 0:
  AG-07 DevOps ──→ AG-01 Architect
  (infra)           (modelos)
  
Sprint 1:
  AG-01 Architect ──→ AG-02 API ──→ AG-06 QA
  (modelos estables)  (endpoints)   (tests)
```

Regla: cada agente solo arranca cuando su dependencia está estable. "Estable" = output entregado, validado por CEO, sin cambios pendientes en su scope, y listo para integración. Agentes pueden generar commits de trabajo en branches temporales, pero no hacen merge a main.

### B2. Matriz de concurrencia

| Agente A ↓ / Agente B → | AG-01 Architect | AG-02 API | AG-06 QA | AG-07 DevOps |
|--------------------------|-----------------|-----------|----------|--------------|
| AG-01 Architect | — | ⛔ Espera | 👁 Read-only | ✅ Paralelo |
| AG-02 API | ⛔ Espera | — | 👁 Read-only | ✅ Paralelo |
| AG-06 QA | 👁 Read-only | ⛔ Espera | — | ✅ Paralelo |
| AG-07 DevOps | ✅ Paralelo | ✅ Paralelo | ✅ Paralelo | — |

**Lectura:**
- ✅ Paralelo = pueden correr al mismo tiempo, ambos escriben sin conflicto
- ⛔ Espera = B debe esperar a que A termine su scope antes de escribir
- 👁 Read-only = B puede leer spec/output de A y preparar trabajo, pero NO escribir hasta que A esté estable

**Excepciones:**
- AG-07 DevOps es casi siempre independiente (toca infra, no código de app)
- AG-06 QA en modo 👁 vs AG-01: puede escribir `tests/test_transitions.py` contra la state machine congelada (spec, no código). No puede escribir tests contra modelos que AG-01 aún no generó.

### B3. Regla de conflicto

Si dos agentes necesitan tocar el mismo archivo:
1. El agente con **ownership** (ver sección D) tiene precedencia
2. El otro agente debe esperar o coordinar via lote
3. Si no hay ownership claro → escalar a CEO

---

## C. Scope de lectura y escritura por agente

### C1. AG-01 Architect

**READ_REQUIRED (debe leer antes de actuar):**
- ENT_OPS_STATE_MACHINE — estados, commands, transaction boundaries
- ENT_PLAT_MODULOS — módulos Django, fases
- ENT_COMERCIAL_PRICING — fórmulas que afectan modelos
- ENT_COMERCIAL_COSTOS — estructura CostLine
- POL_INMUTABILIDAD — reglas append-only
- POL_ARTIFACT_CONTRACT — contrato de artefactos

**READ_OPTIONAL (consulta si necesita contexto):**
- MWT_ARCHITECTURE_PACKAGE — visión global
- ENT_OPS_EXPEDIENTE — flujo operativo completo
- ENT_PLAT_LEGAL_ENTITY — modelo LegalEntity

**DO_NOT_USE (no consumir, otro agente lo maneja):**
- ENT_PLAT_DOCKER, ENT_PLAT_INFRA → DevOps
- PLB_API, PLB_QA → otros agentes

**WRITE scope:**
- `apps/*/models.py`
- `apps/*/admin.py`
- `apps/*/apps.py`
- `apps/*/enums.py`
- `apps/*/managers.py`
- migraciones: **genera** (`makemigrations`). AG-07 **aplica** (`migrate`) en entorno/container.
- `config/settings/`: solo `INSTALLED_APPS` y app-specific flags

**NO WRITE:**
- views, serializers, urls (→ AG-02)
- tests (→ AG-06)
- Docker, nginx, deploy (→ AG-07)

### C2. AG-02 API Builder

**READ_REQUIRED:**
- ENT_OPS_STATE_MACHINE §F — command handlers (su input principal)
- POL_VISIBILIDAD — qué campos filtrar por rol
- Modelos generados por AG-01 (output anterior)

**READ_OPTIONAL:**
- ENT_PLAT_EVENTOS — eventos que los endpoints deben emitir
- ENT_PLAT_SEGURIDAD — reglas de acceso

**DO_NOT_USE:**
- ENT_COMERCIAL_PRICING, ENT_COMERCIAL_COSTOS → no toca lógica de negocio, solo expone

**WRITE scope:**
- `apps/*/views.py`
- `apps/*/serializers.py`
- `apps/*/urls.py`
- `apps/*/permissions.py`
- `config/urls.py` (registro de rutas)

**NO WRITE:**
- models.py (→ AG-01)
- tests (→ AG-06)

### C3. AG-06 QA

**READ_REQUIRED:**
- ENT_OPS_STATE_MACHINE §B + §F — transiciones + commands (spec contra la que testear)
- POL_INMUTABILIDAD — invariantes append-only
- Modelos de AG-01 + Endpoints de AG-02 (outputs anteriores)

**READ_OPTIONAL:**
- ARTIFACT_REGISTRY — tipos de artefactos para fixtures
- ENT_PLAT_EVENTOS — eventos esperados

**WRITE scope:**
- `tests/` (todo)
- `tests/factories.py`
- `tests/conftest.py`
- `tests/test_transitions.py`
- `tests/test_commands.py`
- `tests/test_permissions.py`

**NO WRITE:**
- Nada fuera de tests/

### C4. AG-07 DevOps

**READ_REQUIRED:**
- ENT_PLAT_INFRA — stack, capacity planning
- ENT_PLAT_DOCKER — contenedores, compose
- MWT_ARCHITECTURE_PACKAGE §11 — infra y stack

**READ_OPTIONAL:**
- ENT_PLAT_MVP — qué contenedores en MVP vs post-MVP

**WRITE scope:**
- `docker-compose.yml`
- `Dockerfile` (backend, frontend)
- `nginx/`
- `scripts/infra/deploy.sh`, `scripts/infra/backup_db.sh`, `scripts/infra/migrate.sh`
- `.env.template`
- `config/settings/` (solo configuración de infra: DB, Redis, MinIO, Celery)

**NO WRITE:**
- Nada en `apps/` (→ AG-01, AG-02)
- Nada en `tests/` (→ AG-06)

---

## D. Ownership por carpeta

| Carpeta / Archivo | Owner primario | Puede editar | Bajo qué condición |
|-------------------|---------------|-------------|---------------------|
| `apps/*/models.py` | AG-01 Architect | Solo AG-01 | — |
| `apps/*/admin.py` | AG-01 Architect | Solo AG-01 | — |
| `apps/*/views.py` | AG-02 API | Solo AG-02 | Después de AG-01 estable |
| `apps/*/serializers.py` | AG-02 API | Solo AG-02 | Después de AG-01 estable |
| `apps/*/urls.py` | AG-02 API | Solo AG-02 | — |
| `tests/` | AG-06 QA | Solo AG-06 | Después de AG-01 + AG-02 estables, salvo `tests/test_transitions.py` escribible en modo anticipado contra spec congelada |
| `docker-compose.yml` | AG-07 DevOps | Solo AG-07 | — |
| `nginx/` | AG-07 DevOps | Solo AG-07 | — |
| `scripts/infra/` (deploy, backup, migrate) | AG-07 DevOps | Solo AG-07 | — |
| `config/settings/` (DB, Redis, MinIO, Celery, env, logging) | AG-07 DevOps | Solo AG-07 | — |
| `config/settings/` (INSTALLED_APPS, app flags) | AG-01 Architect | Solo AG-01 | Mientras exista un solo base.py, AG-07 y AG-01 no lo editan en paralelo; se serializa por lote. Post-MVP: split a infra.py + apps.py |
| `CLAUDE.md` | CEO | CEO | — |
| `knowledge/` | CEO | Ningún agente | READ-ONLY para todos |

**Regla de excepción:** Si un agente necesita editar fuera de su scope, debe incluirlo como nota en su output y esperar aprobación CEO antes de ejecutar.

---

## E. Formato de lote ruteado (LOTE_*)

Cada lote es una orden de trabajo para uno o más agentes. Formato obligatorio:

```markdown
# LOTE_[ID]_[NOMBRE] — Orden de Trabajo
sprint: N
priority: P0/P1/P2
depends_on: [LOTE anterior si aplica]

## Items

### Item 1: [nombre descriptivo]
- **Agente:** AG-XX
- **Módulo:** apps/[módulo]/
- **Command ref:** C1 CreateExpediente (ref → ENT_OPS_STATE_MACHINE §F)
- **Archivos a tocar:** models.py, enums.py
- **Archivos prohibidos:** views.py, tests/
- **Dependencia previa:** Ninguna / Item X de este lote
- **Criterio de done:** 
  - [ ] Modelo creado con campos especificados
  - [ ] Migración generada sin errores
  - [ ] Admin registrado
- **Tests requeridos:** AG-06 debe generar test_create_expediente después
```

### E2. Versionado de lotes

- Lote original: `LOTE_SM_SPRINT0`
- Si el lote cambia después de lanzado: `LOTE_SM_SPRINT0_v2` (incrementar)
- Si un lote cerrado necesita extensión: `LOTE_SM_SPRINT0_EXT1`
- Si un lote queda STALE y se reabre: mantener mismo nombre + agregar `_REVALIDATED` al status del item afectado
- Lotes viejos no se borran. Se marcan `SUPERSEDED` si se reemplaza por nueva versión.

1. Un lote puede tener items para múltiples agentes, pero cada item tiene exactamente 1 agente responsable
2. Items dentro del mismo lote pueden tener dependencias entre sí
3. Lote completado = todos los items con criterio de done cumplido
4. Si un item falla, los items dependientes se bloquean automáticamente
5. CEO puede aprobar items individuales dentro de un lote (desbloqueando agentes downstream). El lote solo se marca `DONE` cuando todos los items estén aprobados
6. Si un item falla, solo los items con dependencia directa se bloquean — no el lote entero

---

## F. Política de conflictos y precedencia

### F1. Cadena de autoridad sobre el código

```
ENT_OPS_STATE_MACHINE (spec congelada)
  ↓ es verdad canónica para
AG-01 Architect (modelos)
  ↓ es input canónico para
AG-02 API (endpoints)
  ↓ es input canónico para
AG-06 QA (tests)
```

Si hay conflicto entre lo que dice el código y lo que dice la state machine → **la state machine gana**. El agente que divergió debe corregir.

### F2. Qué pasa cuando AG-01 cambia un modelo

| Situación | Acción |
|-----------|--------|
| AG-02 aún no generó endpoints para ese modelo | Sin impacto. AG-02 usa modelo nuevo |
| AG-02 ya generó endpoints | AG-02 debe regenerar serializers/views afectados. CEO decide si es lote nuevo o extensión |
| AG-06 ya generó tests | AG-06 debe actualizar tests. Factories primero |
| AG-07 ya generó migraciones | AG-01 regenera migraciones. AG-07 solo re-deploya |

### F3. Regla de invalidación

Cuando un agente modifica un archivo que es input de otro agente:
1. Marca el output downstream como `STALE`
2. Notifica al CEO (en el lote o en commit message)
3. El agente downstream re-ejecuta contra el nuevo input
4. CEO valida que la cadena esté consistente antes de mergear

### F4. Precedencia en caso de conflicto de verdad

| Nivel | Fuente | Gana sobre |
|-------|--------|-----------|
| 1 | ENT_OPS_STATE_MACHINE (FROZEN) | Todo lo demás |
| 2 | POL_* (policies del sistema) | Código generado |
| 3 | AG-01 Architect (modelos) | AG-02, AG-06 |
| 4 | AG-02 API (endpoints) | AG-06 |
| 5 | AG-07 DevOps (infra) | Independiente — no compite |

---

## G. Primer lote: LOTE_SM_SPRINT0

```markdown
# LOTE_SM_SPRINT0 — Infraestructura Base
sprint: 0
priority: P0
depends_on: ninguno

## Items

### Item 1: Docker Compose MVP + Infra Settings
- **Agente:** AG-07 DevOps
- **Archivos a tocar:** docker-compose.yml, backend/Dockerfile, nginx/mwt.conf, .env.template, config/settings/base.py (DB, Redis, MinIO, Celery, logging, static/media)
- **Archivos prohibidos:** apps/*, tests/*
- **Criterio de done:**
  - [ ] 6 contenedores: django, postgres, nginx, minio, celery-worker, celery-beat
  - [ ] Healthcheck: django healthy, postgres accepting connections, minio healthy, celery worker registered, celery beat running
  - [ ] mwt.one responde en navegador (SSL si DNS listo, HTTP si no)
  - [ ] Django admin accesible
  - [ ] MinIO console accesible
  - [ ] config/settings/base.py con PostgreSQL, MinIO, Celery, Redis config

### Item 2: Django Project Init + Core Base
- **Agente:** AG-01 Architect
- **Dependencia previa:** Item 1 (stack + settings infra listos)
- **Archivos a tocar:** config/settings/base.py (solo INSTALLED_APPS), config/urls.py, apps/core/models.py, apps/core/apps.py
- **Archivos prohibidos:** docker-compose.yml, nginx/*, config/settings/base.py (secciones de infra)
- **Criterio de done:**
  - [ ] Django project estructura apps/ creada
  - [ ] INSTALLED_APPS actualizado con core
  - [ ] TimestampMixin, AppendOnlyModel en apps/core/models.py
  - [ ] manage.py funciona dentro del contenedor
  - [ ] Migración core generada

### Item 3: Modelos LegalEntity + Expediente
- **Agente:** AG-01 Architect
- **Dependencia previa:** Item 2
- **Command ref:** C1 CreateExpediente, state machine §A (enums)
- **Archivos a tocar:** apps/expedientes/models.py, apps/expedientes/enums.py, apps/expedientes/apps.py, apps/expedientes/admin.py
- **Archivos prohibidos:** views.py, serializers.py, tests/*
- **Criterio de done:**
  - [ ] LegalEntity model con campos de ENT_PLAT_LEGAL_ENTITY.B
  - [ ] Expediente model con: status enum (8 estados), is_blocked + campos bloqueo, payment_status, credit_clock_start_rule
  - [ ] Migraciones generadas sin errores
  - [ ] Admin registrado

### Item 4A: Modelos Artifact + Outbox (ArtifactInstance, EventLog)
- **Agente:** AG-01 Architect
- **Dependencia previa:** Item 3
- **Command ref:** State machine §K (outbox), §E (artifacts)
- **Archivos a tocar:** apps/expedientes/models.py (extend), apps/expedientes/managers.py
- **Archivos prohibidos:** views.py, serializers.py, tests/*
- **Criterio de done:**
  - [ ] ArtifactInstance model (type, status, payload jsonb, expediente FK)
  - [ ] EventLog model (outbox) con 10 campos de state machine §K
  - [ ] Migraciones generadas sin errores
  - [ ] Admin registrado

### Item 4B: Modelos Ledger (CostLine, PaymentLine)
- **Agente:** AG-01 Architect
- **Dependencia previa:** Item 3
- **Command ref:** State machine §F2 (CostLine), §L1 (PaymentLine)
- **Archivos a tocar:** apps/expedientes/models.py (extend)
- **Archivos prohibidos:** views.py, serializers.py, tests/*
- **Criterio de done:**
  - [ ] CostLine model (AppendOnlyModel) con campos de §F2
  - [ ] PaymentLine model (AppendOnlyModel) con campos de §L1
  - [ ] Migraciones generadas sin errores
  - [ ] Admin registrado

### Item 5: AG-07 aplica migraciones en entorno
- **Agente:** AG-07 DevOps
- **Dependencia previa:** Items 2, 3, 4A, 4B (migraciones generadas)
- **Archivos a tocar:** scripts/infra/migrate.sh (si aplica)
- **Criterio de done:**
  - [ ] `python manage.py migrate` corre sin errores en container
  - [ ] Tablas creadas verificables en PostgreSQL
  - [ ] Superuser creado para CEO
```

---

## I. Formato de output obligatorio por agente

Todo agente, al completar un item de un lote, debe entregar este reporte:

```markdown
## Resultado de ejecución
- **Agente:** AG-XX [nombre]
- **Lote:** LOTE_...
- **Item:** #N — [nombre]
- **Status:** DONE / PARTIAL / BLOCKED / STALE
- **Archivos creados:** [lista]
- **Archivos modificados:** [lista]
- **Archivos NO tocados (fuera de scope):** [confirmar]
- **Decisiones asumidas:** [lista de cualquier decisión local que el agente tomó sin instrucción explícita]
- **Blockers:** [lista, o "ninguno"]
- **Tests ejecutados:** [si aplica, o "pendiente AG-06"]
- **Siguiente agente desbloqueado:** AG-XX para Item #N
```

**Reglas:**
- Status `DONE` = todos los criterios de done cumplidos
- Status `PARTIAL` = algunos criterios cumplidos, otros bloqueados. Listar cuáles
- Status `BLOCKED` = no pudo avanzar. Razón obligatoria
- Status `STALE` = un input SSOT cambió durante ejecución. Revalidar antes de merge
- "Decisiones asumidas" es crítico: si el agente inventó algo que no estaba en la spec, debe declararlo aquí para que CEO valide

---

## J. Definition of Stable + Stale

### J1. Cuándo un scope está ESTABLE

Un agente completó su scope de forma estable cuando:
1. Output entregado según criterio de done del item
2. No hay blockers abiertos en su output
3. No hay cambios pendientes dentro de su ownership
4. CEO aprobó el item (revisó reporte §I)
5. Output listo para integración (merge por CEO)

Solo cuando un scope está estable, los agentes downstream pueden empezar a escribir.

### J2. Cuándo un output está STALE

Un output queda STALE cuando:
1. Un doc SSOT que el agente consumió (READ_REQUIRED) cambió después de que el agente empezó
2. Un archivo owner de otro agente que era input cambió después de generar el output
3. El CEO modificó el lote o las precondiciones después del lanzamiento

**Acción:** Item STALE no se mergea. Se revalida contra input actualizado. Si el cambio no afecta el output, CEO puede marcar como válido sin re-ejecutar.

### J3. Regla de granularidad de lote

Un item de lote no debe mezclar más de una responsabilidad estructural:
- ✅ "Crear modelo Expediente" — 1 responsabilidad
- ✅ "Generar endpoints para C1-C5" — 1 responsabilidad (varios commands, mismo agente, mismo módulo)
- ❌ "Crear modelo + endpoints + tests" — 3 responsabilidades, 3 agentes
- ❌ "Crear Expediente + LegalEntity + ArtifactInstance + EventLog" — demasiados modelos en 1 item

Regla: si un item tiene más de 5 criterios de done, probablemente debe dividirse.

---

## K. CLAUDE.md (archivo raíz del repo)

Este es el contenido que debe vivir en la raíz del repositorio como puerta de entrada para cualquier agente:

```markdown
# MWT.ONE — Centro de Operaciones
# Instrucciones para Claude Code / Agentes IA

## Proyecto
Plataforma de comercio exterior. Backend Django + Frontend Next.js.
CEO opera directamente. MVP: gestión de expedientes de importación Marluvas.

## Stack MVP
- Backend: Django 5.x + DRF
- DB: PostgreSQL 16
- Storage: MinIO
- Task queue: Celery + Redis (solo Beat en MVP)
- Frontend: Next.js (mwt.one) — post Sprint 3
- Reverse proxy: Nginx
- Containers: Docker Compose
- Server: Hostinger KVM 8

## Agentes activos
Ver PLB_ORCHESTRATOR para scope, ownership y reglas de concurrencia.

| Agente | Playbook | Scope |
|--------|----------|-------|
| Architect | agents/01_architect.md | Modelos, migraciones, admin |
| API Builder | agents/02_api_builder.md | Endpoints, serializers, permisos |
| QA | agents/06_test_qa.md | Tests unitarios e integración |
| DevOps | agents/07_devops.md | Docker, nginx, deploy |

## Reglas globales
1. **SSOT:** Cada dato tiene UNA versión canónica (ref → POL_DETERMINISMO)
2. **Vacío explícito:** Dato que no existe = [PENDIENTE — NO INVENTAR]. DETENERSE.
3. **Inmutabilidad:** Ledgers append-only. No update, no delete (ref → POL_INMUTABILIDAD)
4. **Spec canónica:** ENT_OPS_STATE_MACHINE es la verdad del dominio. Si el código diverge, el código está mal.
5. **Ownership:** Cada archivo tiene un agente owner. No editar fuera de tu scope sin aprobación.
6. **No invención:** Si falta dato normativo, no inventar. Marcar [SPEC_GAP] y detenerse.
7. **Output acotado:** Cada agente solo produce output dentro de su scope y en los archivos permitidos por PLB_ORCHESTRATOR.
8. **No merge:** Ningún agente hace merge final. Entrega output/patch. CEO valida e integra.

## Convenciones
- Python: Black, isort, flake8
- Commits: Conventional Commits (feat:, fix:, refactor:)
- Todo modelo hereda TimestampMixin (created_at, updated_at)
- Enums como TextChoices, nunca strings sueltos
- Tests: pytest + factory_boy

## Documentos de referencia
| Documento | Contenido |
|-----------|-----------|
| knowledge/ENT_OPS_STATE_MACHINE.md | State machine + 21 commands + transaction boundaries (FROZEN) |
| knowledge/MWT_ARCHITECTURE_PACKAGE.md | Arquitectura completa 13 secciones |
| knowledge/ARTIFACT_REGISTRY.md | 18 artefactos del sistema |
| knowledge/POL_ARTIFACT_CONTRACT.md | Contrato normativo de artefactos |
```

---

Stamp: FROZEN v1.2.2 — Aprobado para Sprint 0-1
Origen: Análisis multi-agente Ale/Antigravity + 4 rondas audit ChatGPT — sesión 2026-02-26
