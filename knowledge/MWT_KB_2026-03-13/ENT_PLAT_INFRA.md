# ENT_PLAT_INFRA — Infraestructura y Capacity Planning
status: DRAFT
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
version: 1.0

---

## A. Servidor — Hostinger KVM 8

| Spec | Valor |
|------|-------|
| CPU | 8 vCPU AMD EPYC |
| RAM | 32 GB |
| Disco | 400 GB NVMe SSD |
| Bandwidth | 32 TB |
| Red | 1 Gbps |
| IP | Dedicada |
| Backups | Weekly gratis |
| OS | Ubuntu 24 |
| Costo | ~$20/mo (deal actual) → $50/mo (renovación) |

## B. Servicios Docker (12 contenedores)

| Servicio | RAM | CPU | Disco | Función |
|----------|-----|-----|-------|---------|
| Django + Gunicorn (4 workers) | 1.5 GB | 2 cores | 2 GB | Backend principal, API DRF, orquestador |
| PostgreSQL 16 | 2 GB | 1 core | 20 GB+ | Base de datos principal |
| Redis 7 | 512 MB | 0.5 core | 1 GB | Cache, event bus (Streams), broker Celery |
| Celery (4 workers) | 1 GB | 1 core | 1 GB | Tasks asíncronos |
| Celery Beat | 128 MB | 0.1 core | 100 MB | Scheduler cron |
| Next.js mwt.one (SPA) | 512 MB | 0.5 core | 2 GB | Frontend interno |
| Next.js ranawalk.com (SSR) | 512 MB | 0.5 core | 2 GB | Frontend público |
| Next.js portal.mwt.one (SPA) | 512 MB - 1 GB | 0.5 core | 2 GB | Portal B2B |
| n8n | 1 GB | 0.5 core | 5 GB | Workflows visuales (email, notificaciones) |
| Windmill | 1.5 GB | 1 core | 5 GB | Scripts Python complejos (pricing, forecast, OCR) |
| MinIO | 512 MB | 0.5 core | 50 GB+ | Object storage (docs, facturas, imágenes) |
| Nginx | 128 MB | 0.1 core | 500 MB | Reverse proxy, SSL, routing |

### B1. Totales estimados
| Recurso | Usado | Disponible | Headroom |
|---------|-------|-----------|----------|
| RAM | ~10 GB | 32 GB | 22 GB |
| CPU | ~7.7 cores | 8 cores | 0.3 cores |
| Disco | ~93 GB | 400 GB | 307 GB |

### B2. Headroom permite agregar
- Grafana + Loki observabilidad (~1 GB RAM).
- Worker Prophet/forecast (~2 GB RAM picos).
- PostgreSQL con más buffer para queries pesados.
- Headroom picos Celery tasks.

Veredicto: KVM 8 suficiente para todo el Centro de Operaciones en una sola máquina.

## C. Separación responsabilidades workflow engines

| Engine | Uso | Ejemplos |
|--------|-----|---------|
| n8n | Workflows visuales simples | Emails, notificaciones, webhooks |
| Windmill | Scripts Python complejos | Pricing cálculos, forecast, OCR documentos, ETL |
| Celery | Tasks asíncronos Django | Event dispatch, background jobs, scheduled tasks |

Django = orquestador central. n8n y Windmill = ejecutores (brazos). Cerebro = arquitectura propietaria MWT.

## D. Dominios y SSL

| Dominio | Frontend | SSL |
|---------|----------|-----|
| mwt.one | Next.js SPA interno | Let's Encrypt |
| ranawalk.com | Next.js SSR público | Let's Encrypt |
| portal.mwt.one | Next.js SPA B2B | Let's Encrypt |

3 certificados via Certbot/Let's Encrypt, renovación automática.

## E. Backup strategy

- PostgreSQL: pg_dump automático diario + semanal completo.
- MinIO: sync a storage externo (S3 o Backblaze B2).
- Hostinger: weekly backup gratis incluido.
- [PENDIENTE — backup offsite automatizado]

## F. Stack técnico confirmado

| Componente | Tecnología | Versión |
|-----------|-----------|---------|
| Backend | Django + DRF | 5.x |
| Base datos | PostgreSQL | 16 |
| Cache/Bus | Redis | 7 |
| Task queue | Celery | latest |
| Frontend | Next.js | latest |
| Object storage | MinIO | latest |
| Workflow visual | n8n | latest |
| Workflow code | Windmill | latest |
| Reverse proxy | Nginx | latest |
| Containers | Docker + Docker Compose | latest |
| OS | Ubuntu | 24 |

---

Stamp: DRAFT — Pendiente aprobación CEO
