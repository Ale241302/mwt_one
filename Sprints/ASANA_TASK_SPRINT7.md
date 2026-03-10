# ASANA_TASK_SPRINT7 — Frontend Operativo mwt.one

**Sprint:** 7
**Fecha:** 2026-03-09
**Estado:** APROBADO — listo para ejecutar
**Agentes:** AG-03 Frontend (Items 1-12) · AG-06 QA (Item 13)
**Fuentes:** LOTE_SM_SPRINT7 · GUIA_SPRINT7_ALEJANDRO
**Auditoría:** 4 rondas · 27 fixes · score final 9.7/10

---

## Contexto

Frontend operativo completo para que el CEO opere expedientes desde consola.mwt.one sin tocar Django Admin ni la API directamente. Backend 100% implementado con 39 command endpoints POST en producción.

**Estado del frontend al inicio de Sprint 7:**

| Ruta | Estado |
|------|--------|
| `/[lang]/expedientes` — lista | ✅ Funcional |
| `/[lang]/expedientes/[id]` — detalle | ✅ Parcial (botones sin handlers) |
| `/[lang]/dashboard/financial` — financiero | ✅ Parcial (solo vista agregada) |
| Todo lo demás | ❌ No existe |

**Gaps críticos confirmados:**
- Acciones Pipeline: botón presente pero sin handler
- Registrar Costo / Bloquear: botones sin modal funcional
- No existe formulario crear expediente
- No existen formularios de artefactos (OC, Proforma, AWB, etc.)
- No existe registro de pagos
- Costos doble vista ausente

---

## Verificaciones previas obligatorias (antes de escribir código)

| # | Verificación | Acción si falla |
|---|-------------|-----------------|
| V1 | `preparation_confirmed: boolean` expuesto en serializer de detalle | Usar nombre wire real y corregir tabla pipeline |
| V2 | `GET /api/expedientes/{id}/financial-summary/` retorna `{ total_cost_internal, total_billed_client, total_paid, payment_status, currency }` | Bloquear Items 4 y 8 · escalar al CEO |
| V3 | Confirmar en `urls.py` si cierre usa `/close/` único o dos endpoints `/close-nationalized/` + `/close-delivered/` | Ajustar implementación según resultado |

---

## Pipeline de estados

```
REGISTRO → PRODUCCION → PREPARACION → DESPACHO → EN_DESTINO → NACIONALIZADO → CERRADO
                                                              ↘ ENTREGADO    → CERRADO
Estados terminales: CANCELADO (desde REGISTRO, PRODUCCION o PREPARACION)
```

| Status actual | Condición | Comando | Label botón |
|---|---|---|---|
| REGISTRO | — | C6 `confirm-production/` | "Confirmar Producción" |
| PRODUCCION | — | C7 `start-preparation/` | "Iniciar Preparación" |
| PREPARACION | `preparation_confirmed = false` | C8 `confirm-preparation/` | "Confirmar Preparación" |
| PREPARACION | `preparation_confirmed = true` | C9 `register-dispatch/` | "Registrar Despacho" |
| DESPACHO | — | C10 `confirm-arrival/` | "Confirmar Llegada" |
| EN_DESTINO | `dispatch_mode = mwt` | C11 `register-nationalization/` | "Registrar Nacionalización" |
| EN_DESTINO | `dispatch_mode = client` | C12 `register-delivery/` | "Registrar Entrega" |
| NACIONALIZADO | — | C13 (ver V3) | "Cerrar Expediente" |
| ENTREGADO | — | C14 (ver V3) | "Cerrar Expediente" |

---

## Convenciones de UI

| Patrón | Regla |
|--------|-------|
| Formularios | Drawer lateral — SALVO crear expediente (página nueva) |
| Acciones destructivas | Modal con campo razón obligatorio |
| Pipeline | Un solo botón visible según status — nunca dos simultáneos |
| Campos CEO-ONLY | Se muestran siempre (MVP = 1 usuario, sin RBAC). Solo aplica separación en PDF espejo y toggle costos |
| Artefactos completados | Solo lectura — excepto superseder/void |
| Estados bloqueados | Badge rojo "BLOQUEADO" en header del detalle |
| Design tokens | Usar ENT_PLAT_DESIGN_TOKENS para todos los componentes nuevos |
| Upload archivos | `multipart/form-data`. Sin archivos → `application/json` |

