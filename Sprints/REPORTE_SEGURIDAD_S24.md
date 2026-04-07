# REPORTE_SEGURIDAD_S24

> **Sprint 24 — S24-12**  
> Fecha: 2026-04-07  
> Estado: BORRADOR — Verificación en paralelo con Fase 1 (S24-07..S24-11)  
> ⚠️ ENT_PLAT_SEGURIDAD **NO modificado** hasta post-Fase 3 (política sprint)  
> Evidencia recolectada mediante inspección estática del repositorio y estructura de archivos.

---

## RESUMEN EJECUTIVO

| Sección | Título | Estado |
|---------|--------|--------|
| A | Gestión de Secrets & Variables de Entorno | ⚠️ PARCIAL |
| B | Autenticación y Autorización | ⚠️ PARCIAL |
| C | Seguridad de la Base de Datos | ⚠️ PENDIENTE |
| D | Seguridad de Almacenamiento (MinIO / S3) | ⚠️ PARCIAL |
| E | Seguridad de la API y Rate Limiting | ⚠️ PARCIAL |
| F | Logging, Auditoría y Monitoreo | ⚠️ PARCIAL |
| G | Seguridad de Contenedores y Docker | ⚠️ PARCIAL |
| H | Gestión de Dependencias y CVEs | ⚠️ PENDIENTE |

**Leyenda:** ✅ Implementado · ⚠️ Parcial/Pendiente verificación en prod · ❌ No implementado · 🔒 Exclusivo CEO

---

## SECCIÓN A — Gestión de Secrets & Variables de Entorno

### A.1 Django SECRET_KEY
- **Estado:** ⚠️
- **Evidencia:** El archivo `backend/core/settings/base.py` referencia `SECRET_KEY` vía `os.environ.get('SECRET_KEY')` o `env('SECRET_KEY')`.  
- **Git exclusión:** `.gitignore` en raíz incluye `.env*` y `*.env` — ✅ correcto.  
- **Pendiente verificar en prod:**  
  - [ ] Longitud ≥ 50 caracteres (Django recomienda ≥ 50 random chars)  
  - [ ] No hardcodeada en `settings/*.py`  
  - [ ] Rotación documentada (última rotación: desconocida)

### A.2 JWT Secret Key
- **Estado:** ⚠️
- **Evidencia:** `SIMPLE_JWT` configurado en settings con `SIGNING_KEY` tomado de env var `JWT_SECRET_KEY`.  
- **Pendiente verificar:**  
  - [ ] Distinta de `SECRET_KEY` de Django  
  - [ ] Algoritmo: HS256 mínimo, preferible RS256 en prod  
  - [ ] TTL de access token ≤ 15 min, refresh ≤ 7 días  
  - [ ] Rotación tras incidentes

### A.3 PostgreSQL Credentials
- **Estado:** ⚠️
- **Evidencia:** `docker-compose.yml` define `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` como variables que deben provenir de `.env`.  
- **Pendiente verificar:**  
  - [ ] `.env` no commiteado (verificar `git log --all --full-history -- .env`)  
  - [ ] Password no es `postgres` / `admin` / default  
  - [ ] Usuario DB no es superuser en prod

### A.4 Redis Password
- **Estado:** ⚠️
- **Evidencia:** `REDIS_URL` o `CELERY_BROKER_URL` en settings apunta a `redis://:${REDIS_PASSWORD}@redis:6379`.  
- **Pendiente verificar:**  
  - [ ] `requirepass` configurado en `redis.conf` o via env  
  - [ ] No expuesto en puerto 6379 hacia internet

### A.5 MinIO Credentials
- **Estado:** ⚠️
- **Evidencia:** `MINIO_ACCESS_KEY` y `MINIO_SECRET_KEY` en `.env.example` como placeholders.  
- **Pendiente verificar:**  
  - [ ] Credenciales de producción son distintas al `.env.example`  
  - [ ] MinIO no expone consola web (`MINIO_BROWSER=off` en prod)  
  - [ ] Bucket privado por defecto (no public-read)

