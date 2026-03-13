# ASANA_TASK_SPRINT8.md
# Sprint 8 — Auth + Knowledge Container
# Generado: 2026-03-13 | Fuente: LOTE_SM_SPRINT8_v3_15.md + GUIA_SPRINT8_ALEJANDRO.md
# Repositorio: https://github.com/Ale241302/mwt_one
# Notion: https://www.notion.so/da371f66c043401b823996e8e23efaf5?v=d9cbefcb5b5246cd8e5e9fa1051bac7d

---

## PILAR A — IDENTIDAD

### S8-01 · MWTUser — Modelo + Migración CEO
- **Agente:** AG-02 API Builder
- **Item:** Item 1
- **Sprint:** Sprint 8
- **Estado:** Pendiente
- **Branch:** feature/s8-01-mwtuser
- **Dependencia:** Verificación 1 (grep FKs auth.User), Verificación 2 (FKs contrib), Verificación 3 (Celery Beat scheduler)
- **Descripción:**
  Crear app `users`, definir modelo `MWTUser` extendiendo `AbstractUser` con campos: `role`, `legal_entity` (FK a LegalEntity existente Sprint 5), `whatsapp_number`, `is_api_user`, `created_by` (FK self). Activar `AUTH_USER_MODEL = 'users.MWTUser'` en settings.py. Generar migración `0001_initial` y data migration `0002_migrate_ceo` que copia el CEO actual preservando PK, asigna `role='CEO'`, `is_api_user=True` y crea todos sus `UserPermission`. Generar y aplicar migraciones de apps con FK a `auth.User` (EventLog, ArtifactInstance, Transfer).
- **Criterios de Éxito:**
  - [ ] App `users` creada
  - [ ] `MWTUser` con todos los campos incluyendo FK a `LegalEntity` existente
  - [ ] `AUTH_USER_MODEL = 'users.MWTUser'` activo
  - [ ] CEO migrado con `role=CEO`, `is_api_user=True`, todos sus `UserPermission`
  - [ ] PK preservado: `MWTUser.objects.get(username=CEO_USERNAME).id == old_auth_user.id`
  - [ ] Migraciones FKs apps existentes aplicadas
  - [ ] `python manage.py check` sin errores
  - [ ] Login CEO en consola funciona post-migración
  - [ ] Admin login funciona con `MWTUser`
- **Riesgos:**
  - Swap de `AUTH_USER_MODEL` rompe FKs existentes si no se hace en orden correcto
  - Histórico `django_admin_log` queda con FK huérfana (aceptable en Sprint 8)

---

### S8-02 · UserPermission — Modelo + Validación Techo
- **Agente:** AG-02 API Builder
- **Item:** Item 2
- **Sprint:** Sprint 8
- **Estado:** Pendiente
- **Branch:** feature/s8-01-mwtuser
- **Dependencia:** Item 1 aprobado
- **Descripción:**
  Modelo `UserPermission` con FK a `MWTUser`, campo `permission` con choices `Permission`, FK `granted_by`, campo `granted_at` auto_now_add. `unique_together = ('user', 'permission')`. Validación en `save()`: permiso fuera del techo del rol lanza `ValidationError`. CEO tiene sus 8 permisos pre-asignados desde `users/0002`.
- **Criterios de Éxito:**
  - [ ] Modelo creado y migrado (en mismo `0001_initial` con MWTUser)
  - [ ] `save()` valida techo de rol
  - [ ] CEO tiene todos sus permisos (creados por `users/0002`)
- **Riesgos:**
  - Validación techo mal implementada podría bloquear la data migration del CEO

---