---

## Scope incluido

| # | Feature | Prioridad | Agente |
|---|---------|-----------|--------|
| 1 | Formulario crear expediente | P0 | AG-03 Frontend |
| 2 | Acciones Pipeline funcionales | P0 | AG-03 Frontend |
| 3 | Modal Registrar Costo | P0 | AG-03 Frontend |
| 4 | Modal Registrar Pago | P0 | AG-03 Frontend |
| 5 | Modal Bloquear / Desbloquear | P0 | AG-03 Frontend |
| 6 | Modal Cancelar expediente | P0 | AG-03 Frontend |
| 7 | Formularios de artefactos (ART-01, 02, 05, 06, 07, 08) | P0 | AG-03 Frontend |
| 8 | Costos doble vista en detalle expediente | P1 | AG-03 Frontend |
| 9 | Generar Factura MWT — ART-09 | P1 | AG-03 Frontend |
| 10 | Modal Superseder artefacto | P1 | AG-03 Frontend |
| 11 | Modal Void artefacto | P1 | AG-03 Frontend |
| 12 | Espejo documental PDF | P2 | AG-03 Frontend |
| 13 | Tests Sprint 7 | P0 | AG-06 QA |

## Scope excluido (Sprint 8)

| Feature | Razón |
|---------|-------|
| Liquidación Marluvas (ART-10) UI | Módulo propio, scope separado |
| Transfers + Nodos UI | Módulo propio, scope separado |
| Consola QR | go.ranawalk.com DNS pendiente |
| Rana Walk en mwt.one (catálogo 54 SKUs) | Depende de transfers UI |
| RBAC / multi-usuario | Post-MVP |
| Notificaciones push/email | Post-MVP |

---

## Tareas detalladas

---

### TASK-S7-01 — Formulario crear expediente

**Agente:** AG-03 Frontend
**Prioridad:** P0
**Branch:** `feat/sprint7-item1-crear-expediente`
**Dependencias:** `GET /api/clients/` + `POST /api/expedientes/` (C1) operativos

**Descripción:**
Crear página nueva en Next.js para que el CEO cree expedientes desde la UI.

- **Ruta Next.js:** `[lang]/(mwt)/(dashboard)/expedientes/nuevo/page`
- **URL browser:** `/es/expedientes/nuevo`
- **Endpoints:** `GET /api/clients/` · `POST /api/expedientes/` (C1)

**Payload C1:**
```json
{
  "client_id": "<uuid>",
  "brand": "marluvas" | "tecmater" | "ranawalk",
  "mode": "FULL" | "COMISION",
  "freight_mode": "prepaid" | "postpaid",
  "transport_mode": "aereo" | "maritimo",
  "dispatch_mode": "mwt" | "client"
}
```

**Regla de negocio:** `COMISION` solo disponible si `brand === "marluvas"`. Si brand cambia, resetear mode a `FULL` automáticamente.

**Criterio de done:**
- [ ] Botón "Nuevo Expediente" en header de `/expedientes`, esquina superior derecha
- [ ] Formulario en página nueva (no drawer)
- [ ] Select clientes carga desde `GET /api/clients/`; spinner mientras carga, error visible si falla
- [ ] brand: `marluvas` / `tecmater` / `ranawalk`
- [ ] mode: `FULL` / `COMISION` — `COMISION` habilitado solo si brand=marluvas
- [ ] freight_mode: `prepaid` / `postpaid`
- [ ] transport_mode: `aereo` / `maritimo`
- [ ] dispatch_mode: `mwt` / `client`
- [ ] Submit: loading state → llama C1 → redirige a `/[lang]/expedientes/{id}`
- [ ] Error handling: mensaje visible si API retorna status ≠ 201

---

### TASK-S7-02 — Acciones Pipeline funcionales

