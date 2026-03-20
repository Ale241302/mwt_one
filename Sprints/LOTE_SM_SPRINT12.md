# LOTE_SM_SPRINT12 — Refactorización + Inventario + WhatsApp + CI/CD
status: DRAFT — aprobado ChatGPT 9.6/10 R3 (pendiente), pendiente aprobación CEO
visibility: INTERNAL
domain: Plataforma (IDX_PLATAFORMA)
version: 2.1
sprint: 12
priority: P0
agente_principal: AG-02 Backend + AG-03 Frontend (Alejandro)
depends_on: LOTE_SM_SPRINT11 (en formulación)
refs: REPORTE_AUDIT_CODEBASE_20260318, ENT_OPS_STATE_MACHINE (FROZEN v1.2.2), ENT_GOB_PENDIENTES

---

## Objetivo Sprint 12

Refactorizar el backend y frontend para escalar, implementar CI/CD, y agregar los módulos faltantes (Inventario, WhatsApp API). El codebase sale de Sprint 12 listo para onboarding de un segundo developer.

**Estructura:** Fase 0 (refactorización obligatoria) → Fase 1 (CI/CD) → Fase 2 (features) → QA.

**Precondición:** Sprint 11 DONE — deuda técnica pre-B2B limpia (states centralizados, rutas únicas, 0 hex, 0 legacy states, tests state machine completos).

**Nota carry-over Sprint 11:** Si S11-10 (Portal B2B) o S11-11 (Módulo Productos) no se completaron en Sprint 11, se incorporan en Fase 2 de este sprint con prioridad P0.

### Incluido

| # | Feature | Fuente | Prioridad |
|---|---------|--------|-----------|
| 1 | Dividir services.py (1,371 líneas) en módulos | DT-15 / OBS-014 | P0 |
| 2 | Colapsar command views en CommandDispatchView | DT-16 / OBS-015 | P1 |
| 3 | Crear useFetch/useCRUD hooks frontend | DT-17 / OBS-024 | P1 |
| 4 | Consolidar modals/drawers duplicados | DT-18 / OBS-025 | P1 |
| 5 | API documentation con drf-spectacular | DT-19 / OBS-045 | P1 |
| 6 | Estandarizar paginación + error responses | DT-20/21 / OBS-046/047 | P1 |
| 7 | Consolidar services_sprint5.py | DT-22 / OBS-021 | P0 |
| 8 | Limpiar backlog bajo esfuerzo (DT-26/27/28) | Backlog | P2 |
| 9 | CI/CD pipeline básica | Nuevo — recomendación Claude Code | P0 |
| 10 | Carry-over Sprint 11 (Portal B2B / Productos si no DONE) | S11-10/11 | P0 si aplica |
| 11 | PLT-10 Módulo Inventario | ENT_GOB_PENDIENTES | P2 |
| 12 | CEO-14 WhatsApp Business API (setup inicial) | CEO-14 | P2 |
| 13 | Tests Sprint 12 | — | P0 |

### Excluido

| Feature | Razón | Cuándo |
|---------|-------|--------|
| API versioning /api/v1/ (DT-23) | Disruptivo, requiere migración clientes | Post-B2B |
| Mensajes error i18n (DT-24) | Cosmético | Backlog |
| Celery Beat DatabaseScheduler (DT-25) | Funcional con schedule estático | Backlog |
| Conector fiscal FacturaProfesional | Dependencia externa | Post-MVP |
| Multi-moneda real | 1 moneda por expediente suficiente | Post-MVP |
| Forecast / inteligencia operativa | Requiere 6+ meses data | Post-MVP |

---

## Constraints obligatorios

### C1. No romper la state machine
Refactorizar services.py y command views SIN cambiar lógica de negocio. Mismos inputs → mismos outputs. Tests de state machine de Sprint 11 deben pasar antes y después.

### C2. Tests como safety net
Antes de refactorizar un archivo, verificar que los tests existentes pasan. Después de refactorizar, los mismos tests deben pasar sin modificación. Si un test falla post-refactor, el refactor introdujo un bug.

