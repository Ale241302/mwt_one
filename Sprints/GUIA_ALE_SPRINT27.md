# GUIA_ALE_SPRINT27 — Instrucciones de Ejecución AG-02
id: GUIA_ALE_SPRINT27
version: 1.0
status: DRAFT
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
stamp: DRAFT v1.0 — 2026-04-09
tipo: Registro especial — instrucciones de ejecución para AG-02
refs: LOTE_SM_SPRINT27 v1.6

**Sprint:** 27 — Seguridad Residual: Audit Completo + Backups + Hardening
**Lote:** LOTE_SM_SPRINT27 v1.6 (auditado R5, 9.5/10)
**Agente:** Alejandro (AG-02)

---

## Antes de empezar

- [ ] `python manage.py check --deploy` → OK
- [ ] `nginx -t` → OK
- [ ] Acceso SSH funcionando
- [ ] GPG key del CEO disponible (preguntar si no la tenés)
- [ ] Consola alternativa abierta (Hostinger panel) — **no cerrar durante todo el sprint**
- [ ] Canal push configurado para alertas (ntfy.sh, Telegram, o webhook — confirmar con CEO cuál)

---

## Fase 0 — Verificación ENT_PLAT_SEGURIDAD (3-4h)

**Objetivo:** recorrer el servidor, documentar estado real, actualizar ENT_PLAT_SEGURIDAD.

### Paso 1: Re-verificar controles S24 (drift check)

Correr todo esto y guardar output:

```bash
# S27-01: SSH
cat /etc/ssh/sshd_config | grep -E "AllowUsers|AllowGroups|PermitRootLogin|PasswordAuthentication"
sudo iptables -L -n | grep 22

# S27-02: WAF
nginx -V 2>&1 | grep -i modsecurity
# Si no hay output → no hay WAF, se resuelve en Fase 3 con Cloudflare

# S27-03: Headers
curl -I https://mwt.one/ 2>/dev/null | grep -E "Strict-Transport|X-Content|X-Frame|Server:"

# S27-04: DNSSEC
for d in mwt.one ranawalk.com portal.mwt.one; do echo "=== $d ==="; dig +dnssec $d | grep -E "RRSIG|flags"; done

# S27-05: Data at rest
docker exec $(docker ps --filter name=postgres -q) psql -U postgres -c "SHOW ssl;"
docker exec $(docker ps --filter name=minio -q) mc admin info local 2>/dev/null || echo "mc no disponible en container"

# S27-06: Data in transit
grep -i ssl /opt/mwt/.env* || grep -i sslmode /opt/mwt/.env*

# S27-07: Docker
for c in $(docker ps -q); do
  echo "$(docker inspect --format '{{.Name}}: User={{.Config.User}}' $c)"
done
docker compose -f /opt/mwt/docker-compose.yml config | grep -A2 "ports:"
docker inspect $(docker ps -q) --format '{{.Name}}: {{.HostConfig.Binds}}' | grep docker.sock
```

### Paso 2: Verificar F (monitoring) y G (compliance) — NUEVOS

```bash
# S27-07c: Logging
docker inspect --format '{{.HostConfig.LogConfig.Type}} max-size={{index .HostConfig.LogConfig.Config "max-size"}}' $(docker ps -q)
# Si max-size está vacío → configurar en docker-compose.yml:
# logging:
#   driver: json-file
#   options:
#     max-size: "10m"
#     max-file: "5"

# S27-07d: Alerting — ¿hay algo?
crontab -l | grep -i health
crontab -l | grep -i alert
# Si vacío → implementar S27-07d2 (ver paso 3)

# S27-07e: Log retention
ls -la /var/log/ | head -20
docker system df
# Documentar cuánto espacio y si hay rotación

# S27-07f/g: Compliance (LGPD)
python manage.py shell -c "
from django.apps import apps
# Verificar si hay consent model o middleware
for model in apps.get_models():
    fields = [f.name for f in model._meta.get_fields()]
    if any('consent' in f.lower() for f in fields):
        print(f'{model.__name__}: {fields}')
"
# Verificar EventLog para audit trail
python manage.py shell -c "
from apps.expedientes.models import EventLog
print('Total events:', EventLog.objects.count())
print('Sample actions:', list(EventLog.objects.values_list('action_source', flat=True).distinct()[:10]))
"
```

### Paso 3: Remediación mínima si F2 o G2 fallan

