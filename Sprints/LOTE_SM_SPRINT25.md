# LOTE_SM_SPRINT25 — Negocio Avanzado: Payment Status Machine + Precio Diferido + Parent/Child
id: LOTE_SM_SPRINT25
version: 1.6
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
status: DRAFT — Pendiente aprobación CEO
stamp: DRAFT v1.6 — 2026-04-07
tipo: Lote ruteado (ref → PLB_ORCHESTRATOR §E)
sprint: 25
priority: P2
depends_on: LOTE_SM_SPRINT18 (DONE — ExpedientePago + separate-products),
            LOTE_SM_SPRINT20 (DONE — proformas como unidad operativa),
            LOTE_SM_SPRINT21 (DONE — EventLog extendido + activity feed),
            LOTE_SM_SPRINT22 (DONE — pricing engine v2)
refs: ENT_OPS_STATE_MACHINE (FROZEN v1.2.2),
      ROADMAP_SPRINTS_17_27 (VIGENTE — Sprint 25 scope),
      ROADMAP_CONVERGENCIA_MWTONE (VIGENTE — Sprint 25 scope),
      ROADMAP_EXTENDIDO_POST_DIRECTRIZ (VIGENTE)

changelog:
  - v1.0 (2026-04-07): Compilación inicial. 17 items en 4 fases. Fuente: ROADMAP_SPRINTS_17_27 (S25) + ROADMAP_CONVERGENCIA_MWTONE (S25). 3 pilares: (A) payment status machine con verificación y liberación de crédito, (B) precio diferido con visibilidad condicional en portal, (C) parent/child con inversión en split. Estado asumido: S18-S24 DONE.
  - v1.1 (2026-04-07): Fixes auditoría R1 (ChatGPT 8.3/10 — 1 bloqueante + 6 mayores). B1: migración legacy unificada en C2 como SSOT — eliminada contradicción entre C2/S25-01/S25-05. M1: contrato action_source cerrado con 5 valores (verify_payment, reject_payment, release_credit, patch_deferred, separate_products) + event_types explícitos. M2: portal pagos recibe los 4 estados incl. rejected (badge sin motivo). M3: locking uniforme — todos los endpoints mutantes lockean Expediente+Pago, incluyendo PATCH deferred. M4: restricción dura en split — invert_parent=true sobre child existente → 409 Conflict. M5: deferred_total_price acepta null explícito, semántica null vs 0 documentada, toggle deshabilitado si null. M6: +15 tests (seguridad CLIENT_*, deferred edge cases, split genealogía, concurrencia). Total: 45 tests backend.
  - v1.2 (2026-04-07): Fixes auditoría R2 (ChatGPT 9.1/10 — 0 bloqueantes, 2 mayores, 3 menores). M1: eliminado event_type `payment.bulk_credit_released` — bulk release genera 1 evento `payment.credit_released` por pago con payload.bulk=true. M2: migración documentada como forward-only, reverse=noop, backup obligatorio pre-ejecución. N1: help_text y criterio de done de S25-01 corregidos para referenciar C2 sin hardcodear destino. N2: GATE_PASSED_STATUSES usa enums canónicos del modelo, no strings literales + test de integridad. N3: "3 valores" → "5 valores" en C5, renumeración S25-07. Total: 47 tests backend.
  - v1.3 (2026-04-07): Fixes auditoría R3 (ChatGPT 9.3/10 — 0 bloqueantes, 2 mayores, 3 menores). M1: invariante backend en S25-06 — si `deferred_total_price` es NULL, forzar `deferred_visible=False`; si se intenta `deferred_visible=True` con precio NULL → ValidationError. 3 tests nuevos (48-50). M2: contrato explícito de tiering CreditBar en S25-08 y S25-10 — CEO/AGENT_* reciben snapshot monetario completo, CLIENT_* solo `payment_coverage` y `%` sin montos. 1 test nuevo (51) + 1 check FE nuevo. N1: nota auditoría 2 reescrita para referenciar C2 como SSOT sin resumirla parcialmente. N2: semántica explícita de `already_released` en S25-04 — el endpoint inspecciona solo pagos `verified` + `credit_released`, no el universo completo; `already_released` = pagos que ya estaban en `credit_released` al momento de la llamada. N3: corregido bug en C2 — `Expediente.Status.ENTREGADO` → `Expediente.Status.EN_DESTINO` (validado contra ENT_OPS_STATE_MACHINE FROZEN v1.2.2: estado 6 = EN_DESTINO, no existe ENTREGADO). Total: 51 tests backend. 15 checks FE.
  - v1.4 (2026-04-07): Fixes auditoría R4 (ChatGPT 9.4/10 — 0 bloqueantes, 1 mayor, 2 menores). M1: `coverage_pct` promovido a campo formal del snapshot en S25-05 con fórmula canónica (total_paid/expediente_total×100), redondeo 2 decimales, cap 100.00, edge case total=0/NULL→0.00. `payment_coverage` y `coverage_pct` DEBEN derivar de la misma función. N1: tests 52-53 nuevos — test 52 verifica presencia exacta del contrato portal (`payment_coverage` + `coverage_pct`, nada más); test 53 verifica que `coverage_pct` coincide con fórmula canónica para los tres escenarios (complete/partial/none). N2: corregida descripción de campos M1 — "todos nullable" → "timestamps/FKs nullable, `payment_status` con default, `rejection_reason` blank". Total: 53 tests backend. 15 checks FE.
  - v1.5 (2026-04-07): Fixes auditoría R5 (ChatGPT 9.2/10 — 0 bloqueantes, 2 mayores, 2 menores). M1: `compute_coverage()` reescrito con early return para edge case `expediente_total=0/NULL` — elimina contradicción prose↔código donde `total_paid>0` + `expediente_total=0` daba `'complete'` en vez de `'none'`. M2: migración C2 reescrita con `apps.get_model()` + strings congelados con comentario de origen FROZEN — elimina import de model vivo (`from apps.expedientes.models import Expediente`) que es frágil en context de migrations Django. N1: test 53 expandido para cubrir explícitamente `expediente_total=None` además de `=0`; nuevo test 54 dedicado. N2: `coverage_pct` agregado a lista inicial del bundle S25-08.1 para eliminar inconsistencia editorial. Total: 54 tests backend. 15 checks FE.
  - v1.6 (2026-04-07): Fixes auditoría R6 (ChatGPT 9.6/10 — 0 bloqueantes, 1 mayor, 2 menores). M1: precedencia explícita en PATCH deferred-price — payload contradictorio (`deferred_total_price=null` + `deferred_visible=true` en misma llamada) es error duro (400), NO auto-corrección silenciosa. Orden: primero validar contradicción → luego auto-corregir null→visible=false → luego validar visible=true contra precio existente. Test 55. N1: `compute_coverage()` usa `ROUND_HALF_UP` explícito en `quantize()` — cierra contrato de redondeo. Test 56 con valor que fuerza redondeo en 3er decimal. N2: pseudocódigo explícito de locking en bulk release — `select_for_update()` sobre queryset `verified`+`credit_released`, `recalculate_expediente_credit()` corre UNA vez post-bulk. Total: 56 tests backend. 15 checks FE.

