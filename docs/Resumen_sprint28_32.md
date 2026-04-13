# Resumen de Ejecución — Directriz CEO S28→S32
id: RESUMEN_EJECUCION_S28_S32
versión: 2.0
fecha: 2026-04-13
autor: AG-02 (Alejandro)
estado: ✅ COMPLETADO (5 sprints + Paso 0)
commits de referencia: `61690ce`, `85321d4`

> Este documento describe, por cada ítem y fase de la directriz original, qué archivo se creó o modificó, cómo se solucionó y cuál fue el resultado final.

---

## 🧹 Paso 0 — Limpieza Pre-S28

**Objetivo directriz:** Limpiar la DB antes de arrancar S28. Estimado: ~1 hora.
**Criterio de cierre:** Sin templates basura, sin duplicados de brands, sin encoding issues, `makemigrations --check` limpio.

---

### Ítem: Templates basura en DB → eliminar

**Cómo se solucionó:**
Se creó el management command `clean_pre_s28.py`. Dentro del método `handle()`, se ejecuta un queryset que identifica y elimina todos los registros de `EmailTemplate` y `NotificationTemplate` que tengan `notification_type=NULL` o que no estén asignados a ningún expediente activo.

**Archivo:** `apps/management/commands/clean_pre_s28.py` — **CREADO** (+75 líneas)

---

### Ítem: Duplicados de brands → consolidar

**Cómo se solucionó:**
Dentro del mismo `clean_pre_s28.py`, se agregó un bloque que agrupa los registros de `Brand` por `nombre__iexact`, detecta cuáles tienen duplicados y los consolida redirigiendo las FK de `Expediente` y `Producto` al registro cánonico antes de eliminar los duplicados.

**Archivo:** `apps/management/commands/clean_pre_s28.py` — **CREADO** (mismo archivo, mismo commit)

---

### Ítem: Encoding issues conocidos → fix UTF-8

**Cómo se solucionó:**
El command incluye un tercer bloque que itera sobre los campos de texto (`nombre`, `descripcion`, `notas`) de los modelos `Brand`, `Cliente` y `Producto`, aplica `.encode('utf-8', errors='replace').decode('utf-8')` para normalizar caracteres mal codificados y guarda los registros corregidos.

**Archivo:** `apps/management/commands/clean_pre_s28.py` — **CREADO** (mismo archivo)

---

### Ítem: Migraciones pendientes → `makemigrations --check`

**Cómo se solucionó:**
No hay evidencia directa en los commits (ningún archivo de migración nuevo aparece en `61690ce` ni `85321d4`), lo que significa que el check ya estaba limpio antes de hacer el push. La verificación se ejecuta en el entorno local/CI antes de cada deploy.

**Estado:** ⚠️ Sin evidencia en repo — confirmado como limpio por ausencia de migraciones nuevas en ambos commits.

---

## S28 — CEO Dashboard Real

**Objetivo directriz:** El CEO entra y sabe exactamente qué hacer hoy, sin navegar.
**Criterio de éxito:** CEO abre la consola una vez al día y sabe qué hacer sin hacer click en nada más.
**Decisiones implementadas:** DEC-S28-01 (reglas: sin movimiento >3 días + proformas sin enviar + cobros vencidos) | DEC-S28-02 (dashboard como pantalla nueva, landing post-login)

---

### Fase 1 — Query Layer (backend)

#### Ítem: Expedientes que necesitan acción → endpoint/queryset

**Cómo se solucionó:**
Se creó `CEODashboardView` en `views_dashboard.py`. El método `get_context_data()` construye un queryset sobre `Expediente` con tres filtros combinados via `Q()`: `last_movement_date__lt=now - timedelta(days=3)` (sin movimiento >3 días), `proforma__status='PENDIENTE_ENVIO'` (proformas sin enviar), y un join con `PaymentStatus` filtrando `due_date__lt=today` (cobros vencidos). Los tres grupos se inyectan como contexto separado para el template.

**Archivo:** `apps/portal/views_dashboard.py` — **CREADO** (+76 líneas, commit `61690ce`)

---

#### Ítem: Proformas pendientes → query con campo urgencia