**S27-07d2 — Si no hay alerting:**
```bash
# Crear script de health check
cat > /opt/mwt/health_check_cron.sh << 'EOF'
#!/bin/bash
for url in https://mwt.one/health/ https://portal.mwt.one/health/; do
  HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
  if [ "$HTTP_CODE" != "200" ]; then
    echo "ALERT $(date) $url returned $HTTP_CODE" >> /opt/mwt/health_alerts.log
    # Push (descomentar el configurado):
    # curl -d "MWT ALERT: $url returned $HTTP_CODE" ntfy.sh/mwt-backup 2>/dev/null
  fi
done
EOF
chmod +x /opt/mwt/health_check_cron.sh

# Agregar a crontab (cada 5 min)
crontab -l > /tmp/crontab_backup.txt
(crontab -l; echo "*/5 * * * * /opt/mwt/health_check_cron.sh") | crontab -
```

**S27-07g2 — Si no hay audit trail de acceso a datos sensibles:**

Agregar middleware o decorator de logging en endpoints sensibles:
```python
# backend/apps/core/middleware.py (o donde corresponda)
import logging
logger = logging.getLogger('data_access')

class DataAccessAuditMiddleware:
    SENSITIVE_PATHS = ['/api/expedientes/', '/api/pagos/', '/api/documents/']
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        if any(request.path.startswith(p) for p in self.SENSITIVE_PATHS):
            logger.info(f"DATA_ACCESS user={request.user} path={request.path} method={request.method} status={response.status_code}")
        return response
```

Agregar a `MIDDLEWARE` en settings y configurar logger `data_access`.

### Paso 4: Actualizar ENT_PLAT_SEGURIDAD

Para cada control, usar EXACTAMENTE uno de estos tags:
- `[ACTIVO]` — verificado y operativo
- `[PENDIENTE]` — requiere acción (bloquea cierre)
- `[N_A]` — no aplica (con justificación)
- `[DECISION_CEO]` — requiere decisión del CEO

**Verificar que:** `grep -c '\[PENDIENTE\]' ENT_PLAT_SEGURIDAD.md` = 0

### Paso 5: Generar checklist evidencias

Crear documento TRANSITORIO con tabla: control × tag × evidencia × fecha.

### Gate Fase 0
- [ ] ENT_PLAT_SEGURIDAD actualizado, 0 [PENDIENTE]
- [ ] F/G verificadas (remediadas si negativas)
- [ ] Checklist evidencias listo
- [ ] Admin users inventariados

---

## Fase 1 — Secrets Audit (2-3h)

### Paso 6: Scan del repo

```bash
pip install truffleHog --break-system-packages
cd /path/to/mwt_one
trufflehog git file://. --only-verified 2>&1 | tee /tmp/trufflehog_output.txt
echo "Hallazgos: $(grep -c 'Found' /tmp/trufflehog_output.txt || echo 0)"
```

### Paso 7: Permisos .env

```bash
find /opt/mwt -name "*.env" -o -name ".env*" | while read f; do
  PERMS=$(stat -c "%a" "$f")
  echo "$f: $PERMS $([ "$PERMS" = "600" ] && echo '✅' || echo '⚠️ FIX: chmod 600')"
done

# Fix si necesario
find /opt/mwt -name "*.env" -o -name ".env*" -exec chmod 600 {} \;
```

### Paso 8: Verificar .gitignore

```bash
cd /path/to/mwt_one
cat .gitignore | grep -i env
git ls-files --others --exclude-standard | grep -i env
# Debe estar vacío
```

### Paso 9: Matriz de secrets

Crear tabla con TODOS estos (y los que encuentres):

| Secreto | Sistema | Ubicación | Owner | Criticidad | Última rotación | Blast radius |
|---------|---------|-----------|-------|-----------|----------------|-------------|
| Django SECRET_KEY | Django | .env | CEO | High | [fecha] | Sessions invalidadas |
| JWT signing key | SimpleJWT | .env (o Django SECRET_KEY) | CEO | High | [fecha] | Tokens invalidados |
| PostgreSQL password | DB | .env | CEO | High | [fecha] | App down |
| Redis password | Cache/Celery | .env + redis.conf | CEO | Medium | [fecha] | Cache flush |
| MinIO access key | Storage | .env | CEO | High | [fecha] | Docs inaccesibles |
| MinIO secret key | Storage | .env | CEO | High | [fecha] | Docs inaccesibles |
| Claude API key | LLM | .env | CEO | Medium | [fecha] | Knowledge offline |
| OpenAI API key | LLM | .env | CEO | Medium | [fecha] | Knowledge offline |
| n8n credentials | Workflows | n8n config | CEO | Medium | [fecha] | Automations down |
| Cloudflare API token | DNS/CDN | .env (post S27-18) | CEO | Medium | [fecha] | DNS changes |
| GPG key backup | Backup | servidor | CEO | High | N/A (key pair) | Backups irrecuperables |
| Push alert creds | Alerting | .env | CEO | Low | [fecha] | Alertas silenciadas |

### Paso 10: Redis requirepass

