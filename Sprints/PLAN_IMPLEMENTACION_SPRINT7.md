# PLAN DE IMPLEMENTACIÓN — SPRINT 7 MWT ONE
**Fecha:** 2026-03-10  
**Agente asignado:** AG-03 Frontend (Antigravity)  
**Repositorio:** https://github.com/Ale241302/mwt_one  
**Stack:** Next.js 14 App Router · TypeScript · Tailwind CSS · react-hot-toast · lucide-react · date-fns  

---

## CONTEXTO Y REGLAS OBLIGATORIAS DE ESTILO

Antes de tocar cualquier archivo, Antigravity **DEBE** revisar y respetar los siguientes archivos como referencia de estilo canónico:

| Archivo de referencia | Por qué revisarlo |
|---|---|
| `frontend/src/app/(mwt)/globals.css` | Variables CSS: `--bg`, `--surface`, `--border`, `--mint`, `--coral`, `--navy`, `--amber`, etc. |
| `frontend/src/app/(mwt)/(dashboard)/expedientes/page.tsx` | Patrón de filtros, tabla, skeleton loading, badges de estado |
| `frontend/src/app/(mwt)/(dashboard)/expedientes/[id]/page.tsx` | Patrón de detalle, Timeline, Artifacts, Actions Panel, grid 2-col |
| `frontend/src/components/Sidebar.tsx` | Navegación lateral, clases activas |
| `frontend/src/components/PaymentsPanel.tsx` | Patrón de panels con datos financieros |
| `frontend/src/lib/api.ts` | Cliente axios configurado — SIEMPRE importar `api` desde aquí |

### Reglas de estilo NO negociables
- Usar **únicamente** clases Tailwind + variables CSS del `globals.css`
- Colores semánticos: `text-text-primary`, `text-text-secondary`, `text-text-tertiary`, `bg-surface`, `bg-bg-alt`, `border-border`
- Botones primarios: `bg-navy hover:bg-slate-800 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all shadow-sm active:scale-95`
- Botones destructivos: `bg-red-50 hover:bg-red-100 text-red-700 border border-red-200`
- Badges: `px-2.5 py-1 text-xs font-semibold rounded-full border shadow-sm`
- Cards/panels: `bg-surface rounded-2xl border border-border shadow-sm p-6`
- Drawers laterales: panel deslizable desde la derecha, fondo overlay `bg-black/40`, `w-full max-w-md`
- Skeleton loading con `animate-pulse` y `bg-border rounded`
- Siempre usar `toast` de `react-hot-toast` para feedback
- Headers de sección: `text-sm font-semibold text-text-secondary uppercase tracking-wider`

---

## ESTRUCTURA DE ARCHIVOS DEL SPRINT 7

### Archivos a CREAR (nuevos)

```
frontend/src/app/(mwt)/(dashboard)/expedientes/nuevo/
└── page.tsx                          ← Item 1: Formulario crear expediente

frontend/src/components/modals/
├── RegisterCostDrawer.tsx            ← Item 3: Drawer registrar costo
├── RegisterPaymentDrawer.tsx         ← Item 4: Drawer registrar pago
├── BlockUnblockModal.tsx             ← Item 5: Modal bloquear/desbloquear
├── CancelExpedienteModal.tsx         ← Item 6: Modal cancelar expediente
├── InvoiceModal.tsx                  ← Item 9: Modal generar factura ART-09
├── SupersederModal.tsx               ← Item 10: Modal superseder artefacto
├── VoidArtifactModal.tsx             ← Item 11: Modal void ART-09
└── ArtifactFormDrawer.tsx            ← Item 7: Drawer formularios artefactos

frontend/src/components/expediente/
├── PipelineActionsPanel.tsx          ← Item 2: Panel de acciones pipeline
├── CostsSection.tsx                  ← Item 8: Sección costos doble vista
└── DocumentMirrorPanel.tsx           ← Item 12: Espejo documental PDF
```

### Archivos a MODIFICAR (existentes)