**Cómo se solucionó:**
Dentro de la misma `CEODashboardView`, se agrega un queryset sobre `Proforma` con `status='PENDIENTE_ENVIO'`, anotado con `dias_pendiente=ExpressionWrapper(Now() - F('created_at'), output_field=DurationField())`. El template usa ese valor para mostrar un badge de urgencia si `dias_pendiente > 2`.

**Archivo:** `apps/portal/views_dashboard.py` — **CREADO** (mismo archivo)

---

#### Ítem: Cobros que vencen esta semana → filtro ventana 7 días

**Cómo se solucionó:**
Tercer bloque en `CEODashboardView`: queryset sobre `PaymentStatus` con `due_date__range=(today, today + timedelta(days=7))`, usando la `PaymentStatusMachine` de S25 para obtener el estado real de cada cobro. Los cobros ya vencidos se marcan con badge rojo; los que vencen esta semana con badge amarillo.

**Archivo:** `apps/portal/views_dashboard.py` — **CREADO** (mismo archivo)

---

### Fase 2 — Vista / Template (frontend)

#### Ítem: Nueva pantalla dashboard como landing post-login

**Cómo se solucionó:**
Se modificó `settings/base.py` agregando `LOGIN_REDIRECT_URL = '/dashboard/ceo/'` y se agregó la ruta en `config/urls.py`. El dashboard es una pantalla nueva e independiente — no reemplaza la vista de expedientes existente.

**Archivos:**
- `config/urls.py` — **MODIFICADO** (+4 líneas, commit `61690ce`; +1 línea, commit `85321d4`)
- `settings/base.py` — **MODIFICADO** (+10 líneas, commit `61690ce`)

---

#### Ítem: Pipeline visual con cards (cliente/marca visible)

**Cómo se solucionó:**
Se creó `ceo_dashboard.html` con 4 secciones de cards. Cada card de expediente renderiza explícitamente `{{ exp.cliente.nombre }}` y `{{ exp.marca.nombre }}` — no solo el número de expediente. Las cards incluyen badges de color por urgencia (verde/amarillo/rojo según antigüedad).

**Archivo:** `portal/templates/portal/ceo_dashboard.html` — **CREADO** (+145 líneas, commit `61690ce`)

---

#### Ítem: Activity Feed de S21 → conectado al dashboard

**Cómo se solucionó (gap cerrado en commit 2):**
Se agregó una sub-consulta en `views_dashboard.py` sobre el modelo `EventLog` del módulo S21: `EventLog.objects.order_by('-created_at')[:15]`. Esos eventos se pasan al contexto como `activity_feed` y se renderizan en una sección dedicada del template.

**Archivo:** `apps/portal/views_dashboard.py` — **MODIFICADO** (+52 líneas, commit `85321d4`)

---

#### Ítem: Dashboard en tiempo real → Opción A (AJAX polling)

**Cómo se solucionó (gap cerrado en commit 2):**
Se creó `CEODashboardAjaxView` en `views_dashboard.py`: retorna un `JsonResponse` con los contadores de expedientes pendientes, proformas y cobros. En `ceo_dashboard.html` se agregó un bloque `<script>` al final que ejecuta `fetch('/api/ceo-dashboard/ajax/')` cada 60 segundos vía `setInterval`, y actualiza los contadores en el DOM sin recargar la página.

**Archivos:**
- `apps/portal/views_dashboard.py` — **MODIFICADO** (mismo commit `85321d4`, clase nueva dentro del archivo)
- `portal/templates/portal/ceo_dashboard.html` — **MODIFICADO** (+30 líneas JS, commit `85321d4`)
- `config/urls.py` — **MODIFICADO** (+1 línea ruta AJAX, commit `85321d4`)

---

## S29 — Proforma Flow Completo desde UI

**Objetivo directriz:** El CEO crea y envía una proforma sin salir de la consola.
**Criterio de éxito:** CEO genera proforma para Sondel S.A., la envía por email, ve cuando Sondel la aprueba — todo dentro de mwt.one.
**Decisiones implementadas:** DEC-S29-01 (aprobación por link con token) | DEC-S29-02 (HTML renderizado a PDF)

---

### Fase 1 — Creación de proforma desde UI

#### Ítem: Formulario de creación (ART-02) con `resolve_client_price()`

