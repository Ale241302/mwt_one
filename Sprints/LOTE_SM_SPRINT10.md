# LOTE_SM_SPRINT10 — Acordeón Operativo + Dashboard + Security Hardening
status: DRAFT — aprobado ChatGPT 9.6/10 R3, pendiente aprobación CEO para freeze
visibility: INTERNAL
domain: Plataforma (IDX_PLATAFORMA)
version: 3.1
sprint: 10
priority: P0
agente_principal: AG-03 Frontend (Alejandro) + AG-02 Backend
depends_on: LOTE_SM_SPRINT9 (DONE), Sprint 9.1 (DONE)
refs: ENT_OPS_STATE_MACHINE (FROZEN v1.2.2), ENT_PLAT_DESIGN_TOKENS, ENT_PLAT_SEGURIDAD, ENT_GOB_PENDIENTES

---

## Objetivo Sprint 10

CEO opera expedientes completos desde la consola con visibilidad de artefactos por estado y botones de avance. Tres pilares:

1. **Acordeón operativo:** Detalle de expediente rediseñado — artefactos agrupados por estado, gates de avance, status done/pending/blocked, botones de avance por estado.
2. **Dashboard mejorado:** Mini-pipeline clickeable + próximas acciones.
3. **Hardening:** Security + Knowledge container funcional.

**Precondición:** Sprint 9.1 DONE — globals.css con design system, FormModal.tsx, ConfirmDialog.tsx, states.ts con CANONICAL_STATES/STATE_LABELS/STATE_BADGE_CLASSES/PIPELINE_STATES.

### Incluido

| # | Feature | Fuente | Prioridad |
|---|---------|--------|-----------|
| 1 | Usuarios: Edit + Delete | Carry-over Sprint 9.1b | P1 |
| 2 | Transfers: Edit + Delete | Carry-over Sprint 9.1b | P1 |
| 3 | Detalle expediente con acordeón + botones avance | PLT-12 / S9-05 | P0 |
| 4 | Modals de registro de 10 artefactos | PLT-13 / S9-07 | P0 |
| 5 | Dashboard: mini-pipeline + próximas acciones | S9-06 parcial | P1 |
| 6 | Security: audit + rate limiting + secrets + Redis/JWT | CEO-17/18/19/21 | P1 |
| 7 | Knowledge: fix /ask/ 500 + carga pgvector | CEO-12/13 | P1 |
| 8 | Tests Sprint 10 | — | P0 |

### Excluido

| Feature | Razón | Cuándo |
|---------|-------|--------|
| Portal B2B (portal.mwt.one) | Necesita security hardening completo + knowledge | Sprint 11 |
| PLT-09 Módulo Productos | Menos urgente que workflow artefactos | Sprint 11 |
| PLT-10 Módulo Inventario | Depende de Productos | Sprint 12 |
| CEO-20 Signed URLs MinIO | Va con Portal B2B | Sprint 11 |
| CEO-14 WhatsApp Business API | Canal B2B P2 | Sprint 11+ |
| Vista Calendario | Nice-to-have | Sprint 11 |
| Paperless bidireccional | Webhook no activo | Sprint 11+ |

---

## Constraints obligatorios (validar en auditoría)

### C1. State machine FROZEN
Fuente de verdad: ENT_OPS_STATE_MACHINE v1.2.2 (FROZEN). No crear state machine paralela. No inventar estados ni artefactos.

### C2. Importar desde states.ts
Todo componente que necesite estados DEBE importar desde `frontend/src/constants/states.ts`. Prohibido redefinir arrays de estados localmente.

### C3. Reutilizar componentes Sprint 9.1
FormModal.tsx, ConfirmDialog.tsx, globals.css. Prohibido crear modals paralelos o drawers custom.

### C4. Restaurar, no reinventar
Sprint 7 (S7-07, S7-09) ya implementó formularios para ART-01, 02, 05, 06, 07, 08, 09. Restaurar dentro del nuevo acordeón.