```
frontend/src/app/(mwt)/(dashboard)/expedientes/[id]/page.tsx
  → Item 2: Reemplazar handleAction() stub por PipelineActionsPanel real
  → Item 3: Conectar botón "💰 Registrar Costo" → abrir RegisterCostDrawer
  → Item 4: Conectar lógica pago → abrir RegisterPaymentDrawer
  → Item 5: Conectar "Bloquear/Desbloquear Manual" → abrir BlockUnblockModal
  → Item 6: Agregar botón "Cancelar Expediente" → abrir CancelExpedienteModal
  → Item 7: En tabla Artefactos, agregar botón "Completar" → ArtifactFormDrawer
  → Item 8: Agregar sección <CostsSection> debajo de Artefacts grid
  → Item 9: Agregar botón "Emitir Factura MWT" condicional → InvoiceModal
  → Item 10: En tabla Artefactos, botón "Superseder" → SupersederModal
  → Item 11: En tabla Artefactos (ART-09), botón "Void" → VoidArtifactModal
  → Item 12: Agregar <DocumentMirrorPanel> al final de la página

frontend/src/app/(mwt)/(dashboard)/expedientes/page.tsx
  → Item 1: Agregar botón "+ Nuevo Expediente" → navegar a /expedientes/nuevo

frontend/src/components/Sidebar.tsx
  → Verificar que /expedientes esté en el nav y no requiera cambios de ruta

frontend/src/lib/api.ts
  → Agregar helpers tipados si se necesitan (opcional, no romper lo existente)
```

---

## TAREAS DETALLADAS POR ÍTEM

---

### ITEM 1 — Formulario Crear Expediente
**Branch:** `feat/sprint7-item1-crear-expediente`  
**Agente:** AG-03 Frontend  
**Dependencia:** `GET /api/clients/` + `POST /api/expedientes/` (C1) operativos  

#### Archivos a crear
- `frontend/src/app/(mwt)/(dashboard)/expedientes/nuevo/page.tsx`

#### Archivos a modificar
- `frontend/src/app/(mwt)/(dashboard)/expedientes/page.tsx` → agregar botón "+ Nuevo Expediente" en el header

#### Especificación de implementación

**`/expedientes/page.tsx` — Modificación del header:**
```tsx
// En el div flex del header, agregar junto al título:
<button
  onClick={() => router.push('/expedientes/nuevo')}
  className="bg-navy hover:bg-slate-800 text-white px-4 py-2 rounded-lg text-sm font-medium 
             transition-all shadow-sm active:scale-95 flex items-center gap-2"
>
  <Plus size={16} /> Nuevo Expediente
</button>
```

**`/expedientes/nuevo/page.tsx` — Página nueva:**
- Es página completa (no drawer), con botón "← Volver" arriba
- Card central `bg-surface rounded-2xl border border-border shadow-sm p-8 max-w-2xl mx-auto`
- Título: `text-2xl font-display font-bold` — "Nuevo Expediente"
- **Campos del formulario** (todos required salvo notes):
  - `client_id` — Select con loading spinner, poblar desde `GET /api/clients/`, placeholder "Seleccionar cliente..."
  - `brand` — Select enum: `SKECHERS | ON | SPEEDO | TOMS | ASICS | VIVAIA | TECMATER`
  - `mode` — Select enum: `IMPORTACION | EXPORTACION | COMISION`
  - `freight_mode` — Select enum: `MARITIMO | AEREO | TERRESTRE`
  - `dispatch_mode` — Select enum: `mwt | directo`
  - `price_basis` — Select enum: `CIF | FOB | EXW`
  - `notes` — Textarea opcional
- Submit → `POST /api/expedientes/` (C1)
- Éxito (201): `toast.success('Expediente creado')` + `router.push('/expedientes/{id}')`
- Error: `toast.error(error.response.data.detail || 'Error al crear')`

#### Criterios de éxito
- [ ] Botón "+ Nuevo Expediente" visible en `/expedientes`
- [ ] Formulario en ruta `/expedientes/nuevo` (no drawer)
- [ ] Select clientes con spinner y error handling
- [ ] Todos los enums con valores wire exactos
- [ ] Submit llama C1 → redirige a `/expedientes/{id}`
- [ ] Error handling si API retorna status ≠ 201

---

### ITEM 2 — Acciones Pipeline Funcionales
**Branch:** `feat/sprint7-item2-pipeline-actions`  
**Agente:** AG-03 Frontend  
**Dependencia:** Item 1. Verificar slugs en `urls.py`

#### Archivos a crear
- `frontend/src/components/expediente/PipelineActionsPanel.tsx`

#### Archivos a modificar
- `frontend/src/app/(mwt)/(dashboard)/expedientes/[id]/page.tsx` → reemplazar sección "⚡ Acciones Pipeline" con `<PipelineActionsPanel>`

