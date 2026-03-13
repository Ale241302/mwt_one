# PLB_AUDIT_VISUAL_BRIEF — Brief de Diseño: Protocolo Auditoría Visual
status: DRAFT
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
version: 0.1
classification: PLAYBOOK — Instrucción operativa. Brief para iterar en chat dedicado.
refs: PLB_AUDIT, ENT_COMP_VISUAL, ENT_PLAT_DESIGN_TOKENS, POL_ANTI_CONFUSION, POL_VISIBILIDAD, POL_PRINT, ENT_MARCA_IDENTIDAD, ENT_COMP_CLAIMS

---

## A. Propósito

Brief arquitectónico para la creación de PLB_AUDIT_VISUAL — protocolo de auditoría visual para todo output con componente visual del proyecto MWT/Rana Walk. Este documento se usa como input en un chat dedicado de iteración. Cuando PLB_AUDIT_VISUAL.md esté estable, este brief se archiva.

---

## B. Principio rector

No redefinir, duplicar ni reemplazar reglas ya existentes en las fuentes canónicas. El playbook final debe consumirlas, establecer precedencia, determinar aplicabilidad y llenar vacíos; solo crear reglas nuevas donde no exista cobertura explícita.

---

## C. Fuentes canónicas que el protocolo debe consumir

- ENT_COMP_VISUAL (paleta completa, tokens semánticos, WCAG ratios verificados, exclusividad color por producto)
- ENT_PLAT_DESIGN_TOKENS (escala tipográfica 15 tokens, spacing base-4, border radius, sombras, componentes, breakpoints)
- POL_ANTI_CONFUSION (exclusividad color por producto, reglas outputs públicos vs internos)
- POL_VISIBILIDAD (5 niveles: ALL, CREATIVE, TECH, INTERNAL, CEO-ONLY)
- POL_PRINT (13 reglas CSS impresión + JS orientación dinámica + 7 checks validación — aplica solo si output es imprimible)
- PLB_AUDIT (protocolo auditoría iterativa por score — ya operativo, probado en 7 rondas con score 9.8/10)
- ENT_MARCA_IDENTIDAD (identidad de marca canónica)
- ENT_COMP_CLAIMS (semáforo GREEN/YELLOW/RED para claims)

---

## D. Relación con PLB_AUDIT

PLB_AUDIT audita estructura, datos, completitud, taxonomía y policies. PLB_AUDIT_VISUAL audita la capa visual: colores, layout, tokens, impresión, accesibilidad, anti-confusión, responsive.

Pipeline real de un output: genera → PLB_AUDIT (estructura) → PLB_AUDIT_VISUAL (visual) → scorecard consolidado → APROBADO / CONTINUAR / BLOQUEADO.

PLB_AUDIT_VISUAL extiende PLB_AUDIT a la capa visual. No lo reemplaza.

---

## E. Lo que falta diseñar

1. Pipeline de validación por capas con perfiles por tipo de output
2. Contrato de entrada (tipificación: tipo, contexto, criticidad, datos sensibles, imprimible)
3. Matriz de perfiles aplicables por tipo (dashboard, HTML printable, sticker, A+ content, PDF, email)
4. Reglas de scoring, pesos por capa, y reglas de bloqueo
5. Scorecard estándar operativo
6. Flujo auto-fix vs escalación CEO

---

## F. Constraints de diseño (obligatorios)

- F1. Cadena de precedencia: POL_ manda sobre ENT_ cuando chocan sobre el mismo elemento
- F2. Fallo raíz = 1 penalización. Impactos derivados = flags sin deducción adicional
- F3. Perfiles como perfil principal + módulos opcionales (no cerrados). Outputs son híbridos por naturaleza
- F4. Auto-fix solo mecánico (token, spacing, font size, contraste). Semántico o comercial = escalar CEO
- F5. Scorecard operativo: APROBADO / CONTINUAR / BLOQUEADO — no decorativo
- F6. Todo hallazgo debe registrar trazabilidad: perfil aplicado, módulos activos, fuente canónica que originó el hallazgo (POL_/ENT_/SCH_/PLB_)

---

## G. Orden de entrega esperado

1. Propósito y alcance
2. Fuentes canónicas y precedencia
3. Contrato de entrada
4. Sistema de perfiles + módulos
5. Pipeline por capas
6. Reglas de scoring y bloqueo
7. Política auto-fix / escalación
8. Formato de scorecard
9. 3 casos de prueba (proforma HTML, sticker producto, dashboard interno)

---

Stamp: DRAFT — Brief de diseño. Vida útil acotada. Se archiva cuando PLB_AUDIT_VISUAL.md esté estable.
