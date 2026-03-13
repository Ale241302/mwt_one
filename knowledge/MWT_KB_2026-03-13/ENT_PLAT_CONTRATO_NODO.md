# ENT_PLAT_CONTRATO_NODO — Contratos Inteligentes entre Nodos
id: ENT_PLAT_CONTRATO_NODO
status: DRAFT
visibility: [INTERNAL] excepto campos marcados [CEO-ONLY]
domain: Plataforma (IDX_PLATAFORMA)
version: 1.0
stamp: DRAFT — pendiente aprobación CEO

---

## A. Concepto

Un NodeContract es un **contrato inteligente privado** que gobierna la relación comercial y operativa entre dos LegalEntities dentro de la red MWT. Combina la inmutabilidad y ejecución automática de los smart contracts con la ejecutabilidad legal directa de un documento firmado.

### A1. Principio fundacional

El contrato no es un PDF archivado — es el núcleo operativo de la relación entre nodos. Cada orden, transfer, reporte y alerta que involucra a las dos partes ejecuta contra las reglas del contrato activo. La desviación se detecta automáticamente, no cuando ya es un problema legal.

### A2. Analogía con smart contracts

| Propiedad smart contract | Implementación en MWT |
|--------------------------|----------------------|
| Inmutabilidad | POL_INMUTABILIDAD + hash SHA-256 del documento sellado |
| Ejecución automática | Windmill (cálculos) + n8n (triggers y alertas) |
| Trazabilidad completa | Bus de eventos ENT_PLAT_EVENTOS — append-only |
| Verificación independiente | AI middleware lee PDF firmado y compara contra DB |
| Sin intermediario | Sistema ejecuta reglas sin intervención manual |
| Registro histórico permanente | MinIO (documento) + PostgreSQL (parámetros) |

MWT es el nodo raíz del sistema. No se necesita descentralización — la inmutabilidad la garantiza la arquitectura, no el consenso distribuido. Eso es una ventaja: más rápido, más barato, legalmente ejecutable en tribunales convencionales.

### A3. Diferencia crítica con contratos convencionales

```
Contrato convencional:
  Documento firmado → archivado → operación manual → desviación detectada tarde

NodeContract MWT:
  Documento firmado → sellado con hash → parámetros en DB → 
  sistema ejecuta reglas → desviación detectada automáticamente →
  alerta al CEO antes de que sea problema legal
```

### A4. Relación con otras entidades

```
NodeContract (1) ──vincula──▶ LegalEntity (2) [emisor + receptor]
NodeContract (1) ──pertenece a cadena──▶ NodeContract padre (0..1)
NodeContract (1) ──genera──▶ Artefacto ART-20 (documento legal)
NodeContract (1) ──genera──▶ Artefacto ART-21 (documento legal complementario)
NodeContract (1) ──ancla──▶ Automation (N) [ejecutores de reglas]
NodeContract (1) ──registra eventos en──▶ ENT_PLAT_EVENTOS (bus)
NodeContract (1) ──almacena en──▶ MinIO (documento PDF firmado)
NodeContract (1) ──verificado por──▶ AI middleware (coherencia DB vs PDF)
```

---

## B. Modelo

