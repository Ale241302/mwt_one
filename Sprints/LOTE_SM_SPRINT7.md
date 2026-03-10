# LOTE_SM_SPRINT7 — Frontend Operativo mwt.one
status: DRAFT — Pendiente aprobación CEO
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
tipo: Lote ruteado (ref → PLB_ORCHESTRATOR §E)
sprint: 7
priority: P0
depends_on: LOTE_SM_SPRINT6 (backend 39 endpoints funcionales — confirmado en producción)
refs: ENT_OPS_EXPEDIENTE, ENT_OPS_STATE_MACHINE, ENT_PLAT_ARTEFACTOS, ARTIFACT_REGISTRY, ENT_PLAT_FRONTENDS, ENT_COMERCIAL_MODELOS, ENT_PLAT_DESIGN_TOKENS

---

## Contexto y diagnóstico

Auditoría visual realizada el 2026-03-09 sobre consola.mwt.one con datos del seed_demo_data.py.

**Estado confirmado del frontend al inicio de Sprint 7:**

| Ruta Next.js | Página | Estado |
|---|---|---|
| `[lang]/(mwt)/(dashboard)/expedientes/page` | Lista expedientes | ✅ Funcional |
| `[lang]/(mwt)/(dashboard)/expedientes/[id]/page` | Detalle expediente | ✅ Parcial |
| `[lang]/(mwt)/(dashboard)/dashboard/financial/page` | Dashboard financiero | ✅ Parcial |
| Todas las demás | — | ❌ No existen |

**Gaps críticos confirmados:**
- Acciones Pipeline: botón presente pero sin handler — "No hay acciones disponibles" en todos los estados
- Registrar Costo: botón presente pero sin modal funcional
- Bloquear Manual: botón presente pero sin modal funcional
- No existe formulario crear expediente
- No existen formularios para ningún artefacto (OC, Proforma, AWB, etc.)
- No existe registro de pagos
- Costos doble vista ausente del detalle de expediente
- Financiero agregado únicamente por marca — sin desglose por expediente

**Precondición verificada:** Backend 100% operativo con 39 command endpoints POST + seed data cargado.

---

## Objetivo Sprint 7

Construir todo el frontend operativo que permita al CEO operar expedientes completos desde la UI — sin necesidad de Django Admin ni llamadas directas a la API. Al cierre del sprint, el CEO puede crear, avanzar, documentar, costear, cobrar y cerrar un expediente de principio a fin desde consola.mwt.one.

---

## Scope

### Incluido

| # | Feature | Prioridad | Agente |
|---|---------|-----------|--------|
| 1 | Formulario crear expediente | P0 | AG-03 Frontend |
| 2 | Acciones Pipeline funcionales (avanzar estado por comando) | P0 | AG-03 Frontend |
| 3 | Modal Registrar Costo (funcional) | P0 | AG-03 Frontend |
| 4 | Modal Registrar Pago (nuevo) | P0 | AG-03 Frontend |
| 5 | Modal Bloquear / Desbloquear (funcional) | P0 | AG-03 Frontend |
| 6 | Modal Cancelar expediente (nuevo) | P0 | AG-03 Frontend |
| 7 | Formularios de artefactos (OC, Proforma, AWB, Cotización flete, Aprobación despacho) | P0 | AG-03 Frontend |
| 8 | Costos doble vista en detalle expediente | P1 | AG-03 Frontend |
| 9 | Generar Factura MWT — ART-09 (modal + trigger) | P1 | AG-03 Frontend |
| 10 | Modal Superseder artefacto | P1 | AG-03 Frontend |
| 11 | Modal Void artefacto | P1 | AG-03 Frontend |
| 12 | Espejo documental PDF (trigger desde UI) | P2 | AG-03 Frontend |
| 13 | Tests Sprint 7 | P0 | AG-06 QA |

### Excluido (Sprint 8)

| Feature | Razón | Sprint |
|---------|-------|--------|
| Liquidación Marluvas (ART-10) UI | Módulo propio, scope separado | 8 |
| Transfers + Nodos UI | Módulo propio, scope separado | 8 |
| Consola QR | go.ranawalk.com DNS pendiente | 8 |
| Rana Walk en mwt.one (catálogo 54 SKUs) | Depende de transfers UI | 8 |
| RBAC / multi-usuario | Post-MVP | Post-MVP |
| Notificaciones push/email | Post-MVP | Post-MVP |

