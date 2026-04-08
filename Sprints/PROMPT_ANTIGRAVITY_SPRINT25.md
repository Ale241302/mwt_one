# PROMPT_ANTIGRAVITY_SPRINT25 — Negocio Avanzado: Payment Status + Deferred + Parent/Child
ref: LOTE_SM_SPRINT25 v1.6 (auditado R6 — score 9.6/10)

## TU ROL
Eres AG-02 (backend developer). Ejecutás el Sprint 25 del proyecto MWT.ONE. Tu trabajo es implementar exactamente lo que dice el LOTE_SM_SPRINT25 v1.6. No diseñás, no proponés alternativas, no expandís scope. Si algo no está claro, preguntás al CEO — no adivinás.

## CONTEXTO
Sprint 25 añade tres capacidades de negocio: (A) payment status machine con verificación y liberación de crédito, (B) precio diferido con visibilidad condicional, (C) parent/child con inversión en split.

**Estado del código (post Sprint 24 DONE):**
- State machine 8 estados, 28+ commands con dispatcher central
- ExpedientePago funcional (modelo S17, endpoint S18)
- CreditPolicy + CreditExposure + CreditOverride (S16)
- recalculate_expediente_credit (S18-10) con snapshot
- Proforma como unidad operativa con ArtifactPolicy (S20)
- EventLog extendido: user FK, proforma FK, action_source (S21)
- Activity feed con badge y panel (S21)
- Pricing engine v2: resolve_client_price() waterfall 4 pasos (S22)
- BrandWorkflowPolicy en DB (S23)
- Portal B2B autogestión + seguridad JWT/rate limiting/signed URLs (S24)
- merge/ y separate-products/ endpoints (S18)

## HARD RULES

1. **State machine FROZEN.** NO tocar handlers de transición en `services/state_machine/`. El payment_status es interno a ExpedientePago, NO un estado del expediente. NO agregar commands al dispatcher.
2. **Backward compat.** POST pagos existente (sin payment_status) DEBE seguir funcionando. Default payment_status='pending'.
3. **Migración additive-only.** Solo `AddField`. Data migration condicional para pagos legacy. Verificar con `sqlmigrate` antes de aplicar. Si aparece `AlterField` o `RemoveField` → PARAR.
4. **Migración usa apps.get_model(), no import model vivo.** Los status en la data migration son strings congelados con comentario de origen FROZEN. NO importar `from apps.expedientes.models import Expediente`.
5. **Locking obligatorio.** Todo endpoint mutante: `transaction.atomic()` + `select_for_update()` en ExpedientePago y/o Expediente según corresponda.
6. **CreditOverride intocable.** Si existe un CreditOverride para el expediente, recalculate_expediente_credit() lo respeta sin importar payment_status.
7. **Transiciones terminales.** `rejected` y `credit_released` son terminales. No hay vuelta atrás. Para corregir un rechazo erróneo → crear nuevo pago.
8. **Deferred es independiente.** `deferred_total_price` NO interactúa con `resolve_client_price()` ni con el pricing engine S22. Es un campo manual del CEO.
9. **Invariante deferred.** `deferred_total_price=null` + `deferred_visible=true` es estado inválido. Payload contradictorio en misma llamada → 400 (NO auto-corrección). PATCH solo null → auto-corrige visible=false.
10. **Tiering CreditBar.** CEO/AGENT_*: snapshot monetario completo. CLIENT_*: solo `payment_coverage` + `coverage_pct`. Serializer SEPARADO por tier — no filtrar post-serialización.

## VERIFICACIÓN PREVIA (antes de escribir código)