```
NodeContract {
  contract_id: string              # NC-XXXX (auto-increment)
  contract_type: enum              # license_jv | distribution | subdistribution | service
  version: semver                  # 1.0.0

  # Partes
  issuer: ref → LegalEntity        # Quién emite (MWT-CR en contratos raíz)
  receiver: ref → LegalEntity      # Quién recibe (FRANQ-BR, SONDEL-CR, etc.)

  # Cadena de herencia
  parent_contract: ref → NodeContract | null  # null = contrato raíz
  child_contracts: ref[] → NodeContract       # Contratos hijos que hereda restricciones

  # Territorio y alcance
  territory: string[]              # Países/regiones cubiertos
  channels: string[]               # Canales incluidos (all | retail | industrial | medical | amazon | marketplace | b2b | digital)
  exclusivity: boolean             # Exclusividad sobre territory + channels

  # Parámetros financieros [CEO-ONLY]
  transfer_price_policy: Object    # Reglas de precio de transferencia por SKU/volumen
  participation_split: Object      # % issuer / % receiver (ej: {mwt: 30, operator: 70})
  channel_params: Object           # Comisiones, descuentos, costos operativos por canal

  # Períodos
  effective_from: datetime         # Fecha de inicio de vigencia
  effective_to: datetime | null    # null = indefinido hasta terminación
  development_period_months: int   # Período sin metas numéricas (ej: 36)
  review_at_month: int             # Mes de revisión conjunta (ej: 33)
  renewal_period_months: int       # Período de renovación automática (ej: 24)

  # Condiciones de terminación
  exit_notice_days: int            # Días hábiles de preaviso (ej: 120)
  exit_conditions: string[]        # Causales de terminación anticipada

  # Restricciones heredables
  inherited_restrictions: Object   # Restricciones del contrato padre que aplican a hijos
  child_restrictions: Object       # Restricciones que este contrato impone a sus hijos

  # Idioma del contrato
  contract_languages: string[]     # ["ES"] | ["ES", "PT-BR"] | ["ES", "EN"]
                                   # Un solo idioma = monolingüe
                                   # Dos idiomas = bilingüe nativo (ambas versiones auténticas)
  prevailing_language: {           # Solo cuando contract_languages.length > 1
    jurisdiction_issuer: string    # Idioma que prevalece en tribunales del issuer (ej: "ES" en CR)
    jurisdiction_receiver: string  # Idioma que prevalece en tribunales del receptor (ej: "PT-BR" en BR)
  } | null

  # Jurisdicción
  jurisdiction: {
    # Hecho objetivo — Compliance los identifica, no se deciden
    mandatory_registrations: [
      {
        country: string            # "BR" | "CR" | "US"
        authority: string          # "INPI" | "APOSTILLE" | etc.
        type: string               # "trademark_license" | "apostille" | "jv_registration"
        required: boolean          # Obligatorio por ley en esa jurisdicción
        recommended: boolean       # Recomendado aunque no obligatorio
        status: enum               # pending | in_process | registered | not_applicable
        registration_number: string | null
        registered_at: datetime | null
        blocking: boolean          # true = bloquea activación si pending
      }
    ]
    # Decisión del CEO — cláusula pactada entre las partes
    elected_forum: {
      type: enum                   # arbitration | tribunal_issuer | tribunal_receiver | tribunal_neutral
      institution: string | null   # "ICC" | "UNCITRAL" | "Tribunales de CR" | etc.
      seat: string | null          # Ciudad/país sede del arbitraje o tribunal
      governing_law: string        # Ley que rige el contrato (ej: "CR" | "BR" | "NY" | "Panama")
    }
  }

  # Documentos legales
  documents: {
    primary: ref → ART-20          # Documento legal principal (licencia + JV)
    complementary: ref → ART-21[]  # Documentos complementarios (anexos, adendas)
    signed_hash: string            # SHA-256 del PDF firmado — inmutable
    signed_at: datetime | null     # Timestamp de firma
    signed_by: string[]            # Nombres legales de firmantes
    stored_at: string              # Path en MinIO
  }

  # Verificación IA
  ai_verification: {
    verified_at: datetime | null
    result: enum | null            # match | mismatch | pending
    discrepancies: Object[]        # Lista de diferencias detectadas entre PDF y DB
    ceo_reviewed: boolean          # CEO revisó y aprobó discrepancias (si las hay)
    ceo_reviewed_at: datetime | null
  }

  # Estado del contrato
  status: enum                     # drafting | under_review | signed | active | suspended | terminated | superseded
  superseded_by: ref → NodeContract | null  # Si fue reemplazado

  # Automatizaciones ancladas
  automations: ref[] → Automation  # Ejecutores de reglas del contrato

  # Gobernanza
  created_by: string
  approved_by: string | null       # CEO
  approved_at: datetime | null
}
```

---

## C. Ciclo de vida del contrato