### S8-03 · JWT Extendido — Serializer + Guardia is_api_user
- **Agente:** AG-02 API Builder
- **Item:** Item 3
- **Sprint:** Sprint 8
- **Estado:** Pendiente
- **Branch:** feature/s8-03-jwt-extended
- **Dependencia:** Item 1 aprobado
- **Descripción:**
  Extender el JWT de Sprint 0 (endpoint `POST /api/auth/token/` ya existe — NO crear nuevo). Crear `MWTTokenObtainPairSerializer` que añade al payload: `role`, `legal_entity_id`, `permissions[]` (preservando `user_id` de Sprint 0). Guardia `is_api_user` en `validate()`: si `is_api_user=False` → `AuthenticationFailed` 401 antes de devolver tokens. Configurar `SIMPLE_JWT`: `ACCESS_TOKEN_LIFETIME=8h`, `REFRESH_TOKEN_LIFETIME=30d`, `ALGORITHM=HS256`.
- **Criterios de Éxito:**
  - [ ] View `POST /api/auth/token/` usa `MWTTokenObtainPairSerializer`
  - [ ] JWT payload incluye `user_id` (Sprint 0, preservado), `role`, `legal_entity_id`, `permissions[]`
  - [ ] `is_api_user=False` → 401 `AuthenticationFailed`
  - [ ] Test: access token emitido contiene todos los claims
  - [ ] Sesión web CEO no se toca
- **Riesgos:**
  - No reordenar la secuencia autenticar→guardia→devolver tokens
  - Guardia con `PermissionDenied` (403) es incorrecto — debe ser `AuthenticationFailed` (401)

---

### S8-04 · Decoradores @require_permission (Session + JWT)
- **Agente:** AG-02 API Builder
- **Item:** Item 4
- **Sprint:** Sprint 8
- **Estado:** Pendiente
- **Branch:** feature/s8-03-jwt-extended
- **Dependencia:** Items 1-3 aprobados
- **Descripción:**
  Implementar `require_permission` (Camino A — Session, para `/api/admin/`) y `require_permission_jwt` (Camino B — JWT sin DB lookup, para `/api/knowledge/`). Crear mixins class-based equivalentes `PermissionRequiredMixin` y `JWTPermissionRequiredMixin` en `apps/users/mixins.py`.
- **Criterios de Éxito:**
  - [ ] Ambos decoradores implementados
  - [ ] Mixins class-based equivalentes
  - [ ] Endpoints `/api/knowledge/` usan exclusivamente `require_permission_jwt`
- **Riesgos:**
  - Confundir Camino A (session) y Camino B (JWT)
  - `request.auth.get()` es la interfaz correcta para JWT — nunca `getattr`

---

### S8-05 · API Admin Usuarios — CRUD + Permisos
- **Agente:** AG-02 API Builder
- **Item:** Item 5
- **Sprint:** Sprint 8
- **Estado:** Pendiente
- **Branch:** feature/s8-05-admin-users-api
- **Dependencia:** Items 1-4 aprobados
- **Descripción:**
  Auth: Session + `MANAGE_USERS`. Endpoints:
  - `POST /api/admin/users/` — crear usuario con cero UserPermission
  - `GET /api/admin/users/` — listar
  - `GET /api/admin/users/{id}/` — detalle
  - `GET /api/admin/users/{id}/permissions/` — ver permisos
  - `PATCH /api/admin/users/{id}/permissions/` — reemplazar permisos (accepted = requested ∩ ceiling, rejected = requested - ceiling)
  Guardia last admin: si el reemplazo dejaría plataforma sin `MANAGE_USERS` → 400 `cannot_remove_last_manage_users`.
- **Criterios de Éxito:**
  - [ ] CRUD usuarios funcionando
  - [ ] Password hasheado con `make_password()`
  - [ ] `legal_entity_id` valida contra LegalEntity existente
  - [ ] Usuario nuevo creado con cero UserPermission
  - [ ] Cada UserPermission insertado tiene `granted_by=request.user`
  - [ ] Self-patch CEO quitando `MANAGE_USERS` → 400
  - [ ] Patch a tercero que dejaría plataforma sin `MANAGE_USERS` → 400
  - [ ] Response PATCH incluye `permissions_applied` y `permissions_rejected`
- **Riesgos:**
  - Guardia last admin debe verificar antes de cualquier write
  - PATCH debe ser transacción atómica (DELETE todos + INSERT accepted)

---

