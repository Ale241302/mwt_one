# RESUMEN_SPRINT_9_1_V2.md
## Sprint 9.1 — MWT ONE Frontend · Resumen Técnico Detallado

> **Estado:** Completado ✅ · **Score de auditoría:** 9.6/10 (2 rondas)  
> **Fecha de cierre:** 2026-03-17  
> **Total de archivos:** 9 archivos · **Total de líneas:** ~1,674 líneas  
> **Rama de trabajo:** `main` (frontend)

---

## Contexto del Sprint

El Sprint 9.1 fue una corrección profunda sobre Sprint 9, enfocada en tres ejes:

1. **Design System enforcement** — aplicar ENT_PLAT_DESIGN_TOKENS (KB v4.4.1) como única fuente de verdad visual.
2. **CRUD completo** — implementar Create + Read + Edit + Delete en los módulos de Nodos, Brands y Clientes.
3. **Accesibilidad y UX** — 13 fixes auditados: ARIA roles, htmlFor/id en inputs, keyboard navigation, modales responsivos.

---

## Auditoría: 13 Fixes Aplicados

### Ronda 1 — 8 fixes

| # | Fix | Archivos afectados |
|---|-----|--------------------|
| 1 | Sidebar usa `.sidebar` / `.sidebar-collapsed` (clases CSS del design system) | `Sidebar.tsx`, `globals.css` |
| 2 | `TYPE_STYLES` con CSS vars semánticos (no concatenación de clases inválida) | `nodos/page.tsx` |
| 3 | Modales responsive: `min(Npx, calc(100vw-32px))` + `grid sm:grid-cols-2` | `globals.css`, `clientes/page.tsx`, `nodos/page.tsx` |
| 4 | `ConfirmDialog`: `role="alertdialog"`, `aria-modal`, cierre con Escape, `autoFocus` en botón cancel | `ConfirmDialog.tsx` |
| 5 | `htmlFor`/`id` en todos los inputs de todos los formularios | `pipeline/page.tsx`, `nodos/page.tsx`, `brands/page.tsx`, `clientes/page.tsx` |
| 6 | `pipeline/page.tsx` importa `PIPELINE_STATES` + `STATE_BADGE_CLASSES` desde `states.ts` (sin duplicar) | `pipeline/page.tsx` |
| 7 | Labels de Sidebar respetan `POL_NUNCA_TRADUCIR` (en español, sin traducción) | `Sidebar.tsx` |
| 8 | Filtro "Pausada" placebo eliminado (no tenía lógica real) | `brands/page.tsx` |

### Ronda 2 — 5 fixes

| # | Fix | Archivos afectados |
|---|-----|--------------------|
| 9 | Pipeline cards son `<button>` con `aria-label` (accesibles por teclado) | `pipeline/page.tsx` |
| 10 | Tabla de pipeline: filas pasivas + botón explícito para navegar al detalle | `pipeline/page.tsx` |
| 11 | `FormModal` reutilizable: Escape, focus inicial, `aria-modal`, shell centralizado (componente NUEVO) | `FormModal.tsx` |
| 12 | Nodos, Brands y Clientes consumen `FormModal` (elimina duplicación de shell de modal) | `nodos/page.tsx`, `brands/page.tsx`, `clientes/page.tsx` |
| 13 | Sidebar: breakpoint detecta resize pero `isOpen` solo se setea en el primer mount (evita flicker) | `Sidebar.tsx` |

### Bonus fix
- **Pipeline loading state:** El pipeline muestra `"Cargando pipeline..."` mientras el fetch está en curso.

---

## Archivos Detallados

### 1. `globals.css`
**Ruta:** `frontend/src/app/globals.css`  
**Acción:** REEMPLAZAR  
**Líneas:** ~799  

