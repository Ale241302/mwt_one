# ENT_PLAT_DESIGN_TOKENS — Design System mwt.one v1
status: APROBADO — Sprint 3
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
version: 1.0
refs: ENT_PROD_GOL.E, ENT_MARCA_IDENTIDAD, ENT_COMP_VISUAL, POL_ANTI_CONFUSION, rw_sticker_v9.html, PLB_COPY

---

## A — Marca (constantes invariables)

| Token | Valor | Nombre | Fuente |
|-------|-------|--------|--------|
| --brand-primary | #013A57 | Deep Navy | ENT_PROD_GOL.E1 / sticker v9 |
| --brand-accent | #75CBB3 | Mint | sticker v9 MINT constant |
| --brand-accent-soft | #E8F5F0 (light) / #0D2E26 (dark) | Mint 10% | Derivado |
| --brand-ice | #A8D8EA | Ice Blue | ENT_PROD_GOL.E2 |
| --brand-ice-soft | #EDF6FB (light) / #0B1F2E (dark) | Ice Blue 10% | Derivado |

Regla: Navy y Mint son constantes de sistema. No cambian entre temas.
Ref: POL_ANTI_CONFUSION — Navy es E1 de Goliath pero también color de sistema MWT.

---

## B — Tipografía

### B1 — Familias

| Rol | Font | Fallback | Uso | Fuente decisión |
|-----|------|----------|-----|-----------------|
| Display | General Sans | Plus Jakarta Sans, system-ui, sans-serif | Títulos, datos hero, secciones | Reemplazo web de Arial Black (sticker v9) |
| Body | Plus Jakarta Sans | system-ui, sans-serif | Texto general, labels, nav, montos | Reemplazo web de Segoe UI (sticker v9) |
| Mono | JetBrains Mono | Fira Code, monospace | IDs, refs expediente, SKUs, UUIDs, timestamps | Reemplazo web de Courier New (sticker v9) |

### B2 — Regla mono vs body (auditoría D1)

| Dato | Font | Regla |
|------|------|-------|
| Referencias expediente (EXP-2026-0047) | Mono | Código técnico inmutable |
| SKUs (RW-GOL-MED-S5) | Mono | POL_NUNCA_TRADUCIR — inmutable |
| Event IDs (evt_a3f7c912) | Mono | Identificador técnico |
| Timestamps (2026-02-15T14:30:00Z) | Mono | Formato técnico |
| Montos ($14,350.00) | Body + tabular-nums | Dato financiero, no código |
| Montos hero ($284K) | Display | Dato Claim en stat cards |

### B3 — Escala tipográfica (15 tokens, 10 activos MVP)

| Token | Size | Weight | Line-height | Uso | MVP |
|-------|------|--------|-------------|-----|-----|
| display-xl | 32px | 800 | 1.1 | Número hero dashboard | ✅ |
| display-lg | 24px | 800 | 1.2 | Títulos de página | ✅ |
| display-md | 20px | 700 | 1.25 | Títulos de sección | ✅ |
| heading-lg | 18px | 700 | 1.3 | Subtítulos, nombre expediente | ✅ |
| heading-md | 16px | 600 | 1.4 | Labels card, headers tabla | ✅ |
| heading-sm | 14px | 600 | 1.4 | Labels campo, nav items | ✅ |
| body-lg | 16px | 400 | 1.5 | Texto principal | reserva |
| body-md | 14px | 400 | 1.5 | Texto general, contenido tablas | ✅ |
| body-sm | 13px | 400 | 1.5 | Texto secundario | reserva |
| caption | 12px | 500 | 1.4 | Timestamps, hints | ✅ |
| micro | 11px | 600 | 1.3 | Badges, counters | ✅ |
| mono-lg | 16px | 600 | 1.4 | Ref expediente en detalle | reserva |
| mono-md | 14px | 500 | 1.4 | IDs, códigos en tablas | ✅ |
| mono-sm | 12px | 500 | 1.3 | UUIDs, timestamps técnicos | reserva |
| tabular-nums | 14px | 600 | 1.4 | Montos en tablas (body font) | reserva |

### B4 — Capitalización

| Contexto | Regla |
|----------|-------|
| Títulos página | Sentence case: "Expedientes activos" |
| Labels campo | UPPERCASE + letter-spacing 0.5px: "ESTADO" |
| Badges | UPPERCASE + letter-spacing 0.5px: "BLOQUEADO" |
| Nav items | Sentence case: "Expedientes" |
| Números | tabular-nums siempre en tablas |
| Énfasis datos | font-weight 600-700, nunca italic |
| Italic | Solo notas/aclaraciones, nunca datos |

---

## C — Colores por tema

### C1 — Estructura

| Token | Light | Dark |
|-------|-------|------|
| --bg | #F8F9FB | #0B1929 |
| --bg-alt | #F0F2F5 | #0E1E30 |
| --surface | #FFFFFF | #0F2337 |
| --surface-hover | #F5F6F8 | #132D47 |
| --surface-active | #EEF0F4 | #173555 |
| --surface-raised | #FFFFFF | #142A40 |
| --border | #E2E5EA | #1E3A54 |
| --border-strong | #C8CDD5 | #2A4D6B |
| --divider | #ECEEF1 | #172E45 |

