# Resumen del Sprint 10

Este documento detalla todas las tareas completadas durante el **Sprint 10**, describiendo el progreso, las acciones tomadas y los archivos clave que fueron modificados a lo largo del flujo de trabajo, tanto en Backend como en Frontend y Ops.

---

## Tareas Completadas

### 1. S10-01 — Usuarios: Edit + Delete (Backend y Frontend)
* **Qué se hizo:** Se habilitaron las operaciones de edición (datos prellenados) y eliminación lógica (soft delete) en el módulo de usuarios. Se incluyeron salvaguardas en el backend para evitar eliminar al último administrador, y en el frontend se implementaron componentes estándar (`FormModal` y `ConfirmDialog`) con manejo del estado de carga (loading states).
* **Archivos modificados:**
  * **Frontend:** `frontend/src/app/[lang]/(mwt)/(dashboard)/usuarios/page.tsx`
  * **Backend:** Endpoints `PUT` y `DELETE` en `/api/admin/users/{id}/`.

### 2. S10-02 — Transfers: Edit + Delete (Backend y Frontend)
* **Qué se hizo:** Se habilitaron las operaciones de actualización parcial y eliminación para las transferencias (Transfers). El modal de frontend pre-carga campos como origen, destino, ítems y estado.
* **Archivos modificados:**
  * **Frontend:** `frontend/src/app/[lang]/(mwt)/(dashboard)/transfers/page.tsx`
  * **Backend:** Endpoints `PUT` y `DELETE` en `/api/transfers/{id}/`.

### 3. S10-03 — Detalle expediente con Acordeón de Artefactos
* **Qué se hizo:** Se rediseñó por completo la página de detalles de expediente. Se incluyó un timeline de progreso nativo, un bloque acordeón colapsable por estado (`<details> / aria-expanded`), secciones de costos transaccionales con *toggle* visual, y manejadores lógicos de control (`blockReason`, `canRegister`) consumiendo el atributo `required_to_advance` para proteger el avance de los estados.
* **Archivos modificados:**
  * **Frontend:** Reescritura masiva de `frontend/src/app/[lang]/(mwt)/(dashboard)/expedientes/[id]/page.tsx`, `states.ts`, `globals.css` y creación de `ExpedienteAccordion.tsx`, `ArtifactRow.tsx`, `GateMessage.tsx` y `CostTable.tsx`.

### 4. S10-04 — ArtifactModal x 10 Formularios y C22 IssueCommissionInvoice
* **Qué se hizo:** Centralización de las subidas de los 10 artefactos bajo un único contenedor o *shell* envolvente (`ArtifactModal`). Las cargas con archivos (ej. ART-01) manejan `multipart/form-data` apropiadamente. Se implementó el comando de cobro de comisión `C22` de backend para insertar `ART-10` cuando la carga está en estado final local (EN_DESTINO) bajo un modelo COMISION.
* **Archivos modificados:**
  * **Frontend:** `frontend/src/components/expediente/ArtifactModal.tsx`
  * **Backend:** Endpoints y lógicas de comandos de expedientes en `backend/apps/expedientes/views.py` / `commands.py`.

### 5. S10-05 — Dashboard Mejorado (Backend y Frontend)
* **Qué se hizo:** Se rediseñó el panel principal inicial (*Dashboard*). Integrado el mini-pipeline interactivo de los 6 estados operacionales que reportan contadores dinámicos del backend (`by_status`). Además, se agregó la sección de "Próximas Acciones" para priorizar expedientes bloqueados o pendientes top 3.
* **Archivos modificados:**
  * **Frontend:** `frontend/src/app/[lang]/(mwt)/(dashboard)/page.tsx`
  * **Backend:** Query analytics en `backend/apps/expedientes/views.py` (endpoint `/api/ui/dashboard/`).

### 6. S10-06 — Security Hardening (Infraestructura, Red, JWT)
* **Qué se hizo:** Blindaje contra extracción de datos o fuerza bruta. Implementación de *Rate Limiting* estricto tanto en proxy inverso (`20r/m`) como en aplicación. Revisión global de contraseñas, activación de clave mandatoria `requirepass` en el contenedor caché de Redis, y ajustes a la expiración de sesiones JWT. Auditoría de control usando `gitleaks` para eliminar hallazgos de secretos expuestos.
* **Archivos modificados:**
  * **Infra:** Configuración Nginx (`nginx/mwt.conf`), orquestación `docker-compose.yml`, archivo de variables `.env`.
  * **Backend:** Configuración Django `backend/mwt_one/settings.py` (ó `base.py`).

### 7. S10-07 — Corrección Microservicio Knowledge (`/ask/`) + pgvector
* **Qué se hizo:** Se corrigió un error persistente (HTTP 500) en el microservicio FastAPI en el contenedor `mwt-knowledge`.
  1. Se forzó la carga de la extensión de base de datos `pgvector` inicializando adecuadamente `init_db()` en la rutina `startup` para crear la tabla de fragmentos y el motor de búsqueda léxica.
  2. Integración de `requirepass` en la inyección de conexión de la URL cliente de Redis (`REDIS_URL`).
  3. Ejecución del Python indexer recursivo (`indexer.py`) omitiendo archivos tipo CEO-ONLY, cargando el `knowledge_chunks` vectorizado con Open AI model `text-embedding-3-small`.
  4. Corrección de una incompatibilidad de Modelos de Base de Datos entre Django (`bigint`) y FastAPI al inyectar identificadores directos en cadena como *"admin"* al guardar el historial en `knowledge_conversationlog`.
* **Archivos modificados:**
  * **Backend Knowledge:** `backend/apps/knowledge/knowledge_service/main.py`, `backend/apps/knowledge/knowledge_service/routers/ask.py`, `backend/apps/knowledge/knowledge_service/indexer.py`
  * **Backend Django:** Migraciones `backend/apps/knowledge/models.py`.

---

## Token JWT Autorizado de Acceso Directo a Knowledge (S10-07)
Este token JWT vitalicio fue generado sin fecha de expiración utilizando el `SECRET_KEY` de producción, abarcando las políticas restrictivas de consulta embebidas (`ASK_KNOWLEDGE_OPS`, `ASK_KNOWLEDGE_PRODUCTS`, `ASK_KNOWLEDGE_PRICING`, e `INDEX_KNOWLEDGE`).

```text
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiYWRtaW4iLCJwZXJtaXNzaW9ucyI6WyJBU0tfS05PV0xFREdFX09QUyIsIkFTS19LTk9XTEVER0VfUFJPRFVDVFMiLCJBU0tfS05PV0xFREdFX1BSSUNJTkciLCJJTkRFWF9LTk9XTEVER0UiXX0.H5d54w_U__Hi_UQZimbom_b8Gim8hH-ivEpfUwPUryQ
```

---

*Fin del resumen Sprint 10.*