### C3. Backwards compatible API
Los endpoints no cambian de path ni de contrato de request/response. CommandDispatchView (S12-03) es consolidación INTERNA — no crea nuevas URLs. Paginación se estandariza con page_size=25 default; vistas existentes que usan más deben tener override documentado. Error responses se envuelven en envelope aditivo preservando `errors` con el shape original de DRF.

### C4. Componentes reutilizables
Nuevos hooks (useFetch, useCRUD) se usan inmediatamente en al menos 3 páginas existentes como prueba de concepto. No se crean hooks que nadie consume.

---

## Items

### FASE 0 — Refactorización backend (estimado 3-4 días)

#### Item S12-01: Dividir services.py en módulos
- **Agente:** AG-02 Backend
- **Archivo actual:** `backend/apps/expedientes/services.py` (1,371 líneas)
- **Qué hacer:**
  1. Crear directorio `backend/apps/expedientes/services/`
  2. Crear `__init__.py` que re-exporte todo (backwards compat)
  3. Dividir en módulos:
     - `services/create.py` — CreateExpediente (C1)
     - `services/commands_registro.py` — C2, C3, C4, C5 (artefactos REGISTRO)
     - `services/commands_produccion.py` — C6 (avance PRODUCCION)
     - `services/commands_preparacion.py` — C7, C8, C9, C10 (artefactos + avance PREPARACION)
     - `services/commands_transito.py` — C11, C12 (avance DESPACHO/TRANSITO)
     - `services/commands_destino.py` — C13, C14, C22 (artefactos + cierre EN_DESTINO)
     - `services/financial.py` — C15 RegisterCostLine, C21 RegisterPayment
     - `services/exceptions.py` — C16 Cancel, C17 Block, C18 Unblock
     - `services/corrections.py` — C19 Supersede, C20 Void
  4. `__init__.py` importa y re-exporta todo para que imports existentes no se rompan

**Matriz de asignación C1-C22 → módulo:**

| Command | Nombre | Módulo destino | Símbolo exportado |
|---------|--------|---------------|-------------------|
| C1 | CreateExpediente | services/create.py | create_expediente |
| C2 | RegisterOC | services/commands_registro.py | register_oc |
| C3 | CreateProforma | services/commands_registro.py | create_proforma |
| C4 | DecideModeBC | services/commands_registro.py | decide_mode_bc |
| C5 | RegisterSAPConfirmation | services/commands_registro.py | register_sap |
| C6 | ConfirmProductionComplete | services/commands_produccion.py | confirm_production |
| C7 | RegisterShipment | services/commands_preparacion.py | register_shipment |
| C8 | RegisterFreightQuote | services/commands_preparacion.py | register_freight |
| C9 | RegisterCustomsDocs | services/commands_preparacion.py | register_customs |
| C10 | ApproveDispatch | services/commands_preparacion.py | approve_dispatch |
| C11 | ConfirmShipmentDeparted | services/commands_transito.py | confirm_departed |
| C12 | ConfirmShipmentArrived | services/commands_transito.py | confirm_arrived |
| C13 | IssueInvoice | services/commands_destino.py | issue_invoice |
| C14 | CloseExpediente | services/commands_destino.py | close_expediente |
| C15 | RegisterCostLine | services/financial.py | register_cost |
| C16 | CancelExpediente | services/exceptions.py | cancel_expediente |
| C17 | BlockExpediente | services/exceptions.py | block_expediente |
| C18 | UnblockExpediente | services/exceptions.py | unblock_expediente |
| C19 | SupersedeArtifact | services/corrections.py | supersede_artifact |
| C20 | VoidArtifact | services/corrections.py | void_artifact |
| C21 | RegisterPayment | services/financial.py | register_payment |
| C22 | IssueCommissionInvoice | services/commands_destino.py | issue_commission |

Todos los 22 símbolos DEBEN estar re-exportados en `services/__init__.py`.
- **Criterio de done:**
  - [ ] services.py eliminado, reemplazado por services/ directorio
  - [ ] `__init__.py` re-exporta todas las funciones/clases públicas
  - [ ] Ningún import en el resto del proyecto se rompe
  - [ ] Tests de state machine pasan sin modificación
  - [ ] Ningún archivo nuevo supera 300 líneas