---

## Contexto

Sprint 25 añade tres capacidades de negocio que faltaban para replicar el sistema viejo: gestión granular de pagos (más allá de "pagado/no pagado"), el concepto de precio diferido que el CEO usa operativamente, y la relación parent/child entre expedientes cuando se hace split.

**Cambio de paradigma en 3 frases:**
1. Los pagos dejan de ser binarios — ahora tienen un ciclo de vida (pendiente → verificado → crédito liberado) que permite al CEO controlar cuándo un pago realmente cuenta para liberar crédito.
2. El precio diferido es un segundo precio del expediente (invisible al cliente por default) que el CEO usa para negociaciones y cálculos internos.
3. Al separar productos de un expediente, el CEO puede invertir la relación parent/child: el expediente "original" se convierte en hijo y el nuevo en padre.

**Estado post-Sprint 24 (asumido DONE):**
- State machine 8 estados, 28+ commands con dispatcher central
- ExpedienteProductLine con FK a ProductMaster + BrandSKU + Proforma
- ExpedientePago funcional (modelo S17, endpoint S18)
- CreditPolicy + CreditExposure + CreditOverride (S16)
- recalculate_expediente_credit (S18-10) con snapshot
- Proforma como unidad operativa con ArtifactPolicy (S20)
- EventLog extendido: user FK, proforma FK, action_source, previous/new status (S21)
- Activity feed con badge y panel (S21)
- Pricing engine v2: resolve_client_price() waterfall 4 pasos (S22)
- Rebates, herencia brand→client→subsidiary, BrandWorkflowPolicy en DB (S23)
- Portal B2B autogestión: catálogo, carrito, pedido→expediente (S24)
- merge/ y separate-products/ endpoints (S18)

**Lo que falta (scope de este sprint):**
- 0 payment_status en ExpedientePago → solo tiene amount + fecha
- 0 flujo de verificación de pago (CEO confirma que el pago es real)
- 0 liberación de crédito condicionada a verificación
- 0 campo deferred_total_price en Expediente
- 0 visibilidad condicional del precio diferido en portal
- 0 parent/child FK entre expedientes
- 0 opción de inversión al hacer split
- recalculate_expediente_credit no distingue pagos verificados de pendientes

---

## Decisiones ya resueltas (NO preguntar de nuevo)

| Decisión | Ref | Detalle |
|----------|-----|---------|
| Proforma como unidad operativa | DIRECTRIZ / S20 | Pagos se registran a nivel expediente, no proforma. |
| State machine FROZEN | ENT_OPS_STATE_MACHINE | No se agregan estados ni transiciones. El payment_status es interno a ExpedientePago, no al state machine del expediente. |
| CreditPolicy es SSOT de crédito | S16 | CreditExposure calcula exposición. CreditOverride permite CEO bypass. |
| Separate-products crea nuevo expediente | S18-06 | El CEO elige qué líneas mover. S25 agrega la opción de invertir parent/child. |
| EventLog append-only | POL_INMUTABILIDAD | Cambios de payment_status se registran como EventLog entries. |
| Merge con master_id | S18-05 | El CEO elige cuál es el master. S25 no modifica merge — solo agrega parent FK a split. |

---

## Convenciones Sprint 25

### C1. State machine FROZEN
No se modifican estados, transiciones ni commands del expediente. El `payment_status` es un campo interno de `ExpedientePago`, no un estado del state machine. No agrega commands.

### C2. Backwards compat con pagos existentes — regla única de migración legacy

Los pagos existentes (pre-S25) no tienen `payment_status`. La data migration en S25-01 los clasifica así:

```python
# DENTRO DE LA MIGRATION — usar apps.get_model(), NO import del model vivo (fix M2 R5).
# Los strings de status están congelados aquí con referencia explícita al SSOT.
# Si el enum cambia en el futuro, esta migración sigue siendo reproducible.

def forwards(apps, schema_editor):
    ExpedientePago = apps.get_model("expedientes", "ExpedientePago")
    Expediente = apps.get_model("expedientes", "Expediente")
    
    # Congelados desde ENT_OPS_STATE_MACHINE FROZEN v1.2.2 — estados post-gate de crédito.
    # NO importar del model vivo: las migrations deben depender del estado histórico.
    GATE_PASSED_STATUSES = {
        "PRODUCCION", "PREPARACION", "DESPACHO",
        "TRANSITO", "EN_DESTINO", "CERRADO",
    }
    
    for pago in ExpedientePago.objects.select_related("expediente").iterator():
        if pago.amount is None or pago.amount <= 0:
            pago.payment_status = 'pending'
        elif pago.expediente.status in GATE_PASSED_STATUSES:
            pago.payment_status = 'credit_released'   # ya pasó gate de crédito → pago cuenta
        else:
            pago.payment_status = 'verified'           # CEO debe liberar manualmente
        pago.save(update_fields=['payment_status'])

# reverse = migrations.RunPython.noop (forward-only, ref C2 §Rollback)
```

**Nota (fix N2 v1.2 + M2 R5):** La migración usa strings congelados con comentario de origen (`ENT_OPS_STATE_MACHINE FROZEN v1.2.2`), no import del model vivo. El test 46 (runtime, no migration) sí importa los enums canónicos del modelo y verifica que el set congelado de la migración es subconjunto del enum — esto detecta si el enum cambia post-migración.

**Rollback (fix M2):** Esta data migration es **forward-only**. La reverse migration es noop (`migrations.RunPython.noop`). Antes de ejecutar en producción: backup obligatorio de la tabla `expedientes_expedientepago`. Si se necesita rollback del release, restaurar tabla desde backup — la migración no es reversible semánticamente porque la clasificación es inferida.

**Esta es la ÚNICA fuente de verdad para migración legacy.** Ninguna otra sección del lote define reglas alternativas. El resultado: expedientes activos (post-gate) no pierden cobertura de crédito; expedientes en estados tempranos requieren liberación manual del CEO.

### C3. CreditPolicy no se modifica
`recalculate_expediente_credit()` se extiende para filtrar solo pagos con `payment_status='credit_released'`. La política crediticia (umbrales, exposure) no cambia.