#### Especificación de implementación

**Mapa de comandos → slugs de endpoint:**
```typescript
const COMMAND_ENDPOINTS: Record<string, string> = {
  'C6':  'confirm-production',
  'C7':  'start-preparation',
  'C8':  'confirm-preparation',
  'C9':  'register-dispatch',
  'C10': 'confirm-arrival',
  'C11': 'register-nationalization',
  'C12': 'register-delivery',
  'C13': 'close',  // verificar si C13 y C14 son el mismo endpoint
  'C14': 'close',
};
```

**Props del componente:**
```typescript
interface PipelineActionsPanelProps {
  expedienteId: string;
  availableActions: string[];
  isBlocked: boolean;
  status: string;
  onActionSuccess: () => void; // callback para refrescar bundle
}
```

**Comportamiento:**
- Si `isBlocked === true`: sección Pipeline oculta, mostrar badge `BLOQUEADO` con `Ban` icon
- Si `status === 'CANCELADO' || status === 'CERRADO'`: sección Pipeline ausente (no renderizar)
- Precondiciones no cumplidas → botón `disabled` con `title` tooltip explicativo
- Antes de ejecutar → Modal de confirmación genérico: "¿Confirmar acción {COMMAND_LABELS[cmd]}?"
- Post-ejecución: `toast.success(...)` + llamar `onActionSuccess()` para refrescar bundle + timeline actualizado
- Error: `toast.error(e.response?.data?.detail || 'Error al ejecutar')`

#### Criterios de éxito
- [ ] Cada botón llama `POST /api/expedientes/{id}/{command_slug}/`
- [ ] Modal de confirmación antes de ejecutar
- [ ] Expediente bloqueado → Pipeline oculto + badge BLOQUEADO
- [ ] Post-ejecución: refresh automático + timeline actualizado
- [ ] CANCELADO/CERRADO: sección Pipeline ausente

---

### ITEM 3 — Drawer Registrar Costo
**Branch:** `feat/sprint7-item3-registrar-costo`  
**Agente:** AG-03 Frontend  
**Dependencia:** `POST /api/expedientes/{id}/costs/` (C15) operativo

#### Archivos a crear
- `frontend/src/components/modals/RegisterCostDrawer.tsx`

#### Archivos a modificar
- `frontend/src/app/(mwt)/(dashboard)/expedientes/[id]/page.tsx` → botón "💰 Registrar Costo" abre el drawer

#### Especificación de implementación

**Props:**
```typescript
interface RegisterCostDrawerProps {
  open: boolean;
  onClose: () => void;
  expedienteId: string;
  onSuccess: () => void;
}
```

**Campos del formulario:**

| Campo | Tipo | Notas |
|---|---|---|
| `cost_type` | Select | `FLETE \| ADUANA \| ALMACENAJE \| SEGURO \| HONORARIOS \| OTRO` |
| `amount` | Number input | Positivo, 2 decimales |
| `currency` | Select | `USD \| COP \| EUR` |
| `phase` | Select | `PRODUCCION \| TRANSITO \| DESTINO \| GENERAL` |
| `description` | Textarea | Opcional |
| `visibility` | Toggle | `internal` (default) / `client` |

**Comportamiento del drawer:**
- Slide-in desde la derecha: `fixed inset-y-0 right-0 w-full max-w-md bg-surface shadow-xl z-50`
- Overlay: `fixed inset-0 bg-black/40 z-40`
- Append-only (no edición de costos pasados)
- Submit → `POST /api/expedientes/{id}/costs/`
- Éxito: `toast.success('Costo registrado')` + cerrar drawer + llamar `onSuccess()`
- Loading state en botón submit con spinner

#### Criterios de éxito
- [ ] Botón abre drawer lateral (no modal centrado)
- [ ] Todos los campos presentes con validación
- [ ] Toggle visibility interno/cliente funcional
- [ ] Submit llama C15, cierra drawer, refresca panel de costos
- [ ] Loading + error handling

---

### ITEM 4 — Drawer Registrar Pago
**Branch:** `feat/sprint7-item4-registrar-pago`  
**Agente:** AG-03 Frontend  
**Dependencia:** `GET /api/expedientes/{id}/financial-summary/` + `POST /api/expedientes/{id}/payments/` (C21)

> ⚠️ **RIESGO CRÍTICO:** Si `financial-summary` no existe en backend, bloquear este item y escalar al CEO.

