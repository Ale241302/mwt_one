# GUIA_ALE_SPRINT25 — Sprint 25: Payment Status + Deferred + Parent/Child

Ale, este sprint agrega el flujo real de pagos, el precio diferido, y la relación padre/hijo cuando separás productos. Son tres cosas que el CEO necesita para operar como lo hacía en el sistema viejo.

---

## El cambio en una frase

**Antes:** Un pago existía como un número plano — o pagado o no.
**Después:** Un pago tiene ciclo de vida (pendiente → verificado → crédito liberado), el expediente tiene un precio diferido que el CEO controla, y al separar productos podés invertir quién es padre y quién hijo.

---

## Qué vas a construir (en orden)

### Fase 0 — Modelo de datos (migración)

1. **6 campos nuevos en ExpedientePago** — payment_status (con default 'pending'), verified_at, verified_by, credit_released_at, credit_released_by, rejection_reason. Timestamps y FKs son nullable. payment_status tiene default. rejection_reason es blank.

2. **4 campos nuevos en Expediente** — deferred_total_price (nullable decimal), deferred_visible (bool, default false), parent_expediente (FK a self, nullable), is_inverted_child (bool, default false).

3. **Data migration para pagos legacy** — usa `apps.get_model()`, NO importes el modelo vivo. Los status para GATE_PASSED son strings congelados: `{"PRODUCCION", "PREPARACION", "DESPACHO", "TRANSITO", "EN_DESTINO", "CERRADO"}`. OJO: el estado se llama `EN_DESTINO`, NO `ENTREGADO`. La migración es forward-only, reverse=noop. Hacé backup de la tabla antes.

### Fase 1 — Endpoints backend

4. **Verify + Reject** — dos POSTs en `/pagos/{id}/verify/` y `/pagos/{id}/reject/`. Ambos lockean Expediente + Pago con `select_for_update()`. Reject requiere `reason` obligatorio. Reject dispara recalculate_credit. Ambos crean EventLog.

5. **Release credit** — POST individual + POST bulk `/release-all-verified/`. El bulk:
   - Lockea expediente + pagos (verified + credit_released)
   - Libera solo los verified → credit_released
   - `already_released` = los que ya estaban en credit_released
   - 1 EventLog por pago con `payload.bulk=true`
   - `recalculate_expediente_credit()` corre UNA vez al final, no por cada pago
   - Response: `{ released: N, already_released: N }`

6. **compute_coverage()** — función nueva que es SSOT para `payment_coverage` + `coverage_pct`. Edge cases importantes:
   - `expediente_total = None o 0` → return `('none', Decimal("0.00"))` inmediatamente (early return)
   - Redondeo: `ROUND_HALF_UP` explícito
   - Cap: 100.00
   - `recalculate_expediente_credit()` DEBE llamar esta función, no calcular aparte

7. **PATCH deferred-price** — endpoint con invariante de precedencia:
   - `{price: null, visible: true}` → **400 error duro** (NO auto-corrección)
   - `{price: null}` solo → auto-corrige visible=false, OK 200
   - `{visible: true}` cuando precio existente es null → 400
   - Usá un sentinel `_MISSING = object()` para distinguir "no enviado" de "enviado como null"

8. **Separate-products con inversión** — agregar `invert_parent: bool` al endpoint existente. Si `invert_parent=true` y el expediente ya es child → 409. EventLog en AMBOS expedientes.

9. **Bundle tiered** — dos serializers separados:
   - **CEO/AGENT_***: todo (snapshot monetario completo, deferred siempre, children, inversión)
   - **CLIENT_***: solo `payment_coverage` + `coverage_pct` en credit (SIN montos). Solo deferred_total_price si visible=True. Solo parent number. Sin rejection_reason, sin verified_by, sin credit_released_by.

### Fase 3 — Tests

