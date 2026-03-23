# GUÍA ALEJANDRO — Sprint 16: Crédito + Supplier Console + Knowledge Fix
## Para: Alejandro (AG-02 Backend + AG-03 Frontend) · Fecha: 2026-03-23

---

## Qué es este sprint

Sprint mixto: backend P0 + UI proveedor + infraestructura knowledge. Tres cosas
que llevan tiempo pendientes y que ahora se pueden hacer porque el modelo de
crédito ya está bien definido y el Portal B2B de S15 está estable.

En resumen: el sistema aprende a proteger el crédito desde el momento en que
registrás un pedido (no solo al despachar), aprende a gestionar proveedores,
y el canal de knowledge finalmente funciona.

---

## Contexto del "por qué" de cada pilar

### Pilar 1 — Crédito desde el registro

Hoy el sistema no reserva crédito cuando creás un expediente. Solo lo evalúa
más tarde (si es que lo evalúa). Eso significa que podés registrar 5 pedidos
a Sondel CR que juntos superan su línea de crédito y el sistema no dice nada.

La regla real: **el crédito se consume desde que registrás el pedido**.
Exposición = lo que está en producción + lo que está en tránsito + lo que
está facturado sin cobrar. Cada pedido nuevo se suma a ese total.

Importante: el crédito es **por marca**. La línea de Sondel CR con Marluvas
es independiente de la línea de Sondel CR con Rana Walk o con Tecmater.
Si Marluvas les bloqueó el crédito, eso no afecta para nada el crédito con RW.

Y el sobrecrédito no es un bloqueo total — el CEO puede autorizar un override,
pero ese override solo sirve para ese command específico. No abre la puerta
para toda la cadena.

### Pilar 2 — Commands C6-C16

Los commands C1-C5 están implementados. Los C6-C16 existen como stubs o
implementación básica pero sin la lógica de negocio real: sin validación de
artefactos gate, sin evaluación de crédito, sin el reloj de cobro.

Este sprint los completa. También agrega la cancelación formal con liberación
de crédito reservado.

### Pilar 3 — Legal entities completas

ClientSubsidiary existe desde S14 pero sin datos legales. Para operar bien
necesitás saber el RUC/NIT/cédula jurídica de cada entidad — es lo que va
en documentos, contratos y facturación. Este sprint agrega esos campos de
forma aditiva (sin romper nada).

### Pilar 4 — Supplier Console

El modelo de proveedor fue diseñado y auditado 9.6/10 hace una semana.
BrandSupplierAgreement ya existe en agreements/. Solo faltaba construir la
app `suppliers/` y la UI para gestionar proveedores con sus KPIs de desempeño.

### Pilar 5 — Knowledge fix

El endpoint `/api/knowledge/ask/` da 500 desde Sprint 8. La causa más probable:
pgvector vacío → query sin resultados → excepción no manejada. Este sprint
lo arregla, carga los .md en pgvector, y cierra el puerto 8001 detrás de Nginx.

---

## Prerequisito

Sprint 15 DONE. El Portal B2B tiene que estar estable antes de arrancar.
Corré S16-00 (gate) primero — si algo falla en staging, avísale al CEO antes
de tocar código.

---

## Orden de ejecución

```
PARALELO (pueden arrancar al mismo tiempo):
  S16-01A (crédito en C1)         ─┐
  S16-04 (ClientSubsidiary campos) ─┤ AG-02, independientes entre sí
  S16-05 (suppliers/ models + API) ─┤
  S16-07 (knowledge fix)           ─┘

SECUENCIAL (después de S16-01A):
  S16-01B (CreditOverride model)
  S16-02 (commands C6-C16)         ← depende de 01A + 01B
  S16-03 (cancelación + reapertura) ← depende de 02

FRONTEND (después de su backend correspondiente):
  S16-06 (Supplier Console UI)     ← después de S16-05

CONDICIONALES (solo si CEO provee datos):
  S16-08 (PaymentTermPricing)
  S16-09 (CreditClockRule)
  S16-10 (Seed Tecmater)
```

---

## Items por agente

### AG-02 Backend

---

#### S16-01A: Reserva de crédito en C1

**Archivo:** `backend/apps/expedientes/services/commands/c1.py`

En `create_expediente`, ANTES de confirmar el registro, evaluar crédito:

