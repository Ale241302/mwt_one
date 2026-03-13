# ENT_GOB_PROVEEDORES — Registro de Proveedores
id: ENT_GOB_PROVEEDORES
version: 1.0
domain: Gobernanza (IDX_GOBERNANZA)
status: DRAFT
visibility: [INTERNAL]
stamp: DRAFT — pendiente aprobación CEO
iso: 9001:2015 §8.4
origin: Audit externo ChatGPT — Hallazgo 4

---

## A. Propósito

Registro único de proveedores de MWT con clasificación, evaluaciones y registro de incidentes. Ref → PLB_SUPPLIER_EVAL para protocolo de evaluación.

---

## B. Registro de proveedores

| ID | Proveedor | Razón social | País | Producto/Servicio | Clase | Status |
|----|----------|-------------|------|------------------|-------|--------|
| SUP-001 | Marluvas | Marluvas Calçados de Segurança | Brasil | Calzado de seguridad | CRÍTICO | ACTIVO |
| SUP-002 | Bangni | Henan Bangni Biological Engineering Co., Ltd. | China (Henan) | Plantillas biomecánicas Rana Walk | CRÍTICO | ACTIVO |
| SUP-003 | OEM Scanner | [En selección] | China | Hardware scanner presión plantar | CRÍTICO | EN SELECCIÓN |
| SUP-004 | Hostinger | Hostinger International Ltd. | Global | Infraestructura servidor KVM 8 | IMPORTANTE | ACTIVO |
| SUP-005 | [Forwarders] | [Varios — registrar conforme se confirmen] | Varios | Flete marítimo/aéreo | IMPORTANTE | [PENDIENTE — registrar individualmente] |
| SUP-006 | Tecmater | [PENDIENTE — status sin definir] | [PENDIENTE] | [PENDIENTE] | [PENDIENTE] | [PENDIENTE] |

---

## C. Historial de incidentes

| Fecha | Proveedor | Descripción | Impacto | Acción tomada | NC ref |
|-------|----------|-------------|---------|---------------|--------|
| — | — | Sin incidentes registrados a la fecha | — | — | — |

---

## D. Historial de evaluaciones

| Período | Proveedor | Score | Decisión | Evaluador |
|---------|----------|-------|----------|-----------|
| — | — | Sin evaluaciones formales a la fecha | — | — |

Nota: primera evaluación formal programada para primer trimestre con evaluaciones activas (ref → PLB_REVISION_DIRECCION agenda punto proveedor).

---

## E. Notas por proveedor

### SUP-001 — Marluvas
- Contacto operativo: João
- Relación: importación directa, MWT como distribuidor autorizado
- Códigos SAP para pedidos
- Lead time típico: [PENDIENTE — documentar con data de expedientes]
- Certificaciones: [PENDIENTE — verificar certificaciones Marluvas]

### SUP-002 — Bangni
- Producto: plantillas biomecánicas con tecnología PORON (ref → ENT_COMP_ROGERS)
- Relación: OEM — Bangni fabrica, MWT es dueño de marca y specs
- Specs controladas por: ENT_PROD_{GOL,VEL,ORB,LEO,BIS} + SCH_FICHA_TECNICA
- Lead time típico: [PENDIENTE — documentar]
- Certificaciones: [PENDIENTE — verificar]
- Riesgo clave: si Bangni cambia formulación o proveedor de PORON sin avisar, specs de producto se invalidan

### SUP-003 — OEM Scanner
- Status: en proceso de selección
- Gate obligatorio: AC-02 (ref → ENT_PROD_SCANNER) — ingeniero MWT lee frames crudos en Python en < 4 horas
- Criterios adicionales: protocolo abierto (SDK documentado), capacitivo preferido, 1681 sensores mínimo
- No se compra hardware sin pasar gate

### SUP-004 — Hostinger
- Servicio: KVM 8 (8 vCPU, 32 GB RAM, 400 GB NVMe)
- SLA: [PENDIENTE — documentar SLA contratado]
- Backups: weekly automáticos (ref → ENT_PLAT_INFRA)
- Riesgo clave: proveedor único de infraestructura. Si Hostinger cae, todo cae.

---

Stamp: DRAFT — Pendiente aprobación CEO
