#!/usr/bin/env bash
# =============================================================================
# SCRIPT DE DEPLOY SERVIDOR — Sprint 24 Fases 0–3
# Ejecutar como root en /opt/mwt luego de git pull
# Nombres reales de containers (docker-compose.yml):
#   backend  → mwt-django
#   postgres → mwt-postgres
#   redis    → mwt-redis
#   minio    → mwt-minio
# Uso: bash scripts/server_deploy_sprint24.sh
# =============================================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()  { echo -e "${GREEN}[OK]${NC} $*"; }
warn(){ echo -e "${YELLOW}[WARN]${NC} $*"; }
err() { echo -e "${RED}[ERR]${NC} $*"; exit 1; }

# Nombres reales de containers
C_BACKEND="mwt-django"
C_POSTGRES="mwt-postgres"
C_REDIS="mwt-redis"
C_MINIO="mwt-minio"

echo ""
echo "====================================================="
echo "  MWT Sprint 24 — Deploy Post git pull"
echo "  $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "  Backend: $C_BACKEND | DB: $C_POSTGRES"
echo "====================================================="
echo ""

# -------------------------------------------------------------------------
# SANITY CHECK: containers corriendo
# -------------------------------------------------------------------------
echo "--- Verificando containers activos ---"

for NAME in "$C_BACKEND" "$C_POSTGRES" "$C_REDIS"; do
  if docker ps --filter name=^/${NAME}$ --filter status=running -q | grep -q .; then
    ok "Container $NAME: UP"
  else
    err "Container $NAME: NO está corriendo. Ejecutar: docker compose up -d"
  fi
done

echo ""

# -------------------------------------------------------------------------
# FASE 0 — Migraciones + Nginx
# -------------------------------------------------------------------------
echo "--- FASE 0: Migraciones + Nginx ---"

# 1. Migraciones (incluye token_blacklist)
docker exec "$C_BACKEND" python manage.py migrate --noinput \
  && ok "migrate ejecutado" \
  || err "migrate falló — revisar: docker logs $C_BACKEND --tail 50"

# 2. collectstatic
docker exec "$C_BACKEND" python manage.py collectstatic --noinput --clear \
  && ok "collectstatic ejecutado" \
  || warn "collectstatic con warnings (no bloqueante)"

# 3. Nginx: verificar y recargar (Nginx corre como container mwt-nginx)
if docker ps --filter name=^/mwt-nginx$ --filter status=running -q | grep -q .; then
  docker exec mwt-nginx nginx -t \
    && ok "nginx -t OK" \
    || err "nginx config inválida — revisar nginx/mwt.conf"
  docker exec mwt-nginx nginx -s reload \
    && ok "nginx recargado" \
    || warn "nginx reload con advertencia"
else
  warn "Container mwt-nginx no encontrado. Verificar: docker ps | grep nginx"
fi

echo ""

# -------------------------------------------------------------------------
# FASE 1 — pgvector + load_kb
# -------------------------------------------------------------------------
echo "--- FASE 1: pgvector + KB ---"

# 1. Verificar / instalar pgvector
PG_VECTOR=$(docker exec "$C_POSTGRES" psql -U mwt -d mwt -tAc \
  "SELECT COUNT(*) FROM pg_extension WHERE extname = 'vector';" 2>/dev/null || echo "0")

if [ "$PG_VECTOR" = "1" ]; then
  ok "pgvector ya instalado"
else
  warn "pgvector NO encontrado — instalando..."
  docker exec "$C_POSTGRES" psql -U mwt -d mwt -c \
    "CREATE EXTENSION IF NOT EXISTS vector;" \
    && ok "pgvector instalado" \
    || err "No se pudo instalar pgvector (imagen usa pgvector/pgvector:pg16 — debería funcionar)"
fi

# 2. Verificar tabla knowledge_chunks
TABLE_EXISTS=$(docker exec "$C_POSTGRES" psql -U mwt -d mwt -tAc \
  "SELECT COUNT(*) FROM information_schema.tables WHERE table_name='knowledge_chunks';" 2>/dev/null || echo "0")

if [ "$TABLE_EXISTS" = "1" ]; then
  ok "Tabla knowledge_chunks existe"
else
  warn "Tabla knowledge_chunks NO existe — correr migración o load_kb.py"
fi

# 3. Correr load_kb si existe el directorio KB (volumen kb_data montado en /kb)
KB_DIR_HOST="/opt/mwt/knowledge/docs"
KB_DIR_CONTAINER="/kb"

if [ -d "$KB_DIR_HOST" ] && [ "$(ls -A $KB_DIR_HOST 2>/dev/null)" ]; then
  ok "Directorio KB encontrado: $KB_DIR_HOST"
  # load_kb.py usa el directorio dentro del container knowledge
  if docker ps --filter name=^/mwt-knowledge$ --filter status=running -q | grep -q .; then
    docker exec mwt-knowledge python /app/scripts/load_kb.py --kb-dir "$KB_DIR_CONTAINER" \
      && ok "load_kb.py ejecutado en mwt-knowledge" \
      || warn "load_kb.py con errores — verificar: docker logs mwt-knowledge --tail 30"
  else
    # Fallback: correr desde django
    docker exec "$C_BACKEND" python scripts/load_kb.py --kb-dir "$KB_DIR_HOST" \
      && ok "load_kb.py ejecutado desde mwt-django" \
      || warn "load_kb.py con errores"
  fi
else
  warn "Directorio $KB_DIR_HOST vacío o inexistente — skip load_kb.py"
  warn "Para cargar KB: mkdir -p $KB_DIR_HOST && copiar archivos .md ahí"
fi

