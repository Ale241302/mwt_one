// ============================================================
// RESUMEN SPRINT 20B — Frontend Policy-Driven + Vista Proformas
// Estado general: ✅ DONE (10/10 ítems completados)
// Fecha cierre: 2026-03-31
// Versión lote: LOTE_SM_SPRINT20B v1.8
// Depende de: LOTE_SM_SPRINT20 DONE v1.6 (35/35 tests, 0 regresiones)
// ============================================================

/**
 * CONTEXTO DEL SPRINT
 *
 * Sprint 20B es el complemento 100% frontend del Sprint 20 (backend).
 * Sprint 20 construyó resolve_artifact_policy(), los endpoints de proformas
 * y el artifact_policy en el bundle. Sprint 20B eliminó la lógica hardcodeada
 * del frontend y la reemplazó por rendering basado exclusivamente en lo que
 * el backend dice via artifact_policy.
 *
 * CAMBIO FUNDAMENTAL:
 * - ANTES: Frontend decidía qué artefactos mostrar por estado (STATE_ARTIFACTS hardcoded)
 * - DESPUÉS: Frontend NO decide nada — lee data.artifact_policy del bundle y renderiza
 *            lo que viene ahí. Si el backend no envía un artefacto en la policy,
 *            el frontend no lo muestra. Punto.
 *
 * BASE DEL SPRINT 20 (confirmado DONE 2026-03-30, 35/35 tests):
 * - Bundle GET /api/ui/expedientes/{id}/ retorna artifact_policy calculada por brand x mode ✅
 * - FK proforma nullable en EPL + FK parent_proforma en ArtifactInstance ✅
 * - Endpoints: POST crear proforma, POST reassign-line/, change_proforma_mode ✅
 * - BRAND_ALLOWED_MODES centralizada en artifact_policy.py ✅
 * - C5 gate: valida proformas + líneas asignadas + modos definidos ✅
 * - Void automático mode_b↔mode_c con confirm_void ✅
 * - select_for_update() en todos los endpoints mutantes (crash PostgreSQL resuelto) ✅
 * - Migración 0019_s20_proforma_fks: AddField puro, 0 alteraciones destructivas ✅
 */

// ============================================================
// ✅ FASE 0 — LIMPIEZA HARDCODED + COMPONENTE GENÉRICO
// ============================================================

/**
 * ✅ S20B-01 — DONE: Eliminar constantes hardcodeadas de ExpedienteAccordion.tsx
 * ─────────────────────────────────────────────────────────────────────────────
 * PROBLEMA:
 *   ExpedienteAccordion.tsx tenía STATE_ARTIFACTS, ARTIFACT_COMMAND_MAP y
 *   ARTIFACT_LABELS hardcodeados en el frontend. Cualquier cambio de política
 *   de artefactos requería modificar el frontend manualmente. Era la fuente
 *   principal de desincronización entre backend y frontend.
 *
 * QUÉ SE HIZO:
 *   1. Se ejecutó grep para localizar todas las ocurrencias:
 *        grep -rn "STATE_ARTIFACTS|ARTIFACT_COMMAND_MAP|ARTIFACT_LABELS" frontend/src/
 *
 *   2. Se eliminaron STATE_ARTIFACTS, ARTIFACT_COMMAND_MAP y ARTIFACT_LABELS
 *      del archivo ExpedienteAccordion.tsx.
 *
 *   3. Las constantes antiguas se movieron a:
 *        frontend/src/app/[lang]/(mwt)/(dashboard)/expedientes/[id]/legacy-artifacts.ts
 *        → Solo como fallback para expedientes que no tienen proformas (legacy).
 *
 *   4. En ExpedienteAccordion.tsx se reemplazó el consumo hardcoded por:
 *        const { artifact_policy } = data;
 *        // artifact_policy es ArtifactPolicyMap { estado: { required, optional, gate_for_advance } }
 *
 *   5. Se implementó el helper isLegacyExpediente() en:
 *        frontend/src/utils/legacy-check.ts
 *      con condición estricta de 3 factores:
 *        - policy vacía o solo REGISTRO
 *        - expediente más allá de REGISTRO
 *        - 0 artefactos ART-02 en el bundle
 *      (Las 3 deben cumplirse — si falta alguna, no es legacy, es un bug)
 *
 *   6. ExpedienteAccordion.tsx ahora bifurca:
 *        if (isLegacyExpediente(data)) → <LegacyAccordion con LEGACY_STATE_ARTIFACTS />
 *        else                          → <PolicyDrivenAccordion con data.artifact_policy />
 *
 * ARCHIVOS MODIFICADOS:
 *   - frontend/src/app/[lang]/(mwt)/(dashboard)/expedientes/[id]/ExpedienteAccordion.tsx
 *   - frontend/src/app/[lang]/(mwt)/(dashboard)/expedientes/[id]/legacy-artifacts.ts (NUEVO)
 *   - frontend/src/utils/legacy-check.ts (NUEVO)
 *
 * VERIFICACIÓN DONE:
 *   ✅ grep STATE_ARTIFACTS frontend/src/ → 0 resultados (excepto legacy-artifacts.ts)
 *   ✅ grep ARTIFACT_COMMAND_MAP frontend/src/ → 0 resultados (excepto legacy)
 *   ✅ Expediente nuevo (con artifact_policy) renderiza correctamente
 *   ✅ Expediente legacy (sin proformas) usa fallback visual sin errores
 *   ✅ Ninguna vista existente se rompió
 */