#### Item S12-02: Consolidar services_sprint5.py
- **Agente:** AG-02 Backend
- **Archivo actual:** `backend/apps/expedientes/services_sprint5.py` (312 líneas)
- **Qué hacer:**
  1. **Primer sub-entregable (antes de mover nada):** inventariar todas las funciones/clases en services_sprint5.py con mapping función → módulo destino en services/. Validar con AG-01.
  2. Mover cada función al módulo apropiado dentro de `services/`
  3. Actualizar imports
  4. Eliminar services_sprint5.py
- **Criterio de done:**
  - [ ] services_sprint5.py eliminado
  - [ ] Funciones integradas en módulos correctos
  - [ ] Tests pasan

#### Item S12-03: Consolidar command views (internamente)
- **Agente:** AG-02 Backend
- **Archivo actual:** `backend/apps/expedientes/views.py` (753 líneas, 18+ clases APIView)
- **Constraint C3:** Los paths públicos NO cambian. CommandDispatchView es consolidación interna.
- **Qué hacer:**
  1. Crear `CommandDispatchView` como handler interno:
     ```python
     class CommandDispatchView(APIView):
         COMMANDS = {
             "register-oc": services.register_oc,
             "create-proforma": services.create_proforma,
             # ... 22 commands mapeados a funciones de services/
         }
         
         def post(self, request, expediente_id, command_name):
             handler = self.COMMANDS.get(command_name)
             if not handler:
                 return Response({"detail": "Unknown command"}, status=404)
             return handler(request, expediente_id)
     ```
  2. Las URLs existentes (POST /api/expedientes/{id}/commands/register-oc/, etc.) siguen siendo las URLs canónicas. Internamente llaman al dispatch.
  3. NO se crea un nuevo path /api/expedientes/{id}/commands/{command_name}/. Solo se consolida el código detrás de las mismas URLs.
  4. Los 18+ APIView de 3 líneas se eliminan, reemplazados por entries en el routing table.
- **Criterio de done:**
  - [ ] Todos los 22 command URLs existentes siguen respondiendo exactamente igual
  - [ ] views.py reducido significativamente (de 753 a ~200 líneas)
  - [ ] Tests pasan sin modificar URLs ni request/response shapes
  - [ ] 0 nuevos paths de API creados

#### Item S12-04: API documentation con drf-spectacular
- **Agente:** AG-02 Backend
- **Qué hacer:**
  1. `pip install drf-spectacular`
  2. Configurar en settings.py
  3. Agregar URLs: `/api/schema/` (YAML) y `/api/docs/` (Swagger UI)
  4. Anotar serializers principales con `@extend_schema`
  5. Verificar que los 22 commands aparecen documentados
- **Archivos:**
  - `backend/config/settings/base.py` — agregar drf-spectacular a INSTALLED_APPS + config
  - `backend/config/urls.py` — agregar rutas schema/docs
- **Criterio de done:**
  - [ ] `/api/docs/` muestra Swagger UI funcional
  - [ ] Los 22 command endpoints están documentados
  - [ ] Serializers principales tienen descriptions

#### Item S12-05: Estandarizar paginación + error responses
- **Agente:** AG-02 Backend

**(A) Paginación**
- Archivo: `backend/config/settings/base.py`
- NO definir `DEFAULT_PAGINATION_CLASS` global (rompe endpoints que hoy devuelven lista plana).
- En cambio, aplicar paginación opt-in por vista con mixin:
  ```python
  # backend/core/pagination.py
  from rest_framework.pagination import PageNumberPagination
  
  class StandardPagination(PageNumberPagination):
      page_size = 25
      page_size_query_param = 'page_size'
      max_page_size = 100
  ```
- Vistas que SÍ migran a paginación en Sprint 12 (allowlist):
  - ExpedienteListView
  - TransferListView
  - LiquidationListView
- Resto de endpoints (brands, clientes, nodos, etc.) quedan devolviendo lista plana hasta post-B2B.
- Criterio: solo endpoints en allowlist devuelven `{ count, next, previous, results }`. El resto sigue flat.

**(B) Error responses**
- Crear `backend/core/exception_handler.py`:
  ```python
  def custom_exception_handler(exc, context):
      response = default_exception_handler(exc, context)
      if response:
          # ADDITIVE: preserve original payload, wrap in envelope
          original = response.data
          response.data = {
              "error": True,
              "code": response.status_code,
              "detail": original.get("detail") if isinstance(original, dict) and "detail" in original else str(original),
              "errors": original,  # preserve original shape for validation errors (dict by field)
          }
      return response
  ```
