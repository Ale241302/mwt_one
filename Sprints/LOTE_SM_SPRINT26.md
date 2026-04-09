# LOTE_SM_SPRINT26 — Notificaciones Email + Cobranza + Admin Templates
id: LOTE_SM_SPRINT26
version: 2.3
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
status: DRAFT — Auditado R13 8.9/10. Pendiente aprobación CEO.
stamp: DRAFT v2.3 — 2026-04-08
tipo: Lote ruteado (ref → PLB_ORCHESTRATOR §E)
sprint: 26
priority: P1
depends_on: LOTE_SM_SPRINT21 (DONE — EventLog extendido + activity feed + sidebar),
            LOTE_SM_SPRINT24 (DONE — seguridad B2B + knowledge pipeline),
            LOTE_SM_SPRINT25 (DONE — payment status machine + deferred price + parent/child, 59 tests)
refs: ENT_OPS_STATE_MACHINE (FROZEN v1.2.2),
      ROADMAP_EXTENDIDO_POST_DIRECTRIZ (VIGENTE — S21 emails scope + S26 permisos),
      ENT_PLAT_CANALES_CLIENTE (DRAFT v1.1),
      PLB_INTERACCION_CLIENTE (LOC templates)
blocker_ceo: CEO-28 (email provider: SMTP/SendGrid/SES + contact_email en ClientSubsidiary)

changelog:
  - v1.0 (2026-04-08): Compilación inicial. 18 items en 4 fases.
  - v1.1 (2026-04-08): Fixes R1 (8.4/10 — 2B + 5M + 3N). Idempotencia via event_log FK. resolve_collection_recipient por proforma del pago. Semánticas trigger_action_source vs template_key separadas. Kill switch crea log 'disabled'. refresh_from_db en cron. test-send requiere sample_expediente_id. Dedup 1h en send-proforma.
  - v1.2 (2026-04-08): Fixes R2 (8.8/10 — 2B + 4M + 2N). B1: UniqueConstraint condicional para templates default (brand=null). B2: idempotencia real pre-envío via get_or_create atómico + status 'pending'. M1: +precondición FK proforma en ExpedientePago. M2: +2 seeds (10 total). M3: kill switch cobranza = logger only. M4: override_used eliminado. N1: conteo 52. N2: dependencias explícitas.
  - v1.3 (2026-04-08): Fixes R3 (8.9/10 — 1B + 2M + 2N). B1: recuperación pending huérfanos. M1: introspección _meta.get_fields(). M2: cobranza con get_or_create atómico. N1: DELETE = desactivar + restore. N2: created_at + completed_at.
  - v1.4 (2026-04-08): Fixes R4 (8.7/10 — 2B + 2M). Advisory lock reemplaza pending. finalize_log centralizado. CollectionEmailLog +completed_at.
  - v1.5 (2026-04-08): Fixes R5 (8.9/10 — 2B + 2M). sha256 lock key. At-least-once con send fuera de tx. Limpieza restos pending. CollectionEmailLog.sent_at → created_at.
  - v1.6 (2026-04-08): Fixes R6 (9.1/10 — 1B + 2M + 1N). Kill switch con advisory lock. Narrativa at-least-once explícita. SES ref eliminada.
  - v1.7 (2026-04-08): Fixes R7 (8.9/10 — 1B + 2M). Status-aware dedup. Transient retry real. Limpieza documental.
  - v1.8 (2026-04-08): Fixes R8. +NotificationAttempt/NotificationLog two-model. exhausted status. Manual try/except.
  - v1.9 (2026-04-08): Fixes R9. SendResult enum. Enforcement delete(). correlation_id + proforma en Attempt.
  - v2.0 (2026-04-08): Fixes R10. SendResult branching en E1. correlation_id + proforma en bases. on_failure eliminado. CollectionEmailLog enforcement.
  - v2.1 (2026-04-08): Fixes R11. Cobranza SendResult. Render try/except. save() enforcement. Limpieza títulos.
  - v2.2 (2026-04-08): Fixes R12. backend.send() try/except catch-all. Conteo 63. ImmutableManager.
  - v2.3 (2026-04-08): Fixes R13 (8.9/10 — 1B + 2M). B1: Task custom con on_failure() para persistir Log(exhausted) cuando retries se agotan — elimina dependencia de MaxRetriesExceededError inline. RETRYABLE usa autoretry_for + throw=False pattern. M1: attempt_count calculado por correlation_id en TODAS las rutas terminales (render error, backend exception, unknown SendResult). M2: unknown SendResult → audit trail (Attempt+Log exhausted) en vez de RuntimeError.

---

## Objetivo

Sistema completo de notificaciones email transaccionales para la plataforma B2B: emails automáticos por cambio de estado, cobranza de pagos vencidos con cron, templates editables por CEO, envío de proformas por email (Flujo C), y frontend admin para gestión de templates + historial de envíos.

**Contexto:** El roadmap original (ROADMAP_EXTENDIDO) planificó emails en S21 y admin templates en S26. El S21 real se ejecutó como "Monitor de Actividad + Role-Based Sidebar" sin la parte de emails. Este sprint absorbe ambos scopes.

---

## A. Decisiones CEO requeridas

| ID | Decisión | Impacto | Default si no se decide |
|----|----------|---------|------------------------|
| DEC-S26-01 | Email provider: SMTP genérico / SendGrid / Amazon SES | Configura backend de envío. SES recomendado por costo ($0.10/1K emails) y ya tenemos AWS. | No ejecutar sprint — es bloqueante |
| DEC-S26-02 | contact_email obligatorio en ClientSubsidiary | Si no hay email, ¿bloquear creación o permitir sin notificaciones? | Nullable — skip notificación si null, log warning |
| DEC-S26-03 | ¿Cuáles transiciones disparan email al cliente? (CEO-16) | Determina el mapeo command→template | Default: C1 (registro), producción, despacho, entrega, pago verificado/rechazado/liberado, pago vencido |
| DEC-S26-04 | Gracia de cobranza: ¿usar payment_grace_days de ClientSubsidiary o un default global? | Cron de cobranza. ClientSubsidiary ya tiene el campo (S17). | Usar payment_grace_days; default 30 si null |
| DEC-S26-05 | ¿Email de cobranza a MWT o al cliente cuando operado_por=MWT (Mode C)? | Quién recibe el email de pago vencido | CEO recibe si Mode C; cliente recibe si Mode B |

---

## B. Estado asumido y precondiciones verificadas (pre-sprint)

### B1. Componentes existentes

| Componente | Estado | Sprint |
|-----------|--------|--------|
| EventLog extendido (user, proforma, action_source, previous/new status) | ✅ Operativo | S21 |
| Activity feed (feed + count + mark-seen) | ✅ Operativo | S21 |
| get_visible_events(user) permisos centralizados | ✅ Operativo | S21 |
| post_command_hooks en dispatcher | ✅ Operativo | S18 |
| JWT rotation + rate limiting + signed URLs | ✅ Operativo | S24 |
| payment_grace_days en ClientSubsidiary | ✅ Existe campo | S17 |
| Celery + Redis operativos | ✅ Operativo | S1+ |
| Celery Beat configurado | ✅ Operativo | S1+ |
| Payment status machine (pending→verified→credit_released) | ✅ DONE (59 tests, Resumen_sprint25) | S25 |

### B2. Precondiciones a verificar en Fase 0

| Campo | Modelo | Existe? | Si no existe | Item |
|-------|--------|---------|-------------|------|
| contact_email | ClientSubsidiary | **Verificar** | Crear migración aditiva (C4) | S26-02 |
| preferred_language | ClientSubsidiary | **Verificar** | Si no existe, usar default 'es' y documentar | S26-02 |
| proforma (FK a ArtifactInstance) | ExpedientePago | **Verificar** | Crear migración aditiva nullable (fix M1 R2) | S26-02b |

**S26-02 y S26-02b verifican estos campos como paso obligatorio antes de continuar Fase 1.**

