# SCH_CONTRATO_NODO — Schema de Contrato Inteligente entre Nodos
id: SCH_CONTRATO_NODO
status: DRAFT
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
version: 1.0
requires:
  - ENT_PLAT_LEGAL_ENTITY (issuer + receiver con tax_id y status definidos)
  - ENT_COMERCIAL_PRICING (transfer_price_policy base para el territorio)
  - ENT_MARCA_IP (confirmación propiedad marca Rana Walk por issuer)
  - ENT_PLAT_CONTRATO_NODO (ciclo de vida y modelo de ejecución)
policies:
  - POL_INMUTABILIDAD (campos CAPA 2 inmutables desde status: signed)
  - POL_DETERMINISMO (no duplicar parámetros que viven en NodeContract; jurisdiction_mandatory ≠ jurisdiction_elected — son capas distintas)
  - POL_VISIBILIDAD (channel_params y participation_split son [CEO-ONLY]; jurisdiction_mandatory es [INTERNAL]; jurisdiction_elected es visible al receptor)
  - POL_NUNCA_TRADUCIR (tech names: Windmill, n8n, MinIO, SHA-256, ICC, UNCITRAL intocables)
inherits: —
stamp: DRAFT — pendiente aprobación CEO

---

## A. Identidad del schema

| Campo | Valor |
|-------|-------|
| Tipo de output | Dos documentos legales complementarios (ART-20 + ART-21) |
| Generado por | Sistema automáticamente desde parámetros DB |
| Firmado por | CEO (issuer) + representante legal receptor |
| Sellado en | MinIO con hash SHA-256 |
| Verificado por | AI middleware post-firma |
| Rige | Relación operativa completa entre dos LegalEntities |

---

## B. Estructura del contrato — capas

Un NodeContract tiene tres capas que no se mezclan:

```
CAPA 1 — CONSTITUCIÓN (inmutable desde creación)
  Campos que definen QUÉ tipo de contrato es.
  No son editables en ninguna instancia.
  Definen el schema, no los valores.

CAPA 2 — CONFIGURACIÓN (editable antes de firma, inmutable después)
  Campos que el CEO configura para cada par específico de LegalEntities.
  Editables en status: drafting y under_review.
  INMUTABLES desde status: signed (ref → POL_INMUTABILIDAD).
  Si algo cambia → nuevo contrato con superseded_by.

CAPA 3 — EJECUCIÓN (lectura continua del sistema)
  Campos que Windmill y n8n leen para ejecutar reglas.
  Son los mismos que CAPA 2 — no hay duplicación.
  El sistema los lee, no los modifica.
```

---

## C. Campos constitutivos — CAPA 1 (schema fijo)

Estos campos son idénticos en todo NodeContract. No se configuran por instancia.

### C1. Tipo de contrato

| contract_type | Descripción | Documentos generados |
|--------------|-------------|---------------------|
| license_jv | Licencia de marca + JV operativo. Para Operadores con participación. | ART-20 (licencia) + ART-21 (JV) |
| distribution | Distribución sin participación. Para distribuidores estándar. | ART-20 (distribución) |
| subdistribution | Sub-distribución bajo un distribuidor. Hereda restricciones padre. | ART-20 (sub-distribución) |
| service | Acuerdo de servicios entre entidades. | ART-20 (servicios) |

### C2. Cláusulas obligatorias en todo contrato

Independientemente del contract_type, todo NodeContract debe incluir:

| Cláusula | Contenido mínimo obligatorio |
|----------|------------------------------|
| Identificación de partes | Razón social + tax_id + representante legal de cada parte |
| Objeto del contrato | Descripción clara del objeto según contract_type |
| Territorio | Definición geográfica exacta + canales incluidos |
| Vigencia | effective_from + condición de terminación o plazo |
| Restricciones heredadas | Restricciones del contrato padre aplicables (si parent_contract ≠ null) |
| Propiedad intelectual | PI del issuer permanece del issuer. Receptor tiene licencia de uso, no propiedad. |
| Confidencialidad | Información operativa y financiera es confidencial entre las partes |
| Ley aplicable y jurisdicción | Ley que rige el contrato (jurisdiction_elected.governing_law) + foro elegido (jurisdiction_elected). Compliance informa registros obligatorios en cada jurisdicción (jurisdiction_mandatory). CEO decide el foro. |
| Mecanismo de salida | Preaviso + condiciones + efecto sobre licencias |
| Integridad del sistema | Receptor acepta operar dentro de la plataforma mwt.one según las reglas del sistema |

