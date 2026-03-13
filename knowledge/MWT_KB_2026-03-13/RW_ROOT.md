# RW_ROOT — Root Index
## Rana Walk / MWT — Arquitectura de Conocimiento v3.3
### Última actualización: 2026-03-13

---

## META-REGLAS DEL SISTEMA

- Todo documento es UTF-8 (POL_UTF8)
- Todo entity tiene: id, version, domain, status, visibility, stamp
- Todo schema tiene: id, version, requires[], policies[], inherits
- Cambio se propaga hacia abajo, nunca hacia arriba
- Nuevo dominio → editar este Root Index
- Nueva estructura de output → Schema en SCHEMA_REGISTRY
- Nuevo dato → Entity en Domain Index correspondiente
- Nueva regla operativa → Playbook en Domain Index correspondiente
- Nueva regla del sistema → Policy en /policies/

## TAXONOMÍA (7 tipos)

| Tipo | Prefijo | Función |
|------|---------|---------|
| Index | IDX_ | Router. Sabe dónde vive cada cosa |
| Schema | SCH_ | Plantilla de ensamblaje con slots |
| Entity | ENT_ | Data pura inyectable |
| Loc | LOC_ | Data localizada por idioma |
| Policy | POL_ | Constraint transversal del sistema |
| Playbook | PLB_ | Instrucciones operativas de dominio/agente |
| Lote | LOTE_SM_SPRINT* | Paquete de ejecución por sprint — solo plataforma |

## REGLAS DE SCHEMAS

- Schema existe = yo puedo ensamblarlo
- Schema no existe = primero se crea, itera y aprueba
- No se crean schemas especulativos. Solo cuando hay uso real.
- Todo schema declara: requires, policies, inherits
- Antes de ensamblar: verificar que todas las entities del requires están disponibles
- Si falta entity → escalar. Nunca inventar.
- Output ensamblado = DRAFT hasta que pase validación de policies
- Schema aprobado en producción = snapshot inmutable (va a archivo, no aquí)

### Ciclo de vida de un Schema

1. Necesidad detectada
2. DRAFT — se define slots, requires, policies, herencia
3. PROTOTIPO — se ensambla con una entity real para validar
4. ITERACIÓN — CEO revisa, ajusta slots, corrige requires
5. APROBADO — se agrega al registry como disponible
6. ACTIVO — disponible para ensamblaje con cualquier entity
7. DEPRECATED — si se reemplaza por otro schema

## DOMINIOS (10)

| Dominio | Index | Ubicación |
|---------|-------|-----------|
| Producto | IDX_PRODUCTO | /producto/ |
| Marca | IDX_MARCA | /marca/ |
| Comercial | IDX_COMERCIAL | /comercial/ |
| Operaciones | IDX_OPS | /operaciones/ |
| Mercados | IDX_MERCADOS | /mercados/ |
| Marketplace | IDX_MARKETPLACE | /marketplace/ |
| Compliance | IDX_COMPLIANCE | /compliance/ |
| Gobernanza | IDX_GOBERNANZA | /gobernanza/ |
| Plataforma | IDX_PLATAFORMA | /plataforma/ |
| Distribución | IDX_DISTRIBUCION | /distribucion/ |

## SCHEMAS

Catálogo de estructuras de output → SCHEMA_REGISTRY (/schemas/)

## POLICIES

21 constraints transversales → /policies/

## REGISTROS ESPECIALES

Archivos que no pertenecen a la taxonomía de 7 tipos pero son parte operativa del proyecto:

| Archivo | Tipo | Función |
|---------|------|---------|
| ARTIFACT_REGISTRY.md | Registry | Catálogo versionado de artefactos del sistema |
| MANIFIESTO_CAMBIOS.md | Manifest | Log de cambios pendientes de aplicar a la KB |
| REPORTE_SESION_ISO_20260301.md | Reporte | Contexto de sesión para continuidad |
| REPORTE_SESION_SWARM_20260313.md | Reporte | Contexto sesión Swarm multi-agente 2026-03-13 |
| COM07_COM08_nomenclatura_marluvas_v1.md | Entity comercial | Nomenclatura tokens Marluvas |
| COM07_COM08_nomenclatura_marluvas_v1.json | Data file | JSON motor de descripciones Marluvas |

---

Stamp: BOOTSTRAP VIGENTE 2026-03-01
Vencimiento: 2026-05-30
Estado: VIGENTE
Aprobador final: CEO

Changelog:
- v3.0: dominio Distribución agregado, 10 dominios, 17 policies
- v3.1: +registros especiales (LOTE_SM, MANIFIESTO, COM07_COM08)
- v3.2: taxonomía 6→7 tipos (Lote formalizado). LOTE_SM_SPRINT* movido de registros especiales a taxonomía.
- v3.3: +REPORTE_SESION_SWARM_20260313 en registros especiales
