# ENT_DIST_DISTRIBUIDORES — Modelo de Distribución B2B
status: DRAFT — Pendiente validación CEO
visibility: [ALL] excepto pricing/márgenes [CEO-ONLY]
domain: Distribución (IDX_DISTRIBUCION)
version: 1.0

---

## A — Propuesta de Valor

Rana Walk no ofrece accesorios de consumo masivo. Ofrece una arquitectura de valor para distribuidores que exigen soluciones consistentes, escalables y con respaldo científico del Costa Rica MedTech Hub.

Diferenciador: tecnologías propietarias (LeapCore, ThinBoom, ShockSphere, NanoSpread, Arch System) + licenciada (PORON XRD) que no compiten con el mercado genérico de gel o espuma. Ref → ENT_TECH.

---

## B — Pilares de la Alianza

### B1. Portafolio de alta diferenciación
- Productos con memoria geométrica y soporte real para usuarios de hasta 110 kg
- 5 líneas con posicionamiento distinto (ref → ENT_PROD_COMPARATIVA)
- Tecnología licenciada PORON XRD exclusiva en el rango de precio

### B2. Transferencia de conocimiento
- Capacitación técnica en biomecánica podal y ergonomía para equipos de ventas
- Material de formación derivado de fichas técnicas (ref → SCH_FICHA_TECNICA)

### B3. Herramientas de venta inteligente
- Consultor IA para prescripción precisa de sistemas en punto de venta
- Reduce margen de error y aumenta satisfacción del cliente final

### B4. Gestión de salud ocupacional
- Soluciones para mejorar postura y neutralizar dolor articular en entornos industriales
- Posiciona al distribuidor como proveedor clave para seguridad laboral

---

## C — Sectores Objetivo

| # | Sector | Productos principales | Argumento clave |
|---|--------|----------------------|-----------------|
| 1 | Seguridad industrial y salud ocupacional | Goliath, Bison | Protección articular +8h, soporte 110kg |
| 2 | Artículos deportivos de alto rendimiento | Leopard, Velox, Bison | Personalización arco, retorno energía |
| 3 | Sector médico / ortopédico | Orbis, Goliath | Upgrade plantilla fábrica, alineamiento postural |
| 4 | Retail especializado | Todas las líneas | Portafolio completo, diferenciación vs genérico |

---

## D — Dossier Comercial (entregables al distribuidor)

| # | Entregable | Fuente |
|---|-----------|--------|
| 1 | Certificaciones de resiliencia: pruebas fatiga +8h, soporte carga 110kg | ENT_TECH, ENT_PROD_{X}.C1 |
| 2 | Especificaciones de materiales: PU bi-densidad (LeapCore), E-TPU (ThinBoom) | ENT_TECH |
| 3 | Ficha de origen: fabricación y validación MedTech Hub | ENT_MARCA_ORIGEN, ENT_MARCA_EEAT |
| 4 | Comparativa de mercado: Rana Walk vs plantillas genéricas gel/espuma | ENT_PROD_COMPARATIVA, ENT_MKT_COMPETENCIA |
| 5 | Guía implementación B2B: Consultor IA punto de venta + capacitación equipo ventas | [PENDIENTE — NO INVENTAR] |

Regla: dossier NUNCA incluye datos [CEO-ONLY] ni [INTERNAL]. Ref → POL_VISIBILIDAD, SCH_BRIEF_PROVEEDOR.

---

## E — Estructura de distribución

### E1. Niveles

| Nivel | Rol plataforma | Alcance |
|-------|---------------|---------|
| Distributor | ranawalk.com | Su inventario, órdenes, territorio asignado |
| SubDistributor | ranawalk.com | Su stock local, órdenes, sucursales |

Ref → ENT_PLAT_MODULOS M3 (roles), M10 (distribution/)

### E2. Territorios
[PENDIENTE — NO INVENTAR. Requiere decisión CEO: ¿exclusivos o abiertos? ¿por país, región, ciudad?]

### E3. Pricing para distribuidores
[PENDIENTE — NO INVENTAR] [CEO-ONLY]

### E4. Márgenes por nivel
[PENDIENTE — NO INVENTAR] [CEO-ONLY]

### E5. Reglas de exclusividad
[PENDIENTE — NO INVENTAR. Requiere decisión CEO.]

### E6. Contrato tipo
[PENDIENTE — NO INVENTAR]

---

## F — Flujo de captación

1. Formulario solicitud: nombre, correo corporativo, empresa, país/región, sector, mensaje
2. Sistema envía dossier comercial automático por email (sección D)
3. Director regional contacta en 48h
4. Evaluación de fit: sector, volumen, territorio
5. Propuesta comercial personalizada [CEO-ONLY]
6. Contrato y onboarding

---

## G — Secuencia de mercados

Ref → PLB_GROWTH: USA → CR → BR
- USA: Amazon FBA directo (canal actual, no distribuidor)
- CR: primer mercado distribución (Muito Work Limitada es entidad local)
- BR: segundo mercado distribución (requiere entidad local o representante — ref → ENT_MERCADO_BR)

---

## Z — Pendientes

| ID | Pendiente | Desbloquea | Quién decide |
|----|-----------|-----------|-------------|
| Z1 | Territorios: exclusivos o abiertos | E2 completo | CEO |
| Z2 | Pricing para distribuidores | E3 completo | CEO |
| Z3 | Márgenes por nivel | E4 completo | CEO |
| Z4 | Reglas exclusividad | E5 completo | CEO |
| Z5 | Contrato tipo | E6 completo | CEO + Legal |
| Z6 | Guía implementación Consultor IA en POS | D5 completo | CEO |
| Z7 | Primer mercado distribución: ¿CR confirmado? | G secuencia | CEO |

---

Stamp: DRAFT — Pendiente aprobación CEO