/**
 * ✅ S20B-02 — DONE: Componente ArtifactSection genérico (policy-driven)
 * ────────────────────────────────────────────────────────────────────────
 * PROBLEMA:
 *   No existía un componente reutilizable que supiera renderizar los
 *   artefactos de un estado a partir de una policy. Cada vista tenía
 *   su propia lógica duplicada e inconsistente.
 *
 * QUÉ SE HIZO:
 *   1. Se creó frontend/src/components/expedientes/ArtifactSection.tsx
 *      con props: state, policy (ArtifactPolicyState), artifacts, proformaId?,
 *      isCurrentState, onCreateArtifact.
 *
 *   2. El componente implementa 3 comportamientos según el tipo de artefacto:
 *      - required: siempre visible. Si existe → card con datos. Si no → card vacía + botón "Registrar".
 *      - optional: NO visible por default. Botón "+ Agregar [nombre]" al final.
 *                  Si ya fue creado → visible como card normal, botón desaparece.
 *      - gate_for_advance: indicador visual. Si todos completados → botón "Avanzar" habilitado.
 *                          Si faltan → botón deshabilitado + tooltip "Faltan: [lista]".
 *
 *   3. Estados anteriores (isCurrentState=false): collapsed con indicador de completado.
 *      Click para expandir si el usuario necesita consultar el historial.
 *
 *   4. Labels de artefactos se importan de ARTIFACT_UI_REGISTRY[type].label.
 *      0 labels inline o duplicados.
 *
 *   5. TypeScript strict: props tipadas con ArtifactPolicyState importado de @/types/expediente.
 *      0 any.
 *
 *   También se crearon en este ítem:
 *   - frontend/src/constants/artifact-ui-registry.ts (ARTIFACT_UI_REGISTRY con 12 tipos ART-01..ART-12)
 *   - frontend/src/types/expediente.ts (ArtifactPolicyState + ArtifactPolicyMap)
 *
 * ARCHIVOS CREADOS:
 *   - frontend/src/components/expedientes/ArtifactSection.tsx
 *   - frontend/src/constants/artifact-ui-registry.ts
 *   - frontend/src/types/expediente.ts
 *
 * VERIFICACIÓN DONE:
 *   ✅ Componente renderiza required, optional y gate correctamente
 *   ✅ Optional muestra botón "+ Agregar [nombre]", NO "Pendiente"
 *   ✅ Botón desaparece si el artefacto ya fue creado
 *   ✅ Estados anteriores: collapsed con indicador completado
 *   ✅ gate_for_advance deshabilitado si faltan artefactos del gate
 *   ✅ TypeScript strict — 0 any
 *   ✅ Labels desde ARTIFACT_UI_REGISTRY[type].label (importado, no inline)
 */

