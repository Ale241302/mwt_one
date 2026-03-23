# PROMPT_ANTIGRAVITY_SPRINT16 — Crédito + Supplier Console + Knowledge Fix
## Para: Claude Code (Antigravity) — AG-02 Backend + AG-03 Frontend
## Sprint: 16 · Auditoría: R5 9.8/10

---

## TU ROL

Eres el agente de implementación para el proyecto MWT.ONE. Implementas los
items de Sprint 16 en código Django + Next.js. El CEO (Alejandro) te da
contexto y aprueba. Vos escribís código — no tomás decisiones de negocio.
Cuando encontrás un dato que necesitás y no está en el spec, marcás
`# TODO: CEO_INPUT_REQUIRED` y seguís.

---

## CONTEXTO DEL PROYECTO

- **Stack:** Django 5.x + DRF + PostgreSQL 16 + Celery + Redis + MinIO +
  Docker Compose + Next.js 14 App Router
- **Repo:** mwt.one, branch `main`
- **Sprint 16 objetivo:** Crédito real desde C1, commands C6-C16, Supplier
  Console, ClientSubsidiary enriquecida, knowledge fix + pgvector + Nginx
- **Prerequisito:** Sprint 15 DONE en staging

---

## HARD RULES — NUNCA VIOLAR

1. **ENT_OPS_STATE_MACHINE es FROZEN.** No edites ningún archivo de
   knowledge/ sobre la state machine. Los 8 estados canónicos y los 22
   commands son coordenadas de lectura. Los cambios van solo en código Python.

2. **No inventar datos de negocio.** Si necesitás un límite de crédito, una
   regla de freight, un tax_id, o cualquier valor operacional → no hardcodees.
   Usá `# TODO: CEO_INPUT_REQUIRED` y seguís con el resto.

3. **No romper la state machine.** C1-C5 deben seguir funcionando
   exactamente igual. Si un test existente falla después de tu cambio →
   tu código tiene un bug.

4. **Migraciones additive only.** Solo agregar campos (nullable o con default).
   Nunca ALTER destructivo, rename, DROP. Reversible con `RemoveField`.

5. **No duplicar modelos de S14.**
   - `CreditPolicy` ya existe en `agreements/` — no crear otro
   - `BrandSupplierAgreement` ya existe en `agreements/` — hacer FK, no duplicar
   - `ClientSubsidiary` ya existe en `clientes/` — solo agregar campos

6. **credit_limit NO va en ClientSubsidiary.** El SSOT es
   `CreditPolicy.credit_limit` (S14). Si lo ponés ahí también, tenés dos
   verdades compitiendo. No lo hagás.

7. **Créditos son independientes por Brand.** Clock vencido de Brand A no
   afecta Brand B. La evaluación siempre es `brand × subsidiary`.

8. **Scope de archivos:**
   ```
   BACKEND permitido:
   - backend/apps/expedientes/services/commands/c*.py
   - backend/apps/expedientes/models.py (extend)
   - backend/apps/agreements/models.py (CreditOverride, CreditClockRule)
   - backend/apps/clientes/models.py (campos aditivos)
   - backend/apps/suppliers/ (nueva app completa)
   - backend/apps/knowledge/views.py (fix 500)
   - backend/apps/knowledge/management/commands/load_knowledge.py (nuevo)
   - backend/tests/ (tests nuevos)
   - /etc/nginx/sites-available/ (bloque knowledge)

   FRONTEND permitido:
   - frontend/src/app/[lang]/dashboard/suppliers/

   NO TOCAR:
   - knowledge/ ENT_OPS_STATE_MACHINE
   - CLAUDE.md
   - docker-compose.yml (solo si knowledge fix lo requiere y CEO aprueba)
   - Modelos existentes de CreditPolicy, BrandSuplierAgreement
   ```

9. **Tests antes y después.** Suite completa pasa antes de tocar.
   La misma suite pasa después. Tests nuevos en archivos separados.

