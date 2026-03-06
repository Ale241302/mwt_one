# ASANA_TASK_SPRINT6 — Rana Walk Flujo Completo · i18n · QR Universal

> **Sprint 6** · Fuentes canónicas: `BRIEF_SPRINT6_ALEJANDRO.md` + `LOTE_SM_SPRINT6.md`  
> **Precondición:** Sprint 5 DONE — Transfer model C30-C35 funcional, ART-10 reconciliación operativa, 35 command endpoints POST.  
> **Total post-Sprint 6:** 35 (Sprint 1-5) + 4 POST nuevos = **39 command endpoints**.

---

## PILAR 1 — Rana Walk en plataforma

---

### [S6-Item1] Brand config Rana Walk en plataforma

| Campo | Valor |
|---|---|
| **Sprint** | Sprint 6 |
| **Item** | 1 |
| **Prioridad** | P0 |
| **Agente** | AG-02 API Builder |
| **Estado** | Pendiente |
| **Branch** | `feature/s6-brand-rana-walk` |
| **Dependencia** | Sprint 5 DONE |

**Descripción:**  
Registrar Rana Walk como marca operativa en la plataforma. Configurar `brand=rana_walk`, `brand_type=own`, ejecutar el flujo completo de artefactos para CR (nacionalización IVA) y USA (directo FBA/DTC), y activar los artefactos de transfer que en Sprint 5 quedaron como reglas puente manuales.

**Criterios de Éxito:**
- `brand=rana_walk`, `brand_type=own` registrado en el sistema
- Flujo de artefactos RW: ART-01, ART-02, ART-05, ART-06, ART-09, ART-11 (ref `ENT_PLAT_ARTEFACTOS.C4`)
- **NO usa** ART-03, ART-04, ART-10 — no aplican a marca propia
- Bifurcación CR (nacionalización IVA) vs USA (directo FBA/DTC) como variante del expediente
- 54 SKUs Rana Walk importables:

| Producto | Arcos | Tallas | SKUs | Nomenclatura |
|---|---|---|---|---|
| Goliath | MED | S1-S6 | 6 | `RW-GOL-MED-S1..S6` |
| Velox | MED | S1-S6 | 6 | `RW-VEL-MED-S1..S6` |
| Orbis | MED | S1-S6 | 6 | `RW-ORB-MED-S1..S6` |
| Leopard | LOW/MED/HGH | S1-S6 | 18 | `RW-LEO-{arco}-S1..S6` |
| Bison | LOW/MED/HGH | S1-S6 | 18 | `RW-BIS-{arco}-S1..S6` |
| **Total** | | | **54** | |

**Riesgos:**
- La bifurcación CR/USA requiere que la state machine soporte variantes del expediente por destino de despacho.
- Los 54 SKUs deben cargarse con los `product_key`, `product_slug` y `display_name` exactos definidos en el contrato de naming (ver sección de convenciones).

---

### [S6-Item2] Artefactos Transfer ART-13, ART-14, ART-15

| Campo | Valor |
|---|---|
| **Sprint** | Sprint 6 |
| **Item** | 2 |
| **Prioridad** | P0 |
| **Agente** | AG-02 API Builder |
| **Estado** | Pendiente |
| **Branch** | `feature/s6-art-13-14-15` |
| **Dependencia** | Sprint 5 — Transfer model funcional (C30-C35) |

**Descripción:**  
Implementar los tres artefactos de transfer que en Sprint 5 se sustituyeron por reglas puente manuales. Reemplazan las confirmaciones manuales del CEO.

