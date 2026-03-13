# POL_VISIBILIDAD — Etiquetas de Acceso

Cada entity declara su nivel de visibilidad.

| Etiqueta | Quién ve | Ejemplo |
|----------|----------|---------|
| [ALL] | Todos, incluido proveedores externos | Specs técnicas, colores, claims |
| [CREATIVE] | Equipo creativo + internos | Hooks, anti-claims, comparativas |
| [TECH] | Equipo técnico + internos | Arquitectura, Docker, APIs |
| [INTERNAL] | Solo equipo interno | Riesgos, estrategia |
| [CEO-ONLY] | Solo CEO | Pricing exacto, costos, márgenes |

## Regla
- SCH_BRIEF_PROVEEDOR excluye [CEO-ONLY] e [INTERNAL] automáticamente
- Dato marcado [CEO-ONLY] nunca aparece en output externo

---
Stamp: BOOTSTRAP VIGENTE 2026-03-01
Vencimiento: 2026-05-30
Estado: VIGENTE
Aprobador final: CEO
