# LOTE_SM_SPRINT16 — Backend Iteración + Supplier Console + Knowledge Fix
id: LOTE_SM_SPRINT16
version: 1.3
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
status: DRAFT — Pendiente aprobación CEO
tipo: Lote ruteado (ref → PLB_ORCHESTRATOR §E)
sprint: 16
priority: P0
depends_on: LOTE_SM_SPRINT15 (DONE)
refs: ENT_OPS_STATE_MACHINE (FROZEN v1.2.2), ENT_PLAT_SEGURIDAD,
      CHECKPOINT_SESSION_20260320_BRAND_CONSOLE, ENT_PLAT_KNOWLEDGE,
      ENT_GOB_PENDIENTES, ENT_COMERCIAL_CLIENTES, ENT_PLAT_LEGAL_ENTITY

changelog:
  - v1.0 (2026-03-23): Compilación inicial
  - v1.1 (2026-03-23): Fixes auditoría R1 (8.1/10) — H1-H12
  - v1.2 (2026-03-23): Fixes auditoría R2 (9.1/10)
  - v1.3 (2026-03-23): Fix auditoría R4 (9.4/10) — S16-04 UI eliminar
    credit_limit de campos CEO-ONLY (SSOT es CreditPolicy) — F1 CreditOverride campo
    único command_code, F2 eliminar credit_limit de ClientSubsidiary (SSOT es
    CreditPolicy), F3 criterio SKIP binario S16-10, F4 política clock expirado
    Opción B (C1 permite registro, expediente nace credit_blocked=True, C6
    requiere override; créditos independientes por Brand)

---

## Contexto y fuentes del scope

**Línea A — Crédito e iteración de estados**
Regla CEO confirmada 2026-03-23:
- La exposición de crédito se RESERVA desde C1 (CreateExpediente).
  No al despachar, no al arribar — desde el registro del pedido.
- Exposición = producción_en_curso + en_tránsito + facturado_sin_pagar
- El crédito lo emite el Brand hacia la ClientSubsidiary. No es crédito
  del cliente como entidad autónoma — es línea Brand × Subsidiaria.
- Sobrecrédito: override CEO disponible en cualquier etapa (registro,
  producción, despacho). No es solo para registro. Requiere autorización
  explícita + reason + EventLog. No avanza automáticamente al siguiente estado.
- CEO-28 (credit_clock_start_rule): cuándo empieza el plazo de cobro/vencimiento
  es INDEPENDIENTE de cuándo se reserva la exposición.

**Línea B — Legal Entities de clientes**
Regla CEO confirmada 2026-03-23:
- Cada ClientSubsidiary es una entidad legal independiente.
- Tiene: legal_name, tax_id, alias (nombre de uso).
  CreditPolicy propia por Brand (SSOT del límite de crédito — ref CreditPolicy en S14).
- Lo único que hereda del grupo es la cascada de precios y acuerdos
  regionales (BrandClientAgreement a nivel ClientGroup).
- Clientes conocidos pendientes de enriquecer (ref ENT_COMERCIAL_CLIENTES §B):
  SONDEL S.A. (CR), SONDEL Nicaragua (si existe como entidad separada),
  IMPORCOMP S.A. (GT), y otros de la lista §B.
- ClientSubsidiary de S14 tiene alias pero no tax_id ni legal_name.
  S16 los agrega como campos aditivos (no destructivos).

**Línea C — Supplier Console** (fuente: S14 retrospectiva)
BrandSupplierAgreement ya existe en agreements/. S16 construye app + UI.

**Línea D — Knowledge fix** (fuente: CEO-12, CEO-13 desde S8)
500 y pgvector vacío bloquean canal B2B completo.

## Objetivo Sprint 16

**5 pilares:**
1. Crédito correcto — reserva desde C1, sobrecrédito por etapa, modelo Brand×Subsidiaria
2. Flujo C6-C16 completo — commands con lógica real, reloj de cobro (CEO-28)
3. Legal entities — ClientSubsidiary enriquecida con campos legales completos
4. Supplier Console — app suppliers/ + UI 4 tabs
5. Knowledge fix — 500 → 200, pgvector, Nginx+SSL, cerrar 8001

**Precondición hard:** Sprint 15 DONE verificado en staging.

---

## Convenciones

### C1. State machine FROZEN — intocable
ENT_OPS_STATE_MACHINE v1.2.2 no se modifica.

### C2. Crédito = exposición Brand × Subsidiaria
La línea de crédito la emite el Brand hacia la ClientSubsidiary.
Toda evaluación, reserva y override se evalúa en contexto de
`brand × client_subsidiary`. No existe "crédito del cliente" genérico.

### C3. Dos conceptos de crédito — no mezclar

| Concepto | Cuándo ocurre | Modelo |
|----------|--------------|--------|
| `credit_exposure_reservation` | En C1 CreateExpediente — al registrar | CreditExposure.reserved += monto |
| `credit_clock_start_rule` | En C9/C12/C14 según freight_mode — para cobro | CreditClockRule por Brand × freight_mode |

Son hooks independientes. C1 siempre evalúa exposición.
C9/C12/C14 disparan el reloj de cobro/vencimiento según CEO-28.

### C4. Sobrecrédito — override disponible en cualquier etapa
No es solo para registro. CEO puede autorizar sobrecrédito en C1, C6, C9, o cualquier command.
El override NO avanza automáticamente al siguiente estado — cada transición
sigue evaluando exposición. El CEO debe autorizar cada step si sigue en sobrecrédito.

