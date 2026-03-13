# ENT_COMP_ISO_ROADMAP — Hoja de Ruta ISO
id: ENT_COMP_ISO_ROADMAP
version: 1.0
status: DRAFT
visibility: [INTERNAL]
domain: Compliance (IDX_COMPLIANCE)
classification: ENTITY — Data pura inyectable
stamp: DRAFT — Pendiente aprobación CEO
regenerado: 2026-03-11 (archivo ausente confirmado en auditoría — reconstruido desde REPORTE_SESION_ISO_20260301)

---

## A. POSTURA ESTRATÉGICA

**Decisión CEO (2026-03-01):** No certificar ISO ahora.
Operar bajo principios ISO. Certificar cuando un trigger externo lo requiera.

Razón: el costo de certificación no genera retorno en la etapa actual. El sistema está diseñado para que los expedientes y operaciones generen evidencia ISO de forma natural (dual 9001 + 27001) sin overhead adicional.

---

## B. NORMAS EN ALCANCE

| Norma | Alcance | Status | Fase activación |
|-------|---------|--------|----------------|
| ISO 9001:2015 | Sistema de Gestión de Calidad — operaciones MWT + distribución | EN PREPARACIÓN | Trigger comercial / distribuidor |
| ISO 45001:2018 | Seguridad y Salud Ocupacional — relevante por uso laboral del calzado | EN PREPARACIÓN | Trigger cliente industrial |
| ISO/IEC 27001:2022 | Seguridad de la Información — datos biométricos, multi-tenancy | EN PREPARACIÓN | Trigger distribuidor / datos N4 |
| ISO 13485 | Dispositivos médicos | EXCLUIDO | Solo si scanner entra canal médico |

**Regla ISO 13485:** Scanner posicionado como wellness/commercial fitting tool. Si entra canal médico (hospital, clínica, prescripción), se activa este ISO. Ref → POL_CLAIMS_SCANNER.

---

## C. TRIGGERS DE CERTIFICACIÓN

Monitoreados en PLB_REVISION_DIRECCION como agenda permanente trimestral.

| ID | Trigger | Norma activada | Prioridad |
|----|---------|---------------|-----------|
| T1 | Cliente industrial requiere ISO 9001 como condición de compra | 9001 | ALTA |
| T2 | Tender / licitación pública requiere certificación | 9001 + 45001 | ALTA |
| T3 | Regulador de mercado exige certificación | Según país | CRÍTICA |
| T4 | Distribuidor clave (>30% volumen) lo requiere | 9001 | ALTA |
| T5 | Onboarding distribuidores con datos biométricos | 27001 | ALTA |
| T6 | Inversión / due diligence requiere auditoría | 27001 | MEDIA |
| T7 | Canal médico (clínicas, hospitales, prescripción) | 13485 | CUANDO APLIQUE |

---

## D. FASES DE IMPLEMENTACIÓN

### Fase 0 — FUNDACIONAL (COMPLETADA 2026-03-01)

Documentos creados:
- POL_CALIDAD.md — política de calidad (ISO 9001 §5.2)
- POL_SSO.md — política SSO (ISO 45001 §5.2)
- POL_DATA_CLASSIFICATION.md — clasificación datos N0–N4 (ISO 27001 A.5.12)
- POL_CLAIMS_SCANNER.md — shield wellness vs médico
- ENT_GOB_RIESGOS.md — registro de riesgos (ISO 9001/45001/27001 §6.1)
- ENT_GOB_KPI.md — KPIs de sistema (ISO 9001/45001 §9.1)
- ENT_GOB_SSO.md — objetivos SSO (ISO 45001 §4-10)
- ENT_GOB_PROVEEDORES.md — evaluación proveedores (ISO 9001 §8.4)
- PLB_REVISION_DIRECCION.md — revisión dirección (ISO §9.3)
- PLB_ACCION_CORRECTIVA.md — acciones correctivas (ISO §10)
- PLB_AUDIT_ISO.md — auditoría interna (ISO §9.2)
- PLB_SUPPLIER_EVAL.md — evaluación proveedores
- SCH_ISO_AUDIT_PACK.md — paquete de auditoría
- IDX_COMPLIANCE.md v2.0 — índice compliance expandido
- IDX_GOBERNANZA.md v2.0 — índice gobernanza expandido

Archivos existentes patcheados:
- POL_VISIBILIDAD.md — regla precedencia Visibility × Classification
- POL_STAMP.md — estados FROZEN-VIGENTE y FROZEN-DEPRECATED
- PLB_COMPLIANCE.md — gate publicación + artifact spec auditable
- POL_DATA_CLASSIFICATION.md — Consent Receipt + regla precedencia
- POL_ARCHIVO.md — Record Contract (9 campos metadata MinIO)
- ENT_PLAT_INFRA.md — §E Backup/Restore Evidence + §F Encryption Controls
- ENT_PLAT_SEGURIDAD.md — §A Enforcement técnico (10 controles)
- RW_ROOT.md — conteo policies 17→21 (registrado como cambio histórico — RW_ROOT actual ya refleja 21 policies)

---

### Fase 1 — EVIDENCIA TÉCNICA (EN PROGRESO)

| Item | Qué falta | Responsable | Referencia |
|------|----------|-------------|-----------|
| F1-01 | Verificar cifrado disco Hostinger (LUKS) | CEO / Hostinger | ENT_PLAT_INFRA §F |
| F1-02 | Confirmar SLA Hostinger (uptime, backup) | CEO / Hostinger | ENT_PLAT_INFRA §E |
| F1-03 | PLB_RISK_ASSESSMENT — protocolo evaluación riesgos | CEO / sesión dedicada | ISO 27001 §8.2 |
| F1-04 | Primera revisión dirección (agenda: Q2 2026) | CEO | PLB_REVISION_DIRECCION |