**Criterios de Éxito:**
- **ART-13 Recepción en nodo** — `ArtifactInstance type=ART-13`, payload: `lines[{sku, quantity_received, condition}]`, `received_by`, `received_at`, `notes`. `condition` enum: `good | damaged | partial`. Command **C36 CompleteReception** `POST /api/transfers/{id}/complete-reception`.
- **ART-14 Preparación/Acondicionamiento** — `ArtifactInstance type=ART-14`, payload: `actions[{action_type, description, quantity_affected}]`, `prepared_by`, `prepared_at`, `notes`. `action_type` enum: `packaging | labeling | stickering | quality_check | other`. Command **C37 CompletePreparation** `POST /api/transfers/{id}/complete-preparation`.
- **ART-15 Despacho inter-nodo** — `ArtifactInstance type=ART-15`, payload: `carrier`, `tracking_number`, `dispatch_date`, `destination_node`, `notes`. Command **C38 CompleteDispatch** `POST /api/transfers/{id}/complete-dispatch`.
- Integración con Transfer state machine: `in_transit` requiere ART-15 completado; `received` requiere ART-13 completado.

**Riesgos:**
- Enhancements P2 (fotos recepción, firma digital, checklist configurable, sub-tramos, ETA) están bloqueados hasta sesión de diseño — **no incluir en Sprint 6**.

---

### [S6-Item3] ART-16 Transfer pricing approval (C39)

| Campo | Valor |
|---|---|
| **Sprint** | Sprint 6 |
| **Item** | 3 |
| **Prioridad** | P1 |
| **Agente** | AG-02 API Builder |
| **Estado** | Pendiente |
| **Branch** | `feature/s6-art-16` |
| **Dependencia** | Item 2 aprobado |

**Descripción:**  
Artefacto de aprobación de precios de transfer para operaciones con cambio de titularidad. CEO-ONLY. Bloquea la reconciliación del transfer si `ownership_change=true` y ART-16 no está aprobado.

**Criterios de Éxito:**
- `ArtifactInstance type=ART-16`, payload: `transfer_price`, `currency`, `justification`, `approved_by`, `approved_at`
- Solo se crea cuando `Transfer.ownership_changes=true`
- **CEO-ONLY** — solo el CEO puede crear/aprobar
- Command **C39 ApproveTransferPricing** `POST /api/transfers/{id}/approve-pricing`
- Transfer no puede pasar a `reconciled` sin ART-16 aprobado si `ownership_changes=true`

**Riesgos:**
- Enhancements P2 (arms-length validation, documentación soporte para auditoría fiscal) pendientes de contexto jurisdiccional — no incluir en Sprint 6.

---

## PILAR 2 — ranawalk.com multi-idioma

---

### [S6-Item4] ranawalk.com i18n routing (en/es/pt)

| Campo | Valor |
|---|---|
| **Sprint** | Sprint 6 |
| **Item** | 4 |
| **Prioridad** | P0 |
| **Agente** | AG-03 Frontend |
| **Estado** | Pendiente |
| **Branch** | `feature/s6-i18n-routing` |
| **Dependencia** | Proyecto ranawalk.com existente |

**Descripción:**  
Configurar el sitio público ranawalk.com para funcionar en 3 idiomas (EN, ES, PT) con routing por prefijo de idioma, detección automática y hreflang.

**Criterios de Éxito:**
- `next-intl` (o equivalente) configurado con 3 locales: `en`, `es`, `pt`
- URLs `/lang/path` funcionales (ej. `/en/goliath`, `/es/goliath`, `/pt/goliath`)
- Middleware en root de `ranawalk.com`: detecta `Accept-Language` → 302 al `/lang` correspondiente (cascada: ref `ENT_PLAT_I18N.C4`)
- `link rel=alternate hreflang` para `en`, `es`, `pt` + `x-default=en` en el layout
- Toggle de idioma visible en el header del sitio

**Riesgos:**
- SEO: los hreflang deben estar presentes antes del lanzamiento de las páginas de producto para evitar penalizaciones.

---

### [S6-Item5] 5 páginas producto "Inside Your Product" (EN/ES/PT)

| Campo | Valor |
|---|---|
| **Sprint** | Sprint 6 |
| **Item** | 5 |
| **Prioridad** | P1 |
| **Agente** | AG-03 Frontend + Copy |
| **Estado** | Pendiente |
| **Branch** | `feature/s6-product-pages` |
| **Dependencia** | Item 4, Item 9 (LOC_TECH) |