Dark mode usa Navy desaturado (#0B1929 familia) para mantener identidad de marca.

### C2 — Texto

| Token | Light | Dark |
|-------|-------|------|
| --text-primary | #013A57 | #F1F5F9 |
| --text-secondary | #3D4F5C | #94A3B8 |
| --text-tertiary | #7A8A96 | #5A6E82 |
| --text-disabled | #B0BAC4 | #3A4F63 |
| --text-inverse | #FFFFFF | #0B1929 |
| --text-on-navy | #FFFFFF | #F1F5F9 |
| --text-on-mint | #013A57 | #013A57 |

### C3 — Semánticos

| Token | Light text | Light bg | Dark text | Dark bg | Origen |
|-------|-----------|---------|-----------|---------|--------|
| --success | #0E8A6D | #F0FAF6 | #75CBB3 | #0D2E26 | Mint oscurecido (WCAG AA 5.2:1) |
| --warning | #B45309 | #FFF7ED | #FFB347 | #2E1D06 | Ámbar oscurecido (WCAG AA 5.5:1) |
| --critical | #DC2626 | #FEF2F2 | #FF6B72 | #2E0A0C | Coral oscurecido (WCAG AA 4.6:1) |
| --info | #0369A1 | #F0F7FB | #A8D8EA | #0B1F2E | Ice Blue oscurecido |

Regla WCAG: Colores puros de marca (Mint, Ámbar, Coral) no pasan AA como texto sobre blanco. En light mode se usan versiones oscurecidas. En dark mode los puros funcionan sobre fondos oscuros.

### C4 — Interactivos

| Token | Light | Dark |
|-------|-------|------|
| --interactive | #013A57 | #75CBB3 |
| --interactive-hover | #014A73 | #8DD5C2 |
| --interactive-active | #012B42 | #5CB8A0 |
| --focus-ring | #A8D8EA | #A8D8EA |
| --selection | rgba(168,216,234,0.2) | rgba(117,203,179,0.2) |

Inversión dark mode: Navy→Mint como interactive. Patrón Claim+Subhead (ENT_MARCA_IDENTIDAD).

### C5 — Navegación (sidebar)

| Token | Light | Dark |
|-------|-------|------|
| --nav-bg | #013A57 | #060F1A |
| --nav-text | rgba(255,255,255,0.6) | rgba(255,255,255,0.5) |
| --nav-text-active | #FFFFFF | #F1F5F9 |
| --nav-item-hover | rgba(255,255,255,0.08) | rgba(255,255,255,0.06) |
| --nav-item-active | rgba(255,255,255,0.12) | rgba(255,255,255,0.1) |

### C6 — Botón primary (inversión por tema)

| Token | Light | Dark |
|-------|-------|------|
| --btn-primary-bg | #013A57 | #75CBB3 |
| --btn-primary-text | #FFFFFF | #013A57 |
| --btn-primary-hover | #014A73 | #8DD5C2 |

---

## D — Espaciado

### D1 — Scale (base 4px)

| Token | Valor | Uso |
|-------|-------|-----|
| --space-1 | 4px | Micro gaps |
| --space-2 | 8px | Padding badges |
| --space-3 | 12px | Padding cells tabla |
| --space-4 | 16px | Padding cards |
| --space-5 | 20px | Padding secciones |
| --space-6 | 24px | Gap entre cards |
| --space-8 | 32px | Separación secciones |
| --space-10 | 40px | Margen bloques |
| --space-12 | 48px | Padding página |

### D2 — Border radius

| Token | Valor | Uso |
|-------|-------|-----|
| --radius-sm | 4px | Badges, tags |
| --radius-md | 6px | Inputs, buttons |
| --radius-lg | 8px | Cards pequeñas, tooltips |
| --radius-xl | 12px | Cards principales, modales (sticker v9) |
| --radius-2xl | 16px | Hero sections |
| --radius-full | 9999px | Avatars, pills |

### D3 — Sombras

| Token | Light | Dark |
|-------|-------|------|
| --shadow-sm | 0 1px 2px rgba(0,0,0,0.05) | 0 1px 2px rgba(0,0,0,0.3) |
| --shadow-md | 0 4px 12px rgba(0,0,0,0.08) | 0 4px 12px rgba(0,0,0,0.4) |
| --shadow-lg | 0 8px 24px rgba(0,0,0,0.12) | 0 8px 24px rgba(0,0,0,0.5) |

---

## E — Componentes

### E1 — Botones

6 variantes: Primary, Secondary, Ghost, Danger, Danger-outline
3 tamaños: sm (32px), md (40px), lg (48px)
5 estados: default, hover, active, disabled (opacity 0.4), focused (focus-ring 3px)

### E2 — Badges

6 colores: Navy, Success, Warning, Critical, Info, Outline
3 tamaños: sm (20px), md (24px), lg (28px)
Forma: radius-sm (rectangular, consistente con sticker v9). Pill (radius-full) disponible.
Siempre: UPPERCASE + letter-spacing 0.5px

### E3 — Tabla

Componente central del dashboard.
Densidad: Compact 40px (default sugerido para CEO power user)
Zebra: bg-alt / surface alternado
Columnas especializadas: Ref (mono clickable), Estado (badge), Cliente (body), Días (number + dot semáforo), Montos (body tabular right-aligned)
Row states:
- default: normal
- .row-selected: bg selection + border-left 3px Mint (auditoría aprobada)
- .row-critical: border-right 3px Coral (auditoría D4)
- .row-selected.row-critical: dual — Mint left + Coral right (auditoría D4)

### E4 — Cards

4 tipos: Stat (dato hero), Entity (campos), Detail (grid campos), Alert (border-left semántico)
Anatomy: header + content + footer, shadow-sm, radius-xl
Stat: display-xl número + micro label + caption trend. Patrón Claim+Subhead.

### E5 — Timeline

Horizontal desktop / vertical mobile
Nodos: 16px completado (Mint filled + ✓), 20px actual (Navy + pulse + box-shadow), 16px futuro (hollow dashed)
Líneas: solid Mint completadas, gradient actual, dashed futuras

### E6 — Sidebar

Width: 240px expanded / 64px collapsed
Background: nav-bg (Navy)
Item active: border-left 3px Mint + nav-item-active bg
Counter badge: Mint bg + Navy text (inversión del header)

### E7 — Toasts

4 tipos: Success, Warning, Critical, Info
Border-left 3px con color semántico
Position: top-right, slide-in 300ms, auto-dismiss 5s (success/info), persistent (warning/critical)

### E8 — Modal

4 tamaños: Confirm (400px), Action (480-560px), Detail (640-800px), Alert (360px)
Overlay: rgba(0,0,0,0.5) light / rgba(0,0,0,0.7) dark
Container: surface, radius-xl, shadow-lg, max-height 85vh

### E9 — Inputs

Height: 40px, radius-md
Focus: border-strong + box-shadow 0 0 0 3px focus-ring (Ice Blue)
Error: critical border + rgba coral ring
Disabled: bg-alt + opacity 0.6

---

## F — Interacción

### F1 — Transiciones

| Contexto | Duración | Easing |
|----------|----------|--------|
| Hover buttons/links | 150ms | ease-out |
| Card hover | 200ms | ease-out |
| Modal open | 250ms | ease-out |
| Modal close | 200ms | ease-in |
| Sidebar expand | 200ms | ease-in-out |
| Toast enter | 300ms | spring |
| Badge pulse critical | 2000ms | ease-in-out infinite |

Principio: Profesional, no juguetonas. 150-300ms. Sin bounce, sin elastic, sin confetti.

### F2 — Responsive

| Breakpoint | Width | Sidebar |
|------------|-------|---------|
| mobile | < 640px | collapsed, stack vertical |
| tablet | 640-1024px | collapsed, content fluid |
| desktop | 1024-1440px | expanded, content max-width |
| wide | > 1440px | expanded, content centrado |

### F3 — Accesibilidad

- Focus ring 3px Ice Blue en TODOS los interactivos
- Keyboard nav: Tab order, Escape modales, Enter confirma
- Screen reader: aria-labels, roles, live regions para toasts
- Color not only: siempre ícono + texto + color (nunca solo color)
- prefers-reduced-motion: disable animaciones
- Touch target: 44px × 44px mínimo mobile

---

## G — Íconos

Librería: Lucide Icons (24px stroke, clean)
Sizes: 20px nav, 16px inline, 18px buttons, 24px stat cards, 48px empty states
Colores: semántico cuando comunica estado, text-secondary cuando decorativo

---

## H — Contrato de marca en UI

| Regla | Aplicación |
|-------|-----------|
| POL_NUNCA_TRADUCIR | Tech names en dashboard siempre en inglés |
| POL_ANTI_CONFUSION | Si se muestran datos de productos, cada uno usa su E1 |
| ENT_MARCA_IDENTIDAD | Claim+Subhead: dato hero grande, label técnico menor |
| ENT_COMP_VISUAL | WCAG contraste verificado en todas las combinaciones |
| Logo MWT | [PENDIENTE — NO INVENTAR] no existe logo formal |

---

## I — Artefacto de referencia

HTML interactivo: mwt_design_system_v1.html
Contenido: 13 secciones con todos los componentes renderizados en light/dark mode
Incluye: verificación WCAG visual, row states demo, reglas tipográficas, page layouts miniatura
Estado: Auditado por Copy + UX con 4 fixes aplicados (D1-D4)

---

Stamp vigente: APROBADO por CEO el 2026-02-27
Vencimiento: 2026-05-28 (stamp + 90 días)
Estado: VIGENTE
Aprobador final: CEO
Origen: sticker v9 + ENT_PROD_GOL.E + ENT_MARCA_IDENTIDAD + POL_ANTI_CONFUSION + ENT_COMP_VISUAL