### B3. Dependencias de paquetes (fix N2 R2)

| Paquete | Archivo | Entorno | Notas |
|---------|---------|---------|-------|
| `Jinja2` | requirements/base.txt | Producción | SandboxedEnvironment para templates |
| `moto[ses]` | requirements/test.txt | Solo tests | Mock SES para test S26-04 |

**Verificar si ya están instalados. Si no, agregar antes de Fase 1.**

---

## C. Modelos

### C1. NotificationTemplate

```python
class NotificationTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)  # Título administrativo para UI: "Registro de expediente"
    template_key = models.CharField(max_length=50, db_index=True)
        # Clave de resolución: 'expediente.registered', 'payment.verified', etc.
        # NO es action_source — ver F1 para el mapeo trigger→template_key.
    subject_template = models.TextField()  # Jinja2
    body_template = models.TextField()  # Jinja2 — plain text, not HTML for MVP
    is_active = models.BooleanField(default=True)
    brand = models.ForeignKey('brands.Brand', null=True, blank=True, on_delete=models.SET_NULL,
                              related_name='notification_templates')
    # brand=null → default template. brand=X → override per brand.
    language = models.CharField(max_length=5, default='es')  # ISO 639-1 + optional region
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)

    class Meta:
        constraints = [
            # Fix B1 R2: UniqueConstraint condicional para brand=null.
            # En PostgreSQL, NULL != NULL rompe unique_together cuando brand=null.
            # Dos constraints separadas garantizan unicidad correcta.
            models.UniqueConstraint(
                fields=['template_key', 'language'],
                condition=models.Q(brand__isnull=True),
                name='uniq_default_template_per_key_lang'
            ),
            models.UniqueConstraint(
                fields=['template_key', 'brand', 'language'],
                condition=models.Q(brand__isnull=False),
                name='uniq_brand_template_per_key_lang'
            ),
        ]
```

**Resolución de template:** `resolve_template(template_key, brand, language)`:
1. Busca `(template_key, brand, lang)` → si existe y `is_active`, retorna.
2. Fallback `(template_key, brand=null, lang)` → si existe y `is_active`, retorna.
3. Fallback `(template_key, brand=null, 'es')` → si existe y `is_active`, retorna.
4. Si no encuentra → retorna None. Log error, no crash.

Cada paso usa `.filter(...).first()` — nunca `.get()` — para evitar `MultipleObjectsReturned` (defensa en profundidad aunque la constraint lo prevenga).

**Política soft delete:** `is_active=False` funciona como soft delete. No `deleted_at`. Queries de resolución filtran `is_active=True`.

### C2a. NotificationAttempt (NUEVO — fix M1 R8, M1+M2 R9)

```python
class NotificationAttempt(models.Model):
    """Registro inmutable de cada intento de envío. Append-only. 1..N por evento."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    correlation_id = models.UUIDField(db_index=True)
        # Fix M2 R9: agrupa attempts con su log terminal.
        # event_log_id si existe, UUID generado por task si no.
    event_log = models.ForeignKey('audit.EventLog', null=True, blank=True, on_delete=models.SET_NULL)
    expediente = models.ForeignKey('expedientes.Expediente', null=True, on_delete=models.SET_NULL)
    proforma = models.ForeignKey('expedientes.ArtifactInstance', null=True, blank=True,
                                 on_delete=models.SET_NULL)  # Fix M2 R9
    recipient_email = models.EmailField()
    template_key = models.CharField(max_length=50, blank=True, default='')
    trigger_action_source = models.CharField(max_length=32, blank=True, default='')
    status = models.CharField(max_length=20, choices=[
        ('sent', 'Sent'), ('failed', 'Failed'), ('skipped', 'Skipped'), ('disabled', 'Disabled'),
    ])
    error = models.TextField(blank=True, default='')
    attempted_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        indexes = [models.Index(fields=['event_log', '-attempted_at']),
                   models.Index(fields=['correlation_id'])]

    def delete(self, *args, **kwargs):
        raise PermissionError("NotificationAttempt is append-only. Cannot delete.")

    def save(self, *args, **kwargs):
        if self.pk and NotificationAttempt.objects.filter(pk=self.pk).exists():
            raise PermissionError("NotificationAttempt is append-only. Cannot update.")
        super().save(*args, **kwargs)
```

**Enforcement (fix M1 R9):** `delete()` raises. `save()` blocks updates on existing records. Admin: `readonly_fields = '__all__'`, `has_delete_permission = False`.

**Operational rule (fix M2 R12):** `QuerySet.update()` and `QuerySet.delete()` are PROHIBITED on NotificationAttempt, NotificationLog, and CollectionEmailLog. Enforcement: custom `ImmutableManager` that overrides `update()` and `delete()` to raise `PermissionError`. Direct SQL bypass is the only escape hatch (requires DBA approval).

```python
class ImmutableQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise PermissionError("Bulk update prohibited on immutable audit trail model.")
    def delete(self):
        raise PermissionError("Bulk delete prohibited on immutable audit trail model.")

class ImmutableManager(models.Manager):
    def get_queryset(self):
        return ImmutableQuerySet(self.model, using=self._db)
```

All three models use `objects = ImmutableManager()` as default manager.

### C2b. NotificationLog (resultado final consolidado — fix M1+M2 R9)

```python
class NotificationLog(models.Model):
    """Registro final único por evento+recipient. Se crea UNA vez con resultado terminal."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    correlation_id = models.UUIDField(db_index=True)  # Fix M2 R9: same as attempts
    template = models.ForeignKey(NotificationTemplate, null=True, on_delete=models.SET_NULL)
    event_log = models.ForeignKey('audit.EventLog', null=True, blank=True, on_delete=models.SET_NULL)
    expediente = models.ForeignKey('expedientes.Expediente', null=True, on_delete=models.SET_NULL)
    proforma = models.ForeignKey('expedientes.ArtifactInstance', null=True, blank=True, on_delete=models.SET_NULL)
    recipient_email = models.EmailField()
    subject = models.TextField(default='')
    body_preview = models.TextField(max_length=500, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('sent', 'Sent'),
        ('skipped', 'Skipped'),
        ('disabled', 'Disabled'),
        ('exhausted', 'Exhausted'),
    ])
    error = models.TextField(blank=True, default='')
    trigger_action_source = models.CharField(max_length=32, blank=True, default='')
    template_key = models.CharField(max_length=50, blank=True, default='')
    attempt_count = models.IntegerField(default=1)
    class Meta:
        indexes = [
            models.Index(fields=['expediente', '-created_at']),
            models.Index(fields=['recipient_email', '-created_at']),
            models.Index(fields=['correlation_id']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['event_log', 'recipient_email'],
                condition=models.Q(event_log__isnull=False),
                name='uniq_notification_per_event_recipient'
            )
        ]

    def delete(self, *args, **kwargs):
        raise PermissionError("NotificationLog is immutable. Cannot delete.")

    def save(self, *args, **kwargs):
        if self.pk and NotificationLog.objects.filter(pk=self.pk).exists():
            raise PermissionError("NotificationLog is immutable. Cannot update.")
        super().save(*args, **kwargs)
```

**Enforcement (fix M1 R9+R11):** `delete()` and `save()` both raise on existing records. Admin: all fields read-only, no delete permission.
**Correlation (fix M2 R9):** `correlation_id` links Log ↔ Attempts. For event-triggered: `correlation_id = event_log_id`. For manual: `correlation_id = uuid4()` generated by task at start.

### C3. CollectionEmailLog

