# PLB_AUDIT_ISO — Auditoría Interna ISO
id: PLB_AUDIT_ISO
version: 1.0
domain: Gobernanza (IDX_GOBERNANZA)
status: DRAFT
visibility: [INTERNAL]
stamp: DRAFT — pendiente aprobación CEO
iso: 9001:2015 §9.2, 45001:2018 §9.2, 27001:2022 §9.2
extends: PLB_AUDIT

---

## A. Propósito

Extiende PLB_AUDIT (auditoría de calidad documental) al dominio de auditoría de procesos y controles ISO. PLB_AUDIT evalúa si un documento es correcto. PLB_AUDIT_ISO evalúa si un proceso funciona como dice el documento.

---

## B. Programa anual de auditoría

| Trimestre | Foco principal | Procesos a auditar | ISO |
|-----------|---------------|-------------------|-----|
| Q1 (Mar) | Operaciones | Expedientes: flujo completo, estados, tiempos, crédito | 9001 |
| Q2 (Jun) | Seguridad info + SSO | Acceso a datos, cifrado, roles, riesgos laborales | 27001, 45001 |
| Q3 (Sep) | Comercial | Pricing, proformas, comunicación con clientes, claims | 9001 |
| Q4 (Dic) | Transversal | Control documental, riesgos, KPIs, acciones correctivas | 9001, 45001, 27001 |

Scanner SaaS (cuando esté activo): auditar en Q2 y Q4 — segregación de datos, consentimiento, integridad de escaneos.

---

## C. Tipos de auditoría

### C1. Auditoría documental (heredada de PLB_AUDIT)
Evalúa: ¿el documento (entity, policy, playbook) es correcto, completo, consistente, ejecutable, claro?
Criterios: los 5 de PLB_AUDIT §D.
Output: score numérico + fixes.

### C2. Auditoría de proceso
Evalúa: ¿el proceso real coincide con lo que dice el documento?
Método: tomar 3-5 expedientes/registros reales y verificar que siguieron el flujo documentado.

Checklist por expediente:
- ¿Pasó por todos los estados según ENT_OPS_EXPEDIENTE?
- ¿El event log tiene todas las transiciones?
- ¿La proforma tiene consecutivo correcto y aprobación CEO?
- ¿Los costos tienen doble vista y el margen fue calculado?
- ¿El reloj de crédito se activó con AWB/BL?
- ¿Los documentos están en MinIO con hash?

### C3. Auditoría de acceso (ISO 27001)
Evalúa: ¿quién accedió a qué datos y tenía autorización?
Método: revisar logs de acceso del último trimestre.

Checklist:
- ¿Hubo acceso fuera de horario?
- ¿Hubo intentos de acceso cross-tenant?
- ¿Los roles en el sistema coinciden con ENT_PLAT_SEGURIDAD?
- ¿Los secrets y API keys están rotados?
- ¿El backup se ejecutó según frecuencia definida?
- ¿Se probó un restore en el trimestre?

### C4. Auditoría de scanner (cuando esté activo)
Evalúa: integridad de datos biométricos y segregación de distribuidores.

Checklist:
- Tomar 5 escaneos al azar → verificar hash de integridad.
- Verificar que distribuidor A no puede ver escaneos de distribuidor B.
- Verificar que existe consent_id para cada escaneo.
- Verificar que motor biomecánico es versión vigente.
- Verificar que escaneos fuera de retención fueron anonimizados.

---

## D. Formato de reporte de auditoría

```
═══════════════════════════════════════════
AUDITORÍA INTERNA — [Q/AÑO]
Fecha: YYYY-MM-DD
Auditor: [nombre/agente]
Alcance: [procesos auditados]
ISO: [9001/45001/27001]
═══════════════════════════════════════════

RESUMEN EJECUTIVO
- Procesos auditados: [N]
- Registros muestreados: [N]
- Hallazgos: [N] (Mayor: [n], Menor: [n], Observación: [n])

HALLAZGOS
[Cada hallazgo → genera entrada en PLB_ACCION_CORRECTIVA]

| # | Tipo | Proceso | Hallazgo | Evidencia | NC-ID |
|---|------|---------|----------|-----------|-------|
| 1 | ... | ... | ... | ... | NC-YYYY-NNN |

CONFORMIDADES DESTACADAS
[Lo que funciona bien — 2-3 líneas, sin cheerleading]

CONCLUSIÓN
Veredicto: [CONFORME / CONFORME CON OBSERVACIONES / NO CONFORME]

───────────────────────────────────────────
Próxima auditoría: [Q/AÑO]
Firma auditor: _______________
Firma CEO: _______________
═══════════════════════════════════════════
```

---

## E. Reglas

- Auditor no audita su propio trabajo (misma regla de PLB_AUDIT §B).
- Mínimo 1 auditoría por trimestre. El programa puede ajustarse pero no eliminarse.
- Hallazgos de auditoría alimentan PLB_ACCION_CORRECTIVA automáticamente.
- Reportes de auditoría son evidencia clave para el auditor externo ISO.
- Almacenamiento: MinIO, inmutable (ref → POL_INMUTABILIDAD).

---

Stamp: DRAFT — Pendiente aprobación CEO