**Agente:** AG-03 Frontend
**Prioridad:** P0
**Branch:** `feat/sprint7-item2-pipeline-actions`
**Dependencias:** Item 1. Verificar `preparation_confirmed` en serializer (V1) y slugs en `urls.py` (V3)

**Descripción:**
Implementar handlers para todos los botones de avance de estado. Patrón estándar:

```
POST /api/expedientes/{id}/{command_slug}/
Content-Type: application/json
Body: {}
```

Slugs canónicos (verificar contra `urls.py`):
`confirm-production/` · `start-preparation/` · `confirm-preparation/` · `register-dispatch/` · `confirm-arrival/` · `register-nationalization/` · `register-delivery/` · `close/`

**Criterio de done:**
- [ ] Sección "Acciones Pipeline" muestra el botón correcto según status actual
- [ ] Mapa estado → comando implementado según tabla de pipeline
- [ ] Un solo botón visible a la vez — nunca dos simultáneos
- [ ] Precondiciones no cumplidas → botón deshabilitado + tooltip explicando qué falta
- [ ] Expediente bloqueado → sección Pipeline oculta + badge BLOQUEADO
- [ ] Modal de confirmación: "¿Confirmar avance a {estado_siguiente}?"
- [ ] Post-ejecución: refresh automático del detalle + timeline actualizado
- [ ] Expediente CANCELADO o CERRADO: sección Pipeline ausente

**Riesgos:**
- `preparation_confirmed` puede tener nombre diferente en el serializer — verificar antes de implementar
- Backend puede usar `/close/` único o dos endpoints distintos — verificar `urls.py`
- Para `dispatch_mode=client`: confirmar en ENT_OPS_STATE_MACHINE que C12 es legal sin pasar por C11

---

### TASK-S7-03 — Modal Registrar Costo

**Agente:** AG-03 Frontend
**Prioridad:** P0
**Branch:** `feat/sprint7-item3-registrar-costo`
**Dependencias:** `POST /api/expedientes/{id}/costs/` (C15) operativo

**Descripción:**
Drawer lateral funcional para registrar costos en un expediente. Append-only — no hay edición de costos existentes.

**Campos del formulario:**
- `cost_type`: `merchandise` / `freight_air` / `freight_sea` / `insurance` / `customs_dai` / `customs_iva` / `storage` / `handling` / `other`
- `amount`: numérico
- `currency`: select — `USD` / `CRC` / `COP` (si backend expone solo esas tres, usar exactamente esas)
- `phase`: `REGISTRO` / `PRODUCCION` / `PREPARACION` / `DESPACHO` / `TRANSITO` / `EN_DESTINO`
- `description`: texto libre
- `visibility`: toggle `internal` (default, CEO-ONLY) / `client`

**Criterio de done:**
- [ ] Botón "Registrar Costo" abre drawer lateral (no navega)
- [ ] Todos los campos presentes con tipos correctos
- [ ] Toggle visibility: `internal` (default) / `client`
- [ ] Append-only — sin edición de costos existentes
- [ ] Submit llama C15, cierra drawer, refresca panel de costos
- [ ] Loading + error handling

---

### TASK-S7-04 — Modal Registrar Pago

**Agente:** AG-03 Frontend
**Prioridad:** P0
**Branch:** `feat/sprint7-item4-registrar-pago`
**Dependencias:** V2 — `GET /api/expedientes/{id}/financial-summary/` debe existir. `POST /api/expedientes/{id}/payments/` (C21)

**Descripción:**
Nuevo drawer lateral para registrar pagos. Muestra el estado financiero actual al abrirse.

**Endpoints:**
```
GET  /api/expedientes/{id}/financial-summary/   ← al abrir el drawer
POST /api/expedientes/{id}/payments/            (C21)
```

**Campos del formulario:**
- `amount`: numérico
- `currency`: select — pre-seleccionar moneda de `financial-summary.currency`
- `method`: `wire` / `check` / `liquidacion_marluvas` / `other`
- `reference`: texto libre
- `payment_date`: date picker