10. **Conventional Commits.** `feat:`, `fix:`, `test:`, `refactor:`.
    Nunca "update", "changes", "wip".

---

## ITEMS — BACKEND (AG-02)

### S16-01A: Reserva de crédito en C1

**Archivo:** `backend/apps/expedientes/services/commands/c1.py`

Agregar llamada a `check_and_reserve_credit` en `create_expediente`,
ANTES de confirmar el registro.

```python
def check_and_reserve_credit(expediente, brand, subsidiary):
    """
    Evalúa la política de crédito y reserva el monto del pedido.
    Retorna CreditCheckResult. Levanta CreditLimitExceeded si over_limit sin override.
    Siempre permite el registro si credit_blocked (Opción B) — marca el flag.
    Créditos son independientes por brand × subsidiary.
    """
    from backend.apps.agreements.models import (
        CreditPolicy, CreditExposure, CreditOverride
    )

    policy = CreditPolicy.objects.get_active(brand=brand, subsidiary=subsidiary)
    if not policy:
        return {'allowed': True, 'over_limit': False, 'credit_blocked': False}

    exposure = CreditExposure.objects.calculate(brand=brand, subsidiary=subsidiary)
    order_amount = expediente.snapshot.order_total

    new_total = exposure.total + order_amount
    over_limit = new_total > policy.credit_limit

    # Override formal — NO usar credit_override_approved (no existe)
    has_override = CreditOverride.objects.filter(
        expediente=expediente, command_code='C1'
    ).exists()

    if over_limit and not has_override:
        raise CreditLimitExceeded(
            current=exposure.total,
            limit=policy.credit_limit,
            requested=order_amount,
            overage=new_total - policy.credit_limit
        )

    # Clock expirado: permite registro pero marca credit_blocked
    # INDEPENDIENTE por brand — evaluar solo brand×subsidiary actual
    credit_blocked = CreditExposure.is_clock_expired(
        brand=brand, subsidiary=subsidiary
    )
    expediente.credit_blocked = credit_blocked

    # Siempre reservar
    CreditExposure.reserve(brand=brand, subsidiary=subsidiary,
                           expediente=expediente, amount=order_amount)

    return {
        'allowed': True,
        'over_limit': over_limit,
        'credit_blocked': credit_blocked,
        'exposure_before': float(exposure.total),
        'reserved': float(order_amount),
        'exposure_after': float(new_total),
        'credit_limit': float(policy.credit_limit),
        'utilization_pct': round((new_total / policy.credit_limit) * 100, 1),
        'message': (
            "Línea de crédito vencida para esta marca. Pedido registrado "
            "pero producción bloqueada hasta autorización CEO."
        ) if credit_blocked else None
    }
```

Agregar campo a Expediente: `credit_blocked = BooleanField(default=False)` +
`credit_warning = BooleanField(default=False)`. Migración aditiva.

**Tests:** `backend/tests/test_credit_reservation.py`
```python
# Cobertura mínima:
def test_c1_reserves_credit_correctly()
def test_c1_no_policy_allows_without_reservation()
def test_c1_over_limit_without_override_raises_400()
def test_c1_over_limit_with_c1_override_returns_201()
def test_c1_clock_expired_marks_credit_blocked_true()
def test_c1_clock_expired_still_reserves_amount()
def test_c1_brand_a_clock_expired_does_not_block_brand_b()
```

---

### S16-01B: CreditOverride model + endpoint

**Archivo:** `backend/apps/agreements/models.py`

```python
class CreditOverride(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    expediente = models.ForeignKey(
        'expedientes.Expediente', on_delete=models.CASCADE,
        related_name='credit_overrides'
    )
    brand = models.ForeignKey('brands.Brand', on_delete=models.PROTECT)
    subsidiary = models.ForeignKey(
        'clientes.ClientSubsidiary', on_delete=models.PROTECT
    )
    command_code = models.CharField(max_length=10)
    # Un CreditOverride = un command = una autorización.
    # No hay campo separado "valid_for_command" — es redundante y fuente
    # de contradicción. command_code define el scope completo.
    amount_over_limit = models.DecimalField(max_digits=14, decimal_places=2)
    authorized_by = models.ForeignKey('users.MWTUser', on_delete=models.PROTECT)
    reason = models.TextField()
    authorized_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('expediente', 'command_code')
```

