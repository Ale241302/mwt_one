#!/usr/bin/env bash
# =============================================================================
# S24 — Backup PostgreSQL automatizado (Sección C.3 REPORTE_SEGURIDAD_S24)
# Crontab sugerido: 0 2 * * * /opt/mwt/scripts/backup_pg.sh >> /var/log/mwt_backup.log 2>&1
# =============================================================================
set -euo pipefail

BACKUP_DIR="/opt/mwt/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
FILE="$BACKUP_DIR/mwt_${DATE}.sql.gz"
RETENTION_DAYS=30

mkdir -p "$BACKUP_DIR"

echo "[$(date -u)] Iniciando backup PostgreSQL..."

docker exec mwt_one_postgres pg_dump -U mwt mwt | gzip > "$FILE" \
  && echo "[$(date -u)] Backup OK: $FILE ($(du -sh $FILE | cut -f1))" \
  || { echo "[$(date -u)] ERROR: backup falló"; exit 1; }

# Rotación: eliminar backups más viejos que RETENTION_DAYS
find "$BACKUP_DIR" -name '*.sql.gz' -mtime +${RETENTION_DAYS} -delete \
  && echo "[$(date -u)] Rotación: eliminados backups > ${RETENTION_DAYS} días"

echo "[$(date -u)] Backup completado."