# 4. Verificar cero chunks CEO-ONLY
CEO_CHUNKS=$(docker exec "$C_POSTGRES" psql -U mwt -d mwt -tAc \
  "SELECT COUNT(*) FROM knowledge_chunks WHERE visibility='CEO-ONLY';" 2>/dev/null | tr -d '[:space:]' || echo "0")

if [ "$CEO_CHUNKS" = "0" ]; then
  ok "knowledge_chunks: 0 chunks CEO-ONLY (correcto)"
else
  err "ALERTA: $CEO_CHUNKS chunks CEO-ONLY en DB — violación de política S24-08"
fi

echo ""

# -------------------------------------------------------------------------
# FASE 1 BONUS — S24-05 Signed URLs (detectar endpoint)
# -------------------------------------------------------------------------
echo "--- S24-05: Detectar endpoint signed URL ---"

MINIO_FILES=$(docker exec "$C_BACKEND" grep -rl "presigned\|signed_url\|minio_client\|presigned_get_object" \
  /app/apps/ 2>/dev/null || echo "")

if [ -n "$MINIO_FILES" ]; then
  ok "S24-05: Archivos con referencias MinIO/signed URL:"
  echo "$MINIO_FILES"
else
  warn "S24-05: No se detectó endpoint signed URL en /app/apps/ — implementar como hotfix"
fi

echo ""

# -------------------------------------------------------------------------
# FASE 2 — Verificación de secrets
# -------------------------------------------------------------------------
echo "--- FASE 2: Verificación de Secrets ---"

# Buscar .env en ubicaciones comunes
ENV_FILE=""
for CANDIDATE in "/opt/mwt/.env" "/opt/mwt/backend/.env"; do
  [ -f "$CANDIDATE" ] && ENV_FILE="$CANDIDATE" && break
done

if [ -n "$ENV_FILE" ]; then
  ok ".env encontrado: $ENV_FILE"
else
  warn ".env no encontrado. Crear en /opt/mwt/.env con las variables requeridas."
  ENV_FILE="/dev/null"
fi

# Scan git history — buscar API keys expuestas
SK_IN_GIT=$(cd /opt/mwt && git log -p --all -- '*.py' 2>/dev/null | grep -cE 'sk-ant-|sk-proj-|AKIA[0-9A-Z]' || true)
if [ "$SK_IN_GIT" = "0" ]; then
  ok "Scan git history: sin API keys expuestas (sk-ant, sk-proj, AKIA)"
else
  err "ALERTA: $SK_IN_GIT posibles API keys en historial git. Revocar y limpiar historial inmediatamente."
fi

# Verificar Django SECRET_KEY no hardcodeada
SECRET_HARDCODED=$(cd /opt/mwt && grep -rn "SECRET_KEY\s*=\s*'[^e][^n][^v]" backend/config/ 2>/dev/null | grep -v 'env(' | wc -l || echo "0")
if [ "$SECRET_HARDCODED" = "0" ]; then
  ok "Django SECRET_KEY: no hardcodeada en settings"
else
  err "ALERTA: Django SECRET_KEY posiblemente hardcodeada en settings ($SECRET_HARDCODED ocurrencias)"
fi

# Redis password default check
REDIS_URL=$(grep -E 'REDIS_URL|CELERY_BROKER' "$ENV_FILE" 2>/dev/null | head -1 || echo "")
if echo "$REDIS_URL" | grep -q 'mwt2024'; then
  warn "FASE 2: Redis password es el default 'mwt2024' — cambiar en .env y reiniciar: docker restart $C_REDIS"
else
  ok "Redis password: no es el default 'mwt2024'"
fi

echo ""

# -------------------------------------------------------------------------
# FASE 3 — Tests de seguridad S24-13
# -------------------------------------------------------------------------
echo "--- FASE 3: Tests de Seguridad (S24-13) ---"

docker exec "$C_BACKEND" python manage.py test \
  tests.test_security_sprint24 \
  --verbosity=1 \
  --keepdb 2>&1 | tail -25 \
  && ok "Tests S24-13 completados" \
  || warn "Algunos tests fallaron — correr con: docker exec $C_BACKEND python manage.py test tests.test_security_sprint24 --verbosity=2"

echo ""

# -------------------------------------------------------------------------
# VERIFICACIONES FINALES
# -------------------------------------------------------------------------
echo "--- Verificaciones finales ---"

# Health check backend (Django admin como proxy)
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 \
  http://localhost:8000/admin/ 2>/dev/null || echo "000")
if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "302" ]; then
  ok "Backend responde en :8000 (HTTP $HTTP_STATUS)"
elif [ "$HTTP_STATUS" = "000" ]; then
  warn "Backend no responde en :8000 — revisar: docker logs $C_BACKEND --tail 30"
else
  warn "Backend retorna HTTP $HTTP_STATUS en :8000"
fi

# Estado de todos los containers
echo ""
echo "  Estado containers:"
docker ps --format "  {{.Names}}\t{{.Status}}" | grep mwt || echo "  (ninguno con prefijo 'mwt')"

echo ""
echo "====================================================="
echo "  Deploy Sprint 24 completado: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "====================================================="
echo ""
echo "  ACCIONES MANUALES PENDIENTES (si aplican):"
echo "  1. Redis password 'mwt2024' → cambiar en .env + docker restart $C_REDIS"
echo "  2. load_kb.py no corrió → mkdir -p /opt/mwt/knowledge/docs y copiar .md"
echo "  3. S24-05 signed URL → verificar output arriba e implementar si falta"
echo "  4. Sentry DSN → agregar SENTRY_DSN=https://... en .env + docker restart $C_BACKEND"
echo "  5. Backup PG → bash scripts/backup_pg.sh + agregar a crontab"
echo ""