### C5. Design system obligatorio
Colores via CSS variables. Clases del design system. Ref: ENT_PLAT_DESIGN_TOKENS.

### C6. Accesibilidad mínima
htmlFor/id, aria-label, aria-expanded, FormModal para modales.

### C7. Gates desde el API, no calculados en frontend
El frontend consume `required_to_advance` del endpoint de detalle. No calcula reglas de negocio ad hoc.

---

## Commands backend — inventario completo

Todos los commands del MVP (ya implementados Sprints 1-7):

| # | Command | Endpoint | Tipo |
|---|---------|----------|------|
| C2 | RegisterOC | POST /api/expedientes/{id}/commands/register-oc/ | Artefacto |
| C3 | CreateProforma | POST /api/expedientes/{id}/commands/create-proforma/ | Artefacto |
| C4 | DecideModeBC | POST /api/expedientes/{id}/commands/decide-mode/ | Artefacto |
| C5 | RegisterSAPConfirmation | POST /api/expedientes/{id}/commands/register-sap/ | Artefacto |
| C6 | ConfirmProductionComplete | POST /api/expedientes/{id}/commands/confirm-production-complete/ | Avance |
| C7 | RegisterShipment | POST /api/expedientes/{id}/commands/register-shipment/ | Artefacto |
| C8 | RegisterFreightQuote | POST /api/expedientes/{id}/commands/register-freight/ | Artefacto |
| C9 | RegisterCustomsDocs | POST /api/expedientes/{id}/commands/register-customs/ | Artefacto |
| C10 | ApproveDispatch | POST /api/expedientes/{id}/commands/approve-dispatch/ | Artefacto+Avance |
| C11 | ConfirmShipmentDeparted | POST /api/expedientes/{id}/commands/confirm-shipment-departed/ | Avance |
| C12 | ConfirmShipmentArrived | POST /api/expedientes/{id}/commands/confirm-shipment-arrived/ | Avance |
| C13 | IssueInvoice | POST /api/expedientes/{id}/commands/issue-invoice/ | Artefacto |
| C14 | CloseExpediente | POST /api/expedientes/{id}/commands/close-expediente/ | Avance |
| C15 | RegisterCostLine | POST /api/expedientes/{id}/commands/register-cost/ | Transversal |
| C16 | CancelExpediente | POST /api/expedientes/{id}/commands/cancel/ | Excepción |
| C17 | BlockExpediente | POST /api/expedientes/{id}/commands/block/ | Excepción |
| C18 | UnblockExpediente | POST /api/expedientes/{id}/commands/unblock/ | Excepción |
| C19 | SupersedeArtifact | POST /api/expedientes/{id}/commands/supersede-artifact/ | Corrección |
| C20 | VoidArtifact | POST /api/expedientes/{id}/commands/void-artifact/ | Corrección |
| C21 | RegisterPayment | POST /api/expedientes/{id}/commands/register-payment/ | Financiero |
| C22 | IssueCommissionInvoice | POST /api/expedientes/{id}/commands/issue-commission-invoice/ | Artefacto |

C21 RegisterPayment — implementado Sprint 7 (S7-04). Payload: `{ amount, currency, paid_at, reference, payment_method }`. Regla: solo en estados operativos + EN_DESTINO. Actualiza payment_status del expediente.

C22 IssueCommissionInvoice — nuevo Sprint 10. Payload: `{ commission_total, currency, beneficiary }`. Regla: solo en EN_DESTINO, solo si mode=COMISION. Crea ART-10.

---

## Items

### FASE 0 — Carry-over CRUD (1 día)

#### Item S10-01: Usuarios Edit + Delete

**S10-01a — Backend (AG-02)**
- Crear endpoints si no existen:
  - `PUT /api/admin/users/{id}/` — partial update de MWTUser
  - `DELETE /api/admin/users/{id}/` — soft delete (guardia último admin ya existe S8-05)
- Archivo físico: `backend/apps/users/views.py`
- Criterio de done:
  - [ ] PUT retorna 200 con user actualizado
  - [ ] DELETE retorna 204 (o 400 si último admin)