### C5. Lección L-S12-01
Items de refactorización solo si AG-02 los propone.

### C6. Knowledge fix es P0
CEO-12 abierto desde Sprint 8. Desbloquea canal B2B.

### C7. ClientSubsidiary enriquecimiento aditivo
Los campos nuevos (tax_id, legal_name, alias) son additive migrations.
# credit_limit NO se agrega — SSOT es CreditPolicy.credit_limit (S14).
No se toca ningún campo existente. Backwards compatible con S14.

---

## Items

### FASE 0 — Gate

#### S16-00: Sprint Gate
- **Agente:** AG-02 Backend

```bash
# Sprint 15 DONE en staging
curl -s https://staging.consola.mwt.one/api/health/ | \
  python -c "import sys,json; d=json.load(sys.stdin); assert d['status']=='ok'"

# Portal B2B S15 funcional
curl -H "Authorization: Bearer $PORTAL_TOKEN" /api/portal/expedientes/ | \
  python -c "import sys,json; d=json.load(sys.stdin); assert 'results' in d"

# S14 agreements estables
curl -H "Authorization: Bearer $TOKEN" /api/agreements/ | \
  python -c "import sys,json; d=json.load(sys.stdin); assert isinstance(d,(list,dict))"

# CI main verde — verificar GitHub Actions
# CEO confirmó sobre CEO-27/28/Tecmater (check manual)
```

- **Criterio de done:**
  - [ ] S15 DONE confirmado en staging
  - [ ] Portal B2B S15 sin errores
  - [ ] CI main verde
  - [ ] AG-02 tiene respuesta del CEO sobre CEO-27/28/Tecmater

---

### FASE 1 — Crédito correcto (P0)

#### S16-01A: credit_exposure_reservation en C1
- **Agente:** AG-02 Backend
- **Dependencia:** S16-00 DONE
- **Archivos impactados:**
  - `backend/apps/expedientes/services/commands/c1.py` — agregar hook
  - `backend/apps/agreements/models.py` — ampliar CreditExposure si necesario
  - `backend/apps/expedientes/tests/test_credit_reservation.py` — NUEVO

**Modelo de exposición (C2):**
```python
# CreditExposure es calculado, no editable (ya existe de S14)
# S16-01A agrega la reserva explícita al registrar expediente

# En C1 CreateExpediente, ANTES de confirmar el registro:
def check_and_reserve_credit(expediente, brand, subsidiary) -> CreditCheckResult:
    policy = CreditPolicy.objects.get_active(brand=brand, subsidiary=subsidiary)
    if not policy:
        return CreditCheckResult(allowed=True, over_limit=False, requires_override=False)

    exposure = CreditExposure.objects.calculate(brand=brand, subsidiary=subsidiary)
    order_amount = expediente.snapshot.order_total  # del ExpedienteContextSnapshot

    new_total = exposure.total + order_amount
    over_limit = new_total > policy.credit_limit

    # Verificar override formal via CreditOverride model (S16-01B)
    # NO usar credit_override_approved — ese boolean no existe en el modelo.
    has_override = CreditOverride.objects.filter(
        expediente=expediente,
        command_code='C1'
    ).exists()
    if over_limit and not has_override:
        raise CreditLimitExceeded(
            current=exposure.total,
            limit=policy.credit_limit,
            requested=order_amount,
            overage=new_total - policy.credit_limit
        )

    # Registrar reserva
    CreditExposure.reserve(
        brand=brand,
        subsidiary=subsidiary,
        expediente=expediente,
        amount=order_amount
    )
    return CreditCheckResult(allowed=True, over_limit=over_limit)
```

**CreditCheckResult en response de C1:**
```json
{
  "expediente_id": "...",
  "credit_check": {
    "allowed": true,
    "over_limit": false,
    "exposure_before": 45000.00,
    "reserved": 12000.00,
    "exposure_after": 57000.00,
    "credit_limit": 75000.00,
    "utilization_pct": 76.0
  }
}
```

- **Criterio de done:**
  - [ ] C1 evalúa CreditPolicy antes de confirmar registro
  - [ ] C1 reserva monto en CreditExposure.reserved al crear expediente
  - [ ] Si over_limit sin override → CreditLimitExceeded (400) con detalle
  - [ ] Response de C1 incluye `credit_check` block
  - [ ] Test: registro con crédito disponible → reserva correcta
  - [ ] Test: registro sin CreditPolicy → permitido (sin bloqueo)
  - [ ] Test: registro sobre límite sin override → 400 CreditLimitExceeded
  - [ ] Test: registro sobre límite con override aprobado → 201 con over_limit=true

#### S16-01B: CreditOverride — sobrecrédito por etapa
- **Agente:** AG-02 Backend
- **Dependencia:** S16-01A DONE
- **Archivos impactados:**
  - `backend/apps/agreements/models.py` — agregar CreditOverride model
  - `backend/apps/expedientes/services/commands/` — hook en c1, c6, c8, c9, c14
  - `backend/apps/agreements/api/views.py` — endpoint authorize-credit-override

