# SCH_ISO_AUDIT_PACK — Paquete de Evidencia ISO
id: SCH_ISO_AUDIT_PACK
version: 1.0
domain: Compliance (IDX_COMPLIANCE)
status: DRAFT
stamp: DRAFT — pendiente aprobación CEO
iso: 9001:2015, 45001:2018, 27001:2022

---

## Propósito

Schema de ensamblaje que genera el paquete de evidencia presentable a un auditor ISO externo. Extrae datos de entities, policies, playbooks y registros operativos existentes y los presenta en formato consolidado.

Un auditor no navega el knowledge base. Este schema produce un documento legible que demuestra cumplimiento.

---

## Requires

| Entity/Policy/Playbook | Qué aporta |
|------------------------|-----------|
| POL_CALIDAD | Política de calidad firmada |
| POL_SSO | Política SSO firmada |
| POL_DATA_CLASSIFICATION | Clasificación de datos |
| POL_SEGURIDAD_INFO | Política de seguridad de información (cuando exista) |
| ENT_GOB_RIESGOS | Registro de riesgos con evaluación y controles |
| ENT_GOB_KPI | Indicadores de desempeño con tendencias |
| ENT_PLAT_SEGURIDAD | Roles y control de acceso |
| ENT_PLAT_INFRA | Infraestructura documentada |
| ENT_OPS_EXPEDIENTE | Procesos operativos documentados |
| PLB_REVISION_DIRECCION | Actas de revisión por la dirección |
| PLB_ACCION_CORRECTIVA | Registro de no conformidades y acciones |
| PLB_AUDIT_ISO | Reportes de auditoría interna |
| POL_ARCHIVO | Gestión documental y retención |
| POL_DETERMINISMO | Principios de dato único |
| POL_STAMP | Control de vigencia |

---

## Policies

POL_VISIBILIDAD — el pack nunca incluye datos [CEO-ONLY] ni datos N2+.
POL_NUNCA_TRADUCIR — tech names y labels se mantienen en idioma original.

---

## Estructura del output

### Sección 1 — Contexto de la organización
- Nombre legal: Muito Work Limitada
- Líneas de negocio: 3 (ref → ENT_PLAT_MODULOS resumen)
- Mercados: USA (activo), CR (construcción), BR (construcción)
- Alcance SGC/SGSI/SSO: según declaración en cada política
- Mapa de procesos: diagrama de los 12 módulos y sus interacciones

### Sección 2 — Políticas firmadas
- POL_CALIDAD (texto completo + firma CEO + fecha)
- POL_SSO (texto completo + firma CEO + fecha)
- POL_SEGURIDAD_INFO (cuando exista)
- POL_DATA_CLASSIFICATION (resumen niveles)

### Sección 3 — Registro de riesgos
- Tabla completa de ENT_GOB_RIESGOS con scores, controles y acciones
- Destacar: riesgos altos/críticos y sus mitigaciones

### Sección 4 — Objetivos e indicadores
- Tabla de ENT_GOB_KPI con valores actuales, tendencias y semáforos
- Gráfico de tendencia de los últimos 4 trimestres (cuando haya data)

### Sección 5 — Control documental
- Descripción del sistema: taxonomía ENT/SCH/POL/PLB/LOC/IDX
- Ciclo de vida: POL_ARCHIVO (captura → retención → archivo → purga)
- Versionado: POL_STAMP (VIGENTE/DRAFT/DEPRECATED)
- Principio de dato único: POL_DETERMINISMO
- Inventario de documentos controlados: conteo por tipo y dominio

### Sección 6 — Procesos operativos
- Flujo de expedientes: 8 estados, transiciones, condiciones (de ENT_OPS_EXPEDIENTE)
- Artefactos controlados: ARTIFACT_REGISTRY resumen
- Event sourcing: descripción del log append-only

### Sección 7 — Auditorías internas
- Programa anual (de PLB_AUDIT_ISO §B)
- Reportes de las últimas 4 auditorías (o las disponibles)
- Resumen: hallazgos por tipo, tendencia

### Sección 8 — No conformidades y acciones correctivas
- Resumen de PLB_ACCION_CORRECTIVA: abiertas, cerradas, vencidas
- Métricas: tiempo promedio de resolución, % eficacia al primer intento
- Top 3 NC más significativas y cómo se resolvieron

### Sección 9 — Revisiones por la dirección
- Últimas 4 actas de PLB_REVISION_DIRECCION (o las disponibles)
- Resumen de decisiones tomadas y su seguimiento

### Sección 10 — Seguridad de la información (si ISO 27001 en alcance)
- Alcance SGSI (de ENT_COMP_SGSI cuando exista)
- Arquitectura de seguridad: roles, cifrado, backups, multi-tenancy
- Gestión de incidentes: resumen de PLB_INCIDENT_RESPONSE
- Statement of Applicability: controles del Anexo A aplicables vs no aplicables

### Sección 11 — SSO (si ISO 45001 en alcance)
- Evaluación de riesgos laborales (de ENT_GOB_SSO)
- Registro de incidentes SSO
- KPIs SSO

---

## Formato de generación

Output: PDF (ref → POL_PRINT) o markdown consolidado.
Generación: manual (CEO ensambla) o automática (sistema extrae de DB + knowledge base).
Frecuencia: antes de cada auditoría externa, o bajo demanda.

---

## Excludes

- Datos [CEO-ONLY]: pricing, costos, márgenes
- Datos N3 [DISTRIBUTOR-SCOPED]: catálogos y escaneos de distribuidores
- Datos N4 [BIOMETRIC]: escaneos individuales
- Código fuente o configuración técnica detallada

---

Stamp: DRAFT — Pendiente aprobación CEO
