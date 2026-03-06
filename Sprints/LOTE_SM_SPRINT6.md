# LOTE_SM_SPRINT6 — Rana Walk Flujo Completo + i18n + QR Universal
status: DRAFT — Pendiente aprobación CEO
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
tipo: Lote ruteado (ref → PLB_ORCHESTRATOR §E)
sprint: 6
priority: P0
depends_on: LOTE_SM_SPRINT5 (todos los items aprobados — Transfer model en producción, ART-10 reconciliación funcional)
refs: ENT_OPS_TRANSFERS, ENT_PLAT_ARTEFACTOS, ARTIFACT_REGISTRY, ENT_PLAT_I18N, ENT_PLAT_FRONTENDS, ENT_PROD_{GOL,VEL,ORB,LEO,BIS}, ENT_TECH

---

## Objetivo Sprint 6

Tres pilares: (1) Rana Walk como marca operativa en la plataforma — brand config, flujo de expediente CR/USA, transfers entre nodos. (2) ranawalk.com público con i18n (3 idiomas) y páginas de producto. (3) QR universal en empaque con resolver administrable en mwt.one.

**Precondición:** Sprint 5 DONE — Transfer model + state machine + commands C30-C35 funcionales, ART-10 reconciliación operativa, ART-12 compensación, Paperless-ngx integrado, 35 command endpoints POST.

### Incluido

| # | Feature | Fuente | Prioridad |
|---|---------|--------|-----------|
| 1 | Brand config Rana Walk en plataforma (catálogo, flujo, bifurcación CR/USA) | ENT_PLAT_ARTEFACTOS.C4, ENT_PLAT_MODULOS | P0 |
| 2 | Artefactos Transfer: ART-13 Recepción, ART-14 Preparación, ART-15 Despacho | ARTIFACT_REGISTRY sección TRANSFER | P0 |
| 3 | ART-16 Transfer pricing approval | ARTIFACT_REGISTRY | P1 |
| 4 | ranawalk.com i18n routing (en/es/pt) + hreflang + toggle | ENT_PLAT_I18N §C3, §E1 | P0 |
| 5 | 5 páginas producto × 3 idiomas ("Inside Your {Product}") | ENT_PLAT_I18N §C3 | P1 |
| 6 | App Django qr/ (QRRoute + QRScan + resolver + consola CEO) | ENT_PLAT_I18N §C2 | P0 |
| 7 | DNS CNAME go.ranawalk.com → mwt.one + Nginx | ENT_PLAT_I18N §C1 | P0 |
| 8 | 5 QR codes + integración empaque (slot en SCH_STICKER_BASE) | ENT_PLAT_I18N §D | P1 |
| 9 | LOC_TECH_{EN,ES,PT} — descripciones 6 tecnologías × 3 idiomas | ENT_PLAT_I18N §G | P1 |
| 10 | Dashboard P&L por marca/cliente/período | LOTE_SM_SPRINT5 "Sprint 6+" | P2 |
| 11 | Paperless-ngx bidireccional (OCR → Django) | LOTE_SM_SPRINT5 "Sprint 6+" | P2 |
| 12 | Tests Sprint 6 | — | P0 |

### Excluido

| Feature | Razón | Cuándo |
|---------|-------|--------|
| Conector fiscal FacturaProfesional | Dependencia externa | Post-MVP |
| RBAC multi-usuario | MVP = CEO solo | Post-MVP |
| Multi-moneda real | 1 moneda por expediente suficiente | Post-MVP |
| Forecast / inteligencia operativa | Requiere 6+ meses data | Post-MVP |
| Portal B2B (clientes/distribuidores) | Solo CEO usa MVP | Post-MVP |
| QR per-SKU (54 individuales) | Contenido igual por talla | Nunca (decisión ENT_PLAT_I18N §I) |
| Autenticidad/garantía en QR | Scope diferente, requiere serialization | Evaluar post-lanzamiento |

---

## Convenciones de naming

Contrato estable para todo el sprint. Cualquier tabla, endpoint, UI o analytics usa estos valores.