### C4. Parent/child es metadata, no constraint
El FK `parent_expediente` es informativo para el CEO. No bloquea transiciones, no afecta crédito, no cambia visibility en portal. Es para trazar el origen de un split.

### C5. Extensión del contrato action_source (S21)

S25 extiende el contrato con 5 valores nuevos:

| action_source | Origen | user | event_type |
|---------------|--------|------|------------|
| `verify_payment` | S25-03 verify_payment() | request.user | `payment.verified` |
| `reject_payment` | S25-03 reject_payment() | request.user | `payment.rejected` |
| `release_credit` | S25-04 release_credit() / release_all_verified() | request.user | `payment.credit_released` |
| `patch_deferred` | S25-06 patch_deferred_price() | request.user | `expediente.deferred_price_updated` |
| `separate_products` | S25-07 (extensión del handler S18) | request.user | `expediente.split` |

Todos estos valores se agregan al contrato cerrado de S21+S22. Tests de EventLog obligatorios para cada uno (ref S25-14).

---

## Modelos de datos

### M1. Extensión de ExpedientePago (campos nuevos — AddField)

Campos compatibles con legacy: timestamps y FKs son nullable, `payment_status` tiene default `'pending'`, `rejection_reason` es blank (fix N2 R4).

```python
# backend/apps/expedientes/models.py — agregar a ExpedientePago:

PAYMENT_STATUS_CHOICES = [
    ('pending', 'Pendiente verificación'),
    ('verified', 'Verificado'),
    ('credit_released', 'Crédito liberado'),
    ('rejected', 'Rechazado'),
]

# Campos nuevos (timestamps/FKs nullable, payment_status con default, rejection_reason blank):
payment_status = models.CharField(
    max_length=20,
    choices=PAYMENT_STATUS_CHOICES,
    default='pending',
    help_text="Estado del pago dentro de su ciclo de vida. "
              "pending → verificado por CEO → crédito liberado. "
              "Pagos legacy (pre-S25) migrados según regla C2."
)

verified_at = models.DateTimeField(
    null=True, blank=True,
    help_text="Timestamp de verificación por CEO."
)
verified_by = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.SET_NULL,
    null=True, blank=True,
    related_name='verified_payments',
    help_text="Usuario que verificó el pago."
)

credit_released_at = models.DateTimeField(
    null=True, blank=True,
    help_text="Timestamp de liberación de crédito."
)
credit_released_by = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.SET_NULL,
    null=True, blank=True,
    related_name='released_payments',
    help_text="Usuario que liberó el crédito."
)

rejection_reason = models.TextField(
    blank=True, default='',
    help_text="Motivo de rechazo si payment_status='rejected'."
)
```

### M2. Extensión de Expediente (campos nuevos — AddField)

```python
# backend/apps/expedientes/models.py — agregar a Expediente:

deferred_total_price = models.DecimalField(
    max_digits=14, decimal_places=2,
    null=True, blank=True,
    help_text="Precio diferido del expediente. Uso interno CEO. "
              "Equivale a 'order_full_price_diferido' del sistema viejo. "
              "NULL = no definido. Editable solo por CEO."
)

deferred_visible = models.BooleanField(
    default=False,
    help_text="Si True, el precio diferido es visible en el portal del cliente. "
              "Por default invisible (solo CEO). Toggle manual."
)

parent_expediente = models.ForeignKey(
    'self',
    on_delete=models.SET_NULL,
    null=True, blank=True,
    related_name='child_expedientes',
    help_text="Expediente padre (origen de un split). NULL = expediente original."
)

is_inverted_child = models.BooleanField(
    default=False,
    help_text="True si este expediente fue creado por split con inversión: "
              "el 'nuevo' expediente tomó el rol de padre y el 'original' se convirtió en hijo. "
              "Informativo para el CEO — no afecta lógica de negocio."
)
```

---

## Payment Status Machine (diagrama)

```
                    ┌──────────┐
        POST pago   │ PENDING  │
        ──────────→ │          │
                    └────┬─────┘
                         │
              ┌──────────┼──────────┐
              │ verify   │          │ reject
              ▼          │          ▼
        ┌──────────┐     │    ┌──────────┐
        │ VERIFIED │     │    │ REJECTED │
        │          │     │    │          │
        └────┬─────┘     │    └──────────┘
             │           │         ▲
             │ release    │         │ reject (desde verified)
             ▼           │         │
        ┌──────────┐     │    ┌────┘
        │ CREDIT   │─────┘
        │ RELEASED │
        └──────────┘
```

**Transiciones válidas:**
- `pending` → `verified` (CEO confirma pago real)
- `pending` → `rejected` (CEO rechaza pago falso/incorrecto)
- `verified` → `credit_released` (CEO libera crédito)
- `verified` → `rejected` (CEO descubre problema post-verificación)

**Transiciones inválidas (hard block):**
- `rejected` → cualquiera (pago rechazado es terminal — crear nuevo pago)
- `credit_released` → cualquiera (crédito liberado es terminal — irreversible)
- `pending` → `credit_released` (no se puede saltar verificación)

---

## Items

### FASE 0 — Modelos y migraciones (estimado 1 día)

#### S25-01: Campos payment_status en ExpedientePago
- **Agente:** AG-02 Backend
- **Qué hacer:**
  1. AddField × 6 en ExpedientePago (modelo M1 arriba)
  2. Data migration (regla canónica — ref C2): `amount <= 0 o NULL` → `pending`. `amount > 0` en expediente PRODUCCION+ → `credit_released`. `amount > 0` en expediente pre-PRODUCCION → `verified`
  3. Admin: payment_status visible + filtrable. verified_by y credit_released_by read-only.
- **Criterio de done:**
  - [ ] Migración aplicada sin error
  - [ ] Pagos legacy migrados conforme a C2 (pending/verified/credit_released según estado expediente)
  - [ ] Admin funcional con filtros

#### S25-02: Campos deferred + parent/child en Expediente
- **Agente:** AG-02 Backend
- **Qué hacer:**
  1. AddField × 4 en Expediente (modelo M2 arriba)
  2. 0 data migration — campos nuevos compatibles con legacy (nullable/default/blank según tipo)
  3. Admin: deferred_total_price + deferred_visible editables. parent_expediente + is_inverted_child read-only.
- **Criterio de done:**
  - [ ] Migración aplicada sin error
  - [ ] Campos visibles en Admin

### FASE 1 — Servicios y endpoints backend (estimado 3-4 días)