**Criterio de done:**
- [ ] Botón "Registrar Pago" en sección Acciones Ops / Admin
- [ ] Al abrir: llama `financial-summary`, muestra en header del drawer:
  - Si `total_billed_client > 0`: "Pagado: {total_paid} / Total: {total_billed_client} — {payment_status}"
  - Si `total_billed_client = 0`: "Total: pendiente de factura"
- [ ] Moneda pre-seleccionada desde financial-summary
- [ ] Si moneda elegida ≠ moneda base: aviso "Conversión es responsabilidad del CEO" — no bloquear
- [ ] `payment_status` viene del backend — el frontend no lo calcula
- [ ] Submit llama C21, refresca estado de pago en el detalle
- [ ] Si `payment_status = PAID`: badge verde "PAGADO" en datos del expediente

**Riesgo:** Si `financial-summary` no existe en backend → bloquear Items 4 y 8, escalar al CEO.

---

### TASK-S7-05 — Modal Bloquear / Desbloquear

**Agente:** AG-03 Frontend
**Prioridad:** P0
**Branch:** `feat/sprint7-item5-bloquear-desbloquear`
**Dependencias:** `POST .../block/` (C17) · `POST .../unblock/` (C18) operativos

**Descripción:**
Modales de bloqueo y desbloqueo manual de expediente. `blocked_by_type` = `CEO` siempre (no seleccionable). `SYSTEM` es exclusivo del backend (crédito >75d).

**Criterio de done:**
- [ ] "Bloquear Manual" → modal con razón obligatoria (min 10 chars)
- [ ] `blocked_by_type` enviado siempre como `CEO` — no es seleccionable
- [ ] Si expediente bloqueado: botón cambia a "Desbloquear" → modal de confirmación simple
- [ ] Badge rojo "BLOQUEADO" en header del detalle cuando `is_blocked = true`
- [ ] Badge muestra razón del bloqueo como tooltip
- [ ] Bloqueo por SYSTEM (crédito >75d): razón auto-generada visible
- [ ] Post-acción: refresh del detalle

---

### TASK-S7-06 — Modal Cancelar expediente

**Agente:** AG-03 Frontend
**Prioridad:** P0
**Branch:** `feat/sprint7-item6-cancelar-expediente`
**Dependencias:** `POST .../cancel/` (C16) operativo

**Descripción:**
Modal de cancelación. Solo disponible en estados tempranos del expediente.

**Criterio de done:**
- [ ] Botón "Cancelar Expediente" visible SOLO si status ∈ `{REGISTRO, PRODUCCION, PREPARACION}`
- [ ] Modal con advertencia "Esta acción no se puede deshacer"
- [ ] Razón obligatoria (min 20 chars)
- [ ] Botón confirmar rojo con texto "Cancelar Expediente" (no "OK", no "Confirmar")
- [ ] Post-cancelación: badge CANCELADO en detalle, sección Pipeline desaparece, acciones Ops deshabilitadas

---

### TASK-S7-07 — Formularios de artefactos (ART-01, 02, 05, 06, 07, 08)

**Agente:** AG-03 Frontend
**Prioridad:** P0
**Branch:** `feat/sprint7-item7-formularios-artefactos`
**Dependencias:** Endpoints de artefactos operativos. ART-07 depende de ART-05 + ART-06 completados.

**Descripción:**
Drawers con formularios específicos por artefacto. Cada artefacto pendiente tiene botón "Completar". Artefactos ya completados: solo lectura.

**Endpoints por artefacto:**

| Artefacto | Endpoint | Content-Type |
|-----------|----------|--------------|
| ART-01 Orden de Compra | `POST .../artifacts/po/` | multipart/form-data |
| ART-02 Proforma MWT | `POST .../artifacts/proforma/` | application/json |
| ART-05 AWB / BL | `POST .../artifacts/awb/` | application/json |
| ART-06 Cotización flete | `POST .../artifacts/freight-quote/` | application/json |
| ART-07 Aprobación despacho | `POST .../artifacts/dispatch-approval/` | application/json |
| ART-08 Documentación aduanal | `POST .../artifacts/customs-docs/` | multipart/form-data |

⚠️ Verificar slugs contra `urls.py` antes de implementar.

**Criterio de done — por artefacto:**