/**
 * ✅ S20B-03 — DONE: Artefacto completado = read-only con badge (HR-6)
 * ─────────────────────────────────────────────────────────────────────
 * PROBLEMA:
 *   Los artefactos con status=COMPLETED seguían mostrando botón "Editar",
 *   violando la regla de inmutabilidad post-completado (HR-6 /
 *   POL_ARTIFACT_CONTRACT.C). Correcciones debían hacerse vía C19
 *   (Supersede) o C20 (Void, CEO-ONLY), no editando directamente.
 *
 * QUÉ SE HIZO:
 *   1. En ArtifactSection.tsx se agregó lógica de renderizado condicional:
 *      - status='COMPLETED': card en read-only, badge verde "Completado ✓",
 *                            0 botón editar, 0 botón registrar.
 *      - status='VOIDED': card en read-only, badge rojo "Anulado", read-only.
 *      - status='DRAFT': muestra botón "Registrar" o "Editar" según si tiene datos.
 *
 *   2. En ArtifactModal.tsx (existente de S9-07) se agregó prop readOnly,
 *      que cuando es true deshabilita todos los inputs y oculta el botón submit.
 *      ArtifactSection pasa readOnly={artifact.status === 'COMPLETED' || artifact.status === 'VOIDED'}.
 *
 *   3. El color del badge usa CSS variables (no hex hardcodeados):
 *      - Completado: var(--color-success)
 *      - Anulado: var(--color-danger)
 *
 * ARCHIVOS MODIFICADOS:
 *   - frontend/src/components/expedientes/ArtifactSection.tsx
 *   - frontend/src/components/expedientes/ArtifactModal.tsx
 *
 * VERIFICACIÓN DONE:
 *   ✅ Artefacto completado muestra badge "Completado" y NO tiene botón editar
 *   ✅ Artefacto VOIDED muestra badge "Anulado" en rojo, read-only
 *   ✅ Artefacto DRAFT/pendiente muestra botón "Registrar" o "Editar"
 */

// ============================================================
// ✅ FASE 1 — VISTA CEO CON PROFORMAS
// ============================================================

/**
 * ✅ S20B-04 — DONE: Vista CEO — expediente → N proformas (HR-7/8)
 * ──────────────────────────────────────────────────────────────────
 * PROBLEMA:
 *   El detalle del expediente no mostraba las proformas. Todas las líneas
 *   y artefactos aparecían como una lista plana sin contexto de a qué
 *   proforma pertenecían. No era posible distinguir qué artefactos
 *   correspondían a Mode B vs Mode C.
 *
 * QUÉ SE HIZO:
 *   1. Se creó frontend/src/components/expedientes/ProformaSection.tsx
 *      con props: proforma, lines (EPL filtradas por proforma_id),
 *      childArtifacts, currentState, brandSlug, isEditable.
 *
 *   2. El componente muestra:
 *      - Badge de mode: pill de color — Mode B = azul "Comisión", Mode C = verde "FULL", default = gris.
 *        Colores via MODE_COLORS de mode-labels.ts (CSS variables, no hex).
 *      - Texto "Opera: Muito Work Ltda" (sutil) solo si mode=mode_c.
 *      - Tabla compacta de líneas: producto, talla, cantidad, precio unitario, subtotal.
 *      - ArtifactSection filtrado por parent_proforma para los artefactos hijos.
 *
 *   3. Se creó frontend/src/utils/resolve-proforma-policy.ts
 *      con función resolveProformaPolicy(brandSlug, mode, state): ArtifactPolicyState.
 *      La función consulta PROFORMA_ARTIFACT_POLICY[brandSlug]?.[mode]?.[state]
 *      y retorna { required: [], optional: [], gate_for_advance: [] } si no encuentra.
 *
 *   4. Se creó frontend/src/constants/proforma-artifact-policy.ts
 *      con PROFORMA_ARTIFACT_POLICY (espejo del backend por brand x mode x state)
 *      y EXPEDIENTE_LEVEL_ARTIFACTS = new Set(['ART-01', 'ART-02', 'ART-11', 'ART-12']).
 *      ProformaSection filtra estos IDs de la policy para NO renderizarlos
 *      dentro de las proformas (se renderizan a nivel expediente).
 *
 *   5. Se creó frontend/src/constants/brand-modes.ts
 *      con BRAND_ALLOWED_MODES (espejo de backend):
 *        marluvas: ['mode_b', 'mode_c']
 *        rana_walk: ['default']
 *        tecmater: ['default']
 *
 *   6. En la página de detalle del expediente se integró ProformaSection:
 *      - Se agrupa data.artifacts por parent_proforma_id para pasarlos a cada sección.
 *      - Se agrupa data.product_lines por proforma_id para pasarlos a cada sección.
 *      - Los artefactos a nivel expediente (EXPEDIENTE_LEVEL_ARTIFACTS) se renderizan fuera.
 *      - Botón "+ Crear nueva proforma" solo visible en REGISTRO.
 *
 * ARCHIVOS CREADOS:
 *   - frontend/src/components/expedientes/ProformaSection.tsx
 *   - frontend/src/utils/resolve-proforma-policy.ts
 *   - frontend/src/constants/proforma-artifact-policy.ts
 *   - frontend/src/constants/brand-modes.ts
 *
 * VERIFICACIÓN DONE:
 *   ✅ Cada proforma se renderiza como sección independiente con badge de mode
 *   ✅ Líneas agrupadas bajo su proforma correspondiente
 *   ✅ Artefactos hijos dentro de proforma según resolveProformaPolicy() + filtro EXPEDIENTE_LEVEL_ARTIFACTS
 *   ✅ ART-01, ART-11, ART-12 renderizados a nivel expediente (fuera de proformas)
 *   ✅ Botón "+ Crear nueva proforma" solo visible en REGISTRO
 *   ✅ "Opera: Muito Work Ltda" visible solo en mode_c
 *   ✅ Rana Walk NO muestra ART-03, ART-04, ART-07, ART-08 (policy espejo correcto)
 */

/**
 * ✅ S20B-05 — DONE: Asignar y mover líneas entre proformas (HR-10)
 * ──────────────────────────────────────────────────────────────────
 * PROBLEMA:
 *   No había forma desde el frontend de reasignar una línea de una proforma
 *   a otra, ni de ver qué líneas estaban "huérfanas" (sin proforma asignada).
 *   El endpoint reassign-line/ de S20 existía pero no tenía UI.
 *
 * QUÉ SE HIZO:
 *   1. En ProformaSection.tsx se agregó sección "Líneas sin asignar" que
 *      muestra las líneas con proforma_id=null con un warning visual
 *      (borde ámbar, ícono ⚠️, texto "Sin asignar a proforma").
 *
 *   2. Se creó frontend/src/components/expedientes/ReassignLineModal.tsx
 *      con:
 *      - Selector de proforma destino (dropdown con proformas del expediente).
 *      - Botón "Mover" que ejecuta POST /api/expedientes/{id}/reassign-line/
 *        con body { line_id, target_proforma_id }.
 *      - Feedback post-mutación: refetch del bundle completo para actualizar la vista.
 *
 *   3. Cada línea en la tabla de ProformaSection tiene botón "Mover →" que abre
 *      ReassignLineModal con la línea preseleccionada.
 *      El botón solo aparece si isEditable=true (es decir, solo en REGISTRO).
 *
 * ARCHIVOS CREADOS:
 *   - frontend/src/components/expedientes/ReassignLineModal.tsx
 *
 * ARCHIVOS MODIFICADOS:
 *   - frontend/src/components/expedientes/ProformaSection.tsx
 *
 * VERIFICACIÓN DONE:
 *   ✅ Líneas huérfanas (proforma=null) visibles con warning visual
 *   ✅ Botón "Mover →" en cada línea solo en REGISTRO
 *   ✅ Modal abre, muestra selector de proforma destino, ejecuta reassign-line/
 *   ✅ Vista se actualiza post-reassign con refetch del bundle
 *   ✅ Botón de mover desaparece en estados distintos a REGISTRO
 */

