# Tareas MWT - Planificación Sprint 0

A continuación se detalla la lista de tareas a importar en Asana bajo el proyecto **Tareas MWT** (Sección: Planificación) derivadas de `PAQUETE_SPRINT0_MWT.md` y `PLB_SPRINT0_EJECUCION.md`.

## Tareas

### Tarea 1: Sprint 0 - Item 1: Docker Compose MVP + Infra Settings
- **Responsable (Agente):** AG-07 DevOps
- **Descripción:** Levantar el stack Docker MVP con 6 contenedores (django, postgres, nginx, minio, celery-worker, celery-beat) y configurar la infraestructura base en `.env` y `base.py`.
- **Criterios de Éxito:**
  - 6 contenedores corriendo y *healthy*.
  - Django admin y MinIO Console accesibles.
  - PostgreSQL aceptando conexiones y Celery/Beat corriendo.
- **Riesgos:** Conflictos de puertos (5432, 6379, 80) o mala configuración de variables de entorno (MinIO, PostgreSQL).

### Tarea 2: Sprint 0 - Item 2: Django Project Init + Core Base
- **Responsable (Agente):** AG-01 Architect
- **Dependencia:** Item 1 aprobado.
- **Descripción:** Crear la estructura base del proyecto Django y los mixins abstractos fundamentales en `apps/core/models.py`.
- **Criterios de Éxito:**
  - Estructura `apps/core` creada y registrada.
  - Modelo `TimestampMixin` y `AppendOnlyModel` implementados.
  - `python manage.py check` y `makemigrations core` sin errores.

### Tarea 3: Sprint 0 - Item 3: Modelos LegalEntity + Expediente
- **Responsable (Agente):** AG-01 Architect
- **Dependencia:** Item 2 aprobado.
- **Descripción:** Desarrollar los modelos centrales del negocio (`LegalEntity` y `Expediente`) basados en `ENT_OPS_STATE_MACHINE` y `ENT_PLAT_LEGAL_ENTITY`.
- **Criterios de Éxito:**
  - Campos exactos según la spec congruentes y tipados.
  - Todos los *enums* definidos como `TextChoices`.
  - Migraciones generadas y modelos registrados en el Admin.

### Tarea 4: Sprint 0 - Item 4A: ArtifactInstance + EventLog (Outbox)
- **Responsable (Agente):** AG-01 Architect
- **Dependencia:** Item 3 aprobado.
- **Descripción:** Implementar el modelo genérico de artefactos (`ArtifactInstance`) y la tabla *append-only* del Outbox (`EventLog`).
- **Criterios de Éxito:**
  - `EventLog` contiene exactamente los 10 campos de la especificación.
  - Índices correctos para concurrencia/polling.
  - Migraciones generadas y modelos registrados en el Admin.

### Tarea 5: Sprint 0 - Item 4B: Modelos Ledger (CostLine, PaymentLine)
- **Responsable (Agente):** AG-01 Architect
- **Dependencia:** Item 3 aprobado (puede ser paralelo a Item 4A).
- **Descripción:** Implementar modelos inmutables de Costos y Pagos, heredando de `AppendOnlyModel`.
- **Criterios de Éxito:**
  - Ninguno de los dos modelos permite `update` ni `delete`.
  - Migraciones generadas y registradas en el Admin.

### Tarea 6: Sprint 0 - Item 5: Aplicar migraciones en entorno
- **Responsable (Agente):** AG-07 DevOps
- **Dependencia:** Items 2, 3, 4A y 4B aprobados.
- **Descripción:** Materializar todos los modelos en tablas PostgreSQL, aplicar todas las migraciones generadas y crear el super-usuario CEO.
- **Criterios de Éxito:**
  - `python manage.py migrate` sin errores.
  - Las 6 tablas existen en la base de datos PostgreSQL.
  - Superuser CEO creado exitosamente.