### C3. Cláusulas adicionales por contract_type

**license_jv (Camino A — Operador BR):**

| Cláusula | Contenido |
|----------|-----------|
| Licencia de marca | Uso no exclusivo / exclusivo de Rana Walk en territorio. Licenciante: Muito Work Limitada. |
| Participación societaria | Estructura de participación (%), aportes de cada parte, distribución de resultados |
| Autonomía operativa | Receptor opera con autonomía total. Issuer no supervisa operación diaria. |
| Aportes tecnológicos | Detalle de lo que MWT aporta: plataforma, scanner (cuando disponible), know-how |
| Compromisos del receptor | Canales, capital de trabajo, equipo, regulaciones locales |
| Período de desarrollo | Plazo garantizado sin metas numéricas + fecha de revisión conjunta |
| Renovación | Condiciones y períodos de renovación automática |

**distribution:**

| Cláusula | Contenido |
|----------|-----------|
| Términos comerciales | Precio de transferencia, condiciones de pago, volúmenes |
| Exclusividad | Si aplica, con condición de medios |
| Obligaciones de reporte | Frecuencia, formato, contenido mínimo |
| Sub-distribución | Si está permitida y bajo qué condiciones |

---

## D. Campos configurables por instancia — CAPA 2

Estos campos los define el CEO para cada par específico de LegalEntities.
Son editables en DRAFTING y UNDER_REVIEW. Inmutables desde SIGNED.

### D1. Campos de configuración

```
# Partes
issuer_entity_id: ref → LegalEntity.entity_id
receiver_entity_id: ref → LegalEntity.entity_id
issuer_signatory: string          # Nombre legal del firmante issuer
receiver_signatory: string        # Nombre legal del firmante receptor

# Territorio
territory: string[]               # ["BR"] | ["BR-SP", "BR-RJ"] | etc.
channels: string[]                # ["all"] | ["retail", "industrial", "amazon_br"]
exclusivity: boolean

# Financiero [CEO-ONLY]
transfer_price_policy: {
  basis: enum                     # fob_cost | fob_plus_percentage | fixed_list
  adjustment_trigger: string      # "cuando costo FOB varíe >5%" | "anual" | etc.
  adjustment_direction: string    # "sube y baja con el costo" — política simétrica
}
participation_split: {            # Solo para license_jv
  issuer_pct: decimal             # 30
  receiver_pct: decimal           # 70
  distribution_trigger: string    # "trimestral después de cubrir costos operativos"
}
channel_params: {                 # Parámetros por canal para cálculo de contribución
  amazon_br_commission_pct: decimal
  subdistributor_discount_pct: decimal
  scanner_pos_operational_cost: decimal
  [canal]: {params}
}

# Umbrales de alerta [CEO-ONLY]
alert_thresholds: {
  channel_contribution_min_pct: decimal   # Alerta si canal baja de este %
  report_overdue_days: int                # Alerta si reporte no llega en N días
  contract_deviation_tolerance: decimal  # % de desviación antes de alerta
}

# Idioma del contrato
contract_languages: string[]      # ["ES"] | ["ES", "PT-BR"] | ["ES", "EN"]
prevailing_language: {            # Solo cuando contract_languages.length > 1
  jurisdiction_issuer: string     # "ES" para CR
  jurisdiction_receiver: string   # "PT-BR" para BR | "EN" para USA
} | null

# Jurisdicción — DOS CAPAS DISTINTAS
# CAPA A: registros obligatorios — Compliance los identifica, son hechos legales
jurisdiction_mandatory: [
  {
    country: string               # "BR" | "CR"
    authority: string             # "INPI" | "APOSTILLE"
    type: string                  # "trademark_license" | "apostille"
    required: boolean
    status: enum                  # pending | in_process | registered | not_applicable
    blocking: boolean             # true = impide SIGNED → ACTIVE
    registration_number: string | null
  }
]
# CAPA B: foro elegido — CEO lo decide, única palanca real
jurisdiction_elected: {
  type: enum                      # arbitration | tribunal_issuer | tribunal_receiver | tribunal_neutral
  institution: string | null      # "ICC" | "UNCITRAL" | "Tribunales de CR"
  seat: string | null             # Ciudad/país sede
  governing_law: string           # Ley aplicable: "CR" | "BR" | "Panama" | etc.
}

# Períodos
effective_from: date
development_period_months: int    # 36
review_at_month: int              # 33
renewal_period_months: int        # 24
exit_notice_days: int             # 120

# Restricciones para hijos
child_restrictions: {
  min_resale_price_policy: string  # Cómo se calcula precio mínimo de reventa
  prohibited_channels: string[]    # Canales que hijos no pueden usar
  reporting_frequency: string      # Frecuencia mínima de reporte que hijos deben cumplir
  territory_sub_grant: string      # Reglas para sub-otorgar territorio
}
```

