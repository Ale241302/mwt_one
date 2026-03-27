# GUÍA ALEJANDRO — Sprint 18: Motor Dimensional + Endpoints
## Para: Alejandro (AG-02 Backend) · Fecha: 2026-03-26

---

## Qué es este sprint

Sprint 18 hace dos cosas grandes:

**A) Motor de tallas como servicio de plataforma.** En vez de que cada marca tenga su propio sistema de tallas hardcodeado, creamos una app `sizing/` que cualquier marca puede usar. Rana Walk tiene S1-S6, Marluvas tiene 33-48, y si mañana entra una marca de ropa con tallas de camisa (cuello/pecho/cintura), el mismo motor lo soporta. Tecmater puede usar el mismo sistema BR 33-48 que Marluvas sin crear uno nuevo.

**B) Endpoints backend para todo lo de Sprint 17.** Los modelos que creaste (ExpedienteProductLine, FactoryOrder, ExpedientePago, los 30 campos operativos) ahora se exponen como API REST: PATCH por estado, CRUD de órdenes de fábrica, registro y confirmación de pagos, merge y split de expedientes, y el bundle de detalle completo.

---

## Prerequisito

Sprint 17 DONE (14/14 items). Antes de empezar:
```bash
python manage.py test
# Si no pasa → no arrancar. Resolver primero.
```

---

## Orden de ejecución (2 fases, no mezclar)

### Fase 0 — Motor dimensional + fixes (hacer primero)

| # | Qué | Tiempo estimado | Notas |
|---|-----|-----------------|-------|
| 0.1 | Crear app `sizing/` con 6 modelos + seed | 2-3 horas | Es la parte más nueva. Seguí el prompt al pie de la letra. El seed tiene todos los datos de RW y Marluvas ya escritos. |
| 0.2 | FK brand_sku en ExpedienteProductLine | 15 min | Un campo nullable. No rompe nada. |
| 0.3 | Fix pricing valid_to=null | 30 min | **IMPORTANTE:** Antes de tocar, corré `grep -n "valid_" apps/pricing/models.py`. Si ves `DateRangeField` → avisame, el fix es diferente. |
| 0.4 | 6 campos nullable | 30 min | 5 nullable + 1 BooleanField default=False (credit_released). |
| 0.5 | Hook dispatcher | 15 min | 5 líneas. Lista de callables post-command. |

**Gate:** `python manage.py test` verde después de aplicar migración. Si no pasa → no avanzar a Fase 1.

### Fase 1 — Endpoints (después de Fase 0 DONE)

| # | Qué | Tiempo estimado | Notas |
|---|-----|-----------------|-------|
| 1.1 | Serializers | 1 hora | El BundleSerializer expone `credit_released` y `credit_exposure`, NO `credit_status` a nivel expediente. |
| 1.2 | 5 PATCH por estado | 2 horas | CONFIRMADO, PREPARACION, PRODUCCION, DESPACHO, TRANSITO. Cada uno valida estado correcto → 409 si no. |
| 1.3 | CRUD FactoryOrder | 1.5 horas | **Clave:** después de cada POST/PATCH/DELETE, llamar `sync_factory_order_number()`. |
| 1.4 | Pagos + confirmación | 1.5 horas | POST crea PENDING. PATCH confirmar → CONFIRMED + recálculo crédito. **Nunca** auto-release al registrar. |
| 1.5 | Merge | 1 hora | Solo expedientes en REGISTRO/PI_SOLICITADA/CONFIRMADO. Followers vía c_cancel. |
| 1.6 | Split | 1 hora | No dejar expediente vacío (error si se separan todas las líneas). |
| 1.7 | Actualizar C1 | 1 hora | Acepta brand_sku + incoterms. Backward compat: sin campos nuevos funciona igual. |
| 1.8 | recalculate_credit | 30 min | **Regla de oro:** SOLO esta función setea credit_released. Nadie más. Bidireccional. |
| 1.9 | Sync CreditExposure | 30 min | Post-recálculo: si credit_released cambió → actualizar CreditExposure del cliente. |
| 1.10 | Chain resolver | 1 hora | Refactorear resolve_client_price a lista de resolvers encadenados. |
| 1.11 | EventLog | 30 min | 3 campos nuevos: event_type, previous_status, new_status. |

---

## Las 3 reglas que no podés romper

1. **credit_released lo setea SOLO recalculate_expediente_credit().** Si ves que otro lugar quiere setear este campo → está mal. Solo esa función. Bidireccional: pagos cubren todo → True. Merge sube exposure → False.

2. **factory_order_number es read-only.** Se sincroniza automáticamente desde la FactoryOrder con menor ID. Llamá `sync_factory_order_number()` después de cada operación en el viewset. Nunca editarlo en un PATCH.

3. **Pagos: PENDING → confirmar → CONFIRMED.** El flujo es: el CEO registra un pago (nace PENDING), después lo confirma (cambia a CONFIRMED + recálculo + sync crédito). Un pago recién creado nunca libera crédito.

---

## Migración

Una tanda coordinada (una migración por app):
```bash
python manage.py makemigrations sizing expedientes pricing clientes
# Revisar cada archivo generado — solo CreateModel + AddField
python manage.py migrate
python manage.py check
python manage.py test
```

---

## Cuando termines

- `python manage.py test` verde (todo, no solo lo nuevo)
- `bandit -ll backend/` sin high/critical
- Conventional commits: `feat: create sizing app`, `feat: add PATCH endpoints`, etc.
- Avisame con el resumen de lo que hiciste

---

## Si algo no matchea

El código real puede tener diferencias con lo que dice el prompt (campos con otro nombre, modelos en otra ubicación). **Siempre verificá con grep antes de asumir.** Si encontrás algo raro:
- Es un campo/modelo que ya existe → no crear de nuevo, solo extender
- Es un campo con otro nombre → usá el nombre real
- Es algo que no existe y no sabés dónde va → preguntame

El prompt de Antigravity (PROMPT_ANTIGRAVITY_SPRINT18.md) tiene los detalles técnicos completos. Esta guía es tu mapa de navegación.
