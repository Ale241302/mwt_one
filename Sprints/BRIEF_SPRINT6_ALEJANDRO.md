# Sprint 6 — Brief para Alejandro
**Fecha:** Marzo 2026
**De:** Álvaro Alfaro, CEO
**Proyecto:** mwt.one + ranawalk.com

---

## Qué se construye en Sprint 6

Tres bloques independientes que pueden avanzar en paralelo:

**Bloque A — Rana Walk como marca en mwt.one**
Registrar Rana Walk como marca operativa en la plataforma. Crear expedientes con brand=rana_walk, ejecutar el flujo completo (CR y USA), y activar los artefactos de transfer que en Sprint 5 quedaron como "reglas puente" manuales.

**Bloque B — ranawalk.com multi-idioma**
El sitio público necesita funcionar en 3 idiomas (EN, ES, PT). Routing por prefijo de idioma, detección automática, y 5 páginas de producto ("Inside Your Goliath", etc.) cada una en los 3 idiomas.

**Bloque C — QR Universal en empaque**
Cada producto Rana Walk va a tener un QR en el sticker. El QR apunta a un subdominio (go.ranawalk.com) que es un CNAME a mwt.one. Django resuelve a qué URL redirigir, detectando el idioma del dispositivo. Los destinos se administran desde una consola en mwt.one.

---

## Precondición

Sprint 5 completado: Transfer model funcional (C30-C35), ART-10 liquidación operativa, 35 command endpoints POST.

---

## Orden sugerido de ejecución

```
Semana 1-2:  Item 6 (app Django qr/) + Item 4 (i18n ranawalk.com) + Item 1 (brand config RW)
Semana 2-3:  Item 2 (ART-13/14/15) + Item 5 (páginas producto) + Item 7 (DNS + Nginx)
Semana 3-4:  Item 3 (ART-16) + Item 8 (QR codes empaque) + Item 12 (tests)
```

Items 10-11 son stretch — solo si hay tiempo.

---

## Naming — esto es contrato, no sugerencia

Usar estos valores exactos en DB, URLs, analytics, y UI. No inventar otros.

| product_key | product_slug | display_name | QR slug |
|-------------|-------------|-------------|---------|
| gol | goliath | Goliath | gol |
| vel | velox | Velox | vel |
| orb | orbis | Orbis | orb |
| leo | leopard | Leopard | leo |
| bis | bison | Bison | bis |

- `product_key` (3 letras): para DB keys, analytics, QR slug. Inmutable.
- `product_slug` (lowercase): para URLs de ranawalk.com (`/en/goliath`). Inmutable.
- `display_name`: para UI visible. Puede cambiar sin romper nada.

---

## BLOQUE A — Rana Walk en plataforma

### Item 1: Brand config
- Registrar brand=rana_walk, brand_type=own en el sistema
- Flujo de artefactos: ART-01, ART-02, ART-05, ART-06, ART-09, ART-11
- NO usa: ART-03, ART-04, ART-10 (no aplican a marca propia)
- Bifurcación: CR (nacionalización + IVA) vs USA (directo FBA/DTC)
- 54 SKUs:

| Producto | Arcos | SKUs | Nomenclatura |
|----------|-------|------|-------------|
| Goliath | MED (1) | 6 | RW-GOL-MED-S1..S6 |
| Velox | MED (1) | 6 | RW-VEL-MED-S1..S6 |
| Orbis | MED (1) | 6 | RW-ORB-MED-S1..S6 |
| Leopard | LOW/MED/HGH (3) | 18 | RW-LEO-{arco}-S1..S6 |
| Bison | LOW/MED/HGH (3) | 18 | RW-BIS-{arco}-S1..S6 |

### Item 2: Artefactos Transfer (ART-13, ART-14, ART-15)

Reemplazan las "reglas puente" de Sprint 5 (confirmaciones manuales).

**ART-13 — Recepción en nodo**
- ArtifactInstance type=ART-13
- Payload: `{ lines: [{ sku, quantity_received, condition }], received_by, received_at, notes }`
- condition: enum (good, damaged, partial)
- Command: `POST /api/transfers/{id}/complete-reception/` (C36)

**ART-14 — Preparación / Acondicionamiento**
- ArtifactInstance type=ART-14
- Payload: `{ actions: [{ action_type, description, quantity_affected }], prepared_by, prepared_at, notes }`
- action_type: enum (packaging, labeling, stickering, quality_check, other)
- Command: `POST /api/transfers/{id}/complete-preparation/` (C37)

**ART-15 — Despacho inter-nodo**
- ArtifactInstance type=ART-15
- Payload: `{ carrier, tracking_number, dispatch_date, destination_node, notes }`
- Command: `POST /api/transfers/{id}/complete-dispatch/` (C38)