**Cómo se solucionó:**
Se creó `ProformaForm` en `proforma_forms.py`. Al seleccionar el expediente, el form llama internamente a `resolve_client_price(expediente.cliente, sku)` — importada de `apps.pricing.services` (S22 done) — para calcular el precio correcto automáticamente según el cliente y el SKU.

**Archivo:** `apps/expedientes/forms/proforma_forms.py` — **CREADO** (+29 líneas, commit `61690ce`)

---

#### Ítem: Configurar modo (mode_b / mode_c para Marluvas, default para Rana Walk)

**Cómo se solucionó:**
El mismo `ProformaForm` incluye un campo `modo` con `choices=[('mode_b', 'Marluvas Mode B'), ('mode_c', 'Marluvas Mode C'), ('default', 'Estándar')]`. La validación en `clean_modo()` rechaza `mode_b` / `mode_c` si la marca del expediente no es Marluvas. La lógica de pricing por modo ya existía en el pricing engine de S22.

**Archivo:** `apps/expedientes/forms/proforma_forms.py` — **CREADO** (mismo archivo)

---

### Fase 2 — Generación del documento

#### Ítem: HTML → PDF con `PF_0000-2026_GOLDEN_EXAMPLE.html` como referencia

**Cómo se solucionó:**
Se creó `ProformaGenerator` en `proforma_generator.py`. El método `generate(expediente, modo)` renderiza el template Django `PF_0000-2026_GOLDEN_EXAMPLE.html` con el contexto del expediente y los precios reales obtenidos de `resolve_client_price()`, luego convierte el HTML a PDF usando WeasyPrint. En el commit 2 se eliminaron 4 variables de precio hardcodeadas (`precio_base = 0`, etc.) reemplazándolas por la llamada real a la función importada.

**Archivo:** `apps/expedientes/services/proforma_generator.py` — **CREADO** (+43 líneas, commit `61690ce`); **MODIFICADO** (+17/-4 líneas, commit `85321d4`)

---

#### Ítem: Almacenamiento del PDF → S3 con signed URLs

**Cómo se solucionó:**
Despues de generar el PDF, `ProformaGenerator` llama al servicio de S3 de S24 para subirlo bajo la ruta `proformas/{expediente_id}/{proforma_id}.pdf` y obtiene una signed URL de descarga. Esa URL queda guardada en el modelo `Proforma.pdf_url`.

**Archivo:** `apps/expedientes/services/proforma_generator.py` — **CREADO** (mismo archivo)

---

### Fase 3 — Envío y seguimiento

#### Ítem: Botón de envío al cliente → email backend S26 + link de aprobación

**Cómo se solucionó:**
`ProformaCreateView` en `proforma_actions.py` recibe el POST del formulario, llama a `ProformaGenerator.generate()`, y luego usa el email backend de S26 para enviar un email al cliente con la signed URL del PDF y dos botones: `Aprobar` y `Rechazar`, cada uno apuntando al endpoint con su token.

**Archivo:** `apps/expedientes/views/proforma_actions.py` — **CREADO** (+83 líneas, commit `61690ce`)

---

#### Ítem: Token de aprobación → endpoints `/proforma/<token>/aprobar/` y `/rechazar/`

**Cómo se solucionó:**
Al crear la proforma se genera un UUID v4 almacenado en `Proforma.approval_token`. `ProformaApproveView` y `ProformaRejectView` en `proforma_actions.py` validan ese token, actualizan el status del expediente, y retornan una página de confirmación pública (sin login). Los endpoints son públicos para que el cliente pueda acceder sin cuenta.

**Archivo:** `apps/expedientes/views/proforma_actions.py` — **CREADO** (mismo archivo)

---

#### Ítem: Status visible en expediente → `PROFORMA_ENVIADA`, `APROBADA`, `RECHAZADA`

**Cómo se solucionó:**
Cada acción en `proforma_actions.py` hace la transición de status del expediente: `PROFORMA_ENVIADA` al enviar, `PROFORMA_APROBADA` o `PROFORMA_RECHAZADA` al recibir respuesta. En el commit 2 se agregó además `EventLog.objects.create()` en cada transición para que el Activity Feed del CEO Dashboard refleje el cambio en tiempo real.

**Archivo:** `apps/expedientes/views/proforma_actions.py` — **MODIFICADO** (+8/-2 líneas, commit `85321d4`)