**(A) ART-01 Orden de Compra:**
- [ ] Campos: `po_number`, `client_name`, `total_amount`, `currency`, `po_date`, `notes`
- [ ] Upload opcional de PDF adjunto

**(B) ART-02 Proforma MWT:**
- [ ] Campos: `consecutive`, `total_amount` (label UI: "Total Proforma"), `currency`, `incoterm` (FOB/CIF/DDP/DAP), `comision_pactada`, `valid_until`
- [ ] `comision_pactada` visible solo si `expediente.mode = COMISION`
- [ ] ⚠️ Si backend usa `total_usd` históricamente, mantener nombre wire pero mostrar "Total Proforma" en UI

**(C) ART-05 AWB / BL:**
- [ ] Campos: `carrier`, `document_number` (label dinámico: "AWB #" si aereo / "BL #" si maritimo), `etd`, `eta`, `origin`, `destination`
- [ ] `transport_mode` pre-llenado desde expediente, solo lectura
- [ ] Post-completar: toast "Reloj de crédito iniciado"

**(D) ART-06 Cotización flete:**
- [ ] Campos: `provider`, `amount`, `currency`, `validity_date`, `notes`

**(E) ART-07 Aprobación despacho:**
- [ ] Campos: `approved_by`, `approval_date`, `notes`
- [ ] Requiere ART-05 + ART-06 completados — si faltan, botón deshabilitado con tooltip

**(F) ART-08 Documentación aduanal:**
- [ ] Solo visible si `expediente.dispatch_mode = mwt`
- [ ] Campos: `doc_types` (multi-select: DUA / BL / factura_comercial / certificado_origen / otros), `customs_agent`, `notes`
- [ ] Upload múltiple de documentos

**Riesgos:**
- ART-02: backend puede usar `total_usd` en lugar de `total_amount` — verificar serializer
- Slugs de endpoints pueden diferir — verificar `urls.py`

---

### TASK-S7-08 — Costos doble vista en detalle expediente

**Agente:** AG-03 Frontend
**Prioridad:** P1
**Branch:** `feat/sprint7-item8-costos-doble-vista`
**Dependencias:** Item 3 (Registrar Costo). V2 — `financial-summary` debe existir.

**Descripción:**
Sección "Costos" en el detalle del expediente con toggle Vista Interna / Vista Cliente.

**Endpoints:**
```
GET /api/expedientes/{id}/costs/
GET /api/expedientes/{id}/financial-summary/
```

**Criterio de done:**
- [ ] Sección "Costos" en detalle, debajo de Artefactos
- [ ] Toggle "Vista Interna / Vista Cliente" en header de la sección
- [ ] **Vista Interna [CEO-ONLY]:** tabla con todas las líneas (tipo, fase, monto, moneda, fecha, visibility) + total acumulado + margen (`total_billed_client − total_cost_internal`). Si ART-09 no existe aún: margen = "n/a" (nunca mostrar cero)
- [ ] **Vista Cliente:** solo líneas con `visibility = client`. Sin costos internos. Sin margen.
- [ ] Read-only. Botón "Registrar Costo" ancla al Item 3

**Riesgo:** Bloqueado si `financial-summary` no existe en backend.

---

### TASK-S7-09 — Generar Factura MWT (ART-09)

**Agente:** AG-03 Frontend
**Prioridad:** P1
**Branch:** `feat/sprint7-item9-factura-mwt`
**Dependencias:** ART-01 y ART-02 completados. Item 7.

**Descripción:**
Modal para emitir la Factura MWT (ART-09). Solo disponible cuando el expediente tiene suficiente avance.

**Endpoint:** `POST /api/expedientes/{id}/artifacts/invoice/`

**Visibilidad del botón "Emitir Factura":**
- Visible solo si: estado ≥ EN_DESTINO **AND** ART-01 completado **AND** ART-02 completado
- Si faltan: deshabilitado con tooltip "Completar OC y Proforma primero"
- Tras emisión: botón desaparece hasta que ART-09 sea VOID

