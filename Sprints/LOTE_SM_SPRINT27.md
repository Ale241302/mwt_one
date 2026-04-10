# LOTE_SM_SPRINT27 — Seguridad Residual: Audit Completo + Backups + Hardening
id: LOTE_SM_SPRINT27
version: 1.6
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
status: DRAFT — Auditado R5 9.5/10 APROBADO. Pendiente aprobación CEO.
stamp: DRAFT v1.6 — 2026-04-09
tipo: Lote ruteado (ref → PLB_ORCHESTRATOR §E)
sprint: 27
priority: P1
depends_on: LOTE_SM_SPRINT24 (DONE — seguridad B2B base),
            LOTE_SM_SPRINT25 (DONE — payment machine + deferred + parent/child, 59 tests)
preconditions:
  - Deploy estable: `python manage.py check --deploy` OK, `nginx -t` OK
  - Rama main sin drift de infra
  - Acceso SSH confirmado por AG-02
  - GPG key CEO disponible
  - Cuenta Cloudflare free tier creada
  - Acceso DNS registrador (3 dominios)
  - Certificado TLS válido en origin (mwt.one, ranawalk.com, portal.mwt.one)
  - Canal push para alertas configurado (ntfy/Telegram/webhook)
refs:
  - ENT_PLAT_SEGURIDAD (DRAFT v2.0 — target: VIGENTE post-S27)
  - ENT_GOB_PENDIENTES (CEO-17 parcial, CEO-19 parcial → residual a este sprint)
  - POL_EPHEMERAL_OUTPUT
  - PLB_INCIDENT_RESPONSE

changelog:
  - v1.0 (2026-04-08): Lote inicial. Residuales CEO-17/CEO-19 + ENT_PLAT_SEGURIDAD.Z §8-§10.
  - v1.1 (2026-04-09): EN PREPARACIÓN → DRAFT.
  - v1.2 (2026-04-09): Fixes R1 (8.2/10 — 2B + 5M + 2N). Fase 0 A-H. DR mínimo viable. Preconditions. Backup endurecido. mem_limit/cpus. Matriz secrets. Rollback granular.
  - v1.3 (2026-04-09): Fixes R2 (9.1/10 — 2M + 4N). [DECISION_CEO]. +S27-15b/15c. Ref WAF. Conteo. TLS precheck. Celery pgrep.
  - v1.4 (2026-04-09): Fixes R3 (9.3/10 — 2M + 2N). DNS 24h + cutover. Redis REDISCLI_AUTH. Push obligatorio.
  - v1.5 (2026-04-09): Fixes R4 (9.4/10 — 2M + 3N). Taxonomía canónica. Config hard fail/opcional. Escalera L1/L2/L3. NanoCpus. Cron manual inmediato.
  - v1.6 (2026-04-09): Fixes R5 (9.5/10 — 1M + 2N). M1: +S27-07d2/07g2 remediación mínima in-sprint para F2/G2 si verificación falla (alerting cron + EventLog audit). N1: gate DNS "sin 5xx sostenido >60s" en vez de "0 downtime". N2: credenciales canal push incluidas explícitamente en S27-11.

---

## Contexto

Sprint 24 resolvió bloqueadores B2B (JWT rotation, rate limiting, signed URLs, security headers). Verificó secciones A-E, H de ENT_PLAT_SEGURIDAD → DRAFT v2.0.

Este sprint cierra la deuda residual:

1. **CEO-17 residual:** verificación F (monitoring) y G (compliance) + remediación mínima si fallan + checklist evidencias → VIGENTE
2. **CEO-19 residual:** secrets audit con inventario formal
3. **ENT_PLAT_SEGURIDAD.Z §8-10:** DR mínimo viable, Cloudflare, Docker hardening

**Esfuerzo estimado:** 12-14h (Alejandro)

---

## Taxonomía de estados ENT_PLAT_SEGURIDAD

| Tag | Emoji | Significado | Bloquea cierre |
|-----|-------|-------------|---------------|
| `[ACTIVO]` | ✅ | Verificado y operativo | No |
| `[PENDIENTE]` | ⚠️ | Acción correctiva requerida | **Sí** |
| `[N_A]` | ➖ | No aplica (justificado) | No |
| `[DECISION_CEO]` | 🔷 | Requiere decisión gobernanza | No |

**Cierre:** `grep -c '\[PENDIENTE\]' ENT_PLAT_SEGURIDAD.md` = 0. Tags entre corchetes son canónicos; emojis decorativos.

