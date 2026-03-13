# PLB_INTEL_ITERACION_MANUAL
## Playbook: Protocolo de Iteración Manual — Lab Multi-LLM

---

id: PLB_INTEL_ITERACION_MANUAL
version: 1.0
domain: Gobernanza (IDX_GOBERNANZA)
status: ACTIVO
visibility: INTERNO
owner: CEO
stamp: BOOTSTRAP VIGENTE 2026-03-13
vencimiento: 2026-05-30
requires:
  - ENT_GOB_PENDIENTES
  - RW_ROOT
policies:
  - POL_UTF8
  - POL_DETERMINISMO (anti-alucinación)

---

## PROPÓSITO

Establecer el flujo de trabajo para sesiones de testeo manual de prompts con el Lab Multi-LLM MWT. El objetivo no es comparar modelos en abstracto — es construir evidencia empírica propia de qué modelo responde mejor a cada tipo de tarea dentro del contexto operacional de Rana Walk / MWT.

---

## CUÁNDO INVOCAR ESTE PROTOCOLO

| Disparador | Acción |
|---|---|
| Prompt nuevo para un agente del sistema | Testear antes de implementar |
| Respuesta de agente sospechosa o inesperada | Triangular con otros modelos |
| Incorporar nuevo dominio o entity a la KB | Verificar que los modelos leen la KB correctamente |
| Duda sobre qué modelo usar para una tarea recurrente | Correr 3+ experimentos, registrar en bitácora |

**No invocar para**: consultas de uso único, preguntas generales sin impacto operacional, tareas ya mapeadas con modelo ganador establecido.

---

## FLUJO DE SESIÓN — 5 PASOS

### PASO 1 — Definir el experimento antes de correrlo

Antes de abrir el lab, responder estas 3 preguntas:

1. **¿Qué quiero saber exactamente?**
   → No "cuál modelo es mejor" sino "cuál modelo responde mejor a [tipo de query] con [KB inyectada / sin KB]"

2. **¿Cuál es el criterio de éxito?**
   → Definirlo antes, no después de ver las respuestas. Ejemplo: "respeta el protocolo anti-alucinación", "cita la fuente correcta del ENT_", "no inventa datos de costos"

3. **¿Qué categoría es este prompt?**
   → Elegir antes: KB/datos internos · razonamiento · redacción · código · búsqueda · análisis numérico · compliance

---

### PASO 2 — Configurar el system prompt

**Regla base**: siempre usar el Protocolo Anti-Alucinación MWT como default.

```
Protocolo Anti-Alucinación MWT v1.0

REGLAS OBLIGATORIAS:
1. Dato no verificado → "[SIN DATOS — NO INVENTAR]"
2. Nunca extrapolar ni rellenar gaps
3. Confianza parcial → declarar: [CONFIANZA ALTA/MEDIA/BAJA]
4. Etiquetar fuente: [ENTRENAMIENTO] [CONTEXTO] [INFERENCIA]
5. Datos contradictorios → "[DATO CONTRADICTORIO — verificar fuente]"
6. Fuera de scope → decirlo sin rodeos

PROHIBIDO:
- Inventar datos, fechas, nombres, métricas o referencias
- Responder con confianza sobre algo desconocido
- Omitir incertidumbre para parecer más útil
```

**Modificaciones permitidas por tipo de tarea**:

| Tipo | Ajuste al system prompt |
|---|---|
| KB / datos internos | Agregar contexto del ENT_ relevante al inicio del system prompt |
| Búsqueda / research | Habilitar KB Gate OFF — el modelo usa conocimiento de entrenamiento |
| Compliance | Agregar: "Responder únicamente con lo que está documentado en [ENT_COMP_*]" |
| Código | Agregar: "Output en código únicamente. Sin prosa especulativa." |

---

### PASO 3 — Correr el experimento

1. Escribir el prompt exacto en el campo "consulta"
2. Verificar que el system prompt está configurado correctamente (editar si hace falta)
3. Correr en paralelo (Ctrl+Enter)
4. **No leer las respuestas todavía** — esperar a que terminen los 3 modelos
5. Leer las 3 respuestas juntas, en orden

---

### PASO 4 — Evaluar con criterio estructurado

Evaluar cada respuesta en 3 dimensiones antes de elegir ganador:

| Dimensión | Pregunta | Peso |
|---|---|---|
| **Protocolo** | ¿Respetó el sistema anti-alucinación? ¿Etiquetó sus fuentes? | Alto |
| **Precisión** | ¿La información es correcta o verificable? ¿No inventó datos? | Alto |
| **Utilidad** | ¿El formato y nivel de detalle son operacionalmente útiles? | Medio |

**Regla de desempate**: si dos modelos empatan en protocolo y precisión, gana el más conciso y directo.

**Señales de alucinación a detectar**:
- Datos específicos sin fuente (precios, fechas, nombres, métricas)
- Confianza alta en afirmaciones que deberían ser inciertas
- Ausencia de etiquetas [SIN DATOS] cuando la respuesta debería tenerlas
- Referencias a entidades o archivos que no existen en la KB

---

### PASO 5 — Registrar en bitácora

Registrar **siempre**, incluso si el resultado fue empate o inconclusivo. El valor está en el volumen de experimentos, no solo en los ganadores claros.

Campos obligatorios:
- **Ganador** (o empate)
- **Categoría** (al menos 1)
- **Nota** — 1 línea que explique el porqué, no solo el qué

Ejemplos de notas útiles:
- ✅ "Claude respetó protocolo, GPT-4o inventó precio de $47 sin fuente"
- ✅ "Perplexity más preciso en research externo, Claude mejor en datos KB"
- ✅ "Los 3 alucinaron — prompt demasiado ambiguo, reformular"
- ❌ "Claude ganó" (sin contexto = no sirve para el mapa)

---

## REGLAS DE INTEGRIDAD

### Lo que NUNCA se hace con los resultados del lab

1. **No copiar output de un modelo directamente a la KB sin validación CEO**
   → Todo dato generado por LLM es DRAFT hasta verificación humana

2. **No asumir que el ganador de una categoría gana siempre en esa categoría**
   → El mapa es estadístico, no determinístico. 3+ experimentos por categoría para considerar el patrón como válido

3. **No usar el lab para reemplazar la KB**
   → Si un modelo responde bien una pregunta sobre la KB, eso no exime de tener el dato en la KB. La KB es la fuente de verdad, el modelo es el interface

4. **No omitir experimentos negativos**
   → Los casos donde todos los modelos alucinaron o fallaron son los más valiosos para mejorar el sistema

---

## CADENCIA RECOMENDADA

| Frecuencia | Actividad |
|---|---|
| Por sesión de trabajo | 1–3 experimentos sobre prompts activos |
| Semanal | Revisar mapa de modelos — ¿hay patrones nuevos? |
| Por sprint | Actualizar ENT_GOB_PENDIENTES con hallazgos del lab que impacten configuración de agentes |
| Por trimestre | Revisar si el modelo ganador por categoría sigue siendo válido (modelos se actualizan) |

---

## OUTPUTS DEL PROTOCOLO

Los hallazgos del lab que tienen impacto operacional van a:

| Hallazgo | Destino |
|---|---|
| Modelo ganador consolidado por categoría | ENT_GOB_PENDIENTES → sección "Inteligencia de modelos" |
| Prompt que funcionó bien → candidato a system prompt de agente | MANIFIESTO_CAMBIOS como propuesta de update |
| Alucinación detectada sobre dato de KB | Verificar que el dato existe correctamente en el ENT_ correspondiente |
| Patrón de falla sistemática | Crear experimento de regression — correr periódicamente |

---

## REFERENCIA RÁPIDA — CHECKLIST DE SESIÓN

```
PRE-SESIÓN
[ ] ¿Tengo claro qué quiero saber?
[ ] ¿Definí el criterio de éxito antes de ver respuestas?
[ ] ¿Elegí la categoría?
[ ] ¿El system prompt tiene el protocolo anti-alucinación?

DURANTE
[ ] Correr los 3 modelos en paralelo
[ ] Leer cuando terminaron los 3 (no uno a uno)
[ ] Evaluar: protocolo → precisión → utilidad

POST-SESIÓN
[ ] Ganador marcado
[ ] Categoría asignada
[ ] Nota escrita (1 línea con el porqué)
[ ] Guardado en bitácora
[ ] Si hay hallazgo operacional → anotado en MANIFIESTO_CAMBIOS
```

---

Changelog:
- v1.0 (2026-03-13): Creación inicial — CEO session. Domain corregido a Gobernanza (IDX_GOBERNANZA).