**Integración con Transfer state machine:**
- in_transit requiere ART-15 completado
- received requiere ART-13 completado

### Item 3: ART-16 Transfer pricing approval
- ArtifactInstance type=ART-16
- Payload: `{ transfer_price, currency, justification, approved_by, approved_at }`
- Solo cuando Transfer.ownership_changes=true
- CEO-ONLY
- Command: `POST /api/transfers/{id}/approve-pricing/` (C39)
- Transfer no puede reconciliarse sin ART-16 (si ownership_changes=true)

---

## BLOQUE B — ranawalk.com multi-idioma

### Item 4: i18n routing
- Instalar next-intl (o equivalente) con 3 locales: en, es, pt
- URLs: `ranawalk.com/{lang}/{path}`
- Middleware root: `ranawalk.com/` → detecta Accept-Language → 302 a `/{lang}/`
- hreflang tags en layout: `<link rel="alternate">` para en, es, pt + x-default apunta a /en/
- Toggle idioma visible en header del sitio

### Item 5: 5 páginas producto "Inside Your {Product}"

Componente reutilizable `InsideProduct` que recibe: techs[], ratings{}, seal (string o null), archProfiles[] (array o null).

| Ruta | Producto | Techs | Seal | Arcos | Color primario | Color accent |
|------|----------|-------|------|-------|---------------|-------------|
| /en/goliath | Goliath | 5 (LeapCore, Arch System, PORON XRD, ThinBoom, NanoSpread) | "American Technology Inside" | — | #013A57 | #A8D8EA |
| /en/velox | Velox | 2 (ThinBoom full, NanoSpread) | null | — | #7B2DBF | #E040FB |
| /en/orbis | Orbis | 2 (LeapCore, NanoSpread) | null | — | #FFFFFF | #EF4E54 |
| /en/leopard | Leopard | 3 (LeapCore, ShockSphere, NanoSpread) | null | Low/Med/High | #5C3A1E | #B87333 |
| /en/bison | Bison | 3 (LeapCore, PORON XRD, NanoSpread) | "American Technology Inside" | Low/Med/High | #2C2C2C | #FF8C00 |

Total: 5 EN + 5 ES + 5 PT = 15 páginas.

Nombres de tecnología (LeapCore, Arch System, etc.) NUNCA se traducen. El sello "American Technology Inside" tampoco.

---

## BLOQUE C — QR Universal

### Cómo funciona

```
Usuario escanea QR en sticker del producto
  → go.ranawalk.com/gol                        (URL corta impresa en QR)
  → DNS CNAME resuelve a mwt.one
  → Nginx rewrite: /gol → /api/qr/gol
  → Django endpoint lee QRRoute de DB
      ├── detecta idioma del dispositivo
      ├── registra scan en DB
      └── 302 redirect al destino
  → ranawalk.com/en/goliath                     (o /es/ o /pt/)
  → Usuario ve "Inside Your Goliath" en su idioma
```

El CEO puede cambiar el destino desde la consola de mwt.one sin reimprimir QR ni hacer deploy.

### Item 6: App Django qr/

**Modelos:**

```python
class QRRoute(models.Model):
    slug = CharField(max_length=10, unique=True)           # "gol"
    product_slug = CharField(max_length=50)                 # "goliath" — inmutable
    product_name = CharField(max_length=50)                 # "Goliath" — display
    destination_template = CharField(max_length=500)        # "https://ranawalk.com/{lang}/goliath"
    is_active = BooleanField(default=True)
    fallback_url = URLField(default="https://ranawalk.com")
    override_url = URLField(blank=True, null=True)          # campaña temporal
    override_reason = CharField(max_length=200, blank=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

class QRScan(models.Model):
    route = ForeignKey(QRRoute, on_delete=SET_NULL, null=True)
    detected_lang = CharField(max_length=2)                 # en, es, pt
    country_code = CharField(max_length=2, blank=True)      # GeoIP
    user_agent = TextField(blank=True)
    ip_hash = CharField(max_length=32)                      # SHA256(ip+SALT) trunc 16 bytes
    scanned_at = DateTimeField(auto_now_add=True)
```

**Seed inicial:**

| slug | product_slug | product_name | destination_template |
|------|-------------|-------------|---------------------|
| gol | goliath | Goliath | `https://ranawalk.com/{lang}/goliath` |
| vel | velox | Velox | `https://ranawalk.com/{lang}/velox` |
| orb | orbis | Orbis | `https://ranawalk.com/{lang}/orbis` |
| leo | leopard | Leopard | `https://ranawalk.com/{lang}/leopard` |
| bis | bison | Bison | `https://ranawalk.com/{lang}/bison` |

override_url=null, is_active=true, fallback_url=https://ranawalk.com para todos.