/**
 * ✅ S20B-06 — DONE: Botón "Avanzar" con validación de gate pre-check (HR-2)
 * ──────────────────────────────────────────────────────────────────────────────
 * PROBLEMA:
 *   El botón "Avanzar" se mostraba habilitado siempre, sin verificar si
 *   el expediente cumplía las condiciones necesarias para avanzar de estado.
 *   El usuario solo se enteraba del error cuando el backend (C5 gate) rechazaba
 *   la operación, sin pistas de qué faltaba.
 *
 * QUÉ SE HIZO:
 *   1. Se implementó pre-check visual ANTES de ejecutar el command de avance:
 *
 *      Check 1 — Artefactos del gate completados:
 *        const currentPolicy = artifact_policy[expediente.status]
 *        const gateArtifacts = currentPolicy.gate_for_advance
 *        const completedTypes = new Set(artifacts.filter(COMPLETED).map(type))
 *        const missingArtifacts = gateArtifacts.filter(g => !completedTypes.has(g))
 *
 *      Check 2 — Para REGISTRO, condiciones extra de C5:
 *        - Líneas huérfanas (proforma_id=null): "{n} línea(s) sin proforma"
 *        - Proformas sin modo (payload.mode vacío): "{n} proforma(s) sin modo"
 *
 *   2. Si hay errores, el botón queda deshabilitado con tooltip mostrando
 *      nombres legibles de los artefactos faltantes (via ARTIFACT_UI_REGISTRY[type].label).
 *
 *   3. Si el backend rechaza con 400 de todos modos (por condiciones que el
 *      frontend no chequeó), el error se muestra como toast/alerta con el
 *      mensaje del backend (detail o errors del response).
 *
 *   4. Se implementó STATE_TO_ADVANCE_COMMAND mapeando estado actual → command ID:
 *        REGISTRO → c5, PRODUCCION → c11b, PREPARACION → c10,
 *        DESPACHO → c11, TRANSITO → c12, EN_DESTINO → c14
 *
 *   5. handleAdvance usa TypeScript strict catch:
 *        catch (error: unknown) con narrow para extraer detail del response.
 *
 * ARCHIVOS MODIFICADOS:
 *   - Componente de acciones del expediente (sección botón avanzar)
 *
 * VERIFICACIÓN DONE:
 *   ✅ Botón deshabilitado + tooltip si faltan artefactos del gate
 *   ✅ En REGISTRO también verifica líneas huérfanas y proformas sin modo
 *   ✅ Tooltip muestra nombres legibles (no IDs técnicos)
 *   ✅ Botón habilitado cuando todos los checks pasan
 *   ✅ Error 400 del backend se muestra como toast/alerta con detalle
 *   ✅ Funciona correctamente con policy de Rana Walk (gate diferente)
 */

// ============================================================
// ✅ FASE 2 — PORTAL CLIENTE + CLEANUP
// ============================================================

/**
 * ✅ S20B-07 — DONE: Vista portal — OC → líneas con estado (Directriz §6.2)
 * ───────────────────────────────────────────────────────────────────────────
 * PROBLEMA:
 *   El portal del cliente mostraba datos internos (proformas, modos, costos)
 *   que el cliente no debe ver. El cliente solo debe ver su OC como ancla
 *   y el estado de cada línea de su pedido.
 *
 * QUÉ SE HIZO:
 *   1. Se refactorizó la página del portal para mostrar exclusivamente:
 *      - Número de OC del cliente como encabezado (ancla del pedido).
 *      - Tabla de líneas: Producto | Talla | Cantidad | Precio | Estado.
 *      - Estado por línea derivado del estado global del expediente
 *        (traducciones legibles: TRANSITO → "En tránsito ✈️", PRODUCCION → "En producción 🏭", etc.).
 *
 *   2. Se verificó el endpoint portal con:
 *        grep -n "operated|is_operated" backend/apps/expedientes/serializers.py
 *      El campo is_operated_by_mwt NO existía en el endpoint portal al momento
 *      de la implementación, por lo que la señal "Operado por Muito Work" quedó
 *      fuera de scope de S20B según el criterio de bloqueo definido en el lote.
 *      Documentado como pendiente para Sprint 21.
 *
 *   3. Se eliminó toda referencia a proformas, modos internos, costos, márgenes,
 *      comisiones, artifact_policy y artefactos internos del portal.
 *
 * ARCHIVOS MODIFICADOS:
 *   - frontend/src/app/[lang]/(portal)/ (página de detalle del pedido cliente)
 *
 * VERIFICACIÓN DONE:
 *   ✅ Portal muestra OC como encabezado con tabla de líneas
 *   ✅ Cada línea tiene producto, talla, cantidad, precio, estado legible
 *   ✅ 0 proformas visibles en el portal
 *   ✅ 0 modos, costos, márgenes, comisiones visibles
 *   ✅ 0 artefactos internos visibles
 *   ✅ is_operated_by_mwt: documentado como pendiente S21
 */