```python
def check_and_reserve_credit(expediente, brand, subsidiary):
    from backend.apps.agreements.models import CreditPolicy, CreditExposure, CreditOverride

    policy = CreditPolicy.objects.get_active(brand=brand, subsidiary=subsidiary)
    if not policy:
        # Sin política de crédito → permitir sin reserva
        return {'allowed': True, 'over_limit': False}

    exposure = CreditExposure.objects.calculate(brand=brand, subsidiary=subsidiary)
    order_amount = expediente.snapshot.order_total

    new_total = exposure.total + order_amount
    over_limit = new_total > policy.credit_limit

    # Verificar override formal (NO usar boolean credit_override_approved — no existe)
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

    # Verificar clock expirado (INDEPENDIENTE del sobrecrédito)
    credit_blocked = CreditExposure.is_clock_expired(brand=brand, subsidiary=subsidiary)
    expediente.credit_blocked = credit_blocked

    # Siempre reservar — incluso si credit_blocked
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
            "Línea de crédito vencida. Pedido registrado pero producción "
            "bloqueada hasta autorización CEO." if credit_blocked else None
        )
    }
```

**Respuesta de C1** incluye `credit_check` block. Si `credit_blocked=True` →
HTTP 201 (se registró) pero con warning en body.

**Tests a crear:** `test_credit_reservation.py`
- Registro con crédito disponible → reserva correcta
- Registro sin CreditPolicy → permitido
- Registro sobre límite sin override → 400 CreditLimitExceeded
- Registro sobre límite con override C1 → 201 over_limit=true
- Clock expirado Brand A → credit_blocked=True, registra igual
- Clock expirado Brand A NO afecta Brand B mismo cliente

---

#### S16-01B: CreditOverride model

**Archivo:** `backend/apps/agreements/models.py`

```python
class CreditOverride(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    expediente = models.ForeignKey('expedientes.Expediente',
                                    on_delete=models.CASCADE,
                                    related_name='credit_overrides')
    brand = models.ForeignKey('brands.Brand', on_delete=models.PROTECT)
    subsidiary = models.ForeignKey('clientes.ClientSubsidiary',
                                    on_delete=models.PROTECT)
    command_code = models.CharField(max_length=10)
    # Un CreditOverride = un command = una autorización.
    # No hay campo separado para "válido para" — command_code lo es todo.
    amount_over_limit = models.DecimalField(max_digits=14, decimal_places=2)
    authorized_by = models.ForeignKey('users.MWTUser', on_delete=models.PROTECT)
    reason = models.TextField()   # mínimo 10 chars — validar en serializer
    authorized_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('expediente', 'command_code')
```

**Endpoint:**
```
POST /api/agreements/credit-override/
Body: { "expediente_id": "...", "command_code": "C1", "reason": "..." }
Solo CEO (is_superuser) → 403 para otros roles
Crea CreditOverride + EventLog
```

---

#### S16-02: Commands C6-C16

**Archivos:** `backend/apps/expedientes/services/commands/c6.py` a `c16.py`

Mapping completo (ref → ENT_OPS_STATE_MACHINE FROZEN v1.2.2):

| Command | De | A | Gate artefactos | Evalúa crédito |
|---------|-----|---|-----------------|----------------|
| C6 ConfirmarProduccion | REGISTRO | PRODUCCION | ART-01,02,03,04 | ✅ + credit_blocked |
| C7 RegistrarFechaProduccion | PRODUCCION | PRODUCCION | — | — |
| C8 ConfirmarPreparacion | PRODUCCION | PREPARACION | ART-05 | ✅ + credit_blocked |
| C9 RegistrarDespacho | PREPARACION | DESPACHO | ART-06 | ✅ + credit_blocked + clock |
| C10 ConfirmarTransito | DESPACHO | TRANSITO | — | — |
| C11 RegistrarETA | TRANSITO | TRANSITO | — | — |
| C12 ConfirmarArribo | TRANSITO | EN_DESTINO | — | clock si on_arrival |
| C13 RegistrarNacionalizacion | EN_DESTINO | EN_DESTINO | ART-08 | — |
| C14 EmitirFactura | EN_DESTINO | EN_DESTINO | ART-09 | ✅ + clock si on_invoice |
| C15 RegistrarPago | EN_DESTINO | EN_DESTINO | — | — |
| C16 CerrarExpediente | EN_DESTINO | CERRADO | ART-09 + pago | libera reserva |

**Para C6, C8, C9, C14 — hook de crédito:**
```python
def check_credit_for_command(expediente, command_code):
    if expediente.credit_blocked:
        has_override = CreditOverride.objects.filter(
            expediente=expediente, command_code=command_code
        ).exists()
        if not has_override:
            raise CreditBlockedError(
                f"Crédito bloqueado para este expediente. "
                f"Requiere override CEO para {command_code}."
            )
    # también evaluar sobrecrédito si aplica...
```