---

### Fase 2 — DATOS BIOMÉTRICOS Y MULTI-TENANCY (BLOQUEADA — pre-distribuidor)

Estos items se activan ANTES del onboarding de primer distribuidor con scanner.

| Item | Qué crear | ISO | Hallazgo origen |
|------|----------|-----|----------------|
| F2-01 | POL_CONSENTIMIENTO.md | 27001 A.5.34 | H1 auditoría |
| F2-02 | POL_RETENCION_ESCANEOS.md | 27001 A.5.33 | H1 auditoría |
| F2-03 | ENT_COMP_PRIVACIDAD.md | 27001 | H1 auditoría |
| F2-04 | Mecanismo anonimización datos biomecánicos | 27001 A.5.34 | H1 auditoría |
| F2-05 | Django middleware access_events (reads N2+) | 27001 A.8.15 | H3 auditoría |
| F2-06 | ENT_PLAT_MULTITENANT.md — aislamiento lógico vs físico | 27001 | H8 auditoría |
| F2-07 | PLB_INCIDENT_RESPONSE.md | 27001 A.5.24 | IDX_COMPLIANCE |
| F2-08 | PLB_ONBOARDING_DIST_DATA.md | 27001 A.5.20 | IDX_COMPLIANCE |

---

### Fase 3 — CERTIFICACIÓN FORMAL (SOLO SI TRIGGER)

Acciones cuando se activa un trigger de Sección C:

1. Seleccionar organismo certificador (Bureau Veritas, SGS, TÜV)
2. Contratar consultor ISO externo para pre-auditoría
3. Completar todos los items Fase 1 y Fase 2 relevantes
4. Auditoría interna completa (PLB_AUDIT_ISO)
5. Auditoría de certificación (etapas 1 y 2)
6. Emisión certificado → registrar en ENT_GOB_KPI

Tiempo estimado Fase 3: 4–6 meses desde trigger.

---

## E. ESTADO EVIDENCIA POR NORMA

### ISO 9001:2015

| Cláusula | Descripción | Evidencia disponible | Gap |
|----------|-------------|---------------------|-----|
| 4.1 | Contexto organización | ENT_PLAT_LEGAL_ENTITY | — |
| 4.4 | SGC y procesos | ENT_OPS_EXPEDIENTE, state machine | — |
| 5.2 | Política calidad | POL_CALIDAD | — |
| 6.1 | Riesgos y oportunidades | ENT_GOB_RIESGOS | — |
| 7.4 | Comunicación | PLB_COMUNICACION | — |
| 8.4 | Control proveedores externos | ENT_GOB_PROVEEDORES, PLB_SUPPLIER_EVAL | — |
| 9.1 | Seguimiento y medición | ENT_GOB_KPI | — |
| 9.2 | Auditoría interna | PLB_AUDIT_ISO | — |
| 9.3 | Revisión por la dirección | PLB_REVISION_DIRECCION | — |
| 10 | Mejora / acciones correctivas | PLB_ACCION_CORRECTIVA | — |

### ISO 45001:2018

| Cláusula | Evidencia disponible | Gap |
|----------|---------------------|-----|
| 5.2 Política SSO | POL_SSO | — |
| 6.1 Riesgos SSO | ENT_GOB_RIESGOS | — |
| §4-10 Sistema SSO | ENT_GOB_SSO | — |
| 8.x Planificación operacional | — | Gap — no documentado aún |
| 9.1 Desempeño | ENT_GOB_KPI | — |
| 9.3 Revisión | PLB_REVISION_DIRECCION | — |

### ISO/IEC 27001:2022

| Control / Cláusula | Evidencia disponible | Gap |
|-------------------|---------------------|-----|
| §6.1 Riesgos info | ENT_GOB_RIESGOS | PLB_RISK_ASSESSMENT falta |
| §8.2 Risk assessment | — | F1-03 pendiente |
| §9.1 Monitoreo | ENT_GOB_KPI | — |
| A.5.12 Clasificación | POL_DATA_CLASSIFICATION | — |
| A.5.33 Retención | — | F2-02 pendiente |
| A.5.34 Privacidad | — | F2-01, F2-04 pendientes |
| A.8.15 Logging | ENT_PLAT_SEGURIDAD | Middleware F2-05 pendiente |
| Encryption | ENT_PLAT_INFRA §F | Verificación Hostinger pendiente |
| Backup/Restore | ENT_PLAT_INFRA §E | Prueba trimestral programar |
| Gate publicación | PLB_COMPLIANCE | — |

---

## F. DECISIONES PERMANENTES (NO REABRIR)

- No certificar ISO ahora — trigger requerido
- No crear tipo REC_ para records — son outputs de playbooks en MinIO
- No crear POL_BACKUP_RESTORE como policy separada — vive en ENT_PLAT_INFRA §E
- No crear POL_CHANGE_CONTROL — cubierto por POL_ITERACION + POL_STAMP + FROZEN
- ISO 13485 excluido hasta trigger canal médico

---

Stamp: DRAFT — Pendiente aprobación CEO
Aprobador: CEO
Origen: Regenerado 2026-03-11 desde REPORTE_SESION_ISO_20260301 (archivo ausente en KB)
