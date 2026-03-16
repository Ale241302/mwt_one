# Resumen Sprint 8 — Auth + Knowledge Container

> **Rama:** `sprint-8-auth-knowledge`
> **Fecha de commits:** 13 de marzo de 2026
> **Estado:** ✅ Completado

---

## Objetivo del Sprint

El Sprint 8 tuvo como objetivo dos pilares en secuencia:

- **Pilar A — Identidad:** Extender el usuario de Django a `MWTUser` con roles granulares y JWT extendido con `role` y `permissions[]`.
- **Pilar B — Knowledge Container:** Crear el microservicio independiente `mwt-knowledge` con búsqueda semántica usando pgvector + Claude, y la app Django `knowledge` para ConversationLog con retención configurable.

---

## Rama Creada

| Rama | URL |
|------|-----|
| `sprint-8-auth-knowledge` | https://github.com/Ale241302/mwt_one/tree/sprint-8-auth-knowledge |

---

## Actividades Realizadas (por commit)

| ID | Commit | Descripción |
|----|--------|-------------|
| S8-01/02 | `Sprint 8 Item 1-2` | App `users` — modelos `MWTUser` + `UserPermission`, migrations `0001` y `0002` |
| S8-01 | `Sprint 8 Item 1: settings.py` | `AUTH_USER_MODEL` + `INSTALLED_APPS users` + configuración JWT |
| S8-03/04 | `users/serializers.py JWT` | JWT extendido con `role` y `permissions[]` + `decorators.py` + `mixins.py` |
| S8-05 | `API Admin Usuarios` | `views.py`, `serializers.py`, `urls.py` con CRUD + PATCH permisos + guardia último admin |
| S8-06 | `apps/knowledge` | `ConversationLog` + `calculate_retention` + signal + tarea purge + urls |
| S8-07 | `knowledge/ FastAPI service` | `main.py`, `indexer.py`, modelos pgvector, `Dockerfile`, `requirements.txt` |
| S8-07/08/09/10 | `knowledge/views.py` | Endpoints `/ask/`, `/index/`, `/sessions/` + tarea Celery purge + fix `docker-compose` |
| S8-11 | `add mwt-knowledge service` | Servicio en `docker-compose.yml` + eliminado flag `--scheduler DatabaseScheduler` de celery-beat |
| S8-12/13 | `tests Pilar A y B` | Suite de tests con mocks para users+JWT y knowledge endpoints |

---

## Carpetas Nuevas Creadas

| Carpeta | Descripción |
|---------|-------------|
| `knowledge/` | Microservicio FastAPI independiente (`mwt-knowledge`) |
| `backend/apps/users/` | Nueva app Django para gestión de usuarios con roles |
| `backend/apps/knowledge/` | Nueva app Django para ConversationLog y proxy al microservicio |

---

## Archivos Creados (Nuevos)

### `knowledge/` — Microservicio FastAPI

| Archivo | Descripción |
|---------|-------------|
| `knowledge/main.py` | Aplicación FastAPI principal con endpoints `/ask/`, `/index/`, `/sessions/` |
| `knowledge/indexer.py` | Indexador de archivos `.md` en pgvector |
| `knowledge/database.py` | Conexión a PostgreSQL + extensión pgvector |
| `knowledge/Dockerfile` | Imagen Docker del microservicio |
| `knowledge/requirements.txt` | Dependencias Python del microservicio (FastAPI, pgvector, anthropic, etc.) |

### `backend/apps/users/` — App Django Users

| Archivo | Descripción |
|---------|-------------|
| `models.py` | Modelos `MWTUser` (AbstractUser extendido) y `UserPermission` |
| `serializers.py` | JWT extendido con `role` y `permissions[]` |
| `views.py` | CRUD de usuarios + PATCH permisos + guardia último admin |
| `decorators.py` | Decoradores de permisos granulares |
| `mixins.py` | Mixins de autorización reutilizables |
| `urls.py` | Rutas de la app users |
| `admin.py` | Registro en Django Admin |
| `apps.py` | Configuración de la app |
| `__init__.py` | Inicializador del módulo |
| `migrations/0001_initial.py` | Migración inicial — tabla `MWTUser` |
| `migrations/0002_migrate_ceo.py` | Migración — asignación rol CEO |

### `backend/apps/knowledge/` — App Django Knowledge

| Archivo | Descripción |
|---------|-------------|
| `models.py` | Modelo `ConversationLog` con campo `retain_until` y `calculate_retention()` |
| `views.py` | Proxy Django al microservicio FastAPI (`/ask/`, `/index/`, `/sessions/`) |
| `signals.py` | Signal `post_save` con `transaction.on_commit()` para setear `retain_until` |
| `tasks.py` | Tarea Celery `purge_expired_conversation_logs` — purga logs expirados |
| `utils.py` | Utilidades auxiliares del módulo |
| `urls.py` | Rutas de la app knowledge |
| `admin.py` | Registro en Django Admin |
| `apps.py` | Configuración de la app + registro de signals |
| `__init__.py` | Inicializador del módulo |
| `migrations/` | Migraciones de la app knowledge |

---

## Archivos Modificados

| Archivo | Cambio |
|---------|--------|
| `docker-compose.yml` | Agregado servicio `mwt-knowledge` (puerto 8001) + eliminado flag `--scheduler DatabaseScheduler` de celery-beat |
| `backend/config/settings.py` | `AUTH_USER_MODEL = 'users.MWTUser'` + configuración JWT (`SIMPLE_JWT`) + `INSTALLED_APPS` (users, knowledge) |
| `backend/config/celery.py` | Tarea `purge_expired_conversation_logs` registrada en `app.conf.beat_schedule` |

---

## Documentos de Planificación Agregados

| Archivo | Descripción |
|---------|-------------|
| `Sprints/PLAN_IMPLEMENTACION_SPRINT8.MD` | Plan de implementación detallado del Sprint 8 (Pilar A y B) |
| `Sprints/modulos_faltantes_frontend_backend.md` | KB de referencia de módulos pendientes para sprints 8–10 |

---

## Tecnologías Utilizadas

- **Django REST Framework** — API admin usuarios + proxy knowledge
- **djangorestframework-simplejwt** — JWT extendido con `role` y `permissions[]`
- **FastAPI** — Microservicio `mwt-knowledge`
- **pgvector** — Búsqueda semántica vectorial sobre PostgreSQL
- **Anthropic Claude** — Generación de respuestas en el endpoint `/ask/`
- **Celery + django-celery-beat** — Tareas asíncronas y periódicas (purge logs)
- **Docker / docker-compose** — Orquestación del nuevo contenedor `mwt-knowledge`