```python
class CollectionEmailLog(models.Model):
    """Audit trail para emails de cobranza automatica. Inmutable."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    expediente = models.ForeignKey('expedientes.Expediente', on_delete=models.CASCADE)
    proforma = models.ForeignKey('expedientes.ArtifactInstance', null=True, blank=True,
                                 on_delete=models.SET_NULL)
    pago = models.ForeignKey('expedientes.ExpedientePago', null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)  # Fix M2 R5: aligned with NotificationLog
    grace_days_used = models.IntegerField()
    amount_overdue = models.DecimalField(max_digits=12, decimal_places=2)
    recipient_email = models.EmailField()
    status = models.CharField(max_length=20, choices=[
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ])
    completed_at = models.DateTimeField(null=True, blank=True)
    error = models.TextField(blank=True, default='')

    def delete(self, *args, **kwargs):
        raise PermissionError("CollectionEmailLog is immutable. Cannot delete.")

    def save(self, *args, **kwargs):
        if self.pk and CollectionEmailLog.objects.filter(pk=self.pk).exists():
            raise PermissionError("CollectionEmailLog is immutable. Cannot update.")
        super().save(*args, **kwargs)
```

**Enforcement (fix M1 R11):** `delete()` and `save()` both raise on existing records. Admin: read-only + no delete. Homogéneo con NotificationAttempt y NotificationLog.

### C4. Campo contact_email en ClientSubsidiary

Verificar si ya existe (S26-02). Si no:

```python
contact_email = models.EmailField(null=True, blank=True,
                                   help_text="Email de contacto para notificaciones. Si null, se salta notificación.")
```

### C5. FK proforma en ExpedientePago (fix M1 R2)

Verificar si ya existe (S26-02b). Si no:

```python
proforma = models.ForeignKey('expedientes.ArtifactInstance', null=True, blank=True,
                              on_delete=models.SET_NULL, related_name='payments',
                              limit_choices_to={'artifact_type': 'ART-02'})
```

**Si el FK no existe y no se puede agregar (por decisión de diseño), la alternativa es:** resolve_collection_recipient cae a Mode B por defecto para pagos sin proforma FK, cobrando al cliente. Documentar esta decisión explícitamente.

---

## D. Email backend abstracto

### D1. Capa de abstracción (fix B1 R9: SendResult enum)

```python
# apps/notifications/backends.py
from abc import ABC, abstractmethod
from enum import Enum
import smtplib, botocore

class SendResult(Enum):
    SENT = "sent"                    # provider accepted
    RETRYABLE = "retryable"          # transient — retry
    PERMANENT = "permanent"          # bad address, blocked — don't retry

class EmailBackend(ABC):
    @abstractmethod
    def send(self, to: str, subject: str, body: str, from_email: str = None) -> SendResult: ...

class SMTPBackend(EmailBackend):
    def send(self, to, subject, body, from_email=None):
        try:
            count = send_mail(subject, body, from_email or settings.DEFAULT_FROM_EMAIL, [to])
            return SendResult.SENT if count == 1 else SendResult.PERMANENT
        except smtplib.SMTPRecipientsRefused:
            return SendResult.PERMANENT
        except (smtplib.SMTPException, ConnectionError, TimeoutError):
            return SendResult.RETRYABLE

class SESBackend(EmailBackend):
    def send(self, to, subject, body, from_email=None):
        try:
            client = boto3.client('ses', region_name=settings.AWS_SES_REGION)
            client.send_email(
                Source=from_email or settings.DEFAULT_FROM_EMAIL,
                Destination={'ToAddresses': [to]},
                Message={
                    'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                    'Body': {'Text': {'Data': body, 'Charset': 'UTF-8'}}
                }
            )
            return SendResult.SENT
        except client.exceptions.MessageRejected:
            return SendResult.PERMANENT
        except (botocore.exceptions.ClientError, ConnectionError):
            return SendResult.RETRYABLE

def get_email_backend() -> EmailBackend:
    return import_string(settings.MWT_EMAIL_BACKEND)()
```

**Contrato cerrado (fix B1 R9):** backend devuelve SENT/RETRYABLE/PERMANENT. Task decide retry vs exhausted sin interpretar bool ni depender de excepciones no tipadas.

### D2. Settings requeridos

```python
# settings/base.py — agregar
MWT_EMAIL_BACKEND = env('MWT_EMAIL_BACKEND', default='apps.notifications.backends.SMTPBackend')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='notificaciones@mwt.one')
MWT_NOTIFICATION_ENABLED = env.bool('MWT_NOTIFICATION_ENABLED', default=False)
CEO_EMAIL = env('CEO_EMAIL', default='')
PORTAL_BASE_URL = env('PORTAL_BASE_URL', default='https://portal.mwt.one')
AWS_SES_REGION = env('AWS_SES_REGION', default='us-east-1')
```

**Kill switch comportamiento definido (fix M3 R2):**
- **Notificaciones transaccionales (send_notification):** MWT_NOTIFICATION_ENABLED=False → crea NotificationLog status='disabled' → return. Deja evidencia persistente.
- **Cobranza (check_overdue_payments):** MWT_NOTIFICATION_ENABLED=False → logger.info → return. **NO crea CollectionEmailLog.** Razón: CollectionEmailLog solo registra intentos reales de envío; log de sistema es suficiente para auditar que el cron corrió pero estaba deshabilitado.

---

## E. Celery tasks

### E1. send_notification (v2.1: SendResult + attempt/log + advisory lock)

```python
from jinja2.sandbox import SandboxedEnvironment
from django.db import transaction, connection
from celery import Task
import hashlib, struct

def _stable_lock_key(value: str) -> int:
    digest = hashlib.sha256(value.encode("utf-8")).digest()
    return struct.unpack(">q", digest[:8])[0]

def _advisory_lock_for_event(event_log_id, recipient_email):
    lock_key = _stable_lock_key(f"notif:{event_log_id}:{recipient_email}")
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(%s)", [lock_key])


class RetryableEmailError(Exception):
    """Raised when backend returns RETRYABLE. Celery will retry this."""
    pass


class SendNotificationTask(Task):
    """
    Custom Task with on_failure callback (fix B1 R13).
    When all retries are exhausted, on_failure persists Log(exhausted).
    This is the canonical Celery pattern — no MaxRetriesExceededError needed.
    """
    max_retries = 3
    default_retry_delay = 60

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called by Celery after all retries are exhausted."""
        event_log_id = kwargs.get('event_log_id')
        expediente_id = kwargs.get('expediente_id')
        template_key = kwargs.get('template_key', '')
        trigger_action_source = kwargs.get('trigger_action_source', '')
        proforma_id = kwargs.get('proforma_id')
        recipient = kwargs.get('_recipient', 'N/A')  # stashed by run()
        correlation_id = kwargs.get('_correlation_id')

        try:
            expediente = Expediente.objects.get(pk=expediente_id)
        except Expediente.DoesNotExist:
            return

        log_base = {
            'correlation_id': correlation_id,
            'event_log_id': event_log_id,
            'expediente': expediente,
            'proforma_id': proforma_id,
            'recipient_email': recipient,
            'template_key': template_key,
            'trigger_action_source': trigger_action_source,
        }

        act = NotificationAttempt.objects.filter(correlation_id=correlation_id).count()
        _persist_terminal(event_log_id, recipient, log_base, 'exhausted',
                          'N/A', f'All retries exhausted: {str(exc)[:400]}',
                          error=f'Exhausted after {act} attempts: {str(exc)[:300]}',
                          attempt_count=act)


@shared_task(bind=True, base=SendNotificationTask,
             autoretry_for=(RetryableEmailError,),
             retry_kwargs={'max_retries': 3},
             default_retry_delay=60)
def send_notification(self, template_key, expediente_id,
                      proforma_id=None, event_log_id=None,
                      trigger_action_source='', extra_context=None,
                      _recipient=None, _correlation_id=None):
    try:
        expediente = Expediente.objects.select_related(
            'client_subsidiary', 'client_subsidiary__client', 'brand'
        ).get(pk=expediente_id)
    except Expediente.DoesNotExist:
        return

    brand = expediente.brand
    language = getattr(expediente.client_subsidiary, 'preferred_language', None) or 'es'
    recipient = resolve_notification_recipient(expediente, proforma_id)

    # Fix B1 R13: correlation_id generated once, stashed in kwargs for on_failure
    if not _correlation_id:
        correlation_id = uuid.UUID(event_log_id) if event_log_id else uuid.uuid4()
        # Stash for on_failure callback access
        self.request.kwargs['_correlation_id'] = str(correlation_id)
        self.request.kwargs['_recipient'] = recipient or 'N/A'
    else:
        correlation_id = uuid.UUID(_correlation_id) if isinstance(_correlation_id, str) else _correlation_id

    attempt_base = {
        'correlation_id': correlation_id,
        'event_log_id': event_log_id,
        'expediente': expediente,
        'proforma_id': proforma_id,  # Fix B2 R10
        'recipient_email': recipient or 'N/A',
        'template_key': template_key,
        'trigger_action_source': trigger_action_source,
    }
    log_base = {**attempt_base}

    # --- Kill switch ---
    if not settings.MWT_NOTIFICATION_ENABLED:
        if event_log_id:
            with transaction.atomic():
                _advisory_lock_for_event(event_log_id, recipient or 'N/A')
                if NotificationLog.objects.filter(
                    event_log_id=event_log_id, recipient_email=recipient or 'N/A',
                ).exists():
                    return
                _create_terminal(log_base, 'disabled', '[DISABLED]',
                                 f'Kill switch off. template_key={template_key}')
        else:
            _create_terminal(log_base, 'disabled', '[DISABLED]',
                             f'Kill switch off. template_key={template_key}')
        NotificationAttempt.objects.create(**attempt_base, status='disabled')
        return

    # --- Dedup check (event-triggered only) ---
    if event_log_id:
        already_terminal = NotificationLog.objects.filter(
            event_log_id=event_log_id, recipient_email=recipient or 'N/A',
        ).exists()
        if already_terminal:
            return

    # --- Resolve template + recipient ---
    template = resolve_template(template_key, brand, language)
    if not template:
        NotificationAttempt.objects.create(**attempt_base, status='skipped', error='Template not found')
        if event_log_id:
            with transaction.atomic():
                _advisory_lock_for_event(event_log_id, recipient or 'N/A')
                if not NotificationLog.objects.filter(event_log_id=event_log_id, recipient_email=recipient or 'N/A').exists():
                    _create_terminal(log_base, 'skipped', 'N/A', f'Template not found: {template_key}')
        else:
            _create_terminal(log_base, 'skipped', 'N/A', f'Template not found: {template_key}')
        return

    if not recipient or recipient == 'N/A':
        NotificationAttempt.objects.create(**attempt_base, status='skipped', error='No contact_email')
        if event_log_id:
            with transaction.atomic():
                _advisory_lock_for_event(event_log_id, recipient or 'N/A')
                if not NotificationLog.objects.filter(event_log_id=event_log_id, recipient_email=recipient or 'N/A').exists():
                    _create_terminal(log_base, 'skipped', 'N/A', 'No contact_email configured')
        else:
            _create_terminal(log_base, 'skipped', 'N/A', 'No contact_email configured')
        return

    # --- Render (fix B2 R11: protected against invalid templates) ---
    try:
        context = build_notification_context(expediente, proforma_id, extra_context)
        env = SandboxedEnvironment()
        subject = env.from_string(template.subject_template).render(context)
        body = env.from_string(template.body_template).render(context)
    except Exception as exc:
        render_error = f'Render error: {str(exc)[:400]}'
        NotificationAttempt.objects.create(**attempt_base, status='failed', error=render_error)
        act = NotificationAttempt.objects.filter(correlation_id=correlation_id).count()
        _persist_terminal(event_log_id, recipient, log_base, 'exhausted',
                          'N/A', render_error, template=template, error=render_error, attempt_count=act)
        return

    # --- Send (OUTSIDE transaction) — SendResult branching ---
    backend = get_email_backend()
    try:
        send_result = backend.send(to=recipient, subject=subject, body=body)
    except Exception as exc:
        # Fix B1 R12: unmapped exception from backend — create audit trail before exit
        error_msg = f'Backend exception: {str(exc)[:400]}'
        NotificationAttempt.objects.create(**attempt_base, status='failed', error=error_msg)
        act = NotificationAttempt.objects.filter(correlation_id=correlation_id).count()
        _persist_terminal(event_log_id, recipient, log_base, 'exhausted',
                          subject, body[:500], template=template, error=error_msg, attempt_count=act)
        return

    if send_result is SendResult.RETRYABLE:
        # Fix B1 R13: log attempt, then raise RetryableEmailError.
        # Celery retries via autoretry. When exhausted, on_failure() persists Log(exhausted).
        NotificationAttempt.objects.create(**attempt_base, status='failed', error='Retryable failure')
        raise RetryableEmailError('Retryable email failure')
        # ↑ Celery catches this, retries up to max_retries, then calls on_failure()

    elif send_result is SendResult.PERMANENT:
        NotificationAttempt.objects.create(**attempt_base, status='failed', error='Permanent failure')
        act = NotificationAttempt.objects.filter(correlation_id=correlation_id).count()
        _persist_terminal(event_log_id, recipient, log_base, 'exhausted', subject, body[:500],
                          template=template, error='Permanent email failure', attempt_count=act)
        return

    elif send_result is SendResult.SENT:
        NotificationAttempt.objects.create(**attempt_base, status='sent')
        act = NotificationAttempt.objects.filter(correlation_id=correlation_id).count()
        _persist_terminal(event_log_id, recipient, log_base, 'sent', subject, body[:500],
                          template=template, attempt_count=act)

    else:
        # Fix M2 R13: unknown SendResult → audit trail, not RuntimeError
        error_msg = f'Unknown SendResult: {send_result}'
        NotificationAttempt.objects.create(**attempt_base, status='failed', error=error_msg)
        act = NotificationAttempt.objects.filter(correlation_id=correlation_id).count()
        _persist_terminal(event_log_id, recipient, log_base, 'exhausted', subject, body[:500],
                          template=template, error=error_msg, attempt_count=act)
        return


def _persist_terminal(event_log_id, recipient, log_base, status, subject, body_preview,
                       template=None, error='', attempt_count=1):
    """Persist NotificationLog with advisory lock if event-triggered, or directly if manual."""
    if event_log_id:
        with transaction.atomic():
            _advisory_lock_for_event(event_log_id, recipient)
            if NotificationLog.objects.filter(event_log_id=event_log_id, recipient_email=recipient).exists():
                return
            _create_terminal(log_base, status, subject, body_preview,
                             template=template, error=error, attempt_count=attempt_count)
    else:
        _create_terminal(log_base, status, subject, body_preview,
                         template=template, error=error, attempt_count=attempt_count)


def _create_terminal(log_base, status, subject, body_preview, template=None, error='', attempt_count=1):
    """Create NotificationLog with completed_at. Single point of terminal log creation."""
    NotificationLog.objects.create(
        **log_base, status=status, subject=subject, body_preview=body_preview,
        template=template, error=error, completed_at=timezone.now(), attempt_count=attempt_count,
    )
```

**Flujo resumido:**
1. Kill switch / no template / no recipient → Attempt(skipped/disabled) + Log terminal.
2. Send OK → Attempt(sent) + Log(sent) dentro de advisory lock.
3. Send transient fail → Attempt(failed) + Celery retry. NO log terminal aún.
4. Retries agotados → Attempt(failed) + Log(exhausted) dentro de advisory lock (fix B1 R8).
5. Flujos manuales (event_log=None) → try/except envuelve todo. Attempt + Log siempre (fix M2 R8).

**Semántica: AT-LEAST-ONCE entrega. Persistencia deduplicada. Audit trail completo via NotificationAttempt.**

### E2. resolve_notification_recipient (para notificaciones transaccionales)

```python
def resolve_notification_recipient(expediente, proforma_id=None):
    """
    Mode C (operado por MWT) → CEO email.
    Mode B (operado por cliente) → client_subsidiary.contact_email.
    """
    if proforma_id:
        try:
            proforma = ArtifactInstance.objects.get(pk=proforma_id)
            mode = proforma.metadata.get('mode', 'B')
        except ArtifactInstance.DoesNotExist:
            mode = 'B'
    else:
        proformas = list(expediente.proformas.values_list('metadata__mode', flat=True))
        mode = 'C' if proformas and all(m == 'C' for m in proformas) else 'B'

    if mode == 'C':
        return settings.CEO_EMAIL or None
    else:
        return getattr(expediente.client_subsidiary, 'contact_email', None)
```

### E2b. resolve_collection_recipient (para cobranza)

```python
def resolve_collection_recipient(pago):
    """
    Resuelve por proforma del pago (si FK existe), no por expediente global.
    Si pago no tiene proforma FK → Mode B por defecto (cobrar al cliente).
    """
    mode = 'B'
    proforma = getattr(pago, 'proforma', None)

    # Verificar que el FK existe en el modelo y que el objeto tiene valor
    if proforma is not None and hasattr(proforma, 'metadata') and proforma.metadata:
        mode = proforma.metadata.get('mode', 'B')

    if mode == 'C':
        return settings.CEO_EMAIL or None, proforma
    else:
        contact = getattr(pago.expediente.client_subsidiary, 'contact_email', None)
        return contact, proforma
```

### E3. check_overdue_payments (Celery Beat)

```python
@shared_task
def check_overdue_payments():
    """
    Diario 8:00 AM Costa Rica (14:00 UTC).
    Kill switch: solo logger.info, NO crea CollectionEmailLog (fix M3 R2).
    """
    if not settings.MWT_NOTIFICATION_ENABLED:
        logger.info("[COLLECTION_DISABLED] MWT_NOTIFICATION_ENABLED=False — no action taken")
        return

    today = timezone.now().date()

    # select_related includes proforma only if FK exists (fix M1 R3: introspection, not try/except)
    qs = ExpedientePago.objects.filter(
        status__in=['pending', 'verified'],
        is_active=True,
    ).select_related('expediente', 'expediente__client_subsidiary')

    pago_field_names = {f.name for f in ExpedientePago._meta.get_fields()}
    if 'proforma' in pago_field_names:
        qs = qs.select_related('proforma')

    for pago in qs:
        # Revalidar estado en caliente (fix M4 R1)
        pago.refresh_from_db(fields=['status', 'is_active'])
        if pago.status not in ['pending', 'verified'] or not pago.is_active:
            continue

        grace_days = pago.expediente.client_subsidiary.payment_grace_days or 30
        due_date = pago.fecha + timedelta(days=grace_days)

        if today <= due_date:
            continue

        # Dedup: no enviar si ya se envió en los últimos 7 días (based on completed_at, fix M2 R4)
        recent = CollectionEmailLog.objects.filter(
            pago=pago, status='sent',
            completed_at__gte=timezone.now() - timedelta(days=7)
        ).exists()
        if recent:
            continue

        recipient, proforma = resolve_collection_recipient(pago)
        if not recipient:
            logger.warning(f"[COLLECTION_SKIP] No recipient for pago={pago.pk}")
            continue

        lang = getattr(pago.expediente.client_subsidiary, 'preferred_language', None) or 'es'
        template = resolve_template('payment.overdue', pago.expediente.brand, lang)
        if not template:
            logger.warning(f"[COLLECTION_SKIP] No template for brand={pago.expediente.brand}")
            continue

        # --- Render (fix B2 R11: protected against invalid templates) ---
        try:
            context = build_notification_context(pago.expediente, extra_context={
                'pago_amount': str(pago.amount),
                'pago_fecha': pago.fecha.isoformat(),
                'days_overdue': (today - due_date).days,
                'grace_days': grace_days,
            })
            env = SandboxedEnvironment()
            subject = env.from_string(template.subject_template).render(context)
            body = env.from_string(template.body_template).render(context)
        except Exception as exc:
            try:
                CollectionEmailLog.objects.create(
                    expediente=pago.expediente, proforma=proforma, pago=pago,
                    grace_days_used=grace_days, amount_overdue=pago.amount,
                    recipient_email=recipient,
                    status='failed', error=f'Render error: {str(exc)[:400]}',
                    completed_at=timezone.now(),
                )
            except Exception:
                pass
            logger.error(f"[COLLECTION_RENDER_FAIL] pago={pago.pk}: {exc}")
            continue

        # --- Send (fix B1 R11+R12: SendResult branching + catch-all) ---
        backend = get_email_backend()
        try:
            send_result = backend.send(to=recipient, subject=subject, body=body)
        except Exception as exc:
            # Fix B1 R12: unmapped backend exception — log and continue to next pago
            try:
                CollectionEmailLog.objects.create(
                    expediente=pago.expediente, proforma=proforma, pago=pago,
                    grace_days_used=grace_days, amount_overdue=pago.amount,
                    recipient_email=recipient,
                    status='failed', error=f'Backend exception: {str(exc)[:400]}',
                    completed_at=timezone.now(),
                )
            except Exception:
                pass
            logger.error(f"[COLLECTION_BACKEND_FAIL] pago={pago.pk}: {exc}")
            continue

        if send_result is SendResult.RETRYABLE:
            # Cobranza no reintenta (cron diario lo hará mañana). Log como failed.
            status = 'failed'
            error_msg = 'Retryable failure — will retry next cron run'
        elif send_result is SendResult.PERMANENT:
            status = 'failed'
            error_msg = 'Permanent failure — recipient rejected or invalid'
        elif send_result is SendResult.SENT:
            status = 'sent'
            error_msg = ''
        else:
            status = 'failed'
            error_msg = f'Unknown SendResult: {send_result}'

        try:
            with transaction.atomic():
                lock_key = _stable_lock_key(f"collection:{pago.pk}:{recipient}")
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_advisory_xact_lock(%s)", [lock_key])

                # Re-check dedup inside lock (completed_at-based)
                recent_sent = CollectionEmailLog.objects.filter(
                    pago=pago, status='sent',
                    completed_at__gte=timezone.now() - timedelta(days=7)
                ).exists()
                if recent_sent:
                    continue

                CollectionEmailLog.objects.create(
                    expediente=pago.expediente, proforma=proforma, pago=pago,
                    grace_days_used=grace_days, amount_overdue=pago.amount,
                    recipient_email=recipient,
                    status=status, error=error_msg,
                    completed_at=timezone.now(),
                )
        except Exception as exc:
            try:
                CollectionEmailLog.objects.create(
                    expediente=pago.expediente, proforma=proforma, pago=pago,
                    grace_days_used=grace_days, amount_overdue=pago.amount,
                    recipient_email=recipient,
                    status='failed', error=str(exc)[:500],
                    completed_at=timezone.now(),
                )
            except Exception:
                pass
            logger.error(f"[COLLECTION_FAIL] pago={pago.pk}: {exc}")
```

### E4. Celery Beat schedule

```python
'check-overdue-payments': {
    'task': 'apps.notifications.tasks.check_overdue_payments',
    'schedule': crontab(hour=14, minute=0),  # 8:00 AM Costa Rica (UTC-6)
},
```

---

## F. Hook en dispatcher

### F1. Mapeo trigger → template_key

```python
# apps/notifications/mappings.py

TRIGGER_TO_TEMPLATE = {
    # action_source (EventLog)  → template_key (NotificationTemplate)
    'C1':                        'expediente.registered',
    'C5':                        'expediente.production_started',
    'C11':                       'expediente.dispatched',
    'C13':                       'expediente.in_transit',
    'C15':                       'expediente.delivered',
    'verify_payment':            'payment.verified',
    'reject_payment':            'payment.rejected',
    'release_credit':            'payment.credit_released',
    # Cobranza (payment.overdue) se maneja via cron, no via hook.
    # proforma.sent se maneja via endpoint manual H3, no via hook.
}
```

### F2. Hook post-command