#### Archivos a crear
- `frontend/src/components/modals/RegisterPaymentDrawer.tsx`

#### Archivos a modificar
- `frontend/src/app/(mwt)/(dashboard)/expedientes/[id]/page.tsx` → estado `paymentDrawerOpen` + render del drawer

#### Especificación del drawer

**Al abrir el drawer:** `GET /api/expedientes/{id}/financial-summary/` para mostrar header financiero:
```
Total Facturado: $X,XXX.XX  |  Total Pagado: $X,XXX.XX  |  Estado: [badge]
```
- Si `total_billed_client === 0`: mostrar "Total: pendiente de factura" en lugar del monto

**Campos del formulario:**

| Campo | Tipo | Notas |
|---|---|---|
| `amount` | Number input | Positivo |
| `currency` | Select | Pre-seleccionar moneda del expediente. Aviso amarillo si diferente |
| `method` | Select | `TRANSFERENCIA \| EFECTIVO \| CHEQUE \| CRYPTO` |
| `reference` | Text | Número de referencia |
| `payment_date` | Date input | Default: hoy |

**Badge de estado:** `payment_status` calculado por backend. Si `PAID`: badge verde `bg-mint-soft text-mint`

#### Criterios de éxito
- [ ] Header muestra `total_paid / total_billed_client / payment_status`
- [ ] Pre-selección de moneda + aviso si diferente
- [ ] Submit → C21, cierra drawer, refresca
- [ ] Si PAID: badge verde visible en detalle

---

### ITEM 5 — Modal Bloquear / Desbloquear
**Branch:** `feat/sprint7-item5-bloquear-desbloquear`  
**Agente:** AG-03 Frontend  
**Dependencia:** `POST .../block/` (C17) y `POST .../unblock/` (C18) operativos

#### Archivos a crear
- `frontend/src/components/modals/BlockUnblockModal.tsx`

#### Archivos a modificar
- `frontend/src/app/(mwt)/(dashboard)/expedientes/[id]/page.tsx` → reemplazar `toast('...')` en botón Bloquear/Desbloquear con el modal real

#### Especificación del modal

**Modal centrado** (`fixed inset-0 flex items-center justify-center z-50`):

**Si `isBlocked === false` → Bloquear:**
- Título: "⚠️ Bloquear Expediente"
- Textarea `block_reason` — obligatoria, mínimo 10 caracteres, contador de chars visible
- `blocked_by_type`: siempre `'CEO'` (hardcoded, no seleccionable por el usuario)
- Botón: `bg-red-600 hover:bg-red-700 text-white` — "Bloquear Expediente"
- `POST .../block/` con `{ block_reason, blocked_by_type: 'CEO' }`

**Si `isBlocked === true` → Desbloquear:**
- Título: "🔓 Desbloquear Expediente"
- Mostrar razón actual: `expediente.block_reason` en card gris de solo lectura
- Botón: `bg-mint hover:bg-mint-dark text-white` — "Desbloquear"
- `POST .../unblock/` (sin body)

**Post-acción:** `toast.success(...)` + cerrar modal + `fetchBundle()`

**Badge en header:** `is_blocked === true` → badge `animate-pulse` rojo con `Ban` icon y razón como `title` (tooltip)

**Bloqueo SYSTEM:** si `blocked_by_type === 'SYSTEM'`, mostrar razón auto-generada en badge, NO mostrar botón desbloquear (solo lectura)

#### Criterios de éxito
- [ ] Bloquear → modal con razón obligatoria (min 10 chars)
- [ ] Si bloqueado: botón cambia a "Desbloquear"
- [ ] Badge rojo BLOQUEADO en header con tooltip de razón
- [ ] SYSTEM: razón visible, no desbloqueable desde UI
- [ ] Post-acción: refresh del detalle

---

### ITEM 6 — Modal Cancelar Expediente
**Branch:** `feat/sprint7-item6-cancelar-expediente`  
**Agente:** AG-03 Frontend  
**Dependencia:** `POST .../cancel/` (C16) operativo

#### Archivos a crear
- `frontend/src/components/modals/CancelExpedienteModal.tsx`

#### Archivos a modificar
- `frontend/src/app/(mwt)/(dashboard)/expedientes/[id]/page.tsx` → agregar botón "Cancelar Expediente" en sección Ops/Admin (solo visible si status ∈ {REGISTRO, PRODUCCION, PREPARACION})

#### Especificación del modal

