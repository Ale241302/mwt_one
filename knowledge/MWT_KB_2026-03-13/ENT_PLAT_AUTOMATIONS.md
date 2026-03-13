# ENT_PLAT_AUTOMATIONS — Capa de Automatización y Orquestación
status: DRAFT
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
version: 1.0

---

## A. Concepto

Automation = workflow ejecutable que se ancla a una entidad del sistema (nodo, expediente, transfer, artefacto) y ejecuta lógica operativa de forma programada, reactiva o manual.

### A1. Principio de diseño

Las automatizaciones se **anclan** a entidades como contexto pero **viven** en la capa de orquestación del sistema. No pertenecen a la entidad.

```
CONFIGURACIÓN VISIBLE EN CONTEXTO  ≠  PERTENENCIA ARQUITECTÓNICA

El CEO ve las automatizaciones desde el nodo FBA-US en su dashboard.
Pero arquitectónicamente viven en la capa de orquestación, no dentro del nodo.
```

Esto permite:
- Mover una automatización de un contexto a otro sin refactorear la entidad
- Compartir automatizaciones entre entidades si tiene sentido
- Escalar la capa de orquestación independientemente
- Gestionar todas las automatizaciones del sistema desde un solo punto

### A2. Engines disponibles

| Engine | Uso principal | Cuándo usar |
|--------|--------------|-------------|
| n8n | Workflows event-driven y scheduled, integraciones, notificaciones | Flujos estándar, conectores, alertas |
| Windmill | Cálculos pesados, scripts Python, procesamiento batch | Forecast, reconciliación, reportes complejos |

Ref → ENT_PLAT_INFRA para capacidad y deployment de cada engine.
Nota: en MVP ninguno de los dos está activo. Ref → ENT_PLAT_MVP.A2.

---

## B. Modelo

```
Automation {
  automation_id: string            # AUT-XXX (auto)
  name: string                     # "Inventory sync FBA-US"
  description: string              # Qué hace en una línea
  
  # Engine
  engine: enum                     # n8n | windmill
  workflow_ref: string             # ID del workflow en n8n/Windmill
  
  # Trigger
  trigger_type: enum               # scheduled | event | manual
  trigger_config: Object           # cron expression, evento específico, etc.
  
  # Contexto (a qué se ancla)
  context_anchor_type: enum        # node | expediente | transfer | artifact
  context_anchor_id: ref           # El nodo/expediente/transfer/artefacto específico
  
  # Propiedad
  legal_entity: ref → LegalEntity  # Quién lo administra (ve en su dashboard)
  
  # Estado
  status: enum                     # active | paused | draft | failed | deprecated
  last_run: datetime | null
  last_result: enum | null         # success | failure | partial
  next_run: datetime | null
  failure_count: int               # Consecutivos. Reset en success.
  
  # Gobernanza
  created_by: string               # Humano o IA
  approved_by: string | null       # CEO (si requires_approval)
  requires_approval: boolean       # true = CEO debe aprobar antes de activar
  
  # Alertas
  alert_on_failure: boolean
  alert_recipients: string[]       # Quién recibe alerta si falla
}
```

---

## C. Automatizaciones conocidas (por contexto)

### C1. Ancladas a nodos

| automation_id | name | engine | trigger | context_anchor | legal_entity | status |
|--------------|------|--------|---------|---------------|-------------|--------|
| AUT-001 | Inventory sync FBA-US | n8n | scheduled/4h | FBA-US | MWT-CR | PLANNED |
| AUT-002 | Alerta stock < 21d | n8n | event | FBA-US | MWT-CR | PLANNED |
| AUT-003 | PPC daily report | n8n | scheduled/daily | FBA-US | MWT-CR | PLANNED |
| AUT-004 | Restock calculation | Windmill | scheduled/weekly | FBA-US | MWT-CR | PLANNED |

### C2. Ancladas a expedientes

| automation_id | name | engine | trigger | context_anchor | legal_entity | status |
|--------------|------|--------|---------|---------------|-------------|--------|
| AUT-010 | Alerta crédito 80d | n8n | scheduled/daily | expediente (any) | MWT-CR | PLANNED |
| AUT-011 | Email indexer PI-XXXX | n8n | event (email) | expediente (any) | MWT-CR | PLANNED |

