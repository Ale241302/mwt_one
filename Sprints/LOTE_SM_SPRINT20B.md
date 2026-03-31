# LOTE_SM_SPRINT20B — Frontend Policy-Driven + Vista Proformas
id: LOTE_SM_SPRINT20B
version: 1.8
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
status: DRAFT — Pendiente aprobación CEO
stamp: DRAFT v1.8 — 2026-03-30
tipo: Lote ruteado (ref → PLB_ORCHESTRATOR §E)
sprint: 20B
priority: P0
depends_on: LOTE_SM_SPRINT20 (DONE v1.6 — 35/35 tests, 0 regresiones)
refs: DIRECTRIZ_ARTEFACTOS_MODULARES (VIGENTE, HR-1 a HR-6, Parte VI),
      LOTE_SM_SPRINT20 v1.6 DONE (ArtifactPolicy en bundle, endpoints proformas, reassign-line),
      Resumen_sprint20.md (confirmación ejecución 100%),
      LOTE_SM_SPRINT9 (ArtifactModal pattern, ExpedienteAccordion original),
      ENT_PLAT_DESIGN_TOKENS,
      POL_ARTIFACT_CONTRACT (VIGENTE v1.0)

changelog:
  - v1.0 (2026-03-30): Compilación inicial. 10 items, 3 fases. 100% frontend (AG-03). Consume artifact_policy de S20, elimina hardcoded artifacts, implementa vista CEO con N proformas y vista portal con OC→líneas.
  - v1.1 (2026-03-30): Fixes auditoría R1 (ChatGPT 8.3/10 — 7 hallazgos). H1: +sección "Contrato de bundle". H2: Portal is_operated_by_mwt condicional. H3: Gate pre-check + error handling. H4: +ARTIFACT_UI_REGISTRY. H5: BRAND_ALLOWED_MODES espejo. H6: isLegacyExpediente() estricto. H7: ArtifactPolicyState + ArtifactPolicyMap.
  - v1.2 (2026-03-30): Fixes R2 (8.9/10 — 5 hallazgos). H1: +PROFORMA_ARTIFACT_POLICY + resolveProformaPolicy(). H2: ArtifactPolicyState en todo. H3: handleAdvance usa comando existente. H4: DONE portal condicional. H5: Labels inline eliminado.
  - v1.3 (2026-03-30): Fixes R3 (9.1/10 — 5 hallazgos). H1: EXPEDIENTE_LEVEL_ARTIFACTS filter. H2: labels solo en ARTIFACT_UI_REGISTRY. H3: STATE_TO_ADVANCE_COMMAND. H4: TS strict catch. H5: paths concretos.
  - v1.4 (2026-03-30): Fixes R4 (9.3/10 — 4 hallazgos). H1: STATE_TO_ADVANCE_COMMAND IDs canónicos. H2: import path unificado. H3: DONE S20B-02 ARTIFACT_UI_REGISTRY. H4: seguridad portal corregida.
  - v1.5 (2026-03-30): Fixes R5 (9.4/10 — 2 hallazgos). H1: PROFORMA_ARTIFACT_POLICY solo en constants. H2: STATE_TO_ADVANCE_COMMAND IDs únicos.
  - v1.6 (2026-03-30): Fixes R6 (9.3/10 — 2 hallazgos). H1: ART-04 eliminado. H2: EXPEDIENTE_LEVEL_ARTIFACTS importado.
  - v1.7 (2026-03-30): Fixes R7 (9.4/10 — 3 hallazgos). H1: layout ASCII corregido. H2: DONE genérico. H3: cláusula escape eliminada.
  - v1.8 (2026-03-30): Ajuste post-ejecución S20 DONE. APROBADO R8 9.6/10. depends_on actualizado a DONE v1.6 (35/35 tests). Contexto actualizado con datos reales de ejecución (migración 0019, crash PostgreSQL resuelto, select_for_update confirmado). Verificación pre-implementación ajustada (ya no es bloqueo, es check de exposure en serializer).

---

## Contexto

Sprint 20B es el complemento frontend del Sprint 20 (backend). Sprint 20 construyó `resolve_artifact_policy()`, los endpoints de proformas, y el `artifact_policy` en el bundle. Sprint 20B elimina la lógica hardcodeada del frontend y la reemplaza por rendering basado exclusivamente en lo que el backend dice.

**Cambio fundamental para AG-03:**
Hasta Sprint 19, el frontend decidía qué artefactos mostrar por estado (`STATE_ARTIFACTS` en `ExpedienteAccordion.tsx`). A partir de Sprint 20B, el frontend NO decide nada — lee `data.artifact_policy` del bundle y renderiza lo que viene ahí. Si el backend no envía un artefacto en la policy, el frontend no lo muestra. Punto.

**Estado post-Sprint 20 (DONE — confirmado 2026-03-30, 35/35 tests):**
- Bundle GET `/api/ui/expedientes/{id}/` retorna `artifact_policy` calculada por brand × mode (S20-06 ✅)
- FK proforma nullable en EPL + FK parent_proforma en ArtifactInstance (S20-01/02 ✅)
- Endpoints: POST crear proforma (S20-11 ✅), POST reassign-line/ (S20-09 ✅), change_proforma_mode (S20-10 ✅)
- BRAND_ALLOWED_MODES centralizada en artifact_policy.py (marluvas: mode_b/mode_c, rana_walk/tecmater: default)
- C1 flexible: solo client_id + brand_id requeridos (S20-07 ✅)
- C5 gate: valida proformas + líneas asignadas + modos definidos (S20-08 ✅)
- Void automático mode_b↔mode_c con confirm_void (S20-10 ✅)
- select_for_update() en todos los endpoints mutantes (resuelto crash PostgreSQL)
- Migración 0019_s20_proforma_fks: AddField puro, 0 alteraciones destructivas

**Estado del frontend (post-Sprint 19):**
- `ExpedienteAccordion.tsx` con `STATE_ARTIFACTS`, `ARTIFACT_COMMAND_MAP`, `ARTIFACT_LABELS` hardcodeados
- `ArtifactModal` pattern existente (Sprint 9 — S9-07)
- Formulario creación extendido con product lines dinámicas
- Detalle por estado con edición inline, merge/split modals, pagos
- CSS variables (0 hex hardcodeados desde S19)
- Brand Console con 6 tabs, Client Console con 7 tabs

---

