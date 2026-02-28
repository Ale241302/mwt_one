# Tareas MWT - Sprint 3: Frontend MVP — El CEO Deja de Usar API

A continuación se detalla la lista de tareas a importar en Asana bajo el proyecto **Tareas MWT** (Sección: Sprint 3) derivadas de `LOTE_SM_SPRINT3.md`, `ENT_PLAT_FRONTENDS.md`, `ENT_PLAT_LEGAL_ENTITY.md`, `IDX_PLATAFORMA.md` y `mwt_sprint3_visual_spec_1.html`.

**Prerequisito:** Sprint 2 DONE — 22 command endpoints (18 Sprint 1 + 2 Sprint 2 + 2 read), reloj crédito automático con bloqueo día 75, supersede/void funcional, Celery+Redis operativos, event dispatcher marcando processed_at.

**Objetivo Sprint 3:** El CEO deja de operar via API. Frontend funcional con login, dashboard, lista de expedientes, detalle con timeline, acciones contextuales y semáforos de crédito. El sistema se usa desde el navegador (mwt.one).

**Stack nuevo Sprint 3:** Next.js 14+ container en Docker + nginx reverse proxy. Auth via Django session cookie + CSRF. Total: 8 containers.

**Decisiones congeladas:** S3-D01 (Auth session+CSRF), S3-D02 (credit_band backend), S3-D03 (available_actions), S3-D04 (Design tokens Navy+Mint), S3-D05 (Solo CEO), S3-D06 (CSRF bootstrap), S3-D07 (Performance <200ms), S3-D08 (Actions order backend).

**Visual Spec:** Referencia `mwt_sprint3_visual_spec_1.html` — prototipo interactivo con login, dashboard, lista, detalle, catálogo UI con design tokens aplicados.

---

## Tareas

### Tarea 1: Sprint 3 - Item 1: Infraestructura Frontend — Next.js + Docker + nginx (AG-07 DevOps)
- **Responsable (Agente):** AG-07 DevOps
- **Dependencia:** Sprint 2 DONE (7 containers existentes).
- **Descripción:** Agregar container Next.js 14+ al stack Docker. Configurar nginx reverse proxy para servir frontend en `/` y API en `/api/`. Variables de entorno `NEXT_PUBLIC_API_URL=/api`. Hot reload en dev. Build producción funcional. Mismo dominio mwt.one para cookies compartidas. Stack total: 8 containers (7 existentes + frontend).
- **Archivos permitidos:** docker-compose.yml, nginx/conf.d/default.conf, .env, frontend/Dockerfile, frontend/package.json, frontend/next.config.js.
- **Archivos prohibidos:** apps/ (Django), tests/, config/settings/.
- **Criterios de Éxito:**
  - Container `frontend` en docker-compose: Next.js 14+, node:20-alpine, port 3000 interno.
  - nginx: `/api/` → django:8000, `/admin/` → django:8000, `/static/` → Django, `/` → frontend:3000.
  - Variables: NEXT_PUBLIC_API_URL=/api, DJANGO_CSRF_COOKIE_NAME=csrftoken.
  - Health check: frontend responde en `/` con placeholder.
  - Hot reload funcional en dev (volume mount frontend/src/).
  - Build producción: `next build` + `next start` OK.
  - Stack completo levanta con `docker-compose up` sin errores: 8 containers.
  - Cookies compartidas entre frontend y API (mismo dominio via nginx).
- **NO toca:** Django settings, CORS/CSRF/session config (→ Item 7 AG-02).
- **Riesgos:** nginx mal configurado (CSRF cookie no llega al frontend), port conflicts, Next.js no resuelve API vía proxy.
- **Branch:** `sprint3/item-1-infra-frontend`

---

### Tarea 2: Sprint 3 - Item 2: Endpoints UI Agregados — list + detail bundle + available_actions (AG-02 API Builder)
- **Responsable (Agente):** AG-02 API Builder
- **Dependencia:** Item 1 aprobado (nginx rutea /api/ correctamente).
- **Descripción:** Crear 3 endpoints UI: (1) `GET /api/ui/expedientes/` — lista paginada con filtros (status, brand, client, is_blocked, credit_band), ordenamiento (created_at, credit_days_elapsed, last_event_at), campos precalculados (total_cost via annotate Sum, artifact_count via annotate Count, credit_band calculado MINT<60d/AMBER 60-74d/CORAL≥75d). (2) `GET /api/ui/expedientes/{id}` — bundle completo con expediente + artifacts + timeline + documents + credit_clock + costs_summary + available_actions en una sola llamada, performance <200ms con select_related + prefetch_related. (3) `GET /api/documents/{id}/download/` — redirect 302 a MinIO presigned URL (5min expiry). Crear función `get_available_commands(expediente)` en services.py: read-only, consume transition map, devuelve lista ordenada Pipeline (PRIMARY→SECONDARY) → Ops. Contrato `available_actions` FROZEN v1.
- **Archivos permitidos:** apps/expedientes/views.py (extend), serializers_ui.py (new), services.py (extend get_available_commands), urls.py (extend).
- **Archivos prohibidos:** models.py, tests/, frontend/.
- **Criterios de Éxito:**
  - List: paginado default=25 max=100, 5 filtros funcionales, 3 ordenamientos.
  - List: total_cost/artifact_count vía SQL annotate (no loop Python).
  - Detail: bundle completo en 1 query + prefetch. Target <200ms.
  - available_actions: contrato v1 (action_id, command, label, kind, variant, enabled, disabled_reason, requires_confirm, confirm_text, requires_reason, artifact_selector, fields).
  - get_available_commands: Pipeline por estado + Ops fijas (C15, C17, C18, C19, C20).
  - Ops: enabled/disabled_reason calculados (ej: C17 enabled solo si !is_blocked).
  - C15 fields: name(string), amount(decimal), currency(string default USD), category(enum).
  - Download: redirect 302 a MinIO presigned URL, session auth, 404 si no existe.
  - Session auth en todos los endpoints.
- **Riesgos:** Performance >200ms en detail bundle. available_actions no cubre todos los edge cases de estado.
- **Branch:** `sprint3/item-2-ui-endpoints`

---

### Tarea 3: Sprint 3 - Item 3: Login + Layout + Navegación — Shell del Dashboard (AG-03 Frontend)
- **Responsable (Agente):** AG-03 Frontend
- **Dependencia:** Item 1 aprobado (container levanta), Item 7 aprobado (auth endpoints disponibles).
- **Descripción:** Implementar login page, layout shell (sidebar + header + content), navegación y auth flow. Login: form username+password → POST /api/auth/login/ → redirect a dashboard. CSRF bootstrap: GET /api/auth/me/ al montar app obtiene csrftoken cookie, toda mutación envía X-CSRFToken header. Sidebar Navy #013A57 (240px expanded / 64px collapsed), items: Dashboard (home), Expedientes (folder), placeholders grises para futuras secciones. Item activo: border-left 3px Mint, bg nav-item-active. Responsive: auto-collapsed <1024px. Logout en sidebar bottom → POST /api/auth/logout/. Interceptor global: 401 → redirect login. Tipografía: General Sans (display), Plus Jakarta Sans (body), JetBrains Mono (mono). CSS custom properties desde ENT_PLAT_DESIGN_TOKENS (light mode only Sprint 3). Loading spinner durante verificación auth.
- **Archivos permitidos:** frontend/src/ (todo).
- **Archivos prohibidos:** apps/ (Django), docker-compose.yml, nginx/.
- **Criterios de Éxito:**
  - Login page funcional: form → auth → redirect.
  - CSRF flow correcto: GET /me/ → cookie → X-CSRFToken en mutaciones.
  - Sidebar: Navy, 240px expanded, 64px collapsed, toggle manual.
  - Items: Dashboard + Expedientes activos, placeholders grises Sprint 4/5.
  - Active item: border-left Mint + bg.
  - Responsive: auto-collapsed <1024px.
  - Logout funcional → redirect login.
  - 401 interceptor global.
  - Tipografía y design tokens aplicados.
  - Loading spinner durante auth verify.
- **Ref visual:** `mwt_sprint3_visual_spec_1.html` — pantallas ①②.
- **Branch:** `sprint3/item-3-login-layout`

---

### Tarea 4: Sprint 3 - Item 4: Lista de Expedientes con Filtros (AG-03 Frontend)
- **Responsable (Agente):** AG-03 Frontend
- **Dependencia:** Item 3 aprobado (layout funcional), Item 2 aprobado (endpoint list disponible).
- **Descripción:** Página `/expedientes` consume `GET /api/ui/expedientes/`. Tabla con 7 columnas: Ref (mono, clickable), Estado (badge color), Cliente, Marca, Días crédito (número + dot credit_band Mint/Ámbar/Coral), Monto (tabular-nums right-aligned), Última actividad (relative time "hace 2h"). Zebra striping filas alternando bg-alt/surface. Row states: Normal, Blocked (border-right 3px Coral), Hover (border-left 3px Mint), Blocked+hover (dual indicator). Filtros: dropdown estado (8 estados + Todos), dropdown marca, dropdown cliente, toggle "Solo bloqueados". Paginación: botones prev/next, indicador "Mostrando 1-25 de 47". Ordenamiento: click en header alterna asc/desc. Click fila → navega a `/expedientes/{id}`. Empty state con ícono. Loading skeleton animado.
- **Archivos permitidos:** frontend/src/ (todo).
- **Archivos prohibidos:** apps/ (Django), docker-compose.yml, nginx/.
- **Criterios de Éxito:**
  - Tabla con 7 columnas implementadas.
  - Zebra striping funcional.
  - 4 row states implementados (normal, blocked, hover, blocked+hover).
  - 4 filtros funcionales (estado, marca, cliente, bloqueados).
  - Paginación con indicador.
  - Ordenamiento en 3 columnas (Días, Fecha, Monto).
  - Click fila → detalle.
  - Empty state y loading skeleton.
- **Ref visual:** `mwt_sprint3_visual_spec_1.html` — pantalla ③.
- **Branch:** `sprint3/item-4-lista-expedientes`

---

### Tarea 5: Sprint 3 - Item 5: Detalle Expediente + Acciones Contextuales (AG-03 Frontend)
- **Responsable (Agente):** AG-03 Frontend
- **Dependencia:** Item 4 aprobado (lista funcional, navegación a detalle).
- **Descripción:** Página `/expedientes/{id}` consume un solo fetch `GET /api/ui/expedientes/{id}`. Secciones: (1) Header: ref mono display-lg, status badge, credit clock badge, blocked badge. (2) Timeline horizontal: nodos completados (Mint filled ✓ 16px), actual (Navy pulse animation 20px), futuros (hollow dashed 16px). Líneas solid Mint/gradient/dashed. Responsive vertical <768px. (3) Datos: grid cards con shadow-sm, radius-xl. (4) Artefactos: lista con status badges, superseded tachado, void tachado+badge. (5) Documentos: nombre, tipo, fecha, botón descargar. (6) Costos: tabla con total row. (7) Pipeline actions: botón principal lg PRIMARY, dropdown "Más acciones" si hay más. Disabled: opacity 0.4, tooltip disabled_reason. (8) Ops actions: toolbar fijo con Block/Unblock/Costo/Corregir/Anular según enabled. (9) Modales: confirm (requires_confirm), reason (requires_reason textarea mín 5 chars), artifact selector (C19/C20), Register Cost form (C15 con 4 campos). (10) Post-acción: re-fetch completo, toast success (Mint 5s auto-dismiss), toast error (Coral persistent). Back button preserva filtros.
- **Archivos permitidos:** frontend/src/ (todo).
- **Archivos prohibidos:** apps/ (Django), docker-compose.yml, nginx/.
- **Criterios de Éxito:**
  - Header con ref, status, credit, blocked badges.
  - Timeline horizontal con 3 tipos de nodos + pulse animation + responsive vertical.
  - Secciones datos, artefactos, documentos, costos implementadas.
  - Pipeline actions: botón principal + dropdown más.
  - Ops actions: toolbar con visibilidad según enabled.
  - 4 tipos de modales funcionales (confirm, reason, artifact selector, cost form).
  - Validación client-side (required, amount>0, reason mín 5 chars).
  - Post-acción: re-fetch + toast success/error.
  - Back button preserva filtros (query params URL).
- **Ref visual:** `mwt_sprint3_visual_spec_1.html` — pantallas ④⑤.
- **Branch:** `sprint3/item-5-detalle-acciones`

---

