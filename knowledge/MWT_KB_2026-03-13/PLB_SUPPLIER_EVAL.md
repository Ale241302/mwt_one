# PLB_SUPPLIER_EVAL — Evaluación y Control de Proveedores
id: PLB_SUPPLIER_EVAL
version: 1.0
domain: Gobernanza (IDX_GOBERNANZA)
status: DRAFT
visibility: [INTERNAL]
stamp: DRAFT — pendiente aprobación CEO
iso: 9001:2015 §8.4
origin: Audit externo ChatGPT — Hallazgo 4

---

## A. Propósito

Protocolo para evaluar, seleccionar y monitorear proveedores críticos de MWT. Un auditor ISO 9001 espera ver: criterios de selección, evaluación periódica, registro de desempeño, y acciones cuando un proveedor falla.

---

## B. Clasificación de proveedores

| Clase | Criterio | Frecuencia evaluación | Ejemplo |
|-------|---------|----------------------|---------|
| CRÍTICO | Su falla detiene operación o afecta producto final | Semestral | Marluvas, Bangni, OEM Scanner |
| IMPORTANTE | Su falla causa retraso o costo adicional pero hay alternativa | Anual | Forwarders, Hostinger |
| ESTÁNDAR | Servicios commoditizados, fácilmente reemplazables | Bienal o por incidente | Insumos empaque, servicios generales |

---

## C. Criterios de evaluación

| Criterio | Peso | Qué se evalúa |
|---------|------|---------------|
| Calidad de producto | 30% | Cumplimiento de specs, defectos por lote, consistencia |
| Cumplimiento de entregas | 25% | On-time delivery, lead time real vs prometido |
| Comunicación | 15% | Tiempo de respuesta, claridad, proactividad ante problemas |
| Capacidad técnica | 15% | Puede cumplir specs futuras, flexibilidad de MOQ, documentación técnica |
| Precio/valor | 15% | Competitividad, estabilidad de precios, condiciones de pago |

---

## D. Scorecard

Escala: 1 (inaceptable) a 5 (excelente). Score ponderado mínimo para mantener: 3.0.

```
═══════════════════════════════════════════
EVALUACIÓN PROVEEDOR — [NOMBRE]
Período: [Q1-Q2 / Q3-Q4 / Anual] [AÑO]
Evaluador: CEO
Clase: [CRÍTICO / IMPORTANTE / ESTÁNDAR]
═══════════════════════════════════════════

Calidad producto:      [1-5] × 0.30 = [score]
Entregas:              [1-5] × 0.25 = [score]
Comunicación:          [1-5] × 0.15 = [score]
Capacidad técnica:     [1-5] × 0.15 = [score]
Precio/valor:          [1-5] × 0.15 = [score]

SCORE PONDERADO:       [X.XX]

Incidentes en período: [N]
NC abiertas:           [N]

Decisión: [MANTENER / MANTENER CON PLAN MEJORA / BUSCAR ALTERNATIVA / DESCONTINUAR]
Notas: [observaciones]
═══════════════════════════════════════════
```

---

## E. Acciones por score

| Score | Acción |
|-------|--------|
| 4.0–5.0 | Mantener. Proveedor confiable. |
| 3.0–3.9 | Mantener con monitoreo. Comunicar áreas de mejora. |
| 2.0–2.9 | Plan de mejora formal con fecha límite. Buscar alternativa en paralelo. |
| < 2.0 | Descontinuar relación o escalar a CEO si no hay alternativa. |

---

## F. Registro de incidentes con proveedor

Cuando un proveedor falla (lote defectuoso, entrega tarde, spec incorrecta):

1. Registrar en ENT_GOB_PROVEEDORES §C como incidente con fecha, descripción, impacto.
2. Si afecta producto final o cliente → abrir NC en PLB_ACCION_CORRECTIVA.
3. Comunicar al proveedor con evidencia y expectativa de corrección.
4. Registrar respuesta del proveedor y acción tomada.
5. Incorporar incidente en siguiente evaluación periódica.

---

## G. Evaluación inicial (selección)

Antes de aprobar un proveedor nuevo (clase CRÍTICO o IMPORTANTE):

1. Solicitar muestras y evaluar contra specs (ref → SCH_BRIEF_PROVEEDOR si aplica).
2. Verificar capacidad de producción y lead times.
3. Solicitar certificaciones relevantes (CE, RoHS, etc. si aplica).
4. Definir condiciones comerciales (MOQ, payment terms, incoterms).
5. Registrar en ENT_GOB_PROVEEDORES con score inicial.

Para OEM Scanner: gate AC-02 de ENT_PROD_SCANNER es la evaluación inicial obligatoria (ingeniero MWT lee frames crudos en Python en < 4 horas).

---

Stamp: DRAFT — Pendiente aprobación CEO