## Decisiones ya resueltas (NO preguntar de nuevo)

| Decisión | Ref | Detalle |
|----------|-----|---------|
| Backend decide artefactos | HR-1 / S20-05 | Frontend consume `artifact_policy` del bundle. No decide. |
| Opcionales como botón | HR-5 | "+ Agregar [nombre]", no "Pendiente". |
| Solo estado actual + anteriores | HR-4 | Estados futuros NO se renderizan. |
| Inmutabilidad post-completado | HR-6 / POL_ARTIFACT_CONTRACT.C | Artefacto completado = read-only. Corrección vía C19/C20. |
| Mode por proforma, no expediente | HR-8/9 / S20-04 | Badge visual por proforma. |
| Labels desde constante | Directriz Parte VIII | 12 labels ART-01..ART-12. Constante en frontend. |
| Portal sin proformas | Directriz §6.2 | Cliente ve OC → líneas con estado. NO ve proformas, modos, costos. |
| Legacy expedientes | S20 conv.6 | Legacy sin proformas → frontend NO depende de artifact_policy para estados > REGISTRO. Fallback visual a lógica anterior. |

---

## Contrato de bundle — shape que AG-03 consume (R1-H1)

El GET `/api/ui/expedientes/{id}/` de Sprint 20 retorna un bundle. AG-03 consume estos campos específicos:

```typescript
// Shape mínima garantizada por S20 (verificar con grep en BundleSerializer)
interface ExpedienteBundle {
  id: number;
  status: string;                    // "REGISTRO", "PRODUCCION", etc.
  client: { id: number; name: string; /* ... */ };
  brand: { id: number; slug: string; name: string; };
  
  // S20 agregó:
  artifact_policy: ArtifactPolicyMap; // {estado: {required, optional, gate_for_advance}}
  
  // Campos existentes que ahora necesitan proforma_id:
  product_lines: Array<{
    id: number;
    proforma_id: number | null;      // FK a ArtifactInstance(ART-02). Null = huérfana.
    brand_sku: { id: number; product_key: string; size_label: string; };
    unit_price: string;
    quantity: number;
    // ... otros campos existentes
  }>;
  
  artifacts: Array<{
    id: number;
    artifact_type: string;           // "ART-01", "ART-02", etc.
    status: string;                  // "DRAFT", "COMPLETED", "VOIDED"
    parent_proforma_id: number | null; // FK self. Null = artefacto a nivel expediente.
    payload: Record<string, unknown>; // incluye mode, proforma_number, operated_by para ART-02
    // ... otros campos existentes
  }>;
  
  factory_orders: Array<{ /* ... existente */ }>;
  pagos: Array<{ /* ... existente */ }>;
}
```

**Verificación pre-implementación para AG-03 (S20 DONE — verificar exposure en serializer):**
```bash
# S20 creó los FK. Confirmar que el serializer los EXPONE al frontend:
grep -n "proforma" backend/apps/expedientes/serializers.py
grep -n "parent_proforma" backend/apps/expedientes/serializers.py
grep -n "artifact_policy" backend/apps/expedientes/serializers.py
```

Si `proforma_id` o `parent_proforma_id` no aparecen como campos del serializer (pueden existir como FK en el modelo pero no estar expuestos), agregar al serializer antes de implementar S20B-04/05/07. Son 2 líneas — no amerita sprint separado.

---

## Contrato del endpoint portal — shape para vista cliente (R1-H2)

El GET portal (endpoint tenant-isolated de S17) retorna datos filtrados para el cliente. Para mostrar la señal "Operado por Muito Work" necesita un campo derivado por línea:

```typescript
// Shape del endpoint portal:
interface PortalExpedienteLine {
  product_name: string;
  size_label: string;
  quantity: number;
  unit_price: string;
  status_label: string;              // "En producción", "En tránsito", etc.
  is_operated_by_mwt: boolean;       // DERIVADO del mode de la proforma (mode_c = true)
}
```

**Si `is_operated_by_mwt` no existe en el endpoint portal actual:** la señal "Operado por Muito Work" queda **fuera de scope de S20B**. Documentar como pendiente para S21 o pedir que S20 agregue el campo derivado. El frontend NO debe recibir `mode` ni `proforma` en el portal para derivarlo manualmente — eso rompe el aislamiento.

---

## Constantes frontend (R1-H4, H5)

### ARTIFACT_UI_REGISTRY — comportamiento por tipo de artefacto

```typescript
// frontend/src/constants/artifact-ui-registry.ts
// Esto NO decide presencia (eso lo hace artifact_policy del backend).
// Esto define CÓMO se renderiza cada tipo cuando el backend dice que existe.

interface ArtifactUIConfig {
  label: string;
  category: 'document' | 'process' | 'pricing';
  modal: string;          // nombre del componente modal (ej: 'RegisterOCModal')
  canCreate: boolean;     // si el usuario puede crear desde UI
  canEdit: boolean;       // si el usuario puede editar (pre-completado)
  ceoOnly: boolean;       // si requiere rol CEO
}

export const ARTIFACT_UI_REGISTRY: Record<string, ArtifactUIConfig> = {
  'ART-01': { label: 'Orden de Compra del Cliente', category: 'document', modal: 'RegisterOCModal', canCreate: true, canEdit: true, ceoOnly: false },
  'ART-02': { label: 'Proforma MWT', category: 'document', modal: 'CreateProformaModal', canCreate: true, canEdit: true, ceoOnly: true },
  'ART-03': { label: 'Decisión Modo B/C', category: 'process', modal: 'DecideModeModal', canCreate: true, canEdit: false, ceoOnly: true },
  'ART-04': { label: 'Confirmación SAP', category: 'document', modal: 'RegisterSAPModal', canCreate: true, canEdit: true, ceoOnly: true },
  'ART-05': { label: 'AWB / Bill of Lading', category: 'document', modal: 'RegisterShipmentModal', canCreate: true, canEdit: true, ceoOnly: true },
  'ART-06': { label: 'Cotización de Flete', category: 'pricing', modal: 'RegisterFreightModal', canCreate: true, canEdit: true, ceoOnly: true },
  'ART-07': { label: 'Aprobación de Despacho', category: 'process', modal: 'ApproveDispatchModal', canCreate: true, canEdit: false, ceoOnly: false },
  'ART-08': { label: 'Documentación Aduanal', category: 'document', modal: 'RegisterCustomsModal', canCreate: true, canEdit: true, ceoOnly: true },
  'ART-09': { label: 'Factura MWT', category: 'document', modal: 'IssueInvoiceModal', canCreate: true, canEdit: false, ceoOnly: true },
  'ART-10': { label: 'Factura Comisión', category: 'document', modal: 'IssueCommissionModal', canCreate: true, canEdit: false, ceoOnly: true },
  'ART-11': { label: 'Registro de Costos', category: 'pricing', modal: 'RegisterCostModal', canCreate: true, canEdit: false, ceoOnly: true },
  'ART-12': { label: 'Nota de Compensación', category: 'document', modal: 'CompensationModal', canCreate: true, canEdit: false, ceoOnly: true },
};
```

