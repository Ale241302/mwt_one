# S9 FASE 2 — Liquidaciones Marluvas UI

Branch: `feat/s9-liquidaciones`
Items: S9-08, S9-09
Prioridad: P1
Depende de: Nada (paralelo a Fase 0/1)

---

## S9-08 — Lista de liquidaciones (/liquidaciones)

**Agente:** AG-03 Frontend
**Ruta:** `/liquidaciones` (NUEVA)
**Estado:** ⏳ PENDIENTE

### Tabla
Columnas: Período | Monto total | Expedientes (count) | Estado | Fecha

Estados posibles: `pendiente` / `parcial` / `reconciliada` / `cerrada`

### Acción
- Botón "Nueva liquidación" → form con período (mes/año) + selección expedientes

### Copy
- Título: `Liquidaciones`
- Subtítulo: `Reconciliación de pagos Marluvas`
- Tabla vacía: `Sin liquidaciones registradas`

### ⚠️ Pendiente backend (S9-P01)
Verificar URL exacta del endpoint de liquidaciones (ART-10 Sprint 5) con el CEO antes de implementar.

### Criterio DONE
- [ ] Tabla con datos reales
- [ ] Botón "Nueva liquidación" funcional
- [ ] Form con período + expedientes

---

## S9-09 — Detalle liquidación — reconciliación visual

**Agente:** AG-03 Frontend
**Ruta:** `/liquidaciones/[id]` (NUEVA)
**Estado:** ⏳ PENDIENTE
**Depende de:** S9-08

### Funcionalidad
- Drag-and-drop upload Excel Marluvas
- Tabla comparativa línea a línea:
  - Columnas Marluvas: SKU, cantidad, precio unitario, total
  - Columnas MWT: SKU (mapped via SKUAlias), cantidad esperada, precio esperado, total esperado
  - Columna diferencia: delta por línea. **Rojo si >0, verde si match**
- Resumen: total conciliado, pendiente, diferencia neta
- Acciones:
  - "Aprobar línea" individual
  - "Disputar" (marca para revisión)
  - "Aprobar todas coincidentes" bulk

### Copy
- Upload: `Arrastra el Excel de Marluvas aquí o haz clic para seleccionar`
- Match: `Conciliado` (verde)
- Diferencia: `Discrepancia: $X.XX` (rojo)
- Aprobación: `Aprobar línea` / `Aprobar todas coincidentes`

### Criterio DONE
- [ ] Upload Excel procesa
- [ ] Tabla comparativa muestra diferencias en rojo/verde
- [ ] Aprobación bulk funciona
- [ ] Resumen con totales correctos

---

*Spec: LOTE_SM_SPRINT9.md v2.0 | Ref: ART-10 Sprint 5*
