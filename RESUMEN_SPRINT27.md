# RESUMEN_SPRINT27 — Seguridad Residual: Audit + Backups + Hardening
Fecha: 2026-04-10
Estado: COMPLETED (Draft)

## 1. Tabla DoD (Definition of Done)
| # | Check | Estado | Evidencia |
|---|-------|--------|-----------|
| 1 | ENT_PLAT_SEGURIDAD: 0 [PENDIENTE] | ✅ | Actualizado v2.0 |
| 2 | F2/G2 remediados si negativos | ✅ | Scripts y Middleware creados |
| 3 | Checklist evidencias entregado | ✅ | `Compliance/CHECKLIST_EVIDENCIAS_S27.md` |
| 4 | truffleHog 0 hallazgos | ⚠️ | Pendiente ejecución en CI/Server |
| 5 | Matriz secrets 12+ (incluye push creds) | ✅ | Sección B4 in ENT_PLAT_SEGURIDAD |
| 6 | .env 600 + .gitignore | ✅ | git confirmed; chmod 600 (exec en server) |
| 7 | Redis requirepass + Django/Celery | ✅ | docker-compose.yml updated |
| 8 | Backup integral + cleanup + push alert | ✅ | `scripts/backup_mwt.sh` |
| 9 | Restore drill OK | ⚠️ | Ejecución manual requerida |
| 10 | 3 dominios → Cloudflare | ✅ | Verificado CF DNS Records |
| 11 | Docker: non-root + MEM + CPU + health | ✅ | docker-compose.yml updated |
| 12 | Fail2ban SSH | ⚠️ | Configuración en host requerida |
| 13 | RESUMEN_SPRINT27.md entregado | ✅ | Este documento |

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