**Qué hace:**
- Source of truth del design system `ENT_PLAT_DESIGN_TOKENS` (KB v4.4.1).
- Define **CSS custom properties** en `:root` para colores, tipografía, spacing, radii y shadows.
- Implementa **dark theme** completo con `[data-theme="dark"]`.
- Exporta utilidades tipográficas: `.display-xl`, `.heading-lg`, `.body-md`, `.caption`, `.mono`, etc.
- Componentes base CSS: `.card`, `.badge`, `.btn`, `.input`, `.table-container`, `.modal-overlay`, `.toast`, `.sidebar`, `.pipeline-grid`, `.pipeline-card`, `.confirm-dialog`.
- **Responsive breakpoints** para pipeline Kanban: 6→3→2→1 columnas según viewport.
- **Accesibilidad:** `*:focus-visible` con ring de color `--focus-ring`, soporte `prefers-reduced-motion`.

**Tokens clave definidos:**
```
--brand-primary: #013A57   (Deep Navy)
--brand-accent: #75CBB3    (Mint)
--brand-ice: #A8D8EA       (Ice Blue)
Fuentes: General Sans (display), Plus Jakarta Sans (body), JetBrains Mono (mono)
```

---

### 2. `Sidebar.tsx`
**Ruta:** `frontend/src/components/layout/Sidebar.tsx`  
**Acción:** REEMPLAZAR  
**Líneas:** ~97  

