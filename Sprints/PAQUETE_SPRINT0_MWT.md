# PAQUETE DE ARRANQUE — Sprint 0 MWT.ONE
refs: PLB_ORCHESTRATOR v1.2.2 (FROZEN), LOTE_SM_SPRINT0 (FROZEN), ENT_OPS_STATE_MACHINE (FROZEN), LOTE_SM_SPRINT1 (FROZEN)
fecha: 2026-02-26
status: Ejecutable

---

# 1. RESUMEN EJECUTIVO

Sprint 0 transforma tres documentos congelados en infraestructura real y modelos de dominio funcionales. El resultado es una base Django operativa con 6 modelos (LegalEntity, Expediente, ArtifactInstance, EventLog, CostLine, PaymentLine) dentro de un stack Docker de 6 contenedores, lista para recibir los 18 command endpoints de Sprint 1.

El sprint tiene 6 items distribuidos en 2 agentes: AG-07 DevOps (infraestructura) y AG-01 Architect (dominio). El CEO actúa como orquestador — valida cada item y autoriza handoffs entre agentes. El desarrollador Ale opera Antigravity como herramienta de ejecución, revisando y aprobando cada output antes de integrar.

La ejecución es estrictamente serializada en 3 fases: AG-07 levanta stack → AG-01 crea modelos (4 items secuenciales) → AG-07 aplica migraciones. Ningún agente hace merge final. Todo output es patch que el CEO (Ale en rol operativo) integra.

El criterio de éxito es binario: `python manage.py migrate` corre sin errores, Django admin muestra los 6 modelos, y los campos son trazables 1:1 a ENT_OPS_STATE_MACHINE y ENT_PLAT_LEGAL_ENTITY.

---

# 2. PLAN DE EJECUCIÓN PARA ANTIGRAVITY (Sprint 0)

## 2.1 Secuencia real de ejecución

Sprint 0 tiene 6 items en 3 fases con 2 handoffs entre agentes.

```
FASE A — Infraestructura (AG-07 DevOps)
│
└── Item 1: Docker Compose MVP + Infra Settings
    Handoff → CEO valida healthchecks → desbloquea Fase B

FASE B — Dominio (AG-01 Architect)
│
├── Item 2: Django Project Init + Core Base
│   └── Item 3: Modelos LegalEntity + Expediente
│       ├── Item 4A: ArtifactInstance + EventLog (outbox)
│       └── Item 4B: CostLine + PaymentLine (ledgers)
│
Handoff → CEO valida modelos completos → desbloquea Fase C

FASE C — Integración (AG-07 DevOps)
│
└── Item 5: Aplicar migraciones en entorno
```

Items 4A y 4B no dependen entre sí (ambos dependen de Item 3). Mismo agente, se ejecutan en secuencia.

## 2.2 Desglose por item

### Item 1: Docker Compose MVP + Infra Settings

Agente: AG-07 DevOps.
Objetivo: Stack Docker operativo con 6 contenedores y configuración de infraestructura.

Archivos permitidos: docker-compose.yml, backend/Dockerfile, nginx/mwt.conf, .env.template, config/settings/base.py (secciones de infra: DATABASE, CACHES, MINIO, CELERY, LOGGING, STATIC/MEDIA).

Archivos prohibidos: todo dentro de apps/, todo dentro de tests/, config/settings/base.py sección INSTALLED_APPS.

Precondiciones: servidor KVM 8 accesible, Docker + Docker Compose instalados, dominio mwt.one apuntando al servidor (o IP directa).

Criterios de done:
- docker-compose.yml con 6 servicios: django, postgres, nginx, minio, celery-worker, celery-beat
- Healthcheck por contenedor: django healthy, postgres accepting connections, minio healthy, celery worker registered, celery beat running
- mwt.one responde en navegador (SSL si DNS listo, HTTP si no)
- Django admin accesible en navegador (sin modelos custom aún)
- MinIO console accesible
- config/settings/base.py con PostgreSQL 16, MinIO, Celery + Redis, logging configurados

Nota sobre contenedores MVP: ENT_PLAT_INFRA.B lista 12 contenedores para el stack completo. Sprint 0 solo levanta 6: django, postgres, nginx, minio, celery-worker, celery-beat. Next.js, n8n, Windmill, portal quedan fuera.

Evidencia mínima para validación CEO:
- Output de `docker ps` mostrando 6 contenedores healthy
- Django admin respondiendo en navegador
- MinIO console accesible
- .env.template con todas las variables documentadas

### Item 2: Django Project Init + Core Base

Agente: AG-01 Architect.
Objetivo: Estructura base del proyecto con mixins abstractos.

Archivos permitidos: config/settings/base.py (solo INSTALLED_APPS), config/urls.py, apps/core/models.py, apps/core/apps.py.

