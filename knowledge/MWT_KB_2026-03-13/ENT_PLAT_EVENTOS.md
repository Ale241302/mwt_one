# ENT_PLAT_EVENTOS — Bus de Eventos y Suscriptores
status: DRAFT
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
version: 1.0

---

## A. Arquitectura de eventos

Patrón: Transactional Outbox → Redis Streams → Consumer Groups.

Cada artefacto al ejecutarse emite eventos estructurados al bus. Suscriptores consumen eventos según su dominio. Eventos son append-only (ref → POL_INMUTABILIDAD).

## B. Eventos canónicos por artefacto

| Artefacto | Evento | Payload mínimo |
|-----------|--------|---------------|
| OC Cliente (ART-01) | oc.received | expediente_id, client_id, brand, items[], total |
| Proforma MWT (ART-02) | proforma.created | expediente_id, consecutivo, brand, mode, lineas[], montos |
| Proforma MWT (ART-02) | proforma.split | expediente_id, proforma_aa, proforma_ab |
| Decisión B/C (ART-03) | mode.selected | expediente_id, mode (COMISION/FULL), decided_by [CEO-ONLY] |
| Confirmación SAP (ART-04) | sap.confirmed | expediente_id, sap_id, fecha_fabricacion_probable |
| AWB/BL (ART-05) | shipment.created | expediente_id, tipo (awb/bl), carrier, origen, destino, tracking, itinerario[], transport_mode |
| Cotización flete (ART-06) | freight.quoted | expediente_id, monto, modo, freight_mode (prepaid/postpaid) |
| Aprobación despacho (ART-07) | dispatch.approved | expediente_id, approved_by (client/ceo), dispatch_mode (mwt/client) |
| Docs aduanales (ART-08) | customs.ready | expediente_id, ncm[], dai_pct, permisos[] |
| Factura MWT (ART-09) | invoice.issued | expediente_id, invoice_id, total_client_view, currency |
| Factura comisión (ART-10) | commission.invoiced | expediente_id, commission_amount [CEO-ONLY] |
| Registro costos (ART-11) | cost.registered | expediente_id, cost_type, amount, phase [CEO-ONLY] |
| Nota compensación (ART-12) | compensation.noted | expediente_id, items[], value [CEO-ONLY] |

### B1. Eventos de estado (sistema)
| Evento | Payload |
|--------|---------|
| expediente.created | expediente_id, brand, mode, client_id |
| expediente.state_changed | expediente_id, from_state, to_state, trigger_artifact |
| expediente.completed | expediente_id, duration_total, cost_total [CEO-ONLY] |
| expediente.blocked | expediente_id, reason, blocked_artifact |

[PENDIENTE — ARCH-02: taxonomía completa de 30-50 eventos con payloads JSON schema formal.]

## C. Suscriptores

| Suscriptor | Consume eventos | Propósito |
|-----------|----------------|----------|
| Contabilidad/ERP | cost.registered, invoice.issued, commission.invoiced | Registro contable automático |
| Dashboard CEO | Todos (filtrado por visibility) | Vista real-time operaciones |
| Dashboard Cliente | state_changed, shipment.created (solo tracking), invoice.issued | Vista limitada estado + docs |
| Forecast | Todos eventos históricos | Análisis predictivo tiempos/costos/rutas |
| Notificaciones | state_changed, dispatch.approved, invoice.issued | Emails/push a cliente y equipo |
| Auditoría | Todos | Log inmutable para compliance |

### C1. Regla de visibilidad eventos
- Eventos con campo [CEO-ONLY] en payload: solo Dashboard CEO y Auditoría.
- Dashboard Cliente: nunca recibe costos internos, modo B/C, compensación.
- Políticas de precio: no consumen eventos — generan restricciones que artefactos consultan antes de actuar.

## D. Dashboard CEO — secciones alimentadas por eventos

| Sección | Eventos fuente | Métricas |
|---------|---------------|----------|
| Expedientes activos | state_changed, blocked | Estado, semáforo tiempos (verde/amarillo/rojo vs histórico), costos acumulados vs margen |
| Rentabilidad | cost.registered, invoice.issued, commission.invoiced | Por expediente, cliente, marca, modo B vs C |
| Alertas | blocked, cost.registered (si supera proyección) | Desviaciones tiempo, costo, patrones reorden |
| Forecast | Todos históricos | Demanda por cliente, punto óptimo aéreo/marítimo, estacionalidad |
| Cash flow | invoice.issued, cost.registered, freight.quoted | Facturas por cobrar, pagos por salir, prepaid/postpaid |
| Comparativa modelos | mode.selected + resultados finales | "¿Qué hubiera pasado si B en vez de C?" Retroactivo. |

## E. Dashboard Cliente — secciones

| Sección | Eventos fuente |
|---------|---------------|
| Mis pedidos | state_changed (filtrado) |
| Tracking | shipment.created (carrier, tracking, itinerario, ETA) |
| Documentos | proforma.created, invoice.issued (solo vista client) |
| Historial | expediente.completed (patrones para reorden) |
| Notificaciones | state_changed, invoice.issued |

Valor: cliente ve estado sin enviar correos. Sistema puede sugerir "basado en tu patrón, deberías ordenar en 3 semanas".

## F. Implementación técnica

| Componente | Tecnología |
|-----------|-----------|
| Outbox | Tabla PostgreSQL (cambio estado + evento en misma transacción) |
| Dispatcher | Celery worker lee outbox, publica a Redis Streams |
| Bus | Redis Streams con consumer groups |
| Consumidores | Celery workers por dominio (contabilidad, notificaciones, etc.) |
| Idempotencia | event_id único + tabla processed_events por consumidor |
| Dead letter | Redis Stream separado para eventos que fallan procesamiento |
| Persistencia | Redis AOF + copia a PostgreSQL event_store para auditoría |

[PENDIENTE — investigación swarm agent Tema 3: Outbox Pattern + Event Bus detalle implementación.]

---

Stamp: DRAFT — Pendiente aprobación CEO