```bash
# Verificar estado actual
docker exec $(docker ps --filter name=redis -q) redis-cli CONFIG GET requirepass

# Si vacío → activar:
# 1. Agregar a .env: REDIS_PASSWORD=<password-fuerte>
# 2. docker-compose.yml → redis service: command: redis-server --requirepass ${REDIS_PASSWORD}
# 3. Django CACHES: "redis://:${REDIS_PASSWORD}@redis:6379/0"
# 4. Celery broker: "redis://:${REDIS_PASSWORD}@redis:6379/1"
# 5. docker compose up -d redis && docker compose restart django celery
# 6. Verificar: docker exec redis redis-cli -a "$REDIS_PASSWORD" ping → PONG
```

### Paso 11: Documentar rotación

En ENT_PLAT_SEGURIDAD.H crear checklist con frecuencia 90d para cada secret.

### Gate Fase 1
- [ ] truffleHog 0 hallazgos
- [ ] .env 600 + .gitignore
- [ ] Matriz 12+ entries
- [ ] Redis con password + Django/Celery configurados
- [ ] Rotación documentada

---

## Fase 2 — Backup + DR (3-4h)

### Paso 12: Crear script backup_mwt.sh

Copiar el script de referencia del LOTE v1.6 a `/opt/mwt/backup_mwt.sh`. Adaptar:
- `$DATABASE_URL` → verificar que está en .env
- `$CEO_GPG_KEY_ID` → pedir al CEO
- Descomentar la línea de push alert que corresponda al canal configurado
- `chmod +x /opt/mwt/backup_mwt.sh`

**Recuerda:** docker-compose.yml y Nginx .conf son **hard fail** — si no se copian, el script falla. .env checksums son opcionales.

### Paso 13: Ejecución manual + verificar

```bash
# Ejecutar manualmente AHORA (no esperar al cron)
/opt/mwt/backup_mwt.sh

# Verificar artefactos
mc ls mwt-backup/postgresql/
mc ls mwt-backup/manifests/
mc cat mwt-backup/manifests/manifest_$(date +%Y-%m-%d).json
```

### Paso 14: Instalar cron

```bash
# SIEMPRE exportar antes de modificar
crontab -l > /opt/mwt/crontab_backup_$(date +%Y%m%d).txt

# Agregar cron 3am UTC-6
(crontab -l; echo "0 3 * * * /opt/mwt/backup_mwt.sh >> /opt/mwt/backup.log 2>&1") | crontab -

# Verificar
crontab -l | grep backup
```

### Paso 15: Cleanup retention

```bash
# Crear script o agregar al cron (5am)
cat > /opt/mwt/backup_cleanup.sh << 'EOF'
#!/bin/bash
set -euo pipefail
CUTOFF=$(date -d "30 days ago" +%Y-%m-%d)
for prefix in postgresql minio_ config_ manifests; do
  mc ls mwt-backup/${prefix}/ | while read line; do
    FILE_DATE=$(echo "$line" | grep -oP '\d{4}-\d{2}-\d{2}')
    if [ -n "$FILE_DATE" ] && [ "$FILE_DATE" \< "$CUTOFF" ]; then
      mc rm "mwt-backup/${prefix}/$(echo "$line" | awk '{print $NF}')"
    fi
  done
done
EOF
chmod +x /opt/mwt/backup_cleanup.sh

(crontab -l; echo "0 5 * * * /opt/mwt/backup_cleanup.sh >> /opt/mwt/cleanup.log 2>&1") | crontab -
```

### Paso 16: Restore drill

```bash
# 1. Desencriptar
gpg --decrypt mwt-backup/postgresql/backup_$(date +%Y-%m-%d).sql.gpg > /tmp/restore_test.sql

# 2. Restaurar en DB de test
docker exec -i $(docker ps --filter name=postgres -q) psql -U postgres -c "CREATE DATABASE test_restore;"
docker exec -i $(docker ps --filter name=postgres -q) psql -U postgres -d test_restore < /tmp/restore_test.sql

# 3. Verificar
docker exec $(docker ps --filter name=postgres -q) psql -U postgres -d test_restore -c "SELECT count(*) FROM expedientes_expediente;"

# 4. MinIO objects
mc ls mwt-backup/minio_$(date +%Y-%m-%d)/ | wc -l

# 5. Cleanup test DB
docker exec $(docker ps --filter name=postgres -q) psql -U postgres -c "DROP DATABASE test_restore;"
rm /tmp/restore_test.sql
```

### Paso 17: RPO/RTO

Documentar en ENT_PLAT_SEGURIDAD.C4: RPO 24h, RTO [DECISION_CEO — propuesta 4h].