/**
 * ✅ S20B-08 — DONE: Mode labels + colors centralizados (R3-H2)
 * ──────────────────────────────────────────────────────────────
 * PROBLEMA:
 *   Los labels de modes ("Comisión", "FULL", "Estándar") y sus colores
 *   estaban duplicados en múltiples componentes, generando inconsistencias
 *   visuales y múltiples puntos de actualización.
 *
 * QUÉ SE HIZO:
 *   1. Se creó frontend/src/constants/mode-labels.ts con:
 *      - MODE_LABELS: { mode_b: 'Comisión', mode_c: 'FULL', default: 'Estándar' }
 *      - MODE_COLORS: { mode_b: 'var(--color-info)', mode_c: 'var(--color-success)',
 *                       default: 'var(--color-text-secondary)' }
 *      (0 hex hardcodeados — todo via CSS variables)
 *
 *   2. Se verificó que NO existe artifact-labels.ts separado.
 *      Los labels de artefactos viven ÚNICAMENTE en ARTIFACT_UI_REGISTRY[type].label.
 *
 *   3. Se hizo grep de limpieza en todos los componentes:
 *        grep -rn "Orden de Compra|Proforma MWT|Confirmación SAP" frontend/src/ | grep -v artifact-ui-registry
 *      → 0 resultados. Todos los labels de artefactos vienen de ARTIFACT_UI_REGISTRY.
 *
 *   Fuentes de verdad establecidas (una sola por concepto):
 *     - Labels de artefactos → ARTIFACT_UI_REGISTRY[type].label
 *     - Labels de modes → MODE_LABELS (mode-labels.ts)
 *     - Colores de modes → MODE_COLORS (mode-labels.ts)
 *     - Modes permitidos por brand → BRAND_ALLOWED_MODES (brand-modes.ts)
 *     - Policy por proforma → PROFORMA_ARTIFACT_POLICY (proforma-artifact-policy.ts)
 *
 * ARCHIVOS CREADOS:
 *   - frontend/src/constants/mode-labels.ts
 *
 * VERIFICACIÓN DONE:
 *   ✅ mode-labels.ts existe con MODE_LABELS + MODE_COLORS en CSS variables
 *   ✅ 0 archivos artifact-labels.ts
 *   ✅ grep "Orden de Compra|Proforma MWT" → 0 resultados fuera de artifact-ui-registry
 */

/**
 * ✅ S20B-09 — DONE: Modal para crear nueva proforma
 * ──────────────────────────────────────────────────
 * PROBLEMA:
 *   No había forma desde el frontend de crear una proforma nueva.
 *   El endpoint POST /api/expedientes/{id}/proformas/ de S20 existía
 *   pero no tenía interfaz de usuario.
 *
 * QUÉ SE HIZO:
 *   1. Se creó frontend/src/components/expedientes/CreateProformaModal.tsx
 *      con los siguientes campos:
 *      - proforma_number: auto-generado (editable), formato PF-{expediente_id}-{timestamp}.
 *      - mode: selector con opciones filtradas por brand:
 *              marluvas → [mode_b, mode_c]
 *              rana_walk, tecmater → [default]
 *              Usa BRAND_ALLOWED_MODES[brand.slug] para filtrar.
 *      - operated_by: readonly "Muito Work Limitada" (siempre MWT — SG-06).
 *      - Líneas a asignar: checkboxes con líneas huérfanas (proforma=null).
 *                          Si no hay huérfanas → mensaje "Todas las líneas ya están asignadas".
 *
 *   2. El submit envía POST /api/expedientes/{id}/proformas/ con:
 *        { proforma_number, mode, operated_by, line_ids: [...] }
 *
 *   3. Validación frontend preventiva:
 *      - mode requerido (no puede quedar vacío).
 *      - mode debe estar en BRAND_ALLOWED_MODES[brand.slug].
 *
 *   4. Post-submit: refetch del bundle completo, modal se cierra.
 *      Error del backend se muestra inline en el modal.
 *
 * ARCHIVOS CREADOS:
 *   - frontend/src/components/expedientes/CreateProformaModal.tsx
 *
 * VERIFICACIÓN DONE:
 *   ✅ Modal abre con campos correctos al clickar "+ Crear nueva proforma"
 *   ✅ Mode selector muestra solo los modos permitidos por brand
 *   ✅ Líneas huérfanas aparecen como checkboxes seleccionables
 *   ✅ Submit llama el endpoint correcto con payload correcto
 *   ✅ Post-submit: refetch del bundle, modal se cierra
 *   ✅ Error del backend se muestra inline en el modal
 */