```
DRAFTING → UNDER_REVIEW → SIGNED → ACTIVE → [SUSPENDED | TERMINATED | SUPERSEDED]

1. DRAFTING
   Quién: CEO configura parámetros en mwt.one
   Qué: todos los campos del contrato, generación automática de ART-20 y ART-21
   Regla: sistema NO ejecuta reglas. Parámetros son editables.
   Output: borrador de documentos legales generados automáticamente

2. UNDER_REVIEW
   Quién: CEO + receptor (Operador BR, distribuidor)
   Qué: revisión y negociación de términos
   Regla: cambios en negociación se registran como versiones del borrador
   Nota: si hay discrepancias entre lo negociado y los parámetros en DB,
         CEO las marca como aprobadas antes de avanzar

3. SIGNED
   Quién: firmantes de ambas partes
   Qué: documentos firmados digitalmente, hash SHA-256 calculado y registrado
   Regla: desde este momento los documentos son INMUTABLES (ref → POL_INMUTABILIDAD)
   Output: AI middleware verifica coherencia PDF vs DB → resultado en ai_verification
   Bloqueo 1: sistema NO activa contrato si ai_verification.result = mismatch
              y ceo_reviewed = false
   Bloqueo 2: sistema NO activa contrato si jurisdiction.mandatory_registrations
              contiene items con required = true Y status = pending Y blocking = true
              → alerta CEO con lista de registros pendientes bloqueantes

4. ACTIVE
   Qué: contrato en vigor, sistema ejecuta reglas automáticamente
   Ejecutores: automatizaciones ancladas (Windmill + n8n)
   Monitoreo: bus de eventos registra cada ejecución
   Visibilidad: CEO ve estado en tiempo real en mwt.one

5. SUSPENDED
   Cuándo: incumplimiento grave detectado o disputa activa
   Qué: automatizaciones pausadas, CEO notificado
   Regla: solo CEO puede suspender o reactivar

6. TERMINATED
   Cuándo: preaviso cumplido + fecha de terminación alcanzada,
           o causal de terminación anticipada verificada
   Qué: licencia de marca se extingue automáticamente,
        acceso receptor al portal se desactiva,
        registro histórico permanece inmutable
   Regla: NUNCA se elimina. Solo status = terminated.

7. SUPERSEDED
   Cuándo: renegociación con nuevos términos
   Qué: contrato anterior queda superseded_by = nuevo contrato
        Historial del contrato anterior es inmutable
        Solo instancias nuevas usan el contrato nuevo
```

---

## D. Cadena de contratos — herencia de restricciones

```
MWT-CR (nodo raíz)
  └── NC-0001: MWT-CR → FRANQ-BR
        Restricciones que FRANQ-BR hereda a sus hijos:
        - precio mínimo de reventa
        - restricción de canales no autorizados
        - obligación de reporte mensual
        - exclusividad territorial por sub-zona

        └── NC-0002: FRANQ-BR → SUBDIST-SP
              FRANQ-BR configura dentro de sus límites
              Sistema valida que NC-0002 no viole NC-0001

              └── NC-0003: SUBDIST-SP → POS-retail
                    Mismo principio: hereda restricciones,
                    agrega las propias dentro de sus límites
```

Regla crítica: el sistema valida automáticamente que cada contrato hijo no contradiga las restricciones del contrato padre antes de permitir la transición a SIGNED. Si hay contradicción → bloqueo + alerta CEO.

---

## E. Verificación IA del documento firmado

### E1. Proceso

```
1. PDF firmado ingresa a MinIO
2. AI middleware extrae parámetros del texto del PDF
3. Sistema compara contra instancia en DB campo por campo
4. Resultado:
   - match: todos los parámetros coinciden → contrato puede activarse
   - mismatch: hay diferencias → lista de discrepancias generada
5. Si mismatch:
   - CEO recibe alerta con lista detallada de diferencias
   - CEO marca cada diferencia como: aprobada | error_a_corregir
   - Si todas aprobadas → ceo_reviewed = true → contrato puede activarse
   - Si hay error_a_corregir → volver a DRAFTING para corrección
```

### E2. Qué verifica la IA

| Campo verificado | Fuente PDF | Fuente DB | Criticidad |
|-----------------|------------|-----------|-----------|
| Porcentaje de participación | Cláusula JV | participation_split | CRÍTICA |
| Precio de transferencia | Cláusula licencia | transfer_price_policy | CRÍTICA |
| Territorio y exclusividad | Cláusula territorial | territory + exclusivity | CRÍTICA |
| Período de desarrollo | Cláusula plazo | development_period_months | ALTA |
| Condiciones de salida | Cláusula terminación | exit_notice_days + exit_conditions | ALTA |
| Canales incluidos | Cláusula canales | channels | ALTA |
| Fecha de vigencia | Cláusula vigencia | effective_from | MEDIA |