**Endpoint público (NO requiere auth):**

`GET /api/qr/{slug}`

Lógica:
1. Buscar QRRoute por slug donde is_active=true
2. Si no existe o inactivo → 302 a fallback_url. No registrar scan.
3. Si override_url tiene valor → 302 a override_url (destino absoluto, sin detección idioma). Registrar scan.
4. Si no hay override → detectar idioma con esta cascada:
   - Prioridad 1: query param `?lang=xx`
   - Prioridad 2: header `Accept-Language` — primer match contra [en, es, pt]
   - Prioridad 3: GeoIP (IP → país → idioma: US→en, CR/GT/CO→es, BR→pt)
   - Prioridad 4: fallback `en`
5. Sustituir `{lang}` en destination_template → 302 a resultado
6. Registrar scan: INSERT sync (no Celery). QRScan.create() — <5ms, no justifica cola.

**ip_hash:** `SHA256(client_ip + settings.QR_SALT)` truncado a 16 bytes (32 hex chars). QR_SALT en settings, rotación anual. Nunca guardar IP raw.

**GeoIP:** MaxMind GeoLite2-Country. DB en `/data/geoip/GeoLite2-Country.mmdb`. Actualización manual trimestral. Si la DB no existe o la IP no resuelve → country_code="" (no bloquea).

**Auth:** El endpoint /api/qr/{slug} es público. La consola de administración usa auth existente de mwt.one (Django session, usuario CEO). Sin login → 401.

**Consola CEO (nueva sección en mwt.one):**
- Tabla de QR routes: slug, producto, destino actual, status override, total scans
- Editar route: cambiar destination_template, activar/desactivar override con motivo
- Dashboard scans: gráfica por producto, por idioma, por país, por día
- Exportar CSV por rango de fechas
- Botón "Test QR" que abre go.ranawalk.com/{slug} en nueva pestaña

### Item 7: DNS + Nginx
- CNAME `go.ranawalk.com` → IP de mwt.one
- SSL via Let's Encrypt existente. Agregar go.ranawalk.com al SAN del certificado. Renovación automática certbot.
- Nginx server block:

```nginx
server {
    server_name go.ranawalk.com;
    
    location ~ ^/(gol|vel|orb|leo|bis)$ {
        rewrite ^/(.*)$ /api/qr/$1 break;
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location / {
        return 404;
    }
}
```

**Verificación:** `curl -I https://go.ranawalk.com/gol` → HTTP 302, Location: `https://ranawalk.com/en/goliath` (si Accept-Language es en).

---

## Endpoints nuevos Sprint 6

| Command | Método | Path | Auth | Item |
|---------|--------|------|------|------|
| C36 CompleteReception | POST | /api/transfers/{id}/complete-reception/ | CEO | 2 |
| C37 CompletePreparation | POST | /api/transfers/{id}/complete-preparation/ | CEO | 2 |
| C38 CompleteDispatch | POST | /api/transfers/{id}/complete-dispatch/ | CEO | 2 |
| C39 ApproveTransferPricing | POST | /api/transfers/{id}/approve-pricing/ | CEO | 3 |
| — QR Resolve | GET | /api/qr/{slug} | Público | 6 |

Total post-Sprint 6: 35 (Sprint 1-5) + 4 POST = 39 command endpoints.

---

## Qué NO hacer

- No crear RBAC ni sistema de roles. MVP = un solo usuario (CEO).
- No conectar con FacturaProfesional (conector fiscal). Facturas se manejan manualmente.
- No implementar multi-moneda. 1 moneda por expediente.
- No crear QR por SKU individual (son 5 por producto, no 54 por talla).
- No hacer tracking automático con APIs de carriers (DHL, MSC). Updates manuales.
- Items 10 y 11 (Dashboard P&L y Paperless bidireccional) son stretch. Solo si sobra tiempo. No son parte de "Sprint DONE".

---

## Cómo saber que Sprint 6 está terminado

1. Puedo crear un expediente con brand=rana_walk y llevarlo hasta CERRADO
2. ART-13/14/15 funcionan en transfers (ya no se usan las confirmaciones manuales de Sprint 5)
3. ranawalk.com muestra 15 páginas de producto (5 × 3 idiomas) con contenido correcto
4. Escaneo un QR con mi celular → llego a ranawalk.com en mi idioma
5. Cambio el destino de un QR en la consola de mwt.one → el siguiente scan va al nuevo destino
6. Los 35 endpoints de Sprint 1-5 siguen funcionando (no regresión)
7. Tests passing

---

**Ref técnica completa:** LOTE_SM_SPRINT6.md (criterios de done detallados por item, 3 rondas auditoría, 10/10).
**Arquitectura QR/i18n:** ENT_PLAT_I18N.md (estrategia, modelos, decisiones).
