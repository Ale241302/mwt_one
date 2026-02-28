# PLB_SPRINT2_EJECUCION — Paquete de Ejecución Sprint 2
status: DRAFT — Pendiente aprobación CEO
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
version: 2.0
tipo: Playbook (instrucción operativa)
refs: LOTE_SM_SPRINT2 v3.5 (FROZEN), PLB_ORCHESTRATOR v1.2.2 (FROZEN), ENT_OPS_STATE_MACHINE v1.2.2 (FROZEN)
complemento: PLB_SPRINT2_PROMPTS (prompts tácticos para Antigravity)
prerrequisito: Sprint 1 DONE (todos los items aprobados)
changelog: |
  v1.0 — Versión inicial Sprint 2
  v1.1 — Propagación fixes ronda 1 (FIX-1 a FIX-4)
  v1.2 — Fixes ronda 2 (FIX-10 a FIX-12 + menores)
  v2.0 — Propagación fixes rondas 3-4: FIX-13 (enforcement vs emisión), FIX-14 (beat canónico), FIX-15 (constante+is_terminal), manejo fallo C17, anti-carreras (select_for_update skip_locked). Alineado a LOTE v3.5 FROZEN.

---

# 1. RESUMEN EJECUTIVO

Sprint 2 activa dos capacidades que el sistema necesita para operación real: (1) el reloj de crédito automático, que protege al CEO bloqueando expedientes que se acercan al límite de 90 días sin intervención manual, y (2) la corrección de artefactos (C19 SupersedeArtifact, C20 VoidArtifact), porque la operación real genera errores y el sistema necesita un mecanismo para corregirlos sin romper la state machine.

Sprint 2 también introduce infraestructura nueva: Redis como broker y Celery worker como ejecutor de tasks asíncronos. Esto es necesario porque el reloj de crédito es un proceso que corre diariamente sin intervención humana — no puede ser un endpoint que alguien llama manualmente.

El sprint tiene 7 items distribuidos en 4 agentes: AG-07 DevOps (infra), AG-02 API Builder (lógica), AG-01 Architect (migraciones), AG-06 QA (tests). Ale sigue como orquestador bajo supervisión CEO.

**Diferencia clave vs Sprint 1:** Sprint 1 fue puro request-response (alguien llama un endpoint, algo pasa). Sprint 2 introduce procesos que corren solos (Celery Beat dispara tasks periódicamente). Esto es conceptualmente nuevo para el stack y para Ale.

---

# 2. DECISIONES CONGELADAS SPRINT 2

Todas las decisiones de Sprint 0 y Sprint 1 siguen vigentes, más las siguientes:

## 2.1 Infraestructura nueva

### Redis como broker Celery
- Redis 7 se agrega al docker-compose como servicio nuevo
- Función: broker de mensajes para Celery (no cache, no event bus — solo broker)
- `CELERY_BROKER_URL = redis://redis:6379/0`
- `CELERY_RESULT_BACKEND = redis://redis:6379/1` (DB separada para resultados)
- No usar Redis Streams, no usar Redis como cache general. Solo broker Celery.

### Celery Worker
- 1 worker con concurrency=2 (MVP, 1 usuario, pocas tasks)
- Pre-fork pool (default). No eventlet, no gevent.
- Se registra contra la app Celery de `config/celery.py`

### Celery Beat
- Sprint 2 Item 1 garantiza celery-beat funcional. Sin condicionales — el estado previo del repo es irrelevante.
- **(FIX-14)** Beat schedule definido ÚNICAMENTE en `app.conf.beat_schedule` dentro de `config/celery.py`. NO usar django-celery-beat (DB), NO duplicar en settings.py. Un solo lugar, una sola verdad.
- 2 periodic tasks Sprint 2:
  - `evaluate_credit_clocks`: crontab(hour=6, minute=0) — diario 6AM UTC
  - `process_pending_events`: cada 300 segundos

## 2.2 Reloj de crédito automático

### Reglas de evaluación (ref §D2, §M2)
Sprint 1 solo persistió `credit_clock_started_at`. Sprint 2 lo evalúa:

| Días transcurridos | Acción | Evento |
|-------------------|--------|--------|
| < 60 | Nada | — |
| 60-74 | Alerta amarilla | credit_clock.warning |
| 75-89 | Bloqueo automático si is_blocked=false | credit_clock.critical + bloqueo SYSTEM |
| ≥ 90 | Evento expirado + bloqueo si no estaba | credit_clock.expired + bloqueo si falta |

