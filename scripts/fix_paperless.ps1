# fix_paperless.ps1 - Crea la base de datos 'paperless' en postgres y reinicia el contenedor
# Uso: .\scripts\fix_paperless.ps1

Write-Host "===== [1/4] Bajando cambios del repo =====" -ForegroundColor Cyan
git pull origin main

Write-Host "===== [2/4] Creando base de datos 'paperless' en mwt-postgres =====" -ForegroundColor Cyan
# Crea la DB solo si no existe (el || true evita error si ya existe)
docker exec mwt-postgres psql -U mwt -d mwt -c "CREATE DATABASE paperless;"

Write-Host "===== [3/4] Reiniciando mwt-paperless =====" -ForegroundColor Cyan
docker compose up -d --no-deps --force-recreate paperless-ngx

Write-Host "===== [4/4] Esperando 30s que Paperless inicialice y aplique migraciones... =====" -ForegroundColor Cyan
Start-Sleep -Seconds 30

Write-Host "--- Estado de paperless ---" -ForegroundColor Yellow
docker ps | Select-String "paperless"

Write-Host "--- Logs de paperless (ultimas 40 lineas) ---" -ForegroundColor Yellow
docker logs mwt-paperless --tail=40

Write-Host ""
Write-Host "Si ves 'Paperless is ready' en los logs, el fix esta aplicado." -ForegroundColor Green
