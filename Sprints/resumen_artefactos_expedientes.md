# Resumen de Gestión de Artefactos en Expedientes

Este documento resume la evolución y el estado actual del sistema de gestión de artefactos en los expedientes, consolidando los cambios realizados en los Sprints 20, 20B y las optimizaciones recientes de UX/UI.

---

## 1. Cambio de Paradigma: De Monolítico a Proformas (ART-02)

Históricamente, el expediente era un objeto único con un modo fijo. Ahora, el expediente funciona como un **contenedor de Proformas (ART-02)**.

- **Multi-Proforma**: Un expediente puede tener múltiples proformas.
- **Modos Independientes**: Cada proforma puede operar en **Modo B (Comisión)** o **Modo C (FULL)** de forma independiente.
- **Jerarquía de Artefactos**: Los artefactos operativos (facturas, sap, fletes) se vinculan directamente a una proforma a través del campo `parent_proforma`, no al expediente global.
- **Asignación de Líneas**: Las líneas de producto (`ExpedienteProductLine`) se asignan a proformas específicas.

---

## 2. Motor de Políticas (Artifact Policy)

La lógica de qué artefactos deben mostrarse en cada fase se ha movido al **Backend**.

- **Backend-Driven**: El frontend consume un objeto `artifact_policy` del bundle del expediente.
- **Dinámico**: La política se calcula en tiempo real basándose en los modos de las proformas completadas.
- **Categorías de Artefactos**:
    - **Required**: Obligatorios para la fase. Aparecen por defecto.
    - **Optional**: No obligatorios. Se agregan mediante el botón "+ Agregar Artefacto".
    - **Gate for Advance**: Artefactos que bloquean el salto a la siguiente fase si no están completados.

---

## 3. Gestión de Artefactos (Admin Workflow)

Se ha optimizado el flujo de trabajo para administradores, eliminando menús complejos e inconsistencias visuales.

### A. Adición de Artefactos (Modal de Selección)
Se reemplazó el listado desplegable inline por un **Modal de Selección Centralizado** (`AddArtifactModal`).

1.  El administrador hace clic en **"+ Agregar artefacto (admin)"**.
2.  Se abre un modal con la lista completa de artefactos disponibles (`ARTIFACT_UI_REGISTRY`).
3.  El modal muestra cuántos registros existen de ese tipo para evitar duplicidad accidental.
4.  Al seleccionar uno, el sistema:
    -   Lo agrega a la política del expediente en esa fase.
    -   **Flujo Automatizado**: Dispara inmediatamente el modal de registro del artefacto, ahorrando clics al administrador.

### B. Eliminación de Artefactos (Control Total Admin)
Anteriormente, los artefactos "Requeridos" por la política base no podían eliminarse. Ahora:

- **Overrides de Administrador**: El icono de eliminar (basurero rojo) es visible para **todos** los artefactos en la lista para un Administrador.
- **Eliminación "Sí o Sí"**: Un administrador puede remover cualquier artefacto de la fase (incluso ART-01 o ART-02), lo cual actualiza la `custom_artifact_policy` en el backend para ese expediente.

---

## 4. Componentes Clave del UI

### `ExpedienteAccordion.tsx`
Orquestador principal que renderiza las fases del expediente.
- **Filtro de Estados**: Filtra estados no operativos como `CANCELADO` de la vista estándar.
- **Legacy Fallback**: Si un expediente es antiguo (pre-Sprint 20), usa un sistema de renderizado alternativo para mantener la compatibilidad.

### `ArtifactSection.tsx`
Componente genérico que renderiza la lista de artefactos de una fase o proforma.
- Muestra el estado actual del artefacto (DRAFT, COMPLETED, VOIDED).
- Gestiona la visualización de botones de acción (Registrar, Editar, Eliminar).

### `ProformaSection.tsx`
Agrupa visualmente las líneas de producto y los artefactos que pertenecen a una proforma específica.
- Muestra el Badge de Modo (Azul para B, Verde para C).
- Indica quién opera la proforma (`operated_by`).

---

## 5. Reglas de Validación y Gates

Para avanzar de una fase a otra (ej. de REGISTRO a PRODUCCION), el sistema valida:
1.  **Gate de Artefactos**: Que todos los artefactos marcados como `gate_for_advance` en la política estén `COMPLETED`.
2.  **Líneas Huérfanas**: No pueden existir líneas de producto sin proforma asignada.
3.  **Modos Definidos**: Todas las proformas deben tener un modo (B o C) definido.

---

> [!IMPORTANT]
> **Nota para Administradores**: La Orden de Compra (ART-01) y la Proforma (ART-02) siempre deben estar presentes en la fase de REGISTRO para poder avanzar. Si se eliminan accidentalmente, pueden volver a agregarse usando el botón de "+ Agregar artefacto (admin)".