### Actor SYSTEM para bloqueo automático (FIX-3)
El reloj ejecuta C17 sin usuario HTTP. Contrato:
- `execute_command(expediente, "C17", data, user=None, actor_type="SYSTEM", actor_id="credit_clock_75d")`
- Bypass de IsCEO permission — el sistema es actor válido para bloqueo automático
- EventLog registra: emitted_by="SYSTEM:evaluate_credit_clocks". actor_type y actor_id van dentro de payload JSON — NO se agregan columnas nuevas a EventLog.
- services.py debe aceptar user=None cuando actor_type="SYSTEM"

### Reglas del reloj (FIX-13 — separación eventos vs enforcement)

El task evalúa cada expediente en DOS pasos independientes:

**Paso 1 — Enforcement de bloqueo (se ejecuta SIEMPRE):**
- Si days_elapsed >= 75 AND is_blocked=false → ejecutar C17 con actor SYSTEM (actor_id="credit_clock_75d")
- Si days_elapsed >= 90 AND is_blocked=false → ejecutar C17 con actor SYSTEM (actor_id="credit_clock_90d")
- Esto se evalúa en cada corrida del task, sin importar si el evento ya fue emitido. Si CEO desbloqueó manualmente y el expediente sigue vencido, el sistema re-bloquea.

**Paso 2 — Emisión de eventos (una sola vez por vida por umbral):**
- Umbral 60: emitir credit_clock.warning UNA vez. Si ya existe EventLog → skip para siempre.
- Umbral 75: emitir credit_clock.critical UNA vez. Si ya existe → skip.
- Umbral 90: emitir credit_clock.expired UNA vez. Si ya existe → skip.
- Verificación: EventLog.filter(expediente=exp, event_type=tipo).exists() → skip emisión.

**Resumen:** idempotencia aplica a emisión de eventos; el bloqueo es enforcement de seguridad y se reimpone siempre.

### Estados ignorados (FIX-15)
- Usar constante `CREDIT_CLOCK_IGNORED_STATUSES` derivada del enum central con `is_terminal=True`.
- MVP: `{CERRADO, CANCELADO}`. Un solo lugar, no hardcode en query.

### Manejo de fallo en enforcement
- Si execute_command(C17) falla → log error con expediente_id + exception → continue al siguiente.
- No retry/backoff en Sprint 2. Reintento natural en la próxima corrida diaria.
- transaction.atomic() por expediente: fallo en uno no afecta a los demás.

### Protección anti-carreras
- Dentro de cada transaction.atomic(): usar `select_for_update(skip_locked=True)`.
- Si el expediente está locked por otro worker → skip silencioso (log "skipped_due_to_lock" + continue). Se reintenta mañana.
- Evita deadlocks y que un lock bloquee el batch completo.

### Qué NO hacer con el reloj
- No enviar emails (Sprint 3+)
- No crear dashboard visual (Sprint 3)
- No implementar cobro automático (§M2: "CEO resuelve manualmente")
- No evaluar expedientes CERRADOS o CANCELADOS (reloj detenido per §D2)

## 2.3 C19 SupersedeArtifact

### Flujo normal (artefacto pre-transición)
Si el artefacto aún no fue precondición de una transición ejecutada:
```
CEO llama C19 → se reemplaza el artefacto → listo
```
Ejemplo: ART-06 (cotización flete) tiene error, pero C10 (ApproveDispatch) aún no se ejecutó.

### Flujo con protección post-transición
Si el artefacto YA fue precondición de una transición:
```
CEO llama C17 (BlockExpediente) → CEO llama C19 (SupersedeArtifact, requiere is_blocked=true) → CEO llama C18 (UnblockExpediente) → continúa
```
Ejemplo: ART-04 (SAP) habilitó T2 (→PRODUCCION). Si tiene error, hay que bloquear primero.

### Campos de modelo necesarios
ArtifactInstance necesita:
- `superseded_by`: UUID nullable, FK a ArtifactInstance (el nuevo que lo reemplaza)
- `supersedes`: UUID nullable, FK a ArtifactInstance (el original que reemplaza)
- `status` enum debe incluir valor `superseded`

Si no existen de Sprint 0 → Item 6 los agrega como migración.

## 2.4 C20 VoidArtifact

### Voidable list (MVP)
Solo estos artifact_types son voidables: ART-09 (Factura MWT). ART-10 y ART-12 no están implementados en Sprint 2.