---

## Convenciones de UI

Reglas estables para todo el sprint. Alejandro no debe inventar patrones fuera de estos.

| Patrón | Regla |
|--------|-------|
| Acciones destructivas | Siempre modal de confirmación con campo razón obligatorio |
| Formularios | Componente drawer lateral (no página nueva) salvo crear expediente |
| Acciones Pipeline | Botón primario contextual según status — un solo botón visible a la vez |
| Costos doble vista | Toggle "Vista CEO / Vista Cliente" — CEO ve todo, cliente ve solo su columna |
| Estados bloqueados | Badge rojo "BLOQUEADO" en header del expediente, no solo en lista |
| Artefactos completados | No editables — solo superseder/void según reglas ART |
| Campos [CEO-ONLY] | Se renderizan siempre en la consola (MVP = un solo usuario, sin RBAC). La separación CEO/cliente aplica únicamente al PDF espejo (Item 12) y al toggle de costos (Item 8). No implementar lógica de role en el frontend durante Sprint 7. |
| Design tokens | Respetar ENT_PLAT_DESIGN_TOKENS en todos los componentes nuevos |

---

## Items

### Item 1 — Formulario crear expediente
**Agente:** AG-03 Frontend
**Endpoint creación:** `POST /api/expedientes/` (C1)
**Endpoint listado clientes:** `GET /api/clients/` → array `[{ id, name }]` — usado para poblar el select de client_id

**Ruta Next.js canónica:** `[lang]/(mwt)/(dashboard)/expedientes/nuevo/page`
URL en browser: `/es/expedientes/nuevo` (o `/en/`, `/pt/` según idioma activo)

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

**Criterio de done:**
- [ ] Botón "Nuevo Expediente" visible en `/expedientes` (header, esquina superior derecha)
- [ ] Formulario en página nueva (ruta canónica arriba) — no drawer
- [ ] Select de client_id carga desde `GET /api/clients/`; muestra spinner mientras carga, error si falla
- [ ] brand: select con valores wire exactos: `marluvas`, `tecmater`, `ranawalk`
- [ ] mode: select con valores wire exactos: `FULL`, `COMISION`. El valor `COMISION` solo aparece habilitado si `brand === "marluvas"`; si brand cambia a otro valor y mode era COMISION, resetear a FULL automáticamente
- [ ] freight_mode: select — `prepaid`, `postpaid`
- [ ] transport_mode: select — `aereo`, `maritimo`
- [ ] dispatch_mode: select — `mwt`, `client`
- [ ] Submit llama C1 con payload exacto, redirige al detalle del expediente creado (`/[lang]/expedientes/{id}`)
- [ ] Loading state en botón submit mientras espera respuesta
- [ ] Error handling: muestra mensaje de error de API si status ≠ 201

---

### Item 2 — Acciones Pipeline funcionales
**Agente:** AG-03 Frontend
**Endpoints:** C6 ConfirmProduction, C7 StartPreparation, C8 ConfirmPreparation, C9 RegisterDispatch, C10 ConfirmArrival, C11 RegisterNationalization, C12 RegisterDelivery, C13/C14 CloseExpediente

