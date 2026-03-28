# Resumen Sprint 19 — Antigravity

**Fechas:** 28 de marzo 2026  
**Rama base:** `main`  
**Total de ítems completados:** 16 (13 en commit principal + 3 fixes/hotfixes post-merge)  
**Líneas modificadas:** +2,287 adiciones / -247 eliminaciones (commit principal)

---

## Objetivo del Sprint

Extender el formulario de creación de expedientes, construir la vista de detalle completa con secciones editables por estado, agregar modales de operaciones críticas (merge, split, pagos) y corregir todos los valores quemados (hardcoded) en el formulario.

---

## Items Completados

### S19-01 — Formulario Nuevo Expediente Extendido

**Estado:** ✅ Completado (con 3 hotfixes post-merge)

**Archivos modificados:**
- `frontend/src/app/[lang]/(mwt)/(dashboard)/expedientes/nuevo/page.tsx`

**Qué se hizo:**  
Se extendió el formulario de creación de expedientes (`/expedientes/nuevo`) para incluir los campos `purchase_order_number` (N° de Orden de Compra, opcional) y `operado_por` (CLIENTE / MWT / sin definir). Se agregó la sección de líneas de producto dinámica con soporte para agregar y eliminar filas.

**Hotfixes aplicados post-merge:**
1. `fix: load clients, brands and products from API (no hardcoded values)` — Se eliminaron todos los valores quemados. Clientes pasan a cargarse desde `GET api/clientes/`, marcas desde `GET api/brands/`, y productos desde `GET api/productos/`. Se agregaron spinners de carga y toasts de error por campo.
2. `feat: product lines auto-show filtered by brand, inline row layout with +/X controls` — Las líneas de producto siempre muestran al menos 1 fila activa. El select de productos se filtra automáticamente según la marca seleccionada. Diseño inline: `[Producto] [Cantidad] [X]` con botón `+ Agregar otra línea` al fondo.
3. `fix: remove brand name from product column header label` — Se eliminó el nombre de la marca del header de la columna de productos (antes mostraba `Producto (Orli Drake)`, ahora solo `Producto`).

**Por qué:** El formulario original tenía selects de clientes, marcas y productos con datos quemados o que llamaban a endpoints inexistentes, por lo que los campos aparecían vacíos o con datos incorrectos a los usuarios.

---

### S19-02 — Componente UrlField Reusable

**Estado:** ✅ Completado

**Archivos creados:**
- `frontend/src/components/UrlField.tsx` (+194 líneas)

**Qué se hizo:**  
Se creó un componente reutilizable `UrlField` que maneja 3 estados visuales para campos de URL: vacío (con botón para agregar), con valor guardado (con enlace externo y botón editar), y en modo edición (input activo con guardar/cancelar). Soporta validación de formato URL, feedback visual de guardado y estado de carga.

**Por qué:** Múltiples secciones del expediente (tracking, documentos, facturación) necesitan campos de URL con la misma lógica de edición inline. El componente centraliza esa lógica en un solo lugar para reutilizarlo en toda la vista de detalle.

---

### S19-03 — EstadoSection con Edición Inline por Estado

**Estado:** ✅ Completado

**Archivos creados:**
- `frontend/src/components/expediente/EstadoSection.tsx` (+342 líneas)

**Qué se hizo:**  
Se creó el componente `EstadoSection` que renderiza la sección de campos operativos de un expediente dependiendo del estado actual (PREPARACION, FABRICA, DESPACHO, TRANSITO, DESTINO). Cada estado tiene su propio set de campos editables inline con PATCH al backend. Incluye campos como `invoice_url`, `bl_url`, `tracking_url`, `eta`, `warehouse_arrival_date`, entre otros.

**Hotfix aplicado:**  
`fix: S19-12 correct invalid character in EstadoSection.tsx line 118` — Se corrigió un carácter hexadecimal inválido (`\x2014`) que causaba error de compilación TypeScript en la línea 118.

**Por qué:** La vista de detalle del expediente necesita mostrar y permitir editar los campos operativos específicos para cada etapa del flujo logístico, sin recargar la página completa.