### C3. Ancladas a transfers

| automation_id | name | engine | trigger | context_anchor | legal_entity | status |
|--------------|------|--------|---------|---------------|-------------|--------|
| AUT-020 | Notificación despacho | n8n | event (status→in-transit) | transfer (any) | MWT-CR | PLANNED |
| AUT-021 | Update inventario nodo destino | n8n | event (status→received) | transfer (any) | MWT-CR | PLANNED |

### C4. Futuras (distribuidores)

| automation_id | name | engine | trigger | context_anchor | legal_entity | status |
|--------------|------|--------|---------|---------------|-------------|--------|
| AUT-030 | Alerta stock bajo Sondel | n8n | scheduled/daily | SONDEL-WH-CR | SONDEL-CR | PLANNED |
| AUT-031 | Reporte mensual automático | n8n | scheduled/monthly | SONDEL-WH-CR | SONDEL-CR | PLANNED |

Nota: distribuidores pueden tener automatizaciones configuradas desde su dashboard en portal.mwt.one, scoped a sus nodos.

---

## D. Gobernanza

### D1. Ciclo de vida

```
DRAFT → APROBACIÓN → ACTIVE → PAUSED/FAILED → DEPRECATED

1. DRAFT
   Quién: IA o humano propone
   Qué: spec de la automatización (qué hace, trigger, contexto)
   Regla: NO se ejecuta

2. APROBACIÓN (si requires_approval = true)
   Quién: CEO
   Qué: revisa spec, valida que tiene sentido operativo
   Regla: automatizaciones con impacto financiero o de datos siempre requieren aprobación

3. ACTIVE
   Qué: se ejecuta según trigger
   Monitoreo: last_run, last_result, failure_count

4. PAUSED
   Manual: CEO o sistema pausa
   Auto: si failure_count > 3 consecutivos → auto-pause + alerta

5. DEPRECATED
   Cuándo: ya no se necesita o fue reemplazada
   Qué: se desactiva, se mantiene registro histórico
```

### D2. Regla de aprobación

```
requires_approval = true CUANDO:
- Automatización modifica datos (no solo lee)
- Automatización envía comunicaciones externas
- Automatización tiene impacto financiero
- Automatización fue creada por IA

requires_approval = false CUANDO:
- Solo genera reportes internos
- Solo envía alertas al CEO
- Es copia de una automatización ya aprobada
```

### D3. IA como creadora de automatizaciones

Una IA puede proponer automatizaciones detectando patrones:
- "El sync de inventario falla frecuentemente los lunes → propongo retry automático"
- "El CEO siempre revisa costos el viernes → propongo reporte semanal"

Flujo: IA genera spec → status: draft → CEO revisa → aprueba o rechaza.
La IA nunca activa automatizaciones directamente.

---

## E. Visualización en dashboard

Cada LegalEntity ve en su dashboard las automatizaciones ancladas a sus entidades:

| Vista | Qué muestra |
|-------|------------|
| Lista por contexto | Agrupadas por nodo / expediente / transfer |
| Estado | Verde (active+success), Amarillo (paused), Rojo (failed) |
| Logs | Últimas N ejecuciones con resultado |
| Acciones | Pausar, reactivar, ver detalle, crear nueva |

MWT ve todas las automatizaciones del sistema.
Distribuidores ven solo las ancladas a sus nodos.

---

## Z. Pendientes

| ID | Pendiente | Desbloquea | Quién decide |
|----|-----------|-----------|-------------|
| Z1 | Definir umbral de auto-pause (¿3 failures?) | D1 auto-pause | Architect + CEO |
| Z2 | ¿Distribuidores pueden crear automatizaciones propias o solo MWT las crea? | C4 scope | CEO |
| Z3 | Capacidad de n8n/Windmill en infra actual | Performance | Architect |

---

Stamp: DRAFT — Pendiente aprobación CEO
Origen: Sesión de diseño conceptual bodegas/nodos/transfers — 2026-02-26