---

## Fase 0 — Verificación completa ENT_PLAT_SEGURIDAD (CEO-17 residual)

**Agente:** AG-02 · **Esfuerzo:** 3-4h

### Subfase 0a — Re-verificación A-E, H (drift check)

| ID | Tarea | Criterio de done |
|----|-------|-----------------|
| S27-01 | SSH: restricción IP | sshd_config documentado. Si no → agregar. |
| S27-02 | WAF estado actual | Si no → S27-18 (Cloudflare). |
| S27-03 | HSTS + headers | `curl -I` confirma S24. |
| S27-04 | DNSSEC (3 dominios) | `dig +dnssec`. N/A si no soportado. |
| S27-05 | Data at rest | PostgreSQL TDE, MinIO. Documentar. |
| S27-06 | Data in transit | sslmode=require. |
| S27-07 | Docker: non-root, ports, socket | Solo Nginx expone. |

### Subfase 0b — Verificación F y G (NUEVAS) + remediación mínima

| ID | Tarea | Sección | Criterio de done |
|----|-------|---------|-----------------|
| S27-07c | Logging: handler, destino, rotación | F1 | Docker log driver max-size/max-file si falta. |
| S27-07d | Alerting: 5xx, disk full, OOM | F2 | Documentar estado. |
| **S27-07d2** | **Remediación F2 si falla:** cron health check mínimo | F2 | Si F2 = negativo → implementar cron cada 5min: `curl -sf https://mwt.one/health/ > /dev/null \|\| echo "ALERT $(date)" >> /opt/mwt/health_alerts.log` + push al canal configurado (S27-15c). Esto lleva F2 a [ACTIVO] con alerting básico. |
| S27-07e | Log retention | F3 | 30d servidor, 90d backup. |
| S27-07f | LGPD consent, data retention | G1 | [ACTIVO], [PENDIENTE], o [N_A]. |
| S27-07g | Audit trail acceso datos personales | G2 | Verificar EventLog. |
| **S27-07g2** | **Remediación G2 si falla:** middleware audit mínimo | G2 | Si G2 = negativo → agregar logging de acceso a endpoints sensibles (expedientes, pagos, documentos): `logger.info(f"DATA_ACCESS user={request.user} path={request.path}")` en middleware o decorator. Esto lleva G2 a [ACTIVO] con audit trail básico. |

### Subfase 0c — Consolidación

| ID | Tarea | Criterio de done |
|----|-------|-----------------|
| S27-07h | Actualizar ENT_PLAT_SEGURIDAD (A-H) | Tags canónicos. `grep -c '\[PENDIENTE\]'` = 0. |
| S27-07i | Checklist evidencias CEO | TRANSITORIO: control × tag × evidencia × fecha. |

### Verificación post-Fase 0

```bash
# JWT
python manage.py shell -c "
from django.conf import settings
st = settings.SIMPLE_JWT
print('ACCESS:', st.get('ACCESS_TOKEN_LIFETIME'))
print('REFRESH:', st.get('REFRESH_TOKEN_LIFETIME'))
print('ROTATE:', st.get('ROTATE_REFRESH_TOKENS'))
print('BLACKLIST:', st.get('BLACKLIST_AFTER_ROTATION'))
"

# Cookies
python manage.py shell -c "
from django.conf import settings
print('HTTPONLY:', settings.SESSION_COOKIE_HTTPONLY)
print('SECURE:', settings.SESSION_COOKIE_SECURE)
print('SAMESITE:', settings.SESSION_COOKIE_SAMESITE)
print('CSRF_SECURE:', settings.CSRF_COOKIE_SECURE)
"

# Redis
docker exec $(docker ps --filter name=redis -q) redis-cli CONFIG GET requirepass

# Headers
curl -I https://mwt.one/ 2>/dev/null | grep -E "Strict-Transport|X-Content|X-Frame|Server:"

# Docker logging (F)
docker inspect --format '{{.HostConfig.LogConfig.Type}} max-size={{index .HostConfig.LogConfig.Config "max-size"}}' $(docker ps -q)

# Admin users (E)
python manage.py shell -c "
from django.contrib.auth import get_user_model
for u in get_user_model().objects.filter(is_staff=True):
    print(f'{u.username} | super={u.is_superuser} | last_login={u.last_login}')
"

# Taxonomía
grep -c '\[PENDIENTE\]' ENT_PLAT_SEGURIDAD.md  # = 0
```