**S10-01b — Frontend (AG-03)** — depende de S10-01a
- Archivo físico: `frontend/src/app/[lang]/(mwt)/(dashboard)/usuarios/page.tsx`
- Ruta URL: `/{lang}/dashboard/usuarios`
- Patrón: idéntico a nodos/page.tsx de Sprint 9.1 (FormModal + ConfirmDialog)
- Criterio de done:
  - [ ] Edit: FormModal con datos pre-llenados (nombre, email, rol, permisos)
  - [ ] Delete: ConfirmDialog, ejecuta DELETE
  - [ ] Loading states en save/delete

#### Item S10-02: Transfers Edit + Delete

**S10-02a — Backend (AG-02)**
- Crear endpoints si no existen:
  - `PUT /api/transfers/{id}/` — partial update
  - `DELETE /api/transfers/{id}/` — delete
- Archivo físico: `backend/apps/transfers/views.py`

**S10-02b — Frontend (AG-03)** — depende de S10-02a
- Archivo físico: `frontend/src/app/[lang]/(mwt)/(dashboard)/transfers/page.tsx`
- Ruta URL: `/{lang}/dashboard/transfers`
- Patrón: FormModal + ConfirmDialog
- Criterio de done:
  - [ ] Edit: FormModal con campos (origen, destino, items, estado)
  - [ ] Delete: ConfirmDialog
  - [ ] Loading states

---

### FASE 1 — Workflow operativo (core del sprint)

#### Item S10-03: Detalle expediente con acordeón de artefactos por estado
- **Agente:** AG-03 Frontend
- **Dependencia:** states.ts, globals.css, FormModal.tsx
- **Archivo físico:** `frontend/src/app/[lang]/(mwt)/(dashboard)/expedientes/[id]/page.tsx` — REESCRITURA
- **Ruta URL:** `/{lang}/dashboard/expedientes/{id}`

**Estructura de la página (de arriba a abajo):**

**A. Header**
- Ref en font mono (.mono)
- Badge estado (STATE_BADGE_CLASSES desde states.ts)
- Badge BLOQUEADO si is_blocked (.badge-critical)
- Breadcrumb: "← Volver a expedientes"

**B. Metadatos** (fila de campos)
- Cliente, Marca, Modo (B/C/FULL), Flete (prepaid/postpaid), Transporte (aereo/maritimo), Dispatch (MWT/client)

**C. Timeline horizontal**
- Clases design system: .timeline, .timeline-node, .timeline-dot-completed, .timeline-dot-active, .timeline-dot-future, .timeline-line-completed, .timeline-line-active, .timeline-line-future
- 7 nodos: REGISTRO, PRODUCCION, PREPARACION, DESPACHO, TRANSITO, EN_DESTINO, CERRADO
- CANCELADO: NO es nodo en el timeline. Badge lateral .badge-critical "CANCELADO" junto al header. Timeline muestra hasta dónde llegó.
- Dot activo: .timeline-dot-active (pulse animation)
- Completados: .timeline-dot-completed (Mint + check)
- Futuros: .timeline-dot-future (dashed)

**D. Acordeón por estado**
Secciones colapsables con `<details>`/`<summary>` o botón con aria-expanded.

Lógica de expansión:
- Completado (antes del actual): colapsado, badge verde "X/X completos"
- Activo (= expediente.status): expandido, artefactos + acciones
- Futuro (después del actual): colapsado, badge gris "Pendiente"
- CANCELADO: no existe panel CANCELADO en el acordeón. Se expande por defecto el último estado operativo alcanzado. Gate de avance no se renderiza. Todas las acciones mutativas (C6/C11/C12/C14/C15/C16/C17/C18/C21/C22) se ocultan o quedan disabled. Solo se permite consulta visual de artefactos y costos.

**D1. Artefactos por estado (FROZEN ENT_OPS_STATE_MACHINE.E):**