```bash
# Verificar que Sprint 24 está limpio
python manage.py check
python manage.py test
python manage.py showmigrations | grep "\[ \]"  # 0 migraciones pendientes

# Verificar modelos existentes
python manage.py shell -c "from apps.expedientes.models import ExpedientePago; print([f.name for f in ExpedientePago._meta.get_fields()])"
python manage.py shell -c "from apps.expedientes.models import Expediente; print([f.name for f in Expediente._meta.get_fields()])"

# Verificar recalculate_expediente_credit existe
grep -rn "recalculate_expediente_credit" backend/apps/expedientes/

# Verificar separate-products endpoint
grep -rn "separate.products\|separate_products" backend/apps/expedientes/
```

## ITEMS

### FASE 0 — Modelos y migraciones

#### S25-01: Campos payment_status en ExpedientePago

Campos compatibles con legacy: timestamps/FKs nullable, `payment_status` con default `'pending'`, `rejection_reason` blank.

```python
# apps/expedientes/models.py — agregar a ExpedientePago:

PAYMENT_STATUS_CHOICES = [
    ('pending', 'Pendiente verificación'),
    ('verified', 'Verificado'),
    ('credit_released', 'Crédito liberado'),
    ('rejected', 'Rechazado'),
]

payment_status = models.CharField(
    max_length=20,
    choices=PAYMENT_STATUS_CHOICES,
    default='pending',
)
verified_at = models.DateTimeField(null=True, blank=True)
verified_by = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.SET_NULL, null=True, blank=True,
    related_name='verified_payments',
)
credit_released_at = models.DateTimeField(null=True, blank=True)
credit_released_by = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.SET_NULL, null=True, blank=True,
    related_name='released_payments',
)
rejection_reason = models.TextField(blank=True, default='')
```

**MIGRACIÓN (dos pasos):**
```bash
# Paso 1: AddField (structural)
python manage.py makemigrations expedientes --name add_payment_status
python manage.py sqlmigrate expedientes XXXX  # SOLO AddField ×6
python manage.py migrate

# Paso 2: Data migration (condicional)
python manage.py makemigrations expedientes --empty --name migrate_legacy_payment_status
```

**Data migration — usa apps.get_model() + strings congelados (ref C2 del lote):**
```python
def forwards(apps, schema_editor):
    ExpedientePago = apps.get_model("expedientes", "ExpedientePago")
    Expediente = apps.get_model("expedientes", "Expediente")

    # Congelados desde ENT_OPS_STATE_MACHINE FROZEN v1.2.2
    # NO importar del model vivo.
    GATE_PASSED_STATUSES = {
        "PRODUCCION", "PREPARACION", "DESPACHO",
        "TRANSITO", "EN_DESTINO", "CERRADO",
    }

    for pago in ExpedientePago.objects.select_related("expediente").iterator():
        if pago.amount is None or pago.amount <= 0:
            pago.payment_status = 'pending'
        elif pago.expediente.status in GATE_PASSED_STATUSES:
            pago.payment_status = 'credit_released'
        else:
            pago.payment_status = 'verified'
        pago.save(update_fields=['payment_status'])

# reverse = migrations.RunPython.noop
```

⚠️ Forward-only. Backup obligatorio de `expedientes_expedientepago` antes de ejecutar.

#### S25-02: Campos deferred + parent/child en Expediente

```python
# apps/expedientes/models.py — agregar a Expediente:

deferred_total_price = models.DecimalField(
    max_digits=14, decimal_places=2,
    null=True, blank=True,
)
deferred_visible = models.BooleanField(default=False)
parent_expediente = models.ForeignKey(
    'self',
    on_delete=models.SET_NULL,
    null=True, blank=True,
    related_name='child_expedientes',
)
is_inverted_child = models.BooleanField(default=False)
```

```bash
python manage.py makemigrations expedientes --name add_deferred_parent_child
python manage.py sqlmigrate expedientes XXXX  # SOLO AddField ×4
python manage.py migrate
```

### FASE 1 — Servicios y endpoints

#### S25-03: Verify + Reject endpoints

```python
# apps/expedientes/views/payment_status.py

@api_view(['POST'])
@permission_classes([IsCEOOrSuperuser])
def verify_payment(request, exp_id, pago_id):
    with transaction.atomic():
        expediente = Expediente.objects.select_for_update().get(id=exp_id)
        pago = ExpedientePago.objects.select_for_update().get(
            id=pago_id, expediente=expediente
        )
        if pago.payment_status != 'pending':
            return Response(
                {'error': f'Cannot verify payment in status {pago.payment_status}'},
                status=status.HTTP_409_CONFLICT
            )
        pago.payment_status = 'verified'
        pago.verified_at = timezone.now()
        pago.verified_by = request.user
        pago.save(update_fields=['payment_status', 'verified_at', 'verified_by'])

        EventLog.objects.create(
            expediente=expediente,
            event_type='payment.verified',
            action_source='verify_payment',
            user=request.user,
            payload={'pago_id': str(pago.id), 'amount': str(pago.amount)}
        )
    return Response({'status': 'verified'})


@api_view(['POST'])
@permission_classes([IsCEOOrSuperuser])
def reject_payment(request, exp_id, pago_id):
    reason = request.data.get('reason', '').strip()
    if not reason:
        return Response({'error': 'reason is required'}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        expediente = Expediente.objects.select_for_update().get(id=exp_id)
        pago = ExpedientePago.objects.select_for_update().get(
            id=pago_id, expediente=expediente
        )
        if pago.payment_status not in ('pending', 'verified'):
            return Response(
                {'error': f'Cannot reject payment in status {pago.payment_status}'},
                status=status.HTTP_409_CONFLICT
            )

        previous_status = pago.payment_status
        pago.payment_status = 'rejected'
        pago.rejection_reason = reason
        pago.save(update_fields=['payment_status', 'rejection_reason'])

        EventLog.objects.create(
            expediente=expediente,
            event_type='payment.rejected',
            action_source='reject_payment',
            user=request.user,
            payload={
                'pago_id': str(pago.id), 'amount': str(pago.amount),
                'previous_status': previous_status, 'reason': reason,
            }
        )
        recalculate_expediente_credit(expediente)
    return Response({'status': 'rejected'})
```

#### S25-04: Release credit endpoints

```python
@api_view(['POST'])
@permission_classes([IsCEOOrSuperuser])
def release_credit(request, exp_id, pago_id):
    with transaction.atomic():
        expediente = Expediente.objects.select_for_update().get(id=exp_id)
        pago = ExpedientePago.objects.select_for_update().get(
            id=pago_id, expediente=expediente
        )
        if pago.payment_status != 'verified':
            return Response(
                {'error': f'Cannot release credit for payment in status {pago.payment_status}'},
                status=status.HTTP_409_CONFLICT
            )
        pago.payment_status = 'credit_released'
        pago.credit_released_at = timezone.now()
        pago.credit_released_by = request.user
        pago.save(update_fields=[
            'payment_status', 'credit_released_at', 'credit_released_by'
        ])

        EventLog.objects.create(
            expediente=expediente,
            event_type='payment.credit_released',
            action_source='release_credit',
            user=request.user,
            payload={'pago_id': str(pago.id), 'amount': str(pago.amount)}
        )
        recalculate_expediente_credit(expediente)
    return Response({'status': 'credit_released'})


@api_view(['POST'])
@permission_classes([IsCEOOrSuperuser])
def release_all_verified(request, exp_id):
    """Bulk release: opera sobre pagos verified + credit_released.
    Pagos pending/rejected se ignoran. Recálculo UNA vez al final."""
    with transaction.atomic():
        expediente = Expediente.objects.select_for_update().get(id=exp_id)
        pagos = (
            ExpedientePago.objects
            .select_for_update()
            .filter(expediente=expediente, payment_status__in=['verified', 'credit_released'])
        )

        released = 0
        already_released = 0
        for pago in pagos:
            if pago.payment_status == 'credit_released':
                already_released += 1
            elif pago.payment_status == 'verified':
                pago.payment_status = 'credit_released'
                pago.credit_released_at = timezone.now()
                pago.credit_released_by = request.user
                pago.save(update_fields=[
                    'payment_status', 'credit_released_at', 'credit_released_by'
                ])
                # 1 EventLog por pago, con payload.bulk=true
                EventLog.objects.create(
                    expediente=expediente,
                    event_type='payment.credit_released',
                    action_source='release_credit',
                    user=request.user,
                    payload={'pago_id': str(pago.id), 'amount': str(pago.amount), 'bulk': True}
                )
                released += 1

        # Recálculo UNA vez post-bulk
        if released > 0:
            recalculate_expediente_credit(expediente)

    return Response({'released': released, 'already_released': already_released})
```

