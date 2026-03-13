# PLB_REGISTRO_PROFORMA — Playbook Registro de Proforma Marluvas
status: DRAFT
visibility: [INTERNAL]
domain: Comercial (IDX_COMERCIAL)
version: 1.0
classification: PLAYBOOK — Instrucciones operativas secuenciales.
refs: SCH_PROFORMA_MWT, ENT_COMERCIAL_CLIENTES, ENT_OPS_EXPEDIENTE.F1, ENT_OPS_STATE_MACHINE.C1-C5, POL_PRINT

---

## A. Propósito

Proceso end-to-end desde recepción de OC de cliente hasta envío de proforma a Marluvas para registro en SAP. Aplica a todas las proformas del canal Marluvas independientemente del mercado.

---

## B. Flujo — 5 pasos

### B1. Trigger — Recepción de OC

Email llega a alvaro@muitowork.com con OC adjunta del cliente.
n8n detecta el correo, extrae adjuntos, identifica cliente.

Datos a extraer de la OC:
- Cliente (cruzar contra ENT_COMERCIAL_CLIENTES §B)
- SKUs / códigos producto
- Cantidades por talla
- Precios del cliente (USD)
- Término comercial (FOB/FCA/CIF)
- Condiciones de pago

### B2. Evaluación CEO

CEO revisa OC y evalúa:
- Cruce de precios OC vs Tabela COMEX → obtener precios Marluvas
- Delta por línea (precio cliente - precio Marluvas)
- Comisión aplicable por mercado (varía por cliente/país)
- Viabilidad del pedido

Nota: cada mercado tiene sensibilidad de precio diferente. Las comisiones no son fijas — se revisan por OC.

### B3. Generar Proforma MWT (ART-02)

Se genera proforma dual-view según SCH_PROFORMA_MWT:
- Vista CEO: precios paralelos, comisión, arbitraje, cadena determinista
- Vista Marluvas: precios cliente, líneas, tallas, condiciones

Datos obligatorios (ref SCH_PROFORMA_MWT):
- Nombre canónico del cliente (exacto per ENT_COMERCIAL_CLIENTES §B)
- Cód. SAP Marluvas (campo codigo_marluvas de ENT_COMERCIAL_CLIENTES §B)
- Consecutivo proforma (XXXX-YYYY)
- Tallas BRA por línea

Output: HTML print-ready (ref POL_PRINT) + PDF.

### B4. Draft a CEO + Revisión

Se genera draft de email a alvaro@muitowork.com (NUNCA directo a Marluvas).

**Formato del email:**
- Idioma: PT-BR
- Sin firma (Gmail la inyecta automáticamente)
- Sin notas operacionales fijas (se agregan caso a caso)
- Tono: directo, no acartonado
- Subject: `Registro de Proforma nº XXXX-XXXX – CLIENTE / País`

**Estructura del cuerpo:**
```
Prezados,

Segue para registro a proforma XXXX-XXXX.

▸ Cliente: [NOMBRE CANÓNICO] (Cód. SAP [CÓDIGO])
▸ País: [PAÍS]
▸ Pagamento: [CONDICIÓN]
▸ Comissão: [X]%
▸ Total: [N] pares – USD [TOTAL]

────────────────────────────────────────
[CÓDIGO] – [REFERENCIA] – [N] pares – $[PRECIO]
▸ [talla]:[qty] · [talla]:[qty] · ...

[CÓDIGO] – [REFERENCIA] – [N] pares – $[PRECIO]
▸ [talla]:[qty] · [talla]:[qty] · ...
────────────────────────────────────────

Proforma em anexo. Aguardo confirmação do registro.
```

**Adjunto:** Proforma PDF (vista Marluvas impresa)

**CEO revisa el draft y decide:**
- Modalidad: triangulación vs directo
- A nombre de: Muito Work Limitada o del cliente
- Ajustes de comisión / precio por línea
- Notas operacionales específicas (ej: consumo de inventario, producción parcial)
- Destinatarios finales

### B5. CEO envía

CEO reenvía desde su correo cuando está satisfecho.

Destinatarios estándar:
- TO: backoffice@marluvas.com.br
- CC: João Paulo Neves, Samuel Fernandes, Maycon Melo

Esto equivale a materializar C2 (RegisterOC) + C3 (CreateProforma) en la state machine del expediente (ref ENT_OPS_STATE_MACHINE).

---

## C. Reglas

1. **Draft a CEO, nunca directo.** El email siempre pasa por revisión antes de llegar a Marluvas.
2. **Idioma PT-BR obligatorio.** Toda comunicación con Marluvas es en portugués brasileño.
3. **Nombre canónico + SAP obligatorio.** Ref ENT_COMERCIAL_CLIENTES §C.1 y §C.2.
4. **Tallas inline en el email.** Formato compacto: talla:qty · talla:qty. Permite al digitador verificar sin abrir PDF.
5. **Sin datos fijos de firma.** Gmail los inyecta automáticamente.
6. **Sin notas operacionales genéricas.** Las notas son caso a caso según la realidad del pedido.
7. **Comisión se revisa por OC.** No hay comisión fija por mercado — cada pedido se evalúa individualmente.

---

## D. Relación con State Machine

| Paso playbook | Command SM | Artefacto | Nota |
|---------------|-----------|-----------|------|
| B1 (OC recibida) | C1 CreateExpediente | — | CEO crea expediente, status=REGISTRO |
| B1 (OC registrada) | C2 RegisterOC | ART-01 | OC como artefacto del expediente |
| B2 (Evaluación) | — | — | Análisis CEO, no muta sistema |
| B3 (Proforma) | C3 CreateProforma | ART-02 | Requiere ART-01 |
| B4 (Draft + revisión) | C4 DecideModeBC | ART-03 | CEO decide B/C durante revisión |
| B5 (Envío) | — | — | Comunicación externa de ART-01+02+03 a Marluvas |
| Post-B5 (Marluvas confirma) | C5 RegisterSAPConfirmation | ART-04 | Auto-transición → PRODUCCION |

Nota: B5 no ejecuta commands — es la comunicación externa de artefactos ya materializados en B1-B4. La respuesta de Marluvas (C5) cierra el ciclo REGISTRO y dispara la transición a PRODUCCION.

---

Stamp: DRAFT — Pendiente aprobación CEO
