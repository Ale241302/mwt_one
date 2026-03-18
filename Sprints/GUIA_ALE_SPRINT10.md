# Sprint 10 — Guía de implementación para Alejandro

## Qué es esto
Acordeón operativo de expedientes + Dashboard mejorado + Security hardening + Knowledge fix.
Auditado 3 rondas por ChatGPT — score 9.6/10. 16 fixes aplicados. LOTE v3.1.

## Scope: 8 items, 4 fases

| Fase | Items | Prioridad |
|------|-------|-----------|
| 0 | S10-01 Usuarios Edit/Delete, S10-02 Transfers Edit/Delete | P1 (1 día) |
| 1 | S10-03 Acordeón artefactos, S10-04 ArtifactModal ×10, S10-05 Dashboard | P0 (core) |
| 2 | S10-06 Security hardening | P1 (paralelo) |
| 3 | S10-07 Knowledge fix | P1 |

## Orden de ejecución

### Día 1 — Fase 0: CRUD carry-over
1. Backend: crear PUT/DELETE para `/api/admin/users/{id}/` y `/api/transfers/{id}/` si no existen
2. Frontend: agregar Edit (FormModal) + Delete (ConfirmDialog) a usuarios y transfers
3. Patrón: idéntico a nodos/page.tsx de Sprint 9.1

### Días 2-4 — Fase 1: Workflow operativo

**S10-03 es el item más grande.** Reescritura de `expedientes/[id]/page.tsx`.

Orden dentro de S10-03:
1. Timeline horizontal con clases .timeline-dot-* del design system
2. Acordeón por estado con aria-expanded
3. Artefactos por estado (tabla FROZEN — ver LOTE)
4. Funciones shouldRender/canRegister/blockReason
5. Botones de avance (C6, C11, C12, C14)
6. Gate de avance consumiendo required_to_advance del API
7. Costos con toggle + guardia terminales
8. Acciones Ops

Después de S10-03:
- S10-04a: Backend — crear C22 IssueCommissionInvoice si no existe
- S10-04b: Frontend — 10 modals de artefactos usando FormModal
- S10-05a: Backend — agregar by_status y next_actions al dashboard endpoint
- S10-05b: Frontend — mini-pipeline bar + próximas acciones

### Paralelo — Fase 2: Security
- Nginx rate limiting (ver config exacta en LOTE)
- Django throttle rates
- gitleaks sobre repo
- Redis requirepass
- JWT lifetimes

### Después — Fase 3: Knowledge
- Fix /api/knowledge/ask/ 500
- Carga pgvector

## Lo que NO debes hacer (constraints del LOTE)

1. **NO crear state machine paralela.** Importar estados desde `frontend/src/constants/states.ts`. Nunca redefinir arrays de estados localmente.
2. **NO crear modals/drawers custom.** Usar FormModal.tsx y ConfirmDialog.tsx existentes.
3. **NO reimplementar formularios de artefactos desde cero.** Sprint 7 (S7-07, S7-09) ya los tiene. Restaurar dentro de FormModal.
4. **NO calcular gates en frontend.** Consumir `required_to_advance` del API.
5. **NO usar hex hardcodeado.** Solo CSS variables del design system.
6. **NO poner CANCELADO como nodo en el timeline.** Es badge lateral.

## Backend necesario (crear si no existe)

| Endpoint | Método | Qué hace |
|----------|--------|----------|
| /api/admin/users/{id}/ | PUT, DELETE | CRUD usuarios |
| /api/transfers/{id}/ | PUT, DELETE | CRUD transfers |
| /api/expedientes/{id}/commands/issue-commission-invoice/ | POST | C22 — ART-10 comisión |
| /api/ui/expedientes/{id}/ | GET (agregar campo) | + required_to_advance |
| /api/ui/dashboard/ | GET (agregar campos) | + by_status + next_actions |

## Archivos principales a tocar

| Archivo físico | Acción |
|---------------|--------|
| `frontend/src/app/[lang]/(mwt)/(dashboard)/expedientes/[id]/page.tsx` | REESCRITURA |
| `frontend/src/components/expediente/ExpedienteAccordion.tsx` | CREAR |
| `frontend/src/components/expediente/ArtifactRow.tsx` | CREAR |
| `frontend/src/components/expediente/GateMessage.tsx` | CREAR |
| `frontend/src/components/expediente/CostTable.tsx` | CREAR |
| `frontend/src/components/expediente/ArtifactModal.tsx` | CREAR (usa FormModal como shell) |
| `frontend/src/app/[lang]/(mwt)/(dashboard)/page.tsx` | MODIFICAR (dashboard) |
| `frontend/src/app/[lang]/(mwt)/(dashboard)/usuarios/page.tsx` | MODIFICAR (Edit/Delete) |
| `frontend/src/app/[lang]/(mwt)/(dashboard)/transfers/page.tsx` | MODIFICAR (Edit/Delete) |

## Tests post-deploy

**State machine:**
- [ ] Acordeón muestra artefactos correctos por estado
- [ ] ART-08 NO aparece cuando dispatch_mode=client
- [ ] ART-10 NO aparece cuando mode=FULL
- [ ] ART-10 SÍ aparece cuando mode=COMISION
- [ ] ART-07 bloqueado hasta ART-05 + ART-06
- [ ] ART-08 bloqueado hasta ART-05 + ART-06 (cuando dispatch_mode=mwt)
- [ ] ART-09 NO disponible antes de EN_DESTINO
- [ ] CANCELADO: badge lateral, no nodo en timeline, acciones deshabilitadas

**Avance:**
- [ ] C6 en PRODUCCION, C11 en DESPACHO, C12 en TRANSITO, C14 en EN_DESTINO
- [ ] C14 solo si ART-09 done
- [ ] REGISTRO/PREPARACION: sin botón avance independiente

**Dashboard:**
- [ ] Mini-pipeline: 6 segmentos, clic navega filtrado
- [ ] Próximas acciones: top 3

**Security:**
- [ ] Rate limiting: 429 al exceder
- [ ] redis-cli ping sin AUTH → NOAUTH
- [ ] JWT access 15min

**Knowledge:**
- [ ] /api/knowledge/ask/ → 200

---

*Sprint 10 · MWT ONE · LOTE v3.1 · Score auditoría 9.6/10*
