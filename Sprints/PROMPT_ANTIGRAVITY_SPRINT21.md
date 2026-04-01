# PROMPT_ANTIGRAVITY_SPRINT21 — Monitor de Actividad + Role-Based Sidebar

## TU ROL
Eres AG-02 (backend developer). Ejecutás el Sprint 21 del proyecto MWT.ONE. Tu trabajo es implementar exactamente lo que dice el LOTE_SM_SPRINT21 v1.3. No diseñás, no proponés alternativas, no expandís scope. Si algo no está claro, preguntás al CEO — no adivinás.

## CONTEXTO
Sprint 21 agrega observabilidad: feed de actividad, badge de notificaciones, y sidebar filtrado por roles. El EventLog existente se extiende con 5 campos nuevos. Un modelo liviano (UserNotificationState) permite calcular "no leídos" por usuario con un high-water mark.

**Estado del código (post Sprint 20+20B DONE):**
- State machine 8 estados, 28+ commands
- Proformas como unidad operativa (ArtifactPolicy, reassign-line, change-mode)
- EventLog con: expediente FK, event_type, payload JSON, created_at
- Hook post_command_hooks en dispatcher
- Frontend policy-driven (artefactos renderizados desde bundle)

## HARD RULES

1. **State machine FROZEN.** NO tocar handlers de transición. Solo agregar campos al EventLog que ya se crea.
2. **Migración additive-only.** AddField ×5 + CreateModel ×1. Verificar con `sqlmigrate`. Si aparece AlterField o RemoveField → PARAR.
3. **Todos los campos null=True.** No default=''. No blank=True sin null=True. Backward compat absoluto.
4. **Permisos centralizados.** `get_visible_events(user)` en `activity_permissions.py`. Los 3 endpoints la llaman. NUNCA duplicar lógica de permisos inline.
5. **action_source contrato cerrado.** Solo valores del contrato: C1..C22, create_proforma, reassign_line, change_mode, patch_{estado}, system_*. Cualquier otro string es bug.
6. **payload NO se serializa.** EventLogFeedSerializer no incluye payload. Datos internos.
7. **user_display NUNCA email.** Chain: full_name → role → "Usuario" → "Sistema".
8. **mark_seen = POST separado sin filtros.** No query param de GET. Avanza al max(id) del queryset base.

## VERIFICACIÓN PREVIA (antes de escribir código)

```bash
# Verificar que Sprint 20+20B están limpios
python manage.py check
python manage.py test
python manage.py showmigrations | grep "\[ \]"  # 0 pendientes

# Verificar EventLog actual
python manage.py shell -c "from apps.expedientes.models import EventLog; print([f.name for f in EventLog._meta.get_fields()])"

# Verificar que post_command_hooks existe
grep -rn "post_command_hooks" backend/apps/expedientes/
```

## ITEMS

### FASE 0 — Modelo de datos

#### S21-01: Extender EventLog (+5 campos)

```python
# apps/expedientes/models.py — agregar a EventLog:

user = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    null=True, blank=True,
    on_delete=models.SET_NULL,
    related_name='event_logs',
)

proforma = models.ForeignKey(
    'ArtifactInstance',
    null=True, blank=True,
    on_delete=models.SET_NULL,
    limit_choices_to={'artifact_type': 'ART-02'},
    related_name='event_logs',
)

action_source = models.CharField(max_length=32, null=True, blank=True)
previous_status = models.CharField(max_length=20, null=True, blank=True)
new_status = models.CharField(max_length=20, null=True, blank=True)
```

Agregar índices:
```python
models.Index(fields=['expediente', '-id'], name='idx_eventlog_exp_id_desc'),
models.Index(fields=['proforma', '-id'], name='idx_eventlog_pf_id_desc'),
```

#### S21-02: Modelo UserNotificationState

```python
class UserNotificationState(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_state',
        primary_key=True,
    )
    last_seen_event_id = models.BigIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
```

Registrar en admin.

### FASE 1 — Permisos + Endpoints

#### Crear `services/activity_permissions.py`

```python
CEO_ONLY_EVENT_TYPES = frozenset([
    'cost.registered',
    'commission.invoiced',
    'compensation.noted',
])

def get_visible_events(user, base_qs=None):
    from apps.expedientes.models import EventLog
    qs = base_qs if base_qs is not None else EventLog.objects.all()
    qs = qs.select_related('expediente', 'proforma', 'user')
    
    user_role = getattr(user, 'role', None)
    if user_role == 'CEO' or user.is_superuser:
        return qs
    
    if hasattr(user, 'client_subsidiary') and user.client_subsidiary:
        return qs.filter(
            expediente__client_subsidiary=user.client_subsidiary
        ).exclude(event_type__in=CEO_ONLY_EVENT_TYPES)
    
    # AGENT_*: solo expedientes donde ha operado
    operated_ids = (
        EventLog.objects.filter(user=user)
        .values_list('expediente_id', flat=True).distinct()
    )
    return qs.filter(expediente_id__in=operated_ids)
```