```python
def notify_on_command(expediente_id, command_name, proforma_id=None,
                      event_log_id=None, **kwargs):
    template_key = TRIGGER_TO_TEMPLATE.get(command_name)
    if template_key:
        send_notification.delay(
            template_key=template_key,
            expediente_id=str(expediente_id),
            proforma_id=str(proforma_id) if proforma_id else None,
            event_log_id=str(event_log_id) if event_log_id else None,
            trigger_action_source=command_name,
            extra_context=kwargs.get('extra_context', {})
        )
```

**Integración:** Agregar `notify_on_command` a `post_command_hooks`. El dispatcher DEBE pasar `event_log_id` — EventLog se crea antes de hooks (S21). Si hook falla, NO revierte command.

---

## G. Templates seed (data migration)

### G1. 10 templates iniciales (fix M2 R2: +2 seeds para paridad con TRIGGER_TO_TEMPLATE)

| # | template_key | subject (Jinja2) | Trigger |
|---|-------------|-------------------|---------|
| 1 | expediente.registered | Expediente {{ expediente_code }} registrado | C1 |
| 2 | expediente.production_started | Producción iniciada — {{ expediente_code }} | C5 |
| 3 | expediente.dispatched | Despacho confirmado — {{ expediente_code }} | C11 |
| 4 | expediente.in_transit | En tránsito — {{ expediente_code }} | C13 |
| 5 | expediente.delivered | Entrega confirmada — {{ expediente_code }} | C15 |
| 6 | payment.verified | Pago verificado — {{ expediente_code }} | verify_payment |
| 7 | payment.rejected | Pago rechazado — {{ expediente_code }} | reject_payment |
| 8 | payment.credit_released | Crédito liberado — {{ expediente_code }} | release_credit |
| 9 | payment.overdue | Pago vencido — {{ expediente_code }} | Cron cobranza |
| 10 | proforma.sent | Proforma {{ proforma_number }} — {{ brand_name }} | Manual H3 |

Todos en idioma='es', brand=null (defaults). CEO puede crear overrides por brand/idioma.

Body: plain text con Jinja2. Incluyen: saludo, info evento, link portal, firma MWT. **NO HTML para MVP.**

### G2. Variables disponibles en contexto

```python
def build_notification_context(expediente, proforma_id=None, extra_context=None):
    ctx = {
        'expediente_code': expediente.code,
        'client_name': expediente.client_subsidiary.client.name,
        'subsidiary_name': expediente.client_subsidiary.name,
        'brand_name': expediente.brand.name if expediente.brand else 'N/A',
        'current_status': expediente.status,
        'portal_url': f"{settings.PORTAL_BASE_URL}/expedientes/{expediente.pk}",
        'mwt_signature': 'Muito Work Limitada — Gestión Comercial B2B',
    }
    if proforma_id:
        try:
            proforma = ArtifactInstance.objects.get(pk=proforma_id)
            ctx['proforma_number'] = proforma.metadata.get('number', 'N/A')
            ctx['proforma_mode'] = proforma.metadata.get('mode', 'N/A')
        except ArtifactInstance.DoesNotExist:
            pass
    if extra_context:
        ctx.update(extra_context)
    return ctx
```

---

## H. API endpoints

### H1. Templates CRUD (CEO-only)

| Método | Endpoint | Permiso | Descripción |
|--------|----------|---------|-------------|
| GET | /api/notifications/templates/ | CEO | Lista templates |
| POST | /api/notifications/templates/ | CEO | Crear template |
| GET | /api/notifications/templates/{id}/ | CEO | Detalle |
| PATCH | /api/notifications/templates/{id}/ | CEO | Editar (subject, body, is_active) |
| DELETE | /api/notifications/templates/{id}/ | CEO | **Desactivar** (is_active=False) — NO borra. Reactivable. |
| POST | /api/notifications/templates/{id}/restore/ | CEO | Reactivar template desactivado (is_active=True) |
| POST | /api/notifications/templates/{id}/test-send/ | CEO | Email de prueba |

**DELETE = desactivar, no borrar (fix N1 R3).** El template queda en DB con is_active=False. No se puede crear otro con la misma combinación template_key/brand/language mientras exista el desactivado — hay que reactivarlo via /restore/. TemplatesTable en frontend muestra inactivos en gris con botón "Restaurar".

**test-send:** Body requiere `{ "sample_expediente_id": "uuid" }`. Si falta → 400. Renderiza template con datos reales del expediente indicado. Envía a CEO_EMAIL. Log con event_log=null, trigger_action_source='test_send'.

### H2. Historial de envíos (CEO-only)

| Método | Endpoint | Permiso | Descripción |
|--------|----------|---------|-------------|
| GET | /api/notifications/log/ | CEO | NotificationLog. Filtros: expediente, status, date range. Paginado 25/page. |
| GET | /api/notifications/collections/ | CEO | CollectionEmailLog. Filtros: expediente, date range. Paginado 25/page. |

### H3. Envío manual de proforma (CEO-only)

| Método | Endpoint | Permiso | Descripción |
|--------|----------|---------|-------------|
| POST | /api/notifications/send-proforma/ | CEO | Envía proforma por email |

**Contrato cerrado (fix M4 R2 — override_used eliminado):**

```python
# Request body
{
    "proforma_id": "uuid",               # Obligatorio
    "recipient_email_override": "email"   # Opcional
}

# Comportamiento:
# - Siempre usa template_key='proforma.sent'.
# - trigger_action_source='send_proforma_manual'.
# - event_log=null (no aplica constraint idempotencia, sino dedup temporal).
# - Dedup: si ya se envió proforma.sent para esta proforma+recipient en última hora → 409 Conflict.
# - Trazabilidad de override: si override se usó, recipient_email del log != contact_email.
#   No se necesita campo booleano separado — el cruce con contact_email es suficiente.
# - proforma_id inexistente → 404.
```

### H4. Seguridad

- CEO-only via `IsCEO`.
- ClientScopedManager no aplica.
- Rate limiting heredado de S24.
- Sin endpoints para CLIENT_*.

---

## I. Frontend — Admin Templates

### I1. Rutas explícitas

| Ruta App Router | Página | Componentes |
|----------------|--------|-------------|
| `/notifications/templates` | Gestión templates | TemplatesTable + TemplateEditor (Drawer) |
| `/notifications/history` | Historial envíos | NotificationLogTable |
| `/notifications/collections` | Historial cobros | CollectionLogTable |

### I2. Componentes

| Componente | Descripción |
|-----------|-------------|
| TemplatesTable | Lista: template_key, name, brand/"Default", language, is_active toggle, edit, test-send |
| TemplateEditor (Drawer) | Form: name, subject, body (textarea), brand, language, is_active. Test Send (selector expediente). Preview renderizado. |
| NotificationLogTable | Tabla: fecha, expediente, recipient, status badge, subject, trigger_action_source. Filtros: status, fecha, expediente. |
| CollectionLogTable | Tabla: fecha, expediente, pago, monto, recipient, status. Filtros: fecha, expediente. |

### I3. Sidebar CEO

"Notificaciones" con 3 subitems: Templates, Historial, Cobros. Solo visible CEO.

### I4. Expediente detail

Sección colapsable "Emails enviados". Últimos 10 NotificationLog. Read-only: fecha, subject, status badge, recipient.

---

## J. Items del sprint

### Fase 0 — Modelos + precondiciones (backend)

| ID | Tarea | Detalle | Tests |
|----|-------|---------|-------|
| S26-01 | Crear app `notifications/` con modelos C1, C2a, C2b, C3 | NotificationTemplate (UniqueConstraint condicional), NotificationAttempt (append-only), NotificationLog (resultado final, UniqueConstraint event_log+recipient), CollectionEmailLog (+completed_at). | Test constraints Template. Test constraint Log. Test Attempt append-only. |
| S26-02 | Verificar contact_email + preferred_language en ClientSubsidiary | Inspeccionar modelo. Si falta → migración aditiva. Documentar resultado en PR. | Test nullable email válido. |
| S26-02b | Verificar FK proforma en ExpedientePago (fix M1 R2) | Inspeccionar modelo. Si no existe → crear migración aditiva nullable O documentar que cobranza usa Mode B default. | Test: si FK existe, select_related('proforma') no falla. |
| S26-03 | Data migration: 10 templates seed (fix M2 R2) | get_or_create por template_key+brand+language. 10 templates (paridad con TRIGGER_TO_TEMPLATE + cron + manual). | Test: 10 templates post-migrate. Test idempotente: 2x → 10. |