| Estado | Artefactos |
|--------|-----------|
| REGISTRO | ART-01 OC Cliente, ART-02 Proforma MWT, ART-03 Decisión B/C, ART-04 Confirmación SAP |
| PRODUCCION | (ningún artefacto) |
| PREPARACION | ART-05 AWB/BL, ART-06 Cotización flete, ART-07 Aprobación despacho, ART-08 Docs aduanales (*) |
| DESPACHO | (ningún artefacto) |
| TRANSITO | (ningún artefacto) |
| EN_DESTINO | ART-09 Factura MWT, ART-10 Factura comisión (**) |

(*) ART-08 solo si dispatch_mode=mwt → no renderizar si dispatch_mode=client
(**) ART-10 solo si mode=COMISION → no renderizar si mode=FULL

**D2. Status visual de cada artefacto:**
- done: check verde, fondo var(--success-bg)
- pending (siguiente): highlight azul var(--info-bg), botón "Registrar"
- blocked: lock gris, texto "Requiere [deps]" en var(--text-tertiary)

**D3. Invariantes de bloqueo (FROZEN):**
1. ART-07 bloqueado hasta ART-05 AND ART-06 COMPLETED → "Requiere ART-05 + ART-06"
2. ART-08 no renderizar si dispatch_mode ≠ mwt
3. ART-08 (si renderiza) bloqueado hasta ART-05 AND ART-06 COMPLETED
4. ART-09 solo registrable en EN_DESTINO
5. ART-10 no renderizar si mode ≠ COMISION

Implementar funciones:
```
shouldRender(type, expediente): boolean
canRegister(type, expediente, artifacts): boolean
blockReason(type, expediente, artifacts): string | null
```

**D4. Acciones de avance por estado (commands sin artefactos):**

| Estado actual | Acción | Command | Endpoint | Condición |
|--------------|--------|---------|----------|-----------|
| PRODUCCION | "Confirmar producción completa" | C6 | POST /api/expedientes/{id}/commands/confirm-production-complete/ | Todos los artefactos de REGISTRO done |
| DESPACHO | "Confirmar salida de carga" | C11 | POST /api/expedientes/{id}/commands/confirm-shipment-departed/ | — |
| TRANSITO | "Confirmar llegada a destino" | C12 | POST /api/expedientes/{id}/commands/confirm-shipment-arrived/ | — |
| EN_DESTINO | "Cerrar expediente" | C14 | POST /api/expedientes/{id}/commands/close-expediente/ | ART-09 COMPLETED |

Estos botones aparecen dentro del acordeón del estado activo, debajo de los artefactos (si los hay) o como acción principal (si no hay artefactos en ese estado).

**E. Gate de avance (constraint C7)**
El frontend consume el campo `required_to_advance` del endpoint de detalle:

```json
GET /api/ui/expedientes/{id}/ responde:
{
  ...
  "required_to_advance": {
    "current_state": "PREPARACION",
    "next_state": "DESPACHO",
    "missing": [
      { "code": "ART-06", "label": "Cotización flete", "kind": "artifact" },
      { "code": "ART-07", "label": "Aprobación despacho", "kind": "artifact" }
    ]
  }
}
```

Si `missing` está vacío:
- En REGISTRO y PREPARACION: mostrar solo "Listo para avanzar". No renderizar botón de avance independiente. La transición ocurre mediante el command del último artefacto requerido (C5 en REGISTRO, C10 en PREPARACION).
- En PRODUCCION, DESPACHO, TRANSITO, EN_DESTINO: mostrar "Listo para avanzar" + botón de avance correspondiente (C6/C11/C12/C14).

Si `missing` tiene items → mostrar "Para avanzar a [next_state]: completar [lista]" en amarillo (.badge-warning bg).

**Backend (AG-02):** agregar campo `required_to_advance` al serializer de GET /api/ui/expedientes/{id}/. La lógica de qué falta ya está en la state machine — solo exponerla en el API.

