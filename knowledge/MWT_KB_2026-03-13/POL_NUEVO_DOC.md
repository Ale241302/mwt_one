# POL_NUEVO_DOC — Regla de Creación

| Necesito... | Creo un... | Ubicación |
|-------------|------------|-----------|
| Estructura de output nueva | Schema (SCH_) | /schemas/ + SCHEMA_REGISTRY |
| Dato nuevo | Entity (ENT_) | Domain Index correspondiente |
| Traducción/adaptación idioma | Loc (LOC_) | Junto a su entity padre |
| Regla del sistema | Policy (POL_) | /policies/ |
| Instrucción operativa | Playbook (PLB_) | Domain Index correspondiente |
| Ruta nueva | Index (IDX_) | Root Index si dominio nuevo |

## Regla
- Nunca mezclar tipos: dato en entity, instrucción en playbook, estructura en schema
- Si no sabés qué tipo es → probablemente es entity (dato puro)

---
Stamp: BOOTSTRAP VIGENTE 2026-03-01
Vencimiento: 2026-05-30
Estado: VIGENTE
Aprobador final: CEO