**C9 y C12** — hook del reloj:
```python
# En C9:
rule = CreditClockRule.objects.filter(
    brand=expediente.brand,
    freight_mode=expediente.freight_mode
).first()
start_event = rule.start_event if rule else 'on_arrival'  # fallback

if start_event == 'on_shipment':
    trigger_credit_clock(expediente)

# En C12:
if start_event == 'on_arrival':
    trigger_credit_clock(expediente)
```

**C16** — liberar reserva al cerrar:
```python
CreditExposure.release(
    brand=expediente.brand,
    subsidiary=expediente.client,
    expediente=expediente
)
```

**Reloj automático** — management command scheduleable:
```bash
python manage.py check_credit_clocks
```
- Día 75: alerta + `expediente.credit_warning = True`
- Día 90: evento `credit_clock.expired` + bloquear C6 para nuevas órdenes
  de esa subsidiaria × brand hasta CEO desbloqueo manual

---

#### S16-03: Cancelación y reapertura CEO

**Archivos:** `c_cancel.py` + `c_reopen.py`

**CancelarExpediente:**
- Cualquier estado != CERRADO/CANCELADO
- Solo CEO — `403` para otros roles
- `reason` obligatorio, mínimo 10 chars — `400` si no cumple
- Libera `CreditExposure.reserved` para este expediente
- EventLog → CANCELADO

**ReabrirExpediente:**
- Solo desde CANCELADO, solo CEO
- `justification` obligatorio
- Re-evalúa crédito al reabrir (re-reserva)
- → REGISTRO
- Constraint: máximo 1 reapertura por expediente → `400` si ya fue reabierto

---

#### S16-04: ClientSubsidiary — campos legales

**Archivo:** `backend/apps/clientes/models.py`

Migración aditiva — todos nullable:
```python
legal_name = models.CharField(max_length=300, blank=True, null=True)
# "SONDEL S.A." — nombre legal exacto para documentos

tax_id = models.CharField(max_length=50, blank=True, null=True)
# Cédula jurídica / NIT / RUC / CNPJ según país

# alias ya debería existir — verificar antes de agregar
# country ya debería existir — verificar antes de agregar
```

**⚠️ ANTES de agregar campos, verificar qué ya existe** en `ClientSubsidiary`
(S14 los puede tener). Solo agregar lo que realmente falta.

**SSOT de crédito:** `CreditPolicy.credit_limit` (ya existe en agreements/).
**NO** agregar `credit_limit` a `ClientSubsidiary` — son dos verdades y rompe
POL_DETERMINISMO.

**Management command:** `seed_legal_data --file legal_data.csv`
Los tax_ids son [PENDIENTE — CEO_INPUT_REQUIRED] hasta que el CEO los provea.

**Serializer:** Exponer los campos nuevos en `/api/clientes/{id}/`.
`tax_id` solo visible para `is_superuser` (CEO).

---

#### S16-05: App suppliers/

**Directorio:** `backend/apps/suppliers/`

Crear: `models.py`, `api/serializers.py`, `api/views.py`, `api/urls.py`,
`migrations/`, `tests/test_suppliers.py`, `admin.py`

**Modelos:** Supplier + SupplierContact + SupplierPerformanceKPI
(ver LOTE_SM_SPRINT16.md §S16-05 para definición completa)

**BrandSupplierAgreement** ya existe en `agreements/` de S14.
Hacer FK a él — **no duplicar**.

**Endpoints con query params:**
```
GET /api/suppliers/?search=&country=&brand=&is_active=
POST /api/suppliers/
GET/PATCH /api/suppliers/{id}/
GET/POST /api/suppliers/{id}/contacts/
GET/POST /api/suppliers/{id}/kpis/
GET /api/suppliers/{id}/agreements/
GET /api/suppliers/{id}/expedientes/
GET /api/suppliers/{id}/catalog/  ← retorna {count:0, results:[]} si no hay datos
```

`/catalog/` nunca retorna 404 — retorna lista vacía si no hay ProductMaster
con supplier_id. Si el campo `supplier` no existe en ProductMaster (S14),
retornar vacío y dejar nota `# TODO: agregar supplier FK a ProductMaster`.

---

#### S16-07: Knowledge fix + pgvector + Nginx

**Objetivo:** eliminar el 500 en `/api/knowledge/ask/`, cargar los .md,
cerrar el puerto 8001.

