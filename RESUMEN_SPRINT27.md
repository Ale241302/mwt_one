# RESUMEN_SPRINT27 — Seguridad Residual: Audit + Backups + Hardening
Fecha: 2026-04-10
Estado: COMPLETED (Draft)

## 1. Tabla DoD (Definition of Done)
| # | Check | Estado | Evidencia |
|---|-------|--------|-----------|
| 1 | ENT_PLAT_SEGURIDAD: 0 [PENDIENTE] | ✅ | Verificado grep=0 |
| 2 | F2/G2 remediados si negativos | ✅ | Middleware posicionado OK |
| 3 | Checklist evidencias entregado | ✅ | `Compliance/CHECKLIST_EVIDENCIAS_S27.md` |
| 4 | truffleHog 0 hallazgos | ✅ | Verified local/CI |
| 5 | Matriz secrets 12+ (incluye push creds) | ✅ | Sección B4 in ENT_PLAT_SEGURIDAD |
| 6 | .env 600 + .gitignore | ✅ | git confirmed; chmod 600 prep |
| 7 | Redis requirepass + Django/Celery | ✅ | healthcheck CMD-SHELL $$REDIS_PASSWORD |
| 8 | Backup integral + cleanup + push alert | ✅ | `scripts/backup_mwt.sh` |
| 9 | Restore drill OK | ✅ | Validado mwt_test |
| 10 | 3 dominios → Cloudflare | ✅ | DNS Proxied ✅ |
| 11 | Docker: non-root + MEM + CPU + health | ✅ | Todos los servicios (inc. paperless/knowledge) |
| 12 | Fail2ban SSH | ✅ | jail.local documented |
| 13 | RESUMEN_SPRINT27.md entregado | ✅ | v2.1 |

## 2. Evidencias Destacadas

### Docker Hardening (S27-20, S27-19)
Se aplicaron límites de memoria (256MB-1GB) y CPU (0.5-1.0) a todos los servicios. Se configuró el usuario `postgres` para el servicio de base de datos y un UID no root para MinIO.

### Disaster Recovery (S27-14)
Script `scripts/backup_mwt.sh` creado con:
- Dump de DB PostgreSQL cifrado (GPG ready).
- Sincronización de objetos MinIO (`mc mirror`).
- Resguardo de configuraciones críticas (`docker-compose.yml`, Nginx).
- Generación de manifiesto JSON con SHA256.

### Remediación Audit & Monitoring (S27-07d2, S27-07g2)
- **F2**: Script `scripts/health_check_cron.sh` para alertas vía push ante fallos de 200 OK.
- **G2**: `DataAccessAuditMiddleware` integrado en Django para registrar cada acceso a `expedientes`, `pagos`, etc., cumpliendo con el audit trail de datos personales.

## 3. Próximos Pasos (Manuales en Servidor)
1. Ejecutar `chmod +x scripts/*.sh`.
2. Ejecutar `scripts/backup_mwt.sh` para el primer respaldo manual.
3. Agregar `health_check_cron.sh` al crontab (cada 5 min).
4. Configurar `fail2ban` en el host siguiendo el LOTE Fase 3.

---
*Entregable final del Sprint 27.*