### Gate Fase 0
- [ ] 0 `[PENDIENTE]` en ENT_PLAT_SEGURIDAD
- [ ] F y G verificadas + remediadas si negativas (S27-07d2/07g2)
- [ ] Checklist evidencias entregado
- [ ] Cuentas privilegiadas inventariadas

---

## Fase 1 — Secrets Audit (CEO-19 residual)

**Agente:** AG-02 · **Esfuerzo:** 2-3h

| ID | Tarea | Criterio de done |
|----|-------|-----------------|
| S27-08 | truffleHog scan repo | 0 hallazgos. |
| S27-09 | .env permisos 600 | Owner correcto. |
| S27-10 | .env en .gitignore | git ls-files vacío. |
| S27-11 | Matriz formal secrets | 12+ entries. Incluir explícitamente: Django SECRET_KEY, JWT signing key, PostgreSQL password, Redis password, MinIO access/secret, API keys (Claude, OpenAI), n8n credentials, Cloudflare API token, GitHub deploy keys, GPG key backup, Celery broker URL, SMTP credentials (si CEO-28 resuelto), **credenciales canal push alertas (Telegram token/webhook URL/ntfy auth si aplica)**. |
| S27-12 | Redis requirepass | docker-compose + redis.conf. Django/Celery con password. |
| S27-13 | Rotación 90d | ENT_PLAT_SEGURIDAD.H documentado. |

### Gate Fase 1
- [ ] truffleHog 0
- [ ] .env 600 + .gitignore
- [ ] Matriz 12+ entries (incluye push alert creds)
- [ ] Redis auth + Django/Celery
- [ ] Rotación documentada

---

## Fase 2 — DR Mínimo Viable

**Agente:** AG-02 · **Esfuerzo:** 3-4h

| ID | Tarea | Criterio de done |
|----|-------|-----------------|
| S27-14 | Script `backup_mwt.sh` | set -euo pipefail, umask, mktemp, trap. Config obligatoria (hard fail) vs opcional (manifest missing_files[]). Push alert ante fallo. |
| S27-15 | Cron diario (3am UTC-6) | Exportar crontab. **Ejecución manual inmediata** + artefactos en MinIO. Día siguiente = validación diferida. |
| S27-15b | Cleanup retention 30d | Purgar >30d por prefijo/fecha. |
| S27-15c | Canal push alerta | ntfy/Telegram/webhook. Sentinel como complemento. |
| S27-16 | Restore drill integral | DB test + expedientes + MinIO objects + app arranca. |
| S27-17 | RPO/RTO | RPO: 24h. RTO: [DECISION_CEO — propuesta: 4h]. Retención: 30d. |

### Script de referencia (backup_mwt.sh)