/**
 * ✅ S20B-10 — DONE: Solo mostrar estado actual + anteriores (HR-4)
 * ──────────────────────────────────────────────────────────────────
 * PROBLEMA:
 *   El acordeón mostraba todos los estados del expediente (incluyendo futuros)
 *   con artefactos grayed-out, violando HR-4. Esto confundía al usuario
 *   mostrando artefactos que aún no aplican como si estuvieran pendientes.
 *
 * QUÉ SE HIZO:
 *   1. Se definió STATE_ORDER canónico:
 *        ['REGISTRO', 'PRODUCCION', 'PREPARACION', 'DESPACHO', 'TRANSITO', 'EN_DESTINO']
 *
 *   2. Se calcula currentIndex = STATE_ORDER.indexOf(expediente.status)
 *
 *   3. Se construye visibleStates = STATE_ORDER.slice(0, currentIndex + 1)
 *      Solo estos estados se renderizan en el DOM.
 *
 *   4. Para cada estado visible:
 *      - Estado actual (último de visibleStates): expandido, editable,
 *        ArtifactSection completo con policy del bundle.
 *      - Estados anteriores (todos los anteriores al actual): collapsed,
 *        read-only, badge "✓ Completado".
 *      - Estados futuros (no en visibleStates): NO se renderizan.
 *        No existen en el DOM. No hay elementos grayed-out.
 *
 * ARCHIVOS MODIFICADOS:
 *   - frontend/src/app/[lang]/(mwt)/(dashboard)/expedientes/[id]/ExpedienteAccordion.tsx
 *
 * VERIFICACIÓN DONE:
 *   ✅ Expediente en REGISTRO: solo sección REGISTRO visible y expandida
 *   ✅ Expediente en PREPARACION: REGISTRO (collapsed ✓) + PRODUCCION (collapsed ✓) + PREPARACION (expandida)
 *   ✅ Estados futuros NO aparecen en el DOM (confirmado con DevTools)
 *   ✅ 0 artefactos grayed-out de estados futuros (HR-4 cumplido)
 */

// ============================================================
// ✅ CI/CD — VERIFICACIONES FINALES
// ============================================================

/**
 * ✅ CI/CD — DONE: Verificaciones de calidad pre-PR
 * ──────────────────────────────────────────────────
 * Se ejecutaron todos los checks de cierre de sprint:
 *
 *   ✅ npm run lint       → verde (0 errores, 0 warnings)
 *   ✅ npm run typecheck  → verde (0 errores TypeScript)
 *   ✅ 0 any en componentes nuevos
 *   ✅ 0 hex hardcodeados:
 *        grep -rn "#[0-9a-fA-F]{3,6}" frontend/src/ | grep -v node_modules | grep -v .css → 0
 *   ✅ STATE_ARTIFACTS eliminado:
 *        grep -rn "STATE_ARTIFACTS" frontend/src/ | grep -v legacy → 0
 *   ✅ Labels centralizados:
 *        grep -rn "Orden de Compra|Proforma MWT" frontend/src/ | grep -v artifact-ui-registry → 0
 */

// ============================================================
// RESUMEN DE ARCHIVOS CREADOS / MODIFICADOS EN SPRINT 20B
// ============================================================

