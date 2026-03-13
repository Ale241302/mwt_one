# POL_ARTIFACT_CONTRACT — Artifact Contract Specification (Normativo)
status: DRAFT
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
version: 1.0
classification: POLICY NORMATIVA — Constraint obligatorio con rango constitucional dentro del sistema de artefactos. Todo artefacto debe cumplir este contrato.

---

## A. Propósito

Este documento define el contrato obligatorio que toda definición de artefacto debe cumplir para existir en el sistema. Es el molde. Cualquier artefacto que no cumpla este contrato no puede registrarse en ARTIFACT_REGISTRY.

Resuelve: ARCH-01 (pendiente histórico en ENT_PLAT_ARTEFACTOS).

### A1. Alcance

Este contrato aplica a:
- Artefactos nuevos (ART-13+)
- Artefactos existentes (ART-01 a ART-12) que deben poder expresarse bajo este contrato sin cambiar su comportamiento

No aplica a:
- Entidades estructurales (nodos, transfers, expedientes, LegalEntity)
- Policies / Services (reglas, cálculos, alertas)
- Conectores
- Automatizaciones

### A2. Principio fundacional

Un artefacto es una **unidad modular ejecutable o registrable del flujo**. Representa algo que ocurre dentro de una operación — no algo que existe permanentemente.

---

## B. Contrato obligatorio

Todo artefacto registrado en ARTIFACT_REGISTRY debe declarar todos los campos siguientes:

### B1. Identidad

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| artifact_type_id | string | Sí | ID único: ART-XX (auto-increment, nunca reutilizar) |
| name | string | Sí | Nombre legible: "Recepción en nodo" |
| version | semver | Sí | Versionamiento semántico: 1.0.0 |
| category | enum | Sí | document / process / pricing / report |
| applies_to | enum[] | Sí | A qué se pega: [expediente, transfer, node] |
| description | string | Sí | Qué hace en una línea |

### B2. Schema de datos

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| field_definitions | Field[] | Sí | Campos propios con nombre, tipo, validación, default |
| input_schema | Object | Sí | Qué recibe para ejecutarse (refs a otras entidades/artefactos) |
| output_schema | Object | Sí | Qué produce al completarse |

### B3. Comportamiento

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| state_model | enum[] | Sí | Estados válidos de la instancia |
| emitted_events | EventType[] | Sí | Eventos que dispara al bus → ENT_PLAT_EVENTOS |
| validation_rules | Rule[] | Sí | Reglas internas declarativas (no código ejecutable) |

### B4. Gobernanza

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| permissions | RoleMatrix | Sí | Quién puede: create, view, edit, approve, complete |
| requires_approval | boolean | Sí | ¿Completar requiere aprobación humana? |
| visibility | enum | Sí | internal / client / public |

### B5. UI

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| ui_hints | Object | Sí | Cómo se renderiza en cada frontend (mwt.one, portal.mwt.one) |

### B6. Lifecycle de la definición

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| definition_status | enum | Sí | draft / sandbox / review / active / deprecated |
| created_by | string | Sí | Quién lo creó (humano o IA) |
| approved_by | string | Auto | CEO — se llena al aprobar |
| approved_at | datetime | Auto | Fecha de aprobación |
| superseded_by | ref | Auto | Si fue reemplazado, por cuál ART-XX |

---

## C. State model estándar de instancias

Toda instancia de artefacto en producción sigue este modelo de estados:

```
draft → submitted → approved → completed → void

draft:      Creado, incompleto, editable
submitted:  Completo, pendiente de aprobación (si requires_approval)
approved:   Aprobado por quién corresponda
completed:  Ejecutado/terminado. Inmutable.
void:       Anulado. Inmutable. Registra razón.
```

Si el artefacto tiene `requires_approval: false`, salta de draft → completed directamente.

---

## D. Reglas de validación

### D1. Reglas que todo artefacto debe cumplir