```bash
#!/bin/bash
set -euo pipefail
umask 077

DATE=$(date +%Y-%m-%d)
WORK_DIR=$(mktemp -d)
STATUS_FILE="/opt/mwt/backup_status.txt"
MISSING_FILES=()

cleanup() { rm -rf "$WORK_DIR"; }
trap cleanup EXIT

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"; }
fail() {
    log "ERROR: $1"
    echo "FAIL $(date '+%Y-%m-%d %H:%M:%S') $1" > "$STATUS_FILE"
    # Push alert (descomentar canal configurado):
    # curl -d "MWT Backup FAIL: $1" ntfy.sh/mwt-backup 2>/dev/null || true
    exit 1
}

# 1. PostgreSQL
log "pg_dump..."
pg_dump "$DATABASE_URL" > "${WORK_DIR}/backup_${DATE}.sql" || fail "pg_dump"
DUMP_SIZE=$(stat -c%s "${WORK_DIR}/backup_${DATE}.sql")
DUMP_SHA256=$(sha256sum "${WORK_DIR}/backup_${DATE}.sql" | awk '{print $1}')

# 2. Encrypt
gpg --batch --yes --recipient "$CEO_GPG_KEY_ID" \
    --encrypt "${WORK_DIR}/backup_${DATE}.sql" || fail "GPG"
rm "${WORK_DIR}/backup_${DATE}.sql"

# 3. MinIO
mc mirror --overwrite mwt-local/documents "${WORK_DIR}/minio_mirror/" || fail "MinIO mirror"
MINIO_COUNT=$(find "${WORK_DIR}/minio_mirror/" -type f | wc -l)

# 4. Config — obligatoria (hard fail) vs opcional (registro)
mkdir -p "${WORK_DIR}/config"
[ -f /opt/mwt/docker-compose.yml ] && cp /opt/mwt/docker-compose.yml "${WORK_DIR}/config/" \
    || fail "docker-compose.yml no encontrado"
NGINX_FOUND=0
for f in /opt/mwt/nginx/*.conf; do
    [ -f "$f" ] && cp "$f" "${WORK_DIR}/config/" && NGINX_FOUND=1
done
[ "$NGINX_FOUND" -eq 0 ] && fail "Ningún .conf Nginx"
if ls /opt/mwt/.env* 1>/dev/null 2>&1; then
    sha256sum /opt/mwt/.env* > "${WORK_DIR}/config/env_checksums.txt"
else
    MISSING_FILES+=("env_checksums")
fi

# 5. Manifest
cat > "${WORK_DIR}/manifest_${DATE}.json" <<EOF
{
  "date": "${DATE}",
  "pg_size": ${DUMP_SIZE},
  "pg_sha256": "${DUMP_SHA256}",
  "minio_count": ${MINIO_COUNT},
  "config_status": "$([ ${#MISSING_FILES[@]} -eq 0 ] && echo 'complete' || echo 'partial')",
  "missing_files": [$(printf '"%s",' "${MISSING_FILES[@]}" | sed 's/,$//')]
}
EOF

# 6. Upload
mc cp "${WORK_DIR}/backup_${DATE}.sql.gpg" "mwt-backup/postgresql/" || fail "upload dump"
mc mirror --overwrite "${WORK_DIR}/minio_mirror/" "mwt-backup/minio_${DATE}/" || fail "upload minio"
mc cp "${WORK_DIR}/manifest_${DATE}.json" "mwt-backup/manifests/" || fail "upload manifest"
mc cp -r "${WORK_DIR}/config/" "mwt-backup/config_${DATE}/" || fail "upload config"

echo "OK $(date '+%Y-%m-%d %H:%M:%S')" > "$STATUS_FILE"
log "Backup OK. Config: $([ ${#MISSING_FILES[@]} -eq 0 ] && echo 'complete' || echo "partial: ${MISSING_FILES[*]}")"
```

### Gate Fase 2
- [ ] backup_mwt.sh OK (ejecución manual inmediata)
- [ ] Manifest con config_status/missing_files
- [ ] Cron + crontab exportado
- [ ] Cleanup 30d
- [ ] Push alert funcional (test)
- [ ] Restore drill OK
- [ ] RPO/RTO documentado

---

## Fase 3 — Cloudflare + Docker Hardening

**Agente:** AG-02 · **Esfuerzo:** 2-3h

**PRE-REQUISITO:** Consola out-of-band abierta.

### Cutover DNS

1. Export zona DNS actual
2. Recrear registros en Cloudflare
3. Validar pre-cutover
4. Ventana controlada (baja actividad)
5. Rollback DNS = **hasta 24h**

### Escalera mitigación DNS

- **L1:** Corregir registro/SSL en Cloudflare (~minutos)
- **L2:** Desactivar proxy en host afectado, DNS-only (~minutos)
- **L3:** Rollback nameservers (hasta 24h, solo si L1+L2 no estabilizan)

| ID | Tarea | Criterio de done |
|----|-------|-----------------|
| S27-18 | Cloudflare: 3 dominios | dig × 3 Cloudflare IPs. SSL Full (strict). portal.mwt.one = CNAME en zona mwt.one. |
| S27-18b | Monitoreo cutover 3 dominios | watch + curl × 3. Si 5xx → escalera L1/L2/L3. |
| S27-19 | Docker non-root | PostgreSQL→postgres. Celery→USER si necesario. |
| S27-20 | Resource limits: mem_limit + cpus | Memoria: `docker stats --no-stream` MEM LIMIT != 0. CPU: `docker inspect --format '{{.HostConfig.NanoCpus}}'` != 0. |
| S27-21 | Health checks | Django→curl, PostgreSQL→pg_isready, Redis→`REDISCLI_AUTH` ping, Nginx→curl, Celery→pgrep timeout 10s. `docker ps` healthy. |
| S27-22 | Fail2ban SSH | maxretry=5, bantime=3600s. Consola alternativa pre. IP no baneada post. |

### Gate Fase 3
- [ ] 3 dominios via Cloudflare
- [ ] Sin 5xx sostenido >60s durante cutover
- [ ] MEM limits: docker stats != 0
- [ ] CPU limits: docker inspect NanoCpus != 0
- [ ] Health checks healthy (Redis con auth)
- [ ] Fail2ban activo

