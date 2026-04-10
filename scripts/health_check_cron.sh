#!/bin/bash
# health_check_cron.sh — Monitoreo mínimo in-sprint (S27-07d2)

# URL a monitorear
URL="https://mwt.one/admin/" # Usamos admin como proxy de salud básica
LOG_FILE="/opt/mwt/health_alerts.log"
# NTFY_TOPIC="mwt-health-alerts"

status_code=$(curl -s -o /dev/null -w "%{http_code}" "$URL")

if [ "$status_code" -ne 200 ]; then
    msg="ALERT: MWT.ONE health check failed with status $status_code at $(date)"
    echo "$msg" >> "$LOG_FILE"
    
    # Push alert (ntfy)
    # curl -d "$msg" "https://ntfy.sh/$NTFY_TOPIC" 2>/dev/null || true
    
    # Push alert (generic webhook if configured)
    # if [ ! -z "$PUSH_WEBHOOK_URL" ]; then
    #    curl -X POST -H "Content-Type: application/json" -d "{\"text\":\"$msg\"}" "$PUSH_WEBHOOK_URL"
    # fi
fi
