# ENT_GOB_SSO — Seguridad y Salud Ocupacional
id: ENT_GOB_SSO
version: 1.0
domain: Gobernanza (IDX_GOBERNANZA)
status: DRAFT
visibility: [INTERNAL]
stamp: DRAFT — pendiente aprobación CEO
iso: 45001:2018 §4-10

---

## A. Alcance

Operación de MWT: equipo remoto (administración, desarrollo, gestión comercial), recepción de mercancía importada en CR, visitas a instalaciones de clientes/distribuidores, y uso del scanner de presión plantar en punto de venta.

---

## B. Partes interesadas SSO

| Parte | Relación con SSO |
|-------|-----------------|
| Equipo MWT (remoto) | Riesgos ergonómicos, jornada |
| Personal en recepción mercancía | Manipulación de cajas |
| CEO en visitas a plantas/distribuidores | Exposición a entorno industrial |
| Vendedores distribuidores (usando scanner) | Uso seguro del hardware en punto de venta |
| Clientes finales (escaneados) | Seguridad durante escaneo de pie |

---

## C. Evaluación de riesgos laborales

Detalle completo con scores en ENT_GOB_RIESGOS §D. Resumen:

| Riesgo | Score | Mitigación |
|--------|-------|-----------|
| Ergonomía trabajo remoto | 6 MEDIO | Guía de postura, pausas activas recomendadas, monitor a altura de ojos |
| Manipulación cajas importación | 4 BAJO | Peso moderado por caja, técnica de levantamiento, guantes si cajas dañadas |
| Visitas a plantas industriales | 6 MEDIO | Usar EPP proporcionado por el cliente, no entrar a zonas restringidas sin guía |
| Tropiezo con scanner/cable en tienda | 2 BAJO | Diseño antideslizante, cable ≥1.5m, protocolo de colocación en PLB_SCANNER_DISTRIB |

---

## D. Objetivos SSO

| Objetivo | Indicador | Meta | Frecuencia medición |
|---------|----------|------|-------------------|
| Cero incidentes laborales | Count(incidentes) | 0 | Trimestral |
| Equipo remoto con setup ergonómico básico | % equipo con checklist ergonómico completado | 100% | Anual |
| Distribuidores capacitados en uso seguro del scanner | % distribuidores con onboarding completado (Fase 3 PLB_SCANNER_DISTRIB) | 100% | Por onboarding |

---

## E. Preparación para emergencias

| Escenario | Alcance MWT | Acción |
|-----------|------------|--------|
| Emergencia médica en oficina/remoto | Individual | Llamar servicios de emergencia locales. MWT no tiene planta física con personal simultáneo. |
| Lesión en recepción de mercancía | Puntual | Botiquín básico. Si requiere atención médica → servicios locales + registrar incidente. |
| Emergencia en planta de cliente durante visita | Del cliente | Seguir protocolo de evacuación del cliente. No actuar independientemente. |
| Incidente con scanner en punto de venta | Del distribuidor | Desconectar equipo, registrar incidente, notificar a MWT. |

---

## F. Registro de incidentes SSO

Formato por incidente:

```
INCIDENTE SSO — [YYYY]-[NNN]
Fecha: YYYY-MM-DD
Lugar: [oficina/bodega/planta cliente/punto de venta]
Persona afectada: [nombre/rol]
Descripción: [qué pasó]
Severidad: [sin lesión / lesión menor / lesión mayor / fatalidad]
Causa: [análisis breve]
Acción tomada: [primeros auxilios, atención médica, etc.]
Acción preventiva: [qué cambió para evitar recurrencia]
Ref NC: [NC-YYYY-NNN si se abrió no conformidad]
```

A la fecha: cero incidentes registrados.

---

## G. Consulta con trabajadores

ISO 45001 requiere evidencia de consulta con el equipo en temas SSO. Para MWT (empresa pequeña, equipo remoto), esto se cubre con: discusión de riesgos SSO en revisión por la dirección trimestral, y canal abierto para reportar preocupaciones (mensaje directo al CEO). No se requiere comité SSO formal dada la escala.

---

Stamp: DRAFT — Pendiente aprobación CEO