**Estructura de llamada (estándar para todos los commands de pipeline):**
```
POST /api/expedientes/{id}/{command_slug}/
Content-Type: application/json
Body: {}   ← vacío salvo que el command requiera payload adicional

Ejemplos:
POST /api/expedientes/{id}/confirm-production/
POST /api/expedientes/{id}/start-preparation/
POST /api/expedientes/{id}/confirm-preparation/
POST /api/expedientes/{id}/register-dispatch/
POST /api/expedientes/{id}/confirm-arrival/
POST /api/expedientes/{id}/register-nationalization/
POST /api/expedientes/{id}/register-delivery/
POST /api/expedientes/{id}/close/
```
Los slugs exactos deben verificarse contra el URL registry del backend (urls.py). Si Alejandro encuentra divergencia, corregir el slug — la lógica del command no cambia.
**Criterio de done:**
- [ ] Sección "Acciones Pipeline" muestra el botón correcto según status actual del expediente
- [ ] Mapa estado → comando → label del botón:

  | Status | Condición adicional | Comando | Label botón |
  |--------|---------------------|---------|-------------|
  | REGISTRO | — | C6 | "Confirmar Producción" |
  | PRODUCCION | — | C7 | "Iniciar Preparación" |
  | PREPARACION | `preparation_confirmed = false` | C8 | "Confirmar Preparación" |
  | PREPARACION | `preparation_confirmed = true` | C9 | "Registrar Despacho" |
  | DESPACHO | — | C10 | "Confirmar Llegada" |
  | EN_DESTINO | `dispatch_mode = mwt` | C11 | "Registrar Nacionalización" |
  | EN_DESTINO | `dispatch_mode = client` | C12 | "Registrar Entrega" |
  | NACIONALIZADO | — | C13 | "Cerrar Expediente" |
  | ENTREGADO | — | C14 | "Cerrar Expediente" |

  Regla para PREPARACION: el backend expone `preparation_confirmed` en el objeto expediente. El frontend lee este campo para decidir cuál de los dos botones mostrar. Un solo botón visible a la vez — nunca los dos simultáneamente.

  **Precondición de implementación:** el serializer de detalle de expediente debe exponer `preparation_confirmed: boolean`. Si el campo no existe con ese nombre exacto en la respuesta actual del backend, Alejandro usa el nombre wire real del serializer y corrige este lote antes de implementar. No inferir el valor en frontend a partir de artefactos, eventos o timeline.

  **Nota sobre cierre de expediente:** el backend puede exponer dos commands distintos (`close-nationalized` / `close-delivered`) o un único endpoint `/close/`. Regla de implementación: si el backend usa un único endpoint `/close/`, el frontend lo llama siempre independientemente del status. Si el backend expone dos endpoints distintos, el frontend selecciona C13 cuando status=NACIONALIZADO y C14 cuando status=ENTREGADO. Verificar contra `urls.py` antes de implementar.

  Regla para EN_DESTINO: C11 aplica cuando MWT nacionaliza (dispatch_mode=mwt), C12 cuando el cliente nacionaliza (dispatch_mode=client). El frontend lee `expediente.dispatch_mode` definido en el momento de creación.

  **Validación de contrato:** confirmar en ENT_OPS_STATE_MACHINE que para `dispatch_mode=client` el comando C12 RegisterDelivery es legal sin pasar por C11. Si el backend exige C11 en ambos dispatch modes, eliminar esta bifurcación, actualizar la tabla y dejar solo C11 → C12 como secuencia fija.

- [ ] Si precondiciones no están cumplidas: botón deshabilitado + tooltip explicando qué falta (ref → ENT_OPS_STATE_MACHINE para precondiciones por estado)
- [ ] Si expediente bloqueado: sección Pipeline oculta, solo se muestra badge BLOQUEADO
- [ ] Confirmación antes de ejecutar: modal simple "¿Confirmar avance a {estado_siguiente}?"
- [ ] Después de ejecutar: refresh automático del detalle, timeline actualizado
- [ ] Expediente CANCELADO o CERRADO: sección Pipeline ausente (flujo terminado)

---

### Item 3 — Modal Registrar Costo
**Agente:** AG-03 Frontend
**Endpoint:** `POST /api/expedientes/{id}/costs/` (C15)
**Criterio de done:**
- [ ] Botón "Registrar Costo" abre drawer lateral (no navega)
- [ ] Campos: cost_type (select con tipos canónicos: merchandise, freight_air, freight_sea, insurance, customs_dai, customs_iva, storage, handling, other), amount (numérico), currency (select cargado desde enum/backend config de monedas permitidas; si en Sprint 7 el backend expone solo USD/CRC/COP, usar exactamente esas tres y no agregar más), phase (select: REGISTRO/PRODUCCION/PREPARACION/DESPACHO/TRANSITO/EN_DESTINO), description (texto libre)
- [ ] Campo visibility: internal (default, [CEO-ONLY]) vs client — toggle
- [ ] Append-only: no hay edición de costos existentes
- [ ] Submit llama C15, cierra drawer, refresca panel de costos
- [ ] Loading + error handling

---

### Item 4 — Modal Registrar Pago
**Agente:** AG-03 Frontend
**Endpoint:** `POST /api/expedientes/{id}/payments/` (C21)
Nota: usar `/payments/` (plural) — consistente con el patrón `/costs/` y `/artifacts/` del mismo recurso.