Archivos prohibidos: docker-compose.yml, nginx/*, config/settings/base.py secciones de infra.

Precondiciones: Item 1 aprobado por CEO.

Criterios de done:
- Directorio apps/ creado con apps/core/ registrada
- INSTALLED_APPS actualizado con apps.core
- TimestampMixin en apps/core/models.py: created_at (auto_now_add), updated_at (auto_now), Meta abstract=True
- AppendOnlyModel en apps/core/models.py: hereda TimestampMixin, override de delete() lanza ProtectedError, override de save() solo permite si pk is None (insert-only), Meta abstract=True
- manage.py funciona dentro del contenedor
- Migración core generada sin errores

Evidencia mínima: output de `python manage.py check` sin errores, output de makemigrations con migración de core, contenido de apps/core/models.py verificable.

### Item 3: Modelos LegalEntity + Expediente

Agente: AG-01 Architect.
Objetivo: Los dos modelos centrales del sistema, campos derivados directamente de specs congeladas.

Archivos permitidos: apps/expedientes/models.py, apps/expedientes/enums.py, apps/expedientes/apps.py, apps/expedientes/admin.py.

Archivos prohibidos: views.py, serializers.py, urls.py, tests/*.

Precondiciones: Item 2 aprobado.

Campos LegalEntity (ref → ENT_PLAT_LEGAL_ENTITY.B):
- entity_id: CharField, unique (MWT-CR, SONDEL-CR, etc.)
- legal_name: CharField
- country: CharField (código ISO)
- tax_id: CharField, nullable
- role: TextChoices — OWNER, DISTRIBUTOR, SUBDISTRIBUTOR, THREEPL, FACTORY
- relationship_to_mwt: TextChoices — SELF, FRANCHISE, DISTRIBUTION, SERVICE
- frontend: TextChoices — MWT_ONE, PORTAL_MWT_ONE, EXTERNAL
- visibility_level: TextChoices — FULL, PARTNER, LIMITED
- pricing_visibility: TextChoices — INTERNAL, CLIENT, NONE
- status: TextChoices — ACTIVE, ONBOARDING, INACTIVE
- Hereda TimestampMixin

Campos Expediente (ref → ENT_OPS_STATE_MACHINE §A, §C, §D, §L):
- expediente_id: UUIDField, PK
- legal_entity: FK → LegalEntity (entidad emisora)
- brand: TextChoices — MARLUVAS (MVP)
- client: FK → LegalEntity (el cliente)
- status: TextChoices (8 estados) — REGISTRO, PRODUCCION, PREPARACION, DESPACHO, TRANSITO, EN_DESTINO, CERRADO, CANCELADO
- is_blocked: BooleanField, default=False
- blocked_reason: TextField, nullable
- blocked_at: DateTimeField, nullable
- blocked_by_type: TextChoices — CEO, SYSTEM (nullable)
- blocked_by_id: CharField, nullable (user_id si CEO, rule_name si SYSTEM)
- mode: CharField (modalidad operativa)
- freight_mode: CharField
- transport_mode: CharField
- dispatch_mode: TextChoices — MWT, CLIENT
- price_basis: CharField
- credit_clock_start_rule: TextChoices — ON_CREATION, ON_SHIPMENT (con override CEO)
- payment_status: TextChoices — PENDING, PARTIAL, PAID (default PENDING)
- payment_registered_at: DateTimeField, nullable
- payment_registered_by_type: TextChoices — CEO, SYSTEM (nullable)
- payment_registered_by_id: CharField, nullable
- Hereda TimestampMixin

Enums (apps/expedientes/enums.py — todo como TextChoices):
- ExpedienteStatus (8 valores)
- BlockedByType (CEO, SYSTEM)
- DispatchMode (MWT, CLIENT)
- PaymentStatus (PENDING, PARTIAL, PAID)
- CreditClockStartRule (ON_CREATION, ON_SHIPMENT)
- LegalEntityRole (5 valores)
- LegalEntityRelationship (4 valores)
- LegalEntityFrontend (3 valores)
- LegalEntityVisibility (3 valores)
- PricingVisibility (3 valores)
- LegalEntityStatus (3 valores)
- Brand (MARLUVAS)

Criterios de done:
- LegalEntity model con todos los campos de ENT_PLAT_LEGAL_ENTITY.B
- Expediente model con status (8), bloqueo (5 campos), pagos (4 campos), credit_clock_start_rule, modalidades
- Todos los enums como TextChoices en enums.py
- Migraciones generadas sin errores
- Admin registrado para ambos modelos

Evidencia mínima: makemigrations sin errores, enums.py con todos los TextChoices, admin mostrando ambos modelos.

### Item 4A: Modelos Artifact + Outbox (ArtifactInstance, EventLog)

Agente: AG-01 Architect.
Objetivo: Modelo genérico de artefactos de negocio y outbox de eventos.

Archivos permitidos: apps/expedientes/models.py (extend), apps/expedientes/managers.py.

Archivos prohibidos: views.py, serializers.py, tests/*.

Precondiciones: Item 3 aprobado.

Campos ArtifactInstance (ref → ENT_OPS_STATE_MACHINE §G, §I):
- artifact_id: UUIDField, PK
- expediente: FK → Expediente
- artifact_type: CharField (ART-01 a ART-12)
- status: TextChoices — DRAFT, COMPLETED, SUPERSEDED, VOID
- payload: JSONField
- supersedes: FK → self, nullable
- superseded_by: FK → self, nullable
- Hereda TimestampMixin

Campos EventLog (ref → ENT_OPS_STATE_MACHINE §K, 10 campos exactos):
- event_id: UUIDField, PK
- event_type: CharField (ej: "expediente.state_changed")
- aggregate_type: TextChoices — EXPEDIENTE, TRANSFER, NODE, ARTIFACT
- aggregate_id: UUIDField
- payload: JSONField
- occurred_at: DateTimeField
- emitted_by: CharField (ej: "C5:RegisterSAPConfirmation")
- processed_at: DateTimeField, nullable (null hasta que dispatcher consuma)
- retry_count: IntegerField, default=0
- correlation_id: UUIDField

Índices recomendados: (aggregate_type, aggregate_id), (processed_at) para outbox polling, (correlation_id).

Criterios de done: ArtifactInstance con type/status/payload/supersedes, EventLog con 10 campos exactos, índices declarados, migraciones generadas, admin registrado.

Evidencia mínima: contenido de models.py mostrando ambos modelos, makemigrations sin errores.

### Item 4B: Modelos Ledger (CostLine, PaymentLine)

Agente: AG-01 Architect.
Objetivo: Modelos append-only de costos y pagos.

Archivos permitidos: apps/expedientes/models.py (extend).

Archivos prohibidos: views.py, serializers.py, tests/*.

Precondiciones: Item 3 aprobado.

Campos CostLine (ref → ENT_OPS_STATE_MACHINE §F2 C15 — hereda AppendOnlyModel):
- cost_line_id: UUIDField, PK
- expediente: FK → Expediente
- cost_type: CharField
- amount: DecimalField
- currency: CharField
- phase: CharField
- description: TextField

Campos PaymentLine (ref → ENT_OPS_STATE_MACHINE §L1 — hereda AppendOnlyModel):
- payment_line_id: UUIDField, PK
- expediente: FK → Expediente
- amount: DecimalField
- currency: CharField
- method: CharField (transferencia, cheque, otro)
- reference: CharField (número comprobante)
- registered_at: DateTimeField
- registered_by_type: TextChoices — CEO, SYSTEM
- registered_by_id: CharField

Criterios de done: ambos heredan AppendOnlyModel (no update, no delete), campos exactos, migraciones generadas, admin registrado.

Evidencia mínima: save() con pk existente lanza error, makemigrations sin errores.

### Item 5: Aplicar migraciones en entorno

Agente: AG-07 DevOps.
Objetivo: Materializar todos los modelos en tablas PostgreSQL.

Archivos permitidos: scripts/infra/migrate.sh (si aplica).

Archivos prohibidos: apps/*, tests/*.

Precondiciones: Items 2, 3, 4A, 4B aprobados (todas las migraciones generadas).

Criterios de done:
- `python manage.py migrate` corre sin errores dentro del contenedor
- Tablas creadas verificables en PostgreSQL
- Superuser CEO creado
- Django admin muestra todos los modelos registrados

Evidencia mínima: output de migrate sin errores, output de showmigrations (todas applied), Django admin con 6 modelos visibles.

## 2.3 Dependencias y handoffs

### Handoff 1: AG-07 → AG-01 (después de Item 1)

Cuándo: AG-07 entrega reporte §I con status DONE para Item 1.

Qué revisa CEO:
- 6 contenedores healthy (docker ps)
- Django admin responde en navegador
- MinIO console accesible
- config/settings/base.py tiene configuración de infra completa
- AG-07 no tocó apps/ ni tests/

Qué significa "estable": output entregado según criterios de done, CEO aprobó, sin blockers, stack listo para que AG-01 trabaje dentro del contenedor.

### Handoff 2: AG-01 → AG-07 (después de Items 2-4B)

Cuándo: AG-01 completa Items 2, 3, 4A, 4B y CEO aprueba cada uno.

Qué revisa CEO:
- Campos de cada modelo trazables 1:1 a la spec congelada
- Enums como TextChoices (nunca strings sueltos)
- AppendOnlyModel bloquea update/delete
- TimestampMixin en todos los modelos
- Migraciones generadas sin errores
- Admin registrado para los 6 modelos
- AG-01 no tocó docker-compose, nginx, ni secciones de infra de settings

Qué significa "estable": todos los modelos generados, migraciones listas, CEO aprobó los 4 items, no hay [SPEC_GAP] abiertos.

### Regla de aprobación por item

CEO aprueba items individuales dentro del sprint. El sprint completo solo se marca DONE cuando los 6 items estén aprobados. Si un item falla, solo los items con dependencia directa se bloquean — no el sprint entero.

## 2.4 Riesgos de ejecución

### Riesgo 1: Conflicto en config/settings/base.py

Causa: AG-07 (Item 1) y AG-01 (Item 2) ambos tocan el mismo archivo.
Impacto: merge conflict, configuración inconsistente, Django no levanta.
Mitigación: ejecución serializada. AG-07 termina y CEO aprueba ANTES de que AG-01 toque el archivo. AG-01 solo toca INSTALLED_APPS — no toca secciones de infra. Si AG-01 necesita tocar algo fuera de INSTALLED_APPS, debe declararlo en "Decisiones asumidas" del reporte §I. Post-MVP: split a infra.py + apps.py elimina este riesgo.

### Riesgo 2: Contenedor levanta pero Django no funciona

Causa: variables de entorno incorrectas, postgres no acepta conexión desde Django, MinIO mal configurado.
Impacto: AG-01 no puede trabajar hasta que se resuelva.
Mitigación: Item 1 incluye healthcheck por contenedor. Si django no está healthy, el item no pasa. AG-07 debe ejecutar `python manage.py check` desde dentro del contenedor como parte de su validación.

### Riesgo 3: Migraciones inconsistentes

Causa: AG-01 genera migraciones parciales o en orden incorrecto.
Impacto: `python manage.py migrate` falla en Item 5.
Mitigación: dependencias estrictas 2 → 3 → 4A/4B. Cada item genera sus migraciones. Item 5 las aplica todas. Si falla, AG-01 regenera la migración del item problemático.

### Riesgo 4: Modelo base no soporta Sprint 1

Causa: campos faltantes, enums incompletos, AppendOnlyModel con bugs.
Impacto: Sprint 1 arranca y se bloquea por refactor de modelo.
Mitigación: los campos están derivados directamente de la state machine FROZEN. CEO verifica campo por campo contra la spec. Sprint 1 (LOTE_SM_SPRINT1) asume que los modelos ya soportan los 21 commands — verificar que: status tiene 8 valores, ArtifactInstance tiene supersedes/superseded_by, EventLog tiene los 10 campos, PaymentLine tiene currency y method.

### Riesgo 5: Invención por parte del agente

Causa: Antigravity agrega campos "útiles" que no están en la spec.
Impacto: deuda técnica desde día 1, posible conflicto con Sprint 1.
Mitigación: reporte §I obliga a declarar "Decisiones asumidas". CEO rechaza cualquier campo no trazable a ENT_OPS_STATE_MACHINE o ENT_PLAT_LEGAL_ENTITY. Si hay hueco, el agente marca [SPEC_GAP] y se detiene.

## 2.5 Criterio de cierre de Sprint 0

Sprint 0 está DONE cuando:

1. 6 contenedores Docker running con healthcheck passing
2. manage.py check, makemigrations y migrate corren sin errores
3. TimestampMixin + AppendOnlyModel creados y verificados manualmente
4. 6 modelos completos: LegalEntity, Expediente, ArtifactInstance, EventLog, CostLine, PaymentLine — todos con campos exactos de spec
5. Todos los enums como TextChoices en enums.py
6. Todos los modelos registrados en Django admin
7. Tablas creadas en PostgreSQL, verificables
8. Superuser CEO creado
9. Los 6 items aprobados con reportes §I, sin blockers abiertos

Lo que significa "base lista para Sprint 1": AG-02 API puede leer los modelos y generar serializers; AG-06 QA puede crear factories; los 8 estados del enum existen; las relaciones FK están definidas; AppendOnlyModel funciona (rechaza update/delete); EventLog tiene los 10 campos del outbox; no hay [SPEC_GAP] sin resolver.

Lo que NO debe existir al cerrar Sprint 0: endpoints, views, serializers, urls de API, tests automatizados, frontend, consumers de outbox, automatizaciones de crédito, conectores externos.

---

# 3. PLAN OPERATIVO PARA ALE

## 3.1 Qué hace Ale antes de arrancar

### Preparar repositorio

Crear repo Git (si no existe). Estructura mínima esperada antes de Item 1:

```
mwt-one/
├── .gitignore
├── README.md
└── (vacío — AG-07 crea la estructura Docker)
```

Branch de trabajo: `main` para empezar. Cada item de Sprint 0 se ejecuta en branch temporal (ej: `sprint0/item-1-docker`). CEO mergea a main después de aprobar.

### Confirmar documentos FROZEN vigentes

Antes de pasar cualquier instrucción a Antigravity, verificar que estos documentos están accesibles y no han cambiado:
- ENT_OPS_STATE_MACHINE v1.2.2 — FROZEN
- PLB_ORCHESTRATOR v1.2.2 — FROZEN
- LOTE_SM_SPRINT0 (dentro de PLB_ORCHESTRATOR §G) — FROZEN
- LOTE_SM_SPRINT1 — FROZEN (referencia, no ejecutar aún)

Si alguno cambió desde la sesión de congelamiento, todos los outputs que lo consumieron quedan STALE.

### Verificar entorno

Para Item 1 (AG-07): servidor KVM 8 accesible via SSH, Docker y Docker Compose instalados, dominio mwt.one apuntando (o preparar IP directa como fallback).

Para Items 2-4B (AG-01): Antigravity debe poder ejecutar código dentro del contenedor Docker levantado por Item 1.

## 3.2 Cómo interactuar con Antigravity

### Enviar contexto

Al arrancar cada item, pasar a Antigravity exactamente:
1. El texto del item de LOTE_SM_SPRINT0 (copiado literal)
2. El scope de lectura/escritura del agente correspondiente (PLB_ORCHESTRATOR §C)
3. El CLAUDE.md como reglas globales (PLB_ORCHESTRATOR §K)

No pasar documentos completos innecesarios. Solo lo que el item requiere.

Ejemplo para Item 1:
```
Ejecuta Item 1 de LOTE_SM_SPRINT0.
Tu agente es AG-07 DevOps.

[Pegar texto Item 1 de PLB_ORCHESTRATOR §G]

Scope de escritura permitido:
- docker-compose.yml, Dockerfile, nginx/, scripts/infra/, .env.template
- config/settings/base.py (solo DB, Redis, MinIO, Celery, logging)

Scope prohibido:
- apps/*, tests/*, INSTALLED_APPS

Reglas:
[Pegar CLAUDE.md de PLB_ORCHESTRATOR §K]

Al terminar, entrega reporte con formato §I.
```

### Lanzar por items, no por bloques

Lanzar un item a la vez. Esperar output, revisar, aprobar o rechazar, y solo entonces lanzar el siguiente. Razones: si un item sale mal, el siguiente ya está contaminado; revisar un item es manejable, revisar 4 a la vez no lo es; el handoff entre AG-07 y AG-01 requiere validación explícita.

La excepción: Items 4A y 4B pueden lanzarse juntos si Item 3 ya está aprobado, porque ambos son del mismo agente, no dependen entre sí, y el scope de escritura es el mismo archivo (models.py extend).

### Evitar que mezcle scopes

Antes de cada item, recordar explícitamente:
- "Solo tocas estos archivos: [lista]"
- "No tocas estos archivos: [lista]"
- "Si necesitas algo fuera de tu scope, decláralo como [SPEC_GAP] y detente"

Si Antigravity genera un archivo fuera de su scope (ej: AG-07 crea algo en apps/), rechazar inmediatamente sin revisar el resto.

### Recordar ownership y restricciones

Para AG-07 (Items 1 y 5), enfatizar: "No tocas nada dentro de apps/. No instalas apps. No modificas INSTALLED_APPS. Tu dominio es infra: Docker, Nginx, settings de base de datos, deploy."

Para AG-01 (Items 2-4B), enfatizar: "No tocas docker-compose.yml. No tocas nginx. No modificas secciones de infra de settings (DB, Redis, MinIO, Celery). Solo tocas INSTALLED_APPS y el código dentro de apps/."

## 3.3 Cómo revisar outputs

### Qué revisar primero

Para cada output de Antigravity, revisar en este orden:

1. **Archivos tocados**: verificar que SOLO los archivos permitidos fueron creados/modificados. Si hay archivos fuera de scope, rechazar.
2. **Reporte §I**: verificar que tiene status, archivos creados, archivos modificados, archivos NO tocados, decisiones asumidas, blockers.
3. **Decisiones asumidas**: si hay alguna, evaluar si es razonable o si es invención. Si inventó algo que no está en la spec, rechazar.
4. **Campos contra spec**: para Items 3-4B, comparar campo por campo contra ENT_OPS_STATE_MACHINE y ENT_PLAT_LEGAL_ENTITY. Cualquier campo extra o faltante es error.
5. **Criterios de done**: verificar cada checkbox del item.

### Detectar invención no autorizada

Señales de que el agente inventó:
- Campos que no aparecen en la state machine ni en LegalEntity
- Lógica de negocio en modelos (validaciones complejas, signals, computed properties)
- Archivos fuera de scope (views.py, serializers.py, tests)
- Migraciones que tocan tablas no especificadas
- Comments en código que asumen decisiones de negocio no documentadas

Si detecta invención: rechazar output, pedir que elimine lo inventado, relanzar con instrucción más restrictiva.

### Verificar criterios de done

Para cada item, ejecutar los checks correspondientes dentro del contenedor:
```bash
# Después de Item 2
docker exec mwt-django python manage.py check
docker exec mwt-django python manage.py makemigrations --check

# Después de Items 3, 4A, 4B
docker exec mwt-django python manage.py makemigrations --check
docker exec mwt-django python manage.py showmigrations

# Después de Item 5
docker exec mwt-django python manage.py migrate
docker exec mwt-django python manage.py showmigrations
# Verificar tablas en PostgreSQL
docker exec mwt-postgres psql -U mwt -d mwt -c "\dt"
```

## 3.4 Cómo manejar branches y cambios

### Estructura de branches

```
main (protegido — solo CEO mergea)
├── sprint0/item-1-docker      ← AG-07 trabaja aquí
├── sprint0/item-2-core        ← AG-01 trabaja aquí
├── sprint0/item-3-models      ← AG-01
├── sprint0/item-4a-artifacts  ← AG-01
├── sprint0/item-4b-ledgers    ← AG-01
└── sprint0/item-5-migrate     ← AG-07
```

Regla: cada item en su branch. CEO mergea a main después de aprobar. El siguiente item se brancha desde main actualizado.

### Cuándo aceptar

Aceptar cuando: el reporte §I dice DONE, todos los criterios de done se verificaron, no hay archivos fuera de scope, no hay invención, no hay [SPEC_GAP] abiertos.

### Cuándo rechazar

Rechazar cuando: archivos fuera de scope, campos inventados, migraciones que fallan, faltan campos de la spec, reporte §I incompleto o con status PARTIAL/BLOCKED sin justificación clara.

### Cuándo pedir corrección

Pedir corrección cuando: casi todo bien pero falta un campo, o un enum tiene valores incorrectos, o la migración necesita ajuste menor. No relanzar el item completo — pedir patch específico.

### Cuándo marcar STALE

Un output queda STALE si: un documento FROZEN cambió después de que el agente empezó (poco probable en Sprint 0), o el CEO modificó el lote o precondiciones, o un item anterior fue rechazado y regenerado cambiando su output.

## 3.5 Cómo documentar y escalar

### Registrar avances

Para cada item completado, crear un comentario en el PR (o un archivo de tracking) con:
- Item #: nombre
- Status: DONE / PARTIAL / BLOCKED
- Branch: sprint0/item-X
- Merge commit: (después de merge)
- Notas: cualquier observación

### Documentar blockers

Si un item se bloquea, registrar: qué item, qué blocker, qué lo desbloquea, quién debe actuar.

### Cuándo escalar al CEO (Alvaro)

Escalar cuando: AG-01 necesita un dato que no está en la spec ([SPEC_GAP]), hay conflicto entre documentos FROZEN, un item requiere tocar archivos fuera de scope, la infraestructura no levanta y no es claro por qué, un modelo necesita un campo que la spec no contempla.

### Cuándo detener el sprint

Detener si: un [SPEC_GAP] afecta los modelos core (Expediente, LegalEntity), las migraciones son inconsistentes y regenerarlas no resuelve, el stack Docker no levanta después de 2 intentos de corrección, se descubre que la spec FROZEN tiene una contradicción que afecta los modelos.

## 3.6 Cómo preparar el paso a Sprint 1

### Qué debe quedar validado

Antes de abrir LOTE_SM_SPRINT1, verificar:
1. `python manage.py migrate` corre sin errores
2. `python manage.py check` sin warnings
3. Django admin muestra los 6 modelos
4. Se puede crear un LegalEntity desde admin
5. Se puede crear un Expediente desde admin (con FK a LegalEntity)
6. Se puede crear un ArtifactInstance desde admin (con FK a Expediente)
7. Se puede crear un CostLine desde admin (append-only)
8. Se puede crear un PaymentLine desde admin (append-only)
9. Los enums muestran opciones correctas en admin dropdowns

### Qué artefactos deben existir

En el repo:
- apps/core/models.py con TimestampMixin y AppendOnlyModel
- apps/expedientes/models.py con 6 modelos
- apps/expedientes/enums.py con todos los TextChoices
- apps/expedientes/admin.py con los 6 modelos registrados
- docker-compose.yml con 6 servicios
- config/settings/base.py con infra + INSTALLED_APPS
- CLAUDE.md en raíz (PLB_ORCHESTRATOR §K)
- Migraciones aplicadas

### Checks mínimos

```bash
docker exec mwt-django python manage.py check
docker exec mwt-django python manage.py migrate --check  # no pending migrations
docker exec mwt-django python manage.py showmigrations   # all applied
```

### Señales de que se puede abrir Sprint 1

Sprint 1 se abre cuando: los 6 items de Sprint 0 están DONE y aprobados, no hay [SPEC_GAP] abiertos, los modelos tienen todos los campos que Sprint 1 necesita (verificar contra LOTE_SM_SPRINT1 Items 1A-1B que listan los serializers), y Django admin funciona sin errores.

Señal negativa (no abrir Sprint 1 si): queda algún item en PARTIAL o BLOCKED, hay campos de la spec no implementados, AppendOnlyModel no bloquea update/delete correctamente, el stack Docker no es estable.

---

# 4. DOCUMENTO DE ARQUITECTURA DE APOYO

## 4.1 Arquitectura MVP relevante para Sprint 0

Sprint 0 levanta un subconjunto del stack completo. Solo lo necesario para tener Django funcional con modelos y admin.

```
┌─────────────────────────────────────────────┐
│                  Nginx                       │
│        (reverse proxy, SSL, routing)         │
└──────────────┬──────────────────────────────┘
               │ :80/:443
┌──────────────▼──────────────────────────────┐
│           Django + Gunicorn                  │
│   (backend, admin, API futuro, orquestador)  │
└──────┬──────────────┬───────────────────────┘
       │              │
┌──────▼──────┐  ┌────▼─────┐  ┌──────────┐
│ PostgreSQL  │  │  MinIO   │  │  Redis   │
│   16        │  │ (storage)│  │  (cache  │
│ (datos)     │  │          │  │  +broker)│
└─────────────┘  └──────────┘  └────┬─────┘
                                    │
                          ┌─────────▼─────────┐
                          │  Celery Worker     │
                          │  + Celery Beat     │
                          │  (tasks async)     │
                          └────────────────────┘
```

Tecnologías y versiones (ref → ENT_PLAT_INFRA.F):
- Django 5.x + DRF (aunque DRF no se usa hasta Sprint 1)
- PostgreSQL 16
- MinIO (object storage para documentos/facturas)
- Redis 7 (cache + broker Celery)
- Celery (workers + beat scheduler)
- Nginx (reverse proxy)
- Docker Compose (orquestación de contenedores)
- Servidor: Hostinger KVM 8 (8 vCPU, 32GB RAM, 400GB NVMe)

Lo que NO se levanta en Sprint 0: Next.js (mwt.one, portal, ranawalk.com), n8n, Windmill. Esos son post-Sprint 3.

## 4.2 Responsabilidad por capa

### Infraestructura (AG-07 construye)

Qué resuelve: contenedores Docker, networking entre servicios, reverse proxy, SSL, healthchecks, variables de entorno, configuración de base de datos, Redis, MinIO, Celery.

Archivos: docker-compose.yml, Dockerfile, nginx/mwt.conf, .env.template, scripts/infra/, config/settings/base.py (secciones de infra).

Frontera: AG-07 prepara el ambiente. No define qué apps existen ni qué modelos hay.

### Dominio (AG-01 construye)

Qué resuelve: modelos de datos, enums, mixins abstractos, relaciones entre entidades, registro en admin.

Archivos: apps/*/models.py, apps/*/enums.py, apps/*/admin.py, apps/*/apps.py, apps/*/managers.py, config/settings/base.py (solo INSTALLED_APPS).