### S8-06 · ConversationLog + Retención + Signal + Beat Task
- **Agente:** AG-02 API Builder
- **Item:** Item 6
- **Sprint:** Sprint 8
- **Estado:** Pendiente
- **Branch:** feature/s8-06-conversation-log
- **Dependencia:** Item 1 aprobado
- **Descripción:**
  Modelo `ConversationLog` en `apps/knowledge/models.py` con campos: `session_id`, `user` FK MWTUser, `user_role`, `expediente_ref` FK Expediente (null), `question`, `answer`, `chunks_used` JSONField, `created_at`, `retain_until`. Función `calculate_retention()` en `apps/knowledge/utils.py` como única fuente de verdad. Signal `post_save` en Expediente con `transaction.on_commit()` para actualizar `retain_until` cuando `status=CERRADO`. Task `purge_expired_logs` en `app.conf.beat_schedule` crontab 3am diario. **Eliminar `--scheduler DatabaseScheduler` de `celery-beat` en este mismo PR.**
- **Criterios de Éxito:**
  - [ ] Modelo `ConversationLog` creado y migrado
  - [ ] `calculate_retention()` en `utils.py`
  - [ ] Signal con `transaction.on_commit()` — no sin él
  - [ ] `purge_expired_logs` en `app.conf.beat_schedule` junto a tasks existentes Sprint 2
  - [ ] `--scheduler DatabaseScheduler` eliminado de `docker-compose.yml`
  - [ ] `docker compose logs celery-beat` muestra 3 tasks
  - [ ] Índice `(retain_until, created_at)` creado
- **Riesgos:**
  - Signal sin `on_commit()` → condición de carrera con signal Transfer Sprint 5
  - D-09: conversaciones en expediente BLOQUEADO son **permitidas** — no agregar verificación de estado
  - Invariante: `status=CERRADO` requiere `closed_at` NOT NULL

---

## PILAR B — KNOWLEDGE

### S8-07 · mwt-knowledge — Servicio FastAPI + pgvector + Indexer
- **Agente:** AG-02 API Builder
- **Item:** Item 7
- **Sprint:** Sprint 8
- **Estado:** Pendiente
- **Branch:** feature/s8-07-knowledge-service
- **Dependencia:** Item 6 aprobado (ConversationLog existe)
- **Descripción:**
  Nuevo servicio `mwt-knowledge` (FastAPI) en directorio `knowledge/`. `CREATE EXTENSION IF NOT EXISTS vector` en DB `mwt`. Modelo `knowledge_chunks` (id, file_path, chunk_index, content TEXT, embedding vector(1536), kb_visibility, metadata JSONB, indexed_at). Indexer recorre `.md` del KB en `/kb/`, hace skip de `visibility=CEO-ONLY`, chunking por secciones, llama `text-embedding-3-small` de OpenAI, inserta con upsert `ON CONFLICT (file_path, chunk_index) DO UPDATE`. Base URL: `/api/knowledge/`.
- **Criterios de Éxito:**
  - [ ] `CREATE EXTENSION vector` en DB `mwt`
  - [ ] Tabla `knowledge_chunks` con índice HNSW `(embedding vector_cosine_ops)`
  - [ ] Indexer procesa `.md`, rechaza CEO-ONLY (`reason: ceo_only_excluded`), hace upsert
  - [ ] Archivos con `visibility=CEO-ONLY` no aparecen en `knowledge_chunks`
  - [ ] Servicio arranca en docker-compose
- **Riesgos:**
  - D-06: `CREATE EXTENSION vector` en DB `mwt` no afecta DB `paperless`
  - D-07: `psycopg2-binary>=2.9` en `requirements.txt` de `mwt-knowledge`
  - D-13: CEO-ONLY excluido intencionalmente — no es error de validación

---