**Endpoint:** `POST /api/agreements/credit-override/`
```python
# Solo CEO
def post(self, request):
    if not request.user.is_superuser:
        return Response(status=403)
    # Validar reason mínimo 10 chars
    # Crear CreditOverride
    # Crear EventLog
    # Retornar 201
```

---

### S16-02: Commands C6-C16

**Archivos:** `c6.py` a `c16.py` en `services/commands/`

Para C6, C8, C9, C14 — hook de crédito al inicio del command:

```python
def _check_credit_gate(expediente, command_code):
    """Levanta error si credit_blocked sin override para este command."""
    if expediente.credit_blocked:
        has_override = CreditOverride.objects.filter(
            expediente=expediente,
            command_code=command_code
        ).exists()
        if not has_override:
            raise CreditBlockedError(
                f"Expediente bloqueado por crédito vencido. "
                f"CEO debe autorizar override para {command_code}."
            )
```

Para C9 — hook de inicio del reloj de cobro:
```python
# Leer regla. Si no existe → fallback on_arrival
rule = CreditClockRule.objects.filter(
    brand=expediente.brand,
    freight_mode=expediente.freight_mode or 'SEA'
).first()
start_event = rule.start_event if rule else 'on_arrival'

if start_event == 'on_shipment':
    trigger_credit_clock(expediente)
```

Para C12 (y C14 con on_invoice) — mismo patrón con el start_event correspondiente.

Para C16 — liberar reserva:
```python
CreditExposure.release(
    brand=expediente.brand,
    subsidiary=expediente.client,
    expediente=expediente
)
```

Management command `check_credit_clocks`:
```python
# backend/apps/agreements/management/commands/check_credit_clocks.py
# Evalúa expedientes con credit_clock_started_at != null
# Día 75: credit_warning=True + crear alerta
# Día 90: credit_clock.expired → bloquear C6 para nuevas órdenes brand×subsidiary
```

**Tests:** `backend/tests/test_commands_c6_c16.py`
```python
def test_c6_invalid_state_returns_400()      # desde DESPACHO → 400
def test_c6_missing_art01_returns_400()
def test_c6_credit_blocked_without_override_returns_400()
def test_c6_credit_blocked_with_override_returns_200()
def test_c8_credit_blocked_without_override_returns_400()
def test_c9_credit_blocked_without_override_returns_400()
def test_c14_credit_blocked_without_override_returns_400()
def test_c16_without_art09_returns_400()
def test_c16_without_payment_returns_400()
def test_c16_releases_credit_exposure()
def test_credit_clock_day75_creates_warning()
def test_credit_clock_day90_blocks_c6()
# + regresión: todos los tests SM S11 pasan sin modificación
```

---

### S16-03: Cancelación y reapertura

**Archivo:** `backend/apps/expedientes/services/commands/c_cancel.py`

```python
def cancel_expediente(expediente, actor, reason):
    if len(reason) < 10:
        raise ValidationError("reason debe tener mínimo 10 caracteres")
    if not actor.is_superuser:
        raise PermissionDenied("Solo CEO puede cancelar expedientes")
    if expediente.status in ['CERRADO', 'CANCELADO']:
        raise ValidationError("No se puede cancelar expediente cerrado o ya cancelado")

    # Liberar crédito reservado
    CreditExposure.release(brand=expediente.brand,
                           subsidiary=expediente.client,
                           expediente=expediente)

    expediente.status = 'CANCELADO'
    expediente.save()
    EventLog.objects.create(
        expediente=expediente, actor=actor,
        command_code='CANCEL', reason=reason,
        old_status=expediente.status, new_status='CANCELADO'
    )
```