| product_key | product_slug | display_name | QR slug | Arcos |
|-------------|-------------|-------------|---------|-------|
| gol | goliath | Goliath | gol | MED |
| vel | velox | Velox | vel | MED |
| orb | orbis | Orbis | orb | MED |
| leo | leopard | Leopard | leo | LOW/MED/HGH |
| bis | bison | Bison | bis | LOW/MED/HGH |

Reglas:
- `product_key` (3 letras): inmutable. Usado en QR slug, QRRoute.slug, analytics, DB keys. Fuente: ENT_PROD_{X}.A1.
- `product_slug` (nombre completo lowercase): inmutable. Usado en URLs de ranawalk.com (`/en/goliath`), QRRoute.product_slug. Fuente: ENT_PROD_{X}.A2 lowercase. Se almacena explícito en QRRoute — no se deriva en runtime.
- `display_name` (capitalizado): usado en UI, consola CEO, textos visibles. Fuente: ENT_PROD_{X}.A2.
- QRRoute almacena `slug` (= product_key), `product_slug` (= slug URL inmutable), y `product_name` (= display_name). Los 3 campos son independientes — cambiar display_name no afecta URLs.

---

## Items

### PILAR 1 — Rana Walk en plataforma

#### Item 1: Brand config Rana Walk
- **Agente:** AG-01 Architect + AG-02 API Builder
- **Dependencia:** Sprint 5 DONE
- **Criterio de done:**
  - [ ] Rana Walk como brand registrada en el sistema (brand=rana_walk, brand_type=own)
  - [ ] Flujo de artefactos RW: ART-01, ART-02, ART-05, ART-06, ART-09, ART-11 (ref → ENT_PLAT_ARTEFACTOS.C4)
  - [ ] Sin ART-03, ART-04, ART-10 (no aplican a marca propia)
  - [ ] Bifurcación: CR (nacionalización + IVA) vs USA (directo FBA/DTC) como variante del expediente
  - [ ] 54 SKUs Rana Walk importables. Desglose por producto:

    | Producto | Arcos | Tallas | SKUs | Nomenclatura |
    |----------|-------|--------|------|-------------|
    | Goliath | MED (1) | S1-S6 | 6 | RW-GOL-MED-S1..S6 |
    | Velox | MED (1) | S1-S6 | 6 | RW-VEL-MED-S1..S6 |
    | Orbis | MED (1) | S1-S6 | 6 | RW-ORB-MED-S1..S6 |
    | Leopard | LOW/MED/HGH (3) | S1-S6 | 18 | RW-LEO-{LOW,MED,HGH}-S1..S6 |
    | Bison | LOW/MED/HGH (3) | S1-S6 | 18 | RW-BIS-{LOW,MED,HGH}-S1..S6 |
    | **Total** | | | **54** | |

    Fuente canónica: ENT_PROD_{X}.D1-D2, ENT_OPS_TALLAS. GOL/VEL/ORB = 1 arco × 6 tallas = 6. LEO/BIS = 3 arcos × 6 tallas = 18. Total: (3×6) + (2×18) = 54.

#### Item 2: Artefactos Transfer ART-13, ART-14, ART-15
- **Agente:** AG-02 API Builder
- **Dependencia:** Sprint 5 Transfer model funcional (C30-C35)
- **Criterio de done:**

  **(A) Baseline ejecutable (P0) — implementable sin sesión de diseño:**
  - [ ] ART-13 Recepción en nodo: modelo ArtifactInstance type=ART-13, payload mínimo: `{ lines: [{ sku, quantity_received, condition }], received_by, received_at, notes }`. Reemplaza regla puente Sprint 5.
  - [ ] ART-14 Preparación: modelo ArtifactInstance type=ART-14, payload mínimo: `{ actions: [{ action_type, description, quantity_affected }], prepared_by, prepared_at, notes }`. action_type enum: packaging, labeling, stickering, quality_check, other.
  - [ ] ART-15 Despacho: modelo ArtifactInstance type=ART-15, payload mínimo: `{ carrier, tracking_number, dispatch_date, destination_node, notes }`. Reemplaza regla puente Sprint 5.
  - [ ] Los 3 integrados con Transfer state machine: in_transit requiere ART-15, received requiere ART-13.
  - [ ] Commands: C36 CompleteReception, C37 CompletePreparation, C38 CompleteDispatch.

  **(B) Enhancements (P2) — bloqueados hasta sesión de diseño:**
  - [ ] ART-13: fotos de recepción, firma digital receptor, reporte daños detallado
  - [ ] ART-14: checklist configurable por tipo de producto, tiempo estimado por acción
  - [ ] ART-15: sub-tramos, integración carrier API, ETA calculada