#### S21-03: GET /api/activity-feed/

ListAPIView con paginación. Filtros: expediente, proforma, event_type, unread_only. Usa `get_visible_events(request.user)`.

Serializer:
```python
class EventLogFeedSerializer(serializers.ModelSerializer):
    expediente_number = serializers.CharField(source='expediente.expediente_number', read_only=True)
    proforma_number = serializers.SerializerMethodField()
    user_display = serializers.SerializerMethodField()
    
    class Meta:
        model = EventLog
        fields = ['id', 'event_type', 'action_source', 'previous_status', 'new_status',
                  'expediente_id', 'expediente_number', 'proforma_id', 'proforma_number',
                  'user_id', 'user_display', 'created_at']
    
    def get_proforma_number(self, obj):
        if obj.proforma and obj.proforma.payload:
            return obj.proforma.payload.get('proforma_number', '')
        return ''
    
    def get_user_display(self, obj):
        if not obj.user:
            return 'Sistema'
        name = obj.user.get_full_name()
        if name and name.strip():
            return name.strip()
        role = getattr(obj.user, 'role', None)
        return role if role else 'Usuario'
```

#### S21-04: GET /api/activity-feed/count/

```python
# Cap real con slice — NO usar .count()
qs = get_visible_events(user).filter(id__gt=state.last_seen_event_id)
ids = list(qs.order_by('-id').values_list('id', flat=True)[:100])
n = len(ids)
return Response({
    'unread_count': min(n, 99),
    'has_more': n == 100,
    'last_seen_event_id': state.last_seen_event_id,
})
```

#### POST /api/activity-feed/mark-seen/

```python
# Sin filtros, sin parámetros
base_qs = get_visible_events(user).order_by('-id')
latest = base_qs.values_list('id', flat=True).first()
state, _ = UserNotificationState.objects.get_or_create(user=user)
previous = state.last_seen_event_id
if latest and latest > state.last_seen_event_id:
    state.last_seen_event_id = latest
    state.save(update_fields=['last_seen_event_id', 'updated_at'])
return Response({
    'previous_last_seen': previous,
    'last_seen_event_id': state.last_seen_event_id,
})
```

### FASE 2 — Actualizar puntos de creación de EventLog

Cada lugar que hoy hace `EventLog.objects.create(...)` necesita los campos nuevos:

```python
# En post_command_hooks — agregar:
EventLog.objects.create(
    expediente=expediente,
    event_type=event_type,
    payload=payload,
    user=getattr(request, 'user', None) if request else None,
    proforma=proforma_if_applicable,
    action_source=command_name,  # 'C1', 'C5', etc.
    previous_status=prev if status_changed else None,
    new_status=expediente.status if status_changed else None,
)
```

### FASE 3 — Tests (24)

Crear `apps/expedientes/tests/test_activity_feed.py`:

1-6: EventLog extendido (campos populados por commands, proformas, celery, backward compat)
7-9: UserNotificationState (get_or_create, mark_seen, advance)
10-13: Feed endpoint (sin filtros, por expediente, por proforma, unread_only)
14-15: mark-seen (response correcto, avanza al max global)
16-20: Permisos (CLIENT_* filtrado, no cost.registered, AGENT_* operados, CEO todo, 401)
21-23: Count (correcto, cap 99, zero)
24: Regresión backward compat

## ARCHIVOS QUE NO PODÉS TOCAR

- `apps/expedientes/services/state_machine/` handlers (FROZEN)
- `apps/expedientes/services/artifact_policy.py` (S20)
- `docker-compose.yml`
- `apps/sizing/`

## VERIFICACIÓN ANTES DE PR

```bash
python manage.py makemigrations expedientes
python manage.py sqlmigrate expedientes XXXX  # AddField ×5 + CreateModel ×1
python manage.py migrate
python manage.py test  # 24 nuevos + todos los existentes verdes

# Sanity checks
grep -rn "CEO_ONLY_EVENT_TYPES" backend/  # solo en activity_permissions.py
grep -rn "get_visible_events" backend/  # activity_permissions + 3 views
grep -rn "\.email" backend/apps/expedientes/serializers.py  # 0 en EventLogFeedSerializer
```
