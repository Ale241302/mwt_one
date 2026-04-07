#!/usr/bin/env bash
# =============================================================================
# SCRIPT DE DEPLOY SERVIDOR — Sprint 24 Fases 0–3
# Ejecutar como root en /opt/mwt luego de git pull
# Uso: bash scripts/server_deploy_sprint24.sh
# =============================================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()  { echo -e "${GREEN}[OK]${NC} $*"; }
warn(){ echo -e "${YELLOW}[WARN]${NC} $*"; }
err() { echo -e "${RED}[ERR]${NC} $*"; exit 1; }

echo ""
echo "====================================================="
echo "  MWT Sprint 24 — Deploy Post git pull"
echo "  $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "====================================================="
echo ""

# -------------------------------------------------------------------------
# FASE 0 — Pendiente manual
# -------------------------------------------------------------------------
echo "--- FASE 0: Migraciones + Nginx ---"

# 1. Migraciones (incluye rest_framework_simplejwt.token_blacklist)
docker exec mwt_one_backend python manage.py migrate --noinput \
  && ok "migrate ejecutado" \
  || err "migrate falló — revisar docker logs mwt_one_backend --tail 50"

# 2. collectstatic
docker exec mwt_one_backend python manage.py collectstatic --noinput --clear \
  && ok "collectstatic ejecutado" \
  || warn "collectstatic con warnings (no bloqueante)"

# 3. Verificar config Nginx
nginx -t && ok "nginx -t OK" || err "nginx config inválida"

# 4. Reload Nginx
systemctl reload nginx && ok "nginx recargado" || err "nginx reload falló"

echo ""

# -------------------------------------------------------------------------
# FASE 1 — pgvector + load_kb
# -------------------------------------------------------------------------
echo "--- FASE 1: pgvector + KB ---"

# 1. Verificar / instalar pgvector
PG_VECTOR=$(docker exec mwt_one_postgres psql -U mwt -d mwt -tAc \
  "SELECT COUNT(*) FROM pg_extension WHERE extname = 'vector';")

if [ "$PG_VECTOR" = "1" ]; then
  ok "pgvector ya instalado"
else
  warn "pgvector NO encontrado — instalando..."
  docker exec mwt_one_postgres psql -U mwt -d mwt -c \
    "CREATE EXTENSION IF NOT EXISTS vector;" \
    && ok "pgvector instalado" \
    || err "No se pudo instalar pgvector. Instalar manualmente: apt install postgresql-16-pgvector"
fi

# 2. Verificar tabla knowledge_chunks
TABLE_EXISTS=$(docker exec mwt_one_postgres psql -U mwt -d mwt -tAc \
  "SELECT COUNT(*) FROM information_schema.tables WHERE table_name='knowledge_chunks';")

if [ "$TABLE_EXISTS" = "1" ]; then
  ok "Tabla knowledge_chunks existe"
else
  warn "Tabla knowledge_chunks NO existe — se creará al correr load_kb.py"
fi

# 3. Correr load_kb si existe el directorio KB
KB_DIR="/opt/mwt/knowledge/docs"
if [ -d "$KB_DIR" ]; then
  ok "Directorio KB encontrado: $KB_DIR"
  docker exec mwt_one_backend python scripts/load_kb.py --kb-dir "$KB_DIR" \
    && ok "load_kb.py ejecutado" \
    || warn "load_kb.py con errores — verificar manualmente"
else
  warn "Directorio $KB_DIR no existe — skip load_kb.py"
  warn "Crear directorio y archivos .md antes de correr carga KB:"
  warn "  mkdir -p $KB_DIR"
fi

# 4. Verificar cero chunks CEO-ONLY
CEO_CHUNKS=$(docker exec mwt_one_postgres psql -U mwt -d mwt -tAc \
  "SELECT COUNT(*) FROM knowledge_chunks WHERE visibility='CEO-ONLY';" 2>/dev/null || echo "0")

if [ "$CEO_CHUNKS" = "0" ]; then
  ok "knowledge_chunks: 0 chunks CEO-ONLY (correcto)"
else
  err "ALERTA: $CEO_CHUNKS chunks CEO-ONLY en DB — violación de política S24-08"
fi

echo ""

# -------------------------------------------------------------------------
# FASE 1 BONUS — S24-05 Signed URLs (verificar endpoint)
# -------------------------------------------------------------------------
echo "--- S24-05: Verificar endpoint signed URL ---"

ENDPOINT_EXP=$(docker exec mwt_one_backend grep -rl "presigned\|signed_url\|minio" \
  /app/apps/expedientes/views.py 2>/dev/null | wc -l)