#### Item 3: ART-16 Transfer pricing approval
- **Agente:** AG-02 API Builder
- **Dependencia:** Item 2
- **Criterio de done:**

  **(A) Baseline ejecutable (P1):**
  - [ ] ART-16: modelo ArtifactInstance type=ART-16, payload mínimo: `{ transfer_price, currency, justification, approved_by, approved_at }`
  - [ ] Solo se crea cuando Transfer.ownership_changes=true
  - [ ] CEO-ONLY: solo CEO puede crear/aprobar
  - [ ] Command: C39 ApproveTransferPricing
  - [ ] Transfer no puede pasar a reconciled sin ART-16 aprobado (si ownership_changes=true)

  **(B) Enhancements (P2) — bloqueados hasta contexto fiscal por jurisdicción:**
  - [ ] Arm's length validation rules por par de jurisdicciones
  - [ ] Documentación soporte para auditoría fiscal

### PILAR 2 — ranawalk.com i18n + páginas producto

#### Item 4: i18n routing ranawalk.com
- **Agente:** AG-03 Frontend
- **Dependencia:** Proyecto ranawalk.com existente
- **Criterio de done:**
  - [ ] next-intl configurado con 3 locales (en/es/pt)
  - [ ] URLs `/{lang}/{path}` funcionales
  - [ ] Middleware root: `ranawalk.com/` → 302 a `/{lang}/` por Accept-Language (cascada ENT_PLAT_I18N §C4)
  - [ ] `<link rel="alternate" hreflang>` × 3 + x-default en layout
  - [ ] Toggle idioma visible en header

#### Item 5: Páginas producto "Inside Your {Product}"
- **Agente:** AG-03 Frontend + Copy
- **Dependencia:** Item 4, Item 9 (LOC_TECH)
- **Criterio de done:**
  - [ ] Componente reutilizable InsideProduct: recibe techs[], ratings{}, seal, archProfiles[]
  - [ ] `/en/goliath` — 5 techs, seal "American Technology Inside", MED. Palette: Navy #013A57 + Ice #A8D8EA
  - [ ] `/en/velox` — 2 techs, MED. Palette: Violet #7B2DBF + Magenta #E040FB
  - [ ] `/en/orbis` — 2 techs, MED. Palette: White #FFFFFF + Coral #EF4E54
  - [ ] `/en/leopard` — 3 techs, 3 arch profiles. Palette: Earth #5C3A1E + Copper #B87333
  - [ ] `/en/bison` — 3 techs, seal, 3 arch profiles. Palette: Carbon #2C2C2C + Amber #FF8C00
  - [ ] 5 páginas ES + 5 páginas PT (total 15)
  - [ ] POL_NUNCA_TRADUCIR: tech names, sello invariables
  - [ ] Mobile-first, scroll vertical. Colores: fuente canónica es ENT_PROD_{X}.E1 (dominante) y E2 (accent). Los hex listados arriba son valores actuales de esos tokens.

### PILAR 3 — QR Universal

