# LOTE_SM_SPRINT21 — Monitor de Actividad + Role-Based Sidebar
id: LOTE_SM_SPRINT21
version: 1.3
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
status: DRAFT — Pendiente aprobación CEO
stamp: DRAFT v1.3 — 2026-03-30
tipo: Lote ruteado (ref → PLB_ORCHESTRATOR §E)
sprint: 21
priority: P1
depends_on: LOTE_SM_SPRINT20B (EN EJECUCIÓN — frontend policy-driven)
refs: ENT_OPS_STATE_MACHINE (FROZEN v1.2.2),
      ENT_PLAT_EVENTOS (DRAFT — taxonomía eventos),
      ENT_PLAT_SEGURIDAD,
      ROADMAP_EXTENDIDO_POST_DIRECTRIZ (VIGENTE — numeración definitiva)

changelog:
  - v1.0 (2026-03-30): Compilación inicial desde ROADMAP_EXTENDIDO_POST_DIRECTRIZ (S21 renumerado, ex-S21B). 7 items: 2 backend modelo, 2 backend endpoint, 2 frontend, 1 QA. Fuente: hallazgos Agent-C (sidebar) y Agent-D (EventLog proforma FK).
  - v1.1 (2026-03-30): Fixes auditoría R1 (ChatGPT 8.6/10 — 7 hallazgos). B1: action_source renombrado de command_id, max_length=32, contrato de valores normalizados definido. B2: contrato de permisos unificado en función `get_visible_events(user)` reutilizada en feed y count, AGENT_* ve solo expedientes que opera. B3: mark_seen extraído a POST /activity-feed/mark-seen/ separado, solo avanza al max(id) del queryset base (sin filtros), no acepta filtros. B4: campos nuevos en EventLog son todos null=True (nullable real), narrativa de migración consistente. M1: count usa `[:100]` slice en vez de `.count()` para cap real de performance. M2: user_display nunca cae a email, fallback a rol o "Usuario". M3: S21-07 renombrado a "Tests backend (24) + validación manual frontend", smoke FE documentados como checklist manual.
  - v1.2 (2026-03-30): Fixes auditoría R2 (ChatGPT 9.1/10 — 5 hallazgos). N1: CEO desacoplado de is_superuser, usa role='CEO' explícito con is_superuser como fallback técnico documentado. N2: AGENT_* definición unificada a "ha operado" (EventLog con user=agent), borrada toda referencia a asignación. N3: response de mark-seen reemplazado — `marked` eliminado, retorna `previous_last_seen` + `last_seen_event_id`. N4: contrato action_source cerrado — commands explícitamente "C1..C22 (todos los del state machine §F)". N5 (nuevo de R2): documentada semántica de concurrencia GET+POST mark-seen para MVP.
  - v1.3 (2026-03-30): Fixes auditoría R3 (ChatGPT 9.3/10 — 4 hallazgos). N6: changelog N4 corregido C1..C21→C1..C22 para alinear con contrato formal. N7: nota de concurrencia mark-seen reescrita — evento marcado sin renderizar NO reaparece como unread, puede aparecer en futuras cargas del feed si está en rango. N8: tabla seguridad mark-seen actualizada — reconoce caso concurrente MVP en vez de vender versión idealizada. N9: contrato UI unread cerrado — unread = id > last_seen_event_id del count previo a abrir el panel.

---

## Contexto

Sprint 21 implementa observabilidad interna: un feed de actividad que permite al CEO y a los agentes internos ver qué pasó en el sistema sin revisar EventLog manualmente, y un sidebar filtrado por rol que ya existe en el código pero no está activado.

**Cambio clave en 3 frases:**
1. EventLog se extiende con campos que permiten reconstruir quién hizo qué, en qué proforma, y qué transición provocó.
2. Un modelo liviano (UserNotificationState) permite calcular "no leídos" por usuario sin marcar cada evento individualmente.
3. El frontend muestra un badge con count + panel dropdown, y el sidebar existente se activa para filtrar por rol.

**Estado post-Sprint 20B (asumido DONE):**
- Frontend policy-driven: artefactos renderizados desde artifact_policy del bundle
- Vista CEO con N proformas por expediente
- Vista portal cliente: OC → líneas con estado
- Gate UI funcional (bloquea avance si faltan artefactos)
- Labels de artefactos desde constante frontend

**EventLog actual (Sprint 1, §K de state machine):**
- `expediente` FK (obligatorio)
- `event_type` CharField (ej: 'expediente.state_changed', 'proforma.created', 'artifact.voided')
- `payload` JSONField (datos arbitrarios del evento)
- `created_at` DateTimeField (auto)
- Append-only (ref → POL_INMUTABILIDAD)
- Ya se usa en: dispatcher post-hooks (S18), create_proforma (S20), change_mode (S20), void (S20)

