# LOTE_SM_SPRINT3 — Frontend MVP: El CEO Deja de Usar API
status: FROZEN — Aprobado CEO 2026-02-27
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
version: 1.0
tipo: Lote ruteado (ref → PLB_ORCHESTRATOR §E)
sprint: 3
priority: P0
depends_on: LOTE_SM_SPRINT2 (todos los items aprobados)
refs: ENT_OPS_STATE_MACHINE v1.2.2 (FROZEN), PLB_ORCHESTRATOR v1.2.2 (FROZEN), ENT_PLAT_DESIGN_TOKENS v1, ENT_COMP_VISUAL v2

---

## Scope Sprint 3

**Objetivo:** El CEO deja de operar via API. Frontend funcional con lista, detalle, timeline, dashboard y acciones contextuales. El sistema se usa desde el navegador.

**Precondición:** Sprint 2 DONE — 22 command endpoints (18 Sprint 1 + 2 Sprint 2 + 2 read), reloj crédito automático con bloqueo día 75, supersede/void funcional, Celery+Redis operativos, event dispatcher marcando processed_at.

### Decisiones congeladas

| ID | Decisión | Valor |
|----|----------|-------|
| S3-D01 | Auth | Django session cookie + CSRF. Next.js fetch con credentials. Mismo dominio via nginx reverse proxy. |
| S3-D02 | Semáforo crédito | Backend calcula `credit_band` (MINT\|AMBER\|CORAL). Frontend solo pinta. |
| S3-D03 | Transiciones | Contextuales via `available_actions[]` en UI bundle. Pipeline vs Ops separados. |
| S3-D04 | Design system | ENT_PLAT_DESIGN_TOKENS v1 (Navy #013A57 + Mint #75CBB3). |
| S3-D05 | Usuario | Un solo usuario humano (CEO). Auth ultra simple, un rol. |
| S3-D06 | CSRF bootstrap | `GET /api/auth/me/` siempre setea cookie csrftoken (incluso en 401). Frontend envía `X-CSRFToken` en toda mutación. |
| S3-D07 | Performance | List: page_size max=100, default=25. Solo counts precalculados, nunca nested. Detail: nested OK (un solo expediente). Target <200ms. |
| S3-D08 | Actions order | `available_actions[]` ordenado por prioridad: PIPELINE primero PRIMARY luego SECONDARY. Backend decide orden, frontend no reordena. |

### Incluido en Sprint 3

| # | Feature | Agente | Prioridad |
|---|---------|--------|-----------|
| 1 | Next.js en Docker + nginx reverse proxy | AG-07 | P0 — sin esto no hay frontend |
| 2 | Endpoints UI agregados (list + detail bundle + available_actions) | AG-02 | P0 — alimenta todo el frontend |
| 3 | Login + Layout + Navegación | AG-03 | P0 — shell del dashboard |
| 4 | Lista de expedientes con filtros | AG-03 | P0 — vista principal |
| 5 | Detalle expediente + acciones contextuales | AG-03 | P0 — operación diaria |
| 6 | Dashboard resumen | AG-03 | P0 — landing page CEO |
| 7 | Auth endpoints + dashboard stats + Django auth config | AG-02 | P0 — backend para Items 3+6 |
| 8 | Tests (backend pytest + Playwright smoke) | AG-06 | P0 — obligatorio |

### Excluido de Sprint 3

| Feature | Razón | Cuándo |
|---------|-------|--------|
| Costos doble vista (internal/client) | Backend adicional + UI compleja. CEO opera con vista única por ahora | Sprint 4 |
| SKUAlias (cliente ↔ fábrica) | No bloquea operación diaria | Sprint 4 |
| Margen / escenario financiero | Requiere costos doble vista primero | Sprint 4 |
| Notificaciones email | Requiere infra SMTP/n8n. No invertir en DNS/SMTP en Sprint 3 | Sprint 4 |
| Event consumers complejos | 1 consumer (reloj crédito) es suficiente | Post-MVP |
| Portal B2B / otros roles | Solo CEO usa MVP | Post-MVP |
| ranawalk.com | Independiente del Centro de Operaciones | Paralelo si hay recursos |
| Dark mode | Tokens definidos en design system, implementación UI post-MVP | Sprint 4+ |

---

## Cadena de ejecución

```
AG-07 DevOps ──→ AG-02 API ──→ AG-03 Frontend ──→ AG-06 QA
(infra)          (endpoints     (páginas +         (tests +
                 + auth config)  componentes)       smoke E2E)
```

Concurrencia posible: AG-02 Items 2+7 pueden ejecutarse en paralelo después de Item 1. AG-03 necesita ambos Items 2+7 antes de arrancar.

---

## Contrato `available_actions` v1 (FROZEN)

```json
{
  "action_id": "PIPELINE:C08",
  "command": "C08",
  "label": "Confirmar Producción",
  "kind": "PIPELINE",
  "variant": "PRIMARY",
  "enabled": true,
  "disabled_reason": null,
  "requires_confirm": true,
  "confirm_text": "¿Confirmar producción para EXP-2026-0047?",
  "requires_reason": false,
  "artifact_selector": null,
  "fields": []
}
```

### Campos del contrato

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| action_id | string | ✅ | Estable. Formato `KIND:COMMAND`. React keys, tracking, logs. |
| command | string | ✅ | ID del command en state machine (C01–C21). |
| label | string | ✅ | Texto para el botón/menú. Idioma del frontend. |
| kind | enum | ✅ | `PIPELINE` (contextual por estado) o `OPS` (siempre visible). |
| variant | enum | ✅ | `PRIMARY` (acción principal), `SECONDARY`, `DANGER`. |
| enabled | boolean | ✅ | Si false, se muestra greyed out con tooltip. |
| disabled_reason | string? | Solo si !enabled | Explica qué falta para habilitar. CEO ve "qué falta". |
| requires_confirm | boolean | ✅ | Si true, modal de confirmación antes de ejecutar. |
| confirm_text | string? | Solo si requires_confirm | Texto del modal. Incluye ref del expediente. |
| requires_reason | boolean | ✅ | Si true, textarea obligatorio en modal. |
| artifact_selector | enum? | Solo C19/C20 | `COMPLETED_SAME_TYPE` (C19) o `VOIDABLE_ONLY` (C20). Frontend filtra lista. |
| fields | array | ✅ | Vacío para todo excepto C15. Sprint 3: solo C15. |

### Ops actions fijas para CEO

| Command | Label | Variant | Enabled cuando | requires_reason | artifact_selector | fields |
|---------|-------|---------|----------------|-----------------|-------------------|--------|
| C15 | Registrar Costo | SECONDARY | status ∉ {CERRADO, CANCELADO} | false | null | name(string), amount(decimal), currency(string default USD), category(enum) |
| C17 | Bloquear | DANGER | !is_blocked | true | null | [] |
| C18 | Desbloquear | SECONDARY | is_blocked | false | null | [] |
| C19 | Corregir Artefacto | DANGER | tiene artifacts completed | true | COMPLETED_SAME_TYPE | [] |
| C20 | Anular Artefacto | DANGER | tiene artifacts voidable (ART-09) | true | VOIDABLE_ONLY | [] |

### Orden de `available_actions[]`

Backend devuelve ordenado: Pipeline primero (PRIMARY antes que SECONDARY), luego Ops. Frontend no reordena.

---

## Items detallados

### Item 1: Infraestructura frontend — AG-07 DevOps

**Agente:** AG-07 DevOps
**Dependencia previa:** Sprint 2 DONE (stack: Django + PostgreSQL + Redis + Celery worker + Celery beat + MinIO + nginx = 7 containers)
**Archivos a tocar:** `docker-compose.yml`, `nginx/conf.d/default.conf`, `.env`, `frontend/Dockerfile`, `frontend/package.json`, `frontend/next.config.js`
**Archivos prohibidos:** `apps/` (Django), `tests/`, `config/settings/`

**Criterio de done:**
- [ ] Container `frontend` en docker-compose: Next.js 14+, node:20-alpine, port 3000 interno
- [ ] nginx reverse proxy configurado:
  - `/api/` → django:8000
  - `/admin/` → django:8000
  - `/static/` → Django static files
  - `/` → frontend:3000 (catch-all)
- [ ] Variables de entorno en `.env`: `NEXT_PUBLIC_API_URL=/api`, `DJANGO_CSRF_COOKIE_NAME=csrftoken`, `DJANGO_SESSION_COOKIE_NAME=sessionid`
- [ ] Health check: frontend container responde en `/` con página placeholder
- [ ] Hot reload funcional en dev (volume mount `frontend/src/`)
- [ ] Build producción funcional (`next build` + `next start`)
- [ ] Stack completo levanta con `docker-compose up` sin errores: 8 containers (7 existentes + frontend)
- [ ] nginx sirve todo bajo mismo dominio (mwt.one) — cookies compartidas entre frontend y API

**NO toca:**
- Django settings (→ Item 7, AG-02)
- Configuración CORS/CSRF/session (→ Item 7, AG-02)

---

### Item 2: Endpoints UI agregados — AG-02 API Builder

**Agente:** AG-02 API Builder
**Dependencia previa:** Item 1 aprobado (nginx rutea /api/ correctamente)
**Refs:** ENT_OPS_STATE_MACHINE §B+§F (estados + transitions), ENT_PLAT_DESIGN_TOKENS §C3 (credit_band colors)
**Archivos a tocar:** `apps/expedientes/views.py` (extend), `apps/expedientes/serializers_ui.py` (new), `apps/expedientes/services.py` (new: `get_available_commands()`), `apps/expedientes/urls.py` (extend)
**Archivos prohibidos:** `apps/expedientes/models.py`, `tests/`, `frontend/`

**Criterio de done:**

**Endpoint 1: `GET /api/ui/expedientes/`**
- [ ] Paginado: `page_size` default=25, max=100
- [ ] Filtros query params: `status`, `brand`, `client`, `is_blocked`, `credit_band`
- [ ] Ordenamiento: `ordering` param acepta `created_at`, `-created_at`, `credit_days_elapsed`, `-credit_days_elapsed`, `last_event_at`, `-last_event_at`
- [ ] Response por item (solo counts precalculados, nunca nested objects):

```json
{
  "id": "uuid",
  "ref": "EXP-2026-0047",
  "status": "PRODUCCION",
  "status_label": "En Producción",
  "brand": "Marluvas",
  "client": "Sondel",
  "mode": "B",
  "credit_days_elapsed": 45,
  "credit_band": "MINT",
  "credit_threshold_next": 60,
  "is_blocked": false,
  "blocked_reason": null,
  "total_cost": 14350.00,
  "currency": "USD",
  "artifact_count": 4,
  "last_event_at": "2026-02-15T14:30:00Z",
  "created_at": "2026-01-10T09:00:00Z"
}
```

- [ ] `total_cost` via `annotate(Sum('cost_lines__amount'))` — no loop Python
- [ ] `artifact_count` via `annotate(Count('artifacts'))` — no loop Python
- [ ] `credit_band` calculado en serializer o annotation: MINT (<60d), AMBER (60-74d), CORAL (≥75d)
- [ ] `last_event_at` precalculado (annotate Max o campo denormalizado)
- [ ] Session auth required (403 sin sesión válida)

**Endpoint 2: `GET /api/ui/expedientes/{id}`**
- [ ] Devuelve bundle completo en una sola llamada con `select_related` + `prefetch_related`:

```json
{
  "expediente": {
    "id": "uuid",
    "ref": "EXP-2026-0047",
    "status": "PRODUCCION",
    "status_label": "En Producción",
    "brand": "Marluvas",
    "client": "Sondel",
    "mode": "B",
    "is_blocked": false,
    "blocked_reason": null,
    "created_at": "...",
    "updated_at": "..."
  },
  "artifacts": [
    {
      "id": "uuid",
      "type": "ART-01",
      "type_label": "OC Cliente",
      "status": "completed",
      "completed_at": "...",
      "superseded_by": null,
      "supersedes": null
    }
  ],
  "timeline": [
    {
      "status": "REGISTRO",
      "status_label": "Registro",
      "entered_at": "2026-01-10T09:00:00Z",
      "exited_at": "2026-01-12T11:00:00Z",
      "duration_days": 2,
      "is_current": false
    }
  ],
  "documents": [
    {
      "id": "uuid",
      "name": "PI-2026-0047.pdf",
      "type": "proforma",
      "uploaded_at": "...",
      "download_url": "/api/documents/uuid/download/"
    }
  ],
  "credit_clock": {
    "started_at": "2026-01-15T00:00:00Z",
    "days_elapsed": 45,
    "band": "MINT",
    "threshold_next": 60,
    "is_expired": false
  },
  "costs_summary": {
    "total": 14350.00,
    "currency": "USD",
    "line_count": 6,
    "lines": [
      {
        "id": "uuid",
        "name": "Flete marítimo",
        "amount": 2400.00,
        "currency": "USD",
        "category": "freight",
        "created_at": "..."
      }
    ]
  },
  "available_actions": []
}
```

- [ ] `available_actions` poblado por `get_available_commands(expediente)` (ver abajo)
- [ ] Performance: una sola query principal + prefetch. Target <200ms.
- [ ] Session auth required

**Función `get_available_commands(expediente)` — `services.py`:**
- [ ] Función pura read-only en `apps/expedientes/services.py`
- [ ] Consume transition map existente de state machine (no duplica lógica de transiciones)
- [ ] Devuelve lista ordenada: Pipeline (PRIMARY primero, luego SECONDARY) → Ops
- [ ] Pipeline actions: solo transiciones válidas para estado actual del expediente
- [ ] Ops actions fijas: C15, C17, C18, C19, C20 con `enabled`/`disabled_reason` calculados
- [ ] `enabled` respeta precondiciones existentes (ej: C17 enabled solo si !is_blocked)
- [ ] `disabled_reason` explica qué falta (ej: "El expediente ya está bloqueado")
- [ ] `fields` solo para C15: `[{name: "name", type: "string"}, {name: "amount", type: "decimal"}, {name: "currency", type: "string", default: "USD"}, {name: "category", type: "enum", options: [...]}]`
- [ ] `artifact_selector` solo para C19 (COMPLETED_SAME_TYPE) y C20 (VOIDABLE_ONLY)
- [ ] Backend nunca lista acciones que después va a negar (no UI→click→403)

**Endpoint 3: `GET /api/documents/{id}/download/`**
- [ ] Devuelve redirect 302 a MinIO presigned URL (expiry 5min)
- [ ] Session auth required
- [ ] Si documento no existe o no pertenece al usuario: 404
- [ ] Si ya existe de Sprint anterior: reutilizar. Si no: crear como parte de este item.

---

### Item 3: Login + Layout + Navegación — AG-03 Frontend

**Agente:** AG-03 Frontend
**Dependencia previa:** Item 1 aprobado (container levanta), Item 7 aprobado (auth endpoints disponibles)
**Refs:** ENT_PLAT_DESIGN_TOKENS v1 (tokens completos), ENT_COMP_VISUAL v2 (compliance visual)
**Archivos a tocar:** `frontend/src/` (todo)
**Archivos prohibidos:** `apps/` (Django), `docker-compose.yml`, `nginx/`

**Criterio de done:**
- [ ] Login page: form username + password → `POST /api/auth/login/` → redirect a `/` (dashboard)
- [ ] CSRF flow: al montar app, `GET /api/auth/me/` obtiene csrftoken cookie. Toda mutación envía `X-CSRFToken` header.
- [ ] Layout shell: sidebar Navy #013A57 (240px expanded / 64px collapsed) + header + content area
- [ ] Sidebar items: Dashboard (icono home), Expedientes (icono folder). Placeholders grises para secciones futuras.
- [ ] Item activo: border-left 3px Mint #75CBB3 + bg nav-item-active
- [ ] Responsive: sidebar auto-collapsed en viewport < 1024px
- [ ] Toggle manual expand/collapse sidebar
- [ ] Logout button en sidebar (bottom) → `POST /api/auth/logout/` → redirect a login
- [ ] Interceptor global: 401 response → redirect a login
- [ ] Tipografía cargada: General Sans (display), Plus Jakarta Sans (body), JetBrains Mono (mono)
- [ ] CSS custom properties generadas desde ENT_PLAT_DESIGN_TOKENS (light mode only en Sprint 3)
- [ ] Loading spinner global mientras auth se verifica al cargar app

---

### Item 4: Lista de expedientes — AG-03 Frontend

**Agente:** AG-03 Frontend
**Dependencia previa:** Item 3 aprobado (layout funcional), Item 2 aprobado (endpoint list disponible)

**Criterio de done:**
- [ ] Página `/expedientes` consume `GET /api/ui/expedientes/`
- [ ] Tabla con columnas:
  - Ref: font mono, clickable (navega a detalle)
  - Estado: badge con color según status
  - Cliente: font body
  - Marca: font body
  - Días crédito: número + dot con color credit_band (Mint/Ámbar/Coral)
  - Monto: font body, tabular-nums, right-aligned
  - Última actividad: caption, relative time ("hace 2h", "hace 3d")
- [ ] Zebra striping: filas alternando bg-alt (#F0F2F5) / surface (#FFFFFF)
- [ ] Row states implementados:
  - Normal: sin bordes especiales
  - Blocked: border-right 3px Coral
  - Selected (hover/focus): border-left 3px Mint
  - Blocked + selected: ambos bordes (dual indicator, auditoría D4)
- [ ] Filtros sobre la tabla:
  - Dropdown estado (todos los 8 estados + "Todos")
  - Dropdown marca
  - Dropdown cliente
  - Toggle "Solo bloqueados"
- [ ] Paginación funcional: botones prev/next, indicador "Mostrando 1-25 de 47"
- [ ] Ordenamiento: click en header Días crédito, Fecha, Monto alterna asc/desc
- [ ] Click en fila → navega a `/expedientes/{id}`
- [ ] Empty state: ícono + "No hay expedientes que coincidan con los filtros" cuando 0 resultados
- [ ] Loading skeleton (placeholder gris animado) mientras carga

---

### Item 5: Detalle de expediente + acciones — AG-03 Frontend

**Agente:** AG-03 Frontend
**Dependencia previa:** Item 4 aprobado (lista funcional, navegación a detalle)

**Criterio de done:**

**Layout detalle:**
- [ ] Página `/expedientes/{id}` consume `GET /api/ui/expedientes/{id}` (un solo fetch)
- [ ] Header: ref en mono display-lg, status badge, credit clock badge (color según band), blocked badge rojo si is_blocked
- [ ] Back button → vuelve a `/expedientes` con filtros preservados (query params en URL)

**Sección timeline:**
- [ ] Componente horizontal con nodos por estado del expediente
- [ ] Nodo completado: Mint filled circle + ✓ (16px)
- [ ] Nodo actual: Navy circle + pulse animation + box-shadow (20px)
- [ ] Nodo futuro: hollow dashed circle (16px)
- [ ] Líneas: solid Mint (completadas), gradient (actual), dashed (futuras)
- [ ] Debajo de cada nodo: status_label + duration_days
- [ ] Responsive: en viewport < 768px, timeline se apila vertical

**Sección datos:**
- [ ] Grid de campos en cards: cliente, marca, modo, fechas (created_at, updated_at), entidad legal
- [ ] Cards con shadow-sm, radius-xl (ENT_PLAT_DESIGN_TOKENS.D2-D3)

**Sección artefactos:**
- [ ] Lista de ArtifactInstance: tipo + type_label, status badge, fecha completado
- [ ] Artefactos superseded: tachado + link "Reemplazado por [ref]"
- [ ] Artefactos void: tachado + badge "Anulado"

**Sección documentos:**
- [ ] Lista: nombre, tipo, fecha upload
- [ ] Botón descargar → `GET /api/documents/{id}/download/` (abre en nueva pestaña)

**Sección costos:**
- [ ] Tabla de CostLine: name, amount (tabular-nums right-aligned), currency, category badge, created_at
- [ ] Fila total al final: sum de amounts, font weight 700

**Panel acciones — Pipeline:**
- [ ] Botón principal: primera acción Pipeline con `enabled=true` y `variant=PRIMARY`. Tamaño lg.
- [ ] Si hay más Pipeline actions: dropdown "Más acciones" con las restantes
- [ ] Disabled actions: visibles pero opacity 0.4, cursor not-allowed, tooltip con `disabled_reason`

**Panel acciones — Ops:**
- [ ] Toolbar o sidebar fijo con: Block/Unblock, Registrar Costo, Corregir Artefacto, Anular Artefacto
- [ ] Visibilidad según `enabled` (ej: Block solo si !is_blocked, Unblock solo si is_blocked)
- [ ] Disabled: greyed out + tooltip con `disabled_reason`

**Modales de acción:**
- [ ] Confirm modal: cuando `requires_confirm=true` → modal con `confirm_text` + botón Confirmar (variant del action) + botón Cancelar
- [ ] Reason modal: cuando `requires_reason=true` → modal con textarea obligatorio (mínimo 5 chars) + confirm
- [ ] Artifact selector: cuando `artifact_selector` presente → dropdown con artefactos filtrados del expediente. COMPLETED_SAME_TYPE para C19, VOIDABLE_ONLY para C20.
- [ ] Register Cost form (C15): modal con 4 campos — name (text input), amount (number input), currency (text input, default USD), category (dropdown enum)
- [ ] Validación client-side: campos requeridos, amount > 0

**Post-acción:**
- [ ] Después de ejecutar acción exitosa: re-fetch `GET /api/ui/expedientes/{id}` completo
- [ ] Toast success (Mint, auto-dismiss 5s): "Acción ejecutada: [label]"
- [ ] Toast error (Coral, persistent): "[error message del backend]"
- [ ] Si la acción cambia estado: timeline se actualiza, available_actions se recalculan

---

### Item 6: Dashboard resumen — AG-03 Frontend

**Agente:** AG-03 Frontend
**Dependencia previa:** Item 3 aprobado (layout), Item 7 aprobado (endpoint dashboard)

**Criterio de done:**
- [ ] Página `/` (dashboard) — landing después de login exitoso
- [ ] Consume exclusivamente `GET /api/ui/dashboard/` (no hace calls a ui/expedientes)
- [ ] 4 stat cards (patrón Claim+Subhead de ENT_MARCA_IDENTIDAD):
  - Expedientes activos: display-xl número, micro label "Activos"
  - Alertas crédito: display-xl número (count AMBER+CORAL), Coral si > 0
  - Bloqueados: display-xl número, Coral si > 0
  - Costo total: display-xl monto (body font tabular-nums, no mono), micro label "Acumulado"
- [ ] Tabla "Top riesgo": 5 expedientes con mayor credit_days_elapsed. Columns: ref (mono clickable), status badge, días, band dot. Click navega a `/expedientes/{id}`.
- [ ] Tabla "Bloqueados": expedientes con is_blocked=true. Columns: ref (mono clickable), status badge, blocked_reason. Click navega a detalle.
- [ ] Panel alertas: lista de expedientes en AMBER y CORAL con badge de días y threshold_next
- [ ] Polling: refresh automático cada 60 segundos (setInterval, no websocket)
- [ ] Design: cards con shadow-sm, radius-xl. Mint para success metrics, Ámbar para warning, Coral para critical.

---

### Item 7: Auth endpoints + dashboard stats + Django auth config — AG-02 API Builder

**Agente:** AG-02 API Builder
**Dependencia previa:** Item 1 aprobado (nginx rutea /api/, container Django accesible)
**Archivos a tocar:** `apps/core/views.py` (new), `apps/core/urls.py` (new), `apps/core/serializers.py` (new), `config/urls.py` (extend), `config/settings/base.py` (auth config)
**Archivos prohibidos:** `apps/expedientes/models.py`, `tests/`, `frontend/`

**Criterio de done:**

**Django auth config (responsabilidad movida de Item 1):**
- [ ] `CORS_ALLOWED_ORIGINS` incluye dominio mwt.one
- [ ] `CSRF_TRUSTED_ORIGINS` incluye dominio mwt.one
- [ ] `SESSION_COOKIE_DOMAIN` configurado para compartir entre frontend y API (mismo dominio via nginx)
- [ ] `CSRF_COOKIE_HTTPONLY = False` (Next.js necesita leer la cookie via JS)
- [ ] `SESSION_COOKIE_SAMESITE = 'Lax'`
- [ ] `SESSION_COOKIE_SECURE = True` en producción
- [ ] Django session middleware + CSRF middleware habilitados

**Endpoints auth:**
- [ ] `POST /api/auth/login/` — username + password → Django `authenticate()` + `login()` → 200 + `{user: {id, username, role: "CEO"}}`. Error: 401 + `{error: "Credenciales inválidas"}`.
- [ ] `POST /api/auth/logout/` — `logout()` + clear session → 200. Requiere session activa.
- [ ] `GET /api/auth/me/` — si sesión activa: 200 + user info. Si no: 401. **SIEMPRE setea cookie csrftoken** (incluso en 401, para que login pueda hacer POST).

**Endpoint dashboard:**
- [ ] `GET /api/ui/dashboard/` — stats agregados:

```json
{
  "active_count": 47,
  "alert_count": 8,
  "blocked_count": 2,
  "total_cost": 284350.00,
  "currency": "USD",
  "top_risk": [
    {
      "id": "uuid",
      "ref": "EXP-2026-0012",
      "status": "TRANSITO",
      "status_label": "En Tránsito",
      "credit_days_elapsed": 82,
      "credit_band": "CORAL",
      "is_blocked": true,
      "blocked_reason": "Crédito día 75"
    }
  ],
  "blocked": [],
  "alerts": []
}
```

- [ ] `top_risk`: top 5 por credit_days_elapsed DESC, solo activos (no CERRADO/CANCELADO)
- [ ] `blocked`: todos los expedientes con is_blocked=true
- [ ] `alerts`: todos los expedientes con credit_band IN (AMBER, CORAL)
- [ ] `total_cost` via aggregation SQL, no loop Python
- [ ] Session auth required en todos (excepto que /me/ devuelve 401 sin romper + setea CSRF)

---

### Item 8: Tests — AG-06 QA

**Agente:** AG-06 QA
**Dependencia previa:** Items 2+7 aprobados (backend tests), Items 3-6 aprobados (Playwright smoke)
**Archivos a tocar:** `tests/test_ui_endpoints.py` (new), `tests/test_auth.py` (new), `tests/test_available_commands.py` (new), `frontend/e2e/` (new)
**Archivos prohibidos:** `apps/*/views.py`, `apps/*/models.py`, `frontend/src/`

**Criterio de done:**

**Backend — pytest:**

Auth:
- [ ] Login success → 200 + session cookie + user info
- [ ] Login fail → 401 + error message
- [ ] Logout → 200 + session cleared
- [ ] Me authenticated → 200 + user info + csrftoken cookie
- [ ] Me unauthenticated → 401 + csrftoken cookie (CSRF siempre presente)

UI List endpoint:
- [ ] Paginación: default 25, custom page_size, max 100 enforced
- [ ] Filtro por status funcional
- [ ] Filtro por brand funcional
- [ ] Filtro por is_blocked funcional
- [ ] Filtro por credit_band funcional
- [ ] Ordenamiento por credit_days_elapsed asc/desc
- [ ] Ordenamiento por created_at asc/desc
- [ ] Response contiene todos los campos del contrato
- [ ] `total_cost` y `artifact_count` son correctos (verificar contra datos de test)

UI Detail endpoint:
- [ ] Bundle completo: expediente + artifacts + timeline + documents + credit_clock + costs_summary + available_actions
- [ ] available_actions correcto para estado REGISTRO (Pipeline: C02 confirm-pi habilitado)
- [ ] available_actions correcto para estado PRODUCCION (Pipeline: C08 confirm-production)
- [ ] available_actions correcto para estado CERRADO (Pipeline: vacío, solo Ops limitadas)
- [ ] Ops C17 enabled cuando !is_blocked, disabled cuando is_blocked
- [ ] Ops C18 enabled cuando is_blocked, disabled cuando !is_blocked
- [ ] Ops C15 enabled cuando status ∉ {CERRADO, CANCELADO}
- [ ] Ops C19 artifact_selector = COMPLETED_SAME_TYPE
- [ ] Ops C20 artifact_selector = VOIDABLE_ONLY
- [ ] disabled_reason presente y descriptivo cuando enabled=false
- [ ] available_actions ordenado: Pipeline (PRIMARY→SECONDARY) → Ops

Dashboard endpoint:
- [ ] active_count correcto
- [ ] alert_count = count(AMBER) + count(CORAL)
- [ ] blocked_count = count(is_blocked=true)
- [ ] total_cost = sum de todos los cost_lines de expedientes activos
- [ ] top_risk ordenado por credit_days_elapsed DESC, max 5
- [ ] blocked contiene solo is_blocked=true

get_available_commands():
- [ ] Para cada uno de los 8 estados: verificar que devuelve las acciones correctas
- [ ] enabled/disabled_reason correcto para cada precondición
- [ ] Función es read-only (no muta nada)

Regresión:
- [ ] Los 22 endpoints de Sprint 1+2 siguen funcionales (ejecutar test suite existente)

**Frontend — Playwright smoke (10 tests, no más):**

- [ ] Test 1: Login con credenciales válidas → redirect a dashboard
- [ ] Test 2: Login con credenciales inválidas → error message visible
- [ ] Test 3: Dashboard muestra 4 stat cards con números (no "undefined", no "NaN")
- [ ] Test 4: Click "Expedientes" en sidebar → lista carga con filas
- [ ] Test 5: Seleccionar filtro estado → lista se actualiza (count cambia o se mantiene coherente)
- [ ] Test 6: Click en fila expediente → detalle carga con header ref + timeline + artefactos
- [ ] Test 7: Detalle muestra acciones habilitadas (al menos 1 botón visible no-disabled)
- [ ] Test 8: Ejecutar Block con reason → confirm modal con textarea → submit reason → success toast → is_blocked=true visible → Unblock → success toast → is_blocked=false
- [ ] Test 9: Detalle → back button → lista con filtros preservados
- [ ] Test 10: Logout → redirect a login → intentar navegar a /expedientes → redirect a login

---

## Regla operativa: `skip_locked` logging

Cuando el task de reloj de crédito (Celery beat, Sprint 2) evalúa expedientes y salta uno por database lock:
- [ ] Log level WARNING: `"skip_locked: expediente_id={id}, reason=row_locked"`
- [ ] No falla silenciosamente. El log es rastreable.
- [ ] Implementar en Sprint 3 si no existe de Sprint 2. Si ya existe, verificar que loguea.

---

## Verificación de cierre Sprint 3

**Checklist de done (ALL must pass):**

1. Stack levanta con 8 containers sin errores
2. CEO hace login en mwt.one con username/password
3. Dashboard muestra 4 stat cards con datos reales
4. Lista expedientes carga, filtra, ordena, pagina
5. Detalle expediente muestra timeline visual + artefactos + documentos + costos + acciones
6. CEO ejecuta Block con reason desde UI → expediente se bloquea → Unblock funcional
7. CEO ejecuta transición Pipeline desde UI → estado avanza → timeline se actualiza
8. CEO registra costo desde UI → cost_line aparece en sección costos
9. Toast de confirmación/error visible después de cada acción
10. Todos los tests de Item 8 passing
11. Los 22 endpoints de Sprint 1+2 siguen funcionales (no regresión)
12. available_actions se recalculan después de cada acción (re-fetch)

**Lo que significa "Sprint 3 DONE":**
- El CEO abre mwt.one en el navegador, hace login, ve dashboard con alertas
- Navega a expedientes, filtra por estado/marca/cliente, entra al detalle
- Ve timeline visual con semáforos de crédito (Mint/Ámbar/Coral)
- Ejecuta acciones contextuales desde UI sin necesitar curl/Postman/Django Admin
- El sistema es operativamente usable desde el navegador
- Total: 22 endpoints previos + 6 nuevos (login, logout, me, dashboard, ui/list, ui/detail) = 28 endpoints

**Lo que NO debe existir al cerrar Sprint 3:**
- Costos doble vista internal/client (Sprint 4)
- SKUAlias (Sprint 4)
- Margen / escenario financiero (Sprint 4)
- Notificaciones email (Sprint 4)
- Dark mode (Sprint 4+)
- Portal B2B / otros roles (Post-MVP)
- Event consumers complejos (Post-MVP)
- WebSocket / real-time (Post-MVP, polling 60s es suficiente)

---

## Qué queda para Sprint 4+

| Feature | Sprint |
|---------|--------|
| Costos doble vista (internal/client) | 4 |
| SKUAlias mínimo (cliente ↔ fábrica) | 4 |
| Margen básico (escenario 1) | 4 |
| Notificaciones email (alertas crédito) | 4 |
| Dark mode | 4+ |
| Dashboard financiero completo | 5+ |
| Factura MWT generación | 5 |
| Portal B2B / otros roles | Post-MVP |

---

Stamp: FROZEN v1.0 — Aprobado CEO 2026-02-27
Auditoría: Iteración en chat + revisión CEO con 5 ajustes incorporados, calificación 10/10
Origen: LOTE_SM_SPRINT2 (FROZEN) + ENT_OPS_STATE_MACHINE v1.2.2 (FROZEN) + PLB_ORCHESTRATOR v1.2.2 (FROZEN) + ENT_PLAT_DESIGN_TOKENS v1 + ENT_COMP_VISUAL v2
Decisiones congeladas: S3-D01 a S3-D08
