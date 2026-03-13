# ENT_COMERCIAL_CANAL — Contribución por Canal y Pricing de Transferencia
id: ENT_COMERCIAL_CANAL
status: DRAFT
visibility: [CEO-ONLY]
domain: Comercial (IDX_COMERCIAL)
version: 1.0
stamp: DRAFT — pendiente aprobación CEO

---

## A. Concepto

Este documento define el modelo de análisis de contribución por canal de distribución y las reglas de pricing de transferencia como política del sistema. Es la capa de inteligencia comercial que permite al CEO — y eventualmente al Operador via M-PARTNER-AI — tomar decisiones de asignación de recursos basadas en el retorno real de cada canal.

### A1. Principio fundamental

El precio de transferencia es una **política**, no un precio de lista. Responde a los costos reales y varía con ellos en ambas direcciones (sube y baja simétricamente). El sistema recalcula automáticamente el punto de retorno por canal cuando cambian los parámetros de costo.

### A2. Fases de operación

```
FASE 1 — Sin datos reales (primeros 6-12 meses de operación)
  Sistema trabaja con parámetros configurados por CEO + proyecciones.
  Output: escenarios proyectados, no análisis real.
  Valor: permite al Operador simular decisiones de canal antes de tener historial.

FASE 2 — Con datos reales (6+ meses de órdenes en DB)
  Sistema recalcula automáticamente con datos históricos reales.
  Output: análisis real de contribución, forecast de reposición, alertas.
  Valor: inteligencia operativa genuina — ningún competidor tiene esto.
```

### A3. Relación con ENT_PLAT_CONTRATO_NODO

Los `channel_params` del NodeContract activo son la fuente de verdad para los parámetros de canal. `ENT_COMERCIAL_CANAL` define la lógica de cálculo — no duplica los parámetros.

```
NodeContract.channel_params → ENT_COMERCIAL_CANAL (lógica) → AUT-041 (cálculo) → Dashboard CEO
```

---

## B. Modelo de pricing de transferencia

### B1. Política de precio de transferencia

El precio que MWT cobra al Operador por producto Rana Walk es **costo FOB fábrica** — política irrevocable establecida en el NodeContract.

```
Precio_Transferencia = Costo_FOB_Fábrica
  (definido en NodeContract.transfer_price_policy)
```

Esta política es:
- Simétrica: si el costo FOB baja, el precio de transferencia baja. Si sube, sube.
- Ajustable: el trigger de ajuste y el mecanismo están definidos en el contrato.
- Inmutable por instancia: el precio de una orden ya registrada no se recalcula (ref → POL_INMUTABILIDAD).
- Transparente: el Operador conoce la política, no necesariamente el costo exacto.

### B2. Cascada de precios por nivel

```
Costo FOB Fábrica (China)
  ↓ [precio de transferencia MWT → Operador]
Precio entrada Operador
  ↓ [margen Operador para canal]
Precio canal (varía por canal)
  ↓ [comisión marketplace o descuento distribuidor]
Precio consumidor final
```

| Capa | Quién define | Visible para |
|------|-------------|-------------|
| Costo FOB Fábrica | Fábrica CN | CEO [CEO-ONLY] |
| Precio de transferencia | NodeContract (política) | CEO [CEO-ONLY] |
| Precio entrada Operador | = precio transferencia | CEO + Operador [CEO-ONLY] |
| Precio canal | Operador (dentro de restricciones contrato) | CEO + Operador |
| Precio consumidor final | Operador | Público |

---

## C. Canales de distribución — parámetros

Cada canal tiene un conjunto de parámetros que determinan su contribución marginal neta.

### C1. Estructura de parámetros por canal