#### S25-03: Endpoints verificación y rechazo de pago
- **Agente:** AG-02 Backend
- **Dependencia:** S25-01
- **Qué hacer:**
  1. `POST /api/expedientes/{exp_id}/pagos/{pago_id}/verify/`
     - Valida: payment_status == 'pending' (sino 409 Conflict)
     - Actualiza: payment_status='verified', verified_at=now(), verified_by=request.user
     - EventLog: event_type='payment.verified', action_source='verify_payment'
     - NO libera crédito automáticamente (paso separado)
  2. `POST /api/expedientes/{exp_id}/pagos/{pago_id}/reject/`
     - Acepta: `{ reason: string }` (obligatorio)
     - Valida: payment_status in ('pending', 'verified') (sino 409)
     - Actualiza: payment_status='rejected', rejection_reason=reason
     - EventLog: event_type='payment.rejected', action_source='reject_payment'
     - Trigger: `recalculate_expediente_credit()` (quita este pago del cálculo)
  3. **Locking uniforme en AMBOS endpoints (fix M3):**
     ```python
     with transaction.atomic():
         expediente = Expediente.objects.select_for_update().get(id=exp_id)
         pago = ExpedientePago.objects.select_for_update().get(id=pago_id, expediente=expediente)
         # ... mutación + EventLog ...
         recalculate_expediente_credit(expediente)  # ya lockeado
     ```
     El lock sobre Expediente protege el snapshot de crédito de concurrent updates.
  4. Permisos: CEO only (IsCEOOrSuperuser)
- **Criterio de done:**
  - [ ] Verify: pending → verified OK
  - [ ] Verify: non-pending → 409
  - [ ] Reject: pending/verified → rejected OK
  - [ ] Reject: sin reason → 400
  - [ ] EventLog creado en ambos casos
  - [ ] Locking correcto

#### S25-04: Endpoint liberación de crédito
- **Agente:** AG-02 Backend
- **Dependencia:** S25-03
- **Qué hacer:**
  1. `POST /api/expedientes/{exp_id}/pagos/{pago_id}/release-credit/`
     - Valida: payment_status == 'verified' (sino 409)
     - Actualiza: payment_status='credit_released', credit_released_at=now(), credit_released_by=request.user
     - Trigger: `recalculate_expediente_credit()` (ahora este pago cuenta)
     - EventLog: event_type='payment.credit_released', action_source='release_credit'
  2. `transaction.atomic()` + `select_for_update()` en ExpedientePago + Expediente
  3. Permisos: CEO only
  4. Opción bulk: `POST /api/expedientes/{exp_id}/pagos/release-all-verified/`
     - Libera crédito de TODOS los pagos verified del expediente en una transacción
     - **EventLog (fix M1):** un evento `payment.credit_released` por cada pago liberado (con `payload.bulk=true`). NO existe `payment.bulk_credit_released` — es el mismo event_type que release individual. Esto mantiene el activity feed granular y auditable.
     - **Conjunto base y semántica del response (fix N2 R3):** el endpoint inspecciona pagos en estados `verified` y `credit_released` del expediente. Pagos `pending` y `rejected` se ignoran silenciosamente (no aparecen en el response). Definición de cada campo:
       - `released`: pagos que estaban en `verified` y fueron transicionados a `credit_released` en esta llamada
       - `already_released`: pagos que ya estaban en `credit_released` al momento de la llamada (idempotencia — no se reprocesan)
       - `skipped_non_verified`: NO existe en el response. Si se necesitara contar pagos en otros estados, agregar en sprint futuro. El endpoint es `release-all-verified/`, no `release-all/`.
     - **Pseudocódigo bulk con locking explícito (fix N2 R6):**
       ```python
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
                   pago.credit_released_at = now()
                   pago.credit_released_by = request.user
                   pago.save(update_fields=['payment_status', 'credit_released_at', 'credit_released_by'])
                   EventLog.objects.create(
                       event_type='payment.credit_released',
                       action_source='release_credit',
                       user=request.user,
                       payload={'bulk': True, 'pago_id': pago.id},
                   )
                   released += 1
           # Recálculo UNA vez post-bulk, no por cada pago
           recalculate_expediente_credit(expediente)
       ```
     - Response: `{ released: N, already_released: N }`
- **Criterio de done:**
  - [ ] Release: verified → credit_released OK
  - [ ] Release: non-verified → 409
  - [ ] recalculate_expediente_credit() se ejecuta post-release
  - [ ] Bulk release funcional
  - [ ] EventLog registra cada liberación

#### S25-05: Extender recalculate_expediente_credit()
- **Agente:** AG-02 Backend
- **Dependencia:** S25-01
- **Qué hacer:**
  1. Modificar `recalculate_expediente_credit()` en `backend/apps/expedientes/services/`
  2. Cambio clave: solo sumar pagos con `payment_status='credit_released'`
     - Antes: `sum(pago.amount for pago in expediente.pagos.all())`
     - Ahora: `sum(pago.amount for pago in expediente.pagos.filter(payment_status='credit_released'))`
  3. Nuevo campo en snapshot de crédito:
     ```python
     {
         'total_paid': Decimal,           # solo credit_released
         'total_pending': Decimal,         # pending + verified (no cuenta aún)
         'total_rejected': Decimal,        # rechazados (informativo)
         'credit_exposure': Decimal,       # CreditExposure calculada
         'credit_available': Decimal,      # CreditPolicy.limit - exposure
         'payment_coverage': str,          # 'complete' | 'partial' | 'none'
         'coverage_pct': Decimal,          # porcentaje de cobertura (fix M1 R4)
     }
     ```
  4. `payment_coverage` y `coverage_pct` — **fórmula canónica, misma función (fix M1 R4):**
     
     ```python
     def compute_coverage(total_paid: Decimal, expediente_total: Decimal | None) -> tuple[str, Decimal]:
         """Retorna (payment_coverage, coverage_pct). SSOT para ambos campos.
         
         Edge case: si expediente_total es None o <= 0, retorna ('none', 0.00)
         inmediatamente — no hay denominador válido para calcular cobertura.
         Esto aplica incluso si total_paid > 0 (fix M1 R5).
         """
         # Early return: sin denominador válido, no hay cobertura posible
         if expediente_total is None or expediente_total <= 0:
             return 'none', Decimal("0.00")
         
         # Denominador válido — calcular porcentaje
         # ROUND_HALF_UP explícito para contrato determinista (fix N1 R6)
         from decimal import ROUND_HALF_UP
         coverage_pct = min(
             Decimal("100.00"),
             ((total_paid / expediente_total) * Decimal("100")).quantize(
                 Decimal("0.01"), rounding=ROUND_HALF_UP
             )
         )
         
         # Clasificación semántica
         if total_paid <= 0:
             payment_coverage = 'none'
         elif total_paid >= expediente_total:
             payment_coverage = 'complete'
         else:
             payment_coverage = 'partial'
         
         return payment_coverage, coverage_pct
     ```
     
     **Reglas de `coverage_pct`:**
     - Denominador: `expediente.total_value` (campo existente — precio total del expediente)
     - Redondeo: 2 decimales, `ROUND_HALF_UP` explícito (fix N1 R6)
     - Cap: 100.00 (sobrepago no muestra >100%)
     - Edge case: `expediente_total` es 0 o NULL → early return `('none', 0.00)` — incluso si `total_paid > 0` (fix M1 R5)
     - `payment_coverage` y `coverage_pct` DEBEN derivar de `compute_coverage()` — nunca calcular por separado
  5. Backwards compat: la data migration de S25-01 (ref C2) ya clasificó pagos legacy correctamente. `recalculate_expediente_credit()` no necesita lógica especial para legacy — solo filtra por `payment_status='credit_released'` y la migración ya los puso ahí si corresponde.