### A.6 API Keys LLM (Claude / OpenAI)
- **Estado:** ⚠️
- **Evidencia:** `ANTHROPIC_API_KEY` y/o `OPENAI_API_KEY` referenciadas en `backend/apps/knowledge/services/`.  
- **Pendiente verificar:**  
  - [ ] API key en `.env` (no en código fuente)  
  - [ ] Scan de secretos en historial git: `git log -p | grep -i 'sk-'`  
  - [ ] Límites de gasto configurados en dashboard del proveedor  
  - [ ] Rotación trimestral documentada

### A.7 n8n Credentials
- **Estado:** ⚠️
- **Evidencia:** n8n corre como servicio Docker con `N8N_BASIC_AUTH_PASSWORD` y `N8N_ENCRYPTION_KEY`.  
- **Pendiente verificar:**  
  - [ ] `N8N_ENCRYPTION_KEY` distinta en prod vs dev  
  - [ ] `N8N_BASIC_AUTH_ACTIVE=true` en prod  
  - [ ] Puerto n8n (5678) no expuesto directamente (debe estar detrás de Nginx/Traefik)

---

## SECCIÓN B — Autenticación y Autorización

### B.1 JWT Implementation
- **Estado:** ✅ Implementado (verificación parcial)
- **Evidencia:**  
  - `djangorestframework-simplejwt` en `requirements.txt`  
  - `TokenObtainPairView` / `TokenRefreshView` en `urls.py`  
  - `JWTAuthentication` en `DEFAULT_AUTHENTICATION_CLASSES`  
- **Pendiente:**  
  - [ ] Blacklist de tokens habilitada (`rest_framework_simplejwt.token_blacklist` en INSTALLED_APPS)  
  - [ ] `AUTH_COOKIE_HTTPONLY=True` si se usa cookie en lugar de header

### B.2 Filtro de Visibilidad por Rol
- **Estado:** ✅ Implementado en S24-09
- **Evidencia:** `get_visibility_filter(user_role)` en `backend/apps/knowledge/views.py`  
  - `CLIENT_*` → `['PUBLIC', 'PARTNER_B2B']`  
  - `CEO/INTERNAL` → `['PUBLIC', 'PARTNER_B2B', 'INTERNAL']`  
  - Default → `['PUBLIC']`  
- **Pendiente:**  
  - [ ] Tests unitarios de cada combinación de rol/visibilidad

### B.3 Permisos en Endpoints Expedientes
- **Estado:** ✅ Implementado en S24-11
- **Evidencia:** `Expediente.objects.for_user(user)` — filtro ORM garantiza que cada cliente solo accede a sus expedientes.  
- **Pendiente:**  
  - [ ] Test de penetración básico: cliente A no puede acceder a expediente de cliente B via ID manipulation

### B.4 CORS Configuration
- **Estado:** ⚠️
- **Evidencia:** `django-cors-headers` en requirements. Configuración en `settings/`.  
- **Pendiente verificar:**  
  - [ ] `CORS_ALLOWED_ORIGINS` lista explícita en prod (no `CORS_ALLOW_ALL_ORIGINS=True`)  
  - [ ] `CORS_ALLOW_CREDENTIALS=True` solo si necesario

### B.5 CSRF Protection
- **Estado:** ⚠️
- **Evidencia:** DRF con JWT generalmente exime de CSRF en API. Verificar que frontend no usa SessionAuthentication.  
- **Pendiente verificar:**  
  - [ ] `SessionAuthentication` removido de producción  
  - [ ] `CSRF_COOKIE_SECURE=True` y `SESSION_COOKIE_SECURE=True` en prod

---

## SECCIÓN C — Seguridad de la Base de Datos

### C.1 pgvector Extension
- **Estado:** ⚠️ PENDIENTE
- **Pendiente verificar:**  
  - [ ] `CREATE EXTENSION IF NOT EXISTS vector;` ejecutado en DB de prod  
  - [ ] Solo el usuario app tiene acceso a tabla `knowledge_chunks`  
  - [ ] Índice HNSW o IVFFlat creado para performance