### S8-08 · Endpoint POST /api/knowledge/ask/ — Búsqueda Semántica + Claude
- **Agente:** AG-02 API Builder
- **Item:** Item 8
- **Sprint:** Sprint 8
- **Estado:** Pendiente
- **Branch:** feature/s8-08-knowledge-ask
- **Dependencia:** Items 4, 6, 7 aprobados
- **Descripción:**
  Endpoint `POST /api/knowledge/ask/` (auth JWT + `ASK_KNOWLEDGE_OPS|PRODUCTS|PRICING`). Flujo:
  1. Verificar JWT + permiso `ask_knowledge_*` vía `require_permission_jwt`
  2. Recuperar historial multi-turn de Redis (`kw:session:{user_id}:{session_id}`)
  3. Embed pregunta con `text-embedding-3-small`
  4. Búsqueda vectorial en `knowledge_chunks` filtrando por `kb_visibility` vs permissions del usuario
  5. Construir contexto + historial
  6. Llamar Claude `claude-3-5-haiku-20241022` con system prompt
  7. Guardar `ConversationLog`
  8. Actualizar Redis con TTL 30min
  Response: `{answer, session_id, chunks_used}`
- **Criterios de Éxito:**
  - [ ] Auth JWT + permiso
  - [ ] Historial multi-turn funciona
  - [ ] Filtro visibilidad por permisos del usuario
  - [ ] `ConversationLog` guardado por cada request
  - [ ] Redis actualizado con TTL
  - [ ] Expediente BLOQUEADO: `/ask/` funciona normalmente (D-09)
- **Riesgos:**
  - Filtro visibilidad: usuario sin `ask_knowledge_pricing` no ve chunks pricing
  - D-09: NO verificar estado expediente antes de llamar `/ask/`
  - Modelo Claude: `claude-3-5-haiku-20241022` — no cambiar sin aprobación

---

### S8-09 · Endpoint POST /api/knowledge/index/ — Re-indexar KB
- **Agente:** AG-02 API Builder
- **Item:** Item 9
- **Sprint:** Sprint 8
- **Estado:** Pendiente
- **Branch:** feature/s8-09-knowledge-index
- **Dependencia:** Item 7 aprobado
- **Descripción:**
  Endpoint `POST /api/knowledge/index/` (auth JWT + role CEO). Dispara el indexer del KB. Rechaza archivos CEO-ONLY. Devuelve `{files_indexed, chunks_inserted, chunks_skipped, errors[]}`.
- **Criterios de Éxito:**
  - [ ] Solo CEO puede llamarlo (JWT + `role=CEO`)
  - [ ] Indexer se ejecuta y devuelve resumen
  - [ ] Archivos CEO-ONLY en `chunks_skipped` con reason
  - [ ] Sin errores en archivos aceptados
- **Riesgos:**
  - Re-indexar con concurrencia puede duplicar chunks si el upsert no es atómico
  - Usar `ON CONFLICT (file_path, chunk_index) DO UPDATE`

---

### S8-10 · Endpoint GET /api/knowledge/sessions/ — Historial Conversaciones
- **Agente:** AG-02 API Builder
- **Item:** Item 10
- **Sprint:** Sprint 8
- **Estado:** Pendiente
- **Branch:** feature/s8-10-knowledge-sessions
- **Dependencia:** Items 6, 8 aprobados
- **Descripción:**
  Endpoint `GET /api/knowledge/sessions/` (auth JWT). Devuelve lista de sesiones del usuario autenticado desde `ConversationLog`. Paginado. CEO puede ver sesiones de cualquier usuario con param `?user_id=`. Los demás solo ven sus propias sesiones. `GET /api/knowledge/sessions/{session_id}/` devuelve detalle completo.
- **Criterios de Éxito:**
  - [ ] Usuario ve solo sus sesiones
  - [ ] CEO puede filtrar por `user_id`
  - [ ] Paginación funciona
  - [ ] Sesión expirada (`retain_until` pasado) no aparece en el listado
- **Riesgos:**
  - Filtro `retain_until`: excluir logs con `retain_until < hoy` en queries

---

## DEVOPS

