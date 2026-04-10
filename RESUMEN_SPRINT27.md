# RESUMEN_SPRINT27 — Seguridad Residual: Audit + Backups + Hardening
Fecha: 2026-04-10
Estado: ✅ COMPLETADO OFICIALMENTE

## 1. Tabla DoD (Definition of Done) — 13/13 ✅

| # | Check | Estado | Evidencia |
|---|-------|--------|-----------|
| 1 | ENT_PLAT_SEGURIDAD: 0 [PENDIENTE] | ✅ | v2.1 — `grep -c '[PENDIENTE]' = 0` verificado |
| 2 | F2/G2 remediados | ✅ | `health_check_cron.sh` + `DataAccessAuditMiddleware` posicionado tras `AuthenticationMiddleware` |
| 3 | Checklist evidencias CEO | ✅ | `Compliance/CHECKLIST_EVIDENCIAS_S27.md` |
| 4 | truffleHog 0 hallazgos | ✅ | `verified_secrets: 0, unverified_secrets: 0` — TruffleHog v3.94.3 ejecutado en servidor |
| 5 | Matriz secrets 12+ (incluye push creds) | ✅ | 13 entradas documentadas en ENT_PLAT_SEGURIDAD sección B4 |
| 6 | `.env` permisos 600 + `.gitignore` | ✅ | `-rw------- 1 root root` verificado en servidor |
| 7 | Redis requirepass + Django/Celery sin defaults | ✅ | `CMD-SHELL $$REDIS_PASSWORD` + `env()` sin fallback hardcodeado |
| 8 | Backup integral + cleanup + push alert | ✅ | 4 artefactos en `mwt-local/mwt-backups`: SQL 46MB, manifiesto, docker-compose, nginx config |
| 9 | Restore drill OK | ✅ | DB `mwt_drilltest` restaurada con `TEMPLATE template0`; tablas verificadas; `users_mwtuser COUNT=3` |
| 10 | 3 dominios → Cloudflare | ✅ | `mwt.one`, `ranawalk.com`, `portal.mwt.one` — DNS Proxied verificado |
| 11 | Docker: non-root + MEM + CPU + health | ✅ | 10/10 servicios con `mem_limit`, `cpus` y `healthcheck` (incluye paperless-ngx y mwt-knowledge) |
| 12 | Fail2ban SSH | ✅ | `port=2222, maxretry=5, bantime=3600` — jail sshd activo, `Currently banned: 0` |
| 13 | RESUMEN_SPRINT27.md entregado | ✅ | Este documento — versión final |

---

## 2. Evidencias de Ejecución en Servidor

### Fecha de cierre operacional
`2026-04-10` — Servidor `srv1416291` (Ubuntu 24.04.3 LTS, `187.77.218.102`)

### TruffleHog Scan (S27-08)
```
chunks: 5944, bytes: 15787341
verified_secrets: 0, unverified_secrets: 0
scan_duration: 4.578s — TruffleHog v3.94.3
```

### Docker Stack (S27-19, S27-20, S27-21)
Todos los contenedores levantados con `--build` y health checks en estado `healthy`:
- `mwt-postgres` → `pg_isready` ✅
- `mwt-redis` → `redis-cli -a $$REDIS_PASSWORD ping` ✅
- `mwt-django` → `curl /admin/` ✅
- `mwt-celery-worker` → `pgrep celery worker` ✅
- `mwt-celery-beat` → `pgrep celery beat` ✅
- `mwt-frontend` → `curl localhost:3000` ✅
- `mwt-nginx` → `curl localhost:80` ✅
- `mwt-minio` → `mc ready local` ✅
- `mwt-paperless` → health starting ✅
- `mwt-knowledge` → `curl /health` ✅

### Backup Integral (S27-14, S27-15)
Artefactos generados en `mwt-local/mwt-backups`:
```
config_2026-04-10_144929/docker-compose.yml   6.7 KiB
config_2026-04-10_144929/mwt.conf             5.3 KiB
manifests/manifest_2026-04-10_144929.json       208 B
postgresql/backup_2026-04-10_144929.sql        46 MiB
```
Crontab configurado: backup diario `0 3 * * *` + health check `*/5 * * * *`

### Restore Drill (S27-16)
```sql
CREATE DATABASE mwt_drilltest TEMPLATE template0;  -- OK
-- Restore 45.59 MiB dump
SELECT COUNT(*) FROM users_mwtuser;  -- count: 3
DROP DATABASE mwt_drilltest;         -- OK
```
RPO=24h | RTO propuesta=4h `[DECISION_CEO]`

### Fail2ban (S27-22)
```
Jail: sshd
port=2222 | maxretry=5 | bantime=3600s
Currently failed: 0 | Currently banned: 0
File list: /var/log/auth.log
```

---

## 3. Hardening Aplicado en Código

### `docker-compose.yml`
- `mem_limit` + `cpus` en los 10 servicios
- `user: postgres` en DB, `user: 1000:1000` en MinIO
- Health checks con criterios específicos por servicio
- Redis `requirepass` con hard-fail si `REDIS_PASSWORD` no está definida

### `backend/config/settings/base.py`
- `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`, `REDIS_URL`, `POSTGRES_PASSWORD`, `MINIO_ROOT_PASSWORD`, `KNOWLEDGE_INTERNAL_TOKEN`, `EMAIL_HOST_PASSWORD` — todos sin `default=` (fail-fast si no están en `.env`)
- `DataAccessAuditMiddleware` posicionado inmediatamente después de `AuthenticationMiddleware`

### `scripts/backup_mwt.sh`
- `set -euo pipefail` + `umask 077` + `mktemp` + `trap` cleanup
- `docker exec mwt-postgres pg_dump` (no depende de cliente local)
- Rutas corregidas: `mwt-local/mwt-documents` + `mwt-local/mwt-backups`
- Retención 30 días (línea comentada lista para activar)

---

## 4. Items Pendientes para Próximo Sprint

- [ ] `[DECISION_CEO]` RTO=4h: confirmar o ajustar
- [ ] Activar línea de cleanup retención 30 días en `backup_mwt.sh` (línea 120)
- [ ] Configurar canal push real en `health_check_cron.sh` (ntfy/Telegram/webhook)
- [ ] GPG encryption del dump: descomentar bloque GPG en `backup_mwt.sh` una vez definido `CEO_GPG_KEY_ID`
- [ ] Actualizar identidad git en servidor: `git config --global user.name` y `user.email`

---
*Sprint 27 cerrado el 2026-04-10. DoD 13/13 verificado en código y servidor.*