**Archivo:** `c_reopen.py`
```python
def reopen_expediente(expediente, actor, justification):
    if not actor.is_superuser:
        raise PermissionDenied()
    if expediente.status != 'CANCELADO':
        raise ValidationError("Solo se puede reabrir desde CANCELADO")

    # Check: máximo 1 reapertura
    reopens = EventLog.objects.filter(
        expediente=expediente, command_code='REOPEN'
    ).count()
    if reopens >= 1:
        raise ValidationError("Máximo 1 reapertura por expediente")

    # Re-evaluar crédito al reabrir
    check_and_reserve_credit(expediente, expediente.brand, expediente.client)

    expediente.status = 'REGISTRO'
    expediente.credit_blocked = False
    expediente.save()
    EventLog.objects.create(
        expediente=expediente, actor=actor,
        command_code='REOPEN', reason=justification
    )
```

---

### S16-04: ClientSubsidiary enriquecida

**Archivo:** `backend/apps/clientes/models.py`

ANTES de agregar nada, correr:
```python
# Verificar qué ya tiene ClientSubsidiary de S14
python manage.py shell -c "from backend.apps.clientes.models import ClientSubsidiary; print([f.name for f in ClientSubsidiary._meta.get_fields()])"
```

Solo agregar los que FALTEN (todos nullable/blank):
```python
legal_name = models.CharField(max_length=300, blank=True, null=True)
tax_id = models.CharField(max_length=50, blank=True, null=True)
# alias probablemente ya existe — verificar
# country probablemente ya existe — verificar
# credit_limit: NO agregar — SSOT es CreditPolicy (S14)
```

**Serializer:** exponer campos en `/api/clientes/{id}/`.
`tax_id` visible solo si `request.user.is_superuser`.

**Management command:** `seed_legal_data`
```bash
python manage.py seed_legal_data --dry-run    # ver qué haría
python manage.py seed_legal_data --file data.csv
```
Los tax_ids son `# TODO: CEO_INPUT_REQUIRED` — no inventar.

---

### S16-05: App suppliers/

**Registrar en `settings.INSTALLED_APPS`:** `'backend.apps.suppliers'`

**Modelos:** ver spec completa en LOTE_SM_SPRINT16.md §S16-05.

**Endpoints — schema completo:**
```python
# urls.py de suppliers
router = DefaultRouter()
router.register(r'suppliers', SupplierViewSet, basename='supplier')

# Extra actions en SupplierViewSet:
@action(detail=True, methods=['get', 'post'])
def contacts(self, request, pk=None): ...

@action(detail=True, methods=['get', 'post'])
def kpis(self, request, pk=None): ...

@action(detail=True, methods=['get'])
def agreements(self, request, pk=None):
    # FK a BrandSupplierAgreement de S14 — no duplicar
    agreements = BrandSupplierAgreement.objects.filter(supplier_id=pk)
    ...

@action(detail=True, methods=['get'])
def expedientes(self, request, pk=None): ...

@action(detail=True, methods=['get'])
def catalog(self, request, pk=None):
    # Buscar ProductMaster donde supplier_id = pk
    # Si el campo no existe en ProductMaster → retornar {count:0, results:[]}
    # NUNCA retornar 404
    ...
```

**Query params en list:**
```python
def get_queryset(self):
    qs = Supplier.objects.all()
    if search := self.request.query_params.get('search'):
        qs = qs.filter(name__icontains=search)
    if country := self.request.query_params.get('country'):
        qs = qs.filter(country=country)
    if brand_id := self.request.query_params.get('brand'):
        qs = qs.filter(
            brandsupplieragreement__brand_id=brand_id
        ).distinct()
    if is_active := self.request.query_params.get('is_active'):
        qs = qs.filter(is_active=(is_active.lower() == 'true'))
    return qs
```

---