#### S25-05: Extender recalculate_expediente_credit()

Localizar la función existente:
```bash
grep -rn "def recalculate_expediente_credit" backend/
```

**Crear `compute_coverage` como función separada (SSOT):**
```python
# apps/expedientes/services/credit.py (o donde esté recalculate)
from decimal import Decimal, ROUND_HALF_UP

def compute_coverage(total_paid: Decimal, expediente_total: Decimal | None) -> tuple[str, Decimal]:
    """SSOT para payment_coverage y coverage_pct."""
    if expediente_total is None or expediente_total <= 0:
        return 'none', Decimal("0.00")

    coverage_pct = min(
        Decimal("100.00"),
        ((total_paid / expediente_total) * Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    )

    if total_paid <= 0:
        payment_coverage = 'none'
    elif total_paid >= expediente_total:
        payment_coverage = 'complete'
    else:
        payment_coverage = 'partial'

    return payment_coverage, coverage_pct
```

**Cambio en recalculate_expediente_credit:**
```python
# ANTES (S18):
total_paid = sum(p.amount for p in expediente.pagos.all() if p.amount)

# DESPUÉS (S25):
total_released = sum(
    p.amount for p in expediente.pagos.filter(payment_status='credit_released')
    if p.amount
) or Decimal('0')
total_pending = sum(
    p.amount for p in expediente.pagos.filter(payment_status__in=['pending', 'verified'])
    if p.amount
) or Decimal('0')
total_rejected = sum(
    p.amount for p in expediente.pagos.filter(payment_status='rejected')
    if p.amount
) or Decimal('0')

payment_coverage, coverage_pct = compute_coverage(total_released, expediente.total_value)

# Snapshot actualizado
credit_snapshot = {
    'total_paid': str(total_released),
    'total_pending': str(total_pending),
    'total_rejected': str(total_rejected),
    'credit_exposure': str(exposure),
    'credit_available': str(available),
    'payment_coverage': payment_coverage,
    'coverage_pct': str(coverage_pct),
}
```

**IMPORTANTE:** Si existe un CreditOverride para este expediente, respetar el override. No modificar esa lógica.

#### S25-06: Endpoint deferred price

```python
# apps/expedientes/views/deferred.py

@api_view(['PATCH'])
@permission_classes([IsCEOOrSuperuser])
def patch_deferred_price(request, exp_id):
    with transaction.atomic():
        expediente = Expediente.objects.select_for_update().get(id=exp_id)

        price_val = request.data.get('deferred_total_price', _MISSING)
        visible_val = request.data.get('deferred_visible', _MISSING)

        # Validar precio >= 0 si se provee
        if price_val is not _MISSING and price_val is not None:
            if Decimal(str(price_val)) < 0:
                return Response(
                    {'error': 'deferred_total_price must be >= 0'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # PRECEDENCIA (fix M1 R6): payload contradictorio = error duro
        if price_val is None and visible_val is True:
            return Response(
                {'error': 'Cannot set deferred_visible=True and deferred_total_price=null in the same request.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        update_fields = []

        # Auto-corrección: null price → forzar visible=false
        if price_val is None and price_val is not _MISSING:
            expediente.deferred_total_price = None
            expediente.deferred_visible = False
            update_fields.extend(['deferred_total_price', 'deferred_visible'])
        elif price_val is not _MISSING:
            expediente.deferred_total_price = price_val
            update_fields.append('deferred_total_price')

        if visible_val is not _MISSING and 'deferred_visible' not in update_fields:
            # Verificar que no se active visible con precio null
            current_price = expediente.deferred_total_price
            if price_val is not _MISSING:
                current_price = price_val
            if visible_val and current_price is None:
                return Response(
                    {'error': 'Cannot set deferred_visible=True when deferred_total_price is null.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            expediente.deferred_visible = visible_val
            update_fields.append('deferred_visible')

        if not update_fields:
            return Response({'error': 'No fields to update'}, status=status.HTTP_400_BAD_REQUEST)

        expediente.save(update_fields=update_fields)

        EventLog.objects.create(
            expediente=expediente,
            event_type='expediente.deferred_price_updated',
            action_source='patch_deferred',
            user=request.user,
            payload={f: str(getattr(expediente, f)) for f in update_fields}
        )
    return Response({'status': 'updated', 'fields': update_fields})
```

**_MISSING** es un sentinel: `_MISSING = object()`. Sirve para distinguir "campo no enviado" de "campo enviado como null".

#### S25-07: Extender separate-products con inversión

Localizar el endpoint existente:
```bash
grep -rn "separate.products\|separate_products" backend/apps/expedientes/
```

**Cambio clave — agregar al handler existente:**
```python
invert_parent = request.data.get('invert_parent', False)

# Restricción: no invertir si ya es child
if invert_parent and expediente.parent_expediente_id is not None:
    return Response(
        {'error': 'Cannot invert parent on an expediente that is already a child.'},
        status=status.HTTP_409_CONFLICT
    )

# Después de crear new_exp dentro de transaction.atomic():
if invert_parent:
    expediente.parent_expediente = new_exp
    expediente.is_inverted_child = True
    expediente.save(update_fields=['parent_expediente', 'is_inverted_child'])
else:
    new_exp.parent_expediente = expediente
    new_exp.save(update_fields=['parent_expediente'])

# EventLog en AMBOS expedientes
for exp, role in [(expediente, 'original'), (new_exp, 'new')]:
    EventLog.objects.create(
        expediente=exp,
        event_type='expediente.split',
        action_source='separate_products',
        user=request.user,
        payload={
            'parent_id': str(new_exp.id if invert_parent else expediente.id),
            'child_id': str(expediente.id if invert_parent else new_exp.id),
            'inverted': invert_parent,
            'role': role,
            'lines_moved': [str(l.id) for l in moved_lines],
        }
    )
```

#### S25-08: Bundle de detalle extendido

**Serializer CEO/AGENT_*:**
```python
# Pagos: agregar payment_status, verified_at, verified_by_display, credit_released_at, rejection_reason
# Credit snapshot: agregar total_pending, total_rejected, payment_coverage, coverage_pct
# Deferred: agregar deferred_total_price, deferred_visible
# Parent/child: agregar parent_expediente {id, number}, child_expedientes [{id, number}], is_inverted_child
```

**Serializer portal (CLIENT_*) — tiering explícito:**
```python
# Pagos: solo amount, date, payment_status (sin rejection_reason, verified_by, credit_released_by)
# Credit snapshot: SOLO payment_coverage + coverage_pct (sin total_paid, total_pending, credit_available, credit_exposure)
# Deferred: solo deferred_total_price SI deferred_visible=True. Sin deferred_visible.
# Parent: solo parent_expediente.number (informativo)
# Sin: child_expedientes, is_inverted_child
```

### URLs