**Modelo:**
```python
class CreditOverride(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    expediente = models.ForeignKey('expedientes.Expediente',
                                    on_delete=models.CASCADE,
                                    related_name='credit_overrides')
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT)
    subsidiary = models.ForeignKey(ClientSubsidiary, on_delete=models.PROTECT)
    command_code = models.CharField(max_length=10)  # C1, C6, C8, C9, C14
    # command_code es el único identificador de scope.
    # Un CreditOverride = un command = una autorización.
    # No existe campo separado — sería redundante y fuente de contradicción.
    amount_over_limit = models.DecimalField(max_digits=14, decimal_places=2)
    authorized_by = models.ForeignKey('users.MWTUser', on_delete=models.PROTECT)
    reason = models.TextField()                      # obligatorio, mínimo 10 chars
    authorized_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Un override por expediente × command — no se reutiliza entre commands
        unique_together = ('expediente', 'command_code')
```

**Endpoint:**
```
POST /api/agreements/credit-override/
Body: {
  "expediente_id": "...",
  "command_code": "C1",   # qué command autoriza
  "reason": "Cliente estratégico, CEO autoriza excepción."
}
Solo CEO (is_superuser). Crea CreditOverride + EventLog.
```

**Hook en commands:**
- Cada command que toca crédito (C1, C6, C8, C9, C14) verifica:
  si `over_limit` → buscar CreditOverride válido para ese command_code
  si no existe → 400 "Sobrecrédito requiere autorización CEO"
- El override NO libera automáticamente el siguiente command.
  Cada command necesita su propio override si sigue en sobrecrédito.

- **Criterio de done:**
  - [ ] CreditOverride model + migration
  - [ ] Endpoint `POST /api/agreements/credit-override/` solo CEO
  - [ ] Hook en C1, C6, C8, C9, C14: verifica override si over_limit
  - [ ] Override válido solo para el command_code declarado
  - [ ] Test: C6 en sobrecrédito sin override → 400
  - [ ] Test: C6 en sobrecrédito con override C6 → 200 (no libera C8)
  - [ ] Test: C8 después de C6 sobrecrédito → sigue evaluando, necesita override C8
  - [ ] EventLog creado por cada override autorizado

---

### FASE 2 — Commands C6-C16 (P0)

#### S16-02: Commands C6-C16 con lógica real
- **Agente:** AG-02 Backend
- **Dependencia:** S16-01A y S16-01B DONE
- **Archivos:** `backend/apps/expedientes/services/commands/c6.py` a `c16.py`
  + `test_commands_c6_c16.py` NUEVO

**Mapping commands (ref → ENT_OPS_STATE_MACHINE FROZEN v1.2.2):**

| Command | Acción | De | A | Gates |
|---------|--------|-----|---|-------|
| C6 | ConfirmarProduccion | REGISTRO | PRODUCCION | ART-01,02,03,04 + crédito |
| C7 | RegistrarFechaProduccion | PRODUCCION | PRODUCCION | — |
| C8 | ConfirmarPreparacion | PRODUCCION | PREPARACION | ART-05 + crédito |
| C9 | RegistrarDespacho | PREPARACION | DESPACHO | ART-06 + crédito + clock |
| C10 | ConfirmarTransito | DESPACHO | TRANSITO | — |
| C11 | RegistrarETA | TRANSITO | TRANSITO | — |
| C12 | ConfirmarArribo | TRANSITO | EN_DESTINO | clock si on_arrival |
| C13 | RegistrarNacionalizacion | EN_DESTINO | EN_DESTINO | ART-08 |
| C14 | EmitirFactura | EN_DESTINO | EN_DESTINO | ART-09 + crédito + clock si on_invoice |
| C15 | RegistrarPago | EN_DESTINO | EN_DESTINO | — |
| C16 | CerrarExpediente | EN_DESTINO | CERRADO | ART-09 emitido + pago + liberar reserva |

**Política clock expirado — Opción B (CEO confirmado 2026-03-23):**
Los créditos son INDEPENDIENTES por Brand. Clock expirado para Brand A
no bloquea Brand B ni ninguna otra pareja brand × subsidiary.

Dentro de la misma pareja brand × subsidiary expirada:
- C1 (CreateExpediente): SIEMPRE permitido administrativamente.
  Si `credit_clock.expired == True` para esa pareja → el expediente nace
  con `credit_blocked = True` + advertencia en response.
  Razón: permite registrar el pedido sin bloquear operación completa.
- C6 (ConfirmarProduccion): BLOQUEADO si `expediente.credit_blocked == True`.
  Requiere CreditOverride CEO para avanzar.
- C8, C9, C14: también bloqueados si `credit_blocked == True` sin override.

```python
# En C1 — siempre registra, pero marca si clock expirado
credit_blocked = check_credit_clock_expired(brand=brand, subsidiary=subsidiary)
expediente.credit_blocked = credit_blocked

if credit_blocked:
    # Reservar igual — el pedido existe administrativamente
    CreditExposure.reserve(brand, subsidiary, expediente, order_amount)
    # Respuesta con advertencia (no error)
    response['credit_check']['credit_blocked'] = True
    response['credit_check']['message'] = (
        "Línea de crédito vencida. Expediente registrado pero "
        "producción bloqueada hasta autorización CEO."
    )
```

**Notas adicionales:**
- C6, C8, C9, C14: evalúan sobrecrédito via hook de S16-01B
  Y evalúan `expediente.credit_blocked` — ambos gates son independientes
- C9: `trigger_credit_clock()` si `credit_clock_start_rule == 'on_shipment'`
  (fallback: si CreditClockRule no existe → usar `on_arrival` como default)
