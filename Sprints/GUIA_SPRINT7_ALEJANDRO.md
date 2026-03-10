# GUÍA DE EJECUCIÓN — Sprint 7 Frontend Operativo
**Para:** Alejandro (AG-03 Frontend + AG-06 QA)
**Fecha:** 2026-03-09
**Estado del documento:** APROBADO — listo para ejecutar
**Auditoría:** 4 rondas, 27 fixes, score final 9.7/10

---

## ANTES DE ESCRIBIR UNA LÍNEA DE CÓDIGO — 3 verificaciones obligatorias

Estas verificaciones deben hacerse contra el backend existente. Si alguna falla, escalar al CEO antes de continuar.

### ✅ Verificación 1 — Campo `preparation_confirmed` en serializer

Abrir el serializer de detalle de expediente y confirmar que expone este campo exacto:

```
preparation_confirmed: boolean
```

Si el campo existe con otro nombre, usar ese nombre wire real y corregir la tabla de pipeline de este documento. No inferirlo desde artefactos, eventos o timeline.

### ✅ Verificación 2 — Endpoint `financial-summary`

Confirmar que existe:

```
GET /api/expedientes/{id}/financial-summary/
```

Y que retorna exactamente:

```json
{
  "total_cost_internal": ...,
  "total_billed_client": ...,
  "total_paid": ...,
  "payment_status": "PENDING" | "PARTIAL" | "PAID",
  "currency": "USD" | "CRC" | "COP"
}
```

Si no existe: bloquear Items 4 y 8 y escalar al CEO.

### ✅ Verificación 3 — Commands de cierre (C13/C14)

Abrir `urls.py` y confirmar si el cierre usa:
- Un único endpoint `/close/` → el frontend siempre llama este, independientemente del status
- Dos endpoints distintos (`/close-nationalized/` y `/close-delivered/`) → el frontend elige según status (NACIONALIZADO → C13, ENTREGADO → C14)

---

## CONTEXTO DEL SISTEMA

### Stack
- Backend: Django + DRF — **100% implementado, 39 endpoints POST, en producción**
- Frontend: Next.js — **este sprint lo construye**
- Usuario único: CEO Alvaro — MVP sin RBAC, sin multi-usuario

### Estado del frontend al inicio del sprint (confirmado en producción)

| Ruta | Estado |
|------|--------|
| `/[lang]/expedientes` — lista | ✅ Funcional |
| `/[lang]/expedientes/[id]` — detalle | ✅ Parcial (botones sin handlers) |
| `/[lang]/dashboard/financial` — financiero | ✅ Parcial (solo vista agregada) |
| Todo lo demás | ❌ No existe |

### Objetivo del sprint

Al terminar, el CEO puede hacer todo esto **desde la UI, sin tocar Django Admin ni la API directamente:**

1. Crear un expediente nuevo
2. Avanzar un expediente desde REGISTRO hasta CERRADO
3. Registrar artefactos (OC, Proforma, AWB, Cotización, Aprobación)
4. Registrar costos y pagos
5. Bloquear, desbloquear y cancelar
6. Ver costos con toggle CEO/cliente
7. Emitir factura MWT
8. Generar espejo PDF para cliente

---

## PIPELINE DE ESTADOS

```
REGISTRO → PRODUCCION → PREPARACION → DESPACHO → EN_DESTINO → NACIONALIZADO → CERRADO
                                                              ↘ ENTREGADO    → CERRADO
Estados terminales: CANCELADO (desde REGISTRO, PRODUCCION o PREPARACION)
```

### Mapa estado → botón Pipeline (Item 2)

| Status actual | Condición | Endpoint | Label botón |
|---|---|---|---|
| REGISTRO | — | `POST .../confirm-production/` | "Confirmar Producción" |
| PRODUCCION | — | `POST .../start-preparation/` | "Iniciar Preparación" |
| PREPARACION | `preparation_confirmed = false` | `POST .../confirm-preparation/` | "Confirmar Preparación" |
| PREPARACION | `preparation_confirmed = true` | `POST .../register-dispatch/` | "Registrar Despacho" |
| DESPACHO | — | `POST .../confirm-arrival/` | "Confirmar Llegada" |
| EN_DESTINO | `dispatch_mode = mwt` | `POST .../register-nationalization/` | "Registrar Nacionalización" |
| EN_DESTINO | `dispatch_mode = client` | `POST .../register-delivery/` | "Registrar Entrega" |
| NACIONALIZADO | — | C13 (ver Verificación 3) | "Cerrar Expediente" |
| ENTREGADO | — | C14 (ver Verificación 3) | "Cerrar Expediente" |

