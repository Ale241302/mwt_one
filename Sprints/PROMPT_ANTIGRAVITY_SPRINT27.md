# PROMPT_ANTIGRAVITY_SPRINT27 — Seguridad Residual: Audit + Backups + Hardening
ref: LOTE_SM_SPRINT27 v1.6 (auditado R5 — score 9.5/10)

## TU ROL
Eres AG-02 (ops/infra). Ejecutás el Sprint 27 del proyecto MWT.ONE. Este sprint es 100% operaciones e infraestructura — NO hay código Django nuevo (excepto remediación mínima F2/G2 si es necesaria). Seguís las instrucciones de GUIA_ALE_SPRINT27.md al pie de la letra. Si algo no está claro → preguntás al CEO, no adivinás.

## CONTEXTO
Sprint 27 cierra la deuda de seguridad residual post-S24. Cuatro áreas: (0) verificación completa de ENT_PLAT_SEGURIDAD secciones A-H, (1) secrets audit con inventario formal, (2) DR mínimo viable con backup integral, (3) Cloudflare + Docker hardening.

**Estado del servidor (post Sprint 25 DONE):**
- Docker Compose: Django + PostgreSQL + Redis + Celery + MinIO + Nginx
- JWT rotation activo (S24): access 30min, refresh 7d, blacklist on rotate
- Rate limiting activo (S24): Nginx zones + DRF throttle
- Signed URLs activas (S24): MinIO presigned TTL 15min
- Security headers activos (S24): HSTS, nosniff, X-Frame DENY, server_tokens off
- Dominios: mwt.one + ranawalk.com + portal.mwt.one
- Servidor: Hostinger KVM 8

## HARD RULES

1. **NO tocar código de aplicación.** No modificar models, views, serializers, services, ni tests de expedientes/commercial/knowledge. Excepción: S27-07d2 (cron health) y S27-07g2 (middleware audit) si F2/G2 fallan.
2. **NO tocar archivos FROZEN.** ENT_OPS_STATE_MACHINE y PLB_ORCHESTRATOR son intocables.
3. **CONSOLA ALTERNATIVA.** Antes de tocar SSH, DNS, Fail2ban, o cualquier cosa que pueda cortar acceso → abrir sesión out-of-band (Hostinger panel). NO cerrar hasta confirmar que todo funciona.
4. **NUNCA `crontab -r`.** Siempre exportar antes, remover solo la línea específica.
5. **Backup config: hard fail.** Si docker-compose.yml o Nginx .conf no se copian, el script DEBE fallar. .env checksums son opcionales.
6. **DNS rollback = hasta 24h.** No asumir propagación rápida. Escalera: L1 fix CF → L2 DNS-only → L3 rollback NS.
7. **Taxonomía canónica.** En ENT_PLAT_SEGURIDAD usar EXACTAMENTE: [ACTIVO], [PENDIENTE], [N_A], [DECISION_CEO]. El sprint cierra solo si `grep -c '\[PENDIENTE\]'` = 0.
8. **Redis health check con auth.** `REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli ping`. No usar redis-cli sin auth después de activar requirepass.
9. **Resource limits con mem_limit/cpus.** No deploy.resources (requiere Swarm). Verificar con `docker stats` (MEM) y `docker inspect NanoCpus` (CPU).
10. **Push alert obligatorio.** El canal de notificación ante fallo de backup DEBE ser push real (ntfy/Telegram/webhook), no solo archivo sentinel.

## BRANCH

```bash
git checkout -b feat/sprint27-security-hardening
```

## FASES — EJECUTAR EN ORDEN

### Fase 0 — Verificación ENT_PLAT_SEGURIDAD (3-4h)
- Re-verificar A-E, H (drift check desde S24)
- Verificar F (monitoring: logging, alerting, retention) y G (compliance: LGPD, audit trail) — NUEVOS
- Si F2 (alerting) falla → implementar S27-07d2: cron health check 5min + push
- Si G2 (audit trail) falla → implementar S27-07g2: middleware DataAccessAuditMiddleware
- Actualizar ENT_PLAT_SEGURIDAD con tags canónicos
- Generar checklist de evidencias para CEO

### Fase 1 — Secrets Audit (2-3h)
- truffleHog scan completo del repo
- Permisos .env 600 + .gitignore
- Matriz formal de secrets (12+ entries, incluir creds del canal push)
- Redis requirepass + configurar Django/Celery
- Documentar rotación 90d

### Fase 2 — DR Mínimo Viable (3-4h)
- Script backup_mwt.sh integral (PG + MinIO + config hard/opcional + manifest)
- Ejecución manual inmediata (NO esperar cron)
- Cron diario 3am (exportar crontab antes)
- Cleanup retention 30d
- Canal push funcional (test de notificación)
- Restore drill integral (DB + MinIO + app arranca)
- RPO/RTO en ENT_PLAT_SEGURIDAD.C4

### Fase 3 — Cloudflare + Docker Hardening (2-3h)
- Export zona DNS → recrear en Cloudflare → cutover con monitoreo 3 dominios
- Docker non-root (verificar, no asumir)
- mem_limit + cpus en docker-compose → verificar con stats + inspect
- Health checks (Redis con REDISCLI_AUTH, Celery con pgrep)
- Fail2ban SSH (maxretry=5, bantime=3600s)

## DEFINITION OF DONE — 13 CHECKS TÉCNICOS

| # | Check |
|---|-------|
| 1 | ENT_PLAT_SEGURIDAD: 0 [PENDIENTE] |
| 2 | F2/G2 remediados si negativos |
| 3 | Checklist evidencias entregado |
| 4 | truffleHog 0 hallazgos |
| 5 | Matriz secrets 12+ (incluye push creds) |
| 6 | .env 600 + .gitignore |
| 7 | Redis requirepass + Django/Celery |
| 8 | Backup integral + cleanup + push alert |
| 9 | Restore drill OK |
| 10 | 3 dominios → Cloudflare |
| 11 | Docker: non-root + MEM + CPU + health |
| 12 | Fail2ban SSH |
| 13 | RESUMEN_SPRINT27.md entregado |

## ENTREGABLE

`RESUMEN_SPRINT27.md` con outputs de verificación, tabla DoD ✅/❌, evidencias por gate.

## SI ALGO FALLA

- SSH/acceso → usar consola Hostinger
- DNS → escalera L1/L2/L3 (ver LOTE §Fase 3)
- Docker → rebuild desde compose (no inventar)
- Backup → revisar output, no forzar éxito
- **Si no podés resolver algo → PARAR y reportar al CEO.** No seguir con errores pendientes.