- C12: `trigger_credit_clock()` si `credit_clock_start_rule == 'on_arrival'`
- C14: `trigger_credit_clock()` si `credit_clock_start_rule == 'on_invoice'`
- C16: liberar `CreditExposure.reserved` para este expediente + recalcular total
- Todos: crear EventLog (actor, timestamp, command_code, old_status, new_status, payload)

**Reloj de crédito automático:**
Management command: `python manage.py check_credit_clocks`
- Evalúa todos los expedientes con `credit_clock_started_at` != null
- Día 75: crear alerta + `expediente.credit_warning = True`
- Día 90: `credit_clock.expired` + bloquear C6 para nuevos expedientes
  de esa subsidiaria × brand hasta CEO desbloqueo manual
Fuente del diseño: LOTE_SM_SPRINT2 (pendiente real desde 2026-02-27).

- **Criterio de done:**
  - [ ] C6-C16 con precondiciones + EventLog
  - [ ] C6, C8, C9, C14 evalúan sobrecrédito
  - [ ] C9, C12, C14 disparan clock según `credit_clock_start_rule`
    con fallback a `on_arrival` si CreditClockRule no existe aún
  - [ ] C16 libera CreditExposure.reserved del expediente
  - [ ] Cron task: día 75 alerta, día 90 bloqueo C6
  - [ ] Tests: 11 commands × estados inválidos
  - [ ] Tests SM S11 sin regresión

#### S16-03: Cancelación y reapertura CEO
- **Agente:** AG-02 Backend
- **Dependencia:** S16-02 DONE
- **Archivos:** `c_cancel.py` + `c_reopen.py` NUEVOS

**CancelarExpediente:**
- Cualquier estado != CERRADO/CANCELADO. Solo CEO.
- `reason` obligatorio (mínimo 10 chars)
- Libera `CreditExposure.reserved` del expediente
- EventLog → CANCELADO (terminal)

**ReabrirExpediente:**
- Solo desde CANCELADO, solo CEO. `justification` obligatorio.
- Revalúa CreditPolicy al reabrir (re-reserva si hay crédito disponible)
- → REGISTRO. Máximo 1 reapertura (constraint → 400 en 2do intento)

- **Criterio de done:**
  - [ ] CancelarExpediente libera reserva de crédito + EventLog
  - [ ] Solo CEO puede cancelar (403 otros roles)
  - [ ] ReabrirExpediente re-evalúa crédito
  - [ ] Máximo 1 reapertura

---

### FASE 3 — Legal Entities enriquecidas (P0)

#### S16-04: ClientSubsidiary — campos legales completos
- **Agente:** AG-02 Backend
- **Dependencia:** S16-00 DONE
- **Archivos impactados:**
  - `backend/apps/clientes/models.py` — agregar campos a ClientSubsidiary
  - `backend/apps/clientes/migrations/` — migration aditiva
  - `backend/apps/clientes/api/serializers.py` — exponer campos nuevos
  - `backend/apps/clientes/management/commands/seed_legal_data.py` — NUEVO

**Campos a agregar a ClientSubsidiary (todos nullable — aditivos):**
```python
# Migration aditiva — no destructiva
# ClientSubsidiary ya tiene: name, alias, client_group (FK)

legal_name = models.CharField(max_length=300, blank=True, null=True)
# "SONDEL S.A." — nombre legal exacto para documentos

tax_id = models.CharField(max_length=50, blank=True, null=True)
# Cédula jurídica / NIT / RUC / CNPJ según país

alias = models.CharField(max_length=100, blank=True, null=True)
# Ya existía — confirmar que existe, si no agregar
# Nombre de uso cotidiano ("Sondel CR", "Imporcomp")

country = models.CharField(max_length=2, blank=True, null=True)
# ISO 3166-1 alpha-2 (si no existe ya en el modelo)

# credit_limit NO se agrega aquí.
# SSOT del límite de crédito: CreditPolicy.credit_limit (Brand × Subsidiary)
# ya existe desde S14 en backend/apps/agreements/models.py.
# La UI CEO lee el límite desde CreditPolicy filtrado por brand_id.
# Agregar credit_limit en ClientSubsidiary crearía dos verdades para el
# mismo dato. POL_DETERMINISMO: dato único en un solo lugar.

external_code_marluvas = models.CharField(max_length=50, blank=True, null=True)
# Código SAP Marluvas (ya puede existir como ClientBrandExternalCode)
# Si ya existe en ClientBrandExternalCode, NO duplicar aquí
```

**Nota crítica:** Antes de agregar campos, AG-02 verifica qué ya existe
en `ClientSubsidiary` (S14) y en `ClientBrandExternalCode`. Solo agregar
lo que realmente falta. No duplicar.

**Seed data (ref → ENT_COMERCIAL_CLIENTES §B):**
Management command `seed_legal_data` pobla los campos para los 11 clientes
conocidos. Los valores de `tax_id` son [PENDIENTE — NO INVENTAR] hasta que
CEO los provea. El comando acepta `--file legal_data.csv` para cargar.

**UI — Admin de clientes (extensión de Client Console S14/S15):**
- Editar `legal_name`, `tax_id`, `alias` desde la tab Identidad del Client Console
- Campo CEO-ONLY: tax_id visible solo role=CEO
- credit_limit: NO es campo de ClientSubsidiary — se consulta desde
  CreditPolicy filtrado por brand_id y no es editable en esta UI
- Los campos se agregan al formulario existente — no crear pantalla nueva