---

### S19-04 — Hook useOperadoPor Centralizado

**Estado:** ✅ Completado

**Archivos creados:**
- `frontend/src/hooks/useOperadoPor.ts` (+35 líneas)

**Qué se hizo:**  
Se creó el hook `useOperadoPor` que encapsula la lógica para leer y actualizar el campo `operado_por` de un expediente. Expone el valor actual, estado de carga y la función `update(valor)` que ejecuta un PATCH a `api/expedientes/{id}/` con el nuevo valor. Maneja errores con toast.

**Por qué:** El campo `operado_por` es accedido desde múltiples componentes (formulario nuevo, vista detalle, sección de estado). Centralizar la lógica en un hook evita duplicación y garantiza consistencia en el comportamiento.

---

### S19-05 — FactoryOrderTable con CRUD Completo

**Estado:** ✅ Completado

**Archivos creados:**
- `frontend/src/components/expediente/FactoryOrderTable.tsx` (+312 líneas)

**Qué se hizo:**  
Se creó el componente `FactoryOrderTable` que muestra y gestiona las órdenes de fábrica asociadas a un expediente. Permite crear nuevas órdenes (modal con formulario), editar inline el número de fábrica y estado, y eliminar órdenes con confirmación. Consume `GET/POST/PATCH/DELETE api/expedientes/{id}/factory-orders/`. Las filas muestran `factory_order_number`, `status`, `quantity` y `notes`.

**Por qué:** Las órdenes de fábrica son el primer nivel operativo del flujo. Los usuarios necesitan gestionar múltiples órdenes por expediente desde la vista de detalle sin ir al admin de Django.

---

### S19-06 — ModalMerge en 2 Pasos

**Estado:** ✅ Completado

**Archivos creados:**
- `frontend/src/components/expediente/ModalMerge.tsx` (+254 líneas)

**Qué se hizo:**  
Se creó el modal `ModalMerge` con flujo en 2 pasos: (1) búsqueda y selección del expediente destino con filtro por marca/cliente, (2) confirmación con resumen de los expedientes involucrados. Al confirmar ejecuta `POST api/expedientes/merge/` con los IDs de origen y destino. Muestra badge de estado y código del expediente destino para identificación rápida.

**Por qué:** La operación de merge (fusionar expedientes) es crítica y destructiva, por lo que requiere confirmación en 2 pasos para evitar errores operativos.

---

### S19-07 — ModalSplit con Checkboxes

**Estado:** ✅ Completado

**Archivos creados:**
- `frontend/src/components/expediente/ModalSplit.tsx` (+241 líneas)

**Qué se hizo:**  
Se creó el modal `ModalSplit` que permite dividir un expediente en dos. Muestra la lista de líneas de producto del expediente con checkboxes para seleccionar cuáles se mueven al nuevo expediente hijo. Valida que no se seleccionen todas ni ninguna línea. Al confirmar ejecuta `POST api/expedientes/split/` con los IDs de líneas seleccionadas.

**Por qué:** La operación de split permite separar productos de un mismo expediente en dos expedientes independientes cuando llegan en embarques distintos o requieren manejo separado.

---

### S19-08 — PagosSection y ModalRegistrarPago

**Estado:** ✅ Completado

**Archivos creados:**
- `frontend/src/components/expediente/PagosSection.tsx` (+169 líneas)
- `frontend/src/components/expediente/ModalRegistrarPago.tsx` (+117 líneas)

**Qué se hizo:**  
`PagosSection` muestra el historial de pagos del expediente en tabla con columnas: fecha, monto, tipo, referencia, registrado por. Consume `GET api/expedientes/{id}/pagos/`. Incluye botón para abrir `ModalRegistrarPago`.  
`ModalRegistrarPago` contiene el formulario de registro de pago con campos: monto, moneda (USD/CRC), tipo (ANTICIPO/SALDO/PARCIAL), referencia bancaria y notas. Ejecuta `POST api/expedientes/{id}/pagos/confirm/`.