### S8-11 · Docker Compose — Servicio mwt-knowledge + pgvector
- **Agente:** AG-07 DevOps
- **Item:** Item 11
- **Sprint:** Sprint 8
- **Estado:** Pendiente
- **Branch:** feature/s8-11-devops-knowledge
- **Dependencia:** Item 7 aprobado
- **Descripción:**
  Agregar servicio `mwt-knowledge` al `docker-compose.yml`. Variables de entorno requeridas: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `DATABASE_URL` (DB mwt), `REDIS_URL`. Verificar que `db` service use `postgres:16` (no `postgres:16-alpine`, para compatibilidad pgvector). Confirmar `EXTENSION vector` en DB `mwt` únicamente. Eliminar `--scheduler DatabaseScheduler` del servicio `celery-beat`.
- **Criterios de Éxito:**
  - [ ] `docker compose up -d` levanta todos los servicios incluyendo `mwt-knowledge`
  - [ ] `mwt-knowledge` puede conectar a DB `mwt` y Redis
  - [ ] `CREATE EXTENSION vector` exitoso
  - [ ] `celery-beat` sin `--scheduler DatabaseScheduler`
- **Riesgos:**
  - D-06: pgvector aplica por DB, no por servidor
  - D-07: `psycopg2-binary` en `requirements.txt` del servicio

---

## QA

### S8-12 · Tests Pilar A — Identidad + JWT
- **Agente:** AG-06 QA
- **Item:** Item 12
- **Sprint:** Sprint 8
- **Estado:** Pendiente
- **Branch:** feature/s8-12-tests-pilar-a
- **Dependencia:** Items 1-6 aprobados
- **Descripción:**
  Suite de tests para Pilar A. Cobertura mínima:
  - `MWTUser` creación con `role` y `is_api_user`
  - `UserPermission` validación techo
  - JWT payload contiene `user_id` + `role` + `legal_entity_id` + `permissions`
  - `is_api_user=False` → 401
  - Decoradores `require_permission` y `require_permission_jwt`
  - API Admin usuarios (crear, listar, PATCH permisos, guardia last admin)
  - `ConversationLog` `calculate_retention()` para los 3 casos
  - `purge_expired_logs` solo purga logs expirados
- **Criterios de Éxito:**
  - [ ] Todos los tests pasan
  - [ ] Cobertura ≥80% en `apps/users/` y `apps/knowledge/models.py`
  - [ ] Redis namespace `kw:` no colisiona con Django sessions
- **Riesgos:**
  - Tests que importan constantes del app desde migraciones fallarán — usar listas locales

---

### S8-13 · Tests Pilar B — Knowledge Endpoints
- **Agente:** AG-06 QA
- **Item:** Item 13
- **Sprint:** Sprint 8
- **Estado:** Pendiente
- **Branch:** feature/s8-13-tests-pilar-b
- **Dependencia:** Items 7-10 aprobados
- **Descripción:**
  Suite de tests para Pilar B. Cobertura:
  - `POST /api/knowledge/ask/` flujo completo (mock OpenAI embed + mock Claude)
  - Filtro visibilidad por permisos
  - Historial multi-turn Redis
  - `ConversationLog` guardado
  - `POST /api/knowledge/index/` CEO-only
  - Indexer rechaza CEO-ONLY
  - `GET /api/knowledge/sessions/` filtra por usuario
  - Expediente BLOQUEADO: `/ask/` funciona
- **Criterios de Éxito:**
  - [ ] Tests pasan con mocks de OpenAI y Anthropic
  - [ ] Filtro visibilidad probado para cada combinación de permiso
  - [ ] `ConversationLog` creado en cada `/ask/`
  - [ ] CEO-ONLY excluido del indexer
- **Riesgos:**
  - Tests requieren mock de OpenAI y Anthropic (pytest-mock / unittest.mock)

---

## ARQUITECTURA

### S8-14 · Verificaciones Arquitectura — Checklist Pre-Deploy
- **Agente:** AG-01 Architect
- **Item:** Item 14 (Verificaciones)
- **Sprint:** Sprint 8
- **Estado:** Pendiente
- **Branch:** feature/s8-14-arch-verification
- **Dependencia:** Todos los items anteriores aprobados
- **Descripción:**
  Verificaciones del arquitecto antes del deploy.