**Paso 1 — Diagnóstico:**
```bash
docker logs mwt-knowledge --tail=100 2>&1 | grep -A 20 "ERROR\|Traceback"
```

**Paso 2 — Fix del 500 en `knowledge/views.py`:**
```python
try:
    results = vector_store.similarity_search(query, k=5)
    if not results:
        return Response({
            "answer": "",
            "sources": [],
            "message": "Knowledge base sin contenido indexado aún."
        }, status=200)
    # lógica con LLM...
except Exception as e:
    logger.error(f"Knowledge ask unexpected error: {e}", exc_info=True)
    return Response({"error": "Error inesperado."}, status=500)
```

Política: **200** para tabla vacía/sin resultados. **500** solo para errores
reales inesperados (LLM caído, DB corruption).

**Paso 3 — Management command `load_knowledge`:**

`backend/apps/knowledge/management/commands/load_knowledge.py`

Opciones: `--path`, `--chunk-size 500`, `--overlap 50`, `--dry-run`, `--clear`

Excluir archivos con estos prefijos:
```
LOTE_SM_SPRINT*, REPORTE_*, PATCH_* (APPLIED), MANIFIESTO_APPEND_*,
CHECKPOINT_SESSION_*, GUIA_ALE_*, PROMPT_ANTIGRAVITY_*, PROMPT_*
```

Excluir secciones CEO-ONLY: leer `ceo_only_sections:` del front matter YAML.
Split por headings `##` y `###`. Si el heading_id está en `ceo_only_sections:`
→ skip esa sección y su contenido hasta el siguiente heading del mismo nivel.
Nunca embedar contenido CEO-ONLY.

Primero correr con `--dry-run` para ver qué cargaría. Luego sin `--dry-run`.
Objetivo: ≥ 50 archivos cargados en staging.

**Paso 4 — Nginx + cerrar puerto 8001:**
```bash
sudo ufw deny 8001
sudo ufw status | grep 8001   # debe mostrar DENY
```
Configurar Nginx proxy hacia localhost:8001 con SSL.

---

#### S16-08, S16-09, S16-10 — Condicionales

**S16-08 (CEO-27 PaymentTermPricing):** Solo si el CEO te pasa un CSV con los
datos reales de términos de pago por cliente. Si no → marcás SKIP con nota
en el PR y seguís.

**S16-09 (CEO-28 CreditClockRule):** Solo si el CEO define explícitamente
cuándo empieza el reloj para cada marca y modo de flete. Mientras no esté
definido, el fallback es `on_arrival` para todo — ya está implementado así
en C9/C12. Si el CEO define → creás el model y seed con sus reglas.

**S16-10 (Seed Tecmater):** Solo si el CEO te pasa el flujo operativo de
Tecmater (qué estados, qué commands, qué artefactos). Sin eso → SKIP.

Para los tres: si SKIP, documentá en el PR con `# TODO: CEO_INPUT_REQUIRED`
y NO inventés valores. El sistema funciona sin estos datos — solo
los items condicionales quedan en stand-by.

---

### AG-03 Frontend

---

#### S16-06: Supplier Console UI

**Prerequisito:** S16-05 DONE (APIs disponibles).

**Archivos:**
- `frontend/src/app/[lang]/dashboard/suppliers/page.tsx` — lista
- `frontend/src/app/[lang]/dashboard/suppliers/[id]/page.tsx` — detalle 4 tabs

**Lista:** tabla con nombre/país/contacto principal/OTIF último período.
Filtros: `?search=`, `?country=`, `?brand=`. FormModal para nuevo proveedor.

**Detalle — 4 tabs:**

**Tab 1 Identidad:** nombre, nombre legal, país, ciudad, email. Tabla contactos.
Payment terms, incoterm, moneda.

**Tab 2 Acuerdos:** lista BrandSupplierAgreement de S14. Read-only para MVP.
Si no hay acuerdos → empty state.

**Tab 3 Catálogo:** `GET /api/suppliers/{id}/catalog/`
Si `count === 0` → empty state "Sin catálogo registrado". No inventar.

**Tab 4 KPIs:** tabla histórica con FormModal "Registrar período".
Mostrar valores numéricos. Los semáforos de color son condicionales —
solo aplicar si `ENT_GOB_KPI` tiene umbrales definidos formalmente.
Si no → mostrar datos sin colores y dejar `// TODO: umbrales pendientes CEO`.

**Sidebar:** agregar "Proveedores" bajo sección Configuración.

