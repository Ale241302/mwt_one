# ENT_PLAT_I18N — Internacionalización y QR Routing
status: DRAFT
visibility: [INTERNAL]
domain: Plataforma (IDX_PLATAFORMA)
version: 0.1
classification: ENTITY — Data pura. Estrategia i18n para todos los frontends + sistema QR universal.
refs: ENT_PLAT_FRONTENDS, ENT_PLAT_PAISES, POL_ORIGEN_LOCAL, POL_NUNCA_TRADUCIR, ENT_PROD_{GOL,VEL,ORB,LEO,BIS}, ENT_TECH, LOC_{X}_{LANG}, SCH_STICKER_BASE

---

## A. Principio

Un producto, un QR, todo el planeta. La localización es server-side, nunca print-side. El empaque no cambia por mercado. El QR es una máscara corta que apunta a mwt.one — el resolver central que decide a dónde redirigir. El destino es un dato en la base de datos, no una decisión de arquitectura. Hoy puede ser ranawalk.com, mañana Amazon, pasado un video.

---

## B. Idiomas soportados

| Código | Idioma | Mercados | Fuente contenido | Obligatorio legal |
|--------|--------|----------|-------------------|-------------------|
| en | English | USA, global fallback | LOC_{X}_EN | No |
| es | Español | Costa Rica, Guatemala, Colombia | LOC_{X}_ES | CR: Ley 7623 |
| pt | Português (BR) | Brasil | LOC_{X}_PT | BR: CDC Art.31 |

Fallback global: en. Ref → POL_NUNCA_TRADUCIR: tech names, labels talla, SKUs, marcas NUNCA se traducen.

---

## C. Arquitectura QR — Dos piezas

```
┌─────────────────────┐     ┌──────────────────────────┐     ┌─────────────────────┐
│  go.ranawalk.com    │     │       mwt.one             │     │   Destino variable  │
│  (DNS CNAME)        │────►│  /api/qr/{slug}           │────►│                     │
│                     │     │  Django resolver           │     │  ranawalk.com       │
│  Lo que ve el QR    │     │  - lee destino de DB       │     │  amazon.com         │
│  URL corta          │     │  - detecta idioma          │     │  youtube.com        │
│  No tiene servidor  │     │  - registra scan           │     │  landing campaña    │
│                     │     │  - 302 redirect            │     │  lo que diga la DB  │
└─────────────────────┘     └──────────────────────────┘     └─────────────────────┘
```

Solo hay 2 piezas: el CNAME (DNS) y el resolver (mwt.one). El destino no es parte de la arquitectura — es un dato administrable. Hoy es ranawalk.com, mañana puede ser cualquier URL.

### C1. go.ranawalk.com — Máscara DNS

No es una app. No tiene servidor. Es un registro CNAME en DNS que apunta a mwt.one. Su única función es que la URL del QR sea corta.

```
go.ranawalk.com  →  CNAME  →  mwt.one
```

### C2. mwt.one — QR Resolver administrable (Django)

Endpoint en la API Django existente. Las redirecciones se administran desde la consola CEO en mwt.one — no están hardcodeadas. El CEO puede cambiar el destino de cualquier QR sin reimprimir nada ni hacer deploy.

**Modelo Django (administrable desde consola CEO):**

```python
# apps/qr/models.py

class QRRoute(models.Model):
    slug = models.CharField(max_length=10, unique=True)          # "gol", "vel", etc.
    product_name = models.CharField(max_length=50)                # "Goliath" (display)
    destination_template = models.CharField(max_length=500)       # "https://ranawalk.com/{lang}/goliath"
    is_active = models.BooleanField(default=True)
    fallback_url = models.URLField(default="https://ranawalk.com")
    override_url = models.URLField(blank=True, null=True)        # Si tiene valor, ignora template y va directo acá
    override_reason = models.CharField(max_length=200, blank=True) # "Black Friday 2026 campaign"
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def resolve(self, lang):
        if self.override_url:
            return self.override_url      # campaña, promo, video — override total
        return self.destination_template.replace("{lang}", lang)

class QRScan(models.Model):
    route = models.ForeignKey(QRRoute, on_delete=models.SET_NULL, null=True)
    detected_lang = models.CharField(max_length=2)
    country_code = models.CharField(max_length=2, blank=True)
    user_agent = models.TextField(blank=True)
    scanned_at = models.DateTimeField(auto_now_add=True)
    ip_hash = models.CharField(max_length=64)

    class Meta:
        indexes = [
            models.Index(fields=["route", "scanned_at"]),
            models.Index(fields=["country_code", "scanned_at"]),
        ]
```

**Datos iniciales (seed):**

| slug | product_name | destination_template | override_url |
|------|-------------|---------------------|-------------|
| gol | Goliath | `https://ranawalk.com/{lang}/goliath` | null |
| vel | Velox | `https://ranawalk.com/{lang}/velox` | null |
| orb | Orbis | `https://ranawalk.com/{lang}/orbis` | null |
| leo | Leopard | `https://ranawalk.com/{lang}/leopard` | null |
| bis | Bison | `https://ranawalk.com/{lang}/bison` | null |

