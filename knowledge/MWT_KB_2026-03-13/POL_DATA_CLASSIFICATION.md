# POL_DATA_CLASSIFICATION — Clasificación de Datos
id: POL_DATA_CLASSIFICATION
version: 1.1
domain: Compliance (IDX_COMPLIANCE)
status: DRAFT
visibility: [INTERNAL]
stamp: DRAFT — pendiente aprobación CEO
refs: POL_VISIBILIDAD, ENT_PLAT_SEGURIDAD, ENT_COMP_PRIVACIDAD
iso: 27001:2022 A.5.12, A.5.13

---

## A. Propósito

Define cómo se clasifican todos los datos que MWT genera, procesa o almacena. Extiende POL_VISIBILIDAD (que clasifica documentos internos) al dominio de datos de terceros, datos biométricos y datos de distribuidores.

POL_VISIBILIDAD sigue vigente para documentos del knowledge base. Esta policy agrega clasificación para datos operativos y de terceros.

---

## B. Niveles de clasificación

| Nivel | Etiqueta | Quién accede | Ejemplo | Almacenamiento | Cifrado |
|-------|---------|-------------|---------|---------------|---------|
| N0 | [PUBLIC] | Cualquiera | Catálogo productos, specs técnicas, claims aprobados | Cualquiera | No requerido |
| N1 | [INTERNAL] | Equipo MWT | Estrategia, riesgos, métricas internas, playbooks | PostgreSQL / MinIO / Git | En reposo recomendado |
| N2 | [CONFIDENTIAL] | CEO + roles autorizados | Pricing fábrica, márgenes, costos, modelos financieros | PostgreSQL con RLS | En reposo obligatorio |
| N3 | [DISTRIBUTOR-SCOPED] | Distribuidor owner + CEO | Catálogo del distribuidor, métricas de uso, escaneos de sus clientes | PostgreSQL con RLS + tenant_id | En tránsito y reposo obligatorio |
| N4 | [BIOMETRIC] | Sistema (procesamiento) + CEO (auditoría) | Escaneos de presión plantar, perfiles biomecánicos, métricas corporales | PostgreSQL cifrado + MinIO cifrado | En tránsito y reposo obligatorio. Anonimizable. |

---

## C. Reglas por nivel

### C1. N0 [PUBLIC]
- Puede aparecer en cualquier output externo.
- No requiere consentimiento para uso.
- Coincide con [ALL] de POL_VISIBILIDAD.

### C2. N1 [INTERNAL]
- No sale en outputs externos.
- Coincide con [INTERNAL] + [TECH] + [CREATIVE] de POL_VISIBILIDAD.

### C3. N2 [CONFIDENTIAL]
- Coincide con [CEO-ONLY] de POL_VISIBILIDAD.
- Acceso auditado: cada consulta genera log entry.
- Nunca aparece en: proformas cliente, espejo documental, portal B2B, outputs del scanner.

### C4. N3 [DISTRIBUTOR-SCOPED]
- Dato pertenece al distribuidor. MWT es procesador, no propietario.
- Row-level security con tenant_id. Distribuidor A no ve datos de Distribuidor B.
- CEO ve todo con flag de auditoría.
- Eliminación obligatoria si distribuidor termina contrato (ref → POL_RETENCION_ESCANEOS).
- Requiere DPA (Data Processing Agreement) firmado antes de capturar datos.

### C5. N4 [BIOMETRIC]
- Dato personal sensible bajo LGPD (Brasil Art. 5 y 11), BIPA (Illinois), CCPA (California).
- Requiere consentimiento explícito del usuario escaneado antes de captura (ref → POL_CONSENTIMIENTO).
- Procesamiento determinístico y versionado (ref → POL_DETERMINISMO): mismos inputs = mismos outputs.
- Anonimización programada: después del período de retención, el perfil se desvincula de la persona.
- Hash de integridad obligatorio: SHA-256 del frame al momento de captura. Inmutable post-captura.
- Derecho de eliminación: el usuario escaneado puede solicitar borrado de su escaneo.

---

## D. Mapeo a sistemas