**F. Costos**
Sección fija al pie (fuera del acordeón).
- Tabla: tipo, descripción, fase, monto (.cell-money), visibilidad
- Toggle "Vista Interna" / "Vista Cliente"
- Botón "+ Registrar Costo" (C15) — **visible y habilitado solo en estados operativos. En CERRADO y CANCELADO: tabla visible, botón oculto.**
- Endpoint: GET /api/expedientes/{id}/costs/

**G. Acciones Ops**
Dentro del acordeón del estado activo:
- Desbloquear Manual (C18, si is_blocked)
- Bloquear Manual (C17, si !is_blocked)
- Registrar Costo (C15)
- Registrar Pago (C21) — payload: `{ amount, currency, paid_at, reference, payment_method }`
- Cancelar Expediente (C16, solo en REGISTRO/PRODUCCION/PREPARACION, CEO only)

**Endpoints consumidos:**
- `GET /api/ui/expedientes/{id}/` → datos + artifacts + available_actions + required_to_advance
- `GET /api/expedientes/{id}/costs/` → cost lines

**Componentes nuevos:**
- Archivo: `frontend/src/components/expediente/ExpedienteAccordion.tsx`
- Archivo: `frontend/src/components/expediente/ArtifactRow.tsx`
- Archivo: `frontend/src/components/expediente/GateMessage.tsx`
- Archivo: `frontend/src/components/expediente/CostTable.tsx`

**Criterio de done:**
  - [ ] Timeline usa clases .timeline-dot-* del design system
  - [ ] CANCELADO como badge lateral, no nodo en timeline
  - [ ] Acordeón: activo expandido, completados/futuros colapsados, badge X/Y
  - [ ] ART-08 no se renderiza cuando dispatch_mode=client
  - [ ] ART-10 no se renderiza cuando mode=FULL
  - [ ] ART-10 sí se renderiza y funciona cuando mode=COMISION
  - [ ] ART-07 bloqueado visual hasta ART-05 + ART-06 done
  - [ ] Gate consume required_to_advance del API (no calcula reglas en frontend)
  - [ ] Botones de avance (C6, C11, C12, C14) visibles en el estado correcto
  - [ ] C14 solo habilitado si ART-09 done
  - [ ] Registrar Costo oculto en CERRADO/CANCELADO
  - [ ] Registrar Pago (C21) funcional
  - [ ] aria-expanded en acordeón
  - [ ] No hay state machine paralela

---

#### Item S10-04: Modals de registro de artefactos (10 formularios)

**S10-04a — Backend (AG-02)**
- Crear C22 IssueCommissionInvoice si no existe:
  - Endpoint: POST /api/expedientes/{id}/commands/issue-commission-invoice/
  - Payload: `{ commission_total: number, currency: string, beneficiary: string }`
  - Precondición: status=EN_DESTINO, mode=COMISION
  - Resultado: INSERT ART-10 instance (completed) + INSERT event_log
  - Archivo físico: `backend/apps/expedientes/views.py` o `commands.py`
- Criterio de done:
  - [ ] C22 retorna 201 con ART-10 creado
  - [ ] C22 retorna 400 si mode ≠ COMISION o status ≠ EN_DESTINO

**S10-04b — Frontend (AG-03)** — depende de S10-03 + S10-04a
- Dependencia: S10-03 (acordeón), Sprint 7 formularios (S7-07, S7-09), S10-04a (C22)
- Constraint C4: restaurar formularios Sprint 7 dentro de FormModal

**Shell:** FormModal.tsx. NO crear drawers/modals paralelos.

**Formularios:**