### BRAND_ALLOWED_MODES — espejo del backend (R1-H5)

```typescript
// frontend/src/constants/brand-modes.ts
// ESPEJO de BRAND_ALLOWED_MODES en backend/apps/expedientes/services/artifact_policy.py
// Si el backend cambia, este archivo DEBE actualizarse.
// El backend 400 sigue siendo la validación final — esto es solo pre-check UI.

export const BRAND_ALLOWED_MODES: Record<string, string[]> = {
  'marluvas': ['mode_b', 'mode_c'],
  'rana_walk': ['default'],
  'tecmater': ['default'],
};
```

---

## Tipos TypeScript canónicos (R1-H7)

```typescript
// frontend/src/types/expediente.ts

// Policy de UN estado (required/optional/gate de un estado específico)
export interface ArtifactPolicyState {
  required: string[];
  optional: string[];
  gate_for_advance: string[];
}

// Mapa completo de policy: estado → ArtifactPolicyState
export type ArtifactPolicyMap = Record<string, ArtifactPolicyState>;

// Usar en componentes:
// data.artifact_policy es ArtifactPolicyMap
// currentPolicy es ArtifactPolicyState
```

---

## Convenciones Sprint 20B

1. **100% frontend.** 0 cambios en backend. 0 migraciones. Si falta un endpoint, documentar como pendiente para S21, no inventar.
2. **artifact_policy es SSOT.** Si el backend no envía un artefacto en la policy, el frontend no lo muestra. Sin excepciones.
3. **0 hex hardcodeados.** Todo via CSS variables (continuidad S19-12).
4. **Backward compat visual.** Expedientes legacy (sin proformas, artifact_policy = solo REGISTRO genérica) deben seguir mostrándose correctamente. Para legacy en estados > REGISTRO, usar fallback a lógica anterior (STATE_ARTIFACTS legacy) hasta que se remedien con proformas.
5. **TypeScript strict.** Tipar `ArtifactPolicyState`, `ArtifactPolicyMap`, `ProformaSection`, etc. No `any`.
6. **Reutilizar ArtifactModal.** El patrón de S9-07 se mantiene para crear/editar artefactos dentro de proformas.

---

## FASE 0 — Eliminar hardcoded + componente genérico

### S20B-01: Eliminar constantes hardcodeadas de ExpedienteAccordion.tsx

**Agente:** AG-03 Frontend
**Dependencia:** Ninguna interna
**Prioridad:** P0 — bloqueante para todo lo demás
**Acción:** Refactorizar archivo existente

**Archivos a tocar:**
- `frontend/src/app/[lang]/(mwt)/(dashboard)/expedientes/[id]/ExpedienteAccordion.tsx` (o ruta equivalente)

**Detalle:**

Buscar y eliminar las siguientes constantes (nombres exactos pueden variar, hacer grep):

```bash
# Antes de modificar — encontrar las constantes:
grep -rn "STATE_ARTIFACTS\|ARTIFACT_COMMAND_MAP\|ARTIFACT_LABELS" frontend/src/
```

Reemplazar por consumo de `data.artifact_policy` del bundle:

```typescript
// ANTES (hardcoded):
const STATE_ARTIFACTS = {
  "REGISTRO": ["ART-01", "ART-02"],
  "PREPARACION": ["ART-05", "ART-06", "ART-07"],
  // ...
};

// DESPUÉS (del bundle):
// artifact_policy ya viene en data desde GET /api/ui/expedientes/{id}/
const { artifact_policy } = data;
// artifact_policy es:
// {
//   "REGISTRO": { required: ["ART-01", "ART-02"], optional: ["ART-03"], gate_for_advance: ["ART-01", "ART-02"] },
//   "PREPARACION": { required: [...], optional: [...], gate_for_advance: [...] },
//   ...
// }
```

**Fallback legacy (R1-H6 — helper estricto):**

```typescript
// frontend/src/utils/legacy-check.ts
// Condición estricta: no confundir legacy real con payload roto/incompleto

export function isLegacyExpediente(bundle: ExpedienteBundle): boolean {
  const { artifact_policy, status, artifacts } = bundle;
  
  // Condición 1: policy vacía o solo REGISTRO
  const policyStates = Object.keys(artifact_policy || {});
  const hasOnlyRegistro = policyStates.length <= 1 && 
    (policyStates.length === 0 || policyStates[0] === 'REGISTRO');
  
  // Condición 2: expediente está más allá de REGISTRO
  const beyondRegistro = status !== 'REGISTRO';
  
  // Condición 3: 0 proformas en el bundle (señal positiva de legacy)
  const hasNoProformas = !artifacts.some(
    a => a.artifact_type === 'ART-02'
  );
  
  // Las 3 condiciones deben cumplirse — si falta alguna, NO es legacy,
  // es un bug que debe exponerse, no maquillarse
  return hasOnlyRegistro && beyondRegistro && hasNoProformas;
}
```

```typescript
// En ExpedienteAccordion.tsx:
import { isLegacyExpediente } from '@/utils/legacy-check';
import { LEGACY_STATE_ARTIFACTS } from './legacy-artifacts'; // constantes viejas

if (isLegacyExpediente(data)) {
  // Renderizar con lógica anterior
  return <LegacyAccordion artifacts={LEGACY_STATE_ARTIFACTS} />;
}
// Renderizar con artifact_policy del bundle
return <PolicyDrivenAccordion policy={data.artifact_policy} />;
```