**Lo que falta (scope de este sprint):**
- EventLog no tiene user FK → no se sabe quién ejecutó
- EventLog no tiene proforma FK → hay que buscar en payload para filtrar
- EventLog no tiene action_source ni previous/new status → difícil reconstruir transiciones
- 0 mecanismo de "leído/no leído" por usuario
- 0 endpoints de activity feed
- 0 badge ni panel en el frontend
- Sidebar tiene código de roles pero está desactivado (Agent-C hallazgo)

---

## Decisiones ya resueltas (NO preguntar de nuevo)

| Decisión | Ref | Detalle |
|----------|-----|---------|
| Proforma como unidad operativa | DIRECTRIZ | Implementado en S20. EventLog ya registra proforma en payload. |
| Polling, no WebSocket | ROADMAP_EXTENDIDO | Polling 60s es suficiente para MVP. WebSocket = nunca para este scope. |
| EventLog es append-only | POL_INMUTABILIDAD | No se editan ni eliminan entries. UserNotificationState es el mecanismo de "lectura". |
| Sidebar roles ya existe | Agent-C hallazgo | `layout/Sidebar.tsx` tiene la lógica, solo hay que activarla. |

## Decisiones nuevas Sprint 21

| Decisión | Detalle |
|----------|---------|
| Extender EventLog, no crear ActivityLog | EventLog ya tiene toda la data. Agregar campos es más económico que crear modelo paralelo. Migración aditiva, 0 riesgo de romper consumers existentes. |
| UserNotificationState con last_seen_event_id | Patrón "high-water mark": el usuario ve todo lo que tiene ID > last_seen_event_id. 1 row por usuario, 1 UPDATE al marcar como visto. Sin tabla intermedia user×event. |
| Activity feed = vista sobre EventLog | No duplicar datos. El endpoint consulta EventLog filtrado por permisos del usuario. |
| Badge count con slice real (no COUNT) | `GET /activity-feed/count/` usa `qs[:100]` para determinar count sin full table scan. Cap visual en 99. (R1-M1) |
| mark_seen = POST separado, sin filtros | POST /activity-feed/mark-seen/ avanza last_seen_event_id al max(id) del queryset base del usuario (sin filtros aplicados). No es query param de GET. (R1-B3) |
| Permisos centralizados en `get_visible_events(user)` | Una sola función determina qué ve cada rol. Feed y count la reutilizan sin duplicar lógica. (R1-B2) |

---

## Convenciones Sprint 21

1. **State machine FROZEN.** No se modifican estados, transiciones ni commands. Se extienden los datos que EventLog captura, no la lógica de negocio.
2. **Additive-only.** 5 AddField en EventLog (todos `null=True`) + 1 CreateModel (UserNotificationState). 0 AlterField, 0 RemoveField. En PostgreSQL, AddField nullable no requiere table rewrite — es instantáneo independientemente del número de rows. (R1-B4: corregido de "blank=True default=''" a nullable real)
3. **Backward compat.** Todos los campos nuevos en EventLog son `null=True`. EventLog entries pre-S21 tienen user=NULL, proforma=NULL, action_source=NULL, previous_status=NULL, new_status=NULL.
4. **Permisos vía `get_visible_events(user)`.** Una sola función centralizada (R1-B2). CEO = usuario con `role='CEO'` (con `is_superuser` como fallback técnico para admin de Django, documentado como excepción — R2-N1). AGENT_* ve solo expedientes donde ha operado, definido como "existe al menos un EventLog con user=agent para ese expediente" (R2-N2 — no hay modelo de asignación; si se crea en futuro, esta función se actualiza). CLIENT_* ve solo expedientes de su client_subsidiary, excluyendo eventos CEO-ONLY.
5. **Polling 60s, no más frecuente.** El endpoint count/ es barato (slice de 100 IDs con índice) pero no hay razón para más de 1 request/minuto.

---

## Contrato de permisos — función centralizada (R1-B2)

```python
# backend/apps/expedientes/services/activity_permissions.py

# Eventos que CLIENT_* nunca ve (CEO-ONLY)
CEO_ONLY_EVENT_TYPES = frozenset([
    'cost.registered',
    'commission.invoiced',
    'compensation.noted',
])


def get_visible_events(user, base_qs=None):
    """
    Retorna queryset de EventLog filtrado por permisos del usuario.
    Función única reutilizada por feed, count y mark-seen — nunca duplicar.
    
    Reglas:
    - CEO (role='CEO'): todo. is_superuser es fallback técnico (R2-N1).
    - AGENT_*: solo expedientes donde ha operado (existe EventLog con user=agent) (R2-N2).
    - CLIENT_*: solo expedientes de su client_subsidiary, sin eventos CEO-ONLY.
    """
    from apps.expedientes.models import EventLog
    
    qs = base_qs if base_qs is not None else EventLog.objects.all()
    qs = qs.select_related('expediente', 'proforma', 'user')
    
    # CEO: role explícito. is_superuser como fallback técnico (R2-N1).
    user_role = getattr(user, 'role', None)
    if user_role == 'CEO' or user.is_superuser:
        return qs
    
    if hasattr(user, 'client_subsidiary') and user.client_subsidiary:
        # CLIENT_*: solo sus expedientes, sin eventos CEO-ONLY
        return qs.filter(
            expediente__client_subsidiary=user.client_subsidiary
        ).exclude(
            event_type__in=CEO_ONLY_EVENT_TYPES
        )
    
    # AGENT_*: solo expedientes donde ha operado (R2-N2).
    # Definición: "ha operado" = existe al menos un EventLog con user=este agente
    # para ese expediente. No hay modelo de asignación formal; si se crea
    # (ej: UserExpedienteAssignment en S27), esta función se actualiza.
    operated_expediente_ids = (
        EventLog.objects
        .filter(user=user)
        .values_list('expediente_id', flat=True)
        .distinct()
    )
    return qs.filter(expediente_id__in=operated_expediente_ids)
```