**Criterio de done:**
- [ ] Modal preview: cliente (ART-01.client_name), total (ART-02.total_amount), incoterm (ART-02.incoterm), comisión si mode=COMISION
- [ ] IVA: campo visible SOLO si `dispatch_mode = mwt`. Si `dispatch_mode = client`, omitir.
- [ ] Campos editables: `invoice_number`, `issued_date`, `notes`
- [ ] Post-emisión: ART-09 en lista con badge "Completed" + link PDF si `response.pdf_url` existe
- [ ] ART-09 solo una versión activa a la vez

---

### TASK-S7-10 — Modal Superseder artefacto

**Agente:** AG-03 Frontend
**Prioridad:** P1
**Branch:** `feat/sprint7-item10-superseder-artefacto`
**Dependencias:** Item 7 (formularios de artefactos). C19 SupersedeArtifact operativo.

**Descripción:**
Opción "Reemplazar" en menú contextual (⋯) de cada artefacto completado. Reutiliza los mismos formularios de Item 7.

**Endpoint:** `POST .../supersede/` (C19)

**Criterio de done:**
- [ ] Menú contextual (⋯) en cada artefacto completado → opción "Reemplazar"
- [ ] Modal: "Vas a reemplazar {tipo}. Esto creará una nueva versión." + formulario correspondiente
- [ ] Si expediente ya avanzó post-artefacto: advertencia adicional "El expediente ya avanzó. Reemplazar bloqueará el expediente temporalmente."
- [ ] Artefactos con archivo: usuario debe subir nuevo archivo explícitamente — formulario NO reutiliza binario anterior
- [ ] Header del modal: referencia del artefacto previo (tipo + fecha) en solo lectura
- [ ] Backend maneja bloqueo automático — frontend muestra estado resultante

---

### TASK-S7-11 — Modal Void artefacto (ART-09 únicamente)

**Agente:** AG-03 Frontend
**Prioridad:** P1
**Branch:** `feat/sprint7-item11-void-artefacto`
**Dependencias:** Item 9 (ART-09 emitido). C20 VoidArtifact operativo.

**Descripción:**
Opción "Anular" en menú contextual de ART-09. **En Sprint 7: ÚNICAMENTE ART-09 es voidable.** Ningún otro artefacto muestra esta opción.

**Endpoint:** `POST .../void/` (C20)

**Criterio de done:**
- [ ] Menú contextual (⋯) en ART-09 completado → opción "Anular"
- [ ] Modal: "Vas a anular {tipo}. Esta acción no se puede deshacer." + razón obligatoria (min 10 chars)
- [ ] Post-void: artefacto muestra badge "VOID" en lista (no desaparece)
- [ ] Botón "Emitir Factura" reaparece para permitir nueva emisión

---

### TASK-S7-12 — Espejo documental PDF

**Agente:** AG-03 Frontend
**Prioridad:** P2
**Branch:** `feat/sprint7-item12-espejo-pdf`
**Dependencias:** Estado ≥ EN_DESTINO. `POST /api/expedientes/{id}/mirror-pdf/` operativo.

**Descripción:**
Trigger de generación del espejo PDF para el cliente. Soporta flujo síncrono (200) y asíncrono (202 + polling).

**Endpoints:**
```
POST /api/expedientes/{id}/mirror-pdf/
GET  /api/expedientes/{id}/mirror-pdf/status/   ← solo si backend usa 202 async
```

**Comportamiento según respuesta:**
- `200` → `{ pdf_url }` → abrir en nueva pestaña (`window.open(pdf_url, '_blank')`)
- `202` → polling `GET .../mirror-pdf/status/` cada 3s, timeout 30s
  - `pending` → continuar polling
  - `ready` → abrir `pdf_url`
  - `error` → mostrar mensaje y detener

**El PDF excluye:** costos `visibility=internal`, campos CEO-ONLY, margen.
**El PDF incluye:** datos visibles al cliente, códigos de cliente, artefactos `visibility=client`.

**Criterio de done:**
- [ ] Botón "Generar Espejo PDF" en Acciones Ops / Admin
- [ ] Disponible solo si estado ≥ EN_DESTINO; deshabilitado con tooltip si anterior
- [ ] Loading state + deshabilitar botón mientras genera (evitar doble click)
- [ ] Error: mensaje inline en el botón (no toast flotante)

