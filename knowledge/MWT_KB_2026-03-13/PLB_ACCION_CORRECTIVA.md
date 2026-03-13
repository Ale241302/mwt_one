# PLB_ACCION_CORRECTIVA — Acciones Correctivas y No Conformidades
id: PLB_ACCION_CORRECTIVA
version: 1.0
domain: Gobernanza (IDX_GOBERNANZA)
status: DRAFT
visibility: [INTERNAL]
stamp: DRAFT — pendiente aprobación CEO
iso: 9001:2015 §10.1, 45001:2018 §10.2, 27001:2022 §10.2

---

## A. Propósito

Protocolo para gestionar no conformidades (algo que salió mal o no cumple un requisito) y acciones correctivas (qué se hace para que no vuelva a pasar). Compartido entre las tres ISOs.

---

## B. Tipos de hallazgo

| Tipo | Definición | Ejemplo |
|------|-----------|---------|
| No conformidad mayor | Fallo sistémico que afecta la capacidad del proceso | Proformas enviadas sin aprobación CEO durante 2 semanas |
| No conformidad menor | Fallo puntual, no sistémico | Un expediente sin hash de documento en MinIO |
| Observación | Oportunidad de mejora, no es fallo | El KPI de tiempo por fase no se actualiza mensualmente |
| Incidente SSO | Evento de seguridad/salud ocupacional | Lesión menor en recepción de mercancía |
| Incidente seguridad info | Evento de seguridad de datos | Intento de acceso cross-tenant detectado |

---

## C. Flujo

```
DETECTAR → REGISTRAR → ANALIZAR CAUSA → DEFINIR ACCIÓN → IMPLEMENTAR → VERIFICAR → CERRAR
```

### C1. Detectar
Fuentes: auditoría interna (PLB_AUDIT_ISO), revisión por dirección (PLB_REVISION_DIRECCION), operación diaria, feedback cliente/distribuidor, alerta automática del sistema (ENT_GOB_ALERTAS).

### C2. Registrar
Formato estandarizado en tabla §D. Cada hallazgo recibe ID único: NC-[AÑO]-[CONSECUTIVO].

### C3. Analizar causa raíz
Método: "5 porqués" simplificado. Mínimo 2 niveles de por qué.
Regla: la causa raíz nunca es "error humano". Siempre hay un proceso que permitió el error.

### C4. Definir acción correctiva
La acción debe atacar la causa raíz, no el síntoma.
Cada acción tiene: responsable, fecha límite, y criterio de verificación.

### C5. Implementar
El responsable ejecuta la acción y registra evidencia.

### C6. Verificar eficacia
Después de la fecha límite, verificar que la acción funcionó.
Si el problema se repitió → la acción no fue eficaz → re-abrir con nuevo análisis.

### C7. Cerrar
Solo cuando la verificación confirma eficacia. Cerrar con fecha y firma.

---

## D. Registro de no conformidades

```
═══════════════════════════════════════════
NC-[YYYY]-[NNN]
Fecha detección: YYYY-MM-DD
Detectado por: [persona/sistema/auditoría]
Tipo: [Mayor/Menor/Observación/Incidente SSO/Incidente SI]
ISO: [9001/45001/27001 — puede ser múltiple]
═══════════════════════════════════════════

Descripción del hallazgo:
[qué pasó, dónde, cuándo]

Evidencia:
[documento, log, screenshot, ref a sistema]

Análisis causa raíz (5 porqués):
- ¿Por qué pasó? → [respuesta 1]
- ¿Por qué [respuesta 1]? → [respuesta 2 = causa raíz]

Acción correctiva:
- Acción: [qué se va a hacer]
- Responsable: [quién]
- Fecha límite: [cuándo]
- Criterio de verificación: [cómo saber que funcionó]

Verificación de eficacia:
- Fecha: [YYYY-MM-DD]
- Resultado: [EFICAZ / NO EFICAZ]
- Evidencia: [ref]

Estado: [ABIERTA / EN PROCESO / VERIFICANDO / CERRADA]
───────────────────────────────────────────
```

---

## E. Reglas

- NC mayor tiene fecha límite máxima de 30 días. Si no se resuelve → escalar a revisión por dirección.
- NC menor tiene fecha límite máxima de 90 días.
- NC vencida (pasó fecha límite sin cerrar) se reporta automáticamente en PLB_REVISION_DIRECCION.
- Todas las NC se almacenan como registros inmutables. No se borran aunque se cierren.
- Un auditor ISO espera ver: registro de NC, evidencia de análisis de causa, acciones tomadas, y verificación de eficacia. Sin esto = no conformidad mayor en la auditoría misma.

---

## F. Métricas derivadas (alimentan ENT_GOB_KPI)

| Métrica | Fórmula |
|---------|---------|
| NC abiertas | Count(estado != CERRADA) |
| NC vencidas | Count(fecha_límite < hoy AND estado != CERRADA) |
| Tiempo promedio de resolución | Σ(fecha_cierre - fecha_detección) / n |
| % acciones eficaces al primer intento | Count(verificación = EFICAZ primera vez) / total |

---

Stamp: DRAFT — Pendiente aprobación CEO