**Precondición explícita Sprint 7:** el backend expone `GET /api/expedientes/{id}/financial-summary/` retornando `{ total_cost_internal, total_billed_client, total_paid, payment_status, currency }`. Si este endpoint no existe, QA debe bloquear la implementación de Items 4 y 8 y escalar al CEO antes de continuar.
**Criterio de done:**
- [ ] Botón "Registrar Pago" en sección Acciones Ops / Admin (junto a Registrar Costo)
- [ ] Campos: amount (numérico), currency (select), method (wire/check/liquidacion_marluvas/other), reference (texto libre), payment_date (date picker)
- [ ] Antes de abrir el drawer: `GET /api/expedientes/{id}/financial-summary/` → `{ total_cost_internal, total_billed_client, total_paid, payment_status, currency }`
- [ ] Header del drawer muestra: "Pagado hasta ahora: {total_paid} / Total facturado: {total_billed_client} — Estado: {payment_status}". Si `total_billed_client = 0` (sin factura aún): mostrar "Total: pendiente de factura".
- [ ] Regla de moneda: el campo currency del formulario debe pre-seleccionar la moneda de `financial-summary.currency`. Si el pago se registra en moneda diferente, mostrar aviso "Este pago se registrará en {moneda}, diferente a la moneda base del expediente ({moneda_base}). La conversión es responsabilidad del CEO." — no bloquear.
- [ ] `payment_status` se calcula en el backend: `PENDING` = nada pagado, `PARTIAL` = pagado > 0 y < total_billed_client, `PAID` = pagado ≥ total_billed_client. El frontend no calcula esto — solo lee el campo del summary.
- [ ] Submit llama C21, refresca estado de pago visible en el detalle
- [ ] Si payment_status llega a PAID: badge verde "PAGADO" en datos del expediente

---

### Item 5 — Modal Bloquear / Desbloquear
**Agente:** AG-03 Frontend
**Endpoints:** C17 BlockExpediente, C18 UnblockExpediente
**Criterio de done:**
- [ ] Botón "Bloquear Manual" → modal con campo razón obligatorio (min 10 chars). `blocked_by_type` se envía siempre como `CEO` — no es seleccionable; SYSTEM es exclusivamente auto-generado por el backend (crédito >75d) y nunca aparece como opción en UI
- [ ] Si expediente bloqueado: botón cambia a "Desbloquear" → modal simple con confirmación
- [ ] Badge "BLOQUEADO" en header del detalle cuando is_blocked=true
- [ ] Badge muestra razón del bloqueo como tooltip
- [ ] Expediente bloqueado por SYSTEM (crédito >75d): razón auto-generada visible
- [ ] Después de bloquear/desbloquear: refresh del detalle

---

### Item 6 — Modal Cancelar expediente
**Agente:** AG-03 Frontend
**Endpoint:** C16 CancelExpediente
**Criterio de done:**
- [ ] Botón "Cancelar Expediente" visible solo si status ∈ {REGISTRO, PRODUCCION, PREPARACION} (ref → ENT_OPS_STATE_MACHINE)
- [ ] Modal con advertencia "Esta acción no se puede deshacer", campo razón obligatorio (min 20 chars)
- [ ] Botón confirmar rojo, texto "Cancelar Expediente" (no "OK")
- [ ] Post-cancelación: status badge CANCELADO en detalle, sección Pipeline desaparece, acciones Ops deshabilitadas

---

### Item 7 — Formularios de artefactos
**Agente:** AG-03 Frontend

**Endpoints por artefacto:**

| Artefacto | Endpoint | Método |
|-----------|----------|--------|
| ART-01 Orden de Compra | `/api/expedientes/{id}/artifacts/po/` | POST |
| ART-02 Proforma MWT | `/api/expedientes/{id}/artifacts/proforma/` | POST |
| ART-05 AWB / BL | `/api/expedientes/{id}/artifacts/awb/` | POST |
| ART-06 Cotización flete | `/api/expedientes/{id}/artifacts/freight-quote/` | POST |
| ART-07 Aprobación despacho | `/api/expedientes/{id}/artifacts/dispatch-approval/` | POST |
| ART-08 Documentación aduanal | `/api/expedientes/{id}/artifacts/customs-docs/` | POST |