- **Criterios de Éxito:**
  - [ ] V1: `grep -rn "ForeignKey.*User|auth.User" apps/` — lista completa confirmada
  - [ ] V2: FKs contrib adicionales identificadas
  - [ ] V3: `celery-beat` sin `--scheduler DatabaseScheduler`
  - [ ] V4: `MWTUser.objects.get(username=CEO_USERNAME).id == old_auth_user.id`
  - [ ] V5: `SELECT count(*) FROM knowledge_chunks WHERE kb_visibility='CEO-ONLY'` = 0
  - [ ] V6: Redis `kw:` namespace no colisiona con Django sessions
  - [ ] V7: `python manage.py check` sin errores
  - [ ] V8: `docker compose logs celery-beat` muestra exactamente 3 tasks
- **Riesgos:**
  - Cualquier verificación fallida bloquea el deploy hasta resolverse

---

## RESUMEN SPRINT 8

| Item | Tarea | Agente | Branch |
|------|-------|--------|--------|
| 1 | MWTUser — Modelo + Migración CEO | AG-02 | feature/s8-01-mwtuser |
| 2 | UserPermission — Modelo + Validación Techo | AG-02 | feature/s8-01-mwtuser |
| 3 | JWT Extendido — Serializer + Guardia is_api_user | AG-02 | feature/s8-03-jwt-extended |
| 4 | Decoradores @require_permission (Session + JWT) | AG-02 | feature/s8-03-jwt-extended |
| 5 | API Admin Usuarios — CRUD + Permisos | AG-02 | feature/s8-05-admin-users-api |
| 6 | ConversationLog + Retención + Signal + Beat Task | AG-02 | feature/s8-06-conversation-log |
| 7 | mwt-knowledge — Servicio FastAPI + pgvector + Indexer | AG-02 | feature/s8-07-knowledge-service |
| 8 | Endpoint POST /api/knowledge/ask/ | AG-02 | feature/s8-08-knowledge-ask |
| 9 | Endpoint POST /api/knowledge/index/ | AG-02 | feature/s8-09-knowledge-index |
| 10 | Endpoint GET /api/knowledge/sessions/ | AG-02 | feature/s8-10-knowledge-sessions |
| 11 | Docker Compose — mwt-knowledge + pgvector | AG-07 | feature/s8-11-devops-knowledge |
| 12 | Tests Pilar A — Identidad + JWT | AG-06 | feature/s8-12-tests-pilar-a |
| 13 | Tests Pilar B — Knowledge Endpoints | AG-06 | feature/s8-13-tests-pilar-b |
| 14 | Verificaciones Arquitectura — Checklist Pre-Deploy | AG-01 | feature/s8-14-arch-verification |

## DECISIONES ARQUITECTÓNICAS CLAVE (D-01 a D-13)

- **D-01:** `legal_entity` es FK directa a `LegalEntity` — NO crear `LegalEntityRef`
- **D-02:** FKs a migrar: EventLog, ArtifactInstance, Transfer
- **D-03:** JWT extiende Sprint 0 — NO crear endpoint nuevo, solo modificar serializer
- **D-04:** Celery Beat usa `app.conf.beat_schedule` — eliminar `--scheduler DatabaseScheduler`
- **D-05:** Redis prefix `kw:` obligatorio para knowledge (zero colisión con sessions)
- **D-06:** pgvector en DB `mwt` — no afecta DB `paperless`
- **D-07:** `psycopg2-binary>=2.9` en `requirements.txt` de `mwt-knowledge`
- **D-08:** CEO migra con `is_api_user=True`
- **D-09:** ConversationLog en expediente BLOQUEADO es **permitido** — no verificar estado
- **D-10:** Signal `retain_until` usa `transaction.on_commit()` obligatoriamente
- **D-11:** Frontend Sprint 7 no se toca — knowledge es API-only en Sprint 8
- **D-12:** Usuarios seed: solo CEO. Nuevos usuarios se crean post-deploy via API
- **D-13:** `visibility=CEO-ONLY` excluido del indexer intencionalmente (`reason: ceo_only_excluded`)
