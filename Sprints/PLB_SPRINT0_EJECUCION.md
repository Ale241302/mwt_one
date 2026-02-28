# PLB_SPRINT0_EJECUCION — Plan Operativo Sprint 0
status: DRAFT
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
version: 1.0
tipo: Playbook (instrucción operativa)
refs: PLB_ORCHESTRATOR v1.2.2 §G (LOTE_SM_SPRINT0), ENT_PLAT_INFRA, ENT_OPS_STATE_MACHINE v1.2.2
prerrequisito: Ninguno — Sprint 0 es el primer sprint

---

# QUÉ ES SPRINT 0

Sprint 0 levanta la infraestructura: el servidor Docker con todos los servicios y los modelos de datos Django. No hay endpoints, no hay API, no hay UI. Solo la base sobre la que se construye todo lo demás.

Al terminar Sprint 0, el sistema:
- Tiene 6 contenedores Docker corriendo (django, postgres, nginx, minio, celery-worker, celery-beat)
- Django admin funciona en mwt.one
- Los modelos de Expediente, ArtifactInstance, EventLog, CostLine, PaymentLine existen como tablas en PostgreSQL
- Un superuser CEO puede entrar al admin
- Nada más. No hay endpoints. No se pueden hacer operaciones. Eso es Sprint 1.

---

# ITEMS (5 items, 2 agentes)

## Visión general

```
Item 1: Docker Compose + Infra (AG-07 DevOps)
    │
    └── Item 2: Django Project Init + Core Base (AG-01 Architect)
            │
            ├── Item 3: Modelos LegalEntity + Expediente (AG-01)
            │       │
            │       ├── Item 4A: Modelos Artifact + Outbox (AG-01)
            │       │
            │       └── Item 4B: Modelos Ledger — CostLine + PaymentLine (AG-01)
            │
            └── Item 5: Aplicar migraciones en entorno (AG-07 DevOps)
```

---

## Item 1: Docker Compose MVP + Infra Settings

**Agente:** AG-07 DevOps
**Dependencia:** Ninguna — es el primer item de todo el proyecto.

**Qué hace:** Crea el docker-compose.yml con los 6 servicios, el Dockerfile del backend, la configuración de nginx, y el .env con las variables de entorno. Configura base.py con PostgreSQL, MinIO, Celery y Redis.

