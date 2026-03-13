# ENT_PLAT_LEGAL_ENTITY — Entidades Legales (Tenant Raíz)
status: DRAFT
visibility: [INTERNAL] excepto campos marcados [CEO-ONLY]
domain: Plataforma (IDX_PLATAFORMA)
version: 1.0

---

## A. Concepto

LegalEntity es la raíz administrativa del sistema. Todo cuelga de ella: nodos, transfers, expedientes, usuarios, automatizaciones, dashboards.

### A1. Dualidad declarada

LegalEntity existe en dos planos simultáneos:

**Plano de negocio:** entidad jurídica real con efectos legales, contables y fiscales. Tiene cédula/CNPJ/EIN, jurisdicción, obligaciones tributarias, contratos con terceros. Existe aunque no haya sistema.

**Plano de plataforma:** tenant raíz del sistema. Define el perímetro de visibilidad, acceso, datos y acciones disponibles. Cada LegalEntity ve solo su mundo dentro del sistema.

Regla: nunca tratar LegalEntity como carpeta de configuración. Tiene consecuencias legales y contables reales. Ref → ENT_OPS_EXPEDIENTE (issuing_entity), ENT_COMERCIAL_MODELOS (facturación por modelo).

### A2. Relación con otras entidades

```
LegalEntity (1) ──administra──▶ Node (N)
LegalEntity (1) ──participa──▶ Transfer (N) como from o to
LegalEntity (1) ──emite──▶ Expediente (N)
LegalEntity (1) ──tiene──▶ User (N) con acceso al dashboard
LegalEntity (1) ──opera en──▶ Frontend (1) → mwt.one o portal.mwt.one
```

---

## B. Modelo

```
LegalEntity {
  entity_id: string                # MWT-CR, SONDEL-CR, FRANQ-BR, etc.
  legal_name: string               # "Muito Work Limitada"
  country: ref → ENT_MERCADO_{X}   # Jurisdicción
  tax_id: string                   # Cédula jurídica / CNPJ / EIN
  
  # Rol en la red
  role: enum                       # owner | distributor | subdistributor | 3pl | factory
  relationship_to_mwt: enum       # self | franchise | distribution | service
  
  # Administración
  nodes: ref[] → ENT_OPS_NODOS    # Nodos que administra
  users: ref[] → User              # Personas con acceso
  
  # Dashboard y visibilidad
  frontend: enum                   # mwt.one | portal.mwt.one
  visibility_level: enum           # full | partner | limited
  pricing_visibility: enum         # internal | client | none
  
  # Estado
  status: enum                     # active | onboarding | inactive
}
```

---

## C. Entidades legales conocidas

**SSOT:** Esta tabla es la fuente única de verdad para entidades legales del sistema. Otros documentos (ENT_OPS_EXPEDIENTE, ENT_PLAT_MODULOS, ENT_COMERCIAL_MODELOS) deben referenciar este entity con `ref → ENT_PLAT_LEGAL_ENTITY.C`, no duplicar datos de entidades legales. Ref → POL_DETERMINISMO (Dato Único).

| entity_id | legal_name | country | tax_id | role | relationship | frontend | status |
|-----------|-----------|---------|--------|------|-------------|----------|--------|
| MWT-CR | Muito Work Limitada | CR | [CEO-ONLY] | owner | self | mwt.one | ACTIVE |
| AMAZON-US | Amazon.com Services LLC | US | — | marketplace | service | — (externo) | ACTIVE |
| MARLUVAS-BR | Marluvas SA | BR | [CEO-ONLY] | factory | service | — (externo) | ACTIVE |
| SONDEL-CR | [PENDIENTE — NO INVENTAR] | CR | [PENDIENTE] | [PENDIENTE] | [PENDIENTE] | portal.mwt.one | [PENDIENTE CEO] |
| FRANQ-BR | [PENDIENTE — NO INVENTAR] | BR | [PENDIENTE] | distributor / franchise | franchise | portal.mwt.one | [PENDIENTE CEO] |
| FACTORY-CN | [PENDIENTE — NO INVENTAR] | CN | [PENDIENTE] | factory | service | — (externo) | [PENDIENTE CEO] |

Nota: Amazon, Marluvas y Factory CN son entidades legales externas sin acceso al sistema MWT. Se modelan como LegalEntity para trazabilidad de ownership en nodos y transfers, pero no tienen dashboard ni usuarios en mwt.one/portal.mwt.one.

---

## D. Reglas de visibilidad por LegalEntity

### D1. MWT (role: owner, frontend: mwt.one)
- Ve TODOS los nodos, transfers, expedientes, automatizaciones
- Pricing: vista internal completa [CEO-ONLY]
- Puede crear y administrar automatizaciones globales
- Puede gestionar LegalEntities de terceros (onboarding, permisos)

### D2. Distribuidor/Franquiciado (frontend: portal.mwt.one)
- Ve solo los nodos que administra
- Ve solo los transfers donde es from o to
- Pricing: vista client solamente
- No ve expedientes de otras entidades legales
- No ve costos internos MWT [CEO-ONLY]
- Puede administrar automatizaciones de sus propios nodos
- Ref → POL_VISIBILIDAD para reglas detalladas

### D3. Entidades externas sin acceso (Amazon, Marluvas, Factory CN)
- Sin dashboard, sin usuarios en el sistema
- Datos fluyen vía conectores (SP-API, email, etc.)
- Se referencian en nodos y transfers para trazabilidad

---

## E. Dashboard como materialización de LegalEntity

El dashboard no es una pantalla genérica. Es la materialización de todo lo que una LegalEntity administra, organizado por contexto:

| Vista | MWT (mwt.one) | Distribuidor (portal.mwt.one) |
|-------|---------------|-------------------------------|
| Nodos | Todos los nodos de la red | Solo sus nodos |
| Transfers | Todos | Solo donde es parte |
| Expedientes | Todos | Solo los suyos |
| Inventario | Global con semáforos | Su stock por nodo |
| Costos | Vista internal completa | No visible |
| Pricing | Internal + client | Solo client |
| Automatizaciones | Todas + gobernanza global | Solo las ancladas a sus nodos |
| Conectores | Todos (SP-API, Helium, etc.) | Solo los suyos (WMS, CSV, etc.) |
| Acciones | Todo (crear, aprobar, configurar) | Scoped a su perímetro |

Misma arquitectura, diferente scope, diferente profundidad.
Ref → ENT_PLAT_FRONTENDS para implementación técnica de surfaces.

---

## Z. Pendientes

| ID | Pendiente | Desbloquea | Quién decide |
|----|-----------|-----------|-------------|
| Z1 | Definir Sondel: ¿qué entidad legal es? ¿tipo? ¿relación? | ENT_PLAT_LEGAL_ENTITY.C completo | CEO |
| Z2 | Definir franquiciado BR: ¿existe? ¿entidad legal? | ENT_PLAT_LEGAL_ENTITY.C completo | CEO |
| Z3 | Definir fábrica CN: ¿nombre legal? | Trazabilidad completa | CEO |
| Z4 | Tax IDs de entidades externas (si aplica) | Compliance | CEO |

---

Stamp: DRAFT — Pendiente aprobación CEO
Origen: Sesión de diseño conceptual bodegas/nodos/transfers — 2026-02-26