**Descripción:**  
Crear las 15 páginas de producto (5 productos × 3 idiomas) con el componente reutilizable `InsideProduct`. Mobile-first, scroll vertical.

**Criterios de Éxito:**
- Componente `InsideProduct` que recibe: `techs`, `ratings`, `seal` (string | null), `arch_profiles` (array | null)
- **POL_NUNCA_TRADUCIR**: nombres de tecnología (LeapCore, Arch System, PORON XRD, ThinBoom, NanoSpread) y sello "American Technology Inside" son invariables en los 3 idiomas

| Ruta | Producto | Techs | Sello | Arcos | Color primario | Color accent |
|---|---|---|---|---|---|---|
| `/en/goliath` | Goliath | 5 | American Technology Inside | MED | `#013A57` (Navy) | `#A8D8EA` (Ice) |
| `/en/velox` | Velox | 2 | — | MED | `#7B2DBF` (Violet) | `#E040FB` (Magenta) |
| `/en/orbis` | Orbis | 2 | — | MED | `#FFFFFF` (White) | `#EF4E54` (Coral) |
| `/en/leopard` | Leopard | 3 | — | LOW/MED/HGH | `#5C3A1E` (Earth) | `#B87333` (Copper) |
| `/en/bison` | Bison | 3 | American Technology Inside | LOW/MED/HGH | `#2C2C2C` (Carbon) | `#FF8C00` (Amber) |

- 5 páginas EN + 5 ES + 5 PT = **15 páginas total**
- Los hexadecimales son los valores actuales de los tokens `ENTPROD_X.E1` (dominante) y `E2` (accent)

**Riesgos:**
- Item 5 está bloqueado hasta que Item 4 (i18n routing) y Item 9 (LOC_TECH contenido) estén aprobados.

---

## PILAR 3 — QR Universal

---

### [S6-Item6] App Django `qr/` — QRRoute + QRScan + resolver + consola CEO

| Campo | Valor |
|---|---|
| **Sprint** | Sprint 6 |
| **Item** | 6 |
| **Prioridad** | P0 |
| **Agente** | AG-01 Architect + AG-02 API Builder + AG-03 Frontend |
| **Estado** | Pendiente |
| **Branch** | `feature/s6-qr-app` |
| **Dependencia** | Ninguna |

**Descripción:**  
App Django `qr/` con modelos `QRRoute` y `QRScan`, endpoint público de resolución con detección de idioma, y consola CEO en mwt.one para administrar destinos sin redeploy.

**Criterios de Éxito:**

**Modelos:**
```python
QRRoute: slug (product_key, ej. "gol"), product_slug ("goliath"), product_name ("Goliath"),
         destination_template ("https://ranawalk.com/{lang}/goliath"),
         override_url (nullable), override_reason, is_active, fallback_url
QRScan:  route (FK), detected_lang, country_code, user_agent,
         ip_hash (SHA256(ip+SALT) truncado 16 bytes / 32 hex chars), scanned_at
```

**Seed inicial — 5 routes:**

| slug | product_slug | product_name | destination_template |
|---|---|---|---|
| `gol` | `goliath` | Goliath | `https://ranawalk.com/{lang}/goliath` |
| `vel` | `velox` | Velox | `https://ranawalk.com/{lang}/velox` |
| `orb` | `orbis` | Orbis | `https://ranawalk.com/{lang}/orbis` |
| `leo` | `leopard` | Leopard | `https://ranawalk.com/{lang}/leopard` |
| `bis` | `bison` | Bison | `https://ranawalk.com/{lang}/bison` |

`override_url=null`, `is_active=true`, `fallback_url=https://ranawalk.com` para todos.

**Endpoint público** `GET /api/qr/<slug>` — NO requiere auth. Lógica:
1. Buscar `QRRoute` donde `is_active=true`. Si no existe → 302 a `fallback_url`, no registrar scan.
2. Si `override_url` tiene valor → 302 a `override_url` (destino absoluto, sin detección idioma). Registrar scan.
3. Si no hay override → cascada detección idioma: (1) query param `?lang=xx`, (2) `Accept-Language` header, (3) GeoIP MaxMind GeoLite2-Country (`data/geoip/GeoLite2-Country.mmdb`), (4) fallback `en`. → Sustituir `{lang}` en `destination_template` → 302. Registrar scan (INSERT sync, no Celery).
4. `ip_hash = SHA256(client_ip + settings.QR_SALT)[:32]`. `QR_SALT` en Django settings, rotación anual. **Nunca guardar IP raw.**

**Consola CEO en mwt.one** (usa auth existente — Django session, usuario CEO. Sin login → 401):
- Tabla de QR routes: slug, producto, destino actual, status override, total scans
- Editar route: `destination_template`, activar/desactivar override con motivo
- Dashboard scans: gráfica por producto / idioma / país / día
- Exportar CSV por rango de fechas
- Botón "Test QR" que abre `go.ranawalk.com/{slug}` en nueva pestaña

**Riesgos:**
- GeoIP: si la DB no existe o la IP no resuelve, `country_code` queda vacío — no debe bloquear el redirect.
- Auth: el endpoint `GET /api/qr/<slug>` es público; las rutas de consola siempre requieren sesión autenticada.

---

### [S6-Item7] DNS + Nginx — CNAME `go.ranawalk.com` → `mwt.one`

| Campo | Valor |
|---|---|
| **Sprint** | Sprint 6 |
| **Item** | 7 |
| **Prioridad** | P0 |
| **Agente** | AG-07 DevOps |
| **Estado** | Pendiente |
| **Branch** | `feature/s6-dns-nginx` |
| **Dependencia** | Ninguna |

**Descripción:**  
Configurar el subdominio `go.ranawalk.com` como CNAME hacia la IP de `mwt.one`, agregar al SAN del certificado SSL y configurar el server block de Nginx para reenviar a la app `qr/`.

**Criterios de Éxito:**
- CNAME `go.ranawalk.com` → IP de `mwt.one`
- SSL via Let's Encrypt existente: agregar `go.ranawalk.com` al SAN del certificado, renovación automática certbot
- Nginx server block:
```nginx
server {
  server_name go.ranawalk.com;
  location ~ ^/(gol|vel|orb|leo|bis)$ {
    rewrite ^/(.+)$ /api/qr/$1 break;
    proxy_pass http://django;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Real-IP $remote_addr;
  }
  location / { return 404; }
}
```
- Verificación: `curl -I https://go.ranawalk.com/gol` → HTTP 302, `Location: https://ranawalk.com/en/goliath` (con `Accept-Language: en`)

**Riesgos:**
- Si se agregan productos nuevos, actualizar el regex del location block o usar `[a-z]{3}` con validación 404 server-side.

---

### [S6-Item8] 5 QR codes PNG + SVG + slot empaque `SCH_STICKER_BASE`

| Campo | Valor |
|---|---|
| **Sprint** | Sprint 6 |
| **Item** | 8 |
| **Prioridad** | P1 |
| **Agente** | Diseño / Arquitectura |
| **Estado** | Pendiente |
| **Branch** | `feature/s6-qr-codes` |
| **Dependencia** | Item 7 — URLs confirmadas |

**Descripción:**  
Generar los 5 QR codes físicos para el empaque de cada producto Rana Walk e integrar el slot en el esquema de sticker base.

**Criterios de Éxito:**
- 5 QR codes (PNG + SVG) — Level M, 15mm mínimo, quiet zone 4 módulos
- URLs destino: `go.ranawalk.com/gol`, `go.ranawalk.com/vel`, `go.ranawalk.com/orb`, `go.ranawalk.com/leo`, `go.ranawalk.com/bis`
- Verificados con al menos 3 apps de escaneo (iOS + Android)
- Slot QR integrado en `SCH_STICKER_BASE` con herencia a bolsa/caja
- Artes de sticker actualizados con el QR

**Riesgos:**
- El QR impreso es inmutable — si el destino de `go.ranawalk.com` cambia de servidor, hay que reimprimir. La URL `go.ranawalk.com/{slug}` es el contrato de largo plazo.