**Visibilidad del botón:**
```typescript
const CANCELLABLE_STATES = ['REGISTRO', 'PRODUCCION', 'PREPARACION'];
// Renderizar solo si: CANCELLABLE_STATES.includes(expediente.status)
```

**Botón disparador:** `bg-red-50 hover:bg-red-100 text-red-700 border border-red-200` con `XCircle` icon

**Modal centrado con advertencia:**
- Banner de advertencia naranja: "⚠️ Esta acción es irreversible. El expediente será marcado como CANCELADO."
- Textarea `cancel_reason` — obligatoria, **mínimo 20 caracteres**, contador visible
- Botón confirm: `bg-red-600 hover:bg-red-700 text-white` — "Cancelar Expediente"
- Botón secundario: "Volver" — `bg-surface border border-border`

**Post-cancelación:**
- `toast.success('Expediente cancelado')`
- `fetchBundle()` → status ahora `CANCELADO`
- Badge `CANCELADO` en header (gris oscuro)
- Sección Pipeline desaparece (lógica ya cubierta en Item 2)
- Botones Ops deshabilitados

#### Criterios de éxito
- [ ] Botón visible solo en REGISTRO, PRODUCCION, PREPARACION
- [ ] Razón obligatoria mínimo 20 chars
- [ ] Post-cancelación: badge CANCELADO, Pipeline desaparece

---

### ITEM 7 — Drawers Formularios de Artefactos (ART-01, 02, 05, 06, 07, 08)
**Branch:** `feat/sprint7-item7-formularios-artefactos`  
**Agente:** AG-03 Frontend  
**Dependencia:** Endpoints de artefactos operativos. ART-07 depende de ART-05 y ART-06.

#### Archivos a crear
- `frontend/src/components/modals/ArtifactFormDrawer.tsx` — componente único con `artifactType` como prop

#### Archivos a modificar
- `frontend/src/app/(mwt)/(dashboard)/expedientes/[id]/page.tsx` → en la tabla de Artefactos, agregar columna "Acción" con botón "Completar" para artefactos pendientes (solo lectura si `status === 'COMPLETED'`)

#### Especificación: formularios por artefacto

**ART-01 — Orden de Compra (multipart/form-data):**
- Endpoint: `POST /api/expedientes/{id}/artifacts/purchase-order/`
- Campos: `po_number` (text), `client_name` (text), `total_amount` (number), `currency` (select USD/COP/EUR), `po_date` (date), `notes` (textarea), `file` (input file, PDF opcional)
- `enctype="multipart/form-data"`

**ART-02 — Proforma MWT:**
- Endpoint: `POST /api/expedientes/{id}/artifacts/proforma/`
- Campos: `total_amount` (o `total_usd` — verificar backend), `currency`, `proforma_date`, `valid_until`, `notes`
- `comision_pactada` (number): visible **solo si** `expediente.mode === 'COMISION'`

**ART-05 — AWB / BL:**
- Endpoint: `POST /api/expedientes/{id}/artifacts/shipment/`
- Label dinámico: `freight_mode === 'AEREO'` → "AWB Number" | else → "BL Number"
- Campos: `tracking_number` (label dinámico), `carrier`, `departure_date`, `eta`
- Post-registro: `toast('⏱ Reloj de crédito iniciado', { icon: '🕐' })`

**ART-06 — Cotización Flete:**
- Endpoint: `POST /api/expedientes/{id}/artifacts/freight-quote/`
- Campos: `carrier`, `freight_cost` (number), `transit_days` (number), `eta` (date), `origin_port`, `destination_port`, `container_type`, `incoterm`

**ART-07 — Aprobación Despacho:**
- Endpoint: `POST /api/expedientes/{id}/artifacts/dispatch-approval/`
- **Precondición:** ART-05 y ART-06 deben estar `status === 'COMPLETED'`. Si no: botón disabled con tooltip "Requiere ART-05 y ART-06 completados"
- Campos: `approved_by`, `approval_date`, `notes`

**ART-08 — Documentos Aduanal (multipart):**
- Endpoint: `POST /api/expedientes/{id}/artifacts/customs/`
- **Visible solo si** `expediente.dispatch_mode === 'mwt'`
- Campos: `customs_agent`, `customs_cost` (number), `customs_declaration`, `tariff_code`, `tax_amount` (number), `dispatch_mode` (pre-relleno con `expediente.dispatch_mode`), `file` (PDF)