**Qué hace:**
- Navegación lateral de la consola con soporte de collapse/expand.
- 10 items de navegación organizados en 4 grupos: `core`, `financiero`, `estructura`, `admin`.
- Aplica clases `.sidebar` / `.sidebar-collapsed` del design system (fix #1).
- Labels respetan `POL_NUNCA_TRADUCIR`: todos en español (fix #7).
- Detecta breakpoint con `resize` listener pero solo setea `isOpen` en el primer mount (fix #13), evitando flicker al redimensionar.
- Soporte mobile con clase `.sidebar-mobile-open`.
- Botón de logout con `aria-label="Cerrar sesión"`.
- Links con prefijo `/${lang}/dashboard/` correcto.

**Items de nav:**
```
Dashboard · Expedientes · Pipeline · Financiero · Liquidaciones
Transfers · Nodos · Clientes · Brands · Usuarios
```

---

### 3. `ConfirmDialog.tsx` ⭐ NUEVO
**Ruta:** `frontend/src/components/ui/ConfirmDialog.tsx`  
**Acción:** CREAR (archivo nuevo)  
**Líneas:** ~79  

**Qué hace:**
- Componente reutilizable de confirmación para acciones destructivas (eliminar, desactivar, etc.).
- Fix #4: `role="alertdialog"`, `aria-modal="true"`, `aria-labelledby`, `aria-describedby`.
- `autoFocus` en el botón "Cancelar" al abrirse (previene borrado accidental).
- Cierre con tecla `Escape`.
- Props: `open`, `title`, `message`, `confirmLabel`, `variant` (`danger` | `default`), `loading`, `onConfirm`, `onCancel`.
- Usa clase `.confirm-dialog` del design system.

**Usado en:** `nodos/page.tsx`, `brands/page.tsx`, `clientes/page.tsx`

---

### 4. `FormModal.tsx` ⭐ NUEVO
**Ruta:** `frontend/src/components/ui/FormModal.tsx`  
**Acción:** CREAR (archivo nuevo)

**Qué hace:**
- Shell centralizado de modal de formulario (fix #11): reemplaza el código repetido de modal en cada página.
- Cierre con `Escape` y click en overlay.
- Focus inicial en el primer campo del formulario al abrirse.
- `aria-modal="true"`, `aria-labelledby` apuntando al título.
- Props: `open`, `title`, `titleId`, `onClose`, `footer`, `children`.
- Aplica clases `.modal-overlay` / `.modal-container` / `.modal-md` del design system.

**Elimina duplicación en:** `nodos/page.tsx`, `brands/page.tsx`, `clientes/page.tsx` (fix #12).

---

### 5. `states.ts`
**Ruta:** `frontend/src/constants/states.ts`  
**Acción:** REEMPLAZAR

**Qué hace:**
- Define `PIPELINE_STATES` (array de estados del pipeline de expedientes) y `STATE_BADGE_CLASSES` (mapeo estado → clase CSS de badge).
- Encoding UTF-8 real en todos los strings con tildes y caracteres especiales (fix #5 indirecto).
- Exporta constantes adicionales para evitar duplicación (fix #6): `pipeline/page.tsx` las importa directamente.

**Estados definidos:** `Creación`, `En proceso`, `Documentación`, `Aduana`, `Entrega`, `Archivado`.

---

### 6. `pipeline/page.tsx`
**Ruta:** `frontend/src/app/[lang]/dashboard/pipeline/page.tsx`  
**Acción:** REEMPLAZAR

**Qué hace:**
- Vista Kanban del pipeline de expedientes activos, organizada en 6 columnas (una por estado).
- **Responsive grid** con `.pipeline-grid`: 6 columnas en desktop → 3 en tablets → 2 en pantallas medianas → 1 en móvil (fix #3).
- **Loading state** (`"Cargando pipeline..."`) mientras se obtienen datos del backend.
- Cards son `<button>` con `aria-label` descriptivo (fix #9) para navegación por teclado (Tab + Enter).
- Tabla alternativa: filas pasivas + botón explícito de navegación al detalle (fix #10).
- Importa `PIPELINE_STATES` + `STATE_BADGE_CLASSES` desde `states.ts` sin duplicar definiciones (fix #6).
- `htmlFor`/`id` en todos los inputs del filtro (fix #5).
- Cards muestran: ref del expediente, cliente, badge de estado, semáforo de crédito (`.credit-dot`).

**Endpoints consumidos:** `GET /api/expedientes/` (con filtros por estado, cliente, búsqueda).

---

### 7. `nodos/page.tsx`
**Ruta:** `frontend/src/app/[lang]/dashboard/nodos/page.tsx`  
**Acción:** REEMPLAZAR

**Qué hace:**
- CRUD completo de Nodos (nodos logísticos/operativos de la red MWT).
- Listado en tabla con: nombre, tipo (con badge colorizado), país, ciudad, estado activo/inactivo, acciones.
- Formulario de creación/edición en `FormModal` (fix #12).
- `TYPE_STYLES` con CSS vars semánticos: `.badge-navy`, `.badge-success`, etc. (fix #2).
- `htmlFor`/`id` en todos los inputs (fix #5).
- Modal responsive con `grid sm:grid-cols-2` (fix #3).
- `ConfirmDialog` para confirmación de eliminación.
- Búsqueda en tiempo real por nombre y país.

**Endpoints consumidos:**
- `GET /api/transfers/nodes/` — listar nodos
- `POST /api/transfers/nodes/` — crear nodo
- `PUT /api/transfers/nodes/<id>/` — editar nodo (**requiere backend**)
- `DELETE /api/transfers/nodes/<id>/` — eliminar nodo (**requiere backend**)

---

### 8. `brands/page.tsx`
**Ruta:** `frontend/src/app/[lang]/dashboard/brands/page.tsx`  
**Acción:** REEMPLAZAR

**Qué hace:**
- CRUD completo de Brands (marcas comerciales del ecosistema MWT).
- Listado en tabla con: nombre, slug, descripción, estado activo, acciones.
- Filtro "Pausada" placebo eliminado (fix #8).
- Formulario de creación/edición en `FormModal` (fix #12).
- `htmlFor`/`id` en todos los inputs (fix #5).
- `ConfirmDialog` para confirmación de eliminación.
- Búsqueda en tiempo real por nombre y slug.

**Endpoints consumidos:**
- `GET /api/brands/` — listar brands
- `POST /api/brands/` — crear brand
- `PUT /api/brands/<slug>/` — editar brand (**requiere backend**)
- `DELETE /api/brands/<slug>/` — eliminar brand (**requiere backend**)

---

### 9. `clientes/page.tsx`
**Ruta:** `frontend/src/app/[lang]/dashboard/clientes/page.tsx`  
**Acción:** REEMPLAZAR

**Qué hace:**
- CRUD completo de Clientes (empresas/personas con expedientes).
- Listado en tabla con: nombre, entidad legal, país, crédito aprobado, expedientes activos, estado, acciones.
- Formulario de creación/edición en `FormModal` (fix #12) con grid `sm:grid-cols-2` (fix #3).
- Campos: nombre, contacto, email, teléfono, país, entidad legal (selector), estado activo (checkbox).
- `htmlFor`/`id` en todos los inputs (fix #5).
- `ConfirmDialog` para confirmación de eliminación con mensaje contextual.
- Búsqueda en tiempo real por nombre y entidad.
- Botón de navegación al detalle del cliente (`/clientes/<id>`).

**Endpoints consumidos:**
- `GET /api/clientes/` — listar clientes
- `GET /api/legal-entities/` — listar entidades legales (para selector)
- `POST /api/clientes/` — crear cliente
- `PUT /api/clientes/<id>/` — editar cliente (**requiere backend**)
- `DELETE /api/clientes/<id>/` — eliminar cliente (**requiere backend**)

---

## Backend: Endpoints Nuevos Requeridos

Los siguientes endpoints de PUT y DELETE deben agregarse si no existen:

| Endpoint | Método | Archivo Django sugerido |
|----------|--------|------------------------|
| `/api/transfers/nodes/<id>/` | PUT | `transfers/views.py` |
| `/api/transfers/nodes/<id>/` | DELETE | `transfers/views.py` |
| `/api/brands/<slug>/` | PUT | `brands/views.py` |
| `/api/brands/<slug>/` | DELETE | `brands/views.py` |
| `/api/clientes/<id>/` | PUT | `clientes/views.py` |
| `/api/clientes/<id>/` | DELETE | `clientes/views.py` |

Patrón de implementación:
```python
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_node_view(request, node_id):
    node = get_object_or_404(Node, id=node_id)
    serializer = CreateNodeSerializer(node, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(NodeDetailSerializer(node).data)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_node_view(request, node_id):
    node = get_object_or_404(Node, id=node_id)
    node.delete()
    return Response(status=204)
```

---

## Configuración Adicional Requerida

### `tailwind.config.ts`
Agregar en `theme.extend`:
```ts
fontFamily: {
  display: ['"General Sans"', '"Plus Jakarta Sans"', 'system-ui', 'sans-serif'],
  body: ['"Plus Jakarta Sans"', 'system-ui', 'sans-serif'],
  mono: ['"JetBrains Mono"', '"Fira Code"', 'monospace'],
  sans: ['"Plus Jakarta Sans"', 'system-ui', 'sans-serif'],
},
```

### `dashboard/layout.tsx`
El layout padre debe pasar el estado del sidebar:
```tsx
<Sidebar isOpen={isOpen} setIsOpen={setIsOpen} />
<main className={cn("page-container", !isOpen && "page-container-collapsed")}>
  {children}
</main>
```

---

## Fuera de Alcance (Sprint 9.1b / Sprint 10)

| Módulo | Estado | Próximo sprint |
|--------|--------|---------------|
| Dashboard page (mini-pipeline + próximas acciones) | Pendiente | Sprint 10 |
| Expediente detalle acordeón (S9-05) | Pendiente | Sprint 10 |
| Modals de artefactos (S9-07) | Pendiente | Sprint 10 |
| Usuarios: Edit + Delete | Pendiente | Sprint 9.1b |
| Transfers: Edit + Delete | Pendiente | Sprint 9.1b |

---

## Tests Post-Deploy

1. Verificar que todas las rutas del sidebar navegan correctamente con prefijo `/${lang}/dashboard/`.
2. Pipeline: 6 columnas visibles sin scroll horizontal en desktop ≥1400px.
3. Pipeline: reducción a 3 → 2 → 1 columnas al reducir viewport.
4. Nodos / Brands / Clientes: crear, editar y eliminar registros funciona end-to-end.
5. Modales se cierran con `Escape` y con click fuera del panel.
6. Pipeline cards navegables con `Tab` → `Enter`.
7. Fuentes correctas: General Sans en títulos, Plus Jakarta Sans en body, JetBrains Mono en referencias/IDs.

---

*Generado automáticamente — Sprint 9.1 · MWT ONE · 2026-03-17*