| Sistema | Datos que maneja | Niveles aplicables |
|---------|-----------------|-------------------|
| PostgreSQL (MWT.ONE) | Expedientes, costos, márgenes, estados | N1, N2 |
| PostgreSQL (Scanner SaaS) | Escaneos, perfiles, catálogos distribuidor | N3, N4 |
| MinIO | Documentos, facturas, escaneos archivados | N1, N2, N3, N4 |
| Git (knowledge base) | Entities, policies, playbooks, schemas | N0, N1 |
| Email (servidor correo) | Comunicaciones operativas | N1, N2 (temporal — ref POL_ARCHIVO) |

---

## E. Acciones prohibidas por nivel

| Acción | N0 | N1 | N2 | N3 | N4 |
|--------|----|----|----|----|-----|
| Publicar sin revisión | ✅ | ❌ | ❌ | ❌ | ❌ |
| Compartir entre distribuidores | ✅ | ✅ | ❌ | ❌ | ❌ |
| Exportar sin cifrado | ✅ | ✅ | ❌ | ❌ | ❌ |
| Almacenar en dispositivo local | ✅ | ✅ | ❌ | ❌ | ❌ |
| Usar para training de IA | ✅ | ✅ | ❌ | ❌ | ❌ |
| Retener indefinidamente | ✅ | ✅ | ✅ | Según DPA | Según POL_RETENCION_ESCANEOS |

---

## F. Etiquetado

Todo registro de datos nivel N2+ debe tener en su metadata:
- `classification`: nivel (N0-N4)
- `owner`: quién es dueño del dato (MWT, distribuidor, usuario final)
- `retention_policy`: ref a la policy de retención aplicable
- `created_at`: timestamp de creación
- `created_by`: actor que creó el registro

Para N4 (biométrico) adicionalmente:
- `consent_id`: referencia al registro de consentimiento (ref → §G)
- `integrity_hash`: SHA-256 del dato original
- `motor_version`: versión del motor biomecánico que lo procesó
- `anonymization_date`: fecha programada de anonimización

---

## G. Consent Receipt — Modelo para datos N4

Cuando se captura un dato N4 [BIOMETRIC], el sistema debe generar un consent receipt vinculado al escaneo.

### G1. Campos mínimos

| Campo | Tipo | Descripción |
|-------|------|-------------|
| consent_id | UUID | Identificador único del consentimiento |
| scan_id | ref | Escaneo al que se vincula |
| timestamp | datetime | Momento en que se otorgó consentimiento |
| distributor_id | ref (tenant) | Distribuidor en cuyo punto de venta se capturó |
| purpose | enum | fitting_recommendation (único propósito válido en v1) |
| scope | text | "Medición de presión plantar para recomendación de calzado y plantilla" |
| policy_version | string | Versión de la política de privacidad aceptada |
| method | enum | digital_checkbox (en UI del scanner, pre-scan) |
| revocable | boolean | true — usuario puede solicitar eliminación |
| revoked_at | datetime | null hasta que se revoque. Si se revoca → anonimizar scan. |

### G2. Reglas
- Sin consent_id válido, el sistema no permite iniciar escaneo.
- Consent receipt es inmutable (ref → POL_INMUTABILIDAD). Revocación = nuevo registro, no edición.
- Consent receipt se almacena separado del escaneo. Si se anonimiza el scan, el consent receipt persiste como evidencia de que hubo consentimiento válido en su momento.
- Implementación: Fase 2 del roadmap ISO, junto con POL_CONSENTIMIENTO.

---

## H. Regla de precedencia Visibilidad × Classification

POL_VISIBILIDAD controla quién ve documentos del knowledge base (editorial, operativo).
POL_DATA_CLASSIFICATION controla cómo se protegen datos operativos en sistemas (técnico).

Reglas:
1. Classification manda sobre Visibility para controles técnicos (cifrado, acceso DB, logging).
2. Visibility manda sobre Classification para outputs y documentos editoriales.
3. Todo documento que contenga datos N2+ debe tener visibility mínima [INTERNAL].
4. Todo documento que contenga datos N3+ debe tener visibility [CEO-ONLY] o [DISTRIBUTOR-SCOPED].
5. Un documento [ALL] nunca puede contener datos N2, N3 o N4 inline. Si necesita referenciarlos, usa ref → sin incluir el dato.

---

Stamp: DRAFT — Pendiente aprobación CEO