**Endpoint resolver:**

```python
# apps/qr/views.py

def qr_resolve(request, slug):
    route = QRRoute.objects.filter(slug=slug, is_active=True).first()
    if not route:
        return redirect("https://ranawalk.com")

    lang = detect_language(request)  # cascada §C4
    destination = route.resolve(lang)

    log_qr_scan.delay(route_id=route.id, lang=lang,
                      country=geoip(request),
                      ua=request.META.get("HTTP_USER_AGENT", ""))

    return redirect(destination, permanent=False)  # siempre 302
```

**Consola CEO en mwt.one (sección QR Routes):**

Vista de tabla con todos los QR routes activos. El CEO puede:

| Acción | Efecto | Ejemplo |
|--------|--------|---------|
| Ver scans | Dashboard con gráfica por producto/idioma/país/día | "Goliath: 340 scans esta semana, 60% EN, 25% ES, 15% PT" |
| Cambiar destino | Editar `destination_template` | Apuntar a una nueva landing en ranawalk.com |
| Activar override | Poner `override_url` + motivo | Black Friday: todos los QR van a `ranawalk.com/en/black-friday` |
| Desactivar override | Vaciar `override_url` | Vuelve al template normal |
| Desactivar route | `is_active = false` | QR devuelve fallback (ranawalk.com home) |
| Crear nuevo route | Nuevo slug + template | Producto nuevo, campaña temporal, evento |

El override es la clave: sin tocar DNS, sin deploy, sin reimprimir — el CEO cambia a dónde llega cada QR desde su dashboard. Cuando termina la campaña, quita el override y el QR vuelve a la página de producto.

**Nginx** en mwt.one para rutear el subdominio:

```nginx
server {
    server_name go.ranawalk.com;
    location / {
        rewrite ^/(\w+)(.*)$ /api/qr/$1$2 break;
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### C3. ranawalk.com — Contenido real (Next.js)

Aquí vive la experiencia "Inside Your {Producto}". ranawalk.com necesita implementar:

1. **i18n routing**: `/{lang}/{path}` con next-intl o middleware custom
2. **Páginas de producto**: 5 productos × 3 idiomas = 15 páginas con sección "Inside Your"
3. **hreflang tags**: `<link rel="alternate" hreflang="en|es|pt">` + `x-default` → /en/
4. **Root redirect**: `ranawalk.com/` → `/{lang}/` por detección Accept-Language
5. **Toggle idioma**: visible en header, cambia prefijo URL

URL structure:

| URL | Contenido |
|-----|-----------|
| `ranawalk.com/` | 302 a `/{lang}/` por detección |
| `ranawalk.com/en/` | Home EN |
| `ranawalk.com/es/` | Home ES |
| `ranawalk.com/pt/` | Home PT |
| `ranawalk.com/en/goliath` | Inside Your Goliath EN |
| `ranawalk.com/es/goliath` | Dentro de Tu Goliath ES |
| `ranawalk.com/pt/goliath` | Dentro do Seu Goliath PT |
| ... | 5 productos × 3 idiomas |

### C4. Cascada detección de idioma

Aplica en mwt.one resolver (§C2) y en ranawalk.com root redirect (§C3).

| Prioridad | Método | Ejemplo | Nota |
|-----------|--------|---------|------|
| 1 | Query param `?lang=` | `go.ranawalk.com/gol?lang=pt` | Override manual. Links compartidos localizados. |
| 2 | `Accept-Language` header | `es-CR,es;q=0.9,en;q=0.8` | Preferencia del dispositivo. Primer match contra en/es/pt. |
| 3 | GeoIP fallback | IP → país → idioma | USA→en, CR/GT/CO→es, BR→pt. Solo si Accept-Language no matchea. |
| 4 | Default | en | Si nada matchea. |

Accept-Language primero porque un brasileño en USA quiere portugués, no inglés.

---

## D. QR Universal — Asignación

### D1. Tabla de URLs (destino default — modificable desde consola)

| Producto | Slug | URL QR permanente | Destino default (editable) |
|----------|------|-------------------|---------------------------|
| Goliath | gol | `go.ranawalk.com/gol` | `ranawalk.com/{lang}/goliath` |
| Velox | vel | `go.ranawalk.com/vel` | `ranawalk.com/{lang}/velox` |
| Orbis | orb | `go.ranawalk.com/orb` | `ranawalk.com/{lang}/orbis` |
| Leopard | leo | `go.ranawalk.com/leo` | `ranawalk.com/{lang}/leopard` |
| Bison | bis | `go.ranawalk.com/bis` | `ranawalk.com/{lang}/bison` |

5 QR codes totales. La columna "Destino default" es el valor inicial en la DB — el CEO puede cambiarla a cualquier URL desde la consola mwt.one sin reimprimir ni hacer deploy. La columna "URL QR permanente" es lo que está impreso en el sticker — nunca cambia.

### D2. Formato QR

| Parámetro | Valor |
|-----------|-------|
| Contenido | `https://go.ranawalk.com/gol` |
| Error correction | Level M (15%) |
| Tamaño mínimo | 15mm × 15mm |
| Quiet zone | 4 módulos |
| Versión | Mínima (~v3 para estas URLs) |