**Por qué:** El control de pagos asociados a un expediente es un requisito operativo crítico. La sección permite al equipo MWT registrar y auditar todos los movimientos financieros por expediente.

---

### S19-09 — MergedBanner Navegable

**Estado:** ✅ Completado

**Archivos creados:**
- `frontend/src/components/expediente/MergedBanner.tsx` (+68 líneas)

**Qué se hizo:**  
Se creó el componente `MergedBanner` que muestra un banner informativo cuando un expediente ha sido fusionado con otro. Muestra el código del expediente padre/destino con un enlace clickeable que navega a ese expediente. Incluye ícono de merge, mensaje explicativo y botón de dismiss.

**Por qué:** Cuando un expediente es fusionado queda como registro histórico pero inactivo. El banner orienta al usuario para navegar al expediente activo resultante del merge.

---

### S19-11 — tracking_url Editable en DESPACHO con Carry-forward a TRANSITO

**Estado:** ✅ Completado (implementado dentro de EstadoSection)

**Archivos modificados:**
- `frontend/src/components/expediente/EstadoSection.tsx`

**Qué se hizo:**  
El campo `tracking_url` es editable mediante el componente `UrlField` cuando el expediente está en estado DESPACHO. Al transicionar a TRANSITO, el valor se lleva automáticamente (carry-forward) para mantener trazabilidad del envío sin tener que re-ingresar la URL.

**Por qué:** La URL de seguimiento se asigna en DESPACHO (cuando sale de fábrica) y debe seguir siendo visible y accesible en TRANSITO (mientras viaja). Es un dato crítico para monitoreo.

---

### S19-12 — Barrido de Caracteres Hex Inválidos en [id]/page.tsx

**Estado:** ✅ Completado

**Archivos modificados:**
- `frontend/src/app/[lang]/(mwt)/(dashboard)/expedientes/[id]/page.tsx` (+93 / -96 líneas)
- `frontend/src/components/expediente/EstadoSection.tsx` (hotfix adicional)

**Qué se hizo:**  
Se realizó un barrido completo de la página de detalle de expediente para reemplazar todos los caracteres hexadecimales directos (como `\x2014`, `\x2019`, etc.) por sus equivalentes Unicode escapados (`\u2014`, `\u2019`) o por entidades JSX. Esto previene errores de compilación TypeScript/Next.js con ciertos parsers de archivos.

**Por qué:** Los caracteres hex directos en strings JSX causaban `SyntaxError` intermitentes en el build de producción dependiendo de la configuración del parser de TypeScript.

---

### S19-15 — PricingTooltip Dinámico Nivel 1 y 2

**Estado:** ✅ Completado

**Archivos creados:**
- `frontend/src/components/expediente/PricingTooltip.tsx` (+114 líneas)

**Qué se hizo:**  
Se creó el componente `PricingTooltip` que muestra información de pricing al hacer hover sobre el precio de un expediente o línea de producto. Nivel 1 muestra precio base, precio CIF/FOB/EXW y márgenes. Nivel 2 (expandible) muestra el desglose por tarifas, impuestos y comisiones. Los datos se cargan dinámicamente desde `GET api/expedientes/{id}/pricing/`.

**Por qué:** El equipo comercial necesita acceso rápido al desglose de precios sin salir de la vista de expediente. El tooltip evita navegación extra y mantiene el contexto de trabajo.

---

### S19-16 — Dependencia recharts ^2.15.3

**Estado:** ✅ Completado

**Archivos modificados:**
- `frontend/package.json` (+1 línea)
- `frontend/package-lock.json` (actualizado con dependencias de recharts)

**Qué se hizo:**  
Se agregó `recharts` versión `^2.15.3` como dependencia en `package.json` y se actualizó `package-lock.json` con el árbol completo de dependencias. Recharts es la librería de gráficos basada en React/D3 usada para los componentes de visualización de datos del dashboard.

**Por qué:** Varios componentes de analítica y dashboard planificados para sprints siguientes requieren recharts. Se agrega en este sprint para que esté disponible desde el inicio.

---

## Resumen de Archivos por Tipo