- **Criterio de done:**
  - [ ] Migration aditiva sin destructivos
  - [ ] Campos nuevos expuestos en `/api/clientes/{id}/` serializer
  - [ ] Admin Django actualizado
  - [ ] Management command `seed_legal_data --dry-run` funcional
  - [ ] Tab Identidad del Client Console muestra legal_name + alias
  - [ ] tax_id visible solo role=CEO en la UI
  - [ ] credit_limit NO vive en ClientSubsidiary — UI CEO lo lee desde
        CreditPolicy filtrado por brand_id (no mostrar campo editable aquí)
  - [ ] Test: editar legal_name → se persiste correctamente
  - [ ] Test: cliente sin rol CEO intenta ver tax_id → campo ausente del response

---

### FASE 4 — Supplier Console (P1)

#### S16-05: App suppliers/ — modelos y API
- **Agente:** AG-02 Backend
- **Dependencia:** S16-00 DONE
- **Archivos creados:** `backend/apps/suppliers/` (models, api/, migrations/, tests/)

**Modelos:**
```python
class Supplier(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=200)
    legal_name = models.CharField(max_length=200, blank=True)
    country = models.CharField(max_length=2)        # ISO 3166-1 alpha-2
    city = models.CharField(max_length=100, blank=True)
    primary_contact_email = models.EmailField()
    payment_terms = models.CharField(max_length=50, blank=True)
    incoterm_default = models.CharField(max_length=10, blank=True)
    currency = models.CharField(max_length=3, default='USD')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class SupplierContact(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE,
                                  related_name='contacts')
    name = models.CharField(max_length=200)
    role = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    is_primary = models.BooleanField(default=False)

class SupplierPerformanceKPI(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE,
                                  related_name='kpis')
    period_start = models.DateField()
    period_end = models.DateField()
    # Umbrales ref → ENT_GOB_KPI (si no existen allí aún → [PENDIENTE CEO])
    otif_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    fill_rate_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    lead_time_variance_days = models.DecimalField(max_digits=6, decimal_places=1,
                                                   null=True)
    defect_rate_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey('users.MWTUser', null=True,
                                     on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('supplier', 'period_start', 'period_end')
        ordering = ['-period_start']
```

`BrandSupplierAgreement` ya existe en agreements/ — no duplicar.

**Endpoints — incluyendo query params (fix H6):**
```
GET  /api/suppliers/
     ?search=           búsqueda por nombre
     ?country=XX        filtro por código ISO país
     ?brand=uuid        filtro por BrandSupplierAgreement.brand
     ?is_active=true|false
     → lista paginada DRF {count, next, previous, results}

POST /api/suppliers/                crear
GET  /api/suppliers/{id}/           detalle
PATCH /api/suppliers/{id}/          editar
GET  /api/suppliers/{id}/contacts/  contactos
POST /api/suppliers/{id}/contacts/  agregar contacto
GET  /api/suppliers/{id}/kpis/      KPIs históricos paginados
POST /api/suppliers/{id}/kpis/      registrar período KPI
GET  /api/suppliers/{id}/agreements/ BrandSupplierAgreement filtrado
GET  /api/suppliers/{id}/expedientes/ expedientes vinculados
GET  /api/suppliers/{id}/catalog/
     → {count, results: [{sku, name, category, price}]}
     → Si no hay ProductMaster con supplier_id → {count:0, results:[]}
     → NO retornar 404 — retornar lista vacía
```

- **Criterio de done:**
  - [ ] Migrations aplicadas sin destructivos
  - [ ] 11 endpoints funcionales con query params declarados
  - [ ] BrandSupplierAgreement de S14 reutilizado (no duplicado)
  - [ ] `/catalog/` retorna lista vacía (no 404) cuando sin datos
  - [ ] Admin Django registrado
  - [ ] unique_together activo
  - [ ] Tests: CRUD Supplier, KPI constraint, query params filtros

#### S16-06: Supplier Console UI — 4 tabs
- **Agente:** AG-03 Frontend
- **Dependencia:** S16-05 DONE
- **Archivos:**
  - `frontend/src/app/[lang]/dashboard/suppliers/page.tsx`
  - `frontend/src/app/[lang]/dashboard/suppliers/[id]/page.tsx`

**Lista:** tabla (nombre/país/contacto principal/acuerdos activos/OTIF último período),
filtros `?country=`, `?brand=`, `?search=`, FormModal nuevo proveedor, badge activo/inactivo.

**Detalle — 4 tabs:**

Tab 1 — Identidad: campos editables (nombre, nombre legal, país, ciudad, email),
tabla contactos (nombre/rol/email/teléfono), términos (payment terms, incoterm, moneda).

Tab 2 — Acuerdos: lista BrandSupplierAgreement read-only MVP.
Columnas: marca / tipo / territorio / valid_from / valid_to / status.

Tab 3 — Catálogo: `GET /api/suppliers/{id}/catalog/`
Empty state si `count === 0`: "Sin catálogo registrado". No inventar datos.

Tab 4 — KPIs: tabla histórica + FormModal "Registrar período".

Semáforo por KPI — umbrales ref ENT_GOB_KPI si existen;
si ENT_GOB_KPI no los define aún, mostrar valores numéricos sin color semáforo
y agregar comentario `// TODO: umbrales pendientes CEO`:

| KPI | Verde (si ENT_GOB_KPI los define) | Fuente |
|-----|------------------------------------|--------|
| OTIF | [PENDIENTE CEO — ref ENT_GOB_KPI] | ENT_GOB_KPI.B? |
| Fill rate | [PENDIENTE CEO] | ENT_GOB_KPI.B? |
| Lead time variance | [PENDIENTE CEO] | ENT_GOB_KPI.B? |
| Defect rate | [PENDIENTE CEO] | ENT_GOB_KPI.B? |

Empty state si sin KPIs: "Sin datos de desempeño aún".
Sidebar: agregar "Proveedores" bajo sección Configuración.

- **Criterio de done:**
  - [ ] Lista con filtros `?country=`, `?brand=`, `?search=` funcionales
  - [ ] 4 tabs con datos reales desde API
  - [ ] Tab Catálogo: empty state (no error) si sin datos
  - [ ] Tab KPIs: muestra datos sin semáforo si umbrales no definidos en KB
  - [ ] Empty states correctos en todos los tabs
  - [ ] Sidebar actualizado
  - [ ] 0 hex hardcodeados

---

### FASE 5 — Knowledge fix (P0)

#### S16-07: Fix 500 + pgvector + Nginx + puerto 8001
- **Agente:** AG-02 Backend
- **Dependencia:** S16-00 DONE
- **Archivos impactados:**
  - `backend/apps/knowledge/views.py` — fix manejo tabla vacía
  - `backend/apps/knowledge/management/commands/load_knowledge.py` — NUEVO
  - `/etc/nginx/sites-available/mwt-knowledge` — NUEVO

**A — Fix del 500 (política clarificada — fix H9):**

Política: `200` para "sin resultados" o "sin datos indexados".
`500` SOLO para errores reales inesperados (LLM caído, DB corruption, etc.).
NO retornar 500 por tabla vacía o query sin resultados — eso es estado válido.

```python
# En /api/knowledge/ask/
try:
    results = vector_store.similarity_search(query, k=5)
    if not results:
        return Response({
            "answer": "",
            "sources": [],
            "message": "Knowledge base sin contenido indexado aún."
        }, status=200)   # 200 — estado válido, no error
    # lógica con LLM...
    return Response({"answer": llm_response, "sources": sources}, status=200)
except VectorStoreEmptyError:
    return Response({"answer": "", "sources": [], "message": "..."}, status=200)
except Exception as e:
    logger.error(f"Knowledge ask unexpected error: {e}", exc_info=True)
    return Response({"error": "Error inesperado. Contactar soporte."}, status=500)
```

Criterio DONE global para S16: "sin 500 por tabla vacía/sin resultados".
El 500 en except de error inesperado es correcto y se mantiene.

**B — Carga inicial pgvector con parser CEO-ONLY (fix H10):**

El management command `load_knowledge` debe implementar exclusión a nivel de
sección, no solo a nivel de archivo:

```python
# Contrato del parser para ceo_only_sections

def parse_md_with_visibility(filepath: str) -> list[Chunk]:
    """
    1. Leer front matter YAML del archivo:
       visibility: [INTERNAL] o [PUBLIC] → incluir
       visibility: [CEO-ONLY] → excluir todo el archivo
       ceo_only_sections: [D3, D4] → incluir archivo, excluir secciones listadas

    2. Split del documento por headings (## Section ID):
       - Detectar pattern: "## D3" o "### D3.subseccion"
       - Si section_id está en ceo_only_sections → skip ese heading y su contenido
         hasta el siguiente heading del mismo nivel

    3. Por cada chunk resultante:
       chunk.source_file = filepath
       chunk.visibility = 'internal' | 'public'
       chunk.section_id = heading_id o None
       chunk.is_ceo_only = False  # si llegó aquí, fue filtrado

    4. Chunking con overlap:
       chunk_size = 500 tokens (aprox)
       overlap = 50 tokens
       split por párrafos preferentemente (no cortar en medio de oración)
    """

# Archivos a excluir completamente (por prefijo):
EXCLUDED_PREFIXES = [
    'LOTE_SM_SPRINT',    # efímeros de ejecución
    'REPORTE_',          # efímeros de sesión
    'PATCH_',            # histórico APPLIED
    'MANIFIESTO_APPEND_',# histórico APPLIED
    'CHECKPOINT_SESSION_',# efímeros
    'GUIA_ALE_',         # efímeros operativos
    'PROMPT_ANTIGRAVITY_',# efímeros operativos
    'PROMPT_',           # prompts de trabajo
]
```

**C — Nginx + SSL + cierre 8001:**
```bash
sudo ufw deny 8001
sudo ufw status | grep 8001   # debe mostrar DENY
```

- **Criterio de done:**
  - [ ] `/ask/` tabla vacía → 200 con message (no 500)
  - [ ] `/ask/` error real inesperado → 500 con log (correcto)
  - [ ] Parser implementa exclusión por sección (`ceo_only_sections:`)
  - [ ] Management command con `--dry-run` reporta qué se cargaría
  - [ ] ≥ 50 archivos cargados en pgvector en staging
  - [ ] Query sobre tema conocido → respuesta con sources
  - [ ] Puerto 8001 cerrado (`ufw deny` verificado)
  - [ ] Nginx proxy funcional
  - [ ] TEST: query sobre sección CEO-ONLY → respuesta sin ese contenido
  - [ ] CEO-12 y CEO-13 cerrados en ENT_GOB_PENDIENTES

---

### FASE 6 — Datos reales (P1 condicional)