- Configurar en settings: `REST_FRAMEWORK['EXCEPTION_HANDLER']`
- **Backwards compat:** el campo `errors` preserva el shape original de DRF (dict por campo para validación, string para 404/403). Frontend existente puede seguir leyendo `response.data.errors` con el mismo shape de siempre. El envelope `error/code/detail` es aditivo.
- Criterio: todos los endpoints retornan envelope CON `errors` original intacto. Tests de validación existentes pasan sin modificación.

#### Item S12-06: Limpiar backlog bajo esfuerzo
- **Agente:** AG-02 Backend + AG-03 Frontend

**(A) DT-26: Índices en campos de filtro**
- Agregar `db_index=True` a: Expediente.status, Expediente.client, Expediente.brand, Expediente.created_at
- Crear migración
- Criterio: `grep -rn "db_index" backend/apps/expedientes/models.py` → al menos 4 campos

**(B) DT-27: Limpiar archivos sueltos**
- Mover `fix_tests*.py` y `generate_brands_fixtures.py` de raíz de backend a `backend/scripts/`
- Criterio: `ls backend/fix_tests* backend/generate_* 2>/dev/null` → 0

**(C) DT-28: Eliminar console statements**
- Frontend: eliminar `console.error` y `console.warn` que no sean error handling real
- Reemplazar con logger que se desactive en producción:
  ```typescript
  // frontend/src/lib/logger.ts
  const isDev = process.env.NODE_ENV === "development";
  export const logger = {
    error: (...args: unknown[]) => isDev && console.error(...args),
    warn: (...args: unknown[]) => isDev && console.warn(...args),
  };
  ```
- Criterio: `grep -rn "console\.\(log\|error\|warn\)" frontend/src/ --include="*.tsx" --include="*.ts" | grep -v node_modules | grep -v logger.ts` → 0

---

### FASE 1 — CI/CD (paralelo a Fase 0)

#### Item S12-07: CI/CD pipeline básica
- **Agente:** AG-02 DevOps
- **Qué hacer:**

  1. Crear `.github/workflows/ci.yml`:
     ```yaml
     # Runtime
     python-version: "3.11"
     node-version: "20"
     
     # Services for tests
     services:
       postgres:
         image: postgres:16
         env: { POSTGRES_DB: mwt_test, POSTGRES_PASSWORD: test }
       redis:
         image: redis:7-alpine
     
     # Backend steps
     - pip install -r requirements.txt
     - ruff check backend/
     - bandit -r backend/ -ll  # only HIGH+ severity
     - pytest backend/ --tb=short
     
     # Frontend steps
     - cd frontend && npm ci
     - npx eslint src/ --max-warnings 0
     - npm run build
     - npm test -- --passWithNoTests
     ```
  
  2. Crear `.github/workflows/deploy.yml`:
     ```yaml
     on: push (main, only after CI green)
     steps:
       - SSH to server
       - cd /opt/mwt && git pull
       - docker-compose pull && docker-compose up -d
       - docker-compose exec django python manage.py migrate --noinput
       - sleep 10 && curl -f https://consola.mwt.one/api/health/ || (echo "HEALTHCHECK FAILED" && exit 1)
     ```
     Rollback: if healthcheck fails:
     ```bash
     LAST_GOOD=$(cat /opt/mwt/.last_good_commit)
     git checkout $LAST_GOOD && docker-compose up -d && docker-compose exec django python manage.py migrate --noinput
     ```
     Post-deploy success: `git rev-parse HEAD > /opt/mwt/.last_good_commit`
  
  3. Secrets de GitHub Actions (configurar manualmente en repo Settings > Secrets):
     - `SSH_HOST`, `SSH_USER`, `SSH_KEY` — para deploy
     - `DJANGO_SECRET_KEY` — para tests backend si necesario
  
  4. Branch protection (configurar manualmente en repo Settings > Branches):
     - Require CI passing before merge
     - Require 1 approval (cuando haya 2+ devs)
  
  5. Pre-commit hooks (opcional):
     ```yaml
     # .pre-commit-config.yaml
     repos:
       - repo: https://github.com/astral-sh/ruff-pre-commit
         hooks: [{ id: ruff, args: [--fix] }, { id: ruff-format }]
     ```

- **Archivos a crear:**
  - `.github/workflows/ci.yml`
  - `.github/workflows/deploy.yml`
  - `.pre-commit-config.yaml` (opcional)
  - `backend/pyproject.toml` — configuración Ruff
- **Criterio de done:**
  - [ ] Push a main dispara CI pipeline
  - [ ] CI ejecuta: ruff + bandit + pytest + eslint + build + jest
  - [ ] CI tiene postgres + redis como services para tests
  - [ ] Deploy tiene healthcheck post-deploy + rollback si falla
  - [ ] Secrets configurados en GitHub (no hardcodeados en YAML)
  - [ ] Branch protection: checklist manual confirmado (no es código)

---

### FASE 2 — Refactorización frontend + features (después de Fase 0)

#### Item S12-08: Crear useFetch / useCRUD hooks
- **Agente:** AG-03 Frontend
- **Archivo nuevo:** `frontend/src/hooks/useFetch.ts`, `frontend/src/hooks/useCRUD.ts`
- **Qué hacer:**
  1. `useFetch(url)` — soporta AMBOS formatos: lista plana y paginada DRF:
     ```typescript
     interface PaginatedResponse<T> { count: number; next: string | null; previous: string | null; results: T[]; }
     
     function useFetch<T>(url: string) {
       // Auto-detect: if response has .results array, treat as paginated
       // Expose: { data: T[], total, loading, error, refetch, page, setPage }
     }
     ```
  2. `useCRUD(baseUrl)` — consume useFetch + create/update/delete + toast:
     ```typescript
     const { items, total, loading, create, update, remove, refetch, page, setPage } = useCRUD<Brand>("/api/brands/");
     ```
  3. Migrar al menos 3 páginas existentes como prueba:
     - brands/page.tsx
     - clientes/page.tsx
     - nodos/page.tsx
  4. Verificar que paginación funciona correctamente (page_size=25 del backend)
- **Criterio de done:**
  - [ ] Hooks soportan PaginatedResponse<T> (count/next/previous/results)
  - [ ] Hooks también funcionan con lista plana (backwards compat)
  - [ ] 3 páginas migradas y funcionando con paginación
  - [ ] Tests de hooks (render + fetch mock con respuesta paginada)

#### Item S12-09: Consolidar modals/drawers duplicados
- **Agente:** AG-03 Frontend
- **Archivos afectados:**
  - `frontend/src/components/modals/ArtifactFormDrawer.tsx`
  - `frontend/src/components/modals/RegisterCostDrawer.tsx`
  - `frontend/src/components/modals/RegisterPaymentDrawer.tsx`
  - 5 modals más con estructura repetitiva
- **Qué hacer:**
  1. Evaluar cuáles pueden migrarse a FormModal directamente
  2. Para drawers que deben seguir siendo drawers: crear `DrawerShell.tsx` con patrón reutilizable (Escape, aria-modal, focus, overlay)
  3. Extraer `useFormSubmit(endpoint)` hook para el patrón handleChange → handleSubmit → api.post → toast
  4. Reducir código duplicado ≥50%
- **Criterio de done:**
  - [ ] FormModal o DrawerShell usado como shell en todos los modals/drawers
  - [ ] useFormSubmit hook creado y usado en al menos 3 modals
  - [ ] Código duplicado entre modals reducido ≥50%
  - [ ] Accesibilidad: todos los drawers con role="dialog" + aria-modal

#### Item S12-10: Carry-over Sprint 11 (si aplica)
- **Condicional:** Solo si S11-10 (Portal B2B) o S11-11 (Productos) no se completaron en Sprint 11.
- **Prioridad:** P0 — completar antes de features nuevas.
- **Spec:** Según LOTE_SM_SPRINT11 v2.1 (stamp: aprobado ChatGPT 9.6/10 R2).

**Criterio DONE resumido de Portal B2B (S11-10):**
  - [ ] Cliente logueado ve solo SUS expedientes (ClientScopedManager)
  - [ ] 0 datos CEO-ONLY expuestos
  - [ ] Documentos via signed URLs (30min expiry)
  - [ ] Tests negativos: cross-tenant 404, signed URL expiry, knowledge scope

