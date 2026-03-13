# POL_IDEA_EVAL
id: POL_IDEA_EVAL
version: 2.0
domain: GOBERNANZA
status: DRAFT
visibility: [INTERNAL]
stamp: DRAFT — pendiente aprobación CEO
fuente: Sesión de desarrollo 2026-03-01

---

## PROPÓSITO

Protocolo estándar de evaluación de ideas de negocio, producto o modelo comercial dentro de MWT. Garantiza evaluación objetiva, documentada y reproducible antes de asignar recursos de desarrollo o capital.

---

## CUÁNDO APLICAR

**Obligatorio:**
- Nueva línea de producto o servicio
- Nuevo canal de distribución
- Nueva feature de plataforma con costo de desarrollo > 20 horas
- CEO solicita evaluación formal

**Opcional:**
- Mejoras incrementales a productos existentes
- Análisis de oportunidad sin compromiso de recursos inmediato

---

## LAS 7 DIMENSIONES

| # | Dimensión | Pregunta clave | Peso |
|---|-----------|---------------|------|
| D1 | Problema real | ¿Existe el dolor que resuelve? ¿Alguien paga hoy por resolverlo? | 20% |
| D2 | Ventaja diferencial | ¿Por qué MWT y no otro? ¿Es copiable en 6 meses? | 20% |
| D3 | Modelo de monetización | ¿Queda claro quién paga, cuánto y con qué frecuencia? | 15% |
| D4 | Tracción con activos existentes | ¿Usa lo que MWT ya tiene sin construir desde cero? | 15% |
| D5 | Complejidad de ejecución | ¿Cuántas cosas tienen que salir bien simultáneamente? (10 = baja complejidad) | 15% |
| D6 | Riesgo de mercado | ¿Puede el cliente no adoptarlo aunque el producto sea bueno? (10 = bajo riesgo) | 10% |
| D7 | Escalabilidad | ¿El esfuerzo marginal cae a medida que crece? | 5% |

**Nota D5 y D6:** se califican de forma inversa. Un 10 en D5 significa baja complejidad (bueno). Un 10 en D6 significa bajo riesgo de no adopción (bueno).

---

## ESCALA DE PUNTUACIÓN

| Puntuación | Significado |
|-----------|-------------|
| 9–10 | Excepcional — ventaja clara, evidencia fuerte |
| 7–8 | Sólido — bien fundamentado con incertidumbre menor |
| 5–6 | Aceptable — presente pero con riesgos identificados |
| 3–4 | Débil — existe pero con problemas serios |
| 0–2 | Ausente o bloqueante |

---

## ESCALA D5 — COMPLEJIDAD (referencia rápida)

| Dependencias simultáneas requeridas | Score D5 |
|------------------------------------|---------|
| 1–2 | 9–10 |
| 3–4 | 7–8 |
| 5–6 | 5–6 |
| 7–9 | 3–4 |
| 10+ | 0–2 |

---

## CÁLCULO DEL SCORE

```
Score ponderado = Σ (D_i × Peso_i)

Ajuste por efecto compuesto: +0.0 a +0.5
  Aplica si la idea crea un activo que multiplica el valor
  de otro activo MWT existente (efecto de red, dependencia
  positiva de canal, datos propietarios, etc.)
  Debe justificarse explícitamente en el reporte.

Score final = Score ponderado + Ajuste
```

---

## TABLA DE DECISIÓN

| Score final | Decisión sugerida |
|-------------|-----------------|
| 9.0–10.0 | Ejecutar con recursos prioritarios |
| 8.0–8.9 | Ejecutar — monitorear los riesgos identificados |
| 7.0–7.9 | Piloto acotado antes de escala |
| 6.0–6.9 | Iterar la idea — una o dos dimensiones bloquean |
| 5.0–5.9 | No ejecutar ahora — revisar en 90 días |
| < 5.0 | Descartar o reformular completamente |

---

## FORMATO ESTANDARIZADO DE REPORTE

```
═══════════════════════════════════════════
IDEA-EVAL: [nombre de la idea]
Fecha: YYYY-MM-DD
Evaluador: [agente o persona]
═══════════════════════════════════════════

D1 Problema real:          [0–10]
   Justificación: ...

D2 Ventaja diferencial:    [0–10]
   Justificación: ...

D3 Monetización:           [0–10]
   Justificación: ...

D4 Activos existentes:     [0–10]
   Justificación: ...

D5 Complejidad ejecución:  [0–10]
   Dependencias identificadas: N
   Justificación: ...

D6 Riesgo de mercado:      [0–10]
   Justificación: ...

D7 Escalabilidad:          [0–10]
   Justificación: ...

───────────────────────────────────────────
Score ponderado:   X.XX
Ajuste compuesto:  +X.X — [justificación]
SCORE FINAL:       X.XX
───────────────────────────────────────────

Decisión sugerida: [Ejecutar / Piloto / Iterar / No ejecutar]

Los dos números que determinan si la idea vive o muere:
1. [KPI crítico #1]: umbral [X] · medir en [plazo]
2. [KPI crítico #2]: umbral [X] · medir en [plazo]
═══════════════════════════════════════════
```

---

## REGISTRO DE EVALUACIONES

### EVAL-001 — RW Scanner + distribución canal calzado industrial
Fecha: 2026-03-01 · Evaluador: Claude (MWT Architecture Agent)

| Dimensión | Score | Resumen |
|-----------|-------|---------|
| D1 Problema real | 9 | Vendedor de calzado industrial no tiene argumento biomecánico. Dolor medible y verificable. |
| D2 Ventaja diferencial | 8 | Nadie en LATAM combina scanner + catálogo + plantilla en flujo único. Copiable en 12–18 meses. |
| D3 Monetización | 7 | Tres capas de ingreso identificadas. Falta definir si software es gratuito o SaaS. |
| D4 Activos existentes | 9 | Scanner acelera dos negocios ya existentes (plantillas + Marluvas) sin construir desde cero. |
| D5 Complejidad | 6 | 6 dependencias simultáneas: OEM protocolo abierto · driver · motor biomecánico · UI · catálogo · adopción del distribuidor. |
| D6 Riesgo mercado | 6 | Riesgo conductual: distribuidor EPP es transaccional. Requiere selección estricta de early adopters. |
| D7 Escalabilidad | 8 | Costo marginal por distribuidor adicional casi cero una vez el software está construido. |

Score ponderado: 7.70
Ajuste compuesto: +0.50 — el módulo catálogo cruzado crea barrera de datos propietarios y genera demanda pull hacia Marluvas desde canal ajeno.
**Score final: 8.20**

Decisión: Piloto acotado con 3–5 early adopters antes de rollout.

KPIs críticos:
1. Attach rate plantilla en primeras 4 semanas: umbral ≥ 20%
2. Tiempo de onboarding (carga catálogo + capacitación vendedor): umbral ≤ 2 horas

