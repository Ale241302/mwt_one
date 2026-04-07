# INSTRUCCIONES CLAUDE CODE — Sprint 24: Security B2B + Knowledge Pipeline

## Contexto

Eres Claude Code operando sobre el repositorio `Ale241302/mwt_one` (Django + Next.js). Tu trabajo es ejecutar el Sprint 24 siguiendo las instrucciones de GUIA_ALE_SPRINT24.md.

**Referencia canónica:** LOTE_SM_SPRINT24 v1.3 (aprobado — GPT-5.4 R4, score 9.5/10, 4 rondas de auditoría).

## Repos

- **App:** `Ale241302/mwt_one` — código Django + Next.js (público)
- **KB:** `sjoalfaro/mwt-knowledge-hub` — knowledge base markdown (privado)

## Estado actual

- Sprint 23 DONE: módulo `commercial` (rebates, comisiones, artifact policies) + remediación seguridad
- Sprint 22 DONE: pricing engine v2 con ClientScopedManager
- Auth: SimpleJWT con roles CEO, INTERNAL, CLIENT_* (Sprint 8)
- Frontend: Next.js con BrandConsole + Portal
- Infra: Docker, Nginx, PostgreSQL + pgvector, MinIO, Redis, Celery

## Tu branch

```bash
git checkout -b feat/sprint24-security-knowledge
```

## Reglas de ejecución

1. **Fase 0 PRIMERO, sin excepciones.** No toques knowledge hasta que seguridad esté desplegada.
2. **Diagnosticá antes de arreglar.** Especialmente S24-07 (500 en knowledge) — leé los logs, no asumás.
3. **No inventés datos.** Si algo falta, reportá. No hardcodees valores de prueba en producción.
4. **No toques el módulo commercial (S23).** `backend/apps/commercial/` es off-limits.
5. **No toques archivos FROZEN de la KB:** ENT_OPS_STATE_MACHINE, PLB_ORCHESTRATOR.
6. **Commit por fase.** Cada fase es un commit separado con mensaje descriptivo.
7. **Tests deben pasar antes de merge.** `python manage.py test` green.
8. **Si algo falla, pará y reportá.** No sigas adelante con errores.

## Sprint — 15 items en 4 fases

### Fase 0 — Security Hardening (S24-01 a S24-06)

**S24-01:** JWT blacklist — agregar `rest_framework_simplejwt.token_blacklist` a INSTALLED_APPS + migrate.
**S24-02:** JWT config — ACCESS=30min, REFRESH=7d, ROTATE=True, BLACKLIST_AFTER_ROTATION=True.
**S24-03:** Nginx rate limiting — 4 zones nombradas (general_zone 10r/s, knowledge_zone 2r/s, commercial_zone 5r/s, auth_zone 3r/s) + limit_req por location con burst.
**S24-04:** DRF throttle — user=60/min, anon=20/min. KnowledgeRateThrottle custom 10/min.
**S24-05:** Signed URLs MinIO — presigned GET TTL 15min + verificación pertenencia + log EMISIÓN en EventLog. (Nota: Django registra emisión, no descarga efectiva.)
**S24-06:** Headers (HSTS, nosniff, X-Frame-Options DENY, server_tokens off, 10M body) + cookies (HttpOnly, Secure, SameSite=Lax).

**Verificaciones post-Fase 0:**
- Refresh rotation: anterior → 401
- Rate limiting: burst+1 → 429
- Signed URL: expirada → error, otro cliente → 403
- `curl -I https://mwt.one/` → headers presentes

**Rollback:** documentado en LOTE por componente. JWT: migrate zero. Nginx: comentar directives. DRF: quitar throttle classes. Signed URLs: revertir a link directo.

### Fase 1 — Knowledge Pipeline (S24-07 a S24-11)

**Preflight:** verificar pgvector extension instalada.

**S24-07:** Fix 500 /api/knowledge/ask/ — DIAGNOSTICAR PRIMERO.
- Criterio Ruta A (RAG): status 200, `answer` no vacío, `source_chunks[]`
- Criterio Ruta B (live): status 200, `answer` no vacío, `source_entities[]`

**S24-08:** Carga pgvector — script load_kb.py respetando POL_VISIBILIDAD:
- CEO-ONLY → SKIP completo
- ceo_only_sections → excluir esas secciones
- Metadata: source_file, visibility, section_id
- Verificar: `SELECT count(*) FROM knowledge_chunks WHERE visibility='CEO-ONLY'` = 0

**S24-09:** Filtro visibilidad — CLIENT_* solo PUBLIC + PARTNER_B2B. CEO ve PUBLIC + PARTNER_B2B + INTERNAL.

**S24-10:** Ruta A — Clasificador de intención con enum cerrado:
- QUERY_PRODUCT, QUERY_OPERATIONS → pgvector search
- Fail-closed: confidence < 0.7 → ESCALATE, multi-intent → ESCALATE, parse failure → ESCALATE
- Params incompletos + intent claro → ASK_CLARIFICATION

**S24-11:** Ruta B — Query orchestration live:
- QUERY_EXPEDIENTE → ORM con for_user(user)
- DOWNLOAD_DOC → signed URL (reutiliza S24-05)
- ESCALATE → alerta CEO

**Rollback Fase 1:** knowledge revert a estado pre-fix. pgvector: TRUNCATE. Clasificador: todo → ESCALATE.

### Fase 2 — Verificación ENT_PLAT_SEGURIDAD (S24-12)

Recorrer TODOS los [PENDIENTE] de ENT_PLAT_SEGURIDAD (secciones A-H). Reportar estado ✅/❌/⚠️ con evidencia en `Sprints/REPORTE_SEGURIDAD_S24.md`.

Checklist obligatorio de secrets: .env prod, rotación, ubicación, exclusión Git, exclusión compose, custodia por secret (Django SECRET_KEY, JWT key, PostgreSQL, Redis, MinIO, API keys, n8n).

**Timing:** recolectar durante Fase 1. Promoción documental de ENT_PLAT_SEGURIDAD → post-Fase 3.

### Fase 3 — Tests + Observabilidad (S24-13 a S24-15)

**S24-13:** 15+ tests: JWT expiry, rotation, blacklist, throttle 429, signed URL emisión, CLIENT scope, visibility filter, classifier (injection→ESCALATE, legítimo→correcto, baja confianza→ESCALATE, params incompletos→ASK_CLARIFICATION), CORS preflight (permitido y no permitido).

**S24-14:** Observabilidad: log emisión URLs, log 429s, log blacklists, log errores knowledge.

**S24-15:** E2E walkthrough como CLIENT_MARLUVAS documentado en `Sprints/E2E_WALKTHROUGH_S24.md`.

### Fase 4 — Hotfixes

Reservada. Agregar commits conforme aparezcan.

## Merge

```bash
gh pr create --title "Sprint 24: Security B2B + Knowledge Pipeline"
# CI green → merge
```

## Seguridad del sprint

- El clasificador NUNCA genera SQL, NUNCA accede a DB, NUNCA recibe contexto sensible
- pgvector NUNCA contiene chunks CEO-ONLY
- Signed URLs verifican pertenencia ANTES de generar
- Rate limiting no produce doble bloqueo (verificar Nginx + DRF juntos)
- CORS: solo portal.mwt.one en Access-Control-Allow-Origin