### Fase 1 — Email backend + tasks (backend)

| ID | Tarea | Detalle | Tests |
|----|-------|---------|-------|
| S26-04 | Email backends + dependencias | SMTPBackend + SESBackend. Agregar Jinja2 y moto[ses] a requirements (fix N2 R2). SandboxedEnvironment. | Test SMTP mock. Test SES mock (moto). Test sandbox bloquea __import__. |
| S26-05 | send_notification task | Two-model: Attempt (per try) + Log (terminal). Advisory lock dedup on Log. SendResult branching (SENT/RETRYABLE/PERMANENT). Render try/except with audit trail. MaxRetriesExceeded → Log(exhausted). Manual flows wrapped in try/except. correlation_id links attempts↔log. | Test: sent → Attempt(sent) + Log(sent). Test: no recipient → Attempt(skipped) + Log(skipped). Test: RETRYABLE → Attempt(failed) + retry, no Log yet. Test: exhausted → Log(exhausted) + attempt_count. Test: PERMANENT → Attempt(failed) + Log(exhausted) immediately. Test: disabled. Test: dedup (Log exists → skip). Test: sha256 key deterministic. Test: render error → Attempt(failed) + Log(exhausted). Test: correlation_id consistent across attempts+log. |
| S26-06 | resolve_notification_recipient + resolve_collection_recipient | Dos funciones. Cobranza resuelve por proforma del pago. Notificación por expediente/proforma. | Test: Mode C → CEO. Test: Mode B → contact. Test: null → None. Test: cobranza con proforma. Test: cobranza sin proforma → Mode B. |
| S26-07 | check_overdue_payments task | refresh_from_db. resolve_collection_recipient. SendResult branching (SENT/RETRYABLE/PERMANENT). Render try/except with audit trail. Advisory lock + dedup 7d on completed_at. Kill switch = logger only. _meta introspection proforma FK. | Test: overdue → sent + completed_at. Test: within grace → skip. Test: dedup 7d (completed_at). Test: status changed → skip. Test: kill switch → no log. Test: lock key deterministic. Test: render error → CollectionEmailLog(failed). Test: RETRYABLE → CollectionEmailLog(failed). |
| S26-08 | Celery Beat config | Schedule 14:00 UTC. | Test: task in beat_schedule. |

### Fase 2 — Hook dispatcher + endpoints (backend)

| ID | Tarea | Detalle | Tests |
|----|-------|---------|-------|
| S26-09 | Hook dispatcher | notify_on_command en post_command_hooks. Pasa event_log_id. | Test: C1 → delay called con event_log_id. Test: hook fail → command safe. Test: unmapped command → no call. |
| S26-10 | Templates CRUD + restore | ViewSet CEO-only. test-send requiere sample_expediente_id. DELETE = desactivar. /restore/ = reactivar (fix N1 R3). Inactivos visibles en lista (grayed). | Test: CRUD. Test: CLIENT → 403. Test: test-send sin expediente → 400. Test: test-send → email + log. Test: DELETE → is_active=False. Test: restore → is_active=True. |
| S26-11 | Historial endpoints | Log + Collections list. Filtros + paginación. | Test: filtro expediente. Test: filtro status. Test: paginación. |
| S26-12 | Send proforma | template_key='proforma.sent'. Dedup 1h. No override_used field. | Test: default recipient. Test: override. Test: 404 proforma. Test: dedup 1h → 409. |

### Fase 3 — Frontend (AG-03)

| ID | Tarea | Detalle | Validación |
|----|-------|---------|------------|
| S26-13 | /notifications/templates | TemplatesTable + TemplateEditor. Toggle. Test-send con expediente selector. | Funcional |
| S26-14 | /notifications/history + /notifications/collections | Dos páginas. Filtros. Paginación. Status badges. | Funcional |
| S26-15 | Sidebar "Notificaciones" | 3 subitems. CEO-only. | Visible solo CEO |
| S26-16 | Expediente detail "Emails enviados" | Colapsable. 10 logs. Read-only. | Datos correctos |

### Fase 4 — Integración + verificación

| ID | Tarea | Detalle | Tests |
|----|-------|---------|-------|
| S26-17 | E2E flow completo | Activar → C1 → email → log → historial → persistencia deduplicada verificada; entrega at-least-once documentada. | Manual + automatizado |
| S26-18 | .env.example | 6 variables nuevas. | Actualizado |
| S26-19 | 0 regresiones | pytest backend/ completo. | 0 failures |

---

## K. Seguridad

| Aspecto | Evaluación |
|---------|-----------|
| Nuevos canales | NO — outbound only |
| Datos en email | Código expediente, nombre cliente, monto pago. Sin pricing/márgenes/costos. |
| Jinja2 injection | SandboxedEnvironment. Test bloquea __import__. CEO-only edita templates. |
| SPF + DKIM | Configurar DNS post-deploy. Pendiente operativo. |
| Rate limiting emails | SES nativo. SMTP: Celery rate_limit='5/s'. |
| Audit trail | CollectionEmailLog inmutable. NotificationLog inmutable. |
| send-proforma | Dedup 1h. CEO-only. Rate limiting S24. |

---

## L. Rollback por fase

| Fase | Rollback |
|------|----------|
| 0 | Revert migración. Sin dependencias externas. |
| 1 | MWT_NOTIFICATION_ENABLED=False. Tasks crean log 'disabled' (notif) o logger.info (cobranza). |
| 2 | Remover hook de post_command_hooks. Dispatcher no cambia. |
| 3 | Remover páginas + sidebar item. Sin impacto. |

---

## M. Archivos a crear/modificar

### Crear

| Archivo | Qué |
|---------|-----|
| `apps/notifications/__init__.py` | App |
| `apps/notifications/models.py` | C1-C3 |
| `apps/notifications/admin.py` | Admin |
| `apps/notifications/backends.py` | D1 |
| `apps/notifications/tasks.py` | E1, E3 |
| `apps/notifications/services.py` | E2, E2b, G2, resolve_template |
| `apps/notifications/mappings.py` | F1 |
| `apps/notifications/serializers.py` | Serializers |
| `apps/notifications/views.py` | H1-H3 |
| `apps/notifications/urls.py` | URLs |
| `apps/notifications/permissions.py` | IsCEO (import) |
| `apps/notifications/migrations/0001_initial.py` | Modelos |
| `apps/notifications/migrations/0002_seed_templates.py` | 10 seeds |
| `backend/tests/test_sprint26.py` | 63 tests |
| `frontend/src/app/[locale]/(mwt)/(dashboard)/notifications/templates/page.tsx` | |
| `frontend/src/app/[locale]/(mwt)/(dashboard)/notifications/history/page.tsx` | |
| `frontend/src/app/[locale]/(mwt)/(dashboard)/notifications/collections/page.tsx` | |
| `frontend/src/components/notifications/` | 4 componentes |

### Modificar

| Archivo | Qué |
|---------|-----|
| `config/settings/base.py` | +INSTALLED_APPS. +6 settings. |
| `config/urls.py` | +include notifications.urls |
| `config/celery.py` | +beat_schedule |
| `apps/expedientes/services/dispatcher.py` | +notify_on_command + pasar event_log_id |
| `apps/clientes/models.py` | +contact_email si no existe |
| `apps/expedientes/models.py` | +proforma FK en ExpedientePago si no existe |
| `frontend/src/components/layout/Sidebar.tsx` | +Notificaciones (CEO, 3 subitems) |
| `.env.example` | +6 variables |
| `requirements/base.txt` | +Jinja2 |
| `requirements/test.txt` | +moto[ses] |

