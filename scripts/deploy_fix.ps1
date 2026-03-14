# deploy_fix.ps1 - Aplica el fix sin bajar toda la infraestructura
# Uso: .\scripts\deploy_fix.ps1

Write-Host "===== [1/4] Git pull =====" -ForegroundColor Cyan
git pull origin main

Write-Host "===== [2/4] Rebuild imagen django =====" -ForegroundColor Cyan
docker compose build django

Write-Host "===== [3/4] Recrear contenedor django =====" -ForegroundColor Cyan
docker compose up -d --no-deps --force-recreate django

Write-Host "===== [4/4] Esperando 20s que gunicorn arranque... =====" -ForegroundColor Cyan
Start-Sleep -Seconds 20

Write-Host "--- Estado del contenedor ---" -ForegroundColor Yellow
docker ps | Select-String "mwt-django"

Write-Host "--- Ultimos logs de django ---" -ForegroundColor Yellow
docker logs mwt-django --tail=30

Write-Host ""
Write-Host "Deploy completado. Si no ves FieldError arriba, el fix esta aplicado." -ForegroundColor Green
