# ENT_PLAT_SEGURIDAD — MWT.ONE
version: 2.1
status: VIGENTE (Auditado y Validado)
domain: Plataforma (IDX_PLATAFORMA)

---

## Taxonomía de Estados
- `[ACTIVO]`: Verificado y operativo.
- `[POR_HACER]`: Acción requerida (Audit Ready).
- `[N_A]`: No aplica.
- `[DECISION_CEO]`: Pendiente de definición por gobernanza.

---

## A. Acceso e Identidad (CEO-17)
| ID | Control | Estado | Evidencia |
|----|---------|--------|-----------|
| A1 | SSH: Restricción IP | [ACTIVO] | Configurado en sshd_config + Fail2ban |
| A2 | JWT Rotation | [ACTIVO] | S24 implementation (verified ROTATE: True) |
| A3 | Password Policy | [N_A] | Delegado a MWTUser (Django defaults) |

## B. Protección de Secretos (CEO-19)
| ID | Control | Estado | Evidencia |
|----|---------|--------|-----------|
| B1 | truffleHog Scan | [ACTIVO] | Verified 0 findings in local scan |
| B2 | .env Permissions (600) | [ACTIVO] | Manual chmod 600 verified in /opt/mwt |
| B3 | .env in .gitignore | [ACTIVO] | git ls-files verified empty |
| B4 | Matriz de 12+ Secrets | [ACTIVO] | Matriz documentada y contrastada |

## C. Disponibilidad y Respaldo (DR)
| ID | Control | Estado | Evidencia |
|----|---------|--------|-----------|
| C1 | Backup PostgreSQL + MinIO | [ACTIVO] | scripts/backup_mwt.sh operativo |
| C2 | Retention policy (30d) | [ACTIVO] | S27-15b via mc rm/lifecycle |
| C3 | Restore Drill | [ACTIVO] | Validado en DB mwt_test |
| C4 | RPO/RTO | [ACTIVO] | RPO=24h, RTO=4h (CEO approved) |

## D. Comunicaciones y Red
| ID | Control | Estado | Evidencia |
|----|---------|--------|-----------|
| D1 | WAF (Cloudflare) | [ACTIVO] | DNS Proxied en CF (cleo/vivienne NS) |
| D2 | HSTS + Security Headers | [ACTIVO] | Nginx mwt.conf (Strict-Transport-Security) |
| D3 | DNSSEC | [ACTIVO] | Enabled in Cloudflare Dashboard |
| D4 | SSL Full (Strict) | [ACTIVO] | Configuración extremo a extremo CF |

## E. Hardening de Infraestructura
| ID | Control | Estado | Evidencia |
|----|---------|--------|-----------|
| E1 | Docker Non-root | [ACTIVO] | user: postgres/1000 en docker-compose |
| E2 | Resource Limits (MEM/CPU)| [ACTIVO] | mem_limit/cpus en todos los servicios |
| E3 | Health Checks | [ACTIVO] | docker ps healthy (Redis auth/pg_isready) |
| E4 | Fail2ban SSH | [ACTIVO] | jail.local activo en host |

## F. Monitoreo y Logging
| ID | Control | Estado | Evidencia |
|----|---------|--------|-----------|
| F1 | Structured Logging (JSON)| [ACTIVO] | settings/base.py S24 |
| F2 | Alerting 5xx/OOM/Disk | [ACTIVO] | scripts/health_check_cron.sh activo |
| F3 | Log Retention (30d/90d) | [ACTIVO] | Configuración de rotación en Docker Log driver |

## G. Cumplimiento (Compliance)
| ID | Control | Estado | Evidencia |
|----|---------|--------|-----------|
| G1 | LGPD Consent | [N_A] | B2B Internal Policy |
| G2 | Data Access Audit | [ACTIVO] | DataAccessAuditMiddleware activo |

## H. Ciclo de Vida
| ID | Control | Estado | Evidencia |
|----|---------|--------|-----------|
| H1 | Secrets Rotation (90d) | [ACTIVO] | Política establecida en esta matriz |

---

## Matriz de Secrets (B4)
| Nombre | Ubicación | Rotación | Responsable |
|--------|-----------|----------|-------------|
| Django SECRET_KEY | .env | 90d | AG-02 |
| JWT Signing Key | .env | 90d | AG-02 |
| PG Password | .env | 90d | AG-02 |
| Redis Password | .env | 90d | AG-02 |
| MinIO Access/Secret| .env | 90d | AG-02 |
| Claude API Key | .env | 90d | CEO |
| OpenAI API Key | .env | 90d | CEO |
| n8n Credentials | .env | 90d | AG-02 |
| CF API Token | .env | 90d | CEO |
| GH Deploy Keys | GitHub | 90d | AG-02 |
| GPG Key Backup | .env | 90d | CEO |
| SMTP Credentials | .env | 90d | AG-02 |
| Alerting Webhook | .env | 90d | AG-02 |

---

Changelog:
- v2.0 (2026-04-10): Estructura Sprint 27.
- v2.1 (2026-04-10): Cierre formal. Todos los controles verificados [ACTIVO].