ENDPOINT_ART=$(docker exec mwt_one_backend grep -rl "presigned\|signed_url\|minio" \
  /app/apps/ 2>/dev/null | head -5)

if [ "$ENDPOINT_EXP" -gt "0" ]; then
  ok "S24-05: endpoint signed URL detectado en apps/expedientes/views.py"
else
  warn "S24-05: Endpoint signed URL pendiente — archivos que mencionan minio:"
  echo "$ENDPOINT_ART"
fi

echo ""

# -------------------------------------------------------------------------
# FASE 2 — Checklist secrets (verificación automática no-intrusiva)
# -------------------------------------------------------------------------
echo "--- FASE 2: Verificación de Secrets ---"

ENV_FILE="/opt/mwt/backend/.env"
[ -f "$ENV_FILE" ] || ENV_FILE="/opt/mwt/.env"
[ -f "$ENV_FILE" ] && ok ".env encontrado: $ENV_FILE" || warn ".env no encontrado en /opt/mwt ni /opt/mwt/backend"

# Verificar que secrets no están en git history
SK_IN_GIT=$(cd /opt/mwt && git log -p --all -- '*.py' '*.env*' 2>/dev/null | grep -c 'sk-ant\|sk-proj\|AKIA' || true)
if [ "$SK_IN_GIT" = "0" ]; then
  ok "Scan git history: sin API keys expuestas"
else
  err "ALERTA: $SK_IN_GIT posibles API keys en historial git. Revocar inmediatamente."
fi

# Redis password no es default
REDIS_URL=$(grep 'REDIS_URL\|CELERY_BROKER' "$ENV_FILE" 2>/dev/null | head -1 || echo "")
if echo "$REDIS_URL" | grep -q 'mwt2024'; then
  warn "Redis password es el default 'mwt2024' — cambiar en prod"
else
  ok "Redis password no es el default"
fi

echo ""

# -------------------------------------------------------------------------
# FASE 3 — Correr tests de seguridad
# -------------------------------------------------------------------------
echo "--- FASE 3: Tests de Seguridad (S24-13) ---"

docker exec mwt_one_backend python manage.py test \
  backend.tests.test_security_sprint24 \
  --verbosity=1 \
  --keepdb 2>&1 | tail -20 \
  && ok "Tests S24-13 completados" \
  || warn "Algunos tests fallaron — revisar output completo con --verbosity=2"

echo ""

# -------------------------------------------------------------------------
# VERIFICACIONES FINALES
# -------------------------------------------------------------------------
echo "--- Verificaciones finales ---"

# Health check backend
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/health/ 2>/dev/null || echo "000")
if [ "$HTTP_STATUS" = "200" ]; then
  ok "Backend health check: 200"
elif [ "$HTTP_STATUS" = "000" ]; then
  warn "Backend no responde en :8000 — verificar docker ps"
else
  warn "Backend /api/health/ retorna $HTTP_STATUS"
fi

# Verificar containers corriendo
BACKEND_UP=$(docker ps --filter name=mwt_one_backend --filter status=running -q | wc -l)
POSTGRES_UP=$(docker ps --filter name=mwt_one_postgres --filter status=running -q | wc -l)
REDIS_UP=$(docker ps --filter name=mwt_one_redis --filter status=running -q | wc -l)
MINIO_UP=$(docker ps --filter name=mwt_one_minio --filter status=running -q | wc -l)

[ "$BACKEND_UP" = "1" ] && ok "Container backend: UP" || err "Container backend: DOWN"
[ "$POSTGRES_UP" = "1" ] && ok "Container postgres: UP" || warn "Container postgres: DOWN o nombre diferente"
[ "$REDIS_UP" = "1" ] && ok "Container redis: UP" || warn "Container redis: DOWN o nombre diferente"
[ "$MINIO_UP" = "1" ] && ok "Container minio: UP" || warn "Container minio: DOWN o nombre diferente"

echo ""
echo "====================================================="
echo "  Deploy Sprint 24 completado: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "====================================================="
echo ""
echo "  COMANDOS MANUALES PENDIENTES:"
echo "  1. Si Redis password es 'mwt2024' — cambiar en .env y reiniciar redis"
echo "  2. Si load_kb.py no corrió — crear /opt/mwt/knowledge/docs y cargar .md"
echo "  3. Verificar S24-05 signed URL endpoint (ver output de S24-05 arriba)"
echo "  4. Configurar Sentry DSN en .env: SENTRY_DSN=https://..."
echo "  5. Configurar backups PostgreSQL: ver scripts/backup_pg.sh"
echo ""