**Criterio de done:**
- [ ] `grep -rn "STATE_ARTIFACTS" frontend/src/` retorna 0 resultados (excepto legacy-artifacts.ts)
- [ ] `grep -rn "ARTIFACT_COMMAND_MAP" frontend/src/` retorna 0 resultados (excepto legacy)
- [ ] Expediente nuevo (con artifact_policy del bundle) renderiza correctamente
- [ ] Expediente legacy (sin proformas) sigue mostrándose con fallback visual
- [ ] No se rompe ninguna vista existente

---

### S20B-02: Componente ArtifactSection genérico

**Agente:** AG-03 Frontend
**Dependencia:** S20B-01
**Prioridad:** P0
**Acción:** Crear componente nuevo

**Archivos a tocar (CREAR):**
- `frontend/src/components/expedientes/ArtifactSection.tsx`

**Detalle:**

```typescript
// Types (importar de @/types/expediente.ts — ver sección "Tipos TypeScript canónicos")
// import { ArtifactPolicyState } from '@/types/expediente';

interface ArtifactSectionProps {
  state: string;                    // "REGISTRO", "PREPARACION", etc.
  policy: ArtifactPolicyState;      // policy de UN estado (no el mapa completo)
  artifacts: ArtifactInstance[];     // artefactos existentes del expediente
  proformaId?: number;              // si es dentro de una proforma
  isCurrentState: boolean;          // estado actual del expediente
  onCreateArtifact: (type: string) => void;
}

// Labels y UI config — IMPORTAR, no duplicar (R2-H5):
// import { ARTIFACT_UI_REGISTRY } from '@/constants/artifact-ui-registry';
// Usar ARTIFACT_UI_REGISTRY[type].label para nombres legibles
```

**Comportamiento:**
- **required**: siempre visible. Si el artefacto existe → card con datos. Si no existe → card vacía con botón "Registrar".
- **optional**: NO visible por default. Botón "+ Agregar [nombre]" al final de la sección. Si ya fue creado → visible como card normal. Si no → solo el botón.
- **gate_for_advance**: indicador visual. Si todos los gate están completados → botón "Avanzar" habilitado. Si faltan → botón deshabilitado + tooltip "Faltan: [lista]".
- **Estado anterior** (isCurrentState=false): collapsed, con indicador de completado. Click para expandir.
- **Estado futuro**: NO se renderiza. Si `state` no es el actual ni anterior, el componente retorna null.

**Criterio de done:**
- [ ] Componente renderiza required, optional y gate correctamente
- [ ] Optional muestra botón "+ Agregar [nombre]", no "Pendiente"
- [ ] Botón desaparece si el artefacto ya fue creado
- [ ] Estados anteriores: collapsed con indicador completado
- [ ] gate_for_advance deshabilitado si faltan artefactos
- [ ] TypeScript strict — 0 `any`
- [ ] Labels desde `ARTIFACT_UI_REGISTRY[type].label` (importado, no inline)

---

### S20B-03: Artefacto completado = read-only (HR-6)

**Agente:** AG-03 Frontend
**Dependencia:** S20B-02
**Prioridad:** P1
**Acción:** Modificar ArtifactModal + card rendering

**Archivos a tocar:**
- `frontend/src/components/expedientes/ArtifactSection.tsx`
- `frontend/src/components/expedientes/ArtifactModal.tsx` (existente de S9-07)

**Detalle:**

Artefacto con `status='COMPLETED'` → card en read-only. No se puede editar. No hay botón "Editar". Si el CEO necesita corregir, usa C19 (Supersede) que crea una nueva versión, o C20 (Void, CEO-ONLY para ART-09/10/12).

Indicador visual: badge "Completado ✓" en la card. Color: verde (CSS variable).

**Criterio de done:**
- [ ] Artefacto completado muestra badge "Completado" y NO tiene botón editar
- [ ] Artefacto VOIDED muestra badge "Anulado" en rojo, read-only
- [ ] Artefacto DRAFT/pendiente muestra botón "Registrar" o "Editar"

---

## FASE 1 — Vista CEO con proformas

### S20B-04: Vista CEO — expediente → N proformas (HR-7/8)

**Agente:** AG-03 Frontend
**Dependencia:** S20B-02
**Prioridad:** P0
**Acción:** Crear componente nuevo + refactorizar detalle

**Archivos a tocar:**
- `frontend/src/components/expedientes/ProformaSection.tsx` (CREAR)
- `frontend/src/app/[lang]/(mwt)/(dashboard)/expedientes/[id]/page.tsx` (o equivalente)

**Detalle:**

Layout §6.1 de la directriz:

```
Expediente Sondel #4521
├── [Estado: REGISTRO]
├── OC: ART-01 ✅ (a nivel expediente, no de proforma)
│
├── Proforma PF-001 (Mode B · Comisión)
│   ├── Línea: 75BPR29 t.35 × 30 pares — $43.00
│   ├── Línea: 75BPR29 t.36 × 40 pares — $43.00
│   └── [+ Agregar Decisión Modo B/C]  ← ART-03 opcional en REGISTRO
│
├── Proforma PF-002 (Mode C · FULL · Opera: Muito Work Ltda)
│   ├── Línea: 75BPR29 t.38 × 60 pares — $43.00
│   └── [+ Agregar Decisión Modo B/C]  ← ART-03 opcional en REGISTRO
│
├── [+ Crear nueva proforma]
├── [+ Agregar líneas]
└── [Avanzar a PRODUCCION] ← gate: ART-01 ✅, PF-001 ✅, PF-002 ✅

--- Ejemplo en EN_DESTINO (para ilustrar ART-09 vs ART-10): ---

Expediente Sondel #4521
├── [Estado: EN_DESTINO]
├── OC: ART-01 ✅ · REGISTRO ✓ · PRODUCCION ✓ · PREPARACION ✓ · DESPACHO ✓ · TRANSITO ✓
│
├── Proforma PF-001 (Mode B · Comisión)
│   └── ART-10 Factura Comisión — pendiente  ← mode_b → ART-10
│
├── Proforma PF-002 (Mode C · FULL)
│   └── ART-09 Factura MWT — pendiente       ← mode_c → ART-09
│
└── [Cerrar expediente] ← gate: ART-10 ✅ (PF-001) + ART-09 ✅ (PF-002)
```

**Componente ProformaSection:**