```
Canal {
  canal_id: string                    # AMAZON_BR | RETAIL_FARMACIA | INDUSTRIAL_B2B | SCANNER_POS | SUBDIST | DIGITAL_DIRECT
  canal_name: string
  market: ref → ENT_MERCADO_{X}

  # Costos específicos del canal [CEO-ONLY]
  marketplace_commission_pct: decimal  # Solo marketplaces (Amazon BR: ~15%, Mercado Livre: ~12%)
  channel_discount_pct: decimal        # Descuento a sub-distribuidores o mayoristas
  operational_cost_per_unit: decimal   # Costo operativo específico (embalaje especial, etc.)
  scanner_cost_per_pos: decimal        # Costo de operar scanner en este POS (si aplica)

  # Métricas de performance (se llenan con datos reales — Fase 2)
  units_sold_last_90d: int             # Calculado
  revenue_last_90d: decimal            # Calculado
  contribution_margin_pct: decimal     # Calculado: (revenue - costos canal) / revenue
  mix_pct: decimal                     # % del total de ventas que viene de este canal
  attach_rate_scanner: decimal | null  # Solo canales con scanner activo
  avg_ticket: decimal                  # Calculado

  # Umbrales de alerta [CEO-ONLY]
  min_contribution_pct: decimal        # Alerta si contribución cae por debajo
  reorder_threshold_units: int         # Alerta de reposición cuando stock cae a N unidades
}
```

### C2. Canales conocidos — Brasil

| canal_id | Descripción | Fase disponible | Scanner aplica |
|----------|-------------|----------------|----------------|
| AMAZON_BR | Amazon.com.br FBA o FBM | Fase 1 roadmap | No |
| MERCADO_LIVRE | Mercado Livre Brasil | Fase 1 roadmap | No |
| RETAIL_FARMACIA | Cadenas de farmacia | Fase 1 | Sí (con scanner en POS) |
| RETAIL_CALZADO | Tiendas de calzado | Fase 1 | Sí (con scanner en POS) |
| INDUSTRIAL_B2B | Venta directa a empresas para seguridad laboral | Fase 1 | Sí (scanner en onboarding) |
| MEDICO_ORTOPEDICO | Canal médico y ortopédico | Fase 2 | Sí (central al canal) |
| SUBDIST_REGIONAL | Sub-distribuidores regionales | Fase 1 | Depende del sub |
| DIGITAL_DIRECT | ranawalk.com.br directo al consumidor | Fase 2 | No (digital) |

---

## D. Cálculo de contribución por canal

### D1. Fórmula de contribución marginal por canal

```
Contribución_Canal =
  Revenue_Canal
  - Precio_Transferencia × Unidades
  - Comisión_Marketplace (si aplica)
  - Descuento_Canal (si aplica)
  - Costo_Operativo_Canal × Unidades
  - Costo_Scanner_POS (si aplica, amortizado por unidades)

Contribución_Marginal_Pct = Contribución_Canal / Revenue_Canal × 100
```

### D2. Punto de retorno por canal

El punto de retorno es el volumen mínimo de unidades necesario para que un canal cubra sus costos específicos y empiece a contribuir positivamente.

```
Punto_Retorno_Canal =
  Costo_Fijo_Canal (setup, scanner, material POS)
  / Contribución_Por_Unidad_Canal
```

Cuando el sistema tiene datos reales (Fase 2), calcula automáticamente cuántos meses faltan para que cada canal nuevo alcance su punto de retorno.

### D3. Mix de distribución

```
Mix_Canal_Pct = Unidades_Canal / Total_Unidades_Período × 100

Contribución_Mix_Ponderada =
  Σ (Mix_Canal_Pct × Contribución_Marginal_Pct_Canal)
  para cada canal activo
```

Esta métrica le dice al CEO y al Operador qué canal está aportando más al negocio ponderado por su peso relativo en las ventas.

---

## E. Impacto del scanner en la contribución por canal

El scanner modifica el modelo de contribución de cualquier canal donde está presente.

```
Sin scanner:
  Revenue_Canal = Unidades × Precio_Palmilha

Con scanner (attach rate A%):
  Revenue_Canal = Unidades × Precio_Palmilha
                + (Unidades × A%) × Precio_Scanner_Sesion
  
  Donde A% = attach rate del canal específico
  Benchmark: 5% (inicial) → 25%+ (canal maduro con operador entrenado)
```