**Patrón de Drawer compartido:**
- Artefacto con `status === 'COMPLETED'`: solo lectura, renderizar `ArtifactPayloadCard` existente
- Artefacto `PENDING`: mostrar formulario
- Post-submit: `toast.success('Artefacto registrado')` + `fetchBundle()` + cerrar drawer

#### Criterios de éxito
- [ ] ART-01: campos correctos + upload PDF
- [ ] ART-02: comision_pactada solo si mode=COMISION
- [ ] ART-05: label dinámico AWB/BL + toast reloj crédito
- [ ] ART-07: disabled con tooltip si ART-05+ART-06 incompletos
- [ ] ART-08: solo si dispatch_mode=mwt
- [ ] Artefactos COMPLETED: solo lectura

---

### ITEM 8 — Costos Doble Vista en Detalle Expediente
**Branch:** `feat/sprint7-item8-costos-doble-vista`  
**Agente:** AG-03 Frontend  
**Dependencia:** Item 3. `GET /api/expedientes/{id}/costs/` + `GET /api/expedientes/{id}/financial-summary/`

> ⚠️ **BLOQUEADO** si `financial-summary` no existe en backend.

#### Archivos a crear
- `frontend/src/components/expediente/CostsSection.tsx`

#### Archivos a modificar
- `frontend/src/app/(mwt)/(dashboard)/expedientes/[id]/page.tsx` → agregar `<CostsSection expedienteId={id} onRegisterCost={() => setRegisterCostOpen(true)} />` debajo del grid de Artefactos

#### Especificación del componente

**Estado interno del componente:**
```typescript
const [view, setView] = useState<'internal' | 'client'>('internal');
const [costs, setCosts] = useState([]);
const [summary, setSummary] = useState(null);
```

**Header de la sección:**
- Toggle tabs: `Vista Interna` / `Vista Cliente`
- Botón `+ Registrar Costo` → callback `onRegisterCost`

**Vista Interna (`visibility === 'internal' || 'client'`):**
- Tabla con columnas: Tipo, Descripción, Fase, Monto, Visibilidad
- Footer: Total de costos + **Margen bruto** = `total_billed_client - total_costs`
- Si sin ART-09: Margen = `n/a` (no mostrar 0)

**Vista Cliente (`visibility === 'client'` únicamente):**
- Misma tabla pero solo líneas con `visibility === 'client'`
- Sin columna Margen

**Estilo de la tabla:** mismo patrón que tabla de Artefactos en `[id]/page.tsx`

#### Criterios de éxito
- [ ] Sección debajo de Artefactos
- [ ] Toggle Vista Interna / Vista Cliente funcional
- [ ] Margen = n/a si sin ART-09
- [ ] Botón "Registrar Costo" ancla al Drawer del Item 3

---

### ITEM 9 — Modal Generar Factura MWT (ART-09)
**Branch:** `feat/sprint7-item9-factura-mwt`  
**Agente:** AG-03 Frontend  
**Dependencia:** ART-01 y ART-02 completados. Item 7.

#### Archivos a crear
- `frontend/src/components/modals/InvoiceModal.tsx`

#### Archivos a modificar
- `frontend/src/app/(mwt)/(dashboard)/expedientes/[id]/page.tsx` → en sección Ops/Admin, agregar botón "Emitir Factura MWT" con lógica condicional

**Condición de visibilidad del botón:**
```typescript
const EN_DESTINO_OR_LATER = ['EN_DESTINO', 'FACTURADO', 'CERRADO'];
const canInvoice = EN_DESTINO_OR_LATER.includes(expediente.status)
  && artifacts.some(a => a.artifact_type === 'ART-01' && a.status === 'COMPLETED')
  && artifacts.some(a => a.artifact_type === 'ART-02' && a.status === 'COMPLETED')
  && !artifacts.some(a => a.artifact_type === 'ART-09' && a.status === 'COMPLETED');
```

**Si `canInvoice === false`:** botón disabled con tooltip descriptivo de qué falta

#### Especificación del modal

**Preview pre-emisión:**
- Card con: Cliente, Total (de ART-02), Incoterm, Comisión (si `mode === 'COMISION'`)
- IVA: solo si `dispatch_mode === 'mwt'` → mostrar campo `iva_rate` (default 19%)

**Campos editables:**
- `invoice_number` (text) — obligatorio
- `issued_date` (date) — default hoy
- `notes` (textarea) — opcional