### No tocar

- `apps/expedientes/services/state_machine/` (FROZEN)
- `apps/expedientes/services/pricing/` (S22)
- `apps/commercial/` (S23)
- `docker-compose.yml`

---

## N. Conteo tests (63)

| Grupo | Tests | Items |
|-------|-------|-------|
| Modelos (constraints Template + Log + Attempt, save/delete enforcement) | 8 | S26-01 |
| Precondiciones (contact_email, proforma FK) | 2 | S26-02, S26-02b |
| Seed templates | 2 | S26-03 |
| Email backends + SandboxedEnvironment + SendResult | 5 | S26-04 |
| send_notification (sent, skipped, disabled, dedup, RETRYABLE+retry, PERMANENT, exhausted, render error, correlation_id, manual fail) | 11 | S26-05 |
| resolve_*_recipient (5 escenarios) | 5 | S26-06 |
| check_overdue_payments (overdue, grace, dedup, recheck, kill switch, lock key, render error, RETRYABLE) | 8 | S26-07 |
| Dispatcher hook (mapped, unmapped, hook-fail-safe) | 3 | S26-09 |
| Templates CRUD + test-send + restore | 6 | S26-10 |
| Historial API (filtros, paginación) | 3 | S26-11 |
| Send proforma (default, override, 404, dedup) | 4 | S26-12 |
| Seguridad (CLIENT → 403) | 2 | S26-10, S26-12 |
| E2E (full flow + dedup persistence) | 2 | S26-17 |
| Regresiones | 2 | S26-19 |
| **Total** | **63** | |

---

## O. Gate Sprint 26

- [ ] NotificationTemplate UniqueConstraint condicional funciona (brand=null y brand!=null)
- [ ] 10 templates seed presentes post-migrate (idempotente)
- [ ] Kill switch notificaciones: MWT_NOTIFICATION_ENABLED=False → log 'disabled', 0 emails
- [ ] Kill switch cobranza: MWT_NOTIFICATION_ENABLED=False → logger.info, 0 CollectionEmailLog (fix M3 R2)
- [ ] MWT_NOTIFICATION_ENABLED=True → emails enviados
- [ ] resolve_notification_recipient: Mode C → CEO, Mode B → contact_email
- [ ] resolve_collection_recipient: resuelve por proforma del pago
- [ ] Hook dispatcher: C1 → delay con event_log_id + trigger_action_source
- [ ] check_overdue_payments: refresh_from_db pre-envío, dedup 7d
- [ ] CollectionEmailLog persiste proforma FK cuando aplica
- [ ] test-send requiere sample_expediente_id (400 si falta)
- [ ] send-proforma: template_key='proforma.sent', dedup 1h, sin override_used
- [ ] NotificationLog: trigger_action_source + template_key + FK event_log
- [ ] Jinja2 SandboxedEnvironment — test bloquea __import__
- [ ] Frontend: 3 páginas (/templates, /history, /collections)
- [ ] Sidebar: "Notificaciones" visible solo CEO, 3 subitems
- [ ] Expediente detail: "Emails enviados" con datos correctos
- [ ] send_notification: advisory lock sha256 (deterministic across workers)
- [ ] send_notification: send OUTSIDE tx, lock+check+log INSIDE tx
- [ ] send_notification: kill switch + event_log_id → advisory lock before disabled log (fix B1 R6)
- [ ] send_notification: no status 'pending' — log created only with final result
- [ ] check_overdue_payments: same at-least-once pattern (send outside, lock+log inside, sha256)
- [ ] check_overdue_payments: dedup 7d basado en completed_at
- [ ] check_overdue_payments: select_related('proforma') via _meta introspection
- [ ] _create_terminal: completed_at seteado en TODOS los paths terminales
- [ ] CollectionEmailLog: created_at + completed_at, dedup on completed_at
- [ ] Templates DELETE = desactivar. /restore/ endpoint. Inactivos visibles en admin
- [ ] NotificationLog: created_at = log creation. completed_at = finalization
- [ ] At-least-once: duplicate sends possible under concurrency, not only crash. Deduplicated persistence only (fix M1+M2 R6).
- [ ] No reference to SES MessageDeduplicationId. Exactly-once = outbox/idempotency layer future (fix N1 R6).
- [ ] SendResult branching en E1 Y E3 — SENT/RETRYABLE/PERMANENT, cero lógica booleana
- [ ] Render Jinja2 envuelto en try/except en E1 Y E3 — error crea audit trail antes de return
- [ ] save() override en NotificationLog, CollectionEmailLog — bloquea updates sobre existentes
- [ ] Enforcement homogéneo: delete()+save() raise en Attempt, Log, y CollectionEmailLog
- [ ] correlation_id en attempt_base y log_base — event_log_id o uuid4()
- [ ] 63 tests backend verdes
- [ ] 0 regresiones
- [ ] .env.example + requirements actualizados

---

## P. Excluido explícitamente

- **Email HTML responsive** → MVP plain text. HTML futuro.
- **Inbound email parsing** → Sprint futuro (ENT_PLAT_CANALES_CLIENTE P3).
- **WhatsApp notificaciones** → CEO-14. Sprint separado.
- **Adjuntos en email** → Signed URLs en body suficientes.
- **Notificaciones push/in-app** → Activity feed (S21) cubre.
- **Unsubscribe por cliente** → Post-MVP.
- **Multi-idioma templates** → Estructura soporta language, seed solo 'es'.

---

## Q. Pendientes CEO resueltos

| ID | Items | Estado post-sprint |
|----|-------|-------------------|
| CEO-16 | DEC-S26-03 + F1 | DONE |
| CEO-28 | DEC-S26-01 + D1 | DONE |

## Pendientes que NO resuelve

CEO-14 (WhatsApp), CEO-15 (artifacts visibles), CEO-22 (LGPD), CEO-24 (LLM Intelligence), CEO-25/26/27 (compliance PORON).

---

## R. Dependencias externas

- Email provider configurado (DEC-S26-01)
- DNS: SPF + DKIM post-deploy
- Variables .env (6 nuevas)
- Celery + Redis operativos
- S25 DONE (payment status)
- Jinja2 + moto[ses] en requirements

---

## S. Auditoría

| Ronda | Auditor | Score | Hallazgos | Aplicados |
|-------|---------|-------|-----------|-----------|
| R1 (v1.0) | ChatGPT | 8.4/10 | 10 (2B + 5M + 3N) | 10 en v1.1 |
| R2 (v1.1) | ChatGPT | 8.8/10 | 8 (2B + 4M + 2N) | 8 en v1.2 |
| R3 (v1.2) | ChatGPT | 8.9/10 | 5 (1B + 2M + 2N) | 5 en v1.3 |
| R4 (v1.3) | ChatGPT | 8.7/10 | 4 (2B + 2M) | 4 en v1.4 |
| R5 (v1.4) | ChatGPT | 8.9/10 | 4 (2B + 2M) | 4 en v1.5 |
| R6 (v1.5) | ChatGPT | 9.1/10 | 4 (1B + 2M + 1N) | 4 en v1.6 |
| R7 (v1.6) | ChatGPT | 8.9/10 | 3 (1B + 2M) | 3 en v1.7 |
| R8 (v1.7) | ChatGPT | 8.9/10 | 3 (1B + 2M) | 3 en v1.8 |
| R9 (v1.8) | ChatGPT | 8.9/10 | 3 (1B + 2M) | 3 en v1.9 |
| R10 (v1.9) | ChatGPT | 8.7/10 | 4 (2B + 2M) | 4 en v2.0 |
| R11 (v2.0) | ChatGPT | 8.8/10 | 4 (2B + 2M) | 4 en v2.1 |
| R12 (v2.1) | ChatGPT | 8.8/10 | 3 (1B + 2M) | 3 en v2.2 |
| R13 (v2.2) | ChatGPT | 8.9/10 | 3 (1B + 2M) | 3 en v2.3 |