---

## E. Campos de ejecución — CAPA 3

Son los campos de CAPA 2 leídos por el sistema para ejecutar reglas. No se duplican.

| Automatización | Lee | Produce |
|---------------|-----|---------|
| AUT-040 (verificación IA) | documents.signed_hash + todos los campos | ai_verification result |
| AUT-041 (contribución canal) | channel_params + transfer_price_policy | tabla contribución por canal |
| AUT-042 (forecast) | transfer_price_policy + datos históricos de órdenes | proyección siguiente pedido |
| AUT-043 (alerta canal) | alert_thresholds.channel_contribution_min_pct | alerta CEO + Operador |
| AUT-044 (reporte trimestral) | participation_split + datos órdenes período | reporte para MWT |
| AUT-045 (verificación cumplimiento) | todos los campos de configuración + operación real | lista de conformidades/no-conformidades |
| AUT-046 (alerta no-conformidad) | output AUT-045 | alerta con referencia a cláusula específica |
| AUT-047 (contrato hijo) | child_restrictions + territory + channels | borrador NC hijo pre-configurado |

---

## F. Documentos generados — ART-20 y ART-21

Ref → ARTIFACT_REGISTRY para registro formal.

### F1. ART-20 — Documento legal principal

| Propiedad | Valor |
|-----------|-------|
| artifact_type_id | ART-20 |
| name | NodeContract — Documento Legal Principal |
| category | document |
| applies_to | [legal_entity_contract] |
| format | PDF (generado desde template + parámetros DB) |
| firmantes | CEO issuer + representante receptor |
| sellado | SHA-256 post-firma, almacenado en MinIO |
| idioma | Determinado por contract_languages. Si monolingüe: idioma del receptor. Si bilingüe: ambas versiones auténticas en un solo PDF. prevailing_language define cuál rige en cada jurisdicción. |

Contenido generado automáticamente: todas las cláusulas de C2 y C3 con los valores de D1 interpolados. El CEO revisa el borrador antes de enviar al receptor.

### F2. ART-21 — Documento complementario (para license_jv)

| Propiedad | Valor |
|-----------|-------|
| artifact_type_id | ART-21 |
| name | NodeContract — Acuerdo JV Operativo |
| category | document |
| applies_to | [legal_entity_contract] |
| format | PDF |
| firmantes | CEO issuer + representante receptor |
| sellado | SHA-256 post-firma, almacenado en MinIO |
| idioma | Bilingüe ES + PT-BR para NC-0001 (MWT-CR → FRANQ-BR). PT-BR prevalece en BR. |

Contenido: cláusulas específicas del JV (participación, aportes, autonomía operativa, período de desarrollo, renovación). Se firma junto con ART-20 pero es documento separado por claridad jurídica.

---

## G. Restricciones de herencia — reglas del sistema