**Criterio DONE resumido de Productos (S11-11):**
  - [ ] CRUD completo (nombre, SKU, brand FK, categoría)
  - [ ] Filtro por brand
  - [ ] FormModal + ConfirmDialog
  - [ ] Sidebar actualizado

#### Item S12-11: PLT-10 Módulo Inventario
- **Agente:** AG-03 Frontend + AG-02 Backend
- **Dependencia:** PLT-09 (Productos) DONE — ya sea en Sprint 11 o Sprint 12 carry-over
- **Archivo frontend:** Crear `inventario/page.tsx` dentro del route tree activo
- **Ruta URL:** `/{lang}/dashboard/inventario`

**Scope:**
- CRUD de inventario: producto (FK), nodo (FK), cantidad, cantidad reservada, lote, fecha ingreso
- Vista por nodo: ¿cuánto hay en cada nodo?
- Vista por producto: ¿dónde está cada producto?
- Alertas de stock bajo (configurable por producto)
- FormModal + ConfirmDialog
- Endpoints: GET/POST /api/inventario/, PUT/DELETE /api/inventario/{id}/, GET /api/inventario/by-node/{node_id}/, GET /api/inventario/by-product/{product_id}/

**Backend modelo:**
```python
class InventoryEntry(models.Model):
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    node = models.ForeignKey(Node, on_delete=models.PROTECT)
    quantity = models.IntegerField(default=0)
    reserved = models.IntegerField(default=0)  # comprometido en expedientes
    lot_number = models.CharField(max_length=50, blank=True)
    received_at = models.DateTimeField()  # obligatorio desde UI/API, no tiene default
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('product', 'node', 'lot_number')
        indexes = [
            models.Index(fields=['product', 'node']),
            models.Index(fields=['node']),
        ]
    
    @property
    def available(self):
        return self.quantity - self.reserved
```

- **Criterio de done:**
  - [ ] CRUD completo
  - [ ] Vista por nodo y por producto
  - [ ] Usa useFetch/useCRUD hooks de S12-08 (si están listos)
  - [ ] FormModal + ConfirmDialog
  - [ ] Sidebar actualizado
  - [ ] Design system aplicado

#### Item S12-12: CEO-14 WhatsApp Business API (setup inicial)
- **Agente:** AG-02 Backend
- **Dependencia:** Portal B2B DONE (necesita tenant model)

**Prerequisitos externos (CEO debe completar ANTES de que Ale arranque):**
- [ ] Cuenta Meta Business verificada (puede tomar 1-7 días)
- [ ] WhatsApp Business API habilitada en Meta dashboard
- [ ] Template de mensaje enviado a Meta para aprobación (puede tomar 1-3 días)
Si estos prerequisitos no están listos cuando Ale llega a S12-12, este item se pasa a Sprint 13.

**Entregables internos (Ale implementa):**
- Webhook endpoint: `POST /api/webhooks/whatsapp/` en `backend/apps/integrations/views.py`
- Modelo: `WhatsAppMessage` en `backend/apps/integrations/models.py` (log de mensajes)
- Celery task: trigger por event_log de transición de estado → envío via WhatsApp API
- Consola CEO: tabla de mensajes enviados en `/{lang}/dashboard/whatsapp/`
- Template de mensaje: "Actualización expediente {ref}: {status_label}" (usar el template aprobado por Meta)

**NO incluido en Sprint 12:**
- Conversaciones bidireccionales (cliente responde)
- Bot automático / NLP
- Multimedia (solo texto)

- **Criterio de done (entregables internos):**
  - [ ] Webhook creado y recibe test ping de Meta
  - [ ] Modelo WhatsAppMessage con campos: expediente_id, client_phone, template_used, status, sent_at
  - [ ] Celery task: al menos 1 transición de estado dispara envío
  - [ ] Log visible en consola CEO
  - [ ] Si template de Meta NO aprobado: todo lo anterior funciona con mock/dry-run, se activa cuando template llega

---

### QA

#### Item S12-13: Tests Sprint 12
- **Dependencia:** Items 1-12