```typescript
interface ProformaSectionProps {
  proforma: {
    id: number;
    payload: {
      proforma_number: string;
      mode: 'mode_b' | 'mode_c' | 'default';
      operated_by: string;
    };
    status: string;
  };
  lines: ProductLine[];              // EPL filtradas por proforma_id
  childArtifacts: ArtifactInstance[]; // artefactos con parent_proforma = this
  currentState: string;              // estado actual del expediente
  brandSlug: string;                 // para resolver policy por proforma
  isEditable: boolean;               // solo en REGISTRO
}
```

**Resolución de policy por proforma (R2-H1):**

El bundle retorna `artifact_policy` como **unión** de todas las proformas. Para saber qué artefactos le corresponden a ESTA proforma específica, el frontend necesita resolver la policy individualmente por `proforma.payload.mode`:

```typescript
// frontend/src/utils/resolve-proforma-policy.ts
import { PROFORMA_ARTIFACT_POLICY } from '@/constants/proforma-artifact-policy';
import type { ArtifactPolicyState } from '@/types/expediente';

export function resolveProformaPolicy(
  brandSlug: string,
  mode: string,
  state: string
): ArtifactPolicyState {
  return PROFORMA_ARTIFACT_POLICY[brandSlug]?.[mode]?.[state] ?? {
    required: [], optional: [], gate_for_advance: []
  };
}
```

**Archivo de constante (separado):**
```typescript
// frontend/src/constants/proforma-artifact-policy.ts
// ESPEJO de ARTIFACT_POLICY del backend. Si el backend cambia, actualizar aquí.
import type { ArtifactPolicyState } from '@/types/expediente';

export const EXPEDIENTE_LEVEL_ARTIFACTS = new Set(['ART-01', 'ART-02', 'ART-11', 'ART-12']);

export const PROFORMA_ARTIFACT_POLICY: Record<string, Record<string, Record<string, ArtifactPolicyState>>> = {
  marluvas: {
    mode_b: {
      REGISTRO:     { required: ['ART-01', 'ART-02'], optional: ['ART-03'], gate_for_advance: ['ART-01', 'ART-02'] },
      PRODUCCION:   { required: [], optional: [], gate_for_advance: [] },
      PREPARACION:  { required: ['ART-05', 'ART-06', 'ART-07'], optional: ['ART-08'], gate_for_advance: ['ART-05', 'ART-06', 'ART-07'] },
      EN_DESTINO:   { required: ['ART-10'], optional: ['ART-12'], gate_for_advance: ['ART-10'] },
    },
    mode_c: {
      REGISTRO:     { required: ['ART-01', 'ART-02'], optional: ['ART-03'], gate_for_advance: ['ART-01', 'ART-02'] },
      PRODUCCION:   { required: [], optional: [], gate_for_advance: [] },
      PREPARACION:  { required: ['ART-05', 'ART-06', 'ART-07'], optional: ['ART-08'], gate_for_advance: ['ART-05', 'ART-06', 'ART-07'] },
      EN_DESTINO:   { required: ['ART-09'], optional: ['ART-12'], gate_for_advance: ['ART-09'] },
    },
  },
  rana_walk: {
    default: {
      REGISTRO:     { required: ['ART-01', 'ART-02'], optional: [], gate_for_advance: ['ART-01', 'ART-02'] },
      DESPACHO:     { required: ['ART-05', 'ART-06'], optional: [], gate_for_advance: ['ART-05', 'ART-06'] },
      EN_DESTINO:   { required: ['ART-09'], optional: [], gate_for_advance: ['ART-09'] },
    },
  },
  tecmater: {
    default: {
      REGISTRO:     { required: ['ART-01', 'ART-02'], optional: [], gate_for_advance: ['ART-01', 'ART-02'] },
      PREPARACION:  { required: ['ART-05', 'ART-06', 'ART-07'], optional: ['ART-08'], gate_for_advance: ['ART-05', 'ART-06', 'ART-07'] },
      EN_DESTINO:   { required: ['ART-09'], optional: [], gate_for_advance: ['ART-09'] },
    },
  },
};
```

**Uso en ProformaSection:**
```typescript
// Importar desde constantes — NO redeclarar (R6-H2)
// import { EXPEDIENTE_LEVEL_ARTIFACTS } from '@/constants/proforma-artifact-policy';

// Dentro de ProformaSection:
const rawPolicy = resolveProformaPolicy(
  brandSlug,
  proforma.payload.mode,
  currentState
);

// Filtrar artefactos de nivel expediente — ProformaSection NO los muestra
const proformaPolicy: ArtifactPolicyState = {
  required: rawPolicy.required.filter(a => !EXPEDIENTE_LEVEL_ARTIFACTS.has(a)),
  optional: rawPolicy.optional.filter(a => !EXPEDIENTE_LEVEL_ARTIFACTS.has(a)),
  gate_for_advance: rawPolicy.gate_for_advance.filter(a => !EXPEDIENTE_LEVEL_ARTIFACTS.has(a)),
};

// Resultado:
// PF-001 mode_b en EN_DESTINO → required: ['ART-10'], NO incluye ART-01/02/11/12
// PF-002 mode_c en EN_DESTINO → required: ['ART-09'], NO incluye ART-01/02/11/12
// ART-01, ART-11, ART-12 se renderizan en la sección de expediente (fuera de proformas)
```

**Archivos concretos (R3-H5):**
- `frontend/src/constants/proforma-artifact-policy.ts` — constante `PROFORMA_ARTIFACT_POLICY` + `EXPEDIENTE_LEVEL_ARTIFACTS`
- `frontend/src/utils/resolve-proforma-policy.ts` — función `resolveProformaPolicy()`, importa desde `@/constants/proforma-artifact-policy`

**Nota:** `artifact_policy` del bundle se usa para el gate de avance a nivel expediente (unión). `resolveProformaPolicy()` se usa para renderizar artefactos DENTRO de cada proforma. Son dos niveles distintos.

**Elementos visuales:**
- **Mode badge**: pill con color — Mode B = azul "Comisión", Mode C = verde "FULL", default = gris
- **operated_by**: solo visible si mode=mode_c, texto sutil "Opera: Muito Work Ltda"
- **Líneas**: tabla compacta (producto, talla, cantidad, precio unitario, subtotal)
- **Artefactos hijos**: usando ArtifactSection filtrado por parent_proforma
- **Botón "+ Crear nueva proforma"**: solo en REGISTRO. Abre modal con: proforma_number (auto), mode selector, líneas a asignar (checkboxes de líneas huérfanas)