| Artefacto | Campos | Content-Type | Endpoint | Sprint 7 ref |
|-----------|--------|-------------|----------|--------------|
| ART-01 OC | file: binary (required), items: JSON array [{sku, quantity, unit_price}] | multipart/form-data | POST /api/expedientes/{id}/commands/register-oc/ | S7-07 |
| ART-02 Proforma | lines: [{product, quantity, unit_price}], total, currency, consecutive (auto) | application/json | POST /api/expedientes/{id}/commands/create-proforma/ | S7-07 |
| ART-03 Decisión B/C | mode_decision: "COMISION" \| "FULL" | application/json | POST /api/expedientes/{id}/commands/decide-mode/ | nuevo |
| ART-04 SAP | sap_id: string, production_date: date | application/json | POST /api/expedientes/{id}/commands/register-sap/ | nuevo |
| ART-05 AWB/BL | type: "aereo"\|"maritimo", carrier: string, origin: string, destination: string, tracking: string, itinerary: [{location, date}] | application/json | POST /api/expedientes/{id}/commands/register-shipment/ | S7-07 |
| ART-06 Cotización flete | amount: number, currency: string, freight_mode: string | application/json | POST /api/expedientes/{id}/commands/register-freight/ | S7-07 |
| ART-07 Aprobación despacho | approved_by: string, approved_at: date | application/json | POST /api/expedientes/{id}/commands/approve-dispatch/ | S7-07 |
| ART-08 Docs aduanales | ncm: string[], dai_percent: number, permits: string[] | application/json | POST /api/expedientes/{id}/commands/register-customs/ | S7-07 |
| ART-09 Factura MWT | total_client_view: number, currency: "USD"\|"BRL"\|"CRC" | application/json | POST /api/expedientes/{id}/commands/issue-invoice/ | S7-09 |
| ART-10 Factura comisión | commission_total: number, currency: string, beneficiary: string | application/json | POST /api/expedientes/{id}/commands/issue-commission-invoice/ (C22) | nuevo S10-04a |

**UX post-submit:**
- Modal cierra → refetch acordeón sin reload → toast .toast-success "ART-XX registrado"
- Error: toast .toast-critical con mensaje del backend
- Loading: botón muestra "Registrando..."
- Precondiciones no cumplidas: submit deshabilitado + tooltip

**Criterio de done:**
  - [ ] 10 formularios (no 9) — incluyendo ART-10
  - [ ] ART-01 usa multipart/form-data, resto usa application/json
  - [ ] Mínimo ART-01, ART-05, ART-09 verificados end-to-end con seed data
  - [ ] ART-10 verificado cuando mode=COMISION
  - [ ] FormModal como shell (no drawers)
  - [ ] Post-submit refresca acordeón
  - [ ] htmlFor/id en todos los inputs

---

#### Item S10-05: Dashboard mejorado

**S10-05a — Backend (AG-02)**
- Archivo físico: `backend/apps/expedientes/views.py` (vista dashboard)
- Agregar 2 campos al response de GET /api/ui/dashboard/:
  - `by_status`: `{ "REGISTRO": 2, "PRODUCCION": 1, "PREPARACION": 1, "DESPACHO": 1, "TRANSITO": 2, "EN_DESTINO": 1 }`
  - `next_actions`: array top 3 `[{ "id": "uuid", "custom_ref": "EXP-xxx", "client_name": "...", "status": "PREPARACION", "action_label": "Registrar cotización flete" }]`
- Criterio de done:
  - [ ] GET /api/ui/dashboard/ incluye by_status con conteo correcto
  - [ ] next_actions retorna top 3 expedientes que necesitan acción

**S10-05b — Frontend (AG-03)** — depende de S10-05a
- Archivo físico: `frontend/src/app/[lang]/(mwt)/(dashboard)/page.tsx`
- Ruta URL: `/{lang}/dashboard`

**(A) Mini-pipeline bar** (encima de stat cards)
- 6 segmentos, uno por PIPELINE_STATES (importar desde states.ts)
- Cada segmento: STATE_LABELS[estado] + conteo de by_status
- Clic navega a `/${lang}/dashboard/pipeline?status=${estado}`
- Responsive: grid 6→3→2 cols

**(B) Sección "Próximas acciones"** (debajo de stat cards, encima de tablas)
- 3 cards de next_actions: ref (.mono), cliente, badge estado, action_label, botón "Ir"
- Empty state: "Todo al día"

- Criterio de done:
  - [ ] 6 segmentos con conteo (suma = total activos)
  - [ ] Clic navega al pipeline filtrado
  - [ ] Próximas acciones top 3
  - [ ] Importa PIPELINE_STATES/STATE_LABELS desde states.ts
  - [ ] Responsive