---

### [S6-Item9] LOC_TECH contenido — 6 tecnologías × 3 idiomas (EN/ES/PT)

| Campo | Valor |
|---|---|
| **Sprint** | Sprint 6 |
| **Item** | 9 |
| **Prioridad** | P1 |
| **Agente** | Copy |
| **Estado** | Pendiente |
| **Branch** | `feature/s6-loc-tech` |
| **Dependencia** | ENT_TECH |

**Descripción:**  
Producir las traducciones de las 6 tecnologías Rana Walk (headline, body, stat) en los 3 idiomas para las páginas de producto.

**Criterios de Éxito:**
- `LOC_TECH_EN` — 6 tecnologías (headline + body + stat) en inglés
- `LOC_TECH_ES` — traducción aprobada al español
- `LOC_TECH_PT` — traducción aprobada al portugués
- **POL_NUNCA_TRADUCIR verificado**: nombres de tecnología (`LeapCore`, `Arch System`, `PORON XRD`, `ThinBoom`, `NanoSpread`) y sello "American Technology Inside" son invariables en los 3 idiomas

**Riesgos:**
- Item 5 (páginas de producto) queda bloqueado hasta que LOC_TECH_ES y LOC_TECH_PT estén aprobados.

---

## STRETCH P2 — Solo si hay tiempo (no parte de Sprint 6 DONE)

---

### [S6-Item10] Dashboard P&L por marca / cliente / período

| Campo | Valor |
|---|---|
| **Sprint** | Sprint 6 |
| **Item** | 10 |
| **Prioridad** | P2 — Stretch |
| **Agente** | AG-03 Frontend + AG-02 API Builder |
| **Estado** | Pendiente |
| **Branch** | `feature/s6-pl-dashboard` |
| **Dependencia** | Sprint 5 DONE, data suficiente |

**Descripción:**  
Vista de rentabilidad por marca, cliente y período. **No es parte de Sprint 6 DONE**. Solo se ejecuta si quedan ciclos libres.

**Criterios de Éxito (pendiente spec detallada del CEO):**
- Vista P&L por marca (Marluvas vs Tecmater vs Rana Walk)
- Vista P&L por cliente
- Vista P&L por período

**Riesgos:**
- PENDIENTE spec detallada según métricas que el CEO quiera ver. No implementar sin spec aprobada.

---

### [S6-Item11] Paperless-ngx bidireccional (OCR → Django)

| Campo | Valor |
|---|---|
| **Sprint** | Sprint 6 |
| **Item** | 11 |
| **Prioridad** | P2 — Stretch |
| **Agente** | AG-02 API Builder |
| **Estado** | Pendiente |
| **Branch** | `feature/s6-paperless-bidir` |
| **Dependencia** | Sprint 5 — Paperless unidireccional funcional |

**Descripción:**  
Extender la integración Paperless-ngx de unidireccional (Sprint 5) a bidireccional: Paperless notifica a Django cuando el OCR completa.

**Criterios de Éxito (pendiente spec detallada):**
- Paperless notifica Django vía webhook cuando OCR completa
- Django registra el texto extraído como metadata del artefacto correspondiente
- PENDIENTE spec detallada — depende de soporte de webhook en la API de Paperless

**Riesgos:**
- No implementar sin confirmar soporte de webhook en la versión de Paperless-ngx instalada.

---

## QA

---

### [S6-Item12] Tests Sprint 6 — E2E + regresión 35 commands

| Campo | Valor |
|---|---|
| **Sprint** | Sprint 6 |
| **Item** | 12 |
| **Prioridad** | P0 |
| **Agente** | AG-06 QA |
| **Estado** | Pendiente |
| **Branch** | `feature/s6-tests` |
| **Dependencia** | Items 1–11 |

**Descripción:**  
Suite completa de tests para Sprint 6 + validación de regresión de los 35 commands de Sprints 1-5.