**Endpoint:** `POST /api/expedientes/{id}/artifacts/invoice/`

**Post-emisión:**
- ART-09 en tabla con badge `Completed` verde
- Link PDF si `artifact.payload.file_url` existe
- Botón "Emitir Factura" desaparece (ya emitida, hasta que sea voided)

#### Criterios de éxito
- [ ] Botón disabled con tooltip si faltan OC/Proforma o estado < EN_DESTINO
- [ ] Modal preview con datos correctos
- [ ] IVA solo si dispatch_mode=mwt
- [ ] Post-emisión: badge Completed + link PDF

---

### ITEM 10 — Modal Superseder Artefacto
**Branch:** `feat/sprint7-item10-superseder-artefacto`  
**Agente:** AG-03 Frontend

#### Archivos a crear
- `frontend/src/components/modals/SupersederModal.tsx`

#### Archivos a modificar
- `frontend/src/app/(mwt)/(dashboard)/expedientes/[id]/page.tsx` → en tabla Artefactos, para artefactos COMPLETED (excepto ART-09), agregar botón "Superseder"

**Endpoint:** `POST /api/expedientes/{id}/artifacts/{artifact_id}/supersede/`

**Modal:**
- Advertencia: "El artefacto actual quedará en estado SUPERSEDED"
- Botón: "Confirmar Superseder" (rojo suave)
- Post-acción: `fetchBundle()`, artefacto aparece con badge `SUPERSEDED` (gris)

---

### ITEM 11 — Modal Void Artefacto (ART-09 únicamente)
**Branch:** `feat/sprint7-item11-void-artefacto`  
**Agente:** AG-03 Frontend

#### Archivos a crear
- `frontend/src/components/modals/VoidArtifactModal.tsx`

#### Archivos a modificar
- `frontend/src/app/(mwt)/(dashboard)/expedientes/[id]/page.tsx` → en tabla Artefactos, para `artifact_type === 'ART-09'` y `status === 'COMPLETED'`, agregar botón "Void"

**Endpoint:** `POST /api/expedientes/{id}/void-artifact/` con `{ artifact_type: 'ART-09' }`

**Modal:**
- Advertencia fuerte: "⚠️ Anular la factura tendrá consecuencias en el pipeline"
- Textarea `void_reason` obligatoria (min 15 chars)
- Botón: `bg-red-600 text-white` — "Anular Factura"
- Post-void: ART-09 badge `VOID` rojo + botón "Emitir Factura" vuelve a aparecer

---

### ITEM 12 — Espejo Documental PDF
**Branch:** `feat/sprint7-item12-espejo-documental`  
**Agente:** AG-03 Frontend

#### Archivos a crear
- `frontend/src/components/expediente/DocumentMirrorPanel.tsx`

#### Archivos a modificar
- `frontend/src/app/(mwt)/(dashboard)/expedientes/[id]/page.tsx` → agregar `<DocumentMirrorPanel>` al final de la página

**Endpoint:** `GET /api/expedientes/{id}/documents/` (o similar — verificar contra backend)

**Especificación del panel:**
- Card `bg-surface rounded-2xl border border-border shadow-sm`
- Header: "📄 Documentos" con badge count
- Grid de documentos: icono PDF, nombre, fecha, botón "Ver" (abre en nueva pestaña)
- Si vacío: empty state con `FileText` icon de lucide-react
- Skeleton loading mientras carga

---

### ITEM 13 — Tests Sprint 7
**Branch:** `feat/sprint7-item13-tests`  
**Agente:** AG-06 QA  

#### Tests requeridos por ítem

| Ítem | Tipo de test | Casos clave |
|---|---|---|
| Item 1 | Playwright E2E | Render form, select clientes carga, submit 201 → redirect, error 400 muestra toast |
| Item 2 | Playwright E2E | Cada botón pipeline llama endpoint correcto, modal confirmación aparece, expediente bloqueado oculta pipeline |
| Item 3 | React Testing Library | Drawer abre/cierra, validación campos, submit llama C15, error handling |
| Item 4 | React Testing Library | financial-summary se llama al abrir, campos correctos, aviso moneda diferente |
| Item 5 | React Testing Library | Block: validación min 10 chars. Unblock: POST correcto. SYSTEM: no botón desbloquear |
| Item 6 | React Testing Library | Botón oculto en TRANSITO, visible en REGISTRO, validación min 20 chars |
| Item 7 | React Testing Library | ART-02 comision field hidden/visible. ART-07 disabled sin ART-05+06. ART-08 hidden si dispatch≠mwt |
| Item 8 | React Testing Library | Toggle vista funciona, margen n/a sin ART-09, solo client en vista cliente |
| Item 9 | Playwright E2E | Botón disabled sin ART-01+02, modal preview correcto, IVA condicional, post-emisión badge |
| Items 10-11 | React Testing Library | Modal void ART-09 únicamente, superseder para otros artefactos |
| Item 12 | React Testing Library | Panel renderiza docs, empty state, links correctos |
| **Regresión** | Playwright E2E | Lista expedientes carga, detalle carga, timeline correcto, no romper artefactos ART-06/ART-08 existentes |