**Regla:** Feed y count SIEMPRE llaman `get_visible_events(request.user)`. Ningún endpoint implementa su propia lógica de permisos para el activity feed.

---

## Contrato de action_source — valores normalizados (R1-B1)

El campo `action_source` (renombrado de `command_id`) identifica qué acción generó el evento. `max_length=32`, `null=True`.

**Valores válidos (contrato cerrado — R2-N4):**

| Categoría | Valores | Regla |
|-----------|---------|-------|
| Commands canónicos | Cualquier command del state machine §F: `C1`, `C2`, `C3`, `C4`, `C5`, `C6`, `C7`, `C8`, `C9`, `C10`, `C11`, `C12`, `C13`, `C14`, `C15`, `C16`, `C17`, `C18`, `C19`, `C20`, `C21`, `C22` | Exactamente el nombre del command handler |
| Acciones de proforma (S20) | `create_proforma`, `reassign_line`, `change_mode` | Nombre de la acción funcional |
| Edición por estado (S18) | `patch_registro`, `patch_produccion`, `patch_preparacion`, `patch_despacho`, `patch_transito`, `patch_en_destino` | `patch_` + status en minúsculas |
| Sistema | `system_credit_clock`, `system_cron` | `system_` + nombre del job |
| NULL | (pre-S21 entries) | Backward compat, no se backfilla |

**Regla:** Cualquier nuevo tipo de acción que genere EventLog DEBE registrarse en esta tabla antes de implementarse. Strings no listados son un bug.

---

## FASE 0 — Modelos (migración aditiva)

### S21-01: Extender EventLog

**Agente:** AG-02 Backend
**Dependencia:** Ninguna interna
**Prioridad:** P0 — bloqueante para S21-03, S21-04
**Acción:** AddField × 5 (todos null=True)

**Archivo a tocar:**
- `backend/apps/expedientes/models.py` (modelo EventLog)

**Campos a agregar:**

```python
# En EventLog — agregar 5 campos, TODOS null=True (R1-B4):

user = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    null=True, blank=True,
    on_delete=models.SET_NULL,
    related_name='event_logs',
    help_text="Usuario que ejecutó la acción. Null = sistema (cron, Celery) o pre-S21."
)

proforma = models.ForeignKey(
    'ArtifactInstance',
    null=True, blank=True,
    on_delete=models.SET_NULL,
    limit_choices_to={'artifact_type': 'ART-02'},
    related_name='event_logs',
    help_text="Proforma asociada al evento. "
              "Permite filtrar actividad por proforma sin parsear payload."
)

action_source = models.CharField(
    max_length=32,
    null=True, blank=True,
    help_text="Acción que generó el evento. Contrato cerrado: "
              "C1..C22 (commands §F), create_proforma, reassign_line, change_mode, "
              "patch_{estado}, system_credit_clock, system_cron. "
              "Null = pre-S21. Nuevos valores requieren actualizar contrato."
)

previous_status = models.CharField(
    max_length=20,
    null=True, blank=True,
    help_text="Estado del expediente ANTES de la acción. "
              "Null si no aplica (evento sin transición de estado)."
)

new_status = models.CharField(
    max_length=20,
    null=True, blank=True,
    help_text="Estado del expediente DESPUÉS de la acción. "
              "Null si no aplica."
)
```

**Índices a agregar:**

```python
class Meta:
    indexes = [
        # ... existentes ...
        # Índice principal para el feed: filter(expediente) + order_by(-id)
        models.Index(fields=['expediente', '-id'], name='idx_eventlog_exp_id_desc'),
        # Índice para filtro por proforma
        models.Index(fields=['proforma', '-id'], name='idx_eventlog_pf_id_desc'),
        # Índice para count high-water mark: filter(id__gt=X)
        # El PK (id) ya tiene índice implícito — no agregar redundante (R1-m2)
    ]
```

**Nota sobre índices (R1-m2):** El filtro principal del feed es `expediente_id + ORDER BY -id`. El filtro del count es `id__gt=X` que usa el PK index. No se agrega índice redundante sobre `-id` porque el PK ya lo cubre. El índice `user/-created_at` de v1.0 se elimina porque no coincide con ningún query real del feed.

**Actualizar puntos de creación de EventLog:**

```python
# En post_command_hooks (S18) — agregar campos:
def post_command_hooks(command_name, expediente, request=None, result=None, **kwargs):
    user = getattr(request, 'user', None) if request else None
    
    proforma = None
    if result and hasattr(result, 'artifact_type') and result.artifact_type == 'ART-02':
        proforma = result
    elif result and hasattr(result, 'parent_proforma'):
        proforma = result.parent_proforma
    
    previous_status = kwargs.get('previous_status', None)
    new_status = expediente.status if kwargs.get('status_changed', False) else None
    
    EventLog.objects.create(
        expediente=expediente,
        event_type=kwargs.get('event_type', f'command.{command_name.lower()}'),
        payload=kwargs.get('payload', {}),
        user=user,
        proforma=proforma,
        action_source=command_name,       # R1-B1: valor normalizado
        previous_status=previous_status,
        new_status=new_status,
    )
```

**Actualizar create_proforma (S20):**
- `action_source='create_proforma'` (no 'C_create_proforma')

**Actualizar change_mode (S20):**
- `action_source='change_mode'`

**Actualizar reassign_line (S20):**
- `action_source='reassign_line'`

**Actualizar PATCH views (S18):**
- `action_source=f'patch_{expediente.status.lower()}'` (ej: 'patch_registro')

**Actualizar Celery tasks (S2):**
- `action_source='system_credit_clock'`

**Criterio de done:**
- [ ] 5 campos nuevos en EventLog, TODOS `null=True` (R1-B4)
- [ ] Migración es AddField × 5 + AddIndex × 2
- [ ] EventLog entries pre-S21 tienen todos los campos nuevos = NULL
- [ ] Dispatcher crea EventLog con user y action_source populados
- [ ] action_source usa solo valores del contrato normalizado (R1-B1)
- [ ] create_proforma, change_mode, reassign_line populan proforma FK
- [ ] PATCH views usan action_source='patch_{estado}'
- [ ] Celery tasks usan action_source='system_*', user=None
- [ ] Admin muestra campos nuevos con filtros

---

### S21-02: Modelo UserNotificationState

**Agente:** AG-02 Backend
**Dependencia:** S21-01
**Prioridad:** P0 — bloqueante para S21-03, S21-04
**Acción:** CreateModel

**Archivo a tocar:**
- `backend/apps/expedientes/models.py`

**Modelo:**

```python
class UserNotificationState(models.Model):
    """
    High-water mark de lectura de actividad por usuario.
    
    1 row por usuario. last_seen_event_id indica hasta qué EventLog
    el usuario ha "leído". Eventos con id > last_seen_event_id son "no leídos".
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_state',
        primary_key=True,
    )
    last_seen_event_id = models.BigIntegerField(
        default=0,
        help_text="ID del último EventLog visto. Eventos con id > este valor son 'no leídos'."
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Estado de notificación de usuario'

    def __str__(self):
        return f"{self.user} — last_seen: {self.last_seen_event_id}"
```

**Criterio de done:**
- [ ] Modelo creado con OneToOneField(user) como PK
- [ ] Migración es CreateModel
- [ ] Admin registrado
- [ ] get_or_create funciona (primera visita crea row con last_seen=0)

---

## FASE 1 — Endpoints

### S21-03: GET /activity-feed/ con filtrado

**Agente:** AG-02 Backend
**Dependencia:** S21-01, S21-02
**Prioridad:** P0 — core del sprint
**Acción:** Crear endpoint

**Archivos a crear/tocar:**
- `backend/apps/expedientes/services/activity_permissions.py` (CREAR — función centralizada)
- `backend/apps/expedientes/views.py` (o views/activity.py)
- `backend/apps/expedientes/serializers.py`
- `backend/apps/expedientes/urls.py`

**Endpoint:**

| Método | Path | Permisos | Descripción |
|--------|------|----------|-------------|
| GET | `/api/activity-feed/` | Autenticado | Feed de actividad filtrado por rol |
| POST | `/api/activity-feed/mark-seen/` | Autenticado | Marcar como visto (R1-B3) |

**Query params (solo GET):**

| Param | Tipo | Default | Descripción |
|-------|------|---------|-------------|
| `expediente` | int | — | Filtrar por expediente ID |
| `proforma` | int | — | Filtrar por proforma ID |
| `event_type` | string | — | Filtrar por tipo |
| `unread_only` | bool | false | Solo id > last_seen_event_id |
| `page` | int | 1 | Paginación |
| `page_size` | int | 25 | Max 100 |

**Pseudocódigo:**

```python
from apps.expedientes.services.activity_permissions import get_visible_events


class ActivityFeedView(generics.ListAPIView):
    serializer_class = EventLogFeedSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Permisos centralizados (R1-B2)
        qs = get_visible_events(user).order_by('-id')
        
        # Filtros opcionales
        expediente_id = self.request.query_params.get('expediente')
        if expediente_id:
            qs = qs.filter(expediente_id=expediente_id)
        
        proforma_id = self.request.query_params.get('proforma')
        if proforma_id:
            qs = qs.filter(proforma_id=proforma_id)
        
        event_type = self.request.query_params.get('event_type')
        if event_type:
            qs = qs.filter(event_type=event_type)
        
        unread_only = self.request.query_params.get('unread_only', '').lower() == 'true'
        if unread_only:
            state, _ = UserNotificationState.objects.get_or_create(user=user)
            qs = qs.filter(id__gt=state.last_seen_event_id)
        
        return qs


class ActivityFeedMarkSeenView(views.APIView):
    """
    POST /activity-feed/mark-seen/
    
    Avanza last_seen_event_id al max(id) del queryset BASE del usuario
    (sin filtros). Esto garantiza que "abrir el panel" = "marcar todo como visto",
    no "marcar accidentalmente eventos no mostrados". (R1-B3)
    
    Semántica de concurrencia MVP (R2-N5, R3-N7): si un evento llega entre el GET
    del feed y este POST, puede quedar incluido en el watermark y por tanto marcado
    como "visto" sin haberse renderizado en pantalla. En ese caso, el evento NO
    reaparecerá como unread en el siguiente polling del badge. Podrá aparecer en
    una futura carga del feed si sigue dentro del rango consultado, pero no
    necesariamente como no leído. Esto es aceptable para MVP.
    
    No acepta filtros. No acepta parámetros.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        
        # Queryset BASE sin filtros — permisos centralizados
        base_qs = get_visible_events(user).order_by('-id')
        
        # Max ID visible para este usuario
        latest = base_qs.values_list('id', flat=True).first()
        
        if latest is None:
            return Response({
                'previous_last_seen': 0,
                'last_seen_event_id': 0,
            })
        
        state, _ = UserNotificationState.objects.get_or_create(user=user)
        previous = state.last_seen_event_id
        
        if latest > state.last_seen_event_id:
            state.last_seen_event_id = latest
            state.save(update_fields=['last_seen_event_id', 'updated_at'])
        
        return Response({
            'previous_last_seen': previous,
            'last_seen_event_id': state.last_seen_event_id,
        })


class EventLogFeedSerializer(serializers.ModelSerializer):
    """
    Serializer para el feed. No expone payload ni email. (R1-M2)
    """
    expediente_number = serializers.CharField(
        source='expediente.expediente_number', read_only=True
    )
    proforma_number = serializers.SerializerMethodField()
    user_display = serializers.SerializerMethodField()
    
    class Meta:
        model = EventLog
        fields = [
            'id', 'event_type', 'action_source',
            'previous_status', 'new_status',
            'expediente_id', 'expediente_number',
            'proforma_id', 'proforma_number',
            'user_id', 'user_display',
            'created_at',
        ]
    
    def get_proforma_number(self, obj):
        if obj.proforma and obj.proforma.payload:
            return obj.proforma.payload.get('proforma_number', '')
        return ''
    
    def get_user_display(self, obj):
        """
        Nunca expone email. (R1-M2)
        Fallback chain: nombre completo → rol → "Usuario" → "Sistema"
        """
        if not obj.user:
            return 'Sistema'
        full_name = obj.user.get_full_name()
        if full_name and full_name.strip():
            return full_name.strip()
        # Fallback a rol si existe
        role = getattr(obj.user, 'role', None)
        if role:
            return role
        return 'Usuario'
```

**Reglas de seguridad:**
- Permisos vía `get_visible_events()` — nunca inline (R1-B2)
- CLIENT_* NUNCA ve eventos en `CEO_ONLY_EVENT_TYPES`
- AGENT_* solo ve expedientes que ha operado
- payload NO se serializa
- user_display NUNCA cae a email (R1-M2)
- mark_seen es POST separado, sin filtros, avanza al max del queryset base (R1-B3)

**Criterio de done:**
- [ ] GET /activity-feed/ retorna lista paginada filtrada por permisos
- [ ] Filtros: expediente, proforma, event_type, unread_only
- [ ] POST /activity-feed/mark-seen/ avanza last_seen al max(id) del queryset base
- [ ] mark_seen NO acepta filtros ni parámetros (R1-B3)
- [ ] Permisos vía get_visible_events() en ambos endpoints (R1-B2)
- [ ] user_display nunca expone email (R1-M2)
- [ ] Paginación default=25, max=100

---

### S21-04: GET /activity-feed/count/

**Agente:** AG-02 Backend
**Dependencia:** S21-01, S21-02
**Prioridad:** P0
**Acción:** Crear endpoint

**Endpoint:**

| Método | Path | Permisos | Descripción |
|--------|------|----------|-------------|
| GET | `/api/activity-feed/count/` | Autenticado | Count no leídos para badge |

**Pseudocódigo:**