ART-01 a ART-08 NO son voidables. Son operativos. Si tienen error → C19 (supersede), no C20 (void).

### Efecto cascada
Si ART-09 es voided → C14 (CloseExpediente) ya no puede ejecutarse porque su precondición requiere ART-09.status=completed. El CEO debe:
1. Void ART-09 (C20)
2. Emitir nueva factura (C13 — crea nuevo ART-09)
3. Registrar pago contra nueva factura (C21)
4. Cerrar (C14)

### Campo de modelo necesario
ArtifactInstance.status enum debe incluir valor `void`.

## 2.5 Event dispatcher mínimo
- Propósito Sprint 2: solo marcar EventLog.processed_at = now() para eventos pendientes
- Sin consumers reales (email, webhook, etc.)
- Prepara el terreno para Sprint 3 donde sí habrá consumers

## 2.6 Response format (heredado Sprint 1)
C19 y C20 siguen el mismo patrón:
- Response body: `{"expediente": ..., "events": [...]}`
- C19: HTTP 200 (modifica recurso existente, no crea nuevo)
- C20: HTTP 200 (modifica recurso existente)

## 2.7 Patrón de endpoints (heredado Sprint 1)
- APIView por command. No ViewSet.
- Lookup: `{pk}`
- Views thin: deserializar → services → serializar respuesta
- Toda la lógica en services.py

---

# 3. PLAN DE EJECUCIÓN (Sprint 2)

## 3.1 Secuencia real

```
PRE-SPRINT 2 — Verificaciones
│
├── Confirmar Sprint 1 DONE (18 command endpoints POST funcionales)
├── Confirmar que tests de Sprint 1 siguen passing
│
FASE A — Infra + Modelo (paralelo)
│
├── Item 6: Migraciones de modelo (AG-01) — campos superseded_by, supersedes, status void/superseded
│
├── Item 1: Redis + Celery Worker (AG-07) — infra nueva
│
FASE B — Lógica de dominio (AG-02, secuencial)
│
├── Item 2: Reloj de Crédito ← item más crítico del sprint
│   │
│   ├── Item 5: Event Dispatcher Mínimo (paralelo a Item 3)
│   │
│   ├── Item 3: C19 SupersedeArtifact
│   │   │
│   │   └── Item 4: C20 VoidArtifact
│
FASE C — Tests (AG-06)
│
└── Item 7: Tests Sprint 2 (después de Items 2-6 aprobados)
```

## 3.2 Desglose por item

### Item 1: Infra — Redis + Celery Worker

Agente: AG-07 DevOps.
Objetivo: Agregar Redis y Celery worker al stack Docker. Verificar que Celery Beat funciona.