### Archivos Creados (nuevos)

| Archivo | Líneas | Descripción |
|---|---|---|
| `frontend/src/components/UrlField.tsx` | +194 | Componente reusable para campos URL con 3 estados |
| `frontend/src/components/expediente/EstadoSection.tsx` | +342 | Sección de campos editables por estado del expediente |
| `frontend/src/components/expediente/FactoryOrderTable.tsx` | +312 | Tabla CRUD de órdenes de fábrica |
| `frontend/src/components/expediente/ModalMerge.tsx` | +254 | Modal para fusionar expedientes en 2 pasos |
| `frontend/src/components/expediente/ModalSplit.tsx` | +241 | Modal para dividir expedientes con checkboxes |
| `frontend/src/components/expediente/PagosSection.tsx` | +169 | Sección de historial y registro de pagos |
| `frontend/src/components/expediente/ModalRegistrarPago.tsx` | +117 | Modal formulario de registro de pago |
| `frontend/src/components/expediente/MergedBanner.tsx` | +68 | Banner informativo para expedientes fusionados |
| `frontend/src/components/expediente/PricingTooltip.tsx` | +114 | Tooltip de desglose de precios nivel 1+2 |
| `frontend/src/hooks/useOperadoPor.ts` | +35 | Hook centralizado para campo operado_por |

### Archivos Modificados

| Archivo | +/- | Razón del cambio |
|---|---|---|
| `frontend/src/app/[lang]/(mwt)/(dashboard)/expedientes/nuevo/page.tsx` | +347 / -151 | Formulario extendido, campos nuevos, líneas de producto dinámicas, carga desde API |
| `frontend/src/app/[lang]/(mwt)/(dashboard)/expedientes/[id]/page.tsx` | +93 / -96 | Barrido de caracteres hex, integración de nuevos componentes |
| `frontend/package.json` | +1 | Agregar dependencia recharts ^2.15.3 |
| `frontend/package-lock.json` | actualizado | Árbol de dependencias recharts |

---

## Commits del Sprint 19

| SHA | Fecha | Descripción |
|---|---|---|
| [`ecafa11`](https://github.com/Ale241302/mwt_one/commit/ecafa11b9b82f50803c9033a0035e4b596eaa4f6) | 2026-03-28 | feat: Sprint 19 — 13 items (commit principal) |
| [`b8ccb6d`](https://github.com/Ale241302/mwt_one/commit/b8ccb6d93c92de984213d1578d855ee5aa970967) | 2026-03-28 | fix: update package-lock.json con recharts |
| [`a869f75`](https://github.com/Ale241302/mwt_one/commit/a869f7534c9b213746ff6b24bd888d472b39a36c) | 2026-03-28 | fix: S19-12 carácter inválido en EstadoSection.tsx línea 118 |
| [`2f678f9`](https://github.com/Ale241302/mwt_one/commit/2f678f923519da1f5a82e9e56e1c6fb81488a928) | 2026-03-28 | fix: cargar clientes, marcas y productos desde API (sin hardcoded) |
| [`f00a208`](https://github.com/Ale241302/mwt_one/commit/f00a208ec06bdd62fa33d39a57727211a30c9953) | 2026-03-28 | feat: líneas de producto auto-show filtradas por marca, layout inline +/X |
| [`6aa760d`](https://github.com/Ale241302/mwt_one/commit/6aa760dba07a803e910494da75bf9c0b38d1574f) | 2026-03-28 | fix: quitar nombre de marca del header de columna productos |

---

## Notas Técnicas

- Todos los componentes nuevos usan variables CSS (`var(--color-*)`) del design system existente, sin colores hardcoded.
- Los modales usan `react-hot-toast` para feedback de éxito/error.
- El filtrado de productos por marca en el formulario es client-side (se cargan todos los productos y se filtra con `.filter()`).
- El hook `useOperadoPor` es el primer hook de dominio específico del módulo expedientes — establece el patrón para hooks similares en sprints futuros.
- S19-10 (asignación de documentos por estado) y S19-13/S19-14 quedaron pendientes para el Sprint 20.