/**
 * ARCHIVOS NUEVOS CREADOS:
 * ─────────────────────────
 * frontend/src/components/expedientes/ArtifactSection.tsx         — Componente genérico policy-driven
 * frontend/src/components/expedientes/ProformaSection.tsx         — Sección de proforma con badge + líneas
 * frontend/src/components/expedientes/ReassignLineModal.tsx       — Modal para mover líneas entre proformas
 * frontend/src/components/expedientes/CreateProformaModal.tsx     — Modal para crear nueva proforma
 * frontend/src/constants/proforma-artifact-policy.ts             — PROFORMA_ARTIFACT_POLICY + EXPEDIENTE_LEVEL_ARTIFACTS
 * frontend/src/constants/artifact-ui-registry.ts                 — Label + modal + handler por artifact_type (12 tipos)
 * frontend/src/constants/mode-labels.ts                          — MODE_LABELS + MODE_COLORS
 * frontend/src/constants/brand-modes.ts                          — BRAND_ALLOWED_MODES espejo backend
 * frontend/src/utils/resolve-proforma-policy.ts                  — resolveProformaPolicy(brand, mode, state)
 * frontend/src/utils/legacy-check.ts                             — isLegacyExpediente() helper estricto
 * frontend/src/types/expediente.ts                               — ArtifactPolicyState + ArtifactPolicyMap
 * frontend/src/app/.../expedientes/[id]/legacy-artifacts.ts      — Constantes viejas como fallback
 *
 * ARCHIVOS MODIFICADOS:
 * ──────────────────────
 * ExpedienteAccordion.tsx  — Elimina hardcoded, consume artifact_policy del bundle,
 *                            bifurca legacy/policy-driven, implementa STATE_ORDER
 * ArtifactModal.tsx        — Agrega prop readOnly para status=COMPLETED/VOIDED
 * Detalle expediente page  — Integra ProformaSection, gate UI, botón "+ Crear nueva proforma"
 * Portal page              — Tabla OC→líneas, 0 proformas/modos/costos/artefactos internos
 *
 * ARCHIVOS NO TOCADOS (conforme reglas):
 * ───────────────────────────────────────
 * backend/ (0 cambios — sprint 100% frontend)
 * docker-compose.yml (0 cambios)
 */

// ============================================================
// CRITERIO SPRINT 20B — DONE ✅ (10/10 obligatorios + 3/3 deseables)
// ============================================================

/**
 * OBLIGATORIOS (bloqueaban Sprint 24) — TODOS CUMPLIDOS:
 *   [✅] 1. 0 constantes de artefactos hardcodeadas (excepto legacy-artifacts.ts fallback)
 *   [✅] 2. ArtifactSection consume artifact_policy del bundle
 *   [✅] 3. Expediente Rana Walk NO muestra ART-03, ART-04, ART-07, ART-08
 *   [✅] 4. 2+ proformas visibles con modos distintos y badges correctos
 *   [✅] 5. Líneas agrupadas bajo proformas con mover funcional (ReassignLineModal)
 *   [✅] 6. Portal muestra OC → líneas sin proformas/modos/costos
 *   [✅] 7. Gate de avance funcional con tooltip de artefactos faltantes
 *   [✅] 8. Expedientes legacy siguen mostrándose (fallback isLegacyExpediente)
 *   [✅] 9. npm run lint && npm run typecheck → verde
 *   [✅] 10. 0 hex hardcodeados en frontend/src/
 *
 * DESEABLES — CUMPLIDOS:
 *   [✅] 11. Labels 100% centralizados (0 en componentes individuales)
 *   [✅] 12. Modal crear proforma con mode filtrado por brand
 *   [✅] 13. Artefactos VOIDED con badge visual "Anulado" en rojo
 *
 * EXCLUIDO EXPLÍCITAMENTE (documentado como pendiente):
 *   - is_operated_by_mwt en portal → Sprint 21 (campo no expuesto en endpoint portal)
 *   - Estado a nivel proforma (una avanza, otra no) → Sprint 24+
 *   - Emails/notificaciones UI → Sprint 21B
 *   - Upload documentos portal → Sprint 24
 *   - WebSocket/realtime → Nunca para MVP (polling suficiente)
 *   - Drag-and-drop mover líneas → Futuro si CEO lo pide
 */

export {};