#### S16-08: CEO-27 — PaymentTermPricing datos reales
- **Condicional:** CEO provee datos antes del sprint. Si no → SKIP.

**Criterio de done si hay datos:**
- [ ] PaymentTermPricingVersion cargado para clientes activos
- [ ] resolve_client_price() aplica terms correctamente
- [ ] Test: cliente 30d vs 60d → precios diferentes
- [ ] CEO-27 cerrado en ENT_GOB_PENDIENTES

**Criterio de done si SKIP:**
- [ ] Registrado como pendiente en ENT_GOB_PENDIENTES con nota
- [ ] Sin seed placeholder ni tests falsos verdes
- [ ] Sin dato inventado en código

#### S16-09: CEO-28 — CreditClockRule por freight_mode
- **Condicional:** CEO define la regla + S16-02 DONE. Si no → SKIP.

```python
# Solo si CEO define las reglas:
class CreditClockRule(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    freight_mode = models.CharField(
        choices=[('SEA','Marítimo'),('AIR','Aéreo'),('LAND','Terrestre')],
        max_length=10)
    start_event = models.CharField(
        choices=[
            ('on_shipment', 'Al despachar (C9)'),
            ('on_arrival', 'Al arribar (C12)'),
            ('on_invoice', 'Al facturar (C14)'),
        ],
        max_length=20)
    grace_days = models.IntegerField(default=0)
    class Meta:
        unique_together = ('brand', 'freight_mode')
```

Fallback mientras no exista CreditClockRule (declarado en S16-02 C9/C12/C14):
usar `on_arrival` como default para todos los freight_mode.

**Criterio de done si hay definición:**
- [ ] CreditClockRule model + migration
- [ ] Seed reglas por marca según CEO
- [ ] Test: SEA on_arrival vs AIR on_shipment → clock inicia en distinto command
- [ ] CEO-28 cerrado en ENT_GOB_PENDIENTES

**Criterio de done si SKIP:**
- [ ] Registrado en ENT_GOB_PENDIENTES
- [ ] Fallback `on_arrival` activo en C9/C12/C14
- [ ] Sin datos inventados

---

### FASE 7 — Seed Tecmater (P2 condicional)

#### S16-10: BrandWorkflowPolicy Tecmater
- **Condicional:** CEO provee flujo operativo real (estados habilitados,
  commands por estado, artefactos requeridos, SKUs si hay catálogo).
  Si no → SKIP.
- Si hay datos: `python manage.py seed_tecmater_policy`
  BrandWorkflowPolicy Tecmater válida (validador de S14 pasa).
  Tests: flujo Tecmater distinto de Marluvas (PRODUCCION no habilitado para TCM).

**Criterio de done si SKIP:**
- [ ] Nuevo pendiente registrado en ENT_GOB_PENDIENTES con nota:
  "CEO-XX: Seed Tecmater — requiere flujo operativo TCM (estados, commands,
  artefactos). Sin esto BrandWorkflowPolicy Tecmater no se puede generar."
- [ ] Sin seed placeholder en código
- [ ] Sin tests falsos verdes (no crear test que pase con datos inventados)
- [ ] Sin dato inventado en ningún archivo

---

### QA

#### S16-11: Tests Sprint 16
- **Dependencia:** S16-01 a S16-10

**Tests crédito (fix H12 — nuevos):**
- [ ] C1 reserva exposición correctamente (brand × subsidiary)
- [ ] C1 sobre límite sin override → 400 CreditLimitExceeded
- [ ] C1 sobre límite con override C1 → 201 over_limit=true
- [ ] C6 sobre límite sin override C6 → 400 (aunque C1 tuvo override)
- [ ] C6 sobre límite con override C6 → 200 (override específico por command)
- [ ] CancelExpediente libera CreditExposure.reserved
- [ ] C16 CerrarExpediente libera CreditExposure.reserved
- [ ] Cron día 75: alerta creada; día 90: C6 bloqueado para nueva orden
- [ ] CreditOverride solo CEO → 403 otros roles
- [ ] C1 clock expirado Brand A → expediente nace credit_blocked=True (no bloquea Brand B)
- [ ] C1 clock expirado → response incluye credit_check.credit_blocked=True con mensaje
- [ ] C6 con expediente.credit_blocked=True sin override → 400
- [ ] C6 con expediente.credit_blocked=True + CreditOverride C6 → 200
- [ ] C8 con expediente.credit_blocked=True sin override → 400
- [ ] C9 con expediente.credit_blocked=True sin override → 400
- [ ] C14 con expediente.credit_blocked=True sin override → 400
- [ ] Clock Brand A expirado NO bloquea C1 de Brand B mismo cliente

**Tests commands:**
- [ ] C6-C16: cada command acepta estado correcto, rechaza estado incorrecto
- [ ] C16 sin ART-09 → 400; C16 sin pago → 400
- [ ] CancelarExpediente: reason obligatorio (mínimo 10 chars)
- [ ] ReabrirExpediente: solo desde CANCELADO, máx 1 vez, re-evalúa crédito

**Tests legal entities:**
- [ ] Agregar legal_name + tax_id a ClientSubsidiary → persiste
- [ ] Cliente sin CEO role no ve tax_id en response API
- [ ] seed_legal_data --dry-run no persiste datos

**Tests suppliers:**
- [ ] CRUD Supplier completo
- [ ] KPI unique_together → 400 en duplicado
- [ ] /suppliers/?country=CR filtra correctamente
- [ ] /suppliers/{id}/catalog/ sin datos → {count:0, results:[]} (no 404)