Los slugs deben verificarse contra el URL registry del backend. La lógica de negocio no cambia.

**Regla de transporte de archivos:** todo artefacto con upload usa `multipart/form-data`; artefactos sin archivos usan `application/json`. Si el backend usa flujo alterno de upload presignado (S3/MinIO direct upload), Alejandro debe documentarlo y escalar al CEO antes de implementar — este lote no asume ese flujo.

**Criterio de done:**

Cada artefacto pendiente en la lista del detalle de expediente tiene un botón "Completar" que abre su formulario específico. Artefactos ya completados muestran sus datos en modo lectura.

**(A) ART-01 Orden de Compra:**
- [ ] Campos: po_number (texto), client_name (texto), total_amount (numérico), currency, po_date (date), notes (texto libre)
- [ ] Upload opcional de PDF adjunto

**(B) ART-02 Proforma MWT:**
- [ ] Campos: consecutive (texto — número de proforma), total_amount (numérico — label UI: "Total Proforma"), currency (select — mismas opciones que Item 3), incoterm (select: FOB/CIF/DDP/DAP), comision_pactada (numérico % — solo visible si mode=COMISION), valid_until (date)
- [ ] Campo comision_pactada visible solo si expediente.mode = COMISION
- [ ] Nota wire: si el backend usa el campo histórico `total_usd` en lugar de `total_amount`, mantener el nombre wire en el payload pero mantener el label "Total Proforma" en UI. Verificar contra el serializer antes de implementar.

**(C) ART-05 AWB / BL:**
- [ ] Campos: carrier (texto), document_number (texto — label dinámico: "AWB #" si transport_mode=aereo, "BL #" si transport_mode=maritimo; pre-fill transport_mode desde expediente), etd (datetime), eta (datetime), origin (texto), destination (texto)
- [ ] El campo `transport_mode` se pre-llena desde `expediente.transport_mode` y es solo lectura en este formulario
- [ ] Payload wire: `{ carrier, document_number, transport_mode, etd, eta, origin, destination }`
- [ ] Al completar ART-05: reloj de crédito se activa automáticamente (backend lo maneja, frontend muestra "Reloj de crédito iniciado" en toast)

**(D) ART-06 Cotización flete:**
- [ ] Campos: provider (texto), amount (numérico), currency, validity_date (date), notes

**(E) ART-07 Aprobación despacho:**
- [ ] Campos: approved_by (texto — nombre del aprobador en cliente), approval_date (date), notes
- [ ] Requiere ART-05 + ART-06 completados — si faltan, botón deshabilitado con tooltip

**(F) ART-08 Documentación aduanal:**
- [ ] Solo visible si expediente.dispatch_mode = mwt
- [ ] Campos: doc_types (multi-select: DUA/BL/factura_comercial/certificado_origen/otros), customs_agent (texto), notes
- [ ] Upload múltiple de documentos

**(G) ART-09 Factura MWT (ver Item 9)**

**(H) ART-11 Registro costos:**
- [ ] Integrado en Item 3 (Registrar Costo) — no es formulario separado

---

### Item 8 — Costos doble vista en detalle expediente
**Agente:** AG-03 Frontend
**Endpoint:** `GET /api/expedientes/{id}/costs/`
**Criterio de done:**
- [ ] Sección "Costos" en detalle del expediente, debajo de Artefactos
- [ ] Toggle "Vista Interna / Vista Cliente" en header de la sección (ref → ENT_COMERCIAL_MODELOS.E1-E3)
- [ ] **Vista Interna [CEO-ONLY]:** tabla con todas las líneas — tipo, fase, monto, moneda, fecha, visibility. Total acumulado. Margen calculado como `total_billed_client − total_cost_internal`, usando datos de `GET /api/expedientes/{id}/financial-summary/` que retorna `{ total_cost_internal, total_billed_client, margin }`. Si ART-09 no existe aún, margen = n/a (no mostrar cero).
- [ ] **Vista Cliente:** solo líneas con visibility=client. Sin costos internos. Sin margen.
- [ ] Líneas de costo read-only (append-only — no hay edición)
- [ ] Botón "Registrar Costo" ancla al Item 3

---