Archivos permitidos: docker-compose.yml, config/settings/base.py (secciones CELERY_*), requirements.txt, config/celery.py, config/__init__.py.
Archivos prohibidos: apps/*, tests/.

Este es un item de infraestructura pura. Ale va a necesitar:
- Entender cómo Docker Compose agrega servicios a un stack existente
- Configurar Redis como broker (no como cache)
- Verificar que Celery worker se registra correctamente
- Verificar que Celery Beat está corriendo (puede ya existir de Sprint 0)

**Troubleshooting esperado para Ale:**
- Redis no arranca: verificar que el puerto 6379 no está ocupado, que la imagen redis:7-alpine existe
- Celery worker no se registra: verificar que `config/celery.py` existe y que `config/__init__.py` lo importa
- Celery Beat no encuentra tasks: verificar que `CELERY_BEAT_SCHEDULE` está en settings y que los tasks están en `apps/expedientes/tasks.py`
- "No module named celery": verificar que celery y redis están en requirements.txt y que la imagen se rebuildeó

**Comando de verificación:**
```bash
docker-compose exec django celery -A config inspect ping
# Debe responder: {"celery@worker": {"ok": "pong"}}

docker-compose exec django celery -A config inspect registered
# Debe mostrar los tasks registrados
```

Evidencia: Redis healthy, Celery worker registered, Beat running, task de prueba ejecuta OK.

### Item 2: Reloj de Crédito — Task + Evaluación

Agente: AG-02 API Builder.
Objetivo: Task Celery que evalúa diariamente todos los expedientes activos y aplica reglas de día 60/75/90.

Archivos permitidos: apps/expedientes/tasks.py (crear), apps/expedientes/services.py (extender).
Archivos prohibidos: models.py, views.py, urls.py, serializers.py.

Precondiciones: Item 1 aprobado (Celery funcional).

Este es el item más crítico de Sprint 2. La lógica es:

1. Task `evaluate_credit_clocks()` registrado en Celery Beat (diario 6AM UTC, definido en config/celery.py)
2. Consulta: expedientes donde credit_clock_started_at IS NOT NULL, excluyendo `CREDIT_CLOCK_IGNORED_STATUSES` (derivada del enum central con `is_terminal=True`, MVP: {CERRADO, CANCELADO})
3. Para cada expediente, dentro de `transaction.atomic()` con `select_for_update(skip_locked=True)`:
   - Si locked por otro worker → log "skipped_due_to_lock" + continue
   - Calcula `days_elapsed = (now - credit_clock_started_at).days`
4. **Paso 1 — Enforcement (SIEMPRE):** si days_elapsed >= 75 AND is_blocked=false → ejecutar C17 con actor SYSTEM. Si falla → log error + continue.
5. **Paso 2 — Emisión (una vez por vida):** verificar EventLog.exists() por (expediente, event_type). Si no existe → emitir evento del umbral más alto aplicable.
6. Si execute_command(C17) falla → log error + continue. Reintento natural mañana.

Referencia canónica: ENT_OPS_STATE_MACHINE §D2 (umbrales), §M2 (día 90), §C2 (bloqueo por sistema).

### Item 3: C19 SupersedeArtifact

Agente: AG-02 API Builder.
Precondiciones: Item 2 aprobado, Item 6 aprobado (campos de modelo existen).

Endpoint nuevo:
- POST /api/expedientes/{pk}/supersede-artifact/ → C19
- Input: original_artifact_id, new_payload, reason
- CEO only
- Precondiciones completas en §I3 + §I3.1

La complejidad está en la regla post-transición: determinar si un artefacto fue precondición de una transición ya ejecutada. Para esto, services.py necesita evaluar:
- ¿Qué transición habilita este artifact_type? (ej: ART-04 habilita T2)
- ¿Esa transición ya se ejecutó? (ej: status actual es PRODUCCION o posterior → T2 ya ocurrió)
- Si sí → expediente debe estar bloqueado para proceder

Referencia canónica: ENT_OPS_STATE_MACHINE §I3, §I3.1.

### Item 4: C20 VoidArtifact

Agente: AG-02 API Builder.
Precondiciones: Item 3 aprobado.

Endpoint nuevo:
- POST /api/expedientes/{pk}/void-artifact/ → C20
- Input: artifact_id, reason
- CEO only
- Voidable list: solo ART-09 en Sprint 2

Más simple que C19 porque no hay reemplazo, solo anulación. Pero comparte la regla post-transición.

Referencia canónica: ENT_OPS_STATE_MACHINE §I5, §I5.1.

### Item 5: Event Dispatcher Mínimo

Agente: AG-02 API Builder.
Precondiciones: Item 1 aprobado (Celery funcional).

Task Celery que cada 5 minutos marca eventos pendientes como procesados. Sin consumers reales. Es intencionalmente mínimo — su valor es validar el pipeline y mantener processed_at limpio para Sprint 3.

Puede correr en paralelo con Items 3-4 (ambos dependen solo de Item 1).

### Item 6: Migraciones de modelo

Agente: AG-01 Architect.
Precondiciones: Ninguna (puede correr al inicio del sprint).

Verificar si ArtifactInstance tiene los campos necesarios para C19/C20. Si faltan, crear migración. Si existen, marcar DONE sin cambios.

Campos necesarios:
- `superseded_by`: UUIDField, nullable, FK a self
- `supersedes`: UUIDField, nullable, FK a self
- `status` enum: agregar valores `void` y `superseded`

### Item 7: Tests Sprint 2

Agente: AG-06 QA.
Precondiciones: Items 2-6 aprobados.

3 archivos de tests: test_credit_clock.py, test_corrections.py, test_dispatcher.py. Criterios detallados en LOTE_SM_SPRINT2 Item 7.

## 3.3 Dependencias y handoffs

### Paralelismo
- Item 6 (migraciones) y Item 1 (infra) pueden correr en paralelo al inicio
- Item 5 (dispatcher) puede correr en paralelo con Items 3-4

### Cadena crítica
Item 1 → Item 2 → Item 3 → Item 4 → Item 7
La cadena más larga pasa por la lógica de dominio. Item 2 (reloj) es el blocker principal.

### Handoff AG-07 → AG-02
AG-02 no puede empezar Item 2 hasta que Item 1 esté aprobado (necesita Celery funcional para crear tasks).

### Handoff AG-01 → AG-02
AG-02 no puede empezar Item 3 hasta que Item 6 esté aprobado (necesita campos superseded_by/supersedes en el modelo).

## 3.4 Riesgos de ejecución

### Riesgo 1: Celery no funciona en el stack Docker
Causa: Redis no conecta, worker no se registra, Beat no dispara tasks.
Impacto: Bloquea todo el sprint (Items 2-5 dependen de Celery).
Mitigación: Item 1 tiene comandos de verificación explícitos. No avanzar hasta que `celery inspect ping` responda OK.
**Nota para Ale:** Este es el riesgo más probable. Celery + Docker tiene curva de aprendizaje. Presupuestar 1-2 días extra.

### Riesgo 2: Task de reloj no es idempotente
Causa: Si el task se ejecuta 2 veces, duplica eventos o re-bloquea expedientes.
Impacto: Event log contaminado, bloqueos espurios.
Mitigación: Tests explícitos de idempotencia en Item 7. El task debe verificar estado actual antes de actuar.

### Riesgo 3: Regla post-transición de C19 mal implementada
Causa: Determinar si un artefacto fue precondición de una transición ejecutada requiere mapear artifact_type → transición → estado actual.
Impacto: C19 permite supersede cuando no debería (riesgo de integridad), o lo bloquea cuando debería permitirlo.
Mitigación: CEO verifica la lógica de evaluación en services.py contra §I3.1 campo por campo.

### Riesgo 4: Ale no entiende la diferencia entre task síncrono y asíncrono
Causa: Sprint 1 fue puro request-response. Sprint 2 introduce procesos que corren solos.
Impacto: Confusión en debugging, tests que no cubren el escenario real.
Mitigación: PLB_SPRINT2_PROMPTS incluye explicación en system prompt de qué es Celery y cómo funciona en este contexto.

## 3.5 Criterio de cierre de Sprint 2

Sprint 2 está DONE cuando:
1. Redis + Celery worker + Beat funcionales
2. evaluate_credit_clocks corre diariamente y aplica reglas 60/75/90
3. Bloqueo automático día 75 funcional (SYSTEM bloquea)
4. C19 SupersedeArtifact funcional con reglas §I3.1
5. C20 VoidArtifact funcional para ART-09
6. Flujo corrección post-transición: Block → Supersede → Unblock OK
7. Event dispatcher marcando processed_at
8. Todos los tests passing (Sprint 1 + Sprint 2)
9. 20 command endpoints POST totales (18 Sprint 1 + C19 + C20)

---

# 4. PLAN OPERATIVO PARA ALE (Sprint 2)

## 4.1 Antes de arrancar

Confirmar que Sprint 1 está cerrado:
- Los 10 items de Sprint 1 DONE y aprobados
- Happy path completo verificable via API: C1→...→C14
- Todos los tests de Sprint 1 passing
- `python manage.py check` sin errores

Confirmar documentos vigentes:
- ENT_OPS_STATE_MACHINE v1.2.2 — FROZEN (mismo que Sprint 1)
- PLB_ORCHESTRATOR v1.2.2 — FROZEN (mismo que Sprint 1)
- LOTE_SM_SPRINT2 — FROZEN (nuevo)

## 4.2 Orden de ejecución recomendado

```
Día 1-2: Item 6 (migraciones) + Item 1 (infra Redis/Celery) — en paralelo
         Ale despacha Item 6 a Antigravity primero (rápido, puede ser no-op)
         Luego despacha Item 1 (infra — más lento, requiere Docker troubleshooting)

Día 3-4: Item 2 (reloj de crédito) — item más crítico
         Requiere que Item 1 esté aprobado
         CEO revisa lógica de idempotencia en tasks.py

Día 4-5: Item 5 (event dispatcher) — puede ir en paralelo con Item 3
         Item 3 (C19 SupersedeArtifact) — requiere Item 6 aprobado
         
Día 5-6: Item 4 (C20 VoidArtifact) — secuencial después de Item 3

Día 6-7: Item 7 (tests) — después de Items 2-6 aprobados
```

**Nota realista:** Con curva de Ale en Celery/Redis, presupuestar 8-12 días.

## 4.3 Interacción con Antigravity

Misma mecánica que Sprint 1: system prompt + prompt táctico del item. Un item a la vez.

**Diferencia clave:** Sprint 2 tiene Items de infra (Docker) que Antigravity puede no resolver bien al primer intento. Ale debe estar preparado para:
- Item 1: 2-3 iteraciones probables. Antigravity genera docker-compose, Ale levanta, algo falla, vuelve a Antigravity con el error.
- Item 2: La lógica del task es compleja. Ale debe verificar idempotencia.
- Items 3-4: Similares a Sprint 1 (endpoint + services), Ale ya tiene el músculo.

## 4.4 Revisión de outputs

### Item 1 (infra): Verificación mecánica
```bash
# Redis corriendo
docker-compose ps | grep redis
# Celery worker registrado
docker-compose exec django celery -A config inspect ping
# Celery Beat corriendo
docker-compose ps | grep beat
# Task de prueba
docker-compose exec django celery -A config call apps.expedientes.tasks.test_task
```

### Item 2 (reloj): REVISIÓN PROFUNDA
- tasks.py: verificar que consulta usa CREDIT_CLOCK_IGNORED_STATUSES (no hardcode)
- tasks.py: verificar DOS pasos separados — Paso 1 enforcement (siempre), Paso 2 emisión (una vez por vida)
- tasks.py: verificar select_for_update(skip_locked=True) por expediente
- tasks.py: verificar que fallo en C17 → log error + continue (no tumba batch)
- tasks.py: verificar que cada expediente es atomic independiente
- tasks.py: verificar que locked → log "skipped_due_to_lock" + continue
- services.py: verificar que bloqueo automático usa blocked_by_type=SYSTEM
- Beat schedule: verificar que evaluate_credit_clocks está registrado

### Items 3-4 (C19/C20): Revisión enfocada
- services.py: verificar regla post-transición (§I3.1.3)
- services.py: verificar voidable_list para C20 (solo ART-09)
- views.py: thin, llama a services
- Verificar que C19 y C20 siguen patrón de response {"expediente": ..., "events": [...]}

### Item 5 (dispatcher): Revisión rápida
- Task simple: marca processed_at. Verificar que no hace nada más.

### Item 7 (tests): Verificar cobertura
- Idempotencia del reloj (test crucial)
- Concurrencia select_for_update del reloj (test crucial — respalda política anti-carreras)
- Post-transición de C19 (test crucial)
- Void ART-09 → C14 falla (test de cascada)

## 4.5 Protocolo SPEC_GAP (mismo que Sprint 1)

Cuando Antigravity reporta [SPEC_GAP]:
1. Ale NO resuelve
2. Ale NO dice "asumí X"
3. Ale escala al CEO con: item + gap + texto exacto
4. CEO decide
5. Si afecta dominio → BLOCKED

## 4.6 Branches y merges

```
main (Sprint 1 completo)
├── sprint2/item-1-infra-celery         ← AG-07 DevOps
├── sprint2/item-2-credit-clock         ← AG-02 — REVISIÓN PROFUNDA
├── sprint2/item-3-supersede-artifact   ← AG-02
├── sprint2/item-4-void-artifact        ← AG-02
├── sprint2/item-5-event-dispatcher     ← AG-02
├── sprint2/item-6-migrations           ← AG-01 (puede ser no-op)
└── sprint2/item-7-tests                ← AG-06
```

## 4.7 Cuándo escalar

Escalar al CEO cuando:
- Celery no levanta después de 2 intentos con Antigravity
- El reloj de crédito bloquea expedientes que no debería
- C19 tiene lógica post-transición que no coincide con §I3.1
- Un modelo necesita campos que no existen y Item 6 no los cubrió
- Antigravity intenta crear notificaciones, consumers, Redis Streams, o dashboard
- Tests de idempotencia fallan

## 4.8 Preparación Sprint 3

Antes de cerrar Sprint 2, verificar:
- Celery healthy: `celery inspect ping` OK
- Reloj: crear expediente con credit_clock_started_at 70 días atrás → correr task → verificar que genera warning
- Reloj: crear expediente con clock 80 días atrás → correr task → verificar bloqueo automático
- Reloj: desbloquear manualmente el de 80 días → correr task → verificar re-bloqueo (enforcement siempre)
- C19: Block → Supersede ART-05 → Unblock → flujo continúa
- C20: Void ART-09 → C14 falla → C13 nueva factura → C21 pago → C14 cierra
- Dispatcher: eventos recientes tienen processed_at != null
- Todos los tests passing (Sprint 1 + Sprint 2)
- No hay [SPEC_GAP] abiertos

---

Stamp: DRAFT — Pendiente aprobación CEO
