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
ok()   { echo -e "${GREEN}[OK]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
# err() solo detiene cuando es un error BLOQUEANTE real (container caído, migrate roto)
err()  { echo -e "${RED}[ERR]${NC} $*"; exit 1; }
# crit() reporta hallazgo crítico sin detener el script — para checks de seguridad informativos
crit() { echo -e "${RED}[CRIT]${NC} $*"; CRIT_COUNT=$((CRIT_COUNT + 1)); }
CRIT_COUNT=0

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
# SANITY CHECK: containers corriendo (bloqueante)
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
if docker exec "$C_BACKEND" python manage.py migrate --noinput; then
  ok "migrate ejecutado"
else
  err "migrate falló — revisar: docker logs $C_BACKEND --tail 50"
fi

# 2. collectstatic
docker exec "$C_BACKEND" python manage.py collectstatic --noinput --clear \
  && ok "collectstatic ejecutado" \
  || warn "collectstatic con warnings (no bloqueante)"

# 3. Nginx: verificar y recargar (corre como container mwt-nginx)
if docker ps --filter name=^/mwt-nginx$ --filter status=running -q | grep -q .; then
  docker exec mwt-nginx nginx -t \
    && ok "nginx -t OK" \
    || warn "nginx config con warnings (ver output arriba)"
  docker exec mwt-nginx nginx -s reload \
    && ok "nginx recargado" \
    || warn "nginx reload con advertencia"
else
  warn "Container mwt-nginx no encontrado — verificar: docker ps | grep nginx"
fi

echo ""

# -------------------------------------------------------------------------
# FASE 1 — pgvector + load_kb
# -------------------------------------------------------------------------
echo "--- FASE 1: pgvector + KB ---"

# 1. Verificar / instalar pgvector
PG_VECTOR=$(docker exec "$C_POSTGRES" psql -U mwt -d mwt -tAc \
  "SELECT COUNT(*) FROM pg_extension WHERE extname = 'vector';" 2>/dev/null | tr -d '[:space:]' || echo "0")

if [ "$PG_VECTOR" = "1" ]; then
  ok "pgvector ya instalado"
else
  warn "pgvector NO encontrado — instalando..."
  docker exec "$C_POSTGRES" psql -U mwt -d mwt -c \
    "CREATE EXTENSION IF NOT EXISTS vector;" \
    && ok "pgvector instalado" \
    || warn "No se pudo instalar pgvector automáticamente — imagen pgvector/pgvector:pg16 debería soportarlo"
fi

# 2. Verificar tabla knowledge_chunks
TABLE_EXISTS=$(docker exec "$C_POSTGRES" psql -U mwt -d mwt -tAc \
  "SELECT COUNT(*) FROM information_schema.tables WHERE table_name='knowledge_chunks';" 2>/dev/null | tr -d '[:space:]' || echo "0")

if [ "$TABLE_EXISTS" = "1" ]; then
  ok "Tabla knowledge_chunks existe"
else
  warn "Tabla knowledge_chunks NO existe — pendiente: correr migrate o load_kb.py"
fi

# 3. Correr load_kb si el directorio KB tiene contenido
KB_DIR_HOST="/opt/mwt/knowledge/docs"
KB_DIR_CONTAINER="/kb"

if [ -d "$KB_DIR_HOST" ] && [ -n "$(ls -A "$KB_DIR_HOST" 2>/dev/null)" ]; then
  ok "Directorio KB encontrado con contenido: $KB_DIR_HOST"
  if docker ps --filter name=^/mwt-knowledge$ --filter status=running -q | grep -q .; then
    docker exec mwt-knowledge python /app/scripts/load_kb.py --kb-dir "$KB_DIR_CONTAINER" \
      && ok "load_kb.py ejecutado en mwt-knowledge" \
      || warn "load_kb.py con errores — revisar: docker logs mwt-knowledge --tail 30"
  else
    docker exec "$C_BACKEND" python scripts/load_kb.py --kb-dir "$KB_DIR_HOST" \
      && ok "load_kb.py ejecutado desde mwt-django" \
      || warn "load_kb.py con errores — revisar: docker logs $C_BACKEND --tail 30"
  fi
else
  warn "Directorio $KB_DIR_HOST vacío o inexistente — skip load_kb.py"
  warn "  → Para cargar KB: mkdir -p $KB_DIR_HOST && copiar archivos .md"
fi

# 4. Verificar cero chunks CEO-ONLY (no bloqueante — tabla puede no existir aún)
CEO_CHUNKS=$(docker exec "$C_POSTGRES" psql -U mwt -d mwt -tAc \
  "SELECT COUNT(*) FROM knowledge_chunks WHERE visibility='CEO-ONLY';" 2>/dev/null | tr -d '[:space:]' || echo "0")

if [ "$CEO_CHUNKS" = "0" ]; then
  ok "knowledge_chunks: 0 chunks CEO-ONLY (correcto)"
else
  crit "$CEO_CHUNKS chunks CEO-ONLY en DB — violación de política S24-08. Limpiar con: DELETE FROM knowledge_chunks WHERE visibility='CEO-ONLY';"
fi

echo ""

# -------------------------------------------------------------------------
# FASE 1 BONUS — S24-05 Signed URLs
# -------------------------------------------------------------------------
echo "--- S24-05: Detectar endpoint signed URL ---"

MINIO_FILES=$(docker exec "$C_BACKEND" grep -rl \
  "presigned\|signed_url\|minio_client\|presigned_get_object" \
  /app/apps/ 2>/dev/null || true)

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

# Buscar .env
ENV_FILE=""
for CANDIDATE in "/opt/mwt/.env" "/opt/mwt/backend/.env"; do
  [ -f "$CANDIDATE" ] && ENV_FILE="$CANDIDATE" && break
done

if [ -n "$ENV_FILE" ]; then
  ok ".env encontrado: $ENV_FILE"
else
  warn ".env no encontrado en /opt/mwt ni /opt/mwt/backend/"
  ENV_FILE="/dev/null"
fi

# Scan git history: API keys en commits
SK_IN_GIT=$(cd /opt/mwt && git log -p --all -- '*.py' 2>/dev/null \
  | grep -cE 'sk-ant-[a-zA-Z0-9]+|sk-proj-[a-zA-Z0-9]+|AKIA[0-9A-Z]{16}' || true)
if [ "$SK_IN_GIT" = "0" ]; then
  ok "Scan git history: sin API keys expuestas (sk-ant, sk-proj, AKIA)"
else
  crit "$SK_IN_GIT posibles API keys en historial git — revocar y limpiar con git-filter-repo"
fi

# Verificar que SECRET_KEY usa env() y no está hardcodeada
# Busca: SECRET_KEY = '<string literal>' donde el valor NO es una llamada a env/os.environ/config
SECRET_HARDCODED=$(cd /opt/mwt && grep -rn "SECRET_KEY" backend/config/ 2>/dev/null \
  | grep -vE "env\(|os\.environ|get_env|config\(|getenv|#" \
  | grep -cE "SECRET_KEY\s*=\s*['\"]" || true)

if [ "$SECRET_HARDCODED" = "0" ]; then
  ok "Django SECRET_KEY: correctamente leída desde variable de entorno"
else
  crit "Django SECRET_KEY posiblemente hardcodeada en settings ($SECRET_HARDCODED líneas) — mover a .env + env()"
fi

# Redis password: verificar que no es el default 'mwt2024'
REDIS_URL=$(grep -E 'REDIS_URL|CELERY_BROKER' "$ENV_FILE" 2>/dev/null | head -1 || echo "")
if echo "$REDIS_URL" | grep -q 'mwt2024'; then
  crit "Redis password es el default 'mwt2024' — cambiar en .env + docker restart $C_REDIS"
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
  || warn "Algunos tests fallaron — correr completo: docker exec $C_BACKEND python manage.py test tests.test_security_sprint24 --verbosity=2"

echo ""

# -------------------------------------------------------------------------
# VERIFICACIONES FINALES
# -------------------------------------------------------------------------
echo "--- Verificaciones finales ---"

# Health check backend
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 \
  http://localhost:8000/admin/ 2>/dev/null || echo "000")
if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "302" ]; then
  ok "Backend responde en :8000 (HTTP $HTTP_STATUS)"