### S16-07: Knowledge fix

**1. Fix 500 en `knowledge/views.py`:**
```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ask(request):
    query = request.data.get('query', '').strip()
    scope = request.data.get('scope', 'internal')

    if not query:
        return Response({'error': 'query es requerido'}, status=400)

    try:
        results = vector_store.similarity_search(query, k=5)
        if not results:
            return Response({
                'answer': '',
                'sources': [],
                'message': 'Knowledge base sin contenido indexado aún.'
            }, status=200)

        # Construir contexto y llamar LLM...
        answer = llm_chain.run(context=results, query=query)
        sources = [{'file': r.metadata.get('source'), 'score': r.score}
                   for r in results]
        return Response({'answer': answer, 'sources': sources}, status=200)

    except Exception as e:
        logger.error(f'Knowledge ask unexpected error: {e}', exc_info=True)
        return Response({'error': 'Error inesperado.'}, status=500)
```

Política: **200** para vacío/sin resultados. **500** solo para error real.

**2. Management command `load_knowledge.py`:**

Parser por secciones CEO-ONLY:
```python
def parse_visibility(filepath):
    """Retorna (should_include_file, ceo_only_section_ids)"""
    with open(filepath) as f:
        content = f.read()

    # Leer front matter YAML
    if content.startswith('---'):
        end = content.find('---', 3)
        front_matter = yaml.safe_load(content[3:end])
    else:
        front_matter = {}

    visibility = front_matter.get('visibility', '[INTERNAL]')
    if 'CEO-ONLY' in str(visibility):
        return False, []   # excluir todo el archivo

    ceo_only = front_matter.get('ceo_only_sections', [])
    return True, ceo_only

def split_by_headings(content, ceo_only_sections):
    """Split por ## headings, excluir secciones en ceo_only_sections."""
    chunks = []
    current_section_id = None
    current_content = []

    for line in content.split('\n'):
        # Detectar heading ## Section ID
        if line.startswith('## '):
            if current_content and current_section_id not in ceo_only_sections:
                chunks.append('\n'.join(current_content))
            current_section_id = line.split(' ')[1] if len(line.split(' ')) > 1 else None
            current_content = [line]
        elif line.startswith('### '):
            sub_id = line.split(' ')[1] if len(line.split(' ')) > 1 else None
            # Si sub_id está en ceo_only_sections, skip
            if any(sub_id and sub_id.startswith(s) for s in ceo_only_sections):
                continue
            current_content.append(line)
        else:
            current_content.append(line)

    if current_content and current_section_id not in ceo_only_sections:
        chunks.append('\n'.join(current_content))

    return chunks
```

Prefijos a excluir:
```python
EXCLUDED_PREFIXES = [
    'LOTE_SM_SPRINT', 'REPORTE_', 'PATCH_', 'MANIFIESTO_APPEND_',
    'CHECKPOINT_SESSION_', 'GUIA_ALE_', 'PROMPT_ANTIGRAVITY_', 'PROMPT_',
]
```

**3. Nginx + puerto 8001:**
```bash
# Agregar config knowledge en Nginx
# Cerrar puerto:
sudo ufw deny 8001
```

---

## ITEMS — FRONTEND (AG-03)

### S16-06: Supplier Console UI

**`suppliers/page.tsx` — Lista:**
```typescript
// Usar useFetch de S12-08 con query params
const { data, loading } = useFetch<DRFPaginatedResponse<Supplier>>(
  `/api/suppliers/?search=${search}&country=${country}&brand=${brand}`
);
```

**`suppliers/[id]/page.tsx` — 4 tabs:**