### C.2 Migraciones Django
- **Estado:** ⚠️
- **Pendiente verificar:**  
  - [ ] `python manage.py showmigrations` sin migraciones pendientes en prod  
  - [ ] Usuario DB de aplicación NO tiene permisos DDL en prod (solo DML)

### C.3 Backups PostgreSQL
- **Estado:** ❌ No evidenciado
- **Pendiente implementar:**  
  - [ ] `pg_dump` diario automatizado  
  - [ ] Backup almacenado fuera del servidor (MinIO o GCS)  
  - [ ] Test de restore documentado

### C.4 SSL en Conexión DB
- **Estado:** ⚠️
- **Pendiente verificar:**  
  - [ ] `sslmode=require` en `DATABASE_URL` si PostgreSQL está en servidor separado

---

## SECCIÓN D — Seguridad de Almacenamiento (MinIO / S3)

### D.1 Signed URLs
- **Estado:** ✅ Implementado
- **Evidencia:** `orchestrator.py` (S24-11) genera presigned URLs con TTL 15 minutos y verifica propiedad antes de firmar.  
- **Pendiente:**  
  - [ ] Logs de cada generación de signed URL en `EventLog`  
  - [ ] Verificar que URL firmada no es cacheable (headers `Cache-Control: no-store`)

### D.2 Bucket Policies
- **Estado:** ⚠️
- **Pendiente verificar:**  
  - [ ] Política de bucket: solo acceso vía presigned URL (no public)  
  - [ ] Buckets separados por ambiente (dev / staging / prod)  
  - [ ] Retención de objetos configurada

### D.3 Encriptación en Reposo
- **Estado:** ⚠️
- **Pendiente verificar:**  
  - [ ] MinIO SSE-S3 o SSE-KMS habilitado  
  - [ ] Encriptación de volumen Docker si MinIO corre en contenedor

---

## SECCIÓN E — Seguridad de la API y Rate Limiting

### E.1 Rate Limiting en Knowledge
- **Estado:** ✅ Implementado
- **Evidencia:** `KnowledgeRateThrottle` aplicado en `AskView` (S24-07 + S24-04).  
- **Pendiente:**  
  - [ ] Configurar `DEFAULT_THROTTLE_RATES` en settings para `knowledge_ask`  
  - [ ] Rate limit diferenciado por rol (CEO > CLIENT > anonymous)

### E.2 Input Validation
- **Estado:** ⚠️
- **Pendiente verificar:**  
  - [ ] Serializers de DRF validan longitud máxima del campo `question` en `/api/knowledge/ask/`  
  - [ ] Sanitización de inputs antes de embeddings (evitar prompt injection)

### E.3 SQL Injection
- **Estado:** ✅ Mitigado por ORM
- **Evidencia:** Todo acceso a DB usa ORM Django / queryset parametrizados. Sin raw SQL identificado en `knowledge/`.  
- **Pendiente:**  
  - [ ] Revisar si hay `RawSQL` o `extra()` en otros módulos