#### Item 6: App Django qr/ + consola
- **Agente:** AG-01 + AG-02 + AG-03
- **Dependencia:** Ninguna
- **Auth:** Usa auth existente de mwt.one (Django session, single user CEO). Todas las rutas de consola QR requieren sesión autenticada. Sin login → 401/redirect. El endpoint público `GET /api/qr/{slug}` NO requiere auth (es el destino del QR scan).
- **Criterio de done:**
  - [ ] Modelo QRRoute (slug, product_slug, product_name, destination_template, override_url, override_reason, is_active, fallback_url). slug=product_key (3 letras), product_slug=URL path inmutable (ej. "goliath"), product_name=display (ej. "Goliath"). Los 3 campos independientes.
  - [ ] Modelo QRScan (FK route, detected_lang, country_code, user_agent, ip_hash, scanned_at). ip_hash = SHA256(ip + SECRET_SALT) truncado a 16 bytes hex (32 chars). SECRET_SALT en Django settings, rotación anual. No guardar IP raw nunca.
  - [ ] Seed inicial 5 routes:

    | slug | product_slug | product_name | destination_template |
    |------|-------------|-------------|---------------------|
    | gol | goliath | Goliath | `https://ranawalk.com/{lang}/goliath` |
    | vel | velox | Velox | `https://ranawalk.com/{lang}/velox` |
    | orb | orbis | Orbis | `https://ranawalk.com/{lang}/orbis` |
    | leo | leopard | Leopard | `https://ranawalk.com/{lang}/leopard` |
    | bis | bison | Bison | `https://ranawalk.com/{lang}/bison` |

    override_url=null, is_active=true, fallback_url=`https://ranawalk.com` para todos.
  - [ ] Endpoint `GET /api/qr/{slug}`: lee QRRoute de DB → detecta idioma → log scan → 302 a destino. Cascada detección idioma (inline, sin depender de doc externo): (1) query param `?lang=xx`, (2) `Accept-Language` header primer match contra [en, es, pt], (3) GeoIP país→idioma default, (4) fallback `en`.
  - [ ] Log de scan: INSERT sync (no Celery). QRScan.create() dentro del mismo request — la latencia de 1 INSERT es <5ms, no justifica cola async para Sprint 6. Si el volumen crece (>1000 scans/min), migrar a Celery task en sprint futuro.
  - [ ] Override: si override_url tiene valor → redirige ahí como destino absoluto. NO aplica detección de idioma ni template. Caso de uso: campaña, video, landing temporal. CEO activa/desactiva desde consola.
  - [ ] Fallback: si route.is_active=false o slug no existe en DB → redirige a fallback_url (default `https://ranawalk.com`). No registra scan.
  - [ ] Accept-Language parser: parsea header, matchea primer hit contra ['en', 'es', 'pt'], fallback 'en'
  - [ ] GeoIP: MaxMind GeoLite2-Country. DB almacenada en `/data/geoip/GeoLite2-Country.mmdb`. Actualización: manual (CEO descarga nueva versión cada 3 meses de MaxMind). Fallback si DB no existe o IP no resuelve: country_code="" (no bloquea redirect).
  - [ ] Consola CEO en mwt.one: tabla routes, editar destino, toggle override con motivo, dashboard scans (producto/idioma/país/día), exportar CSV

#### Item 7: DNS + Nginx
- **Agente:** CEO/Infra + AG-07 DevOps
- **Dependencia:** Ninguna
- **Criterio de done:**
  - [ ] CNAME `go.ranawalk.com` → mwt.one. SSL via automatización LE existente de mwt.one; go.ranawalk.com incluido en SAN del certificado; renovación automática certbot.
  - [ ] Nginx server block: rewrite restringido a slugs válidos `location ~ ^/(gol|vel|orb|leo|bis)$ { rewrite ^/(.+)$ /api/qr/$1 break; proxy_pass ...; }`. Cualquier otro path → 404. Si se agregan productos nuevos, actualizar regex o usar `^/[a-z]{3}$` con validación 404 server-side.
  - [ ] `curl -I go.ranawalk.com/gol` → HTTP 302, Location header apunta a `https://ranawalk.com/{detected_lang}/goliath` (ej. `https://ranawalk.com/en/goliath` para Accept-Language: en)

#### Item 8: QR codes + empaque
- **Agente:** Diseño + Arquitectura
- **Dependencia:** Item 7 (URLs confirmadas)
- **Criterio de done:**
  - [ ] 5 QR codes PNG + SVG (Level M, ≥15mm, quiet zone 4 módulos)
  - [ ] Verificados con 3 apps escaneo (iOS + Android)
  - [ ] Slot [QR] en SCH_STICKER_BASE, herencia a bolsa/caja
  - [ ] Artes sticker actualizados