---

### FASE 2 — Security hardening (paralelo a Fase 1)

#### Item S10-06: Security audit + rate limiting + secrets + Redis/JWT
- **Agente:** AG-02 Backend + DevOps

**(A) Audit seguridad (CEO-17)**
- [ ] Revisar ENT_PLAT_SEGURIDAD.md — estado real de cada [PENDIENTE]
- [ ] Reporte breve con hallazgos

**(B) Rate limiting (CEO-18)**
- Nginx (`nginx/mwt.conf` o `nginx/conf.d/default.conf`):
  ```
  limit_req_zone $binary_remote_addr zone=api_rate:10m rate=20r/m;
  location /api/ { limit_req zone=api_rate burst=20 nodelay; ... }
  ```
- Django (`backend/config/settings.py`):
  ```python
  REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = [
      'rest_framework.throttling.UserRateThrottle',
      'rest_framework.throttling.AnonRateThrottle',
  ]
  REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = { 'user': '120/min', 'anon': '30/min' }
  ```
- [ ] Verificar: `for i in $(seq 1 25); do curl -s -o /dev/null -w "%{http_code}\n" https://consola.mwt.one/api/ui/dashboard/; done` → 429 aparece

**(C) Secrets audit (CEO-19)**
- [ ] Ejecutar `gitleaks detect --source=. --report-format=json --report-path=gitleaks-report.json` en el repo
- [ ] Resultado: 0 hallazgos → adjuntar reporte. Si hay hallazgos → rotar secrets + adjuntar lista de rotaciones.
- [ ] .env en .gitignore (ya confirmado OK)

**(D) Redis + JWT (CEO-21)**
- docker-compose.yml:
  ```yaml
  redis:
    command: ["redis-server", "--requirepass", "${REDIS_PASSWORD}", "--appendonly", "yes"]
  ```
- backend/config/settings.py:
  ```python
  SIMPLE_JWT = {
      'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
      'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
      'ROTATE_REFRESH_TOKENS': True,
      'BLACKLIST_AFTER_ROTATION': True,
  }
  ```
- [ ] Verificar: `redis-cli ping` sin AUTH retorna `NOAUTH Authentication required`
- [ ] Verificar: `redis-cli -a $REDIS_PASSWORD ping` retorna `PONG`
- [ ] Verificar: JWT access token expira en 15min (decodificar con jwt.io)

---

### FASE 3 — Knowledge container fix

#### Item S10-07: Fix /api/knowledge/ask/ + carga pgvector
- **Agente:** AG-02 Backend

**(A) Fix error 500 (CEO-12)**
- [ ] `docker ps | grep knowledge` → contenedor corriendo
- [ ] Proxy Django apunta a `http://mwt-knowledge:8001` (verificar en views.py)
- [ ] API key Anthropic en env vars del contenedor
- [ ] `CREATE EXTENSION IF NOT EXISTS vector;` en PostgreSQL
- [ ] GET /api/knowledge/ask/?q=test retorna 200

**(B) Carga pgvector (CEO-13)**
- [ ] Ejecutar indexer contra .md de la KB
- [ ] Verificar: archivos con visibility CEO-ONLY NO se indexan
- [ ] Verificar con query real: "¿Qué es un expediente?" → respuesta coherente

---

### QA

#### Item S10-08: Tests Sprint 10
- **Dependencia:** Items 1-7

**State machine fidelidad:**
- [ ] Acordeón: expediente en REGISTRO muestra ART-01/02/03/04
- [ ] Acordeón: expediente en PREPARACION muestra ART-05/06/07 (+ART-08 si dispatch_mode=mwt)
- [ ] ART-08 NO aparece cuando dispatch_mode=client
- [ ] ART-10 NO aparece cuando mode=FULL
- [ ] ART-10 SÍ aparece y registra cuando mode=COMISION
- [ ] ART-07 muestra "Requiere ART-05 + ART-06" cuando esos no están done
- [ ] ART-08 aparece pero queda bloqueado hasta ART-05 + ART-06 cuando dispatch_mode=mwt
- [ ] ART-09 NO puede abrirse ni registrarse en REGISTRO/PRODUCCION/PREPARACION/DESPACHO/TRANSITO
- [ ] CANCELADO se renderiza como badge lateral, NO como nodo en timeline