**Regla:** un solo botón visible a la vez. Si el expediente está bloqueado, ocultar toda la sección Pipeline y mostrar solo badge BLOQUEADO.

**Validación de contrato (antes de implementar EN_DESTINO):** confirmar en ENT_OPS_STATE_MACHINE que para `dispatch_mode=client` el comando C12 es legal sin pasar por C11. Si el backend exige C11 en ambos dispatch modes, la bifurcación se elimina.

---

## CONVENCIONES DE UI — SEGUIR SIEMPRE

| Patrón | Regla |
|--------|-------|
| Formularios | Drawer lateral — SALVO crear expediente (página nueva) |
| Acciones destructivas | Modal con campo razón obligatorio |
| Pipeline | Un solo botón visible según status — nunca dos simultáneos |
| Campos CEO-ONLY | Se muestran siempre (MVP = 1 usuario, sin RBAC). La separación solo aplica al PDF espejo y al toggle de costos. NO implementar lógica de roles. |
| Artefactos completados | Solo lectura — excepto superseder/void |
| Estados bloqueados | Badge rojo "BLOQUEADO" en el header del detalle del expediente |
| Design tokens | Usar ENT_PLAT_DESIGN_TOKENS para todos los componentes nuevos |
| Upload de archivos | `multipart/form-data`. Sin archivos → `application/json`. Si el backend usa presigned upload (MinIO), escalar al CEO antes de implementar. |

---

## ITEMS — SPEC COMPLETA

### Item 1 — Formulario crear expediente (P0)

**Ruta Next.js:** `[lang]/(mwt)/(dashboard)/expedientes/nuevo/page`
**URL en browser:** `/es/expedientes/nuevo`

**Endpoints:**
```
GET /api/clients/           → [{ id, name }]  ← poblar select de clientes
POST /api/expedientes/      (C1)
```

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

**Reglas de negocio:**
- `COMISION` solo disponible si `brand === "marluvas"`. Si brand cambia, resetear mode a `FULL` automáticamente.

**Criterio de done:**
- [ ] Botón "Nuevo Expediente" en header de `/expedientes`, esquina superior derecha
- [ ] Formulario en página nueva (no drawer)
- [ ] Select clientes: spinner mientras carga, error visible si falla
- [ ] Todos los enums con valores wire exactos según payload arriba
- [ ] Submit: loading state → llama C1 → redirige a `/[lang]/expedientes/{id}`
- [ ] Error handling: mensaje visible si API retorna status ≠ 201

---

### Item 2 — Acciones Pipeline (P0)

**Patrón de llamada:**
```
POST /api/expedientes/{id}/{command_slug}/
Content-Type: application/json
Body: {}
```

Ver tabla de mapa en sección PIPELINE DE ESTADOS arriba.

**Criterio de done:**
- [ ] Botón Pipeline correcto según mapa de estados
- [ ] Precondiciones no cumplidas → botón deshabilitado + tooltip con qué falta
- [ ] Expediente bloqueado → sección Pipeline oculta, solo badge BLOQUEADO
- [ ] Modal de confirmación: "¿Confirmar avance a {estado_siguiente}?"
- [ ] Post-ejecución: refresh automático del detalle + timeline actualizado
- [ ] CANCELADO / CERRADO: sección Pipeline ausente

---

### Item 3 — Modal Registrar Costo (P0)

**Endpoint:** `POST /api/expedientes/{id}/costs/` (C15)

**Criterio de done:**
- [ ] Botón "Registrar Costo" → drawer lateral
- [ ] Campos:
  - `cost_type`: merchandise / freight_air / freight_sea / insurance / customs_dai / customs_iva / storage / handling / other
  - `amount`: numérico
  - `currency`: select desde enum backend (si solo expone USD/CRC/COP, usar esas tres)
  - `phase`: REGISTRO / PRODUCCION / PREPARACION / DESPACHO / TRANSITO / EN_DESTINO
  - `description`: texto libre
  - `visibility`: toggle internal (default) / client
- [ ] Append-only — sin edición de costos existentes
- [ ] Submit → cierra drawer → refresca panel de costos
- [ ] Loading + error handling

---