- **Criterio de done:**
  - [ ] Solo pagos credit_released cuentan para crédito
  - [ ] Snapshot incluye total_pending y total_rejected
  - [ ] payment_coverage correcto (complete/partial/none)
  - [ ] Expedientes activos no se rompen por la migración

#### S25-06: Endpoints deferred price
- **Agente:** AG-02 Backend
- **Dependencia:** S25-02
- **Qué hacer:**
  1. `PATCH /api/expedientes/{exp_id}/deferred-price/`
     - Payload: `{ deferred_total_price: Decimal|null, deferred_visible: bool }`
     - `deferred_total_price=null` → limpia el campo (vuelve a "no definido"). `0.00` es valor válido, distinto de null.
     - Ambos campos opcionales (PATCH parcial)
     - Permisos: CEO only
     - **Locking (fix M3):** `transaction.atomic()` + `select_for_update()` en Expediente
     - EventLog: event_type='expediente.deferred_price_updated', action_source='patch_deferred'
  2. Bundle de detalle del expediente: incluir `deferred_total_price` y `deferred_visible` SOLO si el caller es CEO/AGENT_*
  3. Portal endpoint: incluir `deferred_total_price` SOLO si `deferred_visible=True`
  4. Validación: deferred_total_price >= 0 si se provee
  5. **Invariante backend (fix M1 R3 + M1 R6):** cerrar la regla en backend, no solo en frontend.
     
     **Precedencia explícita (fix M1 R6):** payload contradictorio (`null` + `true` en misma llamada) es error duro, NO auto-corrección silenciosa. Orden de evaluación:
     ```python
     # En el handler de PATCH, ANTES de guardar:
     
     # Paso 1: payload contradictorio explícito → error duro (fix M1 R6)
     if (
         'deferred_total_price' in validated_data
         and validated_data['deferred_total_price'] is None
         and validated_data.get('deferred_visible') is True
     ):
         raise ValidationError(
             "Cannot set deferred_visible=True and deferred_total_price=null in the same request."
         )
     
     # Paso 2: si se está seteando precio a NULL (sin visible=true), auto-corregir
     if 'deferred_total_price' in validated_data and validated_data['deferred_total_price'] is None:
         validated_data['deferred_visible'] = False
     
     # Paso 3: si se está activando visible en PATCH parcial, verificar precio existente
     current_price = validated_data.get('deferred_total_price', expediente.deferred_total_price)
     if validated_data.get('deferred_visible', False) and current_price is None:
         raise ValidationError("Cannot set deferred_visible=True when deferred_total_price is null.")
     ```
     
     **Resumen de comportamiento:**
     - `{price: null}` → auto-corrige visible=false. OK 200.
     - `{visible: true}` (precio existente null) → 400.
     - `{price: null, visible: true}` → 400 (paso 1, error duro).
     - `{price: null, visible: false}` → OK 200.
     - `{price: 10.00, visible: true}` → OK 200.
- **Criterio de done:**
  - [ ] PATCH funcional, ambos campos editables
  - [ ] Bundle CEO incluye deferred siempre
  - [ ] Portal incluye deferred SOLO si visible=True
  - [ ] Portal NUNCA incluye deferred_visible (el cliente no sabe que existe el toggle)
  - [ ] PATCH `deferred_total_price=null` fuerza `deferred_visible=false` automáticamente
  - [ ] PATCH `deferred_visible=true` con precio null → 400 ValidationError
  - [ ] Portal nunca recibe `deferred_total_price=null` con `deferred_visible=true`

#### S25-07: Extender separate-products con parent/child + inversión
- **Agente:** AG-02 Backend
- **Dependencia:** S25-02
- **Qué hacer:**
  1. Extender endpoint `POST /api/expedientes/{exp_id}/separate-products/`
  2. Nuevo campo en payload: `invert_parent: bool` (default false)
  3. **Restricción: no invertir si ya es child (fix M4).** Si `expediente.parent_expediente_id is not None` y `invert_parent=True` → 409 Conflict con error: "Cannot invert parent on an expediente that is already a child. Split normally or create a new top-level expediente." Esto evita sobrescribir la genealogía y perder trazabilidad.
  4. Lógica normal (`invert_parent=false`):
     - Expediente original = padre (no cambia)
     - Nuevo expediente = hijo (parent_expediente = original, is_inverted_child = false)
  5. Lógica invertida (`invert_parent=true`, solo si original no tiene parent):
     - Nuevo expediente = padre (parent_expediente = NULL)
     - Expediente original = hijo (parent_expediente = nuevo, is_inverted_child = true)
     - **Swap dentro de la misma transacción:** primero crear nuevo, luego actualizar original
  6. EventLog en ambos expedientes: event_type='expediente.split', action_source='separate_products', payload incluye `{ parent_id, child_id, inverted: bool, lines_moved: [...] }`
  7. `transaction.atomic()` + `select_for_update()` en ambos expedientes
  8. Backwards compat: llamadas sin `invert_parent` → comportamiento normal (hijo apunta a padre)
- **Criterio de done:**
  - [ ] Split normal: hijo.parent_expediente = padre
  - [ ] Split invertido: padre.parent_expediente = hijo (original se convierte en child)
  - [ ] is_inverted_child = True en el expediente que cambió de rol
  - [ ] EventLog en ambos expedientes
  - [ ] Backwards compat: payload sin invert_parent → OK