**Tests knowledge:**
- [ ] /ask/ tabla vacía → 200 con message
- [ ] /ask/ query conocida → respuesta con sources
- [ ] /ask/ query sobre sección CEO-ONLY → sin ese contenido
- [ ] Puerto 8001 → connection refused desde exterior
- [ ] /ask/ sin JWT → 401

**Tests regresión:**
- [ ] SM S11: 22 commands sin modificación
- [ ] C1-C5 existentes: sin regresión
- [ ] S14 Agreements: exclusion constraints intactos
- [ ] S15 Portal B2B: cross-tenant 404, signed URLs
- [ ] Brand Console S14: 4 tabs funcionales

**CI gate Sprint DONE:**
```
python manage.py test          ✅
bandit -ll backend/            ✅
npm run lint && typecheck       ✅
npm run test                   ✅
smoke: /ask/ → 200             ✅
smoke: Supplier Console carga  ✅
smoke: Portal B2B sin regresión ✅
CI green en main               ✅
```

---

## Dependencias internas

```
S16-00 (Gate) ─────────────────────────────────────────── BLOQUEA TODO
    │
    ├── S16-01A (credit_exposure en C1) ──────────────── P0 AG-02
    │       └── S16-01B (CreditOverride por etapa) ───── P0 AG-02 dep:01A
    │               └── S16-02 (C6-C16 + clock) ──────── P0 AG-02 dep:01A+01B
    │                       └── S16-03 (Cancel+Reopen) ── P0 dep:S16-02
    │
    ├── S16-04 (ClientSubsidiary enriquecida) ──────────── P0 AG-02 independiente
    │
    ├── S16-05 (suppliers/ models + API) ───────────────── P1 AG-02 independiente
    │       └── S16-06 (Supplier Console UI) ────────────── P1 AG-03 dep:S16-05
    │
    ├── S16-07 (Knowledge fix) ────────────────────────── P0 AG-02 independiente
    │
    ├── S16-08 (CEO-27 PaymentTerm) ── condicional dep: dato CEO + S16-02
    ├── S16-09 (CEO-28 CreditClockRule) condicional dep: dato CEO + S16-02
    └── S16-10 (Seed Tecmater) ─────── condicional P2 dep: dato CEO

S16-11 (Tests) ──── después de todo
```

---

## Excluido explícitamente

| Feature | Cuándo |
|---------|--------|
| Portal externo Supplier (login proveedor) | Post-MVP |
| DSL tipado fórmulas pricing | Post-MVP |
| FXRatePolicy multi-moneda | Post-MVP |
| Forecasting KPIs avanzado | Post-MVP |
| WhatsApp Business API (CEO-14) | Cuando Meta confirme |
| ranawalk.com | Post-MVP |
| LLM Intelligence Module (CEO-24) | Sprint 17+ |
| Notificaciones proactivas (CEO-16) | S17+ post-knowledge |
| API versioning /api/v1/ | Post-B2B |
| Paperless-ngx webhook (PLT-01) | Post-S16 |

---

## Deuda que este sprint cierra

| Pendiente | Status post-S16 |
|-----------|----------------|
| CEO-12 Fix /ask/ 500 | ✅ DONE (S16-07) |
| CEO-13 Carga pgvector | ✅ DONE (S16-07) |
| CEO-27 PaymentTermPricing | ✅ DONE o SKIP documentado |
| CEO-28 credit_clock_start_rule | ✅ DONE o SKIP documentado |
| S14 deuda: Supplier Console | ✅ DONE (S16-05/06) |
| S14 deuda: Seed Tecmater | ✅ DONE o SKIP documentado |
| S2 deuda: reloj crédito automático | ✅ DONE (S16-02) |
| Puerto 8001 expuesto (desde S8) | ✅ DONE (S16-07) |
| ClientSubsidiary sin campos legales | ✅ DONE (S16-04) |
| Crédito sin reserva al registrar | ✅ DONE (S16-01A) |
| Sobrecrédito sin modelo formal | ✅ DONE (S16-01B) |

---

## Criterio Sprint 16 DONE

### Obligatorio (P0)
1. credit_exposure_reservation en C1 con evaluación Brand × Subsidiaria
2. CreditOverride model con override por command (sobrecrédito por etapa)
3. Commands C6-C16 con evaluación de sobrecrédito en C6, C8, C9, C14
4. Reloj de crédito automático (día 75 alerta, día 90 bloqueo)
5. CancelarExpediente libera reserva de crédito
6. ClientSubsidiary con legal_name + tax_id + alias (migration aditiva)
7. /api/knowledge/ask/ retorna 200 siempre por tabla vacía/sin resultados
8. pgvector con ≥ 50 archivos cargados, parser excluye ceo_only_sections
9. Puerto 8001 cerrado, Nginx+SSL configurado
10. CI gate verde en main

### Recomendado (P1)
11. Supplier Console UI 4 tabs con datos reales
12. CEO-27 PaymentTermPricing (si CEO provee datos)
13. CEO-28 CreditClockRule (si CEO define regla)
14. ReabrirExpediente re-evalúa crédito al reabrir

### Deseable (P2)
15. Seed Tecmater BrandWorkflowPolicy

---

Stamp: DRAFT v1.3 — Arquitecto (Claude Sonnet 4.6) — 2026-03-23