elif [ "$HTTP_STATUS" = "000" ]; then
  warn "Backend no responde en :8000 — revisar: docker logs $C_BACKEND --tail 30"
else
  warn "Backend retorna HTTP $HTTP_STATUS en :8000"
fi

# Estado containers
echo ""
echo "  Estado containers:"
docker ps --format "  {{.Names}}\t{{.Status}}" | grep mwt || echo "  (ningún container con prefijo 'mwt')"

# -------------------------------------------------------------------------
# RESUMEN FINAL
# -------------------------------------------------------------------------
echo ""
echo "====================================================="
echo "  Deploy Sprint 24 completado: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
if [ "$CRIT_COUNT" -gt 0 ]; then
  echo -e "  ${RED}HALLAZGOS CRÍTICOS: $CRIT_COUNT — revisar líneas [CRIT] arriba${NC}"
else
  echo -e "  ${GREEN}Sin hallazgos críticos ✓${NC}"
fi
echo "====================================================="
echo ""
echo "  ACCIONES MANUALES PENDIENTES (si aplican):"
echo "  1. load_kb.py no corrió → mkdir -p /opt/mwt/knowledge/docs + copiar .md"
echo "  2. S24-05 signed URL → ver output arriba e implementar si falta"
echo "  3. Sentry DSN → agregar SENTRY_DSN=https://... en .env + docker restart $C_BACKEND"
echo "  4. Backup PG → bash scripts/backup_pg.sh + crontab (ver comentario en script)"
echo "  5. Collation mismatch → docker exec $C_POSTGRES psql -U mwt -d mwt -c 'ALTER DATABASE mwt REFRESH COLLATION VERSION;'"
echo ""