### Gate Fase 2
- [ ] Script OK (ejecución manual exitosa)
- [ ] Manifest con config_status
- [ ] Cron + crontab exportado
- [ ] Cleanup 30d configurado
- [ ] Push alert test exitoso
- [ ] Restore drill OK
- [ ] RPO/RTO documentado

---

## Fase 3 — Cloudflare + Docker Hardening (2-3h)

**⚠️ CONSOLA ALTERNATIVA ABIERTA DURANTE TODA ESTA FASE**

### Paso 18: Cloudflare

1. Export zona DNS actual del registrador (screenshot + txt)
2. En Cloudflare: crear zona, recrear todos los registros
3. portal.mwt.one = CNAME en zona mwt.one
4. SSL → Full (strict)
5. Cambiar nameservers en registrador
6. **Monitorear los 3 dominios:**
```bash
watch -n 30 'for d in mwt.one ranawalk.com portal.mwt.one; do echo -n "$d: "; curl -so /dev/null -w "%{http_code}" https://$d/; echo; done'
```
7. Si 5xx → L1: fix en CF → L2: DNS-only → L3: rollback NS (hasta 24h)

### Paso 19: Docker non-root

```bash
# Verificar
for c in $(docker ps -q); do
  docker inspect --format '{{.Name}}: {{.Config.User}}' $c
done
# PostgreSQL ya debería ser "postgres"
# Si alguno es root → agregar USER en Dockerfile → rebuild
```

### Paso 20: Resource limits

En docker-compose.yml agregar a cada servicio:
```yaml
# Django
mem_limit: 512m
cpus: 0.5

# PostgreSQL
mem_limit: 1g
cpus: 1

# Redis
mem_limit: 256m
cpus: 0.25

# Celery
mem_limit: 512m
cpus: 0.5

# Nginx
mem_limit: 128m
cpus: 0.25
```

```bash
docker compose up -d

# Verificar MEM
docker stats --no-stream

# Verificar CPU
for c in $(docker ps -q); do
  echo "$(docker inspect --format '{{.Name}}: NanoCpus={{.HostConfig.NanoCpus}}' $c)"
done
# NanoCpus != 0 para todos
```

### Paso 21: Health checks

En docker-compose.yml agregar a cada servicio:
```yaml
# Django
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
  interval: 30s
  timeout: 10s
  retries: 3

# PostgreSQL
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER"]
  interval: 30s
  timeout: 5s
  retries: 3

# Redis (con auth!)
healthcheck:
  test: ["CMD-SHELL", "REDISCLI_AUTH=$$REDIS_PASSWORD redis-cli ping"]
  interval: 30s
  timeout: 5s
  retries: 3

# Nginx
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost/health"]
  interval: 30s
  timeout: 5s
  retries: 3

# Celery
healthcheck:
  test: ["CMD-SHELL", "pgrep -f 'celery worker' || exit 1"]
  interval: 30s
  timeout: 10s
  retries: 3
```

```bash
docker compose up -d
# Esperar ~90s
docker ps  # todos (healthy)
```

### Paso 22: Fail2ban

```bash
sudo apt install -y fail2ban
sudo systemctl enable fail2ban

# Configurar jail SSH
sudo cat > /etc/fail2ban/jail.local << 'EOF'
[sshd]
enabled = true
port = ssh
filter = sshd
maxretry = 5
bantime = 3600
findtime = 600
EOF

sudo systemctl restart fail2ban
sudo fail2ban-client status sshd

# Verificar que TU IP no está baneada
sudo fail2ban-client status sshd | grep "Banned IP"
```

### Gate Fase 3
- [ ] 3 dominios via Cloudflare
- [ ] Sin 5xx sostenido >60s
- [ ] MEM limits: docker stats
- [ ] CPU limits: NanoCpus != 0
- [ ] Health checks healthy
- [ ] Fail2ban activo

---

## Entregable final

Crear `RESUMEN_SPRINT27.md` con:
- Output de cada verificación (copiar los outputs de los comandos)
- Tabla DoD con 13 checks técnicos ✅/❌
- Evidencias: screenshots o logs de cada gate
- Lista de archivos creados/modificados

**Commit final:**
```bash
git add -A
git commit -m "feat(security): S27 security audit + backup DR + Cloudflare + Docker hardening

- ENT_PLAT_SEGURIDAD: 0 [PENDIENTE], A-H verified
- Secrets: truffleHog clean, matrix 12+ entries, rotation policy
- DR: backup_mwt.sh integral (PG+MinIO+config), 30d retention, push alerts
- Cloudflare: 3 domains, Full (strict)
- Docker: non-root, mem_limit+cpus, health checks
- Fail2ban: SSH jail active

Refs: CEO-17 DONE, CEO-19 DONE, LOTE_SM_SPRINT27 v1.6"
git push origin feat/sprint27-security-hardening
```