Frontera: AG-01 define la estructura de datos. No define endpoints, no crea views, no escribe tests, no toca infraestructura.

### Configuración (compartida con ownership claro)

config/settings/base.py es archivo compartido con split de ownership:
- AG-07 es owner de: DATABASE, CACHES (Redis), MINIO settings, CELERY settings, LOGGING, STATIC/MEDIA paths
- AG-01 es owner de: INSTALLED_APPS, app-specific flags

Regla de serialización: AG-07 y AG-01 no editan base.py en paralelo. AG-07 termina primero. AG-01 solo agrega apps después.

Post-MVP: split a config/settings/infra.py + config/settings/apps.py elimina el riesgo de conflicto.

## 4.3 Fronteras de Sprint 0

### SÍ entra en Sprint 0

- Docker Compose con 6 contenedores + healthchecks
- Django project init (estructura apps/)
- Core base: TimestampMixin, AppendOnlyModel
- LegalEntity model (tenant raíz)
- Expediente model (8 estados, bloqueo, pagos, crédito)
- ArtifactInstance model (artefactos genéricos)
- EventLog model (outbox 10 campos)
- CostLine model (append-only)
- PaymentLine model (append-only)
- Todos los enums como TextChoices
- Admin registrado para los 6 modelos
- Migraciones aplicadas
- Superuser CEO
- CLAUDE.md en raíz del repo

