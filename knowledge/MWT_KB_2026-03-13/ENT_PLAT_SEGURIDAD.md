# ENT_PLAT_SEGURIDAD — MWT.ONE
version: 2.0
status: VIGENTE (post-S27 completion)
domain: Plataforma (IDX_PLATAFORMA)

---

## Taxonomía de Estados
- `[ACTIVO]`: Verificado y operativo.
- `[PENDIENTE]`: Acción requerida en este sprint.
- `[N_A]`: No aplica.
- `[DECISION_CEO]`: Pendiente de definición por gobernanza.

---

## A. Acceso e Identidad (CEO-17)
| ID | Control | Estado | Evidencia |
|----|---------|--------|-----------|
| A1 | SSH: Restricción IP | [PENDIENTE] | Por configurar en sshd_config |
| A2 | JWT Rotation | [ACTIVO] | S24 implementation |
| A3 | Password Policy | [N_A] | Delegado a MWTUser (Django defaults) |

## B. Protección de Secretos (CEO-19)
| ID | Control | Estado | Evidencia |
|----|---------|--------|-----------|
| B1 | truffleHog Scan | [PENDIENTE] | Ejecutar en Fase 1 |
| B2 | .env Permissions (600) | [PENDIENTE] | Verificar en servidor |
| B3 | .env in .gitignore | [ACTIVO] | git ls-files is empty |
| B4 | Matriz de 12+ Secrets | [PENDIENTE] | Crear tabla en esta sección |

## C. Disponibilidad y Respaldo (DR)
| ID | Control | Estado | Evidencia |
|----|---------|--------|-----------|
| C1 | Backup PostgreSQL + MinIO | [PENDIENTE] | Crear backup_mwt.sh |
| C2 | Retention policy (30d) | [PENDIENTE] | S27-15b implementation |
| C3 | Restore Drill | [PENDIENTE] | Fase 2 Gate |
| C4 | RPO/RTO | [DECISION_CEO] | Propuesta: RPO=24h, RTO=4h |

## D. Comunicaciones y Red
| ID | Control | Estado | Evidencia |
|----|---------|--------|-----------|
| D1 | WAF (Cloudflare) | [ACTIVO] | DNS Proxied en CF |
| D2 | HSTS + Security Headers | [ACTIVO] | Nginx mwt.conf config |
| D3 | DNSSEC | [PENDIENTE] | Verificar en CF Dashboard |
| D4 | SSL Full (Strict) | [PENDIENTE] | Fase 3 cutover |

## E. Hardening de Infraestructura
| ID | Control | Estado | Evidencia |
|----|---------|--------|-----------|
| E1 | Docker Non-root | [PENDIENTE] | S27-19 implementation |
| E2 | Resource Limits (MEM/CPU)| [PENDIENTE] | S27-20 implementation |
| E3 | Health Checks | [PENDIENTE] | S27-21 implementation |
| E4 | Fail2ban SSH | [PENDIENTE] | S27-22 implementation |

## F. Monitoreo y Logging
| ID | Control | Estado | Evidencia |
|----|---------|--------|-----------|
| F1 | Structured Logging (JSON)| [ACTIVO] | settings/base.py S24 |
| F2 | Alerting 5xx/OOM/Disk | [PENDIENTE] | Remediación S27-07d2 |
| F3 | Log Retention (30d/90d) | [PENDIENTE] | S27-07e implementation |

## G. Cumplimiento (Compliance)
| ID | Control | Estado | Evidencia |
|----|---------|--------|-----------|
| G1 | LGPD Consent | [N_A] | Justificado por uso interno B2B |
| G2 | Data Access Audit | [PENDIENTE] | Remediación S27-07g2 |

## H. Ciclo de Vida
| ID | Control | Estado | Evidencia |
|----|---------|--------|-----------|
| H1 | Secrets Rotation (90d) | [PENDIENTE] | Documentar en S27-13 |

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
- v2.0 (2026-04-10): Estructura Sprint 27 con tags canónicos.