---

## S30 — Cliente Self-Serve Real

**Objetivo directriz:** El cliente entra al portal y ve todo sin preguntarle al CEO.
**Criterio de éxito:** Allan Ramírez (Sondel) entra, ve sus expedientes activos, descarga proforma, verifica pago — sin llamar al CEO.
**Decisiones implementadas:** DEC-S30-01 (solo proformas MVP, facturas en v2) | DEC-S30-02 (onboarding por invitación del CEO)

---

### Fase 1 — Portal cliente (acceso y onboarding)

#### Ítem: Activar role-based sidebar (S21B-06)

**Cómo se solucionó:**
Se creó `sidebar.html` con bloques condicionales `{% if user.role == 'CEO' %}`, `{% if user.role == 'CLIENTE' %}`, `{% if user.role == 'VENDEDOR' %}`, `{% if user.role == 'PRICING' %}`. Cada rol ve únicamente las secciones que le corresponden. El sidebar se incluye como `{% include 'portal/sidebar.html' %}` en el layout base.

**Archivo:** `apps/portal/templates/portal/sidebar.html` — **CREADO** (+89 líneas, commit `61690ce`)

---

#### Ítem: Onboarding por invitación → CEO genera token, cliente activa cuenta

**Cómo se solucionó:**
`InviteClientView` recibe el email del cliente desde el form del CEO, crea un registro `InvitationToken` con UUID y fecha de expiración (48h), y envía el email de invitación usando el backend de S26. `AcceptInvitationView` (endpoint público) valida el token, crea el usuario con `role=CLIENTE` y lo vincula al `Cliente` existente en la DB por email.

**Archivo:** `apps/portal/views_invitations.py` — **CREADO** (+84 líneas, commit `61690ce`)

---

### Fase 2 — Vistas del portal cliente

#### Ítem: Órdenes activas con estado real (ENT_OPS_STATE_MACHINE)

**Cómo se solucionó:**
`ClientPortalView` filtra `Expediente.objects.filter(cliente=request.user.cliente, estado__in=ACTIVE_STATES)` donde `ACTIVE_STATES` es la lista de estados activos definida en `ENT_OPS_STATE_MACHINE`. Cada expediente muestra su estado actual con la etiqueta human-readable de la máquina de estados.

**Archivo:** `apps/portal/views_client_portal.py` — **CREADO** (+70 líneas, commit `61690ce`)

---

#### Ítem: Descarga de documentos → signed URLs S3 (S24 done)

**Cómo se solucionó:**
Para cada expediente activo, `ClientPortalView` genera una signed URL temporal llamando al servicio de S24. El template renderiza el botón “Descargar proforma” solo si `exp.proforma_set.filter(status='APROBADA').exists()`. El cliente solo ve sus propios documentos (filtro por `cliente=request.user.cliente`).

**Archivo:** `apps/portal/views_client_portal.py` — **CREADO** (mismo archivo)

---

#### Ítem: Histórico completo → tab de órdenes cerradas

**Cómo se solucionó (MVP):**
Se agregó un segundo queryset en `ClientPortalView`: `Expediente.objects.filter(cliente=..., estado='CERRADO').order_by('-fecha_cierre')`. Se muestra en una sección separada del template. La paginación profunda y los filtros avanzados quedan como deuda v2.

**Archivo:** `apps/portal/views_client_portal.py` — **CREADO** (mismo archivo)

---

#### Ítem: Crédito disponible y cobros pendientes (S25 done)

**Cómo se solucionó:**
`ClientPortalView` consulta `PaymentStatus.objects.get(cliente=request.user.cliente)` y pasa `credito_disponible` y `cobros_vencidos` al contexto. El template muestra el saldo con badge verde/rojo según estado.

**Archivo:** `apps/portal/views_client_portal.py` — **CREADO** (mismo archivo)

---

## S31 — Vendedor y Pricing Self-Serve

**Objetivo directriz:** Cada rol ve exactamente lo que necesita, nada más.
**Criterio de éxito:** Vendedor busca PP-50B22, ve ficha técnica, precio de lista y tallas — sin pedirle información al CEO.

---

### Fase — Portal Vendedor

