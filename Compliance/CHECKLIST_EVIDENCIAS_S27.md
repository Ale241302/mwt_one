# CHECKLIST_EVIDENCIAS_S27 — MWT.ONE
Fecha: 2026-04-10
Sprint: 27
Estado: IN_PROGRESS

| Tag | Control | Evidencia Requerida | Estado | Fecha |
|-----|---------|---------------------|--------|-------|
| A1 | SSH Restricted | `sshd_config` snippet + IP match | [ ] | |
| A2 | JWT Rotation | Output `python manage.py shell` (ROTATE: True)| [ ] | |
| B1 | truffleHog 0 | Screenshot/Output trufflehog scan result | [ ] | |
| B3 | .env ignored | `git ls-files .env` is empty | [ ] | |
| C1 | Backup Script | `scripts/backup_mwt.sh` existance | [ ] | |
| C3 | Restore Drill | Log de restauración exitosa (DB+MinIO) | [ ] | |
| D1 | WAF CF | `dig` output Cloudflare IPs | [ ] | |
| D2 | HSTS Headers | `curl -I` output Strict-Transport-Security | [ ] | |
| E1 | Non-root Docker| `docker exec user id` check | [ ] | |
| E2 | Resource Limits| `docker stats` Memory != 0 | [ ] | |
| E3 | Health Checks | `docker ps` column 'Status' (healthy)| [ ] | |
| F2 | Alerting Cron | Cron job entry + Push notification test | [ ] | |
| G2 | Audit Policy | `Data_Access` logs entries | [ ] | |
| DoD | RESUMEN Final | `RESUMEN_SPRINT27.md` complete | [ ] | |

---
*Este documento es transitorio y sirve como base para la aprobación final del CEO.*