```
REGLA 1 — Un hijo no puede tener más derechos que su padre
  Si NC padre dice channels: ["retail", "industrial"]
  → NC hijo no puede agregar "amazon_br"
  Sistema bloquea si hijo intenta incluir canal no autorizado por padre

REGLA 2 — Precio mínimo se hereda hacia abajo
  Si NC padre define min_resale_price_policy
  → NC hijo hereda la misma política o una más restrictiva
  Sistema valida antes de permitir status: signed en hijo

REGLA 3 — Territorio se subdivide, no se expande
  Si NC padre cubre territory: ["BR"]
  → NC hijo puede ser territory: ["BR-SP"]
  → NC hijo NO puede ser territory: ["BR", "AR"]
  Sistema bloquea expansión de territorio más allá del padre

REGLA 4 — Reporting no puede ser menos frecuente que el padre
  Si NC padre requiere reporting mensual
  → NC hijo no puede requerir solo trimestral
  Sistema alerta pero no bloquea (es configuración del Operador)
```

---

## H. Requires del schema

Antes de generar ART-20 + ART-21, el sistema verifica que existan:

```
requires:
  - ENT_PLAT_LEGAL_ENTITY → issuer con status: active, tax_id definido
  - ENT_PLAT_LEGAL_ENTITY → receiver con status: active | onboarding, tax_id definido
  - ENT_COMERCIAL_PRICING → transfer_price_policy base para el territorio
  - ENT_MARCA_IP → confirmación de propiedad de marca Rana Walk por issuer
  - parent_contract → si no es contrato raíz, padre debe estar en status: active
  - Si contract_type = license_jv: confirmación registro marca en territorio del receptor
    (o registro en proceso — el sistema permite continuar con warning, no bloqueo)
  - jurisdiction_elected definido por CEO antes de generar ART-20
  - jurisdiction_mandatory evaluado por Compliance antes de transición SIGNED → ACTIVE
```

### H2. Regla de idioma

```
Si issuer.country ≠ receiver.country:
  contract_languages debe tener al menos 2 elementos
  prevailing_language debe estar definido
  Sistema genera un único PDF con ambas versiones auténticas en paralelo
  Un solo SHA-256 sella el documento completo — no hay dos archivos separados

Si issuer.country = receiver.country:
  contract_languages puede tener 1 elemento
  prevailing_language = null
```

### H3. Regla de activación — bloqueos

```
SIGNED → ACTIVE requiere:
  [1] ai_verification.result = match
      O (ai_verification.result = mismatch AND ceo_reviewed = true)
  [2] jurisdiction.mandatory_registrations donde
      required = true AND blocking = true AND status ≠ registered
      → lista vacía (todos resueltos o marcados not_applicable)
  [3] jurisdiction_elected definido (no puede ser null en ACTIVE)

Si cualquier condición falla → sistema bloquea y notifica CEO con causa exacta.
```

---

## Z. Pendientes

| ID | Pendiente | Desbloquea | Quién decide |
|----|-----------|-----------|-------------|
| Z1 | Template ART-20 por contract_type + idioma (ES, PT-BR, EN) | Generación automática documentos | CEO + abogado |
| Z2 | Template ART-21 bilingüe ES + PT-BR para FRANQ-BR | ART-21 generación automática | CEO + abogado BR |
| Z3 | Lógica de extracción IA del PDF — qué campos y cómo | AUT-040 spec completa | Architect + CEO |
| Z4 | elected_forum NC-0001: tipo (arbitraje/tribunal), institución, sede, ley aplicable | Cláusula C2 en ART-20 | CEO + abogado |
| Z5 | Definición formal de channel_params para BR | AUT-041 operativo | CEO [CEO-ONLY] |
| Z6 | Compliance debe mapear jurisdiction_mandatory para cada mercado nuevo (BR listo, USA y CR pendientes) | Bloqueos de activación correctos por mercado | Compliance |
| Z7 | Definir cuáles jurisdiction_mandatory son blocking = true vs solo warning | Precisión del bloqueo SIGNED → ACTIVE | CEO + Compliance |

---

Stamp: DRAFT — pendiente aprobación CEO
Origen: Sesión de diseño arquitectura contratos inteligentes — 2026-03-09