```python
class ActivityFeedCountView(views.APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        state, _ = UserNotificationState.objects.get_or_create(user=user)
        
        # Permisos centralizados (R1-B2)
        qs = get_visible_events(user).filter(id__gt=state.last_seen_event_id)
        
        # Slice real para cap de performance (R1-M1):
        # Solo leer hasta 100 IDs — si hay 100, sabemos que hay más.
        # Esto evita COUNT(*) sobre millones de rows.
        ids = list(qs.order_by('-id').values_list('id', flat=True)[:100])
        n = len(ids)
        
        return Response({
            'unread_count': min(n, 99),
            'has_more': n == 100,
            'last_seen_event_id': state.last_seen_event_id,
        })
```

**Optimización real (R1-M1):**
- `[:100]` hace un `LIMIT 100` en PostgreSQL — no lee más de 100 rows
- Si `len(ids) == 100` → hay al menos 100 no leídos → `has_more=true`
- Si `len(ids) < 100` → count exacto
- El filtro `id__gt=X` usa el PK index — no necesita índice adicional

**Criterio de done:**
- [ ] GET /activity-feed/count/ retorna `{ unread_count, has_more, last_seen_event_id }`
- [ ] Permisos vía get_visible_events() (R1-B2)
- [ ] Cap real con slice [:100], no COUNT (R1-M1)
- [ ] < 50ms (verificar con EXPLAIN)
- [ ] get_or_create para usuarios sin NotificationState

---

## FASE 2 — Frontend

### S21-05: Badge header + panel dropdown

**Agente:** AG-03 Frontend
**Dependencia:** S21-03, S21-04
**Prioridad:** P0
**Acción:** Crear componentes

**Archivos a crear:**
- `frontend/src/components/ui/ActivityBadge.tsx`
- `frontend/src/components/ui/ActivityPanel.tsx`
- `frontend/src/hooks/useActivityFeed.ts`

**Archivo a tocar:**
- `frontend/src/components/layout/Header.tsx` (agregar badge)

**ActivityBadge.tsx:**

```typescript
// Comportamiento:
// 1. Polling cada 60s a GET /activity-feed/count/
// 2. Badge numérico rojo si unread_count > 0
// 3. "99+" si has_more=true
// 4. Click → abre ActivityPanel
// 5. Al abrir panel:
//    a. Llama GET /activity-feed/?page_size=20 (solo lectura, sin mark_seen)
//    b. Llama POST /activity-feed/mark-seen/ (marca todo como visto)
//    c. Badge se resetea a 0
// 6. Polling suspendido mientras panel abierto
```

**ActivityPanel.tsx:**

```typescript
// Comportamiento:
// 1. Dropdown desde el badge
// 2. Lista últimas 20 actividades
// 3. Cada item:
//    - Ícono por event_type
//    - "{user_display} {acción} {expediente_number}"
//    - Si hay proforma: "+ PF-{number}"
//    - Timestamp relativo (hace 5 min, hace 2 horas)
// 4. Click → navega a /dashboard/expedientes/{id}
// 5. Items no leídos con fondo highlight sutil
//
// Contrato unread (R3-N9):
// Un item se considera "unread" si item.id > last_seen_event_id
// obtenido del último GET /activity-feed/count/ ANTES de abrir el panel.
// El hook useActivityFeed mantiene este valor en estado local.
// Después del POST mark-seen, todos los items pasan a "read".
```

**useActivityFeed.ts:**

```typescript
function useActivityFeed() {
    // Retorna:
    // - unreadCount: number
    // - hasMore: boolean
    // - lastSeenEventId: number  // del último count, usado para highlight unread (R3-N9)
    // - activities: EventLogItem[]
    // - isLoading: boolean
    // - markAsSeen: () => Promise<void>  // POST /activity-feed/mark-seen/
    // - refresh: () => void
    
    // Polling 60s con pausa en tab inactiva (document.hidden)
    // Al abrir panel: capturar lastSeenEventId actual → fetch activities → markAsSeen()
    // Items con id > lastSeenEventId capturado = highlight unread (R3-N9)
}
```

**Mapeo event_type → texto UI:**

| event_type | Texto |
|------------|-------|
| `expediente.state_changed` | `{user} avanzó {exp} a {new_status}` |
| `expediente.created` | `{user} creó expediente {exp}` |
| `proforma.created` | `{user} creó proforma {pf} en {exp}` |
| `proforma.mode_changed` | `{user} cambió modo de {pf}` |
| `artifact.voided` | `{user} anuló artefacto en {exp}` |
| `command.c21` | `{user} registró pago en {exp}` |
| `merge` | `{user} fusionó expedientes` |
| `line.reassigned` | `{user} reasignó línea en {exp}` |
| Default | `{user} actualizó {exp}` |

**Criterio de done:**
- [ ] Badge en header con count numérico rojo
- [ ] "99+" si has_more
- [ ] Panel dropdown con actividades recientes
- [ ] Click navega a expediente
- [ ] Al abrir panel: GET feed + POST mark-seen (R1-B3)
- [ ] Polling 60s con pausa en tab inactiva
- [ ] 0 hex hardcodeados — CSS variables
- [ ] Responsive (panel full-width en mobile)

---

### S21-06: Activar role-based sidebar

**Agente:** AG-03 Frontend
**Dependencia:** Ninguna (paralelo con S21-05)
**Prioridad:** P1
**Acción:** Activar código existente