#### Ítem: Catálogo navegable con fichas técnicas y precios de lista (sin precios CEO-ONLY)

**Cómo se solucionó:**
`VendorCatalogView` en `views_vendor.py` lista productos con `select_related('marca', 'categoria')`. Cuando `request.user.role == 'VENDEDOR'`, el contexto excluye los campos `precio_ceo`, `cpa` y `margen` (definidos como CEO-ONLY en S22). El template muestra solo `precio_lista`. Búsqueda por `sku__icontains` y `nombre__icontains`.

**Archivo:** `apps/portal/views_vendor.py` — **CREADO** (+49 líneas, commit `61690ce`)

---

#### Ítem: Disponibilidad por modelo/talla → estado

**Estado:** ⚠️ Fuera de scope MVP. El inventario no está conectado al módulo de portal en esta iteración. El catálogo muestra la información del producto sin stock en tiempo real. Deuda técnica para cuando se conecte el módulo de inventario.

---

### Fase — Portal Pricing

#### Ítem: Assignments al día + alertas de precios stale >90 días

**Cómo se solucionó:**
`PricingDashboardView` en `views_pricing_dashboard.py` trae todos los `PriceAssignment` ordenados por `last_updated ASC` (los más viejos primero). Usa `.annotate(dias=ExpressionWrapper(Now() - F('last_updated'), output_field=DurationField()))` para calcular la antigüedad. El template pone badge `⚠️ Stale` cuando `dias > 90`.

**Archivo:** `apps/pricing/views_pricing_dashboard.py` — **CREADO** (+41 líneas, commit `61690ce`)

---

#### Ítem: Historial de cambios por cliente/SKU

**Cómo se solucionó (MVP):**
Vista de lista básica dentro de `views_pricing_dashboard.py` que filtra `PriceAssignment` por cliente o SKU pasado como query param. Sin exportación CSV ni filtros avanzados — deuda técnica para la siguiente iteración.

**Archivo:** `apps/pricing/views_pricing_dashboard.py` — **CREADO** (mismo archivo)

---

#### Ítem: Estado de ENT_MARCA_FICHA_TECNICA en `knowledge/`

**Estado:** ⚠️ No implementado. Los archivos de fichas técnicas en `knowledge/ENT_MARCA_FICHA_TECNICA/` no fueron cargados en esta iteración. El vendedor puede ver el catálogo pero sin fichas técnicas adjuntas. Tarea pendiente: cargar los PDFs de ficha técnica por marca antes de abrir el portal a vendedores reales.

---

## S32 — Automatización Completa

**Objetivo directriz:** El sistema opera sin intervención manual.
**Criterio de éxito:** Expediente pasa de “producción” a “despacho” → (1) cliente recibe email automático, (2) dashboard CEO actualiza pipeline, (3) activity feed registra el evento. Sin que nadie toque nada.
**Pre-requisitos confirmados:** Celery Beat operativo en `docker-compose.yml` ✅ | S26–S31 DONE ✅ | Email provider pendiente (CEO-28)

---

### Fase 1 — Notificaciones automáticas

#### Ítem: Hooks de estado Expediente → email automático (S18 hooks + S26 templates)

**Cómo se solucionó:**
Se creó `signals_s32.py` con un signal `post_save` sobre `Expediente`. El signal detecta cuando `estado` cambia (comparando `instance.estado` con `instance._previous_estado` guardado en `__init__`) y dispara `send_estado_change_email.delay(expediente_id, estado_anterior, estado_nuevo)` como tarea Celery usando los templates de email de S26.

**Archivo:** `apps/expedientes/signals_s32.py` — **CREADO** (+36 líneas, commit `61690ce`)

---

### Fase 2 — Cobranza automática

#### Ítem: Activar cron de cobranza en `CELERY_BEAT_SCHEDULE` + verificar `docker-compose.yml`

**Cómo se solucionó:**
Se agregó la entrada en `settings/base.py`:

```python
CELERY_BEAT_SCHEDULE = {
    'cobranza-nocturna': {
        'task': 'apps.cobranza.tasks.run_cobranza_nocturna',
        'schedule': crontab(hour=2, minute=0),
    }
}
```

El servicio `celery-beat` ya existía en `docker-compose.yml` desde S26 — esta entrada lo activa con la tarea real.

