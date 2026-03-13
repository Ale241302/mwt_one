# ENT_PLAT_ARTEFACTOS — Artefactos Modulares del Centro de Operaciones
status: DRAFT
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
version: 1.0

---

## A. Concepto

Artefacto = módulo pluggable que se agrega a un expediente. Similar a Page Builder donde se arrastran módulos. Cada artefacto tiene:
- Configuración propia (campos, opciones, valores por defecto según contexto)
- Reglas internas (validaciones, cálculos, restricciones)
- Interfaz estándar (inputs que recibe, outputs/eventos que emite)
- Extensibilidad (si caso nuevo no cabe, se programa artefacto nuevo y se enchufa)

## B. Catálogo de artefactos

| ID | Artefacto | Función | Trigger | Emite evento |
|----|-----------|---------|---------|-------------|
| ART-01 | OC Cliente | Documento entrante, inicia expediente | Manual | oc.received |
| ART-02 | Proforma MWT | Consecutivo, líneas producto, puede dividir AA/AB | Manual | proforma.created |
| ART-03 | Decisión B/C | CEO elige modo operación [CEO-ONLY] | Manual | mode.selected |
| ART-04 | Confirmación SAP | ID Marluvas, fecha fabricación | Manual | sap.confirmed |
| ART-05 | AWB/BL | Carrier, ruta, tracking, itinerario | Manual | shipment.created |
| ART-06 | Cotización flete | Monto, modo, prepaid/postpaid | Manual | freight.quoted |
| ART-07 | Aprobación despacho | Quién aprobó (cliente/CEO), fecha | Manual | dispatch.approved |
| ART-08 | Documentación aduanal | Permisos, NCM, DAI% | Condicional (dispatch_mode=mwt) | customs.ready |
| ART-09 | Factura MWT | Vista client siempre | Auto (condiciones cumplidas) | invoice.issued |
| ART-10 | Factura comisión | Solo modo B | Auto | commission.invoiced |
| ART-11 | Registro costos | Vista internal, se llena progresivamente | Auto | cost.registered |
| ART-12 | Nota compensación | Producto extra por sobreprecio [CEO-ONLY] | Manual | compensation.noted |

## C. Artefactos obligatorios por flujo

### C1. Marluvas modo B (comisión)
ART-01, ART-02, ART-03, ART-04, ART-05, ART-06, ART-07, ART-10, ART-11.
Opcional: ART-08 (si dispatch_mode=mwt), ART-12 (si hay compensación).

### C2. Marluvas modo C (FULL)
ART-01, ART-02, ART-03, ART-04, ART-05, ART-06, ART-07, ART-09, ART-11.
Opcional: ART-08 (si dispatch_mode=mwt), ART-12 (si hay compensación).

### C3. Tecmater (siempre FULL)
ART-01, ART-02, ART-05, ART-06, ART-07, ART-09, ART-11.
No usa: ART-03 (siempre FULL), ART-04 (sin SAP), ART-10 (sin comisión).
Opcional: ART-08 (si dispatch_mode=mwt).

### C4. Rana Walk
ART-01, ART-02, ART-05, ART-06, ART-09, ART-11.
No usa: ART-03, ART-04, ART-10.
Variante: bifurcación CR (nacionalización) vs reexportación.

## D. Interfaz estándar de artefacto

```
Artifact {
  id: string                    # ART-XX
  name: string                  # Nombre humano
  config: Object                # Campos configurables (varían por artefacto)
  required_inputs: string[]     # Qué necesita para ejecutarse
  outputs: string[]             # Qué produce
  events: string[]              # Eventos que emite al bus
  validation_rules: Rule[]      # Reglas internas de validación
  state: enum                   # pending / active / complete / blocked
  completed_at: datetime | null
  completed_by: string | null   # Quién lo completó (user o system)
}
```

[PENDIENTE — ARCH-01: Artifact Contract Specification formal. Definir schema JSON completo, versionamiento, registro de artefactos nuevos, declaración de dependencias entre artefactos.]

## E. Artefacto Envío (ART-05) — ejemplo configuración compleja

### E1. Campos
- transport_mode: aéreo / marítimo
- freight_mode: prepaid / postpaid
- carrier: lista por modo (diferentes tracking APIs)
- ruta: origen → destino con/sin escalas
- itinerario: segmentos con fechas, cada tramo sub-registro
- dispatch_mode: mwt / client
- consolidacion: sí / no

### E2. Reglas internas
- Si modo marítimo y volumen < X → sugerir aéreo (basado en punto óptimo histórico).
- Si carrier específico + ruta específica → tiempo estimado = promedio histórico.
- Si prepaid → validar factura proveedor incluye línea flete.
- Si itinerario con escalas → crear sub-registros por tramo.
- Si consolidación → ajustar tiempos y costos.

## F. Versionamiento

Si un artefacto cambia su interfaz, expedientes activos que lo usan no se rompen. Artefacto nuevo = versión nueva. Expedientes existentes siguen con versión anterior. Solo expedientes nuevos usan versión nueva.

---

Stamp: DRAFT — Pendiente aprobación CEO
