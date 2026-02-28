# ENT_PLAT_LEGAL_ENTITY — Entidades Legales (Tenant Raíz)
status: DRAFT
visibility: [INTERNAL] excepto campos marcados [CEO-ONLY]
domain: Plataforma (IDX_PLATAFORMA)
version: 2.0

---

## A. Concepto

LegalEntity es la raíz administrativa del sistema. Todo cuelga de ella: nodos, transfers, expedientes, usuarios, automatizaciones, dashboards.

### A1. Dualidad declarada

LegalEntity existe en dos planos simultáneos:

**Plano de negocio:** entidad jurídica real con efectos legales, contables y fiscales. Tiene cédula/CNPJ/EIN, jurisdicción, obligaciones tributarias, contratos con terceros. Existe aunque no haya sistema.

**Plano de plataforma:** tenant raíz del sistema. Define el perímetro de visibilidad, acceso, datos y acciones disponibles. Cada LegalEntity ve solo su mundo dentro del sistema.

Regla: nunca tratar LegalEntity como carpeta de configuración. Tiene consecuencias legales y contables reales. Ref → ENT_OPS_EXPEDIENTE (issuing_entity), ENT_COMERCIAL_MODELOS (facturación por modelo).

### A2. Estructura corporativa

```
Muito Work Limitada (CR) — HOLDING
  └── MWT One S.A. (PA) — SUBSIDIARIA
        └── opera mwt.one (plataforma)
```

Muito Work Limitada es dueña de todo. MWT One S.A. es la subsidiaria panameña que opera la estructura internacional y la plataforma mwt.one.

Propiedad de marcas (Rana Walk, Marluvas distribución, Tecmater): [PENDIENTE — NO INVENTAR. Requiere decisión CEO: ¿propiedad de Muito CR o MWT One PA?]

### A3. Relación con otras entidades

```
LegalEntity (1) ──administra──▶ Node (N)
LegalEntity (1) ──participa──▶ Transfer (N) como from o to
LegalEntity (1) ──emite──▶ Expediente (N)
LegalEntity (1) ──tiene──▶ User (N) con acceso al dashboard
LegalEntity (1) ──opera en──▶ mwt.one (plataforma única, RBAC filtra vista)
```

---

## B. Modelo

```
LegalEntity {
  entity_id: string                # MUITO-CR, MWT-PA, SONDEL-CR, etc.
  legal_name: string               # "Muito Work Limitada"
  country: ref → ENT_MERCADO_{X}   # Jurisdicción
  tax_id: string                   # Cédula jurídica / CNPJ / EIN
  
  # Estructura corporativa
  parent_entity: ref → LegalEntity? # null para holding, entity_id para subsidiarias
  
  # Rol en la red
  role: enum                       # holding | subsidiary | distributor | subdistributor | 3pl | factory | marketplace
  relationship_to_muito: enum      # self | subsidiary | franchise | distribution | service
  
  # Administración
  nodes: ref[] → ENT_OPS_NODOS    # Nodos que administra
  users: ref[] → User              # Personas con acceso
  
  # Dashboard y visibilidad (todo en mwt.one, RBAC filtra)
  visibility_level: enum           # full | partner | limited
  pricing_visibility: enum         # internal | client | none
  
  # Estado
  status: enum                     # active | onboarding | inactive
}
```

---

## C. Entidades legales conocidas

**SSOT:** Esta tabla es la fuente única de verdad para entidades legales del sistema. Otros documentos (ENT_OPS_EXPEDIENTE, ENT_PLAT_MODULOS, ENT_COMERCIAL_MODELOS) deben referenciar este entity con `ref → ENT_PLAT_LEGAL_ENTITY.C`, no duplicar datos de entidades legales. Ref → POL_DETERMINISMO (Dato Único).

| entity_id | legal_name | country | tax_id | parent | role | relationship | status |
|-----------|-----------|---------|--------|--------|------|-------------|--------|
| MUITO-CR | Muito Work Limitada | CR | [CEO-ONLY] | null (raíz) | holding | self | ACTIVE |
| MWT-PA | MWT One S.A. | PA | [CEO-ONLY] | MUITO-CR | subsidiary | subsidiary | ACTIVE |
| AMAZON-US | Amazon.com Services LLC | US | — | null | marketplace | service | ACTIVE |
| MARLUVAS-BR | Marluvas SA | BR | [CEO-ONLY] | null | factory | service | ACTIVE |
| SONDEL-CR | [PENDIENTE — NO INVENTAR] | CR | [PENDIENTE] | null | [PENDIENTE] | [PENDIENTE] | [PENDIENTE CEO] |
| FRANQ-BR | [PENDIENTE — NO INVENTAR] | BR | [PENDIENTE] | null | distributor / franchise | franchise | [PENDIENTE CEO] |
| FACTORY-CN | [PENDIENTE — NO INVENTAR] | CN | [PENDIENTE] | null | factory | service | [PENDIENTE CEO] |