### NO entra en Sprint 0

- Endpoints REST (Sprint 1 — AG-02)
- Views, serializers, URLs de API (Sprint 1)
- Tests automatizados (Sprint 1 — AG-06)
- Frontend / UI (Sprint 3)
- Services.py / domain logic (Sprint 1 — AG-02)
- Permissions.py / guards (Sprint 1 — AG-02)
- Event consumers / dispatcher (Sprint 2)
- Reloj de crédito automático (Sprint 2)
- Conectores externos / fiscal (post-MVP)
- n8n, Windmill, Next.js (post-Sprint 3)

## 4.4 Riesgos técnicos inmediatos

### Config centralizada demasiado temprano

config/settings/base.py es un solo archivo que contiene tanto configuración de infra como de apps. Esto funciona en Sprint 0 porque solo hay 2 agentes y la ejecución es serializada. Se vuelve problema cuando múltiples agentes necesiten modificar settings en paralelo.

Mitigación Sprint 0: serialización estricta (AG-07 primero, AG-01 después).
Mitigación post-MVP: split a infra.py + apps.py. PLB_ORCHESTRATOR §D ya documenta esta decisión.

### Acoplamiento entre infra y app config

INSTALLED_APPS y database config viven en el mismo archivo. Si AG-01 accidentalmente modifica una variable de infra, el stack puede dejar de funcionar.