- Todo artefacto debe tener al menos un `applies_to` declarado
- Todo artefacto debe emitir al menos un evento
- Los field_definitions deben usar tipos estándar: string, int, decimal, boolean, datetime, enum, ref
- Las validation_rules deben ser declarativas (condiciones evaluables), no código ejecutable
- El ui_hints debe cubrir al menos mwt.one como surface

### D2. Compatibilidad

- ART-01 a ART-12 deben poder expresarse bajo este contrato sin cambiar su comportamiento actual
- Si un artefacto existente no puede cumplir el contrato, el contrato está mal diseñado — no el artefacto
- Nuevas versiones de un artefacto no rompen instancias existentes (ref → ENT_PLAT_ARTEFACTOS.F)

---

## E. Exclusiones explícitas — Qué NO es un artefacto

Estas entidades y conceptos NO deben modelarse como artefactos bajo ninguna circunstancia:

| Concepto | Qué es | Por qué no es artefacto |
|----------|--------|------------------------|
| Nodo | Entidad estructural | Existe permanentemente, no "ocurre" en un flujo |
| Transfer | Entidad estructural | Es movimiento entre nodos, no pieza del flujo |
| Expediente | Entidad estructural | Es contenedor, no contenido |
| LegalEntity | Entidad estructural | Es tenant raíz, no actividad |
| Conector | Capacidad técnica | Es puente de integración, no objeto de proceso |
| Policy / Service | Regla / cálculo | Es lógica del sistema, no registro de actividad |
| Automatización | Ejecución | Es orquestación, no objeto del flujo |
| Costo acumulado | Campo computado | Es derivado, no artefacto. Vive en policy/service |
| Semáforo de inventario | Regla | Es cálculo en ENT_OPS_INVENTARIO, no artefacto |
| Forecast | Cálculo | Es output de ENT_OPS_DEMAND_PLANNING, no artefacto |

Regla: si dudás si algo es artefacto, preguntá: *¿es algo que ocurre dentro de un flujo operativo y deja evidencia registrable?* Si sí → puede ser artefacto. Si no → es otra cosa.

---

## F. Gobernanza de creación

### F1. Quién puede proponer artefactos nuevos

- CEO (siempre)
- Agentes IA (con flujo: propuesta → sandbox → revisión CEO → publicación)
- Architects del sistema (con revisión CEO)

### F2. Flujo de aprobación

```
1. Propuesta
   - Crear spec completa siguiendo secciones B1-B6
   - Registrar en ARTIFACT_REGISTRY con definition_status: draft

2. Sandbox
   - Simular contra datos de prueba
   - Validar: campos coherentes, reglas ejecutables, eventos emiten correctamente
   - Output: reporte de simulación

3. Revisión CEO
   - CEO revisa spec + reporte sandbox
   - Aprueba → definition_status: active
   - Rechaza → feedback → vuelta a propuesta
   - Pide cambios → ajustar y re-simular

4. Publicación
   - definition_status: active en ARTIFACT_REGISTRY
   - Disponible para instanciar en producción
```

### F3. Reglas de IA

- IA puede proponer artefactos leyendo este contrato
- IA nunca activa artefactos sin aprobación CEO
- IA nunca modifica artefactos ACTIVE sin aprobación CEO
- IA puede detectar gaps y sugerir artefactos faltantes

---

## G. Versionamiento

- Cambio en field_definitions o validation_rules → nueva versión minor (1.0 → 1.1)
- Cambio en state_model o applies_to → nueva versión major (1.0 → 2.0)
- Instancias existentes siguen con versión anterior
- Solo instancias nuevas usan versión nueva
- Versión anterior se marca DEPRECATED cuando nueva versión es ACTIVE

---

Stamp: DRAFT — Pendiente aprobación CEO
Origen: Sesión de diseño conceptual bodegas/nodos/transfers — 2026-02-26
Resuelve: ARCH-01 (Artifact Contract Specification — pendiente histórico)