#### S25-08: Bundle de detalle extendido
- **Agente:** AG-02 Backend
- **Dependencia:** S25-01 a S25-07
- **Qué hacer:**
  1. Actualizar `GET /api/ui/expedientes/{id}/` bundle:
     - Pagos: agregar `payment_status`, `verified_at`, `verified_by_display`, `credit_released_at`, `rejection_reason`
     - Credit snapshot: agregar `total_pending`, `total_rejected`, `payment_coverage`, `coverage_pct`
     - Deferred: agregar `deferred_total_price`, `deferred_visible` (CEO only)
     - Parent/child: agregar `parent_expediente` (id + number), `child_expedientes` (list), `is_inverted_child`
  2. Portal bundle: pagos muestra `amount`, `date`, `payment_status` (los 4 valores: pending/verified/credit_released/rejected). CLIENT_* VE el badge de rejected pero NUNCA ve: `rejection_reason`, `verified_by`, `credit_released_by`. El estado rejected es informativo — el cliente sabe que su pago fue rechazado pero no el motivo interno.
  3. Parent/child en portal: solo `parent_expediente.number` si existe (informativo)
  4. **Contrato explícito de tiering credit snapshot (fix M2 R3):**
     - **CEO / AGENT_*:** reciben snapshot completo: `total_paid`, `total_pending`, `total_rejected`, `credit_exposure`, `credit_available`, `payment_coverage`, `coverage_pct`
     - **CLIENT_*:** reciben SOLO `payment_coverage` (string: complete/partial/none) y `coverage_pct` (número 0-100). Sin `total_paid`, sin `total_pending`, sin `credit_available`, sin `credit_exposure`. Esto se implementa con serializer separado (patrón S22-C5), no con filtrado post-serialización.
     - Justificación: montos internos de crédito son CEO-ONLY. El cliente solo necesita saber si su cobertura es completa, parcial o nula — nunca los montos detrás del cálculo.
- **Criterio de done:**
  - [ ] Bundle CEO tiene todos los campos nuevos
  - [ ] Bundle portal filtra campos sensibles
  - [ ] Serializers separados por tier (patrón S22-C5)
  - [ ] Bundle portal credit snapshot solo contiene `payment_coverage` + `coverage_pct` (sin montos)

### FASE 2 — Frontend (estimado 3-4 días)

#### S25-09: Sección pagos con status y acciones
- **Agente:** AG-03 Frontend
- **Dependencia:** S25-03, S25-04, S25-08
- **Qué hacer:**
  1. Tabla de pagos: agregar columna "Estado" con badge por payment_status:
     - `pending` → badge amarillo "Pendiente"
     - `verified` → badge azul "Verificado"
     - `credit_released` → badge verde "Crédito liberado"
     - `rejected` → badge rojo "Rechazado" + tooltip con reason
  2. Acciones por pago (botones inline, CEO only):
     - Pending: [Verificar] [Rechazar]
     - Verified: [Liberar crédito] [Rechazar]
     - Credit released: sin acciones (terminal)
     - Rejected: sin acciones (terminal) + motivo visible
  3. Botón "Rechazar" → modal con textarea "Motivo de rechazo" (required)
  4. Botón "Liberar todos los verificados" en header de sección (bulk action)
  5. Summary row: "Pagado (liberado): $X | Pendiente verificación: $Y | Rechazado: $Z"
- **Criterio de done:**
  - [ ] Badges de status correctos
  - [ ] Acciones visibles solo para CEO
  - [ ] Modal de rechazo con motivo
  - [ ] Bulk release funcional
  - [ ] Summary row con 3 totales

#### S25-10: Credit bar actualizada
- **Agente:** AG-03 Frontend
- **Dependencia:** S25-05, S25-08
- **Qué hacer:**
  1. Actualizar CreditBar (componente existente de S16) para mostrar payment_coverage:
     - `complete` → barra verde "Pagado completo"
     - `partial` → barra amarilla con % de cobertura
     - `none` → barra roja "Sin pagos liberados"
  2. **Tooltip tiered por rol (fix M2 R3):**
     - **CEO / AGENT_*:** tooltip monetario completo: "Liberado: $X de $Y (Z%)" + "Pendiente verificación: $W"
     - **CLIENT_* (portal):** tooltip solo textual: "Cobertura: Z%" — sin montos, sin `$X`, sin `$W`. El componente CreditBar en portal consume solo `payment_coverage` y `coverage_pct` del bundle (ref S25-08 fix M2).
  3. Si hay pagos `pending` o `verified` → nota sutil: "Hay pagos pendientes de liberar" (CEO only — portal no muestra esta nota)
- **Criterio de done:**
  - [ ] CreditBar refleja solo pagos credit_released
  - [ ] Tooltip CEO: monetario completo
  - [ ] Tooltip portal: solo % sin montos
  - [ ] Nota de pagos pendientes visible solo para CEO
  - [ ] Portal CreditBar no muestra montos de crédito en ningún elemento (tooltip, label, aria)

#### S25-11: Toggle y display precio diferido
- **Agente:** AG-03 Frontend
- **Dependencia:** S25-06, S25-08
- **Qué hacer:**
  1. Sección "Precio diferido" en detalle expediente (CEO only):
     - Input numérico para `deferred_total_price` (editable inline)
     - **Semántica null vs 0 (fix M5):** input vacío → enviar `null` (no definido). `0.00` es un valor válido y distinto. Botón "✕ Limpiar" junto al input para volver a null explícitamente.
     - Toggle "Visible para cliente" → `deferred_visible`
     - Label: si visible → "El cliente ve este precio en su portal" (verde)
     - Label: si no visible → "Solo visible internamente" (gris)
     - Si `deferred_total_price` es null → toggle deshabilitado con tooltip "Define un precio diferido primero"
  2. Guardar: PATCH al endpoint S25-06 on blur / on toggle change
  3. Portal: si deferred_visible=True → mostrar "Precio acordado: $X" en la vista de expediente del cliente. No mostrar el toggle ni la opción de editar.
- **Criterio de done:**
  - [ ] Input + toggle funcional para CEO
  - [ ] PATCH se envía correctamente
  - [ ] Portal muestra precio solo si visible=True
  - [ ] Portal no muestra toggle ni hint de "diferido"

#### S25-12: Banner parent/child + inversión en split
- **Agente:** AG-03 Frontend
- **Dependencia:** S25-07, S25-08
- **Qué hacer:**
  1. Banner en header del expediente si tiene parent o children:
     - Tiene parent: "🔗 Separado de Expediente #{parent.number}" (link clicable)
     - Tiene children: "🔗 Expedientes derivados: #{child1.number}, #{child2.number}" (links)
     - Si is_inverted_child: agregar "(inversión)" al banner del hijo
  2. Modal "Separar productos" (existente de S19-07): agregar checkbox:
     - "☐ Invertir relación: el nuevo expediente será el principal"
     - Tooltip explicativo: "Marcar si el expediente nuevo debe considerarse el pedido principal y el actual pasa a ser derivado."
  3. Enviar `invert_parent: true/false` en payload de separate-products