**Riesgo:** Si `/mirror-pdf/status/` no existe en backend → implementar solo flujo síncrono 200 + pdf_url.

---

### TASK-S7-13 — Tests Sprint 7

**Agente:** AG-06 QA
**Prioridad:** P0
**Branch:** `feat/sprint7-item13-tests`
**Dependencias:** Items 1-12 completados.

**Stack:** Jest + React Testing Library (unit/integration) · Playwright (E2E)

**Criterio de done:**
- [ ] Tests de integración por formulario: submit correcto → API call correcto → UI actualizada
- [ ] Test toggle costos: "Vista Cliente" oculta líneas `visibility=internal` y no muestra margen
- [ ] Tests de estado: botones deshabilitados correctamente según status del expediente
- [ ] Tests de validación: campos requeridos, mínimos de caracteres en razones

**Suite de regresión Sprints 3-6 (todos passing antes de declarar DONE):**
- [ ] Dashboard home carga KPIs correctamente (expedientes activos, alertas crédito, bloqueados)
- [ ] Lista expedientes filtra por estado y marca
- [ ] Detalle expediente muestra timeline, datos del expediente y lista de artefactos
- [ ] Dashboard financiero muestra totales y desglose por marca
- [ ] Navegación entre los 3 módulos existentes sin error 404

**Playwright E2E:**
- [ ] Flujo completo REGISTRO → CERRADO con al menos un artefacto registrado
- [ ] Flujo `dispatch_mode=mwt`: REGISTRO → NACIONALIZADO → CERRADO
- [ ] Flujo `dispatch_mode=client`: REGISTRO → ENTREGADO → CERRADO

---

## Criterio global de done

Sprint 7 está DONE cuando:

1. CEO puede crear expediente desde UI (sin Django Admin)
2. CEO puede avanzar expediente de REGISTRO a CERRADO desde UI
3. CEO puede registrar OC, Proforma y AWB desde UI
4. CEO puede registrar costos y pagos desde UI
5. CEO puede bloquear, desbloquear y cancelar desde UI
6. Sección costos muestra doble vista con toggle CEO/cliente
7. Todos los tests de Item 13 passing
8. Sin regresión en Sprints 1-6
9. QA valida dos flujos E2E completos:
   - `dispatch_mode=mwt`: REGISTRO → NACIONALIZADO → CERRADO
   - `dispatch_mode=client`: REGISTRO → ENTREGADO → CERRADO

---

## Riesgos documentados

| # | Riesgo | Impacto | Mitigación |
|---|--------|---------|------------|
| R1 | `financial-summary` cambia serializer | Items 4 y 8 se rompen simultáneamente | Verificación V2 obligatoria antes de implementar |
| R2 | Backend migra a presigned upload MinIO | Formularios con archivo deben cambiar | Escalar al CEO si se detecta — no asumir flujo |
| R3 | `preparation_confirmed` cambia de nombre | Pipeline roto en PREPARACION | Verificación V1 obligatoria antes de implementar |

---

## Qué queda para Sprint 8

| Feature | Razón |
|---------|-------|
| Liquidación Marluvas — upload Excel + reconciliación + aprobar/disputar | Módulo propio, scope separado |
| Transfers + Nodos — lista, crear transfer, ART-13/14/15 | Depende de UI base de Sprint 7 |
| Consola QR — CRUD 5 rutas, toggle is_active, historial scans | go.ranawalk.com DNS pendiente |
| Rana Walk en mwt.one — catálogo 54 SKUs, expediente bifurcación CR/USA | Depende de transfers UI |
| go.ranawalk.com resolver activo | DNS + backend implementado, falta DNS config |
| Manta en ranawalk.com | ENT_PROD_MTA no existe — crear KB primero |

---

Stamp: FROZEN v1.0 — generado 2026-03-09
Origen: LOTE_SM_SPRINT7 (APROBADO) + GUIA_SPRINT7_ALEJANDRO (APROBADO 9.7/10)