### Item 4 — Modal Registrar Pago (P0)

**Precondición:** `GET /api/expedientes/{id}/financial-summary/` debe existir (ver Verificación 2).

**Endpoints:**
```
GET /api/expedientes/{id}/financial-summary/   ← al abrir el drawer
POST /api/expedientes/{id}/payments/           (C21)
```

**Criterio de done:**
- [ ] Botón "Registrar Pago" en Acciones Ops / Admin
- [ ] Al abrir: llama financial-summary, muestra header del drawer:
  - Si `total_billed_client > 0`: "Pagado: {total_paid} / Total: {total_billed_client} — {payment_status}"
  - Si `total_billed_client = 0`: "Total: pendiente de factura"
- [ ] Campos: `amount`, `currency` (pre-seleccionar moneda de financial-summary), `method` (wire/check/liquidacion_marluvas/other), `reference`, `payment_date`
- [ ] Si moneda elegida ≠ moneda base: aviso "Conversión es responsabilidad del CEO" — no bloquear
- [ ] `payment_status` viene del backend — el frontend no calcula
- [ ] Post-submit: si payment_status = PAID → badge verde "PAGADO" en datos del expediente

---

### Item 5 — Modal Bloquear / Desbloquear (P0)

**Endpoints:** `POST .../block/` (C17), `POST .../unblock/` (C18)

**Criterio de done:**
- [ ] "Bloquear Manual" → modal con razón obligatoria (min 10 chars). `blocked_by_type` = `CEO` siempre (no seleccionable). SYSTEM es exclusivo del backend.
- [ ] Si bloqueado: botón cambia a "Desbloquear" → modal de confirmación simple
- [ ] Badge rojo "BLOQUEADO" en header del detalle cuando `is_blocked = true`
- [ ] Badge muestra razón como tooltip
- [ ] Bloqueo por SYSTEM (crédito >75d): razón auto-generada visible
- [ ] Post-acción: refresh del detalle

---

### Item 6 — Modal Cancelar expediente (P0)

**Endpoint:** C16 `POST .../cancel/`

**Criterio de done:**
- [ ] Botón visible SOLO si status ∈ {REGISTRO, PRODUCCION, PREPARACION}
- [ ] Modal: advertencia "Esta acción no se puede deshacer" + razón obligatoria (min 20 chars)
- [ ] Botón rojo que diga "Cancelar Expediente" (no "OK", no "Confirmar")
- [ ] Post-cancelación: badge CANCELADO, sección Pipeline desaparece, acciones Ops deshabilitadas

---

### Item 7 — Formularios de artefactos (P0)

**Endpoints por artefacto:**

| Artefacto | Endpoint | Content-Type |
|-----------|----------|--------------|
| ART-01 Orden de Compra | `POST .../artifacts/po/` | multipart/form-data |
| ART-02 Proforma MWT | `POST .../artifacts/proforma/` | application/json |
| ART-05 AWB / BL | `POST .../artifacts/awb/` | application/json |
| ART-06 Cotización flete | `POST .../artifacts/freight-quote/` | application/json |
| ART-07 Aprobación despacho | `POST .../artifacts/dispatch-approval/` | application/json |
| ART-08 Documentación aduanal | `POST .../artifacts/customs-docs/` | multipart/form-data |

Los slugs deben verificarse contra `urls.py`. La lógica de negocio no cambia.

Cada artefacto pendiente tiene botón "Completar" → abre drawer con su formulario.
Artefactos completados: solo lectura.

**(A) ART-01 Orden de Compra**
Campos: `po_number`, `client_name`, `total_amount`, `currency`, `po_date`, `notes`
Upload: PDF adjunto (opcional)

**(B) ART-02 Proforma MWT**
Campos: `consecutive`, `total_amount` (label UI: "Total Proforma"), `currency`, `incoterm` (FOB/CIF/DDP/DAP), `comision_pactada` (solo si `expediente.mode = COMISION`), `valid_until`
⚠️ Nota wire: si el backend usa el campo histórico `total_usd`, mantener ese nombre en el payload pero mostrar "Total Proforma" en UI. Verificar serializer.

**(C) ART-05 AWB / BL**
Campos: `carrier`, `document_number` (label dinámico: "AWB #" si aereo, "BL #" si maritimo), `etd`, `eta`, `origin`, `destination`
`transport_mode` pre-llenado desde expediente, solo lectura.
Payload: `{ carrier, document_number, transport_mode, etd, eta, origin, destination }`
Post-completar: toast "Reloj de crédito iniciado" (backend activa automáticamente).