**Avance por estado:**
- [ ] PRODUCCION: botón "Confirmar producción completa" → avanza a PREPARACION
- [ ] DESPACHO: botón "Confirmar salida" → avanza a TRANSITO
- [ ] TRANSITO: botón "Confirmar llegada" → avanza a EN_DESTINO
- [ ] EN_DESTINO: "Cerrar expediente" solo habilitado si ART-09 done

**Gates:**
- [ ] Gate consume required_to_advance del API
- [ ] Gate muestra artefactos faltantes correctos
- [ ] "Listo para avanzar" aparece cuando no falta nada

**Costos:**
- [ ] Registrar Costo funciona en estados operativos
- [ ] Registrar Costo NO aparece en CERRADO ni CANCELADO

**Modals:**
- [ ] ART-01, ART-05, ART-09: registro end-to-end
- [ ] ART-10: registro end-to-end cuando mode=COMISION
- [ ] ART-01 envía multipart/form-data

**Dashboard:**
- [ ] Mini-pipeline: 6 segmentos, conteo coincide con pipeline real
- [ ] Clic en segmento navega al pipeline filtrado
- [ ] Próximas acciones: top 3 correctos

**CRUD:**
- [ ] Usuarios Edit + Delete funciona
- [ ] Transfers Edit + Delete funciona

**Security:**
- [ ] Rate limiting: 429 al exceder
- [ ] Redis con requirepass
- [ ] JWT 15min access / 7d refresh

**Knowledge:**
- [ ] /api/knowledge/ask/ retorna 200

**Regresión:**
- [ ] Pipeline Kanban funciona
- [ ] Expedientes lista funciona
- [ ] Nodos, Brands, Clientes CRUD funciona

---

## Dependencias internas

```
S10-01a (Usuarios BE) → S10-01b (Usuarios FE)
S10-02a (Transfers BE) → S10-02b (Transfers FE)
                                                  ── Fase 0 (1 día)

S10-03 (Acordeón + avance) ─────────────────────
S10-04a (C22 Backend) ──┐
S10-03 ─────────────────┼→ S10-04b (ArtifactModal × 10 FE)
S10-05a (Dashboard BE) → S10-05b (Dashboard FE)
                                                  ── Fase 1 (core)

S10-06 (Security) ───────────────────────────────── Fase 2 (paralelo)

S10-07 (Knowledge) ──────────────────────────────── Fase 3 (independiente)

S10-08 (Tests) ──────────────────────────────────── después de todo
```

---

## Criterio Sprint 10 DONE

1. Acordeón con artefactos agrupados por estado, gates, done/pending/blocked
2. ART-08 condicional dispatch_mode=mwt, ART-10 condicional mode=COMISION
3. ART-07 bloqueado visual hasta ART-05 + ART-06 done
4. Botones de avance (C6, C11, C12, C14) en estados correctos. C14 solo si ART-09 done.
5. 10 modals de artefactos funcionan, C22 implementado (mínimo ART-01, ART-05, ART-09, ART-10 verificados)
6. Dashboard: mini-pipeline + próximas acciones
7. Usuarios y Transfers con Edit + Delete
8. Rate limiting activo, Redis con password, JWT configurado
9. /api/knowledge/ask/ retorna 200
10. Sin regresiones Sprint 9/9.1

---

## Retrospectiva
(Completar al cerrar el sprint)

---

Stamp: DRAFT v3.1 — Arquitecto (Claude Opus) 2026-03-17. Auditoría ChatGPT: R1 8.6 → R2 9.2 → R3 9.6 (aprobado). 16 fixes acumulados.
