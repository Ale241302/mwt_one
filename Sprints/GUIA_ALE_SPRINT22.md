# GUIA_ALE_SPRINT22 — Sprint 22: Pricing Engine + Pricelists + Assignments

Ale, este sprint construye el motor comercial. Hasta ahora los precios se ingresaban a mano en cada expediente. A partir de Sprint 22, el sistema resuelve precios automáticamente desde pricelists versionadas, aplica descuentos por pronto pago, y maneja assignments por cliente con cache.

---

## El cambio en una frase

**Antes:** CEO ingresa precio manualmente al agregar línea a proforma
**Después:** Sistema sugiere precio automáticamente desde pricelists + descuentos + assignments, CEO puede override

---

## Qué vas a construir (en orden)

### Fase 0 — Modelos (4 modelos nuevos + 1 campo en Brand)

1. **PriceListVersion** — versión de pricelist por brand. N pueden estar activas al mismo tiempo (período de gracia cuando suben precios). Campo `storage_key` para el archivo (NO `file_url` — las signed URLs se generan al leer).

2. **PriceListGradeItem** — item de pricelist con Grade real de Marluvas. Tiene `unit_price_usd` (precio por par, aplica a todas las tallas), `grade_label` (ej: "35 ao 45"), y `size_multipliers` JSON (dict talla→multiplicador MOQ). Esto reemplaza los items planos para items con Grade. **PriceListItem de S14 sigue existiendo como fallback.**

3. **ClientProductAssignment** — asignación permanente de producto a cliente con precio cached. `is_active` toggle (sin vigencia temporal en MVP). Unique por client_subsidiary + brand_sku.

4. **EarlyPaymentPolicy + EarlyPaymentTier** — descuento por pronto pago por cliente×brand. Policy tiene base_payment_days (90) y base_commission_pct (10%). Tiers: plazo→descuento% (8d→2.75%, 30d→1.75%, 60d→1%). **Excepción a inmutabilidad S14-C5:** es mutable en MVP, cambios van a ConfigChangeLog via signal.

5. **Brand.min_margin_alert_pct** — nullable DecimalField. Si tiene valor y un CPA cae debajo, alerta al CEO.

### Fase 1 — Servicios (6 servicios)

6. **Extender resolve_client_price() v2** — el waterfall ahora tiene 5 pasos:
   - Paso 0: CPA cached_client_price (skip si `skip_cache=True`)
   - Paso 1: BCPA override
   - Paso 2A: PriceListGradeItem MIN de todas las activas
   - Paso 2B: PriceListItem S14 fallback (si no hay GradeItem)
   - Paso 3: Manual
   - Post: descuento pronto pago si hay EarlyPaymentPolicy
   
   **Importante:** El dict de retorno incluye `pricelist_version` (fuente del precio) Y `grade_pricelist_version` (fuente del MOQ). Pueden ser distintos cuando el precio viene de CPA/BCPA.

7. **activate_pricelist()** — activa una versión. Lógica de extinción: se extingue una versión previa SOLO si para TODOS los SKUs solapados la nueva tiene precio ≤. Si la previa tiene al menos 1 SKU más barato → no se extingue. `force=True` extingue todas sin evaluar.

8. **validate_moq()** — usa `size_multipliers` del response de resolve. WARNING si cantidad < multiplicador de la talla. ERROR si sum < grade_moq. El ERROR bloquea C5. **MOQ es independiente de la fuente del precio** — siempre viene del Grade activo.

9. **Bulk assignment** — POST `/api/pricing/client-assignments/bulk/`. Recibe product_key → crea N CPAs (1 por talla). Idempotente.

10. **Recálculo Celery** — se dispara al activar pricelist. Recorre CPAs del brand y llama resolve con `skip_cache=True` (CRÍTICO: sin esto lee su propio cache y no recalcula nada).

11. **Alerta de margen** — al final del recálculo, si CPA < Brand.min_margin_alert_pct → alerta.

### Fase 2 — Upload (2 endpoints)

12. **Upload pricelist** — POST multipart, parsing con Pandas (CSV/Excel). Detecta columnas de Marluvas (Referência, Preço, Grade, tallas). Retorna preview — NO crea versión aún.