**Refactorización (constraint C1/C2):**
- [ ] Tests de state machine de Sprint 11 pasan sin modificación post-refactor
- [ ] Los 22 commands funcionan end-to-end vía CommandDispatchView (mismas URLs, mismos request/response)
- [ ] API docs (/api/docs/) muestran todos los endpoints
- [ ] TEST CONTRACTUAL: para cada command, comparar response shape legacy (pre-refactor snapshot) vs post-refactor → idéntico
- [ ] TEST custom_exception_handler: 400 ValidationError retorna { error, code, detail, errors: {field: [...]} }
- [ ] TEST custom_exception_handler: 403 PermissionDenied retorna { error, code, detail, errors: "..." }
- [ ] TEST custom_exception_handler: 404 NotFound retorna { error, code, detail, errors: "..." }

**Frontend:**
- [ ] useFetch/useCRUD hooks funcionan en 3+ páginas con respuestas paginadas
- [ ] Modals consolidados mantienen funcionalidad (crear/editar/eliminar)
- [ ] 0 console.log/error/warn fuera de logger.ts
- [ ] Tests de hooks: `frontend/src/hooks/__tests__/useFetch.test.ts`, `useCRUD.test.ts`
- [ ] Tests de modals: `frontend/src/components/modals/__tests__/` al menos 1 por drawer migrado

**CI/CD:**
- [ ] Push a main dispara CI
- [ ] CI falla si lint o tests fallan
- [ ] Bandit 0 HIGH severity

**Inventario (si se implementó):**
- [ ] CRUD funcional
- [ ] Vista por nodo y por producto
- [ ] Stock disponible = quantity - reserved

**WhatsApp (si se implementó):**
- [ ] Webhook recibe test message
- [ ] Transición de estado → notificación enviada
- [ ] Log visible en consola

**Regresión:**
- [ ] Acordeón Sprint 10 funciona
- [ ] Portal B2B (Sprint 11) funciona (si aplica)
- [ ] Pipeline, CRUD Nodos/Brands/Clientes funciona

---

## Dependencias internas

```
S12-01 (services.py split) ──┐
S12-02 (services_sprint5) ────┤── Fase 0 bloque 1 (backend refactor)
S12-03 (command views) ────────┤   S12-03 depende de S12-01
S12-04 (API docs) ─────────────┤   independiente
S12-05 (pagination + errors) ──┤
S12-06 (backlog cleanup) ──────┤

S12-07 (CI/CD) ─────────────────── Fase 1 (paralelo a Fase 0)

S12-08 (hooks frontend) ──────┤── Fase 2
S12-09 (modals consolidate) ──┤   independiente de S12-08
S12-10 (carry-over S11) ──────┤   P0 si aplica
S12-11 (Inventario) ───────────┤   depende de PLT-09 DONE (sea S11-11 o S12-10)
S12-12 (WhatsApp) ─────────────┤   depende de Portal B2B DONE (sea S11-10 o S12-10)
                                    + prerequisitos externos Meta

Si Productos viene como carry-over: S12-11 bloqueado por S12-10 (Productos).
Si Portal B2B viene como carry-over: S12-12 bloqueado por S12-10 (Portal B2B).

S12-13 (Tests) ─────────────────── después de todo
```

---

## Criterio Sprint 12 DONE

### Obligatorio
1. services.py dividido en módulos, ninguno >300 líneas
2. services_sprint5.py eliminado e integrado
3. CommandDispatchView funcional detrás de las URLs existentes; 0 nuevos paths públicos; mismo request/response shape
4. API docs en /api/docs/ con Swagger UI
5. Paginación y error responses estandarizados
6. CI pipeline verde en main
7. 0 console statements fuera de logger
8. Tests de state machine pasan sin modificación
9. Sin regresiones Sprint 10/11

### Deseable
10. useFetch/useCRUD hooks usados en 3+ páginas
11. Modals consolidados (≥50% reducción duplicación)
12. Inventario CRUD funcional
13. WhatsApp: al menos 1 notificación end-to-end

---

## Retrospectiva
(Completar al cerrar el sprint)

---

Stamp: DRAFT v2.1 — Arquitecto (Claude Opus) 2026-03-18. Auditoría ChatGPT: R1 8.5 → R2 9.3 → R3 pendiente (14 fixes acumulados).
