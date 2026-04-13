# DIRECTRIZ CEO — Plan Secuencial S28→S32
id: DIRECTRIZ_CEO_PLAN_SECUENCIAL
version: 1.0
status: DRAFT
visibility: [INTERNAL]
domain: Gobernanza
fecha: 2026-04-10
de: CEO (Álvaro)
para: AG-02 (Alejandro)

---

## Contexto

Llevamos 26 sprints construyendo módulos. El resultado: muchos módulos al ~65%, ninguno al 100% operable. A partir de S28 cambiamos el enfoque: **diseñamos por journey de usuario, no por feature técnica.**

La lógica es simple:

```
CEO opera solo
  → Cliente opera solo
    → Roles secundarios operan solos
      → El sistema opera solo
```

Cada sprint desbloquea el siguiente. No tiene sentido que el cliente tenga portal si el CEO todavía navega a mano. No tiene sentido automatizar notificaciones si el flujo de proforma no está cerrado desde UI.

---

## Estado actual (pre-plan)

| Sprint | Status | Qué hizo |
|--------|--------|----------|
| S0–S24 | DONE | Infraestructura, modelos, seguridad B2B, knowledge pipeline |
| S25 | DONE | Payment status machine + precio diferido + parent/child (59 tests) |
| S26 | SPEC LISTA | Notificaciones email + cobranza + admin templates. Bloqueado en CEO-28 (email provider). |
| S27 | EN PREPARACIÓN | Seguridad residual: secrets audit, backup encriptado, Cloudflare + Docker hardening |

**S26 y S27 se ejecutan como están.** Este plan define S28→S32.

---

## Paso 0 — Limpieza (sin sprint, antes de S28)

Tiempo estimado: 1 hora. Alejandro lo puede hacer mientras planifica S28.

- [ ] Templates basura en la DB → eliminar
- [ ] Duplicados de brands → consolidar
- [ ] Encoding issues conocidos → fix
- [ ] Verificar que `makemigrations --check` no tenga pendientes

---

## S28 — CEO Dashboard Real

**Objetivo:** El CEO entra y sabe exactamente qué hacer hoy, sin navegar.

**Por qué primero:** Todo lo demás depende de que el CEO pueda operar. Si el CEO sigue navegando a mano, no importa lo que venga después.

### Lo que debe mostrar

1. **Expedientes que necesitan acción hoy** — no todos, solo los que requieren algo del CEO
2. **Proformas pendientes de enviar** — con un indicador claro de urgencia
3. **Cobros que vencen esta semana** — integrado con payment status (S25) y cobranza (S26)
4. **Pipeline visual** — cliente/marca visible en cada card, no solo un número

### Criterio de éxito

El CEO abre la consola una vez al día y sabe qué hacer sin hacer click en nada más. Si tiene que navegar para entender el estado de las cosas, el dashboard falló.

### Dependencias

- S25 DONE (payment status) ✅
- S26 DONE (cobranza — para mostrar cobros vencidos)
- S27 DONE (seguridad — para abrir B2B con confianza)

### Decisiones pendientes CEO

| ID | Decisión | Default |
|----|----------|---------|
| DEC-S28-01 | ¿Qué cuenta como "necesita acción"? Definir las reglas exactas de filtrado. | Expediente sin movimiento >3 días + proformas sin enviar + cobros vencidos |
| DEC-S28-02 | ¿Dashboard reemplaza la vista actual de expedientes o es una pantalla nueva? | Pantalla nueva, landing page post-login |

---

## S29 — Proforma Flow Completo desde UI

**Objetivo:** El CEO crea y envía una proforma sin salir de la consola.

**Por qué segundo:** Es la operación diaria más costosa en tiempo. Hoy se hace manualmente todos los días. Automatizar esto libera horas reales inmediatamente.

### Lo que debe poder hacer desde UI

1. **Crear proforma** (ART-02) para un expediente
2. **Configurar modo** — mode_b / mode_c para Marluvas, default para Rana Walk
3. **Enviarla al cliente** con un botón — integrado con email backend (S26)
4. **Ver si el cliente aprobó o rechazó** — status visible en el expediente

### Criterio de éxito

El CEO genera una proforma para Sondel S.A. desde cero, la envía por email, y ve cuando Sondel la aprueba — todo sin salir de mwt.one.

### Dependencias

- S26 DONE (email backend para envío)
- S28 DONE (dashboard muestra proformas pendientes)
- `resolve_client_price()` operativo (S22 DONE)
- `PF_0000-2026_GOLDEN_EXAMPLE.html` como referencia de formato

### Decisiones pendientes CEO

| ID | Decisión | Default |
|----|----------|---------|
| DEC-S29-01 | ¿Aprobación del cliente es por email reply, por link, o por portal? | Link con token (portal aún no existe) |
| DEC-S29-02 | ¿Proforma se genera como PDF o HTML? | HTML renderizado a PDF para envío |

---

## S30 — Cliente Self-Serve Real

**Objetivo:** El cliente entra al portal y ve todo sin preguntarle al CEO.

**Por qué tercero:** Una vez que el CEO puede operar, el siguiente dolor es que igual tiene que comunicarse con cada cliente para darle updates. Esto lo elimina.

### Lo que debe ver el cliente

1. **Órdenes activas** y en qué estado están — con la máquina de estados real (ENT_OPS_STATE_MACHINE)
2. **Documentos** — proformas, facturas — via signed URLs (S24)
3. **Histórico completo** — todas las órdenes cerradas
4. **Crédito disponible y cobros pendientes** — integrado con payment status (S25)

### Criterio de éxito

Allan Ramírez (Sondel) entra al portal, ve sus 3 expedientes activos, descarga la proforma del último, y verifica que su pago de la semana pasada ya se acreditó. Sin llamar al CEO.

### Dependencias

- S24 DONE (signed URLs, JWT, rate limiting) ✅
- S25 DONE (payment status) ✅
- S29 DONE (proformas generadas en el sistema)
- Role-based sidebar activada (S21B-06 — verificar estado)

### Decisiones pendientes CEO

| ID | Decisión | Default |
|----|----------|---------|
| DEC-S30-01 | ¿El cliente puede descargar facturas o solo proformas? | Solo proformas MVP. Facturas en v2. |
| DEC-S30-02 | ¿Onboarding del cliente: invitación por email o registro abierto? | Invitación por email (CEO controla acceso) |

---

## S31 — Vendedor y Pricing Self-Serve

**Objetivo:** Cada rol ve exactamente lo que necesita, nada más.

**Por qué cuarto:** Son usuarios de consulta, no de operación diaria. Importantes pero no urgentes.

### Vendedor

- Catálogo navegable con fichas técnicas reales por producto
- Precios de lista visibles (sin precios CEO-ONLY)
- Disponibilidad por modelo/talla (si inventario está conectado)

### Pricing

- Assignments al día (sin precios stale)
- Historial de cambios de precio por cliente/SKU
- Alertas cuando un precio lleva >90 días sin revisión

### Criterio de éxito

Un vendedor nuevo busca "PP-50B22" (Marluvas Vulcaflex), ve la ficha técnica, el precio de lista, y las tallas disponibles — sin pedirle información al CEO.

### Dependencias

- S22 DONE (pricing engine, pricelists, CPA) ✅
- S30 DONE (portal cliente como base de portal vendedor)
- Fichas técnicas cargadas (ENT_MARCA_FICHA_TECNICA — verificar estado)

---

## S32 — Automatización Completa

**Objetivo:** El sistema opera sin intervención manual.

**Por qué último:** Solo tiene sentido automatizar lo que ya funciona bien operativamente. Si automatizás un flujo roto, automatizás el error.

### Componentes

1. **Notificaciones automáticas** en cada cambio de estado del expediente — hooks ya existen (S18), templates ya existen (S26), falta conectar
2. **Cobranza automática por cron** — cron definido en S26, falta activar en producción
3. **CPA auto-recalculate** cuando el precio cambia — evento pricing → recalcular cached_base_price
4. **Dashboard CEO se actualiza en tiempo real** — websocket o polling con el activity feed (S21)

### Criterio de éxito

Un expediente pasa de "producción" a "despacho" y automáticamente: (1) el cliente recibe email, (2) el dashboard del CEO actualiza el pipeline, (3) el activity feed registra el evento. Sin que nadie toque nada.

### Dependencias

- S26–S31 todos DONE
- Celery Beat operativo ✅
- Email provider configurado (CEO-28)

---

## Resumen de secuencia

| Sprint | Nombre | Desbloquea | Duración est. |
|--------|--------|------------|---------------|
| S26 | Emails + Cobranza + Templates | S28 (cobros en dashboard) | 2 semanas |
| S27 | Seguridad residual | S28 (abrir B2B con confianza) | 1.5 semanas |
| S28 | CEO Dashboard Real | S29 (CEO puede ver qué falta) | 1.5 semanas |
| S29 | Proforma Flow UI | S30 (proformas existen en el sistema) | 2 semanas |
| S30 | Cliente Self-Serve | S31 (portal base para vendedor) | 2 semanas |
| S31 | Vendedor + Pricing | S32 (todos los roles operan) | 1.5 semanas |
| S32 | Automatización | — (sistema autónomo) | 2 semanas |

**Total secuencial S26→S32:** ~12.5 semanas
**Con paralelización S26∥S27:** ~11 semanas

---

## Principio de diseño que cambia

Antes: Sprint = feature técnica (pricing engine, inventario, state machine).
Ahora: Sprint = un usuario puede hacer su trabajo completo sin ayuda.

Si un sprint no deja a un usuario operando solo, el sprint no está terminado.

---

## Para Alejandro

S28 y S29 son los que más valor generan para el CEO en menos tiempo. Si los hacés bien, el sistema ya se empieza a autogestionar desde S30 en adelante. Los módulos técnicos ya están — lo que falta es conectarlos en flujos que un humano pueda usar sin documentación.

Cada sprint tiene decisiones pendientes (DEC-S28 a DEC-S32). Si tenés una preferencia técnica diferente sobre alguna, proponé antes de empezar — no durante.

---

Changelog:
- v1.0 (2026-04-10): Compilación inicial. Directriz CEO basada en análisis de journey de usuario.