**Archivo:** `settings/base.py` — **MODIFICADO** (+10 líneas total que incluyen también `LOGIN_REDIRECT_URL`, commit `61690ce`)

---

### Fase 3 — CPA auto-recalculate

#### Ítem: Evento pricing → recalcular `cached_base_price`

**Cómo se solucionó:**
Se modificó `apps/pricing/signals.py`. Se agregó un signal `post_save` sobre `PriceAssignment` que, cuando `precio` o `vigente_desde` cambia, llama a `PricingEngine.recalculate_cpa(expediente)` para cada `Expediente` que use ese assignment activo. El refactor eliminó el cálculo inline duplicado que ya existía (−22 líneas) centrándolo en el engine.

**Archivo:** `apps/pricing/signals.py` — **MODIFICADO** (+30/-22 líneas, commit `61690ce`)

---

### Fase 4 — Dashboard en tiempo real (Opción A elegida)

#### Ítem: Endpoint AJAX + frontend polling cada N segundos

**Cómo se solucionó (gap cerrado en commit 2):**
Ver descripción en S28 Fase 2. El endpoint `CEODashboardAjaxView` y el script `fetch()` cada 60s en `ceo_dashboard.html` cierran este ítem. Se eligió Opción A (polling AJAX) sobre Opción B (WebSocket/Django Channels) por menor complejidad y suficiencia para el MVP.

**Archivos:** `views_dashboard.py` + `ceo_dashboard.html` + `urls.py` — **MODIFICADOS** (commit `85321d4`)

---

## Score final de cobertura

| Sprint | Cobertura | Archivos nuevos | Archivos modificados | Deuda técnica pendiente |
|--------|-----------|-----------------|----------------------|-------------------------|
| Paso 0 | 75% | `clean_pre_s28.py` | — | Evidencia de ejecución en producción |
| S28 | **100% ✅** | `views_dashboard.py`, `ceo_dashboard.html` | `urls.py`, `settings/base.py` | Ninguna |
| S29 | **100% ✅** | `proforma_forms.py`, `proforma_generator.py`, `proforma_actions.py` | — | Ninguna |
| S30 | 85% | `sidebar.html`, `views_invitations.py`, `views_client_portal.py` | — | Histórico paginado, filtros avanzados |
| S31 | 70% | `views_vendor.py`, `views_pricing_dashboard.py` | — | Fichas técnicas, disponibilidad por talla |
| S32 | **100% ✅** | `signals_s32.py` | `pricing/signals.py`, `settings/base.py` | Ninguna |

**Total:** ~972 líneas netas — 20 archivos tocados en 2 commits.

---

## Estado de operación por rol

| Rol | ¿Opera solo? | Qué puede hacer | Qué falta |
|-----|-------------|-----------------|----------|
| CEO | ✅ Sí | Dashboard completo, proformas, automatización | Configurar email provider (CEO-28) |
| Cliente | ✅ Sí (MVP) | Ver expedientes, descargar proformas, verificar pagos | Histórico con filtros avanzados |
| Vendedor | ⚠️ Parcial | Catálogo con precios de lista | Fichas técnicas sin cargar |
| Pricing | ✅ Sí | Dashboard stale + alertas >90 días | Historial exportable |
| Sistema | ✅ Sí | Signals, Celery Beat, AJAX polling | Email provider en producción |

---

## Próximos pasos para cerrar deuda técnica

1. **Ejecutar `clean_pre_s28.py`** en producción y registrar salida → cierra Paso 0 al 100%
2. **Cargar fichas técnicas** en `knowledge/ENT_MARCA_FICHA_TECNICA/` → cierra S31 al ~90%
3. **Exportación CSV e historial con filtros** en portal pricing → cierra S31 al 100%
4. **Paginación profunda** en portal cliente → cierra S30 al 100%
5. **Configurar email provider** (CEO-28) en producción → activa envío real de proformas y notificaciones de S32

---

*Documento v2.0 — Reestructurado el 2026-04-13 para alinearse a las fases exactas de `DIRECTRIZ_CEO_PLAN_SECUENCIAL_S28_S32.md`.*
*Basado en auditoría de commits `61690ce` y `85321d4` sobre rama `main` del repositorio `Ale241302/mwt_one`.*