### D3. Empaque

Slot nuevo `[QR]` en SCH_STICKER_BASE. Se hereda a SCH_STICKER_BOLSA y SCH_STICKER_CAJA. Un QR por producto, reutilizado en todos los artes. No varía por talla, arco, ni mercado.

### D4. Inmutabilidad

Lo que es permanente: la URL del QR (`go.ranawalk.com/gol`). Impresa en sticker, nunca cambia. Ref → POL_INMUTABILIDAD.

Lo que es variable: el destino. El CEO lo cambia desde consola mwt.one. Si el producto se discontinúa, el route se puede redirigir a ranawalk.com home, a otro producto, o desactivarse (fallback).

---

## E. Frontends no-QR

### E1. mwt.one (plataforma interna)

Idioma fijo por sesión. MVP: español. Post-MVP: configurable en perfil. Sin routing por idioma en URL. Documentos comerciales tienen idioma según destinatario (lógica de negocio, no i18n frontend).

### E2. muitowork.com (brochure)

Estático. Español o bilingüe ES/EN. Sin routing dinámico.

---

## F. Analytics

Modelo QRScan definido en §C2. IP hasheada (SHA256) por privacidad (ref → POL_DATA_CLASSIFICATION). Datos visibles en la consola QR Routes de mwt.one.

Métricas disponibles: scans por producto, por idioma detectado, por país (GeoIP), por día/semana/mes. Filtrable por rango de fechas. Exportable CSV desde consola.

---

## G. Contenido por idioma — Fuentes

| Sección | EN | ES | PT |
|---------|----|----|-----|
| "Inside Your" | Fijo | "Dentro de Tu" | "Dentro do Seu" |
| Tagline | LOC_{X}_EN.B1 | LOC_{X}_ES.B9 | LOC_{X}_PT.B9 |
| Tech names | ENT_TECH (invariable) | Invariable | Invariable |
| Tech descriptions | [PENDIENTE — LOC_TECH_EN] | [PENDIENTE — LOC_TECH_ES] | [PENDIENTE — LOC_TECH_PT] |
| Rating labels | "Posture, Impact..." | "Postura, Impacto..." | "Postura, Impacto..." |
| Sello | "American Technology Inside" (invariable) | Invariable | Invariable |
| Origen | POL_ORIGEN_LOCAL.EN | POL_ORIGEN_LOCAL.ES | POL_ORIGEN_LOCAL.PT |

---

## H. Implementación

Tareas de ejecución → ref LOTE_SM_SPRINT6 (paquete congelable con agentes, dependencias y criterios de done). Sprint 5 está FROZEN con scope diferente (Liquidación Marluvas + Transfer Model). i18n + QR va en Sprint 6 junto con Rana Walk flujo completo — el QR en empaque es parte del lanzamiento RW en nuevos mercados.

Scope Sprint 6 para i18n + QR: app Django qr/ (modelos QRRoute + QRScan + resolver + consola), DNS CNAME, ranawalk.com i18n routing + 5 páginas producto × 3 idiomas, QR codes para empaque, LOC_TECH_{EN,ES,PT}.

---

## I. Decisiones tomadas

| Decisión | Descartada | Razón |
|----------|-----------|-------|
| mwt.one es el resolver central, destino es dato en DB | Apuntar QR directo a ranawalk.com | El destino cambia (campaña, producto, marketplace). Si el QR apunta fijo a ranawalk.com, perdés flexibilidad. mwt.one como intermediario permite redirigir a cualquier URL sin reimprimir. |
| Consola admin en mwt.one | Hardcodear slugs en código | CEO cambia destinos sin deploy. Override para campañas. QR es activo permanente con destino variable. |
| 1 QR por producto (5 total) | 1 QR por SKU (54) | Contenido igual por talla. 54 QRs = pesadilla empaque. |
| Slug 3 letras (gol/vel/orb/leo/bis) | Nombre completo | QR más corto = mejor escaneo en sticker pequeño. |
| 302 (no 301) | 301 permanent | Idioma varía por dispositivo. 301 se cachea. |
| Accept-Language > GeoIP | GeoIP primero | Brasileño en USA quiere PT, no EN. |
| IP hash (SHA256) | IP raw | GDPR/LGPD compliance. |

---

Stamp: DRAFT — Pendiente aprobación CEO
Origen: Sesión 2026-03-04. Decisión CEO: QR universal, "Inside Your {Product}", server-side language detection, go.ranawalk.com como CNAME a mwt.one resolver.

---

Changelog:
- v0.1 (2026-03-13): version: field agregado (normalización batch Ola 3).
