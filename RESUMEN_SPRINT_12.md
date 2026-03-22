# DETALLE TÉCNICO — RESUMEN SPRINT 12

Este informe detalla las implementaciones realizadas durante el **Sprint 12**, proporcionando trazabilidad sobre cada cambio arquitectónico y funcional solicitado en la especificación `Sprints/LOTE_SM_SPRINT12.md`.

---

## 🏗️ Fase 0: Refactorización Arquitectónica (Backend)

### S12-01: Modularización de `services.py`
Se ha eliminado el archivo monolítico `services.py` de 1,300+ líneas y se ha reemplazado por un paquete estructurado en `backend/apps/expedientes/services/`.
- **Archivos creados**:
    - `services/create.py`: Lógica de apertura de expedientes.
    - `services/commands_registro.py`: Gestión de OC, Proformas y confirmaciones SAP.
    - `services/commands_produccion.py`: Seguimiento de hitos de producción.
    - `services/commands_preparacion.py`: Despacho y documentación aduanera.
    - `services/commands_transito.py`: Salidas y arribos de carga.
    - `services/commands_destino.py`: Facturación y cierre.
    - `services/financial.py`: Registro de gastos y pagos.
    - `services/exceptions.py`: Bloqueos y cancelaciones.
    - `services/corrections.py`: Anulaciones (`void`) y versiones (`supersede`).
- **Compatibilidad**: El archivo `services/__init__.py` re-exporta todos los símbolos originales para no romper los imports existentes en el proyecto.

### S12-03: Consolidación `CommandDispatchView`
Se refactorizó `views.py` para eliminar 18 clases `APIView` redundantes de 3 líneas cada una.
- **Implementación**: Se creó una vista genérica que despacha peticiones `POST` a la función correspondiente en el paquete de `services` basada en un diccionario de mapeo.
- **Beneficio**: Reducción del código repetitivo en un 60% manteniendo las mismas URLs públicas de la API.

### S12-05: Paginación y Errores Estandarizados
Se implementó una política global de respuestas predecibles.
- **Paginación Opt-in**: Se activó en `Expedientes`, `Transfers` y `Liquidaciones` usando `StandardPagination` (25 items/pág).
    - Estructura: `{ count, next, previous, results: [...] }`.
- **Manejador de Excepciones**: Nueva capa en `backend/core/exception_handler.py`.
    - Estructura de Error:
      ```json
      {
        "error": true,
        "code": 400,
        "detail": "Error de validación",
        "errors": { "field_name": ["motivo"] }
      }
      ```
    - Se preservó el campo `errors` original de DRF para asegurar compatibilidad total con el frontend.

---

## 🛠️ Fase 1: Automatización (CI/CD)

### S12-07: Pipelines de GitHub Actions
Se crearon archivos de configuración para automatizar el ciclo de vida del código:
- **`ci.yml`**: Ejecuta `pytest` (backend), `ruff` (linter), `bandit` (seguridad) y `npm run build` (frontend) en cada Pull Request.
- **`deploy.yml`**: Automatiza el despliegue al servidor mediante SSH, realizando `docker compose pull`, `migrate` y un `healthcheck` de seguridad post-despliegue.

---

## 📦 Fase 2: Módulo de Inventario y Features

### S12-11: Implementación de Inventario (PLT-10)
Nuevo sistema de trazabilidad de stock físico.
- **Backend (`apps/inventario`)**:
    - Modelo `StockRecord`: Almacena el stock actual por producto, nodo y número de lote.
    - Índice único: `unique_together = ('product', 'node', 'lot_number')` para evitar duplicidad de lotes en el mismo lugar.
    - Propiedad `available`: Cálculo dinámico de `quantity - reserved`.
- **Frontend**:
    - Dashboard principal en `/[lang]/dashboard/inventario`.
    - Filtros por Nodo y Producto integrados.
    - CRUD completo usando los nuevos hooks `useFetch` y `useCRUD`.

### S12-08: Hooks React de Datos
Se crearon abstracciones para simplificar la comunicación con la API:
- **`useFetch<T>`**: Maneja estados de carga, error y autodetección de paginación (si detecta `results`, devuelve el array interno automáticamente).
- **`useCRUD`**: Centraliza las operaciones `create`, `update` y `delete` con notificaciones de éxito/error integradas vía `react-hot-toast`.

---

## 🐞 Correcciones de Último Minuto

1.  **Parsing de Paginación**: Se detectó que las pantallas de `Transfers` y `Nuevo Transfer` quedaron vacías tras activar la paginación en el backend. Se actualizaron los componentes para procesar el nuevo sobre `results`.
2.  **Visibilidad Sidebar**: Se movió el botón de **Inventario** al componente `src/components/Sidebar.tsx` (el activo en el layout principal), solucionando el problema de su desaparición.

---
**Reporte Completo - Sprint 12**
*Alejandro (Antigravity)*