**Criterios de Éxito:**
- **Rana Walk E2E:** expediente `brand=rana_walk` flujo completo hasta CERRADO en CR y USA
- **Transfers ART-13/14/15:** reemplazan reglas puente Sprint 5 correctamente
- **QR E2E:** 5 productos × 3 idiomas = 15 scans verificados con detección automática de idioma
- **Override QR:** cambiar destino en consola → siguiente scan va al nuevo destino
- **Edge cases QR:** slug inválido → fallback; `Accept-Language` vacío → `en`; GeoIP fail → no bloquea
- **ranawalk.com:** 15 páginas de producto renderizan correctamente
- **hreflang:** verificar con Google Search Console o herramienta externa
- **Regresión:** 35 commands Sprint 1-5 funcionales (no regresión)
- Tests passing en CI

---

## Tabla resumen — Nuevos endpoints Sprint 6

| Command | Método | Path | Auth | Item |
|---|---|---|---|---|
| C36 CompleteReception | POST | `/api/transfers/{id}/complete-reception` | CEO | 2 |
| C37 CompletePreparation | POST | `/api/transfers/{id}/complete-preparation` | CEO | 2 |
| C38 CompleteDispatch | POST | `/api/transfers/{id}/complete-dispatch` | CEO | 2 |
| C39 ApproveTransferPricing | POST | `/api/transfers/{id}/approve-pricing` | CEO | 3 |
| QR Resolve | GET | `/api/qr/<slug>` | Público | 6 |

> `QR Resolve` es GET, no command POST. No suma al conteo de commands pero sí es endpoint nuevo.  
> **Total post-Sprint 6:** 35 (Sprint 1-5) + 4 POST = **39 command endpoints**.

---

## Convenciones de naming — Contrato inmutable

| product_key | product_slug | display_name | QR slug | Arcos |
|---|---|---|---|---|
| `gol` | `goliath` | Goliath | `gol` | MED |
| `vel` | `velox` | Velox | `vel` | MED |
| `orb` | `orbis` | Orbis | `orb` | MED |
| `leo` | `leopard` | Leopard | `leo` | LOW/MED/HGH |
| `bis` | `bison` | Bison | `bis` | LOW/MED/HGH |

- `product_key` — 3 letras, **inmutable**. Usado en QR slug, `QRRoute.slug`, analytics, DB keys.
- `product_slug` — lowercase, **inmutable**. Usado en URLs de `ranawalk.com` (`/en/goliath`) y `QRRoute.product_slug`.
- `display_name` — capitalizado, usado en UI, consola CEO, textos visibles. Puede cambiar sin romper nada.

---

## Qué NO hacer en Sprint 6

| Feature | Razón |
|---|---|
| Conector fiscal FacturaProfesional | Dependencia externa — Post-MVP |
| RBAC multi-usuario | MVP CEO solo — Post-MVP |
| Multi-moneda | 1 moneda por expediente es suficiente — Post-MVP |
| QR por SKU individual (54 individuales) | Contenido igual por talla — decisión final `ENT_PLAT_I18N.I` |
| Tracking automático carriers (DHL, MSC) | Updates manuales Sprint 6 — Post-MVP |
| Items 10 y 11 (Dashboard P&L + Paperless bidir) | Stretch P2 — solo si sobra tiempo |

---

## Criterio Sprint 6 DONE

1. Puedo crear un expediente con `brand=rana_walk` y llevarlo hasta CERRADO
2. ART-13/14/15 funcionan en transfers — ya no se usan las confirmaciones manuales de Sprint 5
3. `ranawalk.com` muestra 15 páginas de producto (5 × 3 idiomas) con contenido correcto
4. Escaneo un QR con mi celular → llego a `ranawalk.com` en mi idioma
5. Cambio el destino de un QR en la consola de `mwt.one` → el siguiente scan va al nuevo destino
6. Los 35 endpoints de Sprint 1-5 siguen funcionando (no regresión)
7. Tests passing

---

*Generado desde: `BRIEF_SPRINT6_ALEJANDRO.md` + `LOTE_SM_SPRINT6.md` · Notion: MWT Plataforma — Tareas por Sprint (Sprint 6)*