- **Criterio de done:**
  - [ ] Banner parent visible con link
  - [ ] Banner children visible con links
  - [ ] Banner inversión visible cuando aplica
  - [ ] Checkbox inversión en modal split
  - [ ] Payload envía invert_parent

#### S25-13: Vista portal pagos (CLIENT_*)
- **Agente:** AG-03 Frontend
- **Dependencia:** S25-08
- **Qué hacer:**
  1. En portal del cliente, sección pagos del expediente:
     - Lista simplificada: fecha, monto, estado (badge)
     - CLIENT_* NUNCA ve: verified_by, rejection_reason detallado, credit_released_by
     - Si rejected: solo badge rojo "Rechazado" sin detalle
  2. Si deferred_visible=True: mostrar precio diferido como "Precio acordado: $X" (sin label "diferido")
  3. Sin acciones para el cliente — solo lectura
- **Criterio de done:**
  - [ ] Lista de pagos con badges
  - [ ] Sin campos sensibles
  - [ ] Precio diferido visible solo si toggle activo

### FASE 3 — Tests y QA (estimado 1-2 días)

#### S25-14: Tests backend (28+)

```python
# Tests obligatorios (28 mínimo, 56 con fixes R1-R6)

# Payment status transitions
1. pending → verified OK ✓
2. pending → rejected OK (con reason) ✓
3. verified → credit_released OK ✓
4. verified → rejected OK ✓
5. rejected → verify → 409 ✓
6. rejected → release → 409 ✓
7. credit_released → reject → 409 ✓
8. credit_released → verify → 409 ✓
9. pending → credit_released (skip verify) → 409 ✓
10. reject sin reason → 400 ✓

# EventLog
11. verify → EventLog con action_source='verify_payment' ✓
12. reject → EventLog con action_source='reject_payment' ✓
13. release → EventLog con action_source='release_credit' ✓

# recalculate_expediente_credit
14. Solo pagos credit_released cuentan en crédito ✓
15. Pago pending + verified → NO cuentan ✓
16. Pago rejected → NO cuenta ✓
17. payment_coverage='complete' cuando total_paid >= total ✓
18. payment_coverage='partial' cuando 0 < total_paid < total ✓
19. payment_coverage='none' cuando total_paid == 0 ✓
20. Bulk release-all-verified → N pagos released + recalculate ✓

# Deferred price
21. PATCH deferred_total_price OK ✓
22. PATCH deferred_visible toggle OK ✓
23. Bundle CEO incluye deferred siempre ✓
24. Portal incluye deferred SOLO si visible=True ✓
25. Portal NO incluye deferred_visible ni label "diferido" ✓

# Parent/child + inversión
26. Split normal → child.parent_expediente = original ✓
27. Split inverted → original.parent_expediente = nuevo, is_inverted_child=True ✓
28. Split sin invert_parent → backwards compat OK ✓

# Data migration
29. Pagos legacy (pre-S25) migrados a 'verified' (expediente pre-PRODUCCION) ✓
30. Pagos legacy en expedientes PRODUCCION+ migrados a 'credit_released' ✓
31. Pagos legacy con amount=0 → 'pending' ✓
32. Pagos legacy con amount=NULL → 'pending' ✓

# Seguridad y permisos (fix M6)
33. CLIENT_* → 403 en verify endpoint ✓
34. CLIENT_* → 403 en reject endpoint ✓
35. CLIENT_* → 403 en release-credit endpoint ✓
36. CLIENT_* → 403 en PATCH deferred-price endpoint ✓

# Deferred edge cases (fix M5, M6)
37. PATCH deferred_total_price=null → campo vuelve a NULL ✓
38. PATCH deferred_total_price=0.00 → valor válido, distinto de null ✓
39. PATCH solo deferred_visible sin deferred_total_price → OK parcial ✓
40. EventLog creado en deferred update ✓

# Split edge cases (fix M4, M6)
41. Split con invert_parent=true sobre expediente ya child → 409 ✓
42. EventLog split creado en AMBOS expedientes (parent y child) ✓

# Concurrencia (fix M3, M6)
43. Doble verify concurrente → una OK, una 409 (select_for_update) ✓
44. Reject concurrente con release sobre mismo pago → una gana, otra 409 ✓
45. Bulk release idempotente: llamar dos veces → segunda retorna released=0 ✓

# Integridad migración (fix N2)
46. GATE_PASSED_STATUSES es subconjunto de Expediente.Status enum canónico ✓
47. Bulk release genera 1 EventLog por pago (no evento agregado) con payload.bulk=true ✓

# Invariante deferred null/visible (fix M1 R3)
48. PATCH deferred_total_price=null → fuerza deferred_visible=false automáticamente ✓
49. PATCH deferred_visible=true con deferred_total_price=null → 400 ValidationError ✓
50. Portal nunca recibe expediente con deferred_total_price=null y deferred_visible=true ✓

# Tiering credit snapshot portal (fix M2 R3 + N1 R4)
51. Bundle portal credit snapshot no contiene total_paid, total_pending, credit_available, credit_exposure ✓
52. Bundle portal credit snapshot contiene exactamente payment_coverage + coverage_pct (nada más) ✓
53. coverage_pct coincide con fórmula canónica compute_coverage() para complete/partial/none + edge case total=0 ✓
54. compute_coverage(total_paid=Decimal("10.00"), expediente_total=None) == ('none', Decimal("0.00")) — edge case NULL explícito (fix N1 R5) ✓

# Precedencia deferred (fix M1 R6)
55. PATCH {"deferred_total_price": null, "deferred_visible": true} → 400 (payload contradictorio, error duro, NO auto-corrección) ✓

# Redondeo determinista (fix N1 R6)
56. compute_coverage(total_paid=Decimal("33.33"), expediente_total=Decimal("100.00")) == ('partial', Decimal("33.33")) — ROUND_HALF_UP verificado con valor que fuerza redondeo ✓
```

#### S25-15: Validación manual frontend

```
Checklist validación manual frontend (15 checks):

# Sección pagos (S25-09)
□ Badges de status correctos (4 colores)
□ Acciones visibles solo para CEO (verify/reject/release)
□ Modal rechazo con motivo obligatorio
□ Bulk "Liberar todos" funcional
□ Summary row con 3 totales

# CreditBar (S25-10)
□ CreditBar refleja solo pagos credit_released
□ Nota "pagos pendientes de liberar" visible cuando aplica

# Precio diferido (S25-11)
□ Input + toggle funcional (CEO only)
□ Portal muestra precio solo si visible=True

# Parent/child (S25-12)
□ Banner parent/child con links clicables
□ Checkbox inversión en modal split
□ Banner "(inversión)" visible cuando aplica

# Portal (S25-13)
□ Lista pagos sin campos sensibles
□ Precio diferido sin label "diferido"

# CreditBar portal (fix M2 R3)
□ CreditBar portal muestra solo % sin montos en tooltip, label ni aria
```