Mitigación: instrucciones explícitas a Antigravity de qué secciones tocar. Revisión manual por Ale. Diff del PR muestra exactamente qué líneas cambiaron.

### Fragilidad en migraciones iniciales

Sprint 0 genera migraciones para 6 modelos en 4 items secuenciales. Si el orden de migraciones no es correcto (ej: Expediente antes de LegalEntity), migrate falla.

Mitigación: la secuencia de items respeta dependencias de FK: core (sin FK) → LegalEntity (sin FK a modelos propios) → Expediente (FK a LegalEntity) → ArtifactInstance (FK a Expediente) → CostLine/PaymentLine (FK a Expediente). Cada item genera su migración. Si falla, se regenera en orden.

### AppendOnlyModel no probado automáticamente

Sprint 0 no incluye tests automatizados (eso es Sprint 1). AppendOnlyModel debe verificarse manualmente: intentar update via admin, intentar delete via admin, ambos deben fallar.

Mitigación: Ale verifica manualmente en Django admin antes de aprobar Item 4B. Si AppendOnlyModel no bloquea correctamente, es blocker para Sprint 1 (CostLine y PaymentLine dependen de ello).

## 4.5 Decisiones congeladas que no deben reinterpretarse

Estas decisiones están en documentos FROZEN. Antigravity no debe rediseñarlas, cuestionarlas ni proponer alternativas.

