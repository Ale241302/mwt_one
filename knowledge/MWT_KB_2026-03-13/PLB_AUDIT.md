# PLB_AUDIT — Protocolo de Auditoría Iterativa
status: DRAFT
visibility: [INTERNAL]
domain: Gobernanza (IDX_GOBERNANZA)
version: 1.0

---

## A. Propósito

Define cómo se audita e itera cualquier documento del ecosistema MWT/RW hasta alcanzar calidad de producción. Aplica a: entities, schemas, playbooks, policies, lotes, paquetes de ejecución, prompts tácticos, y cualquier artefacto textual que deba cumplir estándares antes de ser usado.

Complementa POL_ITERACION (que define cuándo conversar vs materializar). Este playbook define cómo evaluar calidad una vez que el artefacto existe.

---

## B. Roles

| Rol | Función |
|-----|---------|
| Auditor | Evalúa, da score, lista fixes. Puede ser agente AI o humano. |
| CEO | Aprueba/rechaza, aplica fixes o delega, decide cuándo congelar. |
| Autor | Quien generó el documento. Puede ser el mismo auditor en sesión distinta, u otro agente. |

Regla: el auditor no es el autor en la misma sesión. Si el CEO quiere que un agente audite su propio output, debe ser en sesión separada o con prompt explícito de "modo auditoría".

---

## C. Flujo de rondas

### C1. Ronda 1 — Audit inicial

El auditor recibe el documento y los criterios de evaluación. Entrega:

1. **Score numérico** (X/10) — obligatorio, no opcional
2. **Lo que está bien** — 1-3 líneas máximo, sin cheerleading
3. **Problemas encontrados** — numerados, cada uno con:
   - Ubicación exacta (sección, campo, línea)
   - Qué está mal
   - Fix concreto (no vago, no "considerar mejorar")
4. **Score breakdown** por criterio (si aplica)
5. **Veredicto**: CONTINUAR (con fixes) o APROBADO

### C2. Rondas 2+ — Re-audit

El CEO pasa la versión corregida. El auditor:

1. Re-evalúa SOLO lo que cambió
2. Verifica que fixes anteriores se aplicaron correctamente
3. Si un fix introdujo problema nuevo, lo señala
4. Actualiza score
5. Lista fixes restantes (si quedan)
6. Veredicto: CONTINUAR o APROBADO

### C3. Ronda final — Aprobación

Cuando el score llega a **9.5+** y no quedan fixes críticos:

1. Veredicto: **APROBADO — listo para [siguiente paso]**
2. No seguir iterando por perfeccionismo
3. 9.5 es el umbral. 10/10 no es requisito.

### C4. Modo "aplicar directamente"

Si el CEO dice "aplica los fixes directamente":
- El auditor aplica los fixes en el documento sin preguntar
- Entrega versión corregida
- Solo se detiene cuando el CEO dice "freeze" o "congelar"

---

## D. Criterios de evaluación

Jerarquía de criterios, en orden de importancia:

| # | Criterio | Qué evalúa |
|---|----------|-------------|
| 1 | Corrección | ¿Datos correctos y trazables a la spec? |
| 2 | Completitud | ¿Falta algo que la spec requiere? |
| 3 | Consistencia | ¿Hay contradicciones internas? |
| 4 | Ejecutabilidad | ¿Alguien puede usar esto para trabajar hoy? |
| 5 | Claridad | ¿Se entiende sin contexto adicional? |

No se evalúa: elegancia de redacción, "best practices" genéricas, lo que "otros proyectos" hacen, alternativas filosóficas.

---

## E. Formato obligatorio de reporte

Cada ronda debe seguir este formato:

```
## Ronda N — Veredicto: X/10

### Lo que está bien (breve)
[1-3 líneas]

### Problemas encontrados
1. [SECCIÓN/CAMPO]: [qué está mal] → Fix: [qué hacer exactamente]
2. [SECCIÓN/CAMPO]: [qué está mal] → Fix: [qué hacer exactamente]
...

### Score breakdown (si aplica)
- Corrección: X/10
- Completitud: X/10
- Consistencia: X/10
- Ejecutabilidad: X/10
- Claridad: X/10

### Veredicto
CONTINUAR — aplicar fixes 1-N
o
APROBADO — listo para [siguiente paso]
```

---

## F. Antipatrones

El auditor NO debe:

| Antipatrón | Correcto |
|-----------|----------|
| "Esto se ve bien en general pero podría beneficiarse de..." | "Sección 2.3 falta campo blocked_by_type. Fix: agregar según §C." |
| "Considerar agregar validaciones adicionales para robustez" | "Item 3 no tiene criterio de done para admin. Fix: agregar checkbox." |
| 2 párrafos de halagos antes de los fixes | "8.7/10. 4 fixes:" |
| 10 sugerencias "nice to have" | 3 fixes críticos + "el resto es cosmético, aprobado si se arreglan estos" |
| Expandir scope (auditar Sprint 0, proponer cambios a Sprint 1) | Evaluar solo lo que le pidieron |
| Inventar contexto que no tiene | Preguntar si no entiende |

---

## G. Cuándo usar este playbook

| Situación | Usar PLB_AUDIT |
|-----------|---------------|
| Documento nuevo antes de FROZEN | Sí — auditar hasta 9.5+ |
| Documento FROZEN que se reabre | Sí — auditar delta |
| Paquete de ejecución (Sprint 0/1) | Sí |
| Prompts tácticos para agentes | Sí |
| Corrección menor (typo, ref rota) | No — aplicar directamente |
| Conversación exploratoria sin artefacto | No — usar POL_ITERACION |

---

## H. Prompt de activación

Para activar modo auditoría en cualquier agente AI, pegar al inicio del chat:

```
Modo auditoría iterativa (ref → PLB_AUDIT).
Evalúa el documento que te pase.
Score numérico + fixes concretos por ronda.
Formato: sección E de PLB_AUDIT.
Umbral de aprobación: 9.5/10.
No expandas scope. No hagas cheerleading.
Si digo "aplica directamente", corrige sin preguntar.
Si digo "freeze", para.
```

---

Stamp: DRAFT — Pendiente aprobación CEO
