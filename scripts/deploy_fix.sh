#!/bin/bash
# deploy_fix.sh — Aplica el fix Count('expediente_id') sin bajar toda la infraestructura
# Uso: bash scripts/deploy_fix.sh

set -e

echo "===== [1/4] Git pull ====="
git pull origin main

echo "===== [2/4] Rebuild imagen django ====="
docker compose build django

echo "===== [3/4] Recrear contenedor django (sin tocar postgres/redis/nginx) ====="
docker compose up -d --no-deps --force-recreate django

echo "===== [4/4] Esperando 20s que gunicorn arranque... ====="
sleep 20

echo "--- Estado del contenedor ---"
docker ps | grep mwt-django

echo "--- Ultimos logs de django ---"
docker logs mwt-django --tail=30

echo ""
echo "✅ Deploy completado. Si no ves FieldError arriba, el fix esta aplicado."
