# PLB_REVISION_DIRECCION — Revisión por la Dirección
id: PLB_REVISION_DIRECCION
version: 1.0
domain: Gobernanza (IDX_GOBERNANZA)
status: DRAFT
visibility: [INTERNAL]
stamp: DRAFT — pendiente aprobación CEO
iso: 9001:2015 §9.3, 45001:2018 §9.3, 27001:2022 §9.3

---

## A. Propósito

Protocolo de revisión periódica donde el CEO evalúa el desempeño de los sistemas de gestión (calidad, SSO, seguridad de información) y toma decisiones de mejora. Es el protocolo compartido que las tres ISOs exigen.

---

## B. Frecuencia

Trimestral. Meses: marzo, junio, septiembre, diciembre.
Extraordinaria: cuando ocurra incidente crítico (score ≥ 13 en ENT_GOB_RIESGOS) o cambio significativo de alcance.

---

## C. Agenda estándar

| # | Tema | Fuente | Quién reporta |
|---|------|--------|--------------|
| 1 | Estado de acciones de revisiones anteriores | Acta revisión anterior | CEO |
| 2 | Cambios en contexto externo/interno | Mercados, regulaciones, equipo | CEO |
| 3 | KPIs de desempeño | ENT_GOB_KPI — dashboard con semáforos | Sistema / CEO |
| 4 | Resultados de auditorías internas | PLB_AUDIT_ISO — últimos hallazgos | Auditor (agente o externo) |
| 5 | No conformidades y acciones correctivas | PLB_ACCION_CORRECTIVA — registro activo | CEO |
| 6 | Registro de riesgos — cambios | ENT_GOB_RIESGOS — nuevos, cerrados, re-evaluados | CEO |
| 7 | Incidentes SSO (si aplica) | ENT_GOB_SSO §F | CEO |
| 8 | Incidentes de seguridad info (si aplica) | PLB_INCIDENT_RESPONSE log | CEO |
| 9 | Retroalimentación de clientes/distribuidores | Feedback directo, reclamos, NPS si existe | CEO |
| 10 | Oportunidades de mejora | Propuestas del equipo o del sistema | CEO |
| 11 | Decisiones y asignación de recursos | — | CEO |

---

## D. Formato del acta

```
═══════════════════════════════════════════
REVISIÓN POR LA DIRECCIÓN — Q[N] [AÑO]
Fecha: YYYY-MM-DD
Participantes: [nombres/roles]
═══════════════════════════════════════════

1. ACCIONES ANTERIORES
   - [acción]: [CERRADA/ABIERTA/VENCIDA]

2. CAMBIOS DE CONTEXTO
   - [descripción si aplica]

3. KPIs — RESUMEN
   | KPI | Valor | Tendencia | Semáforo |
   |-----|-------|-----------|---------|
   | ... | ... | ↑/→/↓ | 🟢/🟡/🔴 |

4. AUDITORÍAS
   - Última auditoría: [fecha]
   - Hallazgos abiertos: [N]
   - Hallazgos cerrados desde última revisión: [N]

5. NO CONFORMIDADES
   - Abiertas: [N]
   - Cerradas: [N]
   - Vencidas: [N] → acción requerida

6. RIESGOS
   - Nuevos: [N]
   - Re-evaluados: [N]
   - Score máximo activo: [score] — [ID riesgo]

7. INCIDENTES
   - SSO: [N] (detalle si > 0)
   - Seguridad info: [N] (detalle si > 0)

8. FEEDBACK CLIENTES
   - [resumen si hay]

9. DECISIONES
   - [decisión]: [responsable] [fecha límite]

───────────────────────────────────────────
Próxima revisión: [fecha]
Firma CEO: _______________
═══════════════════════════════════════════
```

---

## E. Reglas

- El acta se almacena como documento inmutable en MinIO (ref → POL_INMUTABILIDAD).
- Si no hay cambios en un tema, se anota "sin cambios" — no se omite el tema.
- Las decisiones del acta se convierten en acciones con responsable y fecha en ENT_GOB_PENDIENTES o PLB_ACCION_CORRECTIVA según corresponda.
- Un auditor ISO espera ver actas trimestrales con evidencia de seguimiento. Sin actas = no conformidad mayor.

---

Stamp: DRAFT — Pendiente aprobación CEO
