# RESUMEN SPRINT 13: Costeo, Viabilidad y Aforo Aduanero

Este documento resume las tareas implementadas y completadas para el Sprint 13, detallando los archivos creados o modificados por fase. Todas las fases y requerimientos fueron completados exitosamente.

## Estado General
**COMPLETO**

---

## Fases y Tareas

### Fase 0 - Knowledge Base y Configuraciones
* **S13-01: Configurar array arancelario**
  * **Estado:** Completado
  * **Descripción:** Se agregó la configuración harcodeada inicial de `DAI_RATES` de contingencia y `VIABILITY_FLETE_PCT`.
  * **Archivos modificados:**
    * `backend/config/settings/base.py` (Se agregaron los diccionarios de aranceles)

### Fase 1 - Modelo (CostLine y Multi-moneda)
* **S13-02: Agregar `cost_category` a CostLine**
* **S13-03: Agregar `cost_behavior` a CostLine**
* **S13-04: Multi-moneda en CostLine**
  * **Estado:** Completado
  * **Descripción:** Implementación de las categorías de costos para analítica (Landed Cost, Tax Credit, etc), comportamiento (Fixed, Variable), y manejo de tipo de cambio base (`exchange_rate` y `amount_base_currency`).
  * **Archivos modificados:**
    * `backend/apps/expedientes/models.py` (Nuevos campos del modelo `CostLine`)
    * `backend/apps/expedientes/enums_exp.py` (Opciones `CostCategory` y `CostBehavior`)
    * `backend/apps/expedientes/admin.py` (Se exhiben los nuevos campos de `CostLineAdmin`)
    * `backend/apps/expedientes/serializers.py` (Integración de validación de campos)
    * `backend/apps/expedientes/services/financial.py` (Lógica de conversión `amount_base_currency` al procesar C15)
    * `backend/apps/expedientes/migrations/0..._auto.py` (Nuevas migraciones del modelo)

### Fase 2 - Lógica (Viabilidad y Artefactos)
* **S13-05: `pre_check_viability` en Comando C4 con fallback degradado**
* **S13-06: Configuración Certificado Origen (ART-13) y DU-E (ART-14)**
  * **Estado:** Completado
  * **Descripción:** Comprobación lógica que alerta sobre la viabilidad del modo de importación en Comando 4 generada contra el `EventLog`. Inclusión de dos nuevos artefactos clave para el registro de origen y de exportación de Brasil.
  * **Archivos modificados:**
    * `backend/apps/expedientes/services/commands_registro.py` (Implementación funcional de `pre_check_viability` y su llamada en `handle_c4`)
    * `backend/apps/expedientes/enums_exp.py` (Adición de `CERTIFICATE_OF_ORIGIN` y `DUE_EXPORT_BR` al `ArtifactType`)

### Fase 3 - Datos (Aforo)
* **S13-07: Aforo Aduanero**
  * **Estado:** Completado
  * **Descripción:** Capacidad de documentar y registrar incidencias del Aforo Aduanero (Verde, Amarillo, Rojo) desde el administrador del sistema y atado al modelo `Expediente`.
  * **Archivos modificados:**
    * `backend/apps/expedientes/models.py` (Campos `aforo_type` y `aforo_date` agregados en `Expediente`)
    * `backend/apps/expedientes/admin.py` (Visualización del aforo en lista y filtros)
    * `backend/apps/expedientes/enums_exp.py` (Definición del enumerador `AforoType`)

### Final - Tests
* **S13-08: Banco de Pruebas Unitarias**
  * **Estado:** Completado
  * **Descripción:** Suite ampliada de test implementada para asegurar regresión de todos los comportamientos construidos (Modelos en C15, fallbacks de viabilidad en C4, configuración multi-moneda de base, integridad Enum y validaciones completas).
  * **Archivos creados:**
    * `backend/apps/expedientes/tests/test_sprint13.py`
  * **Archivos modificados:**
    * `backend/apps/expedientes/tests/test_sprint4.py` (Arreglo urgente de importaciones circulares en modulos previos detectado en testing global)
