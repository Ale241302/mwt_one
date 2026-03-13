# POL_CLAIMS_SCANNER — Claims y Lenguaje del Scanner
id: POL_CLAIMS_SCANNER
version: 1.0
domain: Compliance (IDX_COMPLIANCE)
status: DRAFT
visibility: [ALL]
stamp: DRAFT — pendiente aprobación CEO
iso: —
origin: Audit externo ChatGPT — Hallazgo 2
extends: ENT_COMP_CLAIMS

---

## A. Propósito

Blindar el posicionamiento "wellness / herramienta de prescripción comercial" del Rana Walk Pressure Scanner. Define qué se puede y qué no se puede decir sobre el scanner en cualquier material, conversación de venta, UI, o comunicación.

Riesgo: si el lenguaje cruza la línea hacia "diagnóstico médico", se activan regulaciones FDA (USA), ANVISA (Brasil), Ministerio de Salud (CR) que hoy no aplican. Un solo claim mal puesto puede reclasificar el producto.

---

## B. Posicionamiento canónico

El scanner es una **herramienta de prescripción de calzado y plantillas en punto de venta**, basada en medición objetiva de presión plantar. No diagnostica, no trata, no previene condiciones médicas.

Frase canónica: "Medimos tu pie para encontrar el calzado y la plantilla que mejor se adaptan a tu pisada."

---

## C. Frases PERMITIDAS

| Contexto | Permitido |
|---------|-----------|
| Punto de venta | "Vamos a medir tu pie para ver qué modelo te calza mejor" |
| Punto de venta | "Tu presión se concentra más en esta zona — esta plantilla redistribuye mejor" |
| Material comercial | "Recomendación basada en datos biomecánicos" |
| Material comercial | "Medición objetiva de presión plantar" |
| Material comercial | "Herramienta de fitting profesional" |
| Material comercial | "Análisis de distribución de presión" |
| UI del scanner | "Perfil de presión", "Mapa de calor", "Zonas de concentración" |
| UI del scanner | "Recomendación de producto basada en tu perfil" |

---

## D. Frases PROHIBIDAS

| Prohibido | Por qué | Alternativa |
|----------|---------|-------------|
| "Diagnóstico" / "diagnosticar" | Implica acto médico | "Análisis" / "evaluación" |
| "Tratamiento" / "tratar" | Implica intervención terapéutica | "Recomendación de producto" |
| "Previene lesiones" / "evita problemas" | Claim médico no sustentado | "Mejora la distribución de presión" |
| "Corrige" / "corrección" | Implica dispositivo correctivo (médico) | "Redistribuye" / "adapta" |
| "Patología" / "enfermedad" / "condición médica" | Territorio clínico | No usar — referir a profesional |
| "Ortopédico" como descriptor del scanner | Reclasifica producto | "Biomecánico" |
| "Prescripción médica" | Acto médico | "Prescripción de producto" o "recomendación" |
| "Pie plano" / "pronación severa" / "fascitis" | Diagnósticos clínicos | "Arco bajo" / "presión medial alta" / no mencionar |
| "Clínicamente probado" | Requiere evidencia clínica formal | "Basado en medición objetiva" |

---

## E. Disclaimer obligatorio en UI

En toda pantalla del scanner que muestre resultados, debe aparecer:

```
Esta medición es una herramienta de fitting para calzado y plantillas.
No constituye diagnóstico médico. Si tiene dolor persistente o una
condición médica, consulte a un profesional de salud.
```

Tamaño mínimo: legible (no microprint). Posición: footer de pantalla de resultados, siempre visible.

---

## F. Reglas para distribuidores

1. El distribuidor recibe las frases permitidas/prohibidas en el onboarding (Fase 3 de PLB_SCANNER_DISTRIB).
2. Todo material de marketing que el distribuidor produzca sobre el scanner debe pasar por MWT antes de publicarse.
3. Si un vendedor en piso dice "esto le diagnostica pie plano" a un cliente, es responsabilidad del distribuidor corregir. MWT puede revocar acceso al scanner si hay abuso reiterado de claims.
4. El script de venta estandarizado (PLB_SCANNER_DISTRIB Fase 3) usa solo frases permitidas.

---

## G. Gate de revisión

Antes de publicar cualquier material sobre el scanner (listing, folleto, video, social media, presentación B2B):

1. Verificar contra sección D (frases prohibidas).
2. Verificar disclaimer §E si aplica.
3. Si hay duda → escalar a CEO. Nunca publicar en duda.

Ref → PLB_COMPLIANCE (claim check + brand check) para flujo general.

---

Stamp: DRAFT — Pendiente aprobación CEO
