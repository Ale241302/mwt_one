# RESUMEN SPRINT 22 — Pricing Engine Upgrade (Marluvas Structure)

**Estado final:** ✅ Completado — Servidor operativo, migraciones aplicadas y frontend enriquecido.

---

## Objetivo del Sprint

Implementar la estructura real de precios de Marluvas, permitiendo el manejo de versiones de listas de precios, asignaciones por producto/cliente (CPA), políticas de pronto pago (Early Payment) y un waterfall de resolución de precios de 5 pasos. Se incluye el motor de validación de MOQ por talla y herramientas de carga masiva vía Excel/CSV.

---

## FASE 0 — Modelos y Migraciones

### S22-01 — PriceListVersion + PriceListGradeItem
**Qué se hizo:** Se implementó la estructura de versionado de precios. `PriceListVersion` permite múltiples versiones activas por marca. `PriceListGradeItem` introduce el soporte para "Grades" (rangos de tallas) y multiplicadores de MOQ mediante un campo JSON.
- **Archivos modificados:** 
    - `backend/apps/pricing/models.py` (Se agregaron `PriceListVersion` y `PriceListGradeItem`)
- **Archivos creados:**
    - `backend/apps/pricing/migrations/0023_pricelist_version_gradeitem.py`
- **Resultado:** ✅ Registrado y migrado. Propiedades `moq_total` y `available_sizes` operativas.

### S22-02 — ClientProductAssignment (CPA)
**Qué se hizo:** Creación del modelo CPA para el "Paso 0" del waterfall. Permite fijar un precio específico a un cliente para un SKU, cacheando la versión de la lista de origen.
- **Archivos modificados:** 
    - `backend/apps/pricing/models.py` (Se agregó `ClientProductAssignment`)
- **Archivos creados:**
    - `backend/apps/pricing/migrations/0024_clientproductassignment.py`
- **Resultado:** ✅ Implementado con índice único `(client_subsidiary, brand_sku)`.

### S22-03 — EarlyPaymentPolicy + EarlyPaymentTier
**Qué se hizo:** Modelado de políticas de descuento por pronto pago. Incluye un mecanismo de tramos dinámicos (Tiers) y un sistema de auditoría mediante señales.
- **Archivos modificados:** 
    - `backend/apps/pricing/models.py` (Modelos `EarlyPaymentPolicy` y `Tier`)
    - `backend/apps/pricing/apps.py` (Conexión de señales)
- **Archivos creados:**
    - `backend/apps/pricing/signals.py` (Integración con `ConfigChangeLog`)
    - `backend/apps/pricing/migrations/0025_earlypaymentpolicy.py`
- **Resultado:** ✅ Mutable y auditable. Descuentos aplicados correctamente en el cálculo final.

### S22-04 — Brand.min_margin_alert_pct
**Qué se hizo:** Extensión del modelo de marcas para soportar alertas de margen mínimo.
- **Archivos modificados:** 
    - `backend/apps/brands/models.py` (Nuevo campo `min_margin_alert_pct`)
- **Archivos creados:**
    - `backend/apps/brands/migrations/0008_brand_margin_alert.py`
- **Resultado:** ✅ Campo agregado. Solo dispara alertas si no es NULL.

---

## FASE 1 — Servicios

### S22-05 — resolve_client_price() v2
**Qué se hizo:** Extensión del motor de resolución de precios con el waterfall de 5 pasos (CPA → BCPA → GradeItem → Legacy → Manual) y aplicación de Early Payment.
- **Archivos modificados:** 
    - `backend/apps/pricing/services.py` (Lógica extendida y helpers `_resolve_grade_constraints`, `_apply_early_payment`)
- **Resultado:** ✅ 100% retrocompatible. Retorna desglose con `price`, `source`, `discount`, `moq` y `multipliers`.

### S22-06 — activate_pricelist()
**Qué se hizo:** Implementación de la lógica de activación inteligente. Una versión previa solo se extingue si todos los SKUs solapados son más baratos o iguales en la nueva versión (salvo `force=True`).
- **Archivos modificados:** 
    - `backend/apps/pricing/services.py` (`activate_pricelist` con auditoría `EventLog`)
- **Resultado:** ✅ Protección de precios activada.

### S22-07 — validate_moq()
**Qué se hizo:** Motor de validación de cantidades según el Grade activo. Bloquea si no se cumple el `grade_moq` y advierte si no se respeta el multiplicador de talla.
- **Archivos modificados:** 
    - `backend/apps/pricing/services.py` (Nueva función `validate_moq`)
- **Resultado:** ✅ Integrado con la lógica de confirmación de pedidos.

### S22-08 — Bulk Assignment Endpoint
**Qué se hizo:** Creación de endpoint masivo para asignar productos a clientes de forma idempotente.
- **Archivos modificados:** 
    - `backend/apps/pricing/views.py` (`BulkAssignmentView`)
    - `backend/apps/pricing/serializers.py` (`BulkAssignmentSerializer`)
    - `backend/apps/pricing/urls.py` (Registro de ruta)
- **Resultado:** ✅ Operación masiva funcional con reporte de `created`/`skipped`.

### S22-09 y S22-10 — Tareas Celery y Alerta de Margen
**Qué se hizo:** Implementación de tarea de recálculo masivo tras activación de lista. Incluye validación de margen contra el nuevo campo de la marca y generación de notificaciones `margin_alert`.
- **Archivos creados:**
    - `backend/apps/pricing/tasks.py` (`recalculate_assignments_for_brand`)