### Item 9 — Generar Factura MWT (ART-09)
**Agente:** AG-03 Frontend
**Endpoint:** `POST /api/expedientes/{id}/artifacts/invoice/` (generación ART-09)
**Criterio de done:**
- [ ] Botón "Emitir Factura" visible solo si: estado ≥ EN_DESTINO **AND** ART-01 completado **AND** ART-02 completado. Si faltan, botón deshabilitado con tooltip "Completar OC y Proforma primero".
- [ ] Modal con preview de datos para revisión del CEO: cliente (desde ART-01.client_name), total (desde ART-02.total_amount o campo wire equivalente — ver serializer), incoterm (desde ART-02.incoterm), comisión pactada si mode=COMISION (desde ART-02.comision_pactada). Nota: ART-01 y ART-02 capturan totales, no líneas de producto individuales — el preview muestra totales, no desglose por SKU.
- [ ] IVA: solo mostrar si `expediente.dispatch_mode = mwt` (MWT nacionaliza = MWT aplica IVA). Si dispatch_mode=client, omitir campo IVA. Monto IVA ingresado manualmente por CEO en el modal (campo numérico opcional).
- [ ] Campos editables antes de emitir: invoice_number (texto), issued_date (date), notes (texto libre)
- [ ] Emitir genera ART-09 con status=completed
- [ ] Post-emisión: ART-09 aparece en lista de artefactos con badge "Completed" + link para ver PDF si `response.pdf_url` existe
- [ ] ART-09 solo puede tener una versión activa a la vez. Tras emisión inicial, el botón "Emitir Factura" desaparece. Si ART-09 es VOID (Item 11), el botón reaparece para permitir nueva emisión. Supersede (Item 10) reemplaza la versión activa sin void previo.

---

### Item 10 — Modal Superseder artefacto
**Agente:** AG-03 Frontend
**Endpoint:** C19 SupersedeArtifact
**Criterio de done:**
- [ ] En cada artefacto completado: menú contextual (⋯) con opción "Reemplazar"
- [ ] Modal: "Vas a reemplazar {tipo_artefacto}. Esto creará una nueva versión." + formulario del artefacto correspondiente (mismo form que Item 7)
- [ ] Si la transición ya ocurrió post-artefacto: advertencia adicional "El expediente ya avanzó. Reemplazar bloqueará el expediente temporalmente."
- [ ] En artefactos con archivo adjunto previo: el formulario de supersede no reutiliza el binario anterior. Si el artefacto requiere archivo, el usuario debe subir uno nuevo explícitamente. Mostrar referencia del artefacto previo (tipo + fecha) solo como lectura en el header del modal, no como campo editable.
- [ ] Backend maneja el bloqueo automático — frontend muestra estado resultante

---

### Item 11 — Modal Void artefacto
**Agente:** AG-03 Frontend
**Endpoint:** C20 VoidArtifact
**Criterio de done:**
- [ ] Artefactos voidables en Sprint 7: **únicamente ART-09** (Factura MWT). Ningún otro artefacto muestra opción "Anular" en este sprint.
- [ ] Menú contextual (⋯) en ART-09 completado con opción "Anular"
- [ ] Modal: "Vas a anular {tipo_artefacto}. Esta acción no se puede deshacer." + campo razón obligatorio (min 10 chars)
- [ ] Post-void: artefacto muestra badge "VOID" en lista, no desaparece. Botón "Emitir Factura" reaparece para permitir nueva emisión.

---

### Item 12 — Espejo documental PDF
**Agente:** AG-03 Frontend
**Endpoint:** `POST /api/expedientes/{id}/mirror-pdf/`
**Contrato de respuesta:** `{ "pdf_url": "https://..." }` — URL firmada (MinIO presigned URL), válida por 15 minutos
**Comportamiento tras respuesta:**
- Respuesta exitosa (200): abrir `pdf_url` en nueva pestaña (`window.open(pdf_url, '_blank')`)
- Si el backend retorna 202 (generación async): mostrar toast "Generando PDF..." + polling `GET /api/expedientes/{id}/mirror-pdf/status/` cada 3s. **Precondición:** este endpoint debe existir en el backend antes de implementar el flujo async. Si no existe, Sprint 7 implementa únicamente flujo síncrono 200 + pdf_url y se elimina el polling de este lote.

  Contrato de respuesta del endpoint status:
  ```json
  { "status": "pending" | "ready" | "error", "pdf_url": "https://..." | null }
  ```
  Regla frontend: `pending` → continuar polling; `ready` → abrir `pdf_url`; `error` → mostrar mensaje y detener. Timeout global a los 30s con mensaje de error.
