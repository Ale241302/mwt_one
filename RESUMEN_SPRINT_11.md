# Resumen Sprint 11 — MWT.ONE

Este documento detalla las soluciones implementadas durante el Sprint 11, enfocado en la limpieza técnica (cleanup), seguridad, accesibilidad y la expansión hacia el Portal B2B y el Módulo de Productos.

---

## 🛠️ Cleanup & Arquitectura

### S11-01: Eliminación de ARCHIVADO (Backend)
Se eliminó el estado `ARCHIVADO` del enum `ExpedienteStatus` para simplificar el flujo de vida del expediente.
- **Solución:** Eliminación física en el código y verificación de dependencias en modelos y vistas.
- **Archivos Modificados:**
  - `backend/apps/expedientes/enums.py`

### S11-02 & S11-03 & S11-05: Centralización de Estados
Se consolidaron 28 strings de estado y arrays derivados en un único punto de verdad. Se eliminó la duplicidad de archivos de constantes.
- **Solución:**
  - Exportación de `TERMINAL_STATES`, `CANCELLABLE_STATES`, `COST_PHASES` y `TIMELINE_STATES_CANONICAL`.
  - Eliminación de `frontend/src/lib/constants/states.ts` a favor de `frontend/src/constants/states.ts`.
- **Archivos Modificados:**
  - `frontend/src/constants/states.ts`
  - `frontend/src/components/ui/StateBadge.tsx`
  - La mayoría de los componentes ahora importan desde `@/constants/states`.
- **Archivos Eliminados:**
  - `frontend/src/lib/constants/states.ts`

### S11-04: Eliminación de Rutas Duplicadas
Limpieza masiva de ~1,300 líneas de código eliminando carpetas legacy de rutas en el dashboard para unificar la experiencia de usuario.
- **Solución:** Consolidación de rutas en `frontend/src/app/[lang]/(mwt)/(dashboard)`.
- **Archivos Modificados:**
  - `frontend/src/middleware.ts`
  - Reestructuración de la carpeta `frontend/src/app`.

---

## 🎨 Diseño & UI

### S11-06: Migración de Hex a CSS Variables
Eliminación total de colores hardcodeados en el frontend para asegurar la consistencia del design system y facilitar el mantenimiento temático.
- **Solución:** Uso de clases como `badge-info`, `badge-success`, `badge-critical` (mapeadas en `globals.css`) en lugar de `#hex`.
- **Archivos Modificados:**
  - `frontend/src/components/ui/StateBadge.tsx`
  - Páginas de productos Rana Walk (bison, goliath, leopard, orbis, velox).

### S11-07: Accesibilidad (A11y)
Mejora de la interacción para tecnologías asistivas en inputs, botones y drawers, cumpliendo estándares básicos de navegación por teclado.
- **Solución:** Implementación de `role="dialog"`, `aria-modal="true"` y handlers para la tecla `Escape`. Agregado de `id` y `htmlFor` ausentes en 26 inputs.
- **Archivos Modificados:**
  - `frontend/src/components/modals/ArtifactFormDrawer.tsx`
  - `frontend/src/components/modals/RegisterCostDrawer.tsx`
  - `frontend/src/components/modals/FormModal.tsx`

---

## 🔒 Seguridad & API

### S11-09: Auditoría SQL & Serializers
Protección proactiva contra inyecciones SQL y minimización de la superficie de exposición de datos.
- **Solución:**
  - Auditoría de `ask.py` y `sessions.py`: Uso estricto de parámetros en `sqlalchemy.text()`.
  - Reemplazo de `fields = "__all__"` por listas explícitas en serializers de `liquidations` y `transfers`.
- **Archivos Modificados:**
  - `backend/apps/liquidations/serializers.py`
  - `backend/apps/transfers/serializers.py`
  - `backend/apps/knowledge/knowledge_service/routers/ask.py`

---

## ✨ Nuevas Funcionalidades (Fase 1)

### S11-10: Portal B2B (Vista Cliente)
Lanzamiento de la interfaz dedicada para clientes bajo `portal.mwt.one` para visualización propia de expedientes.
- **Solución:**
  - Nueva ruta `/portal` con filtrado (`ClientScopedManager`).
  - Vista de detalle con timeline interactivo y documentos vía URLs firmadas (S3/Cloudfront).
- **Archivos Nuevos:**
  - `frontend/src/app/[lang]/(mwt)/(dashboard)/portal/page.tsx`
  - `frontend/src/app/[lang]/(mwt)/(dashboard)/portal/expedientes/[id]/page.tsx`

### S11-11: Módulo Productos (PLT-09)
Gestión centralizada del catálogo de productos con integración a marcas y categorías.
- **Solución:**
  - Endpoints CRUD en `/api/productos/`.
  - UI de gestión con filtros avanzados por marca.
- **Archivos Nuevos:**
  - App Django `backend/apps/productos/`.
  - Ruteo frontend en `frontend/src/app/[lang]/(mwt)/(dashboard)/productos/page.tsx`.

---

## ✅ Calidad & QA

### S11-08 & S11-12: Tests de Regresión y State Machine
Validación exhaustiva de las reglas de negocio y estabilidad global del sistema.
- **Solución:**
  - Test paramétrico de transiciones cubriendo 22 comandos × estados inválidos.
  - Regresión Sprint 9/10 exitosa tras reestructuración de rutas.
- **Archivos Modificados:**
  - `backend/tests/test_transitions.py`
  - `frontend/tests/page.test.tsx`