El sistema trackea el attach rate por canal y lo incluye en el cálculo de contribución. Un canal con scanner activo y attach rate creciente tiene un perfil de retorno completamente diferente al mismo canal sin scanner.

---

## F. Automatizaciones de este dominio

Ref → ENT_PLAT_AUTOMATIONS + ENT_PLAT_CONTRATO_NODO.F para specs completas.

| Automatización | Engine | Trigger | Output |
|---------------|--------|---------|--------|
| AUT-041 | Windmill | Semanal | Tabla contribución por canal actualizada |
| AUT-042 | Windmill | Mensual | Forecast reposición por SKU por canal |
| AUT-043 | n8n | Evento: contribución < umbral | Alerta CEO + Operador con análisis |
| AUT-044 | Windmill | Trimestral | Reporte completo para MWT (sin intervención Operador) |

---

## G. Inteligencia disponible vía M-PARTNER-AI

Cuando el AI middleware tiene acceso a la tabla de contribución por canal, el Operador puede consultar al sistema:

| Consulta tipo | Ejemplo | Fase |
|--------------|---------|------|
| Comparativa de canales | "¿Qué canal me conviene escalar este trimestre?" | Fase 2 |
| Simulación de canal nuevo | "¿Cuándo recupero la inversión si abro 10 POS con scanner?" | Fase 1+ |
| Alerta de deterioro | "Este canal bajó de su umbral, ¿qué está pasando?" | Fase 2 |
| Forecast de reposición | "¿Cuánto debo pedir a MWT el próximo mes?" | Fase 2 |
| Impacto de precio | "Si Amazon BR sube sus comisiones, ¿cómo afecta mi mix?" | Fase 1+ |

Regla de visibilidad: M-PARTNER-AI expone la contribución del canal en términos relativos (mejor/peor canal) pero NUNCA expone costos de transferencia ni márgenes de MWT. Ref → POL_VISIBILIDAD.

---

## H. Vista CEO vs vista Operador

| Métrica | CEO (mwt.one) | Operador (portal.mwt.one) |
|---------|--------------|--------------------------|
| Precio de transferencia exacto | ✅ | ❌ |
| Costo FOB fábrica | ✅ | ❌ |
| Margen de MWT | ✅ | ❌ |
| Contribución marginal por canal | ✅ completa | ✅ su propia operación |
| Mix de distribución | ✅ global | ✅ su propia operación |
| Punto de retorno por canal | ✅ | ✅ |
| Forecast de reposición | ✅ | ✅ |
| Attach rate scanner | ✅ | ✅ |
| Alertas de canal bajo umbral | ✅ todas | ✅ las suyas |
| Comparativa entre Operadores | ✅ | ❌ |

---

## Z. Pendientes

| ID | Pendiente | Desbloquea | Quién decide |
|----|-----------|-----------|-------------|
| Z1 | Parámetros reales canal_params para BR | AUT-041 operativo Fase 1 | CEO [CEO-ONLY] |
| Z2 | Umbrales de alerta por canal BR | AUT-043 operativo | CEO [CEO-ONLY] |
| Z3 | Comisiones exactas Amazon BR y Mercado Livre | AMAZON_BR y MERCADO_LIVRE params | CEO (verificar con plataformas) |
| Z4 | Costo operativo scanner por POS BR | attach rate model BR | CEO + Operador BR |
| Z5 | ¿Operador BR puede ver contribución de otros Operadores en otros mercados? | Visibilidad comparativa | CEO |
| Z6 | Modelo de amortización scanner en cálculo de contribución | D1 fórmula completa | Architect + CEO |

---

Stamp: DRAFT — pendiente aprobación CEO
Origen: Sesión de diseño arquitectura contratos inteligentes y canales — 2026-03-09