**Reglas:**
- 0 hex hardcodeados — todos los colores via CSS variables
- Empty states correctos en todos los tabs (no crashes, no 404s en UI)
- Paginación DRF: detectar automáticamente `{count, next, results}` vs array plano

---

## Migración — resumen de campos nuevos

Todos additive. Si algo sale mal → revert migration.

| Campo | Modelo | App | Default/Null |
|-------|--------|-----|-------------|
| credit_blocked | Expediente | expedientes | default=False |
| credit_warning | Expediente | expedientes | default=False |
| CreditOverride | — | agreements | tabla nueva |
| CreditClockRule | — | agreements | tabla nueva (condicional) |
| legal_name | ClientSubsidiary | clientes | null=True |
| tax_id | ClientSubsidiary | clientes | null=True |
| Supplier | — | suppliers | tabla nueva |
| SupplierContact | — | suppliers | tabla nueva |
| SupplierPerformanceKPI | — | suppliers | tabla nueva |

---

## Lo que NO tocás

- ❌ `ENT_OPS_STATE_MACHINE` — FROZEN, ni lo abras
- ❌ CreditPolicy.credit_limit — ya existe en S14, no duplicar
- ❌ BrandSupplierAgreement — ya existe en agreements/, no duplicar
- ❌ ALTER destructivo o rename en ninguna tabla
- ❌ docker-compose.yml, nginx/ (excepto agregar el bloque knowledge)
- ❌ Datos de negocio inventados — si no tenés el dato, `# TODO: CEO_INPUT_REQUIRED`

---

## Checklist de entrega

```
ANTES DE EMPEZAR
[ ] S16-00 (gate): Sprint 15 DONE en staging
[ ] Tests suite existente pasan

BACKEND
[ ] check_and_reserve_credit() en C1 funciona
[ ] CreditOverride model + endpoint CEO-only
[ ] C6-C16 con gates de artefactos + evaluación crédito
[ ] credit_blocked bloquea C6/C8/C9/C14 sin override CEO
[ ] C16 libera CreditExposure.reserved
[ ] CancelarExpediente libera crédito + EventLog
[ ] ClientSubsidiary: legal_name + tax_id (additive, no credit_limit)
[ ] App suppliers/ con 11 endpoints y query params
[ ] /catalog/ retorna lista vacía (no 404)
[ ] /api/knowledge/ask/ retorna 200 para tabla vacía
[ ] load_knowledge --dry-run reporta correctamente
[ ] ≥ 50 archivos cargados en pgvector
[ ] Puerto 8001 cerrado (ufw deny)

FRONTEND
[ ] Supplier Console lista + 4 tabs funcionales
[ ] Empty states correctos
[ ] 0 hex hardcodeados
[ ] Sidebar actualizado

TESTS
[ ] Reserva crédito: con/sin límite, con/sin override
[ ] credit_blocked: C6/C8/C9/C14 sin override → 400
[ ] Clock Brand A no afecta Brand B
[ ] Cancelar libera crédito
[ ] /ask/ tabla vacía → 200
[ ] /ask/ query CEO-ONLY → sin ese contenido
[ ] test_cross_tenant_access S15 sigue pasando
[ ] SM S11: tests sin modificación
[ ] python manage.py test — 0 failures
[ ] bandit -ll backend/ — sin críticos

ITEMS CONDICIONALES (si CEO provee datos)
[ ] S16-08 PaymentTermPricing O documentado SKIP
[ ] S16-09 CreditClockRule O documentado SKIP
[ ] S16-10 Seed Tecmater O documentado SKIP
```

---

## Reporte de ejecución (entregá esto al terminar)

```markdown
## Resultado Sprint 16
- **Agente:** AG-02 + AG-03 Alejandro
- **Status:** DONE / PARTIAL / BLOCKED
- **Archivos creados:** [lista]
- **Archivos modificados:** [lista]
- **Archivos NO tocados:** ENT_OPS_STATE_MACHINE, CreditPolicy, BrandSupplierAgreement
- **Condicionales ejecutados:** S16-08 DONE/SKIP · S16-09 DONE/SKIP · S16-10 DONE/SKIP
- **Decisiones asumidas:** [lo que decidiste sin spec explícita]
- **Blockers:** [lista o "ninguno"]
- **Tests ejecutados:** [resumen]
- **CEO_INPUT_REQUIRED pendientes:** [si quedó alguno]
- **Puerto 8001:** cerrado / pendiente
- **pgvector archivos cargados:** [número]
```