- **Archivos modificados:** 
    - `backend/apps/pricing/services.py` (Disparo de tarea en activación)
- **Resultado:** ✅ Recálculo en background 100% funcional.

---

## FASE 2 — Upload y Parsing

### S22-11 y S22-12 — Upload y Confirmación de Pricelists
**Qué se hizo:** Pipeline de carga de archivos (Pandas) para procesar la estructura Marluvas. Se maneja sesión temporal con preview detallado y reporte de errores antes de la persistencia final.
- **Archivos creados:**
    - `backend/apps/pricing/parsers.py` (Lógica Pandas para CSV/Excel)
- **Archivos modificados:** 
    - `backend/apps/pricing/views.py` (`PriceListUploadView`, `PriceListConfirmView`)
    - `backend/apps/pricing/urls.py` (Registro de rutas)
- **Resultado:** ✅ Parsing robusto que soporta aliases de columnas y normalización de datos.

---

## FASE 3 — Frontend

### S22-13 — Pre-fill en Proforma
**Qué se hizo:** Integración del waterfall en la creación de proformas. El sistema pre-llena el precio, muestra el desglose en tooltip y genera badges de alerta de MOQ.
- **Archivos modificados:** 
    - Componentes de línea de proforma y `frontend/src/api/pricing.ts`
- **Resultado:** ✅ UX automatizada.

### S22-14 — Refactor Tab 5: Pricing (Brand Console)
**Qué se hizo:** Reescritura total del tab de precios para soportar el flujo de Versiones → Grades.
- **Archivos creados/modificados:** 
    - `PricingTab.tsx` (Reescritura), `PriceListVersionCard.tsx`, `UploadPreviewModal.tsx`, `GradeItemsTable.tsx`.
- **Resultado:** ✅ UI moderna con gestión de histórico de versiones.

### S22-15 — Enriquecer Tab 4: Catalog
**Qué se hizo:** Inserción de columnas de precio base y MOQ en la tabla de catálogo, con sub-fila expandible para ver multiplicadores.
- **Archivos creados/modificados:** 
    - `CatalogTab.tsx`, `SizeMultipliersExpand.tsx`.
- **Resultado:** ✅ Visibilidad total de restricciones por SKU.

### S22-16 y S22-17 — Tabs 8 (Payment Terms) y 9 (Assignments)
**Qué se hizo:** Inclusión de nuevos módulos para gestión de políticas financieras y asignaciones directas.
- **Archivos creados:** 
    - `PaymentTermsTab.tsx`, `AssignmentsTab.tsx`, `BulkAssignModal.tsx`.
- **Archivos modificados:** 
    - `BrandConsole.tsx` (Registro de nuevos tabs).
- **Resultado:** ✅ CRUD completo y herramientas de asignación masiva operativas.

### S22-18 — Client Console Enriquecimiento
**Qué se hizo:** Adaptación del portal de cliente para mostrar precios netos (post-descuento pronto pago) y MOQ, ocultando la cascada de cálculo interna.
- **Archivos modificados:** 
    - `ClientConsole/CatalogTab.tsx`, `serializers.py` (`PricingPortalSerializer`).
- **Resultado:** ✅ Privacidad de margen asegurada.

---

## FASE 4 — Testing y Calidad

### S22-19 y S22-20 — Suite de Tests
**Qué se hizo:** Implementación de 44 tests backend cubriendo el waterfall, Celery tasks y modelos.
- **Archivos creados:**
    - `backend/apps/pricing/tests/test_resolve.py`
    - `backend/apps/pricing/tests/test_models.py`
    - `backend/apps/pricing/tests/test_tasks.py`
- **Puntos Críticos Verificados:**
    - ✅ `#26` — `skip_cache=True` salta el Paso 0 correctamente.
    - ✅ `#35/36` — CPA/BCPA + Grade activo respeta MOQ.
    - ✅ `#38` — Activación dispara recálculo Celery y cambia precios en cascada.
    - ✅ `#42` — Portal de cliente no expone datos sensibles (margen/source).

---

## Resumen de Archivos Generado por Capa

### Backend (Modelos, Vistas, Serializers)
- `backend/apps/pricing/models.py` — Implementación de 4 modelos de pricing.
- `backend/apps/pricing/services.py` — Core del waterfall y lógica de activación.
- `backend/apps/pricing/views.py` — 4 nuevos endpoints (Upload, Confirm, Bulk, Resolve).
- `backend/apps/pricing/serializers.py` — Serializers internos y de portal.
- `backend/apps/pricing/urls.py` — Rutas del engine S22.
- `backend/apps/brands/models.py` — Campo de alerta de margen.
- `backend/apps/pricing/signals.py` — Auditoría de políticas de pago.
- `backend/apps/pricing/parsers.py` — Motor de parsing Pandas.
- `backend/apps/pricing/tasks.py` — Recalculador masivo Celery.

### Frontend (Componentes y Páginas)
- `PricingTab.tsx`, `PaymentTermsTab.tsx`, `AssignmentsTab.tsx` — Tabs principales.
- `PriceListVersionCard.tsx`, `UploadPreviewModal.tsx`, `GradeItemsTable.tsx` — UI de carga.
- `SizeMultipliersExpand.tsx`, `BulkAssignModal.tsx` — Helpers de catálogo y asignación.
- `frontend/src/api/pricing.ts` — Implementación de hooks de API.