---

## Seguridad (ref → ENT_PLAT_SEGURIDAD)

| Aspecto | Evaluación | Acción |
|---------|-----------|--------|
| Payment status mutation | CEO-ONLY | verify/reject/release detrás de IsCEOOrSuperuser. CLIENT_* no puede mutar pagos. |
| Deferred price | CEO-ONLY | PATCH deferred solo para CEO. Portal recibe valor final solo si visible=True. |
| Rejection reason | INTERNAL | CLIENT_* no ve el motivo de rechazo (puede contener info sensible). |
| Parent/child links | INTERNAL | Portal ve solo number del parent. No ve children ni inversión flag. |
| Bulk release | Operación masiva | Auditada en EventLog. Rate limit no necesario (CEO only, operación infrecuente). |
| CreditBar data | Tiered (fix M2 R3) | CEO/AGENT_*: `total_paid`, `total_pending`, `credit_available`, `credit_exposure`, `payment_coverage`, `coverage_pct`. CLIENT_*: SOLO `payment_coverage` + `coverage_pct`. Serializer separado por tier — no filtrado post-serialización. Tooltip portal: solo "Cobertura: Z%", sin montos. |

**Sin nuevos canales de acceso externo.** Todas las mutaciones son CEO-only. El portal solo ve datos filtrados.

---

## Gate Sprint 25

- [ ] Payment status machine funcional (pending → verified → credit_released)
- [ ] Pagos rejected son terminales con motivo
- [ ] recalculate_expediente_credit solo cuenta pagos credit_released
- [ ] payment_coverage (complete/partial/none) correcto
- [ ] Bulk release-all-verified funcional
- [ ] Deferred total price editable por CEO
- [ ] Deferred visible en portal solo con toggle activo
- [ ] Invariante backend: deferred_total_price=null → deferred_visible=false; visible=true con null → 400 (fix M1 R3)
- [ ] Parent/child FK funcional en split
- [ ] Inversión de parent/child funcional
- [ ] Banner parent/child visible con links
- [ ] Data migration backwards compat (pagos legacy → verified/credit_released según estado expediente, ref C2)
- [ ] 56 tests backend verdes
- [ ] 15 checks validación manual FE
- [ ] Credit snapshot portal no contiene montos internos (fix M2 R3)
- [ ] coverage_pct definido en snapshot con fórmula canónica, cap 100, edge case 0/NULL con early return (fix M1 R4+R5)
- [ ] Migración C2 usa apps.get_model() + strings congelados, no import model vivo (fix M2 R5)
- [ ] PATCH deferred payload contradictorio (null+true) → 400, no auto-corrección (fix M1 R6)
- [ ] 0 regresiones en tests existentes

---

## Excluido explícitamente

- **Payment plan / cuotas** → post-MVP. S25 es status por pago individual, no un plan de pagos.
- **Pago parcial automático** → un pago es un monto fijo. No se divide automáticamente.
- **Merge de crédito entre expedientes** → no aplica. Crédito es por cliente (CreditPolicy), no por expediente.
- **Notificaciones email por payment status** → usa EventLog + activity feed (S21). Email dedicado en sprint futuro.
- **Parent/child cascade** → cambiar estado del padre NO cambia estado de hijos. Son independientes.
- **Deferred price en proforma** → solo a nivel expediente. Si se necesita por proforma → sprint futuro.

---

## Dependencias internas

```
S25-01 (payment_status) → S25-03 (verify/reject endpoints)
S25-01 (payment_status) → S25-05 (recalculate_credit)
S25-02 (deferred + parent) → S25-06 (deferred endpoint)
S25-02 (deferred + parent) → S25-07 (split con inversión)
S25-03 (verify/reject) → S25-04 (release-credit)
S25-04 (release-credit) → S25-05 (recalculate trigger)
S25-05 (recalculate) → S25-08 (bundle actualizado)
S25-06 (deferred endpoint) → S25-08 (bundle)
S25-07 (split inversión) → S25-08 (bundle)
S25-08 (bundle) → S25-09..S25-13 (todos los FE)

Orden sugerido:
  AG-02 Día 1: S25-01 + S25-02 (modelos + migraciones)
  AG-02 Día 2: S25-03 + S25-04 (verify/reject/release endpoints)
  AG-02 Día 3: S25-05 + S25-06 (recalculate + deferred endpoint)
  AG-02 Día 4: S25-07 + S25-08 (split inversión + bundle actualizado)
  AG-03 Día 1-2: S25-09 + S25-10 (pagos UI + CreditBar)
  AG-03 Día 3: S25-11 (deferred price UI)
  AG-03 Día 4: S25-12 + S25-13 (parent/child banner + portal)
  AG-02 Día 5: S25-14 (tests)
  AG-03 Día 5: S25-15 (validación manual FE)
```

---

## Notas para auditoría

1. **Payment status machine es interna a ExpedientePago, no al state machine FROZEN.** No se agregan commands ni transiciones al dispatcher. Los endpoints son CRUD-like sobre el campo payment_status del pago, no operaciones del state machine del expediente.

2. **Data migration con lógica condicional (fix N1 R3):** la regla canónica y única de migración legacy es C2. Los tres casos (`pending`, `verified`, `credit_released`) dependen del monto del pago y del estado del expediente en el momento de la migración. No resumir C2 aquí — consultar C2 directamente para la lógica completa. La migración es forward-only con reverse=noop y backup obligatorio pre-ejecución (ref C2 §Rollback).

3. **Inversión parent/child es informativa:** El FK `parent_expediente` y el flag `is_inverted_child` son metadata para el CEO. No afectan crédito, transiciones, pricing, ni portal. Si en el futuro se necesita cascade (ej: cerrar padre cierra hijos), se agrega en un sprint posterior.

4. **Deferred price es independiente del pricing engine (S22).** No interactúa con `resolve_client_price()`. Es un campo manual del CEO que coexiste con el precio calculado. El portal puede mostrar uno u otro según el toggle.

5. **Backwards compat con CreditOverride (S16):** CreditOverride sigue funcionando. Si el CEO hizo un override manual de crédito, `recalculate_expediente_credit()` respeta el override independientemente del payment_status de los pagos individuales.