### E3. Regla de activación

```
SIGNED → ACTIVE solo si:
  ai_verification.result = match
  O
  ai_verification.result = mismatch AND ceo_reviewed = true
  
Sistema NUNCA activa un contrato con mismatch no revisado por CEO.
```

---

## F. Automatizaciones ancladas al contrato

Ref → ENT_PLAT_AUTOMATIONS para el modelo completo.

| automation_id | name | engine | trigger | función |
|--------------|------|--------|---------|---------|
| AUT-040 | Verificación IA post-firma | Windmill | event (status→signed) | Extrae y compara PDF vs DB |
| AUT-041 | Cálculo contribución por canal | Windmill | scheduled/weekly | Calcula retorno por canal con datos reales |
| AUT-042 | Forecast reposición | Windmill | scheduled/monthly | Proyecta siguiente pedido basado en velocidad |
| AUT-043 | Alerta canal bajo umbral | n8n | event (contribución < threshold) | Notifica CEO + Operador |
| AUT-044 | Reporte trimestral automático | Windmill | scheduled/quarterly | Genera reporte para MWT sin intervención Operador |
| AUT-045 | Verificación cumplimiento contrato | Windmill | scheduled/monthly | Compara operación real vs condiciones del contrato |
| AUT-046 | Alerta no-conformidad contractual | n8n | event (AUT-045 detecta desviación) | Notifica CEO con referencia al artículo específico |
| AUT-047 | Generación contrato hijo | n8n | event (Operador activa sub-distribuidor) | Genera borrador NC hijo con restricciones heredadas |

---

## G. Visibilidad por rol

| Elemento | CEO (mwt.one) | Operador (portal.mwt.one) |
|----------|--------------|--------------------------|
| Parámetros financieros | Completo [CEO-ONLY] | Solo su vista client |
| Estado del contrato | Completo | Estado actual + fechas |
| Historial de versiones | Completo | Solo versión activa |
| Verificación IA | Completo | No visible |
| Automatizaciones | Todas + gobernanza | Solo las que le afectan |
| Cadena de contratos hijos | Completa | Solo sus hijos directos |
| Alertas de no-conformidad | Todas | Las que le corresponden |
| Documentos firmados | Acceso completo | Acceso a sus documentos |
| Registros de jurisdicción | Completo (mandatory + elected) | Solo elected_forum (foro pactado) |
| Idiomas del contrato | Completo | Solo la versión en su idioma |

---

## Z. Pendientes

| ID | Pendiente | Desbloquea | Quién decide |
|----|-----------|-----------|-------------|
| Z1 | CNPJ y razón social FRANQ-BR | Instanciar NC-0001 | CEO + Operador BR |
| Z2 | Decisión propiedad marca: Muito CR o MWT PA | Issuer correcto en ART-20 | CEO |
| Z3 | Registro INPI Brasil en proceso | Enforcement licencia BR | CEO + agente PI |
| Z4 | Validación estructura Camino A por abogado BR | NC-0001 legalmente ejecutable | CEO + abogado BR |
| Z5 | Validación estructura Camino A por abogado CR | Licencia desde Muito CR ejecutable | CEO + abogado CR |
| Z6 | Parámetros financieros NC-0001 | transfer_price_policy, participation_split | CEO [CEO-ONLY] |
| Z7 | ¿Distribuidores pueden ver historial de automatizaciones ancladas a su contrato? | Visibilidad portal | CEO |
| Z8 | elected_forum NC-0001: tipo, institución, sede y ley aplicable | Cláusula jurisdicción en ART-20 | CEO + abogado |
| Z9 | Registro licencia de marca ante INPI BR post-registro marca | blocking = true para NC-0001 ACTIVE | CEO + agente PI |

---

Stamp: DRAFT — pendiente aprobación CEO
Origen: Sesión de diseño arquitectura contratos inteligentes — 2026-03-09