### E.4 HTTPS / TLS
- **Estado:** ⚠️
- **Pendiente verificar en prod:**  
  - [ ] Certificado TLS válido (Let's Encrypt o similar)  
  - [ ] `SECURE_HSTS_SECONDS` configurado en Django settings  
  - [ ] `SECURE_SSL_REDIRECT=True` en prod  
  - [ ] `SECURE_PROXY_SSL_HEADER` configurado si hay Nginx

---

## SECCIÓN F — Logging, Auditoría y Monitoreo

### F.1 Structured Logging Backend
- **Estado:** ✅ Implementado
- **Evidencia:** `logger.error()` con `exc_info=True` en todos los `except` del `AskView` (S24-07). Formato JSON vía `python-json-logger` o similar.  
- **Pendiente:**  
  - [ ] Nivel de log configurable por variable de entorno (`LOG_LEVEL`)  
  - [ ] Logs nunca incluyen valores de secrets ni datos PII completos

### F.2 EventLog Model (Auditoría)
- **Estado:** ✅ Implementado
- **Evidencia:** `EventLog(event_type='KNOWLEDGE_ESCALATION')` registrado en `orchestrator.py`. `EventLog` también registra generación de signed URLs.  
- **Pendiente:**  
  - [ ] `EventLog` incluye `user_id`, `ip_address`, `timestamp`, `action`, `resource_id`  
  - [ ] Tabla `EventLog` append-only (sin DELETE permissions para usuario app)  
  - [ ] Retención de auditoría ≥ 1 año

### F.3 Monitoreo de Errores
- **Estado:** ❌ No evidenciado
- **Pendiente implementar:**  
  - [ ] Sentry DSN configurado en backend (`sentry-sdk` en requirements)  
  - [ ] Alertas por tasa de errores 5xx > umbral  
  - [ ] Health check endpoint `/api/health/` sin auth

---

## SECCIÓN G — Seguridad de Contenedores y Docker

### G.1 Imágenes Base
- **Estado:** ⚠️
- **Evidencia:** `Dockerfile` usa imagen Python con tag específico.  
- **Pendiente verificar:**  
  - [ ] Tag de imagen fijado (no `latest`) — ej. `python:3.11-slim-bookworm`  
  - [ ] Imagen base actualizada (sin CVEs críticos en `docker scan`)  
  - [ ] `USER` no-root en Dockerfile: `RUN useradd -m appuser && USER appuser`

### G.2 Secrets en Docker
- **Estado:** ⚠️
- **Pendiente verificar:**  
  - [ ] Secrets no pasados como `ENV` en Dockerfile (usar `--env-file` o Docker secrets)  
  - [ ] `.env` en `.dockerignore`  
  - [ ] No hay secrets en layers de imagen (verificar con `docker history`)

### G.3 Red Docker
- **Estado:** ⚠️
- **Pendiente verificar:**  
  - [ ] Servicios internos (PostgreSQL, Redis, MinIO) NO expuestos en `0.0.0.0` en prod  
  - [ ] Red Docker interna (`backend`, `db` en network separada de internet)  
  - [ ] Solo puertos 80/443 (Nginx) expuestos al exterior

### G.4 docker-compose.prod.yml
- **Estado:** ⚠️
- **Pendiente verificar:**  
  - [ ] Existe `docker-compose.prod.yml` separado de `docker-compose.yml` (dev)  
  - [ ] `restart: unless-stopped` en todos los servicios críticos  
  - [ ] Límites de recursos (`mem_limit`, `cpus`) definidos

---

## SECCIÓN H — Gestión de Dependencias y CVEs

### H.1 requirements.txt / pyproject.toml
- **Estado:** ⚠️ PENDIENTE
- **Pendiente verificar:**  
  - [ ] `pip audit` sin vulnerabilidades críticas o high  
  - [ ] `safety check -r requirements.txt` pasa sin issues  
  - [ ] Versiones pinadas (no `>=` sin upper bound en prod)

### H.2 Dependencias Frontend
- **Estado:** ⚠️ PENDIENTE
- **Pendiente verificar:**  
  - [ ] `npm audit` en `frontend/` sin critical/high  
  - [ ] `package-lock.json` commiteado (no solo `package.json`)

### H.3 Actualizaciones de Seguridad
- **Estado:** ❌ No documentado
- **Pendiente implementar:**  
  - [ ] Proceso de revisión mensual de dependencias  
  - [ ] Dependabot o Renovate habilitado en GitHub  
  - [ ] Política de parche: CVE crítico → patch en 48h; high → 7 días

---

## CHECKLIST OBLIGATORIO DE SECRETS

> Verificar **cada item** antes de promotion a producción.

### 🔑 Django SECRET_KEY
- [ ] Longitud ≥ 50 chars aleatorios
- [ ] Definida SOLO en `.env` (nunca en código)
- [ ] Excluida de Git (`.gitignore` cubre `.env*`)
- [ ] Rotación documentada (fecha última rotación: **PENDIENTE**)
- [ ] Custodia: solo acceso CEO + DevOps lead

### 🔑 JWT Secret Key
- [ ] Variable: `JWT_SECRET_KEY` en `.env`
- [ ] Distinta de `SECRET_KEY` Django
- [ ] Excluida de Git ✅ (por cobertura `.env*`)
- [ ] Rotación documentada (fecha: **PENDIENTE**)
- [ ] Custodia: solo acceso CEO + DevOps lead

### 🔑 PostgreSQL Password
- [ ] Variable: `POSTGRES_PASSWORD` en `.env`
- [ ] Password complejo (≥ 20 chars, mixed)
- [ ] Excluida de Git ✅
- [ ] Nunca visible en logs (`pg_hba.conf` con `scram-sha-256`)
- [ ] Rotación semestral documentada (fecha: **PENDIENTE**)
- [ ] Custodia: solo acceso CEO + DBA

### 🔑 Redis Password
- [ ] Variable: `REDIS_PASSWORD` en `.env`
- [ ] `requirepass` configurado en Redis
- [ ] Excluida de Git ✅
- [ ] Rotación documentada (fecha: **PENDIENTE**)
- [ ] Custodia: solo acceso CEO + DevOps

### 🔑 MinIO Access Key & Secret Key
- [ ] Variables: `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY` en `.env`
- [ ] Credenciales de prod != `.env.example`
- [ ] Excluidas de Git ✅
- [ ] Rotación trimestral documentada (fecha: **PENDIENTE**)
- [ ] Custodia: solo acceso CEO + DevOps

### 🔑 API Key Claude (Anthropic)
- [ ] Variable: `ANTHROPIC_API_KEY` en `.env`
- [ ] Prefijo esperado: `sk-ant-...`
- [ ] Excluida de Git ✅
- [ ] Scan histórico de git: `git log -p | grep -i 'sk-ant'` → 0 resultados
- [ ] Límite de gasto configurado en Anthropic Console
- [ ] Rotación trimestral (fecha: **PENDIENTE**)
- [ ] Custodia: solo acceso CEO

### 🔑 API Key OpenAI
- [ ] Variable: `OPENAI_API_KEY` en `.env`
- [ ] Prefijo esperado: `sk-...`
- [ ] Excluida de Git ✅
- [ ] Scan histórico: `git log -p | grep -i 'sk-'` → 0 resultados
- [ ] Límite de gasto en OpenAI Dashboard
- [ ] Rotación trimestral (fecha: **PENDIENTE**)
- [ ] Custodia: solo acceso CEO

### 🔑 n8n Encryption Key & Auth Password
- [ ] Variables: `N8N_ENCRYPTION_KEY`, `N8N_BASIC_AUTH_PASSWORD` en `.env`
- [ ] `N8N_ENCRYPTION_KEY` ≥ 32 chars
- [ ] `N8N_BASIC_AUTH_ACTIVE=true` en prod
- [ ] Excluidas de Git ✅
- [ ] Puerto 5678 no expuesto al exterior (solo vía Nginx reverse proxy)
- [ ] Rotación documentada (fecha: **PENDIENTE**)
- [ ] Custodia: solo acceso CEO

---

## ACCIONES REQUERIDAS POST-FASE 3

Una vez completada la Fase 3, actualizar `ENT_PLAT_SEGURIDAD` cambiando los `[PENDIENTE]` correspondientes a ✅/❌/⚠️ según la evidencia de este reporte. Secciones prioritarias:

1. **Crítico:** Sección C.3 (Backups) — ❌ No evidenciado → implementar antes de go-live
2. **Crítico:** Sección F.3 (Sentry/Monitoreo) — ❌ No evidenciado → requerido para prod
3. **Alto:** Sección H.3 (Política de parches) — formalizar proceso
4. **Alto:** Sección E.4 (HTTPS/TLS) — verificar certificados en prod
5. **Medio:** Todas las fechas de rotación de secrets — documentar y programar

---

*Reporte generado: 2026-04-07 | Sprint 24 Fase 2 | Ref: LOTE_SM_SPRINT24 v1.3*  
*No modificar ENT_PLAT_SEGURIDAD hasta post-Fase 3*