- Error: mostrar mensaje inline en el botón, no toast flotante

**Criterio de done:**
- [ ] Botón "Generar Espejo PDF" en sección Acciones Ops / Admin
- [ ] Disponible solo si estado ≥ EN_DESTINO; deshabilitado con tooltip si es anterior
- [ ] El PDF generado excluye: costos con visibility=internal, campos marcados [CEO-ONLY] en el expediente, margen
- [ ] Incluye: datos del expediente visibles al cliente, códigos de cliente, artefactos con visibility=client
- [ ] Loading state en el botón mientras se genera (spinner + deshabilitar para evitar doble click)
- [ ] Comportamiento según contrato de respuesta arriba

---

### Item 13 — Tests Sprint 7
**Agente:** AG-06 QA
**Stack:** Jest + React Testing Library para unit/integration. Playwright para flujos E2E críticos (crear expediente → avanzar estado → registrar costo).
**Criterio de done:**
- [ ] Tests de integración para cada formulario: submit correcto → API call correcto → UI actualizada
- [ ] Tests de vista cliente: el toggle "Vista Cliente" en costos (Item 8) oculta líneas internal=true y no muestra margen
- [ ] Tests de estado: botones deshabilitados correctamente según status del expediente
- [ ] Tests de validación: campos requeridos, mínimos de caracteres en razones
- [ ] Suite mínima de regresión (Sprints 3-6) — AG-06 debe correr y dejar passing los siguientes antes de declarar Sprint 7 DONE:
  - Dashboard home carga KPIs correctamente (expedientes activos, alertas crédito, bloqueados)
  - Lista expedientes filtra por estado y marca
  - Detalle expediente muestra timeline, datos del expediente y lista de artefactos
  - Dashboard financiero muestra totales y desglose por marca
  - Navegación entre los 3 módulos existentes sin error 404
- [ ] Playwright E2E crítico: flujo completo REGISTRO → CERRADO con al menos un artefacto registrado

---

## Criterio global de done

Sprint 7 está DONE cuando:

1. El CEO puede crear un expediente nuevo desde consola.mwt.one sin tocar Django Admin
2. El CEO puede avanzar un expediente desde REGISTRO hasta CERRADO usando solo los botones del panel
3. El CEO puede registrar OC, Proforma y AWB desde la UI
4. El CEO puede registrar costos y pagos desde la UI
5. El CEO puede bloquear, desbloquear y cancelar desde la UI
6. La sección de costos muestra doble vista con toggle CEO/cliente
7. Todos los tests de Item 13 passing
8. Sin regresión en funcionalidad de Sprints 1-6
9. QA valida al menos dos flujos E2E completos: uno con `dispatch_mode=mwt` (REGISTRO → NACIONALIZADO → CERRADO) y otro con `dispatch_mode=client` (REGISTRO → ENTREGADO → CERRADO), cubriendo ambas ramas del pipeline en EN_DESTINO

---

## Qué queda para Sprint 8

| Feature | Razón |
|---------|-------|
| Liquidación Marluvas — upload Excel + reconciliación + aprobar/disputar | Módulo propio, scope separado |
| Transfers + Nodos — lista, crear transfer, ART-13/14/15 | Depende de UI base de Sprint 7 |
| Consola QR — CRUD 5 rutas, toggle is_active, historial scans | go.ranawalk.com DNS pendiente |
| Rana Walk en mwt.one — catálogo 54 SKUs, expediente bifurcación CR/USA | Depende de transfers UI |
| go.ranawalk.com resolver activo | DNS + backend ya implementado, falta DNS config |
| Manta en ranawalk.com | ENT_PROD_MTA no existe — crear KB primero |

---

Stamp: APROBADO — listo para ejecutar con Alejandro
Origen: Auditoría visual consola.mwt.one 2026-03-09 + diagnóstico chunks Next.js + sesión CEO
Auditoría: R1 Sonnet 4.6 (8.4) → 12 fixes | R1 Thinking 5.2 (8.6) → 1 fix | R2 Thinking 5.4 extended (9.2) → 10 fixes | R3 Thinking 5.4 extended (APROBADO) → 4 fixes finales
