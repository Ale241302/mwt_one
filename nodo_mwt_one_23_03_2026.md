# Estructura de Módulos y Campos

A continuación se detalla el orden de los módulos del sistema y los campos que conforman cada uno de ellos. 

**Nota importante:** Los módulos 8, 9 y 10 tienen una dependencia estricta y requieren que exista un **Expediente** creado (Módulo 7) para poder operar.

---

## 1. Módulo: Brands
* **Orden:** 1
* **Campos:**
  * Nombre
  * Código
  * Activa

## 2. Módulo: Productos
* **Orden:** 2
* **Campos:**
  * Nombre del Producto
  * Marca
  * SKU
  * Categoria
  * Descripcion

## 3. Módulo: Nodos
* **Orden:** 3
* **Campos:**
  * Nombre
  * Tipo de Nodo
  * Ubicación
  * Entidad Legal
  * Estado

## 4. Módulo: Inventario
* **Orden:** 4
* **Campos:**
  * Producto
  * Nodo
  * Cantidad
  * Reservado
  * Número de Lote
  * Fecha de Recepción

## 5. Módulo: Transferencias
* **Orden:** 5
* **Campos:**
  * Nodo origen
  * Nodo Destino
  * Contexto Legal
  * Expediente Asociado
  * Lineas de Productos
  * Cantidad

## 6. Módulo: Clientes
* **Orden:** 6
* **Campos:**
  * Nombre
  * Contacto
  * Teléfono
  * Email
  * País
  * Entidad Legal
  * Activo

## 7. Módulo: Expedientes
* **Orden:** 7
* **Campos:**
  * Cliente
  * Marca
  * Modo
  * Destino
  * Modo de Flete
  * Modo de Despacho
  * Base de Precio
  * Notas

## 8. Módulo: Registro Costos
* **Orden:** 8
* **Dependencia:** Requiere un expediente creado previamente.
* **Campos:**
  * Tipo de Costo
  * Monto *(Corregido de "Moto")*
  * Divisa
  * Visibilidad

## 9. Módulo: Registrar Pagos
* **Orden:** 9
* **Dependencia:** Requiere un expediente creado previamente.
* **Campos:**
  * Monto
  * Metodo de Pago
  * Referencia

## 10. Módulo: Materialización Logistica
* **Orden:** 10
* **Dependencia:** Requiere un expediente creado previamente.
* **Campos:**
  * Id Operación Logistica