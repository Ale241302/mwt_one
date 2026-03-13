# ENT_GOB_KPI — Indicadores de Desempeño
id: ENT_GOB_KPI
version: 1.0
domain: Gobernanza (IDX_GOBERNANZA)
status: DRAFT
visibility: [INTERNAL]
stamp: DRAFT — pendiente aprobación CEO
iso: 9001:2015 §9.1, 45001:2018 §9.1

---

## A. Propósito

KPIs medibles por proceso. Alimentan la revisión por la dirección (PLB_REVISION_DIRECCION) y demuestran mejora continua a un auditor ISO.

Principio: solo se mide lo que se puede actuar. KPI sin acción asociada = métrica de vanidad.

---

## B. KPIs por módulo

### B1. Expedientes (M1)

| KPI | Fórmula | Fuente | Umbral verde | Umbral rojo | Frecuencia |
|-----|---------|--------|-------------|-------------|-----------|
| Tiempo promedio por fase | Σ(días en fase) / n expedientes | ENT_OPS_STATE_MACHINE event log | ≤ histórico + 10% | > histórico + 30% | Mensual |
| % expedientes con corrección de costo | Expedientes con R1+ en costos / total | ART-11 versioning | < 10% | > 25% | Mensual |
| Reloj crédito: días promedio de cobro | Σ(días hasta pago) / n expedientes | Reloj crédito 90d | ≤ 60 días | > 80 días | Mensual |
| Expedientes bloqueados por crédito | Count(estado=BLOQUEADO por crédito) | State machine | 0 | > 2 simultáneos | Semanal |
| Proformas aprobadas sin revisión | Proformas R0 aprobadas / total | ART-02 versioning | > 80% | < 60% | Mensual |

### B2. Pricing (M2)

| KPI | Fórmula | Fuente | Umbral verde | Umbral rojo | Frecuencia |
|-----|---------|--------|-------------|-------------|-----------|
| Margen real vs proyectado | |margen_real - margen_proyectado| / margen_proyectado | ENT_OPS_EXPEDIENTE.C2 | < 5% desviación | > 15% desviación | Por expediente cerrado |

### B3. Marketplace / Amazon (M8)

| KPI | Fórmula | Fuente | Umbral verde | Umbral rojo | Frecuencia |
|-----|---------|--------|-------------|-------------|-----------|
| TACoS | Ad spend / total revenue | Amazon Advertising | < 12% | > 20% | Semanal |
| Devoluciones por defecto de producto | Returns "defective" / units sold | Amazon reports | < 2% | > 5% | Mensual |

### B4. Scanner SaaS (futuro)

| KPI | Fórmula | Fuente | Umbral verde | Umbral rojo | Frecuencia |
|-----|---------|--------|-------------|-------------|-----------|
| Attach rate plantilla/scan | Ventas plantilla post-scan / total scans | Scanner SaaS DB | > 25% | < 15% | Semanal |
| Scans por distribuidor/mes | Count(scans) por tenant | Scanner SaaS DB | > 50 | < 20 | Mensual |
| Uptime del servicio | Horas disponible / horas totales | Monitoring | > 99.5% | < 99% | Mensual |
| Incidentes de seguridad | Count(incidentes) | PLB_INCIDENT_RESPONSE log | 0 | > 0 | Mensual |
| Tiempo de respuesta a incidente | Horas desde detección hasta contención | PLB_INCIDENT_RESPONSE log | < 4 horas | > 24 horas | Por incidente |

### B5. SSO (ISO 45001)

| KPI | Fórmula | Fuente | Umbral verde | Umbral rojo | Frecuencia |
|-----|---------|--------|-------------|-------------|-----------|
| Incidentes laborales | Count(incidentes) | ENT_GOB_SSO log | 0 | > 0 | Trimestral |
| Días sin incidente | Días consecutivos sin incidente | ENT_GOB_SSO log | > 90 | < 30 | Continuo |

---

## C. Dashboard de revisión

Para PLB_REVISION_DIRECCION, el SCH_ISO_AUDIT_PACK genera una vista consolidada de todos los KPIs con semáforo verde/amarillo/rojo y tendencia (mejorando/estable/empeorando).

Fuente de datos MVP: manual (CEO reporta). Post-MVP: automático desde PostgreSQL vía Grafana (ref → ENT_PLAT_OBSERVABILIDAD).

---

Stamp: DRAFT — Pendiente aprobación CEO