#### Archivos de test a crear
```
frontend/__tests__/
├── expedientes-nuevo.spec.tsx        ← Item 1
├── pipeline-actions.spec.tsx         ← Item 2
├── register-cost-drawer.spec.tsx     ← Item 3
├── register-payment-drawer.spec.tsx  ← Item 4
├── block-unblock-modal.spec.tsx      ← Item 5
├── cancel-expediente-modal.spec.tsx  ← Item 6
├── artifact-form-drawer.spec.tsx     ← Item 7
├── costs-section.spec.tsx            ← Item 8
├── invoice-modal.spec.tsx            ← Item 9
├── superseder-void-modal.spec.tsx    ← Items 10-11
└── document-mirror-panel.spec.tsx    ← Item 12
```

---

## ORDEN DE IMPLEMENTACIÓN RECOMENDADO

```
Fase 1 — Fundamentos (sin dependencias)
  Item 1 → Item 5 → Item 6

Fase 2 — Pipeline y Artefactos
  Item 2 → Item 7

Fase 3 — Financiero
  Item 3 → Item 4 → Item 8

Fase 4 — Documentos y Factura
  Item 9 (requiere Item 7) → Item 10 → Item 11 → Item 12

Fase 5 — QA
  Item 13 (corre sobre todo lo anterior)
```

---

## VERIFICACIONES PREVIAS (antes de empezar a codear)

Antigravity debe verificar estos endpoints en el backend antes de implementar cada ítem:

```bash
# Item 1
GET  /api/clients/
POST /api/expedientes/

# Item 2 — verificar slugs exactos
POST /api/expedientes/{id}/confirm-production/
POST /api/expedientes/{id}/start-preparation/
POST /api/expedientes/{id}/confirm-preparation/
POST /api/expedientes/{id}/register-dispatch/
POST /api/expedientes/{id}/confirm-arrival/
POST /api/expedientes/{id}/register-nationalization/
POST /api/expedientes/{id}/register-delivery/
POST /api/expedientes/{id}/close/

# Items 3, 8
POST /api/expedientes/{id}/costs/
GET  /api/expedientes/{id}/costs/
GET  /api/expedientes/{id}/financial-summary/   ← CRÍTICO: escalar si no existe

# Item 4
POST /api/expedientes/{id}/payments/

# Item 5
POST /api/expedientes/{id}/block/
POST /api/expedientes/{id}/unblock/

# Item 6
POST /api/expedientes/{id}/cancel/

# Item 7 — verificar slugs de artefactos
POST /api/expedientes/{id}/artifacts/purchase-order/
POST /api/expedientes/{id}/artifacts/proforma/
POST /api/expedientes/{id}/artifacts/shipment/
POST /api/expedientes/{id}/artifacts/freight-quote/
POST /api/expedientes/{id}/artifacts/dispatch-approval/
POST /api/expedientes/{id}/artifacts/customs/

# Item 9
POST /api/expedientes/{id}/artifacts/invoice/

# Items 10-11
POST /api/expedientes/{id}/artifacts/{artifact_id}/supersede/
POST /api/expedientes/{id}/void-artifact/
```

---

## RESUMEN DE ARCHIVOS

| Operación | Cantidad | Archivos |
|---|---|---|
| **CREAR** | 12 | `expedientes/nuevo/page.tsx` + 8 modals/drawers + 2 componentes expediente + 12 test files |
| **MODIFICAR** | 3 | `expedientes/[id]/page.tsx` (principal), `expedientes/page.tsx`, opcionalmente `api.ts` |
| **NO TOCAR** | — | `globals.css`, `Sidebar.tsx`, `layout.tsx`, `middleware.ts`, `api.ts` (salvo helpers) |