13. **Confirmar upload** — POST con session_id → crea PriceListVersion + GradeItems. `is_active=False` (CEO activa manualmente).

### Fase 3 — Frontend (6 items)

14. **Pre-fill precio en proforma** — al seleccionar SKU, llama resolve, pre-llena precio + tooltip desglose.

15. **Refactorizar Tab Pricing en Brand Console** — reemplazar items planos por PriceListVersions con GradeItems. Upload → preview → confirm → activar/extinguir.

16. **Enriquecer Tab Catalog en Brand Console** — agregar columnas precio base + MOQ + tallas disponibles. Expandir producto → multiplicadores por talla.

17. **Nuevo Tab Payment Terms** (tab 8) — CRUD EarlyPaymentPolicy + tiers inline.

18. **Nuevo Tab Assignments** (tab 9) — vista por cliente, bulk assign, stale indicator.

19. **Enriquecer Client Console Catalog** — precio con descuento aplicado + MOQ. **NUNCA** muestra source, base_price, cascada, margen. Dos serializers distintos (Internal vs Portal).

### Fase 4 — Tests (44 backend + 20 FE manual)

20. **Tests + validación** — ver lista completa en LOTE.

---

## Reglas que no podés romper

1. **State machine FROZEN** — no toques handlers de transición. El pricing se conecta al flujo existente vía resolve_client_price() que ya se usa.

2. **PriceListItem de S14 sigue vivo** — no lo elimines ni modifiques. Es fallback en Paso 2B. Vigencia solo por valid_from/valid_to (NO tiene is_active).

3. **Backward compat** — resolve_client_price() sin los nuevos params (payment_days, skip_cache, proforma_mode) debe comportarse exactamente como v1.

4. **skip_cache=True en recálculo Celery** — SIN ESTO el recálculo lee su propio cache y no hace nada. Es el bug más fácil de meter.

5. **Dos serializers** — PricingInternalSerializer (CEO/AGENT: todo) y PricingPortalSerializer (CLIENT_*: solo price + moq). Nunca mezclar.

6. **storage_key, no file_url** — signed URLs se generan al leer. Nunca persistir URL firmada en DB.

7. **EarlyPaymentPolicy mutable** — excepción explícita a S14-C5. Cambios van a ConfigChangeLog via post_save signal.

8. **Extinción por versión completa** — nunca por SKU individual. Si al menos 1 SKU de la previa es más barato → la versión previa vive.

---

## Orden de ejecución sugerido

```
Día 1-2:  S22-01 + S22-02 + S22-03 + S22-04 (modelos + migraciones)
Día 3-4:  S22-05 + S22-06 (waterfall v2 + extinción)
Día 5-6:  S22-07 + S22-08 (MOQ + bulk)
Día 7-8:  S22-09 + S22-10 (Celery + alerta)
Día 9-10: S22-11 + S22-12 (upload + confirm)
Día 11-12: S22-19 (tests)
```

AG-03 en paralelo:
```
Día 1-3:  S22-15 (catalog enrichment)
Día 3-5:  S22-14 (pricelists tab refactor)
Día 5-6:  S22-16 + S22-17 (payment terms + assignments)
Día 7-8:  S22-13 (pre-fill expediente)
Día 8-9:  S22-18 (client console catalog)
Día 10:   S22-20 (validación manual FE)
```

---

## Verificación antes de empezar

```bash
python manage.py check
python manage.py test
python manage.py showmigrations | grep "\[ \]"  # 0 pendientes

# Verificar que resolve_client_price v1 existe
python manage.py shell -c "from apps.pricing.services import resolve_client_price; print('OK')"

# Verificar PriceListItem S14
python manage.py shell -c "from apps.pricing.models import PriceListItem; print(PriceListItem.objects.count())"

# Verificar BrandSKU count
python manage.py shell -c "from apps.productos.models import BrandSKU; print(BrandSKU.objects.count())"
```

---

## Si algo no está claro

No adivinés. Preguntá al CEO. Especialmente:
- Si `PriceListItem` de S14 tiene campos que no esperás
- Si `resolve_client_price` v1 tiene parámetros diferentes a lo documentado
- Si necesitás crear modelos adicionales no listados acá