---

## Definition of Done (S27)

### Hitos técnicos (AG-02)

| # | Check | Verificación |
|---|-------|-------------|
| 1 | ENT_PLAT_SEGURIDAD: 0 [PENDIENTE] (A-H) | grep = 0 |
| 2 | F2/G2 remediados si negativos | S27-07d2/07g2 ejecutados |
| 3 | Checklist evidencias entregado | TRANSITORIO |
| 4 | truffleHog 0 | Output |
| 5 | Matriz secrets 12+ (incluye push creds) | ENT_PLAT_SEGURIDAD.B4 |
| 6 | .env 600 + .gitignore | ls + git |
| 7 | Redis requirepass + Django/Celery | redis-cli + .env |
| 8 | Backup integral + cleanup + push alert | Manifest + retention + push |
| 9 | Restore drill OK | DB + MinIO + app |
| 10 | 3 dominios → Cloudflare | dig × 3 |
| 11 | Docker: non-root + MEM + CPU + health | stats + inspect + ps |
| 12 | Fail2ban SSH | fail2ban-client |
| 13 | RESUMEN_SPRINT27.md | Evidencias |

### CEO gate

| # | Check |
|---|-------|
| 14 | Revisar checklist evidencias |
| 15 | Aprobar ENT_PLAT_SEGURIDAD → VIGENTE |
| 16 | Definir RTO (propuesta: 4h) |

**CEO pendientes resueltos:** CEO-17, CEO-19

---

## Rollback

**Orden:** DNS (L1→L2→L3) → Fail2ban → Docker → Backup cron → Redis

| Componente | Rollback | Tiempo |
|-----------|----------|--------|
| Cloudflare | L1 fix CF. L2 DNS-only. L3 nameservers (**hasta 24h**). | Variable |
| Fail2ban | stop + disable | Consola alt |
| Docker non-root | Revertir USER → rebuild | ~2min |
| Limits | Quitar mem_limit/cpus → restart | Rolling |
| Health checks | Quitar → restart | Sin impacto |
| Redis pass | Quitar → restart | ~10s |
| Backup cron | Export → remover SOLO línea. **Nunca `crontab -r`.** | Inmediato |

---

## Conteo

| Categoría | Cantidad |
|-----------|----------|
| Items totales | 34 (v1.5 32 + S27-07d2 + S27-07g2) |
| Ejecución | 26 |
| Documentales | 8 |
| Fases | 4 |

---

## Dependencias externas

GPG key CEO · Cloudflare free tier · DNS registrador (3) · TLS origin (3) · Fail2ban · Consola out-of-band · Canal push (ntfy/Telegram/webhook)

---

## Notas para auditoría

1. **100% ops/infra.** 0 Django models/endpoints/migrations (excepto S27-07d2/07g2 que son remediación mínima: cron + logger).
2. **Fase 0 A-H con salida garantizada.** F2/G2 negativos → remediación in-sprint (S27-07d2: cron health + push, S27-07g2: middleware audit logger). Sprint no se auto-bloquea.
3. **Taxonomía canónica.** [ACTIVO]/[PENDIENTE]/[N_A]/[DECISION_CEO]. grep cuenta tags.
4. **DR = PostgreSQL + MinIO + config (hard/opcional) + drill + 30d + push.**
5. **DNS: rollback hasta 24h. Escalera L1/L2/L3.**
6. **Gate DNS: "sin 5xx sostenido >60s"**, no "0 downtime" absoluto.
7. **Secrets matriz incluye push alert creds.**
8. **CPU: docker inspect NanoCpus.** MEM: docker stats.
9. **Cron: ejecución manual inmediata.** Día siguiente = diferida.
10. **Redis health: REDISCLI_AUTH.** Celery: pgrep.

---

## Auditoría

| Ronda | Auditor | Score | Hallazgos | Aplicados en |
|-------|---------|-------|-----------|-------------|
| R1 (v1.1) | ChatGPT | 8.2/10 | 2B + 5M + 2N | v1.2 |
| R2 (v1.2) | ChatGPT | 9.1/10 | 2M + 4N | v1.3 |
| R3 (v1.3) | ChatGPT | 9.3/10 | 2M + 2N | v1.4 |
| R4 (v1.4) | ChatGPT | 9.4/10 | 2M + 3N | v1.5 |
| R5 (v1.5) | ChatGPT | 9.5/10 | 1M + 2N | v1.6 |

---

Stamp: DRAFT v1.6 — 2026-04-09
