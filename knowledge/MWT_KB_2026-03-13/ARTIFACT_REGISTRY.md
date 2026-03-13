# ARTIFACT_REGISTRY — Registro de Artefactos del Sistema
status: DRAFT
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
version: 1.0

---

Principio: artefacto registrado + ACTIVE = se puede instanciar. Artefacto no registrado = primero se crea, valida y aprueba.

Funciones: registry (catálogo versionado), catalog (referencia consultable), governance index (ciclo de vida y aprobación).

Ref → POL_ARTIFACT_CONTRACT para contrato normativo que todo artefacto debe cumplir.

---

## EXPEDIENTE (artefactos que se pegan a expedientes)

| ID | Artefacto | Version | Category | Status | Ref |
|----|-----------|---------|----------|--------|-----|
| ART-01 | OC Cliente | 1.0 | document | ACTIVE | ENT_PLAT_ARTEFACTOS.B |
| ART-02 | Proforma MWT | 1.0 | document | ACTIVE | ENT_PLAT_ARTEFACTOS.B |
| ART-03 | Decisión B/C | 1.0 | document | ACTIVE | ENT_PLAT_ARTEFACTOS.B |
| ART-04 | Confirmación SAP | 1.0 | document | ACTIVE | ENT_PLAT_ARTEFACTOS.B |
| ART-05 | AWB/BL | 1.0 | document | ACTIVE | ENT_PLAT_ARTEFACTOS.B |
| ART-06 | Cotización flete | 1.0 | document | ACTIVE | ENT_PLAT_ARTEFACTOS.B |
| ART-07 | Aprobación despacho | 1.0 | process | ACTIVE | ENT_PLAT_ARTEFACTOS.B |
| ART-08 | Documentación aduanal | 1.0 | document | ACTIVE | ENT_PLAT_ARTEFACTOS.B |
| ART-09 | Factura MWT | 1.0 | document | ACTIVE | ENT_PLAT_ARTEFACTOS.B |
| ART-10 | Factura comisión | 1.0 | document | ACTIVE | ENT_PLAT_ARTEFACTOS.B |
| ART-11 | Registro costos | 1.0 | pricing | ACTIVE | ENT_PLAT_ARTEFACTOS.B |
| ART-12 | Nota compensación | 1.0 | document | ACTIVE | ENT_PLAT_ARTEFACTOS.B |

## TRANSFER (artefactos que se pegan a transfers entre nodos)

| ID | Artefacto | Version | Category | Status | Ref |
|----|-----------|---------|----------|--------|-----|
| ART-13 | Recepción en nodo | 1.0 | process | DRAFT | [por crear] |
| ART-14 | Preparación / Acondicionamiento | 1.0 | process | DRAFT | [por crear] |
| ART-15 | Despacho inter-nodo | 1.0 | process | DRAFT | [por crear] |
| ART-16 | Transfer pricing approval | 1.0 | pricing | DRAFT | [por crear] |
| ART-17 | Documento de excepción | 1.0 | document | DRAFT | [por crear] |

## NODE (artefactos que se pegan a nodos)

| ID | Artefacto | Version | Category | Status | Ref |
|----|-----------|---------|----------|--------|-----|
| ART-18 | Reporte operativo | 1.0 | report | DRAFT | [por crear] |

## CROSS (artefactos transversales)

(vacío — se agregan cuando aparezca necesidad real)

---

## Ciclo de vida de una definición de artefacto

```
1. DRAFT
   Quién: IA o humano propone spec siguiendo POL_ARTIFACT_CONTRACT
   Qué: definición completa (campos, reglas, eventos, permisos, UI hints)
   Regla: NO puede instanciarse en producción

2. SANDBOX
   Quién: sistema
   Qué: simular artefacto contra datos de prueba
   Validar: inputs/outputs coherentes, reglas funcionan, eventos emiten, UI renderiza
   Output: reporte de simulación

3. REVIEW
   Quién: CEO (único aprobador — ref → POL_STAMP)
   Qué: revisar spec + reporte sandbox
   Decisiones: aprobar / rechazar con feedback / pedir cambios

4. ACTIVE
   Qué: registrado en ARTIFACT_REGISTRY como disponible
   Regla: se puede instanciar en expedientes/transfers/nodos reales
   Versionamiento: nueva versión no rompe instancias existentes (ref → ENT_PLAT_ARTEFACTOS.F)

5. DEPRECATED
   Cuándo: reemplazado por versión nueva o ya no necesario
   Qué: instancias activas siguen con versión anterior
   Campo: superseded_by → ID del reemplazo
   Nuevos usos solo con versión nueva
```

---

## Reglas del registry

- Todo artefacto debe cumplir POL_ARTIFACT_CONTRACT antes de entrar al registry
- No se crean artefactos especulativos. Solo cuando hay uso real.
- Status ACTIVE = se puede usar. Status DRAFT = no se puede usar en producción.
- ID auto-incremental: ART-XX. Nunca reutilizar IDs deprecados.
- Categorías válidas: document | process | pricing | report
- applies_to válidos: expediente | transfer | node | cross

---

## Métricas del registry

Total artefactos: 18
- ACTIVE: 12 (ART-01 a ART-12)
- DRAFT: 6 (ART-13 a ART-18)
- DEPRECATED: 0

---

Stamp: DRAFT — Pendiente aprobación CEO
Origen: Sesión de diseño conceptual bodegas/nodos/transfers — 2026-02-26