**Archivo a tocar:**
- `frontend/src/components/layout/Sidebar.tsx`

**Reglas de visibilidad por rol:**

| Rol | Items visibles |
|-----|----------------|
| CEO | Todo: Dashboard, Expedientes, Brands, Clients, Suppliers, Products, Portal, Settings |
| AGENT_* | Operaciones: Dashboard, Expedientes, Products |
| CLIENT_* | Portal: Portal Home, Mis Pedidos, Documentos |

**Acción:**
1. Verificar `Sidebar.tsx` — buscar lógica de roles existente
2. Si comentada → descomentar
3. Si es feature flag → activar
4. Si no existe → implementar (~30 líneas de filtrado por rol)

**Criterio de done:**
- [ ] CEO ve todos los items
- [ ] CLIENT_* ve solo portal
- [ ] AGENT_* ve solo operaciones
- [ ] No hay ruta visible que el usuario no pueda acceder
- [ ] Cambio mínimo si el código ya existe

---

## FASE 3 — Tests + Validación

### S21-07: Tests backend (24) + validación manual frontend

**Agente:** AG-02 Backend (tests) + AG-03 Frontend (validación manual)
**Dependencia:** Todos los items anteriores
**Prioridad:** P0
**Acción:** Tests automatizados backend + checklist manual frontend (R1-M3)

**Archivo a crear:**
- `backend/apps/expedientes/tests/test_activity_feed.py`

**Tests backend (24):**

```
# EventLog extendido
1. Command C1 → EventLog con user, action_source='C1' ✓
2. Command C5 → EventLog con previous_status='REGISTRO', new_status='PRODUCCION' ✓
3. create_proforma → EventLog con proforma FK populado, action_source='create_proforma' ✓
4. change_mode → EventLog con proforma FK, action_source='change_mode' ✓
5. Celery task (credit clock) → EventLog con user=NULL, action_source='system_credit_clock' ✓
6. EventLog pre-S21 (sin campos nuevos) → consultable, campos = NULL ✓

# UserNotificationState
7. Primera visita: get_or_create → last_seen_event_id=0 ✓
8. POST mark-seen → last_seen avanza, response tiene previous_last_seen + last_seen_event_id (R2-N3) ✓
9. Segundo mark-seen con nuevos eventos → last_seen avanza ✓

# Activity feed endpoint
10. GET /activity-feed/ sin filtros → paginado ✓
11. GET /activity-feed/?expediente=1 → solo ese expediente ✓
12. GET /activity-feed/?proforma=5 → solo esa proforma ✓
13. GET /activity-feed/?unread_only=true → solo id > last_seen ✓

# mark-seen (R1-B3, R2-N3)
14. POST /activity-feed/mark-seen/ → response tiene previous_last_seen + last_seen_event_id (no 'marked') ✓
15. POST mark-seen → last_seen = max GLOBAL del queryset base, no del max filtrado ✓

# Permisos (R1-B2: función centralizada)
16. CLIENT_* → solo ve eventos de sus expedientes ✓
17. CLIENT_* → NO ve eventos cost.registered ✓
18. AGENT_* → solo ve eventos de expedientes que operó ✓
19. CEO → ve todos los eventos ✓
20. Non-authenticated → 401 ✓

# Count endpoint (R1-M1)
21. GET /activity-feed/count/ → unread_count correcto ✓
22. 150 eventos no leídos → unread_count=99, has_more=true ✓
23. 0 eventos no leídos → unread_count=0, has_more=false ✓

# Regresión
24. EventLog.objects.create() sin campos nuevos → no explota (null=True) ✓
```

**Checklist validación manual frontend (R1-M3):**

No se escriben tests automatizados frontend en este sprint. Se valida manualmente:

```
□ Badge en header muestra count correcto
□ Badge muestra "99+" cuando has_more=true
□ Abrir panel dispara GET feed + POST mark-seen
□ Badge se resetea a 0 después de abrir panel
□ Items con id > lastSeenEventId previo muestran highlight unread (R3-N9)
□ Después de POST mark-seen, todos los items pasan a read (sin highlight) (R3-N9)
□ Sidebar CEO muestra todos los items
□ Sidebar CLIENT_* muestra solo portal
□ Sidebar AGENT_* muestra solo operaciones
□ Polling se pausa en tab inactiva
□ Panel responsive en mobile
```

**Si la validación manual falla, AG-03 corrige antes del gate.** Tests frontend automatizados se evalúan para un sprint futuro de testing infra.

**Criterio de done:**
- [ ] 24 tests backend verdes
- [ ] 11 checks de validación manual frontend pasados
- [ ] Tests de seguridad (AGENT_*, CLIENT_* filtrado) explícitos (R1-B2)
- [ ] Tests de count con fixture de volumen (150+ eventos) (R1-M1)
- [ ] Tests de mark-seen verifican que avanza al max global, no filtrado (R1-B3)

---

## Seguridad (ref → ENT_PLAT_SEGURIDAD)