**Criterio de done:**
- [ ] Cada proforma se renderiza como sección independiente con badge de mode
- [ ] Líneas agrupadas bajo su proforma
- [ ] Artefactos hijos renderizados dentro de su proforma según `resolveProformaPolicy()` filtrados por `EXPEDIENTE_LEVEL_ARTIFACTS` — no hardcodear lista de ART-IDs
- [ ] ART-01, ART-11, ART-12 renderizados a nivel expediente (fuera de proformas)
- [ ] Botón "+ Crear nueva proforma" solo en REGISTRO
- [ ] operated_by visible solo en mode_c

---

### S20B-05: Asignar y mover líneas entre proformas (HR-10)

**Agente:** AG-03 Frontend
**Dependencia:** S20B-04
**Prioridad:** P1
**Acción:** Crear componente interacción

**Archivos a tocar:**
- `frontend/src/components/expedientes/ProformaSection.tsx`
- `frontend/src/components/expedientes/ReassignLineModal.tsx` (CREAR)

**Detalle:**

- **Líneas huérfanas** (proforma=null): mostrar en sección separada "Líneas sin asignar" con warning visual
- **Mover línea**: botón en cada línea → abre modal con selector de proforma destino → POST `reassign-line/`
- **Solo en REGISTRO**: botón de mover desaparece en otros estados
- **Feedback**: después de mover, refetch del bundle para actualizar la vista

**Criterio de done:**
- [ ] Líneas huérfanas visibles con warning
- [ ] Botón mover → modal → seleccionar proforma destino → ejecuta reassign-line/
- [ ] Mover solo disponible en REGISTRO
- [ ] Vista se actualiza post-reassign (refetch)

---

### S20B-06: Botón "Avanzar" con validación de gate (HR-2)

**Agente:** AG-03 Frontend
**Dependencia:** S20B-02
**Prioridad:** P0
**Acción:** Modificar componente existente

**Archivos a tocar:**
- Componente de acciones del expediente (donde está el botón de avanzar estado)

**Detalle:**

**Principio (R1-H3):** El gate frontend es un **pre-check visual** que mejora la UX. El backend (C5 validate_c5_gate) sigue siendo la fuente final de verdad. Si el frontend permite avanzar pero el backend bloquea, el error del backend se muestra al usuario.

Antes de avanzar de estado, verificar:

```typescript
const currentPolicy = artifact_policy[expediente.status] as ArtifactPolicyState | undefined;
if (!currentPolicy) return;

// Check 1: artefactos del gate completados
const gateArtifacts = currentPolicy.gate_for_advance;
const completedTypes = new Set(
  expediente.artifacts
    .filter(a => a.status === 'COMPLETED')
    .map(a => a.artifact_type)
);
const missingArtifacts = gateArtifacts.filter(g => !completedTypes.has(g));

// Check 2: para REGISTRO, también verificar condiciones de C5 (R1-H3)
const registroExtraErrors: string[] = [];
if (expediente.status === 'REGISTRO') {
  const orphanLines = expediente.product_lines.filter(l => l.proforma_id === null);
  if (orphanLines.length > 0) {
    registroExtraErrors.push(`${orphanLines.length} línea(s) sin proforma`);
  }
  const proformas = expediente.artifacts.filter(
    a => a.artifact_type === 'ART-02' && a.status === 'COMPLETED'
  );
  const noMode = proformas.filter(p => !p.payload?.mode);
  if (noMode.length > 0) {
    registroExtraErrors.push(`${noMode.length} proforma(s) sin modo`);
  }
}

const allErrors = [
  ...missingArtifacts.map(m => ARTIFACT_UI_REGISTRY[m]?.label || m),
  ...registroExtraErrors,
];

// Botón
if (allErrors.length > 0) {
  <Button disabled tooltip={`Faltan: ${allErrors.join(', ')}`}>
    Avanzar a {nextState}
  </Button>
} else {
  <Button onClick={handleAdvance}>
    Avanzar a {nextState}
  </Button>
}

// Mapeo estado actual → command de avance (R5-H2 — IDs únicos, 0 duplicados)
// Ref: ENT_OPS_STATE_MACHINE §F — commands canónicos
const STATE_TO_ADVANCE_COMMAND: Record<string, string> = {
  'REGISTRO': 'c5',        // RegisterSAPConfirmation → auto-transition PRODUCCION
  'PRODUCCION': 'c11b',    // ConfirmPreparationReady → PREPARACION (creado en S17)
  'PREPARACION': 'c10',    // ApproveDispatch → DESPACHO
  'DESPACHO': 'c11',       // ConfirmShipmentDeparted → TRANSITO
  'TRANSITO': 'c12',       // ConfirmShipmentArrived → EN_DESTINO
  'EN_DESTINO': 'c14',     // CloseExpediente → CERRADO
};
// AG-03: verificar IDs exactos antes de implementar:
// grep -rn "def handle_c" backend/apps/expedientes/services/state_machine/
// Los IDs de arriba corresponden a la state machine FROZEN + commands creados en S17 (c11b).

// handleAdvance con TypeScript strict (R3-H4):
async function handleAdvance() {
  const command = STATE_TO_ADVANCE_COMMAND[expediente.status];
  if (!command) return; // estado sin command de avance

  try {
    await api.post(`/api/expedientes/${expediente.id}/commands/${command}/`);
    refetchBundle();
  } catch (error: unknown) {
    // Narrow del error para TS strict
    let detail = 'No se pudo avanzar. Verificar requisitos.';
    if (error instanceof Error && 'response' in error) {
      const axiosErr = error as { response?: { data?: { detail?: string; errors?: string[] } } };
      detail = axiosErr.response?.data?.detail
        || axiosErr.response?.data?.errors?.join(', ')
        || detail;
    }
    showErrorToast(detail);
  }
}
```

**Criterio de done:**
- [ ] Botón deshabilitado si faltan artefactos del gate
- [ ] En REGISTRO: también verifica huérfanas y modos por proforma
- [ ] Tooltip muestra nombres legibles (no IDs)
- [ ] Botón habilitado cuando todos los checks pasan
- [ ] Error 400 del backend se muestra como toast/alerta
- [ ] Funciona correctamente con policy de Rana Walk

---

## FASE 2 — Portal cliente + cleanup

### S20B-07: Vista portal — OC → líneas con estado (Directriz §6.2)

**Agente:** AG-03 Frontend
**Dependencia:** S20B-01 (no depende de proformas, es vista simplificada)
**Prioridad:** P0
**Acción:** Modificar vista portal existente

**Archivos a tocar:**
- `frontend/src/app/[lang]/(portal)/` (o ruta equivalente del portal B2B)

**Detalle:**

El cliente ve:

```
Mi Pedido OC #4521 — 225 pares

  Producto          Talla  Cant   Precio    Estado
  ──────────────────────────────────────────────────
  75BPR29 Goliath   35     30     $43.00    En tránsito ✈️
  75BPR29 Goliath   36     40     $43.00    En tránsito ✈️
  75BPR29 Goliath   37     30     $43.00    En tránsito ✈️
  75BPR29 Goliath   38     60     $43.00    En producción 🏭 · Operado por Muito Work
  75BPR29 Goliath   42     65     $43.00    En producción 🏭 · Operado por Muito Work
```

**Reglas de visibilidad del cliente:**
- Ve su OC como ancla (número, total pares)
- Ve estado individual por línea (derivado del estado del expediente)
- Si la línea pertenece a una proforma Mode C: señal sutil "Operado por Muito Work" — **requiere campo `is_operated_by_mwt` (boolean) en el endpoint portal** (ver sección "Contrato del endpoint portal" arriba)
- **NO ve:** proformas, modos internos, costos, márgenes, comisiones, artefactos internos
- **NO ve:** artifact_policy, gate_for_advance, nada de la lógica interna

**Bloqueo (R1-H2):** Si el endpoint portal NO retorna `is_operated_by_mwt` por línea, AG-03 NO debe derivar la señal manualmente desde `mode` u otra data interna. En ese caso, la señal "Operado por Muito Work" queda **fuera de scope de S20B** y se documenta como pendiente para S21.

**Verificación pre-implementación:**
```bash
grep -n "operated\|is_operated" backend/apps/expedientes/serializers.py
# Si retorna 0: señal fuera de scope. Implementar tabla sin esa columna.
```

**Estado por línea:** se deriva del estado del expediente. Si el expediente está en TRANSITO, todas las líneas muestran "En tránsito". El estado a nivel proforma (cuando una proforma avanza y otra no) es futuro — Sprint 24+.

**Criterio de done:**
- [ ] Portal muestra OC con tabla de líneas
- [ ] Cada línea tiene producto, talla, cantidad, precio, estado
- [ ] Si endpoint portal retorna `is_operated_by_mwt`: señal "Operado por Muito Work" visible en líneas donde es true. Si NO retorna el campo: tabla sale sin esa columna y se documenta como pendiente S21.
- [ ] 0 proformas visibles en el portal
- [ ] 0 modos, costos, márgenes, comisiones visibles
- [ ] 0 artefactos internos visibles

---

### S20B-08: Mode labels + colors centralizados (R3-H2)

**Agente:** AG-03 Frontend
**Dependencia:** Ninguna (paralelo)
**Prioridad:** P1
**Acción:** Crear constante de modes + refactorizar imports

**Archivos a tocar (CREAR):**
- `frontend/src/constants/mode-labels.ts`

**Detalle:**

**Labels de artefactos** ya viven en `ARTIFACT_UI_REGISTRY` (sección "Constantes frontend"). NO crear archivo separado `artifact-labels.ts` — eso duplica. Usar `ARTIFACT_UI_REGISTRY[type].label` para todo.

Este archivo solo contiene labels y colores de **modes**:

```typescript
// frontend/src/constants/mode-labels.ts
// Solo modes. Labels de artefactos → ARTIFACT_UI_REGISTRY.

export const MODE_LABELS: Record<string, string> = {
  'mode_b': 'Comisión',
  'mode_c': 'FULL',
  'default': 'Estándar',
};

export const MODE_COLORS: Record<string, string> = {
  'mode_b': 'var(--color-info)',      // azul
  'mode_c': 'var(--color-success)',   // verde
  'default': 'var(--color-text-secondary)', // gris
};
```

**Fuentes de verdad (una sola por concepto):**
- Labels de artefactos → `ARTIFACT_UI_REGISTRY[type].label` (en `artifact-ui-registry.ts`)
- Labels de modes → `MODE_LABELS` (en `mode-labels.ts`)
- Colores de modes → `MODE_COLORS` (en `mode-labels.ts`)
- Modes permitidos por brand → `BRAND_ALLOWED_MODES` (en `brand-modes.ts`)
- Policy por proforma → `PROFORMA_ARTIFACT_POLICY` (en `proforma-artifact-policy.ts`)

**Criterio de done:**
- [ ] `mode-labels.ts` existe con MODE_LABELS + MODE_COLORS
- [ ] 0 archivos `artifact-labels.ts` (labels de artefactos viven en ARTIFACT_UI_REGISTRY)
- [ ] `grep -rn "Orden de Compra\|Proforma MWT\|Confirmación SAP" frontend/src/ | grep -v artifact-ui-registry` retorna 0

---

### S20B-09: Crear modal para nueva proforma

**Agente:** AG-03 Frontend
**Dependencia:** S20B-04
**Prioridad:** P1
**Acción:** Crear componente nuevo

**Archivos a tocar (CREAR):**
- `frontend/src/components/expedientes/CreateProformaModal.tsx`

**Detalle:**

Modal que se abre al hacer click en "+ Crear nueva proforma":

**Campos del modal:**
- `proforma_number`: auto-generado (editable), formato PF-{expediente_id}-{timestamp}
- `mode`: selector — opciones filtradas por brand (marluvas: mode_b/mode_c, rana_walk/tecmater: default)
- `operated_by`: readonly "Muito Work Limitada" (por ahora siempre MWT — SG-06)
- `Líneas a asignar`: checkboxes de líneas huérfanas (proforma=null). Si no hay huérfanas, mensaje "Todas las líneas ya están asignadas"

**Submit:** POST `/api/expedientes/{id}/proformas/` con `{ proforma_number, mode, operated_by, line_ids }`

**Validación frontend:**
- mode requerido
- Al menos el selector de mode debe coincidir con lo que la brand permite (el backend también valida, pero mostrar error preventivo en UI)

**Criterio de done:**
- [ ] Modal abre con campos correctos
- [ ] Mode selector filtrado por brand
- [ ] Líneas huérfanas como checkboxes
- [ ] Submit llama endpoint correcto
- [ ] Post-submit: refetch del bundle, modal cierra
- [ ] Error del backend se muestra en el modal