#### Item 9: LOC_TECH contenido
- **Agente:** Copy
- **Dependencia:** ENT_TECH
- **Criterio de done:**
  - [ ] LOC_TECH_EN: 6 tecnologías (headline + body + stat)
  - [ ] LOC_TECH_ES: traducción aprobada
  - [ ] LOC_TECH_PT: traducción aprobada
  - [ ] POL_NUNCA_TRADUCIR verificado

### STRETCH (P2 — no parte de Sprint 6 DONE, se hacen si hay tiempo)

#### Item 10: Dashboard P&L
- **Agente:** AG-03 Frontend + AG-02 API
- **Dependencia:** Sprint 5 DONE (data suficiente)
- **Criterio de done:**
  - [ ] Vista P&L por marca (Marluvas vs Tecmater vs Rana Walk)
  - [ ] Vista P&L por cliente
  - [ ] Vista P&L por período
  - [ ] [PENDIENTE — spec detallada según métricas que el CEO quiera ver]

#### Item 11: Paperless-ngx bidireccional
- **Agente:** AG-02 API Builder
- **Dependencia:** Sprint 5 Paperless unidireccional funcional
- **Criterio de done:**
  - [ ] Paperless notifica Django cuando OCR completa
  - [ ] Django registra texto extraído como metadata del artefacto
  - [ ] [PENDIENTE — spec detallada. Depende de Paperless API webhook support.]

### QA

#### Item 12: Tests Sprint 6
- **Agente:** QA
- **Dependencia:** Items 1-11
- **Criterio de done:**
  - [ ] Rana Walk: expediente creado con brand=rana_walk, flujo completo hasta CERRADO
  - [ ] Transfers: ART-13/14/15 reemplazan reglas puente Sprint 5
  - [ ] QR E2E: 5 productos × 3 idiomas = 15 scans verificados
  - [ ] Override: cambiar destino en consola → QR redirige a nueva URL
  - [ ] Edge cases QR: slug inválido, Accept-Language vacío, GeoIP fail
  - [ ] ranawalk.com: 15 páginas producto renderizan correctamente
  - [ ] hreflang: verificar con Google Search Console o herramienta externa
  - [ ] Regresión: 35 commands Sprint 1-5 funcionales

---

## Criterio Sprint 6 DONE

1. Rana Walk operativa como marca en mwt.one (expedientes, artefactos, transfers)
2. ART-13/14/15 reemplazan reglas puente de Sprint 5
3. ranawalk.com con 15 páginas producto localizadas
4. QR universal funcional: scan → mwt.one resolve → landing correcta
5. Consola QR en mwt.one: CEO cambia destinos, ve analytics
6. 5 QR codes integrados en artes de empaque
7. Tests passing, sin regresión

**Total post-Sprint 6: 35 + 4 = 39 command endpoints POST**

## Endpoints nuevos Sprint 6

| Command | Método | Path | Auth | Owner | Item |
|---------|--------|------|------|-------|------|
| C36 CompleteReception | POST | /api/transfers/{id}/complete-reception/ | CEO | AG-02 | 2 |
| C37 CompletePreparation | POST | /api/transfers/{id}/complete-preparation/ | CEO | AG-02 | 2 |
| C38 CompleteDispatch | POST | /api/transfers/{id}/complete-dispatch/ | CEO | AG-02 | 2 |
| C39 ApproveTransferPricing | POST | /api/transfers/{id}/approve-pricing/ | CEO | AG-02 | 3 |
| — QR Resolve | GET | /api/qr/{slug} | Público | AG-02 | 6 |

Nota: QR Resolve es GET (no command POST). No suma al conteo de commands pero sí es endpoint nuevo.

---

## Qué queda para Sprint 7+

| Feature | Sprint |
|---------|--------|
| Conector fiscal FacturaProfesional | Post-MVP |
| RBAC multi-usuario + Portal B2B en mwt.one | Post-MVP |
| Multi-moneda real | Post-MVP |
| Forecast / inteligencia operativa | Post-MVP (6+ meses data) |
| QR autenticidad / garantía (per-unit serialization) | Evaluar |
| Carrier API integrations (DHL, MSC tracking automático) | Post-MVP |

---

Stamp: DRAFT — Pendiente aprobación CEO
Origen: LOTE_SM_SPRINT5 forward-looking + ENT_PLAT_I18N + sesión 2026-03-04