**(D) ART-06 Cotización flete**
Campos: `provider`, `amount`, `currency`, `validity_date`, `notes`

**(E) ART-07 Aprobación despacho**
Campos: `approved_by`, `approval_date`, `notes`
Precondición: ART-05 + ART-06 completados. Si faltan → botón deshabilitado con tooltip.

**(F) ART-08 Documentación aduanal**
Solo visible si `expediente.dispatch_mode = mwt`.
Campos: `doc_types` (multi-select: DUA / BL / factura_comercial / certificado_origen / otros), `customs_agent`, `notes`
Upload múltiple de documentos.

---

### Item 8 — Costos doble vista (P1)

**Endpoints:**
```
GET /api/expedientes/{id}/costs/
GET /api/expedientes/{id}/financial-summary/
```

**Criterio de done:**
- [ ] Sección "Costos" en detalle, debajo de Artefactos
- [ ] Toggle "Vista Interna / Vista Cliente"
- [ ] **Vista Interna:** todas las líneas (tipo, fase, monto, moneda, fecha, visibility) + total acumulado + margen (`total_billed_client − total_cost_internal` desde financial-summary). Si ART-09 no existe: margen = "n/a" (nunca mostrar cero).
- [ ] **Vista Cliente:** solo líneas con `visibility = client`. Sin costos internos. Sin margen.
- [ ] Read-only. Botón "Registrar Costo" ancla al Item 3.

---

### Item 9 — Generar Factura MWT / ART-09 (P1)

**Endpoint:** `POST /api/expedientes/{id}/artifacts/invoice/`

**Reglas de visibilidad del botón "Emitir Factura":**
- Visible solo si: estado ≥ EN_DESTINO **AND** ART-01 completado **AND** ART-02 completado
- Si faltan: deshabilitado con tooltip "Completar OC y Proforma primero"
- ART-09 solo puede tener una versión activa a la vez:
  - Tras emisión: botón desaparece
  - Si ART-09 es VOID: botón reaparece
  - Supersede: reemplaza versión activa sin void previo

**Criterio de done:**
- [ ] Modal preview: cliente (ART-01.client_name), total (ART-02.total_amount o campo wire equivalente), incoterm (ART-02.incoterm), comisión si mode=COMISION
- [ ] IVA: campo visible SOLO si `dispatch_mode = mwt`. Si `dispatch_mode = client`, omitir campo IVA.
- [ ] Campos editables: `invoice_number`, `issued_date`, `notes`
- [ ] Post-emisión: ART-09 con badge "Completed" + link PDF si `response.pdf_url` existe

---

### Item 10 — Modal Superseder artefacto (P1)

**Endpoint:** C19 `POST .../supersede/`

**Criterio de done:**
- [ ] Menú contextual (⋯) en cada artefacto completado → opción "Reemplazar"
- [ ] Modal: "Vas a reemplazar {tipo}. Esto creará una nueva versión." + formulario correspondiente (mismo form que Item 7)
- [ ] Si expediente ya avanzó post-artefacto: advertencia adicional "El expediente ya avanzó. Reemplazar bloqueará el expediente temporalmente."
- [ ] Artefactos con archivo: formulario NO reutiliza el binario anterior. Usuario debe subir nuevo archivo explícitamente. Header del modal muestra referencia del artefacto previo (tipo + fecha) solo como lectura.
- [ ] Backend maneja bloqueo automático — frontend muestra estado resultante

---

### Item 11 — Modal Void artefacto (P1)

**Endpoint:** C20 `POST .../void/`

**Artefactos voidables en Sprint 7: ÚNICAMENTE ART-09.** Ningún otro artefacto muestra opción "Anular".

**Criterio de done:**
- [ ] Menú contextual (⋯) en ART-09 completado → opción "Anular"
- [ ] Modal: "Vas a anular {tipo}. Esta acción no se puede deshacer." + razón obligatoria (min 10 chars)
- [ ] Post-void: badge "VOID" en lista, no desaparece. Botón "Emitir Factura" reaparece.

---

### Item 12 — Espejo documental PDF (P2)

**Endpoints:**
```
POST /api/expedientes/{id}/mirror-pdf/
GET  /api/expedientes/{id}/mirror-pdf/status/   ← solo si backend usa 202 async
```

