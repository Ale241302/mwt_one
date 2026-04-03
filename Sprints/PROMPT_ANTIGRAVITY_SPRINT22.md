# PROMPT_ANTIGRAVITY_SPRINT22 — Pricing Engine + Pricelists + Assignments

## TU ROL
Eres AG-02 (backend developer). Ejecutás el Sprint 22 del proyecto MWT.ONE. Tu trabajo es implementar exactamente lo que dice el LOTE_SM_SPRINT22 v1.6. No diseñás, no proponés alternativas, no expandís scope. Si algo no está claro, preguntás al CEO — no adivinás.

## CONTEXTO
Sprint 22 construye el pricing engine: pricelists versionadas con Grade/multiplicadores por talla, descuentos por pronto pago, assignments por cliente con cache, y conexión con proformas. Es P0 camino crítico — bloquea S23 (rebates) y S24 (autogestión B2B).

**Estado del código (post Sprint 21 DONE asumido):**
- resolve_client_price() v1 en `apps/pricing/services.py` — cascada: PriceList → BCPA
- PriceListItem en `apps/pricing/models.py` — modelo plano S14
- BrandClientPriceAgreement en `apps/agreements/models.py`
- 565 BrandSKUs en ProductMaster
- ExpedienteProductLine con FK a BrandSKU + unit_price editable + price_source
- ArtifactPolicy como constante Python en `artifact_policy.py`
- EventLog extendido con user, proforma, action_source
- Activity feed endpoints funcionales
- ConfigChangeLog + signals en `apps/audit/`

## HARD RULES

1. **State machine FROZEN.** NO tocar handlers de transición. Solo conectar pricing a flujo existente.
2. **PriceListItem S14 intocable.** NO modificar ni eliminar. Es fallback en Paso 2B. Vigencia solo por valid_from/valid_to (NO tiene is_active).
3. **Backward compat.** `resolve_client_price()` sin nuevos params DEBE funcionar igual que v1.
4. **skip_cache=True en Celery.** El recálculo SIEMPRE pasa skip_cache=True. Sin esto lee su propio cache y no recalcula nada.
5. **Dos serializers.** PricingInternalSerializer (CEO/AGENT) y PricingPortalSerializer (CLIENT_*). grade_pricelist_version y size_multipliers NUNCA salen por portal.
6. **storage_key.** Archivos de pricelist se guardan como object_path. Signed URLs se generan al leer con TTL 30min.
7. **Extinción por versión completa.** NUNCA por SKU individual. Si al menos 1 SKU de versión previa es más barato → la versión vive.
8. **EarlyPaymentPolicy mutable.** Excepción a S14-C5. Registrar cambios en ConfigChangeLog via post_save signal.
9. **Locking.** Todo endpoint mutante: `transaction.atomic()` + `select_for_update()`.
10. **MOQ desacoplado.** Precio puede venir de CPA/BCPA/pricelist. MOQ siempre viene del Grade activo. `_resolve_grade_constraints()` se invoca siempre.

## VERIFICACIÓN PREVIA (antes de escribir código)

```bash
# Sprint 21 limpio
python manage.py check
python manage.py test
python manage.py showmigrations | grep "\[ \]"  # 0 pendientes

# Verificar modelos existentes
python manage.py shell -c "from apps.pricing.services import resolve_client_price; print('OK')"
python manage.py shell -c "from apps.pricing.models import PriceListItem; print([f.name for f in PriceListItem._meta.get_fields()])"
python manage.py shell -c "from apps.productos.models import BrandSKU; print(BrandSKU.objects.count())"
python manage.py shell -c "from apps.agreements.models import BrandClientPriceAgreement; print('OK')"
python manage.py shell -c "from apps.audit.models import ConfigChangeLog; print('OK')"

# Verificar que NO existe ya un modelo ClientProductAssignment
grep -rn "ClientProductAssignment" backend/apps/
```

## ITEMS

### FASE 0 — Modelos y migraciones

#### S22-01: PriceListVersion + PriceListGradeItem