```python
# apps/expedientes/urls.py — agregar:

# Payment status
path('<uuid:exp_id>/pagos/<uuid:pago_id>/verify/', verify_payment),
path('<uuid:exp_id>/pagos/<uuid:pago_id>/reject/', reject_payment),
path('<uuid:exp_id>/pagos/<uuid:pago_id>/release-credit/', release_credit),
path('<uuid:exp_id>/pagos/release-all-verified/', release_all_verified),

# Deferred price
path('<uuid:exp_id>/deferred-price/', patch_deferred_price),
```

### FASE 3 — Tests (56 mínimo)

Implementar los 56 tests del lote. Ver LOTE_SM_SPRINT25 v1.6 §S25-14 para la lista completa numerada.

Tests críticos que NO podés saltarte:
- Test 46: GATE_PASSED_STATUSES de la migración es subconjunto de Expediente.Status enum canónico
- Test 48-50: invariante deferred null/visible (3 escenarios)
- Test 51-52: tiering portal (ausencia montos + presencia contrato)
- Test 53-54: compute_coverage edge cases (total=0, total=None)
- Test 55: payload contradictorio deferred → 400
- Test 56: ROUND_HALF_UP verificado

```bash
pytest backend/tests/test_sprint25.py -v
# → 56/56 passed ✅
```

## ARCHIVOS QUE VAS A TOCAR

| Archivo | Qué hacer |
|---------|-----------|
| `apps/expedientes/models.py` | +6 campos en ExpedientePago, +4 campos en Expediente |
| `apps/expedientes/services/credit.py` | +compute_coverage(), extender recalculate_expediente_credit() |
| `apps/expedientes/views/payment_status.py` | CREAR — verify, reject, release, release_all |
| `apps/expedientes/views/deferred.py` | CREAR — patch_deferred_price con invariante |
| `apps/expedientes/serializers.py` | +PagoSerializer fields, +CEO/portal serializers separados, +credit snapshot tiered |
| `apps/expedientes/views.py` | Extender separate-products con inversión |
| `apps/expedientes/urls.py` | Registrar nuevos endpoints |
| `apps/expedientes/admin.py` | Actualizar filtros + read-only fields |
| `backend/tests/test_sprint25.py` | CREAR — 56 tests |

## ARCHIVOS QUE NO PODÉS TOCAR

- `apps/expedientes/services/state_machine/` handlers de transición (FROZEN)
- `apps/expedientes/services/pricing/` (pricing engine S22 — deferred es independiente)
- `docker-compose.yml`

## VERIFICACIÓN ANTES DE HACER PR

```bash
# 1. Migración limpia
python manage.py sqlmigrate expedientes XXXX  # solo AddField
python manage.py migrate
python manage.py check

# 2. Tests
pytest backend/tests/test_sprint25.py -v  # 56/56

# 3. Tests existentes sin regresión
pytest backend/ -v  # 0 failures

# 4. Seguridad
bandit -ll backend/  # 0 high/critical

# 5. Grep de sanidad
grep -rn "from apps.expedientes.models import" backend/apps/expedientes/migrations/  # debe ser 0
grep -rn "ENTREGADO" backend/  # debe ser 0
grep -rn "bulk_credit_released" backend/  # debe ser 0
grep -rn "skipped_non_verified" backend/  # debe ser 0
```

## SI TENÉS DUDAS

- Sobre migración legacy: leer C2 del LOTE (es el SSOT)
- Sobre state machine: leer ENT_OPS_STATE_MACHINE (FROZEN, no cambiar)
- Sobre tiering portal: leer S25-08 fix M2 R3 del LOTE
- Sobre invariante deferred: leer S25-06 fix M1 R6 del LOTE
- Sobre compute_coverage: leer S25-05 fix M1 R4+R5 del LOTE
- Sobre cualquier decisión marcada DEC-*: ya está resuelta, no preguntar de nuevo
- Sobre algo no cubierto: preguntale al CEO, no adivines