Nota: Amazon, Marluvas y Factory CN son entidades legales externas sin acceso al sistema MWT. Se modelan como LegalEntity para trazabilidad de ownership en nodos y transfers, pero no tienen usuarios en mwt.one.

Nota 2: Todos los usuarios (CEO, distribuidores, clientes B2B) acceden a mwt.one. No hay portal separado. RBAC filtra qué ve cada quien según su LegalEntity y rol.

---

## D. Reglas de visibilidad por LegalEntity

### D1. Muito / MWT (role: holding/subsidiary, visibility: full)
- Ve TODOS los nodos, transfers, expedientes, automatizaciones
- Pricing: vista internal completa [CEO-ONLY]
- Puede crear y administrar automatizaciones globales
- Puede gestionar LegalEntities de terceros (onboarding, permisos)

### D2. Distribuidor/Franquiciado (role: distributor, visibility: partner)
- Accede a mwt.one con su usuario (RBAC filtra vista)
- Ve solo los nodos que administra
- Ve solo los transfers donde es from o to
- Pricing: vista client solamente
- No ve expedientes de otras entidades legales
- No ve costos internos MWT [CEO-ONLY]
- Puede administrar automatizaciones de sus propios nodos
- Ref → POL_VISIBILIDAD para reglas detalladas

### D3. Cliente B2B (role: client, visibility: limited)
- Accede a mwt.one con su usuario (RBAC filtra vista)
- Ve solo sus expedientes con estado simplificado
- Ve solo sus documentos (proforma, factura, BL/AWB)
- No ve costos, no ve otros clientes
- Valor: deja de enviar correos preguntando estado

### D4. Entidades externas sin acceso (Amazon, Marluvas, Factory CN)
- Sin usuarios en el sistema
- Datos fluyen vía conectores (SP-API, email, etc.)
- Se referencian en nodos y transfers para trazabilidad

---

## E. Dashboard como materialización de LegalEntity

El dashboard no es una pantalla genérica. Es la materialización de todo lo que una LegalEntity administra, organizado por contexto. Todos acceden a mwt.one — RBAC filtra la vista:

| Vista | Muito/MWT (full) | Distribuidor (partner) | Cliente B2B (limited) |
|-------|-----------------|----------------------|---------------------|
| Nodos | Todos | Solo suyos | No visible |
| Transfers | Todos | Solo donde es parte | No visible |
| Expedientes | Todos | Solo suyos | Solo suyos (simplificado) |
| Inventario | Global con semáforos | Su stock por nodo | No visible |
| Costos | Vista internal completa | No visible | No visible |
| Pricing | Internal + client | Solo client | No visible |
| Documentos | Todos | Solo suyos | Solo suyos |
| Tracking | Todos | Solo suyos | Solo suyos |
| Acciones | Todo | Scoped a su perímetro | Solo lectura |

Misma plataforma, diferente scope, diferente profundidad.
Ref → ENT_PLAT_FRONTENDS para implementación técnica.

---

## Z. Pendientes

| ID | Pendiente | Desbloquea | Quién decide |
|----|-----------|-----------|-------------|
| Z1 | Propiedad de marcas: ¿Muito CR o MWT One PA? | Estructura IP completa | CEO |
| Z2 | Definir Sondel: ¿qué entidad legal es? ¿tipo? ¿relación? | C completo | CEO |
| Z3 | Definir franquiciado BR: ¿existe? ¿entidad legal? | C completo | CEO |
| Z4 | Definir fábrica CN: ¿nombre legal? | Trazabilidad completa | CEO |
| Z5 | Tax IDs de entidades externas (si aplica) | Compliance | CEO |

---

Stamp: DRAFT — Pendiente aprobación CEO
Origen: Sesión de diseño conceptual bodegas/nodos/transfers — 2026-02-26
Actualizado: 2026-02-27 — Corrección estructura corporativa (Muito CR holding, MWT One PA subsidiaria) + eliminación portal.mwt.one (todo converge en mwt.one con RBAC)