---

### S20B-10: Solo mostrar estado actual + anteriores (HR-4)

**Agente:** AG-03 Frontend
**Dependencia:** S20B-02
**Prioridad:** P0
**Acción:** Refactorizar rendering de acordeón

**Detalle:**

El acordeón de estados ahora solo renderiza secciones para:
- **Estado actual**: expandido, editable, con ArtifactSection completo
- **Estados anteriores**: collapsed, read-only, con indicador "✓ Completado"
- **Estados futuros**: NO se renderizan. No existen en el DOM.

```typescript
const STATE_ORDER = ['REGISTRO', 'PRODUCCION', 'PREPARACION', 'DESPACHO', 'TRANSITO', 'EN_DESTINO'];
const currentIndex = STATE_ORDER.indexOf(expediente.status);

// Solo renderizar estados hasta el actual (inclusive)
const visibleStates = STATE_ORDER.slice(0, currentIndex + 1);

// Para cada estado visible:
// - Si es el actual: expandido, editable
// - Si es anterior: collapsed, read-only, badge "✓"
// - Si es futuro (no en visibleStates): NO renderizar
```

**Criterio de done:**
- [ ] Expediente en REGISTRO: solo muestra sección REGISTRO
- [ ] Expediente en PREPARACION: muestra REGISTRO (collapsed ✓), PRODUCCION (collapsed ✓), PREPARACION (expandido)
- [ ] Estados futuros NO aparecen en el DOM
- [ ] Nunca mostrar artefactos grayed-out de estados futuros (HR-4)

---

## Dependencias internas Sprint 20B

```
S20B-01 (limpiar hardcoded) ──→ S20B-02 (ArtifactSection genérico)
                                    │
                         ┌──────────┼──────────┬────────────┐
                         │          │          │            │
                    S20B-03     S20B-04    S20B-06      S20B-10
                   (read-only) (proformas) (gate UI)   (solo actual)
                                    │
                              ┌─────┼─────┐
                              │           │
                         S20B-05     S20B-09
                        (mover)    (modal crear)

S20B-07 (portal) → independiente de todo (no usa proformas)
S20B-08 (labels) → paralelo con todo (constante compartida)
```

---

## Checklist completa Sprint 20B

### Fase 0 — Limpieza + componente genérico
- [ ] S20B-01: 0 constantes hardcodeadas (excepto legacy-artifacts.ts fallback)
- [ ] S20B-02: ArtifactSection genérico con required/optional/gate
- [ ] S20B-03: Artefacto completado = read-only con badge

### Fase 1 — Vista CEO con proformas
- [ ] S20B-04: N proformas renderizadas con badge mode + líneas + artefactos hijos
- [ ] S20B-05: Mover líneas entre proformas con modal
- [ ] S20B-06: Gate de avance con tooltip de artefactos faltantes

### Fase 2 — Portal + cleanup
- [ ] S20B-07: Portal muestra OC → líneas, 0 proformas/modos/costos visibles
- [ ] S20B-08: Labels centralizados, 0 hardcodeados en componentes
- [ ] S20B-09: Modal crear proforma con mode filtrado por brand
- [ ] S20B-10: Solo estado actual + anteriores, futuros NO en DOM

### CI/CD
- [ ] `npm run lint` verde
- [ ] `npm run typecheck` verde
- [ ] 0 `any` en componentes nuevos
- [ ] 0 hex hardcodeados (`grep -rn "#[0-9a-fA-F]\{3,6\}" frontend/src/ | grep -v node_modules | grep -v .css`)

---

## Excluido explícitamente de Sprint 20B

| Feature | Razón | Cuándo |
|---------|-------|--------|
| Estado a nivel proforma (una avanza, otra no) | Complejidad — requiere backend adicional | Sprint 24+ |
| Emails/notificaciones UI | Sprint 21B o S22 | Después de S21 backend |
| Upload documentos desde portal | Sprint 24 | CEO-26 pendiente |
| Admin templates de notificación | Sprint 21B | Después de S21 backend |
| WebSocket/realtime | Nunca para MVP — polling suficiente | — |
| Drag-and-drop para mover líneas | Complejidad UI — modal selector es suficiente | Futuro si CEO lo pide |

---

## Criterio Sprint 20B DONE

### Obligatorio (bloquea Sprint 24)
1. 0 constantes de artefactos hardcodeadas en frontend (excepto legacy fallback)
2. ArtifactSection consume artifact_policy del bundle
3. Expediente Rana Walk NO muestra ART-03, ART-04, ART-07, ART-08
4. 2 proformas visibles con modos distintos y badges
5. Líneas agrupadas bajo proformas con mover funcional
6. Portal muestra OC → líneas sin proformas/modos/costos
7. Gate de avance funcional con tooltip
8. Expedientes legacy siguen mostrándose (fallback visual)
9. `npm run lint && npm run typecheck` verde
10. 0 hex hardcodeados

### Deseable (no bloquea)
11. Labels 100% centralizados (0 en componentes individuales)
12. Modal crear proforma con mode filtrado por brand
13. Artefactos VOIDED con badge visual

---

## Impacto en seguridad

| Superficie | Cambio | Evaluación |
|-----------|--------|------------|
| Portal cliente | Renderiza datos del endpoint portal tenant-isolated (no del bundle CEO) | No amplía — el endpoint ya filtra por tenant (S17). Frontend solo muestra lo que recibe. |
| artifact_policy en bundle | Datos de policy visibles en response | Contiene solo IDs de artefactos (ART-01..ART-12), no datos sensibles. Visibility INTERNAL. |
| Modal crear proforma | Llama endpoint POST S20 | Endpoint ya validado (CEO-only, BRAND_ALLOWED_MODES, select_for_update). Frontend no agrega superficie. |

---

## Lecciones de Sprint 19 aplicadas

1. **CSS variables obligatorio.** 0 hex hardcodeados — continuidad de S19-12.
2. **TypeScript strict.** No `any` — los tipos previenen bugs de contrato.
3. **Refetch después de mutación.** Optimistic update + refetch del bundle completo.
4. **Legacy fallback.** Transición gradual, no big-bang.

---

Stamp: DRAFT v1.8 — Arquitecto (Claude Opus 4.6) — 2026-03-30