```python
# apps/pricing/models.py — AGREGAR (no modificar existentes)

class PriceListVersion(models.Model):
    brand = models.ForeignKey('brands.Brand', on_delete=models.CASCADE, related_name='pricelist_versions')
    version_label = models.CharField(max_length=50)  # Ej: 'Light 2026v6'
    storage_key = models.CharField(max_length=500, null=True, blank=True)  # Object path, NO URL
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=False)
    activated_at = models.DateTimeField(null=True, blank=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    deactivation_reason = models.CharField(max_length=50, null=True, blank=True,
        choices=[('manual', 'Manual CEO'), ('price_decrease', 'Nueva versión más barata'), ('superseded', 'Reemplazada')])
    notes = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-uploaded_at']
        indexes = [models.Index(fields=['brand', 'is_active'])]


class PriceListGradeItem(models.Model):
    pricelist_version = models.ForeignKey(PriceListVersion, on_delete=models.CASCADE, related_name='grade_items')
    reference_code = models.CharField(max_length=80)
    brand_sku = models.ForeignKey('productos.BrandSKU', on_delete=models.PROTECT, null=True, blank=True)
    description_upper = models.CharField(max_length=200, blank=True, default='')
    tip_type = models.CharField(max_length=50, blank=True, default='')
    insole_type = models.CharField(max_length=100, blank=True, default='')
    ncm = models.CharField(max_length=20, blank=True, default='')
    ca_number = models.CharField(max_length=20, blank=True, default='')
    factory_code = models.CharField(max_length=20, blank=True, default='')
    factory_center = models.CharField(max_length=50, blank=True, default='')
    unit_price_usd = models.DecimalField(max_digits=12, decimal_places=2)
    grade_label = models.CharField(max_length=20)  # Ej: '35 ao 45'
    size_multipliers = models.JSONField()  # {'37': 5, '38': 5, '39': 10, ...}

    class Meta:
        unique_together = ['pricelist_version', 'reference_code']
        indexes = [
            models.Index(fields=['pricelist_version', 'brand_sku']),
            models.Index(fields=['reference_code']),
        ]

    @property
    def moq_total(self):
        return sum(self.size_multipliers.values())
```

Verificación:
```bash
python manage.py makemigrations pricing
python manage.py sqlmigrate pricing XXXX  # Solo CreateModel, NO AlterField
python manage.py migrate
```

#### S22-02: ClientProductAssignment
Ver modelo M1 en LOTE. Unique: client_subsidiary + brand_sku.

#### S22-03: EarlyPaymentPolicy + EarlyPaymentTier
Ver modelo M4 en LOTE. Unique: client×brand para policy, policy×days para tier. Registrar signal post_save → ConfigChangeLog.

#### S22-04: Brand.min_margin_alert_pct
AddField nullable. Verificar con sqlmigrate: solo AddField.

### FASE 1 — Servicios

#### S22-05: resolve_client_price() v2

Waterfall completo — ver pseudocódigo en LOTE. Puntos críticos:

1. `skip_cache=False` default. `skip_cache=True` salta Paso 0.
2. Paso 2A: PriceListGradeItem. Paso 2B: PriceListItem S14 (fallback, NO usa is_active).
3. Source values: `'assignment'`, `'agreement'`, `'pricelist_grade'`, `'pricelist_legacy'`, `'manual'`
4. `_resolve_grade_constraints()` se invoca siempre que `size_multipliers` es None (CPA, BCPA, legacy).
5. `_apply_early_payment()` helper para descuento pronto pago.
6. Return dict incluye: price, source, pricelist_version, discount_applied, base_price, grade_moq, size_multipliers, grade_pricelist_version.

#### S22-06: activate_pricelist()
Extinción por versión completa. Ver regla en LOTE S22-06. EventLog obligatorio.

#### S22-07: validate_moq()
Usa size_multipliers del response de resolve. MOQ desacoplado del precio. Ver LOTE.

#### S22-08: Bulk assignment
POST `/api/pricing/client-assignments/bulk/`. Idempotente.

#### S22-09: Recálculo Celery
**SIEMPRE** `skip_cache=True`. Sin esto → bug silencioso.

#### S22-10: Alerta de margen
Solo si Brand.min_margin_alert_pct no es NULL.

### FASE 2 — Upload

#### S22-11 + S22-12: Upload + Confirm
Pandas para CSV/Excel. Preview → confirm. Ver LOTE para detalle de columnas Marluvas.

### FASE 3 — Frontend (AG-03)
Items S22-13 a S22-18. Ver LOTE + GUIA_ALE para detalles.

### FASE 4 — Tests

44 tests obligatorios. Ver lista completa en LOTE S22-19.

Tests críticos a no olvidar:
- #26: skip_cache=True salta paso 0
- #35: CPA + Grade activo → MOQ funciona
- #36: BCPA + Grade activo → MOQ funciona
- #37: Legacy sin Grade → size_multipliers=None, graceful
- #38: Activar pricelist → Celery recalcula con skip_cache=True → precio cambia
- #42: Portal NO retorna source/base_price/discount/size_multipliers/grade_pricelist_version

## COMMIT CONVENTION

```
feat(pricing): S22-01 PriceListVersion + PriceListGradeItem models
feat(pricing): S22-05 resolve_client_price v2 waterfall
feat(pricing): S22-06 activate_pricelist with extinction logic
feat(pricing): S22-09 Celery recalculate assignments
test(pricing): S22-19 44 backend tests
```

## DONE CRITERIA

```bash
python manage.py test  # 44 nuevos + 0 regresiones
python manage.py check --deploy  # 0 warnings
bandit -ll backend/  # 0 high/critical
```

Gate completo en LOTE S22 — 44 tests backend + 20 checks FE manual + 0 regresiones.