**Archivos permitidos:** docker-compose.yml, backend/Dockerfile, nginx/mwt.conf, .env.template, config/settings/base.py (secciones DB, Redis, MinIO, Celery, logging, static/media).
**Archivos prohibidos:** apps/*, tests/*.

**Los 6 contenedores:**

| Contenedor | Imagen | Función |
|-----------|--------|---------|
| django | Custom (Dockerfile) | Backend Django + Gunicorn |
| postgres | postgres:16 | Base de datos |
| nginx | nginx:alpine | Reverse proxy, SSL |
| minio | minio/minio | Object storage (docs, facturas) |
| celery-worker | Misma que django | Tasks asíncronos |
| celery-beat | Misma que django | Scheduler cron |

**Verificación (que Ale debe correr):**
```bash
# Todos los contenedores levantados
docker-compose ps
# Todos deben mostrar "Up" o "healthy"

# Django responde
curl http://localhost:8000/admin/
# Debe cargar la página de login del admin

# mwt.one responde (si DNS está listo)
curl https://mwt.one/admin/

# MinIO accesible
curl http://localhost:9001
# Debe cargar la consola de MinIO

# PostgreSQL aceptando conexiones
docker-compose exec postgres pg_isready
# Debe responder: accepting connections

# Celery worker registrado
docker-compose exec django celery -A config inspect ping
# Debe responder: pong

# Celery Beat corriendo
docker-compose ps | grep beat
# Debe mostrar "Up"
```

**⚠️ Troubleshooting esperado para Ale:**

- **"Port already in use"**: Verificar que no hay otro servicio usando 5432 (postgres), 6379 (redis), 9000/9001 (minio), 80/443 (nginx). Usar `lsof -i :PUERTO` para verificar.
- **django no arranca**: Revisar logs con `docker-compose logs django`. Error común: no encuentra módulo de settings. Verificar que DJANGO_SETTINGS_MODULE está en .env.
- **postgres "password authentication failed"**: Verificar que POSTGRES_PASSWORD en .env coincide con lo configurado en base.py.
- **minio no arranca**: Verificar que las variables MINIO_ROOT_USER y MINIO_ROOT_PASSWORD están en .env.
- **celery-worker no se conecta a redis**: Verificar que redis está corriendo y que CELERY_BROKER_URL en base.py apunta a redis://redis:6379/0 (nombre del servicio Docker, no localhost).
- **nginx 502 Bad Gateway**: django no está listo aún. Esperar a que django arranque. Verificar que upstream en nginx.conf apunta al nombre correcto del servicio.
- **"No module named 'config'"**: El Dockerfile no está copiando el código correctamente. Verificar WORKDIR y COPY en Dockerfile.

**Criterio de done:**
1. 6 contenedores corriendo y healthy
2. Django admin accesible
3. MinIO console accesible
4. PostgreSQL aceptando conexiones
5. Celery worker registrado (ping → pong)
6. Celery Beat corriendo

**Branch:** sprint0/item-1-docker-infra

---

## Item 2: Django Project Init + Core Base

**Agente:** AG-01 Architect
**Dependencia:** Item 1 aprobado (stack corriendo).

**Qué hace:** Crea la estructura de carpetas apps/, el proyecto Django base, y los modelos fundacionales en apps/core/ (TimestampMixin, AppendOnlyModel que otros modelos heredan).

**Archivos permitidos:** config/settings/base.py (solo INSTALLED_APPS), config/urls.py, apps/core/models.py, apps/core/apps.py.
**Archivos prohibidos:** docker-compose.yml, nginx/*, config/settings/base.py (secciones de infra).

**Qué contiene apps/core/models.py:**
- `TimestampMixin`: agrega created_at y updated_at a cualquier modelo que lo herede
- `AppendOnlyModel`: modelo base que no permite updates ni deletes (para CostLine, PaymentLine, EventLog)

**Verificación:**
```bash
# Dentro del contenedor django
docker-compose exec django python manage.py check
# Debe reportar: System check identified no issues

docker-compose exec django python manage.py makemigrations core
# Debe generar migración (o decir "No changes detected" si ya se generó)
```

**⚠️ Troubleshooting para Ale:**
- **"No module named 'apps.core'"**: Falta agregar 'apps.core' a INSTALLED_APPS en base.py.
- **"ModuleNotFoundError"**: La estructura de carpetas no coincide. Verificar que apps/core/__init__.py existe.
- **AppConfig conflict**: Verificar que apps/core/apps.py tiene name='apps.core', no solo 'core'.

**Criterio de done:**
1. Estructura apps/ creada
2. INSTALLED_APPS actualizado con core
3. TimestampMixin y AppendOnlyModel en apps/core/models.py
4. manage.py funciona dentro del contenedor
5. Migración core generada

**Branch:** sprint0/item-2-django-init

---

## Item 3: Modelos LegalEntity + Expediente

**Agente:** AG-01 Architect
**Dependencia:** Item 2 aprobado.

**Qué hace:** Crea los dos modelos principales del negocio: LegalEntity (empresas que participan en importaciones) y Expediente (el proceso de importación, con su state machine de 8 estados).

**Archivos permitidos:** apps/expedientes/models.py, apps/expedientes/enums.py, apps/expedientes/apps.py, apps/expedientes/admin.py.
**Archivos prohibidos:** views.py, serializers.py, tests/*.

**Modelo Expediente — campos clave:**
- status: enum con 8 estados (REGISTRO, PRODUCCION, PREPARACION, DESPACHO, TRANSITO, EN_DESTINO, CERRADO, CANCELADO)
- is_blocked, blocked_by_type, blocked_by_id, blocked_at, blocked_reason
- payment_status (pending, partial, paid)
- credit_clock_start_rule (on_creation, on_shipment)
- credit_clock_started_at (timestamp nullable)
- brand, client (FK a LegalEntity), mode, freight_mode, transport_mode, dispatch_mode

**Fuente de verdad:** ENT_OPS_STATE_MACHINE §A (estados), §C (bloqueo), §D (reloj), §L (pagos).

**Verificación:**
```bash
docker-compose exec django python manage.py makemigrations expedientes
# Debe generar migración

docker-compose exec django python manage.py check
# Sin errores
```

**⚠️ Troubleshooting para Ale:**
- **FK a LegalEntity**: El modelo Expediente tiene FK a LegalEntity. Si LegalEntity está en apps/core/ o apps/expedientes/, verificar que la referencia es correcta.
- **Enum conflicts**: Python enums en Django se usan via choices en el campo. Verificar que enums.py define correctamente los choices.

**Criterio de done:**
1. LegalEntity model con campos de ENT_PLAT_LEGAL_ENTITY
2. Expediente model con status (8 estados), bloqueo, payment_status, credit_clock
3. Migraciones generadas sin errores
4. Admin registrado

**Branch:** sprint0/item-3-models-expediente

---

## Item 4A: Modelos Artifact + Outbox (ArtifactInstance, EventLog)

**Agente:** AG-01 Architect
**Dependencia:** Item 3 aprobado.

**Qué hace:** Crea ArtifactInstance (documentos asociados al expediente: OC, proforma, AWB, factura, etc.) y EventLog (tabla append-only que registra todo lo que pasa — el "outbox").

**Archivos permitidos:** apps/expedientes/models.py (extender), apps/expedientes/managers.py.
**Archivos prohibidos:** views.py, serializers.py, tests/*.

**ArtifactInstance — campos clave:**
- type: enum (ART-01 a ART-12)
- status: enum (draft, completed, superseded, void)
- payload: JSONField (contenido del artefacto)
- expediente: FK
- validation_rules: según tipo

**EventLog — 10 campos de §K:**
- expediente FK, event_type, emitted_by, occurred_at, processed_at, actor_type, actor_id, previous_state, new_state, payload

**Fuente de verdad:** ENT_OPS_STATE_MACHINE §K (EventLog), §E (artifacts).

**Criterio de done:**
1. ArtifactInstance model funcional
2. EventLog model (outbox) con 10 campos de §K
3. Migraciones generadas sin errores
4. Admin registrado

**Branch:** sprint0/item-4a-models-artifact-outbox

---

## Item 4B: Modelos Ledger (CostLine, PaymentLine)

**Agente:** AG-01 Architect
**Dependencia:** Item 3 aprobado (puede correr en paralelo con 4A).

**Qué hace:** Crea CostLine (costos del expediente) y PaymentLine (pagos recibidos). Ambos son AppendOnlyModel — no se editan ni borran.

**Archivos permitidos:** apps/expedientes/models.py (extender).
**Archivos prohibidos:** views.py, serializers.py, tests/*.

**CostLine:** cost_type, amount, currency, phase, description, expediente FK.
**PaymentLine:** amount, currency, method, reference, expediente FK.

**Fuente de verdad:** ENT_OPS_STATE_MACHINE §F2 (CostLine), §L1 (PaymentLine).

**Criterio de done:**
1. CostLine model (AppendOnlyModel) con campos de §F2
2. PaymentLine model (AppendOnlyModel) con campos de §L1
3. Migraciones generadas sin errores
4. Admin registrado

**Branch:** sprint0/item-4b-models-ledger

---

## Item 5: Aplicar Migraciones en Entorno

**Agente:** AG-07 DevOps
**Dependencia:** Items 2, 3, 4A, 4B todos aprobados (migraciones generadas).

**Qué hace:** Aplica todas las migraciones en el entorno Docker, verifica que las tablas existen en PostgreSQL, y crea el superuser CEO.

**Archivos permitidos:** scripts/infra/migrate.sh (si aplica).
**Archivos prohibidos:** apps/*, models.py.

**Verificación:**
```bash
# Aplicar migraciones
docker-compose exec django python manage.py migrate
# Debe aplicar todas las migraciones sin errores

# Verificar tablas en PostgreSQL
docker-compose exec postgres psql -U mwt -d mwt_db -c "\dt"
# Debe mostrar tablas: core_*, expedientes_expediente, expedientes_legalentity,
# expedientes_artifactinstance, expedientes_eventlog, expedientes_costline, expedientes_paymentline

# Crear superuser
docker-compose exec django python manage.py createsuperuser
# Seguir instrucciones (email CEO, password)

# Verificar login
# Ir a mwt.one/admin/ → loguearse con superuser → debe funcionar
```

**Criterio de done:**
1. migrate corre sin errores
2. Tablas creadas verificables en PostgreSQL
3. Superuser CEO creado y puede loguearse al admin

**Branch:** sprint0/item-5-migrations

---

# ORDEN DE EJECUCIÓN

```
Día 1:
  → Item 1 (Docker) — EL MÁS LENTO. Ale va a pelear con Docker.
    Despachar a Antigravity con prompt de Item 1.
    Iterar hasta que los 6 contenedores levanten y pasen verificación.

Día 2:
  → Item 2 (Django init) — Rápido si Item 1 funciona.
  → Item 3 (Modelos principales) — Secuencial después de Item 2.

Día 3:
  → Item 4A + 4B (pueden ir en paralelo) — Extienden modelos.
  → Item 5 (Migraciones) — Último: aplica todo y crea superuser.
```

**Tiempo realista:** 4-6 días (con curva Docker de Ale).

---

# CRITERIO DE CIERRE SPRINT 0

Sprint 0 está DONE cuando:
1. docker-compose up levanta los 6 contenedores sin errores
2. Django admin funciona en mwt.one
3. Modelos Expediente, LegalEntity, ArtifactInstance, EventLog, CostLine, PaymentLine existen como tablas
4. Superuser CEO puede loguearse
5. manage.py check sin errores
6. manage.py migrate sin errores

**Lo que NO debe existir al cerrar Sprint 0:**
- Endpoints / API
- Serializers, views, urls (más allá del admin)
- Tests
- Lógica de dominio (services.py)
- Frontend

---

# CUÁNDO ESCALAR AL CEO

- Docker no levanta después de 3 intentos con Antigravity
- PostgreSQL no acepta conexiones
- Conflicto en config/settings/base.py entre AG-07 y AG-01
- Antigravity genera modelos con campos que no están en la spec
- Antigravity intenta crear endpoints, serializers o tests
- Algo de Sprint 1 se filtra en Sprint 0

---

Stamp: DRAFT — Pendiente aprobación CEO
