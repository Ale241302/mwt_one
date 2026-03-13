# PLB_INDEXACION — Protocolo de Indexación y Gate de Auto-Auditoría
status: DRAFT
visibility: [INTERNAL]
domain: Gobernanza (IDX_GOBERNANZA)
version: 1.0
last_updated: 2026-03-11
tipo: Playbook (instrucción operativa)
refs: POL_DETERMINISMO, POL_NUEVO_DOC, POL_STAMP, ENT_GOB_PENDIENTES

---

## A. Propósito

Garantizar que todo output de indexación cumpla las reglas del sistema antes de ser entregado al CEO. El agente corre el gate internamente — el CEO nunca debe preguntar si se cumplieron las reglas.

---

## B. Trigger

El gate se activa automáticamente cuando el CEO dice **"indexa"**. Sin esa palabra, el contenido permanece en discusión. No se generan archivos.

---

## C. Gate de auto-auditoría (obligatorio antes de cualquier output)

El agente corre este checklist internamente antes de producir archivos. Si algún ítem falla, lo corrige primero. El CEO solo ve output limpio.

| # | Check | Ref | Acción si falla |
|---|-------|-----|----------------|
| 1 | El contenido reemplaza, no duplica ni parchea | POL_DETERMINISMO | Fusionar en documento canónico existente |
| 2 | Tipo de documento correcto (ENT_/SCH_/PLB_/POL_/IDX_/LOC_/LOTE_) | POL_NUEVO_DOC | Reclasificar antes de generar |
| 3 | Stamp incluido con estado correcto | POL_STAMP | Agregar stamp |
| 4 | Version bump respecto a versión en KB | RW_ROOT meta-reglas | Incrementar versión |
| 5 | Documentos impactados por el cambio están actualizados | POL_DETERMINISMO | Actualizar en el mismo batch |
| 6 | ENT_GOB_PENDIENTES refleja lo resuelto y lo nuevo abierto | ENT_GOB_PENDIENTES | Actualizar pendientes en el mismo batch |
| 7 | Ningún dato inventado — campos sin dato real marcados [PENDIENTE] | RW_ROOT meta-reglas | Marcar [PENDIENTE — NO INVENTAR] |
| 8 | IDX del dominio afectado registra el documento nuevo o modificado | IDX_{DOMINIO} | Actualizar IDX en el mismo batch |

---

## D. Reporte del gate

El agente reporta el resultado del gate antes de presentar los archivos, con este formato:

```
GATE ✅ / ❌
□ Determinismo     — [descripción]
□ Tipo             — [tipo asignado]
□ Stamp            — [estado]
□ Version          — [anterior → nueva]
□ Impacto cruzado  — [documentos actualizados]
□ Pendientes       — [resueltos / nuevos abiertos]
□ Sin inventados   — [confirmado / campos marcados]
□ IDX              — [IDX afectado actualizado]
```

Si algún check es ❌, el agente lo corrige antes de presentar archivos. No entrega output parcial.

---

## E. Regla de batch

Todos los documentos afectados por una indexación se entregan en el mismo batch. No hay entregas parciales que requieran una segunda ronda para completar el impacto cruzado.

---

## F. Lo que el CEO no necesita hacer

- Preguntar si se cumplieron las reglas.
- Verificar que ENT_GOB_PENDIENTES fue actualizado.
- Pedir que se corra el gate retroactivamente.

El CEO solo necesita: revisar el reporte del gate, revisar los archivos, y subirlos al proyecto.

---

Stamp: DRAFT — Pendiente aprobación CEO