### Tarea 6: Sprint 3 - Item 6: Dashboard Resumen — Landing Page CEO (AG-03 Frontend)
- **Responsable (Agente):** AG-03 Frontend
- **Dependencia:** Item 3 aprobado (layout), Item 7 aprobado (endpoint dashboard).
- **Descripción:** Página `/` (dashboard) — landing después de login. Consume exclusivamente `GET /api/ui/dashboard/` (NO hace calls a ui/expedientes). 4 stat cards: Expedientes activos (display-xl), Alertas crédito (count AMBER+CORAL, Coral si >0), Bloqueados (Coral si >0), Costo total (tabular-nums body font, no mono). Tabla "Top riesgo": 5 expedientes con mayor credit_days_elapsed, click navega a detalle. Tabla "Bloqueados" con razón. Panel alertas AMBER/CORAL. Polling: refresh cada 60 segundos (setInterval, no websocket). Design: cards shadow-sm radius-xl, colores semáforo Mint/Ámbar/Coral.
- **Archivos permitidos:** frontend/src/ (todo).
- **Archivos prohibidos:** apps/ (Django), docker-compose.yml, nginx/.
- **Criterios de Éxito:**
  - Página `/` como dashboard landing.
  - Consume SOLO `GET /api/ui/dashboard/`.
  - 4 stat cards con datos reales (no "undefined", no "NaN").
  - Tabla Top riesgo: 5 expedientes, click → detalle.
  - Tabla Bloqueados con razón.
  - Panel alertas AMBER + CORAL.
  - Polling 60s funcional.
  - Design tokens aplicados (Mint success, Ámbar warning, Coral critical).
- **Ref visual:** `mwt_sprint3_visual_spec_1.html` — pantalla ②.
- **Branch:** `sprint3/item-6-dashboard`

---

### Tarea 7: Sprint 3 - Item 7: Auth Endpoints + Dashboard Stats + Django Auth Config (AG-02 API Builder)
- **Responsable (Agente):** AG-02 API Builder
- **Dependencia:** Item 1 aprobado (nginx rutea /api/, container Django accesible).
- **Descripción:** Configurar Django auth para session cookies compartidas con frontend via nginx same-domain. Crear endpoints auth: (1) POST /api/auth/login/ — authenticate+login → 200 user info o 401 error. (2) POST /api/auth/logout/ — logout+clear session → 200. (3) GET /api/auth/me/ — si session: 200 user info, si no: 401. SIEMPRE setea csrftoken cookie (incluso en 401, S3-D06). (4) GET /api/ui/dashboard/ — stats agregados: active_count, alert_count (AMBER+CORAL), blocked_count, total_cost (SQL aggregation, no loop), top_risk (top 5 por credit_days DESC), blocked list, alerts list. Django settings: CORS_ALLOWED_ORIGINS, CSRF_TRUSTED_ORIGINS, SESSION_COOKIE_DOMAIN, CSRF_COOKIE_HTTPONLY=False, SESSION_COOKIE_SAMESITE=Lax, SESSION_COOKIE_SECURE=True prod.
- **Archivos permitidos:** apps/core/views.py (new), apps/core/urls.py (new), apps/core/serializers.py (new), config/urls.py (extend), config/settings/base.py (auth config).
- **Archivos prohibidos:** apps/expedientes/models.py, tests/, frontend/.
- **Criterios de Éxito:**
  - Login: 200 + session + {user: {id, username, role: "CEO"}}. Error: 401.
  - Logout: 200 + session cleared. Requiere session activa.
  - Me: 200 user info si sesión, 401 si no. CSRF cookie SIEMPRE presente.
  - Dashboard: active_count, alert_count, blocked_count, total_cost correctos.
  - top_risk: top 5 por credit_days DESC, solo activos.
  - blocked: todos is_blocked=true.
  - alerts: todos credit_band IN (AMBER, CORAL).
  - total_cost via SQL aggregation.
  - Django auth config completa (CORS, CSRF, session cookies).
- **Riesgos:** CSRF cookie no llega al frontend (HttpOnly=True por error). Session no persiste entre requests.
- **Branch:** `sprint3/item-7-auth-dashboard`

---

### Tarea 8: Sprint 3 - Item 8: Tests — Backend pytest + Playwright Smoke E2E (~35+ tests) (AG-06 QA)
- **Responsable (Agente):** AG-06 QA
- **Dependencia:** Items 2+7 aprobados (backend tests), Items 3-6 aprobados (Playwright smoke).
- **Descripción:** Tests en 2 bloques: (A) Backend pytest — auth tests (5: login success/fail, logout, me auth/unauth+CSRF), UI list endpoint tests (8: paginación, filtros status/brand/is_blocked/credit_band, ordenamiento, response contrato, aggregations), UI detail endpoint tests (11: bundle completo, available_actions por estado REGISTRO/PRODUCCION/CERRADO, ops C17/C18/C15/C19/C20, disabled_reason, ordenamiento actions), dashboard endpoint tests (6: counts, top_risk, blocked, alerts, total_cost), get_available_commands tests (8 estados), regresión Sprint 1+2 (1). (B) Playwright smoke (10 tests): login success, login fail, dashboard 4 cards, sidebar → lista, filtro estado, click detalle, acciones habilitadas, Block+reason+Unblock flujo completo, back preserva filtros, logout → redirect.
- **Archivos permitidos:** tests/test_ui_endpoints.py (new), tests/test_auth.py (new), tests/test_available_commands.py (new), frontend/e2e/ (new).
- **Archivos prohibidos:** apps/*/views.py, apps/*/models.py, frontend/src/.
- **Criterios de Éxito:**
  - **Auth (5 tests):** login success/fail, logout, me auth/unauth+CSRF.
  - **UI List (8 tests):** paginación, 4 filtros, ordenamiento, response format, aggregations.
  - **UI Detail (11 tests):** bundle completo, available_actions para REGISTRO/PRODUCCION/CERRADO, ops enabled/disabled, disabled_reason, artifact_selector, fields C15, orden actions.
  - **Dashboard (6 tests):** active_count, alert_count, blocked_count, total_cost, top_risk, blocked list.
  - **get_available_commands (por 8 estados):** acciones correctas.
  - **Regresión (1 test):** 22 endpoints Sprint 1+2 funcionales.
  - **Playwright smoke (10 tests):** login, dashboard, lista, filtros, detalle, acciones, Block/Unblock, back, logout.
  - Todos los tests passing.
  - Tests Sprint 1+2 siguen passing.
- **Branch:** `sprint3/item-8-tests`

---

## Dependencias Sprint 3

```
Sprint 2 DONE
    │
    ├── Item 1: Infra Next.js + Docker + nginx (AG-07, P0)
    │       │
    │       ├── Item 2: Endpoints UI (AG-02, después de Item 1)     ─┐
    │       │                                                        │
    │       └── Item 7: Auth + Dashboard + Django config (AG-02,     │
    │           después de Item 1, PARALELO con Item 2)             ─┤
    │                                                                │
    │       ┌─── Items 2+7 aprobados ────────────────────────────────┘
    │       │
    │       ├── Item 3: Login + Layout (AG-03, después de Items 1+7)
    │       │       │
    │       │       ├── Item 4: Lista expedientes (AG-03, después de Items 2+3)
    │       │       │       │
    │       │       │       └── Item 5: Detalle + Acciones (AG-03, después de Item 4)
    │       │       │
    │       │       └── Item 6: Dashboard (AG-03, después de Items 3+7)
    │       │
    │       └── Item 8: Tests (AG-06, después de TODOS los items)
```

**Cadena crítica:** Item 1 → Item 2/Item 7 (paralelo) → Item 3 → Item 4 → Item 5 → Item 8.

---

## Criterio de Cierre Sprint 3

Sprint 3 está **DONE** cuando:
1. Stack levanta con 8 containers sin errores.
2. CEO hace login en mwt.one con username/password.
3. Dashboard muestra 4 stat cards con datos reales.
4. Lista expedientes carga, filtra, ordena, pagina.
5. Detalle expediente muestra timeline visual + artefactos + documentos + costos + acciones.
6. CEO ejecuta Block con reason desde UI → bloqueo → Unblock funcional.
7. CEO ejecuta transición Pipeline desde UI → estado avanza → timeline actualiza.
8. CEO registra costo desde UI → cost_line aparece.
9. Toast confirmación/error visible después de cada acción.
10. Todos los tests Item 8 passing.
11. Los 22 endpoints Sprint 1+2 siguen funcionales.
12. available_actions se recalculan después de cada acción (re-fetch).
13. 28 endpoints totales (22 previos + login + logout + me + dashboard + ui/list + ui/detail).

## Lo que NO debe existir en Sprint 3
- Costos doble vista internal/client (Sprint 4)
- SKUAlias (Sprint 4)
- Margen / escenario financiero (Sprint 4)
- Notificaciones email (Sprint 4)
- Dark mode (Sprint 4+, tokens definidos pero no implementado)
- Portal B2B / otros roles (Post-MVP, solo CEO usa MVP)
- Event consumers complejos (Post-MVP)
- WebSocket / real-time (Post-MVP, polling 60s es suficiente)
- ranawalk.com (paralelo si hay recursos)
- muitowork.com (estático, sin backend)