```typescript
const TABS = ['Identidad', 'Acuerdos', 'Catálogo', 'KPIs'] as const;

// Tab 3 — Catálogo
const { data: catalog } = useFetch(`/api/suppliers/${id}/catalog/`);
if (catalog?.count === 0) {
  return <EmptyState message="Sin catálogo registrado" />;
}

// Tab 4 — KPIs
// Mostrar datos sin semáforo si umbrales no están en ENT_GOB_KPI
// TODO: umbrales pendientes CEO — aplicar colores cuando estén definidos formalmente
const kpiRows = kpis.results.map(kpi => ({
  period: `${kpi.period_start} – ${kpi.period_end}`,
  otif: kpi.otif_pct ? `${kpi.otif_pct}%` : '—',
  fill_rate: kpi.fill_rate_pct ? `${kpi.fill_rate_pct}%` : '—',
  lead_time: kpi.lead_time_variance_days != null
    ? `${kpi.lead_time_variance_days}d` : '—',
  defect: kpi.defect_rate_pct ? `${kpi.defect_rate_pct}%` : '—',
}));
```

**Reglas de UI:**
- 0 hex hardcodeados — usar CSS variables
- Auto-detectar formato DRF paginado `{count, next, results}` vs array plano
- Empty states en todos los tabs antes de datos

---

## CONDICIONALES — S16-08, S16-09, S16-10

```python
# S16-08: PaymentTermPricing
# Solo si CEO provee CSV con datos. Si no → SKIP.
# Marcar en PR: "# TODO: CEO_INPUT_REQUIRED — datos PaymentTermPricing pendientes"

# S16-09: CreditClockRule
# Solo si CEO define reglas de freight_mode. Si no → SKIP.
# El fallback on_arrival ya está implementado en C9/C12.

# S16-10: Seed Tecmater
# Solo si CEO provee flujo operativo TCM. Si no → SKIP.
# No crear policy con datos placeholder.
```

---

## CHECKLIST PRE-PUSH

```bash
# Backend
python manage.py test                    # 0 failures
bandit -ll backend/                      # sin HIGH/CRITICAL nuevos

# Verificaciones específicas S16
python -c "
from backend.apps.clientes.models import ClientSubsidiary
fields = [f.name for f in ClientSubsidiary._meta.get_fields()]
assert 'credit_limit' not in fields, 'credit_limit no debe estar en ClientSubsidiary'
assert 'legal_name' in fields
assert 'tax_id' in fields
print('✅ ClientSubsidiary OK')
"

# Knowledge
curl -X POST http://localhost:8001/api/knowledge/ask/ \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer $TOKEN' \
  -d '{"query": "test"}' | python -c \
  "import sys,json; d=json.load(sys.stdin); assert d.get('answer') is not None or d.get('message'), 'Debe retornar answer o message'"

# Puerto 8001
sudo ufw status | grep "8001" | grep "DENY" || echo "ERROR: puerto 8001 no cerrado"

# Frontend
npm run lint && npm run typecheck && npm run test

# Cross-tenant S15 no roto
python manage.py test backend.apps.portal.tests.test_tenant_isolation
```

---

## REPORTE AL CEO (al terminar)

```markdown
## Resultado Sprint 16
- **Agente:** AG-02 + AG-03 Alejandro
- **Status:** DONE / PARTIAL / BLOCKED
- **Archivos creados:** [lista exacta]
- **Archivos modificados:** [lista exacta]
- **Archivos NO tocados:** [confirmar: ENT_OPS_STATE_MACHINE, CreditPolicy, BrandSupplierAgreement]
- **Condicionales:**
  - S16-08 PaymentTermPricing: DONE / SKIP — [razón]
  - S16-09 CreditClockRule: DONE / SKIP — [razón]
  - S16-10 Seed Tecmater: DONE / SKIP — [razón]
- **Campos agregados a ClientSubsidiary:** [lista — NO incluir credit_limit]
- **pgvector archivos cargados:** [número]
- **Puerto 8001:** cerrado / pendiente / [problema]
- **Tests ejecutados:** [resumen pasan/fallan]
- **CEO_INPUT_REQUIRED pendientes:** [lista]
- **Decisiones asumidas:** [cualquier cosa fuera del spec]
- **Blockers:** [lista o "ninguno"]
```