**Contrato de respuesta `POST /mirror-pdf/`:**
- 200 → `{ "pdf_url": "https://..." }` (MinIO presigned URL, válida 15 min) → abrir en nueva pestaña
- 202 → generación async → polling `GET .../mirror-pdf/status/` cada 3s

**⚠️ Precondición async:** si el backend no expone `/mirror-pdf/status/`, implementar SOLO el flujo síncrono 200 + pdf_url. Eliminar el polling.

**Contrato respuesta endpoint status:**
```json
{ "status": "pending" | "ready" | "error", "pdf_url": "https://..." | null }
```
- `pending` → continuar polling
- `ready` → abrir pdf_url
- `error` → mostrar mensaje y detener
- Timeout global: 30s

**El PDF excluye:** costos `visibility=internal`, campos CEO-ONLY, margen.
**El PDF incluye:** datos visibles al cliente, códigos de cliente, artefactos `visibility=client`.

**Criterio de done:**
- [ ] Botón "Generar Espejo PDF" en Acciones Ops / Admin
- [ ] Disponible solo si estado ≥ EN_DESTINO
- [ ] Loading state + deshabilitar botón mientras genera (evitar doble click)
- [ ] Error: mensaje inline en el botón (no toast)

---

### Item 13 — Tests Sprint 7 (P0)

**Stack:** Jest + React Testing Library (unit/integration) + Playwright (E2E)

**Criterio de done:**
- [ ] Tests de integración por formulario: submit correcto → API call correcto → UI actualizada
- [ ] Test toggle costos: "Vista Cliente" oculta líneas `visibility=internal` y no muestra margen
- [ ] Tests de estado: botones deshabilitados correctamente según status
- [ ] Tests de validación: campos requeridos, mínimos de caracteres
- [ ] Suite de regresión Sprint 3-6 (todos passing antes de declarar DONE):
  - Dashboard carga KPIs (expedientes activos, alertas crédito, bloqueados)
  - Lista expedientes filtra por estado y marca
  - Detalle muestra timeline, datos y artefactos
  - Financiero muestra totales y desglose por marca
  - Navegación sin error 404
- [ ] Playwright E2E: flujo REGISTRO → CERRADO con al menos un artefacto registrado

---

## CRITERIO GLOBAL DE DONE

Sprint 7 está DONE cuando:

1. CEO puede crear expediente desde UI (sin Django Admin)
2. CEO puede avanzar expediente de REGISTRO a CERRADO desde UI
3. CEO puede registrar OC, Proforma y AWB desde UI
4. CEO puede registrar costos y pagos desde UI
5. CEO puede bloquear, desbloquear y cancelar desde UI
6. Sección costos muestra doble vista con toggle CEO/cliente
7. Todos los tests de Item 13 passing
8. Sin regresión en Sprints 1-6
9. QA valida **dos flujos E2E completos**:
   - `dispatch_mode=mwt`: REGISTRO → NACIONALIZADO → CERRADO
   - `dispatch_mode=client`: REGISTRO → ENTREGADO → CERRADO

---

## SCOPE EXCLUIDO — NO TOCAR EN SPRINT 7

| Feature | Sprint |
|---------|--------|
| Liquidación Marluvas (ART-10) | 8 |
| Transfers + Nodos | 8 |
| Consola QR | 8 |
| Rana Walk en mwt.one | 8 |
| RBAC / multi-usuario | Post-MVP |
| Notificaciones push/email | Post-MVP |

---

## RIESGOS DOCUMENTADOS (no requieren acción ahora)

1. **`financial-summary`** — Si el backend cambia ese serializer, Items 4 y 8 se rompen simultáneamente. Tener en cuenta para Sprint 8.
2. **Uploads `multipart/form-data`** — Si el backend migra a presigned upload (MinIO), el frontend debe cambiar. Ya advertido en los formularios.
3. **`preparation_confirmed`** — Si el serializer cambia el nombre del campo, el pipeline se rompe. Documentado en Item 2.

---

Stamp: APROBADO — listo para ejecutar
Origen: LOTE_SM_SPRINT7 (aprobado) + verificación visual consola.mwt.one 2026-03-09
Auditoría lote: 4 rondas — Sonnet 4.6 (8.4) + Thinking 5.2 (8.6) + Thinking 5.4 extended (9.2 → APROBADO 9.7)