10. **56 tests** — ver lista completa en LOTE_SM_SPRINT25 v1.6 §S25-14. Los que no podés saltarte:
    - Test 46: GATE_PASSED_STATUSES congelados es subconjunto del enum real
    - Tests 48-50: invariante deferred (3 escenarios)
    - Tests 51-52: tiering portal (sin montos + contrato exacto)
    - Tests 53-54: compute_coverage con total=0 y total=None
    - Test 55: payload contradictorio deferred → 400
    - Test 56: ROUND_HALF_UP con valor que fuerza redondeo

---

## Reglas que no podés romper

1. **State machine FROZEN** — no toques handlers de transición. Payment status es interno a ExpedientePago, no al state machine del expediente.

2. **Backward compat** — POST pagos existente sin payment_status sigue funcionando (default='pending').

3. **Migración additive-only** — solo AddField. Verificá con `sqlmigrate`. Si ves AlterField o RemoveField → PARAR.

4. **Migración con apps.get_model()** — NO importar el modelo vivo en la data migration. Strings congelados.

5. **CreditOverride intocable** — si hay override, respetarlo sin importar payment_status.

6. **Transiciones terminales** — rejected y credit_released no tienen vuelta atrás.

7. **Deferred independiente** — no interactúa con resolve_client_price() ni pricing engine.

8. **Tiering con serializer separado** — no filtrar post-serialización. CLIENT_* nunca debe recibir montos de crédito.

---

## Archivos que vas a tocar

| Archivo | Qué hacer |
|---------|-----------|
| `apps/expedientes/models.py` | +6 campos ExpedientePago, +4 campos Expediente |
| `apps/expedientes/services/credit.py` | +compute_coverage(), extender recalculate |
| `apps/expedientes/views/payment_status.py` | CREAR — verify, reject, release, release_all |
| `apps/expedientes/views/deferred.py` | CREAR — patch_deferred_price |
| `apps/expedientes/serializers.py` | +CEO/portal serializers separados |
| `apps/expedientes/views.py` | Extender separate-products |
| `apps/expedientes/urls.py` | Registrar nuevos endpoints |
| `apps/expedientes/admin.py` | Filtros + read-only |
| `backend/tests/test_sprint25.py` | CREAR — 56 tests |

## Archivos que NO podés tocar

- `apps/expedientes/services/state_machine/` (FROZEN)
- `apps/expedientes/services/pricing/` (S22 — deferred es independiente)
- `docker-compose.yml`

---

## Verificación antes de hacer PR

```bash
# 1. Migración limpia
python manage.py sqlmigrate expedientes XXXX  # solo AddField
python manage.py migrate
python manage.py check

# 2. Tests
pytest backend/tests/test_sprint25.py -v  # 56/56

# 3. Sin regresiones
pytest backend/ -v  # 0 failures

# 4. Grep de sanidad
grep -rn "from apps.expedientes.models import" backend/apps/expedientes/migrations/  # 0
grep -rn "ENTREGADO" backend/  # 0
grep -rn "bulk_credit_released" backend/  # 0
grep -rn "skipped_non_verified" backend/  # 0
```

---

## Orden sugerido (5 días AG-02)

- **Día 1:** S25-01 + S25-02 (modelos + migraciones)
- **Día 2:** S25-03 + S25-04 (verify/reject/release endpoints)
- **Día 3:** S25-05 + S25-06 (compute_coverage + recalculate + deferred con invariante)
- **Día 4:** S25-07 + S25-08 (split inversión + bundle tiered)
- **Día 5:** Tests (56) + verificación final

---

## Si tenés dudas

- Migración legacy → leer C2 del LOTE (es el SSOT único)
- State machine → leer ENT_OPS_STATE_MACHINE (FROZEN)
- Invariante deferred → leer S25-06 del LOTE (precedencia M1 R6)
- compute_coverage → leer S25-05 del LOTE (early return + ROUND_HALF_UP)
- Tiering portal → leer S25-08 del LOTE (contrato M2 R3)
- Decisión ya resuelta → no preguntar de nuevo
- Algo no cubierto → preguntale al CEO, no adivines