1. **Ownership por agente** (PLB_ORCHESTRATOR §D): cada archivo tiene un agente owner. No se edita fuera de scope sin aprobación CEO.

2. **No merge por agentes** (PLB_ORCHESTRATOR §A2): ningún agente hace merge final. Entrega output/patch. CEO valida e integra.

3. **CEO como integrador** (PLB_ORCHESTRATOR §A2): el CEO decide qué se mergea, cuándo, y en qué orden.

4. **State machine como spec canónica** (PLB_ORCHESTRATOR §F): ENT_OPS_STATE_MACHINE es la verdad del dominio. Si el código diverge de la spec, el código está mal. Los 8 estados, 21 commands y transaction boundaries no se reinterpretan.

5. **Sprint 0 solo con AG-07 + AG-01** (PLB_ORCHESTRATOR §A1): no se agregan agentes. AG-02 API y AG-06 QA entran en Sprint 1.

6. **Salida de Sprint 0 orientada a base estable** (PLB_ORCHESTRATOR §G): el objetivo es dejar modelos y admin funcionales, no endpoints ni lógica de negocio.

7. **Patrón command-heavy para Sprint 1** (LOTE_SM_SPRINT1): 1 command = 1 endpoint POST. No ViewSet + @action. Esto no se implementa en Sprint 0, pero los modelos deben soportarlo sin refactor.

8. **Enums como TextChoices** (ENT_OPS_STATE_MACHINE §A): nunca strings sueltos. Los 8 estados son enum, no CharField con choices manuales.

9. **AppendOnlyModel para ledgers** (POL_INMUTABILIDAD): CostLine y PaymentLine no permiten update ni delete. Esto es arquitectural, no negociable.

10. **EventLog con 10 campos exactos** (ENT_OPS_STATE_MACHINE §K): no agregar campos, no quitar campos. El outbox es spec congelada.