| Aspecto | Evaluación | Acción |
|---------|-----------|--------|
| Superficie de ataque | Feed expone metadata de actividad | payload no se serializa. user_display no expone email (R1-M2). |
| Permisos centralizados | get_visible_events() | CEO todo, AGENT_* operados, CLIENT_* subsidiary + excluir CEO-ONLY (R1-B2). |
| mark_seen | POST separado sin filtros | En operación normal evita marcar resultados filtrados/no visibles. En concurrencia GET+POST de MVP, puede marcar como visto un evento no renderizado (R3-N8). |
| Polling abuse | Bajo | Rate limit estándar. Count usa slice [:100] (R1-M1). |
| Data leakage | Controlado | payload no serializado. Email nunca en user_display. |

**Sin nuevos canales de acceso externo.** No amplía superficie de ataque.

---

## Gate Sprint 21

- [ ] EventLog tiene user, proforma, action_source, previous_status, new_status (todos null=True)
- [ ] action_source usa contrato normalizado (R1-B1)
- [ ] UserNotificationState funcional (high-water mark)
- [ ] GET /activity-feed/ con filtrado, paginación
- [ ] POST /activity-feed/mark-seen/ avanza al max del queryset base sin filtros (R1-B3)
- [ ] GET /activity-feed/count/ con slice [:100] real (R1-M1)
- [ ] Permisos vía get_visible_events() en los 3 endpoints (R1-B2)
- [ ] CEO detectado por role='CEO' con is_superuser como fallback (R2-N1)
- [ ] CLIENT_* NO ve eventos CEO-ONLY
- [ ] AGENT_* solo ve expedientes donde ha operado (EventLog con user=agent) (R2-N2)
- [ ] user_display nunca expone email (R1-M2)
- [ ] Badge en header muestra count correcto
- [ ] Sidebar filtra items según rol
- [ ] 24 tests backend verdes + 11 checks validación manual FE
- [ ] 0 regresiones en tests existentes

---

## Excluido explícitamente

- **Página dedicada /dashboard/activity** → futuro.
- **WebSocket/realtime** → nunca para MVP.
- **Notificaciones email** → S26.
- **Tests frontend automatizados** → sprint futuro de testing infra.
- **EventLog cleanup/archival** → futuro.

---

## Dependencias internas

```
S21-01 (extender EventLog) → S21-03 (feed endpoint)
S21-01 (extender EventLog) → S21-04 (count endpoint)
S21-02 (UserNotificationState) → S21-03 (mark-seen)
S21-02 (UserNotificationState) → S21-04 (count high-water mark)
S21-03 + S21-04 → S21-05 (frontend)
S21-06 (sidebar) → paralelo con todo
S21-07 (tests + validación) → después de todo

Orden sugerido:
  AG-02 Día 1: S21-01 (EventLog + actualizar dispatcher) + activity_permissions.py
  AG-02 Día 2: S21-02 (UserNotificationState) + S21-04 (count)
  AG-02 Día 3: S21-03 (feed + mark-seen)
  AG-03 Día 1-2: S21-06 (sidebar — paralelo)
  AG-03 Día 3-4: S21-05 (badge + panel)
  AG-02 Día 4-5: S21-07 (tests)
  AG-03 Día 5: validación manual FE
```

---

## Notas para auditoría

1. **action_source (R1-B1, R2-N4):** Renombrado de command_id. max_length=32. Contrato cerrado — lista exhaustiva de todos los commands C1..C22, acciones de proforma, patches por estado, y system jobs. Nuevos valores requieren actualizar el contrato primero.
2. **Permisos centralizados (R1-B2, R2-N1, R2-N2):** `get_visible_events(user)` es la ÚNICA función de permisos del feed. CEO = `role='CEO'`, con `is_superuser` como fallback técnico de Django (no equivalente de negocio). AGENT_* = "ha operado" definido como "existe EventLog con user=agent para ese expediente" — no hay modelo de asignación, si se crea se actualiza esta función.
3. **mark_seen separado (R1-B3, R2-N3, R2-N5, R3-N7, R3-N8):** POST /activity-feed/mark-seen/ sin filtros. Response: `previous_last_seen` + `last_seen_event_id`. Semántica de concurrencia MVP: evento entre GET y POST puede quedar marcado sin renderizarse; NO reaparece como unread, puede aparecer en futuras cargas del feed si está en rango consultado. Tabla de seguridad alineada con esta semántica (no vende versión idealizada).
4. **Nullable real (R1-B4):** Todos los campos nuevos son `null=True`. No `default=''`. Migración instantánea en PostgreSQL.
5. **Cap real (R1-M1):** `[:100]` = `LIMIT 100` en SQL. Performance real.
6. **user_display (R1-M2):** Chain: full_name → role → "Usuario" → "Sistema". Email NUNCA.
7. **Validación FE manual (R1-M3):** 11 checks explícitos (incluyendo highlight unread pre/post mark-seen — R4-m10). Tests frontend automatizados en sprint futuro.
