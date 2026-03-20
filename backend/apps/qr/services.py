import hashlib
from django.conf import settings
from .models import QRRoute, QRScan

try:
    import geoip2.database
    GEOIP_AVAILABLE = True
except ImportError:
    GEOIP_AVAILABLE = False

class GeoIPResolver:
    @staticmethod
    def resolve(ip_address):
        if not GEOIP_AVAILABLE or not ip_address:
            return ""
        try:
            with geoip2.database.Reader('/data/geoip/GeoLite2-Country.mmdb') as reader:
                response = reader.country(ip_address)
                return response.country.iso_code or ""
        except Exception:
            return ""

class LangDetector:
    @staticmethod
    def detect(request, geo_country=""):
        # priority 1: query param
        if 'lang' in request.GET and request.GET['lang'] in ['en', 'es', 'pt']:
            return request.GET['lang']
        # priority 2: header Accept-Language
        accept_lang = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        for lang in ['en', 'es', 'pt']:
            if lang in accept_lang.lower():
                return lang
        # priority 3: GeoIP
        if geo_country in ['US', 'CA', 'GB', 'AU', 'NZ']: return 'en'
        if geo_country in ['CR', 'GT', 'CO', 'MX', 'ES', 'AR', 'CL', 'PE', 'VE', 'EC', 'DO', 'SV', 'HN', 'PA', 'NI', 'PY', 'BO', 'UY']: return 'es'
        if geo_country in ['BR', 'PT', 'AO', 'MZ']: return 'pt'
        # priority 4: default fallback
        return 'en'

class QRResolver:
    @staticmethod
    def resolve_and_log(slug, request):
        route = QRRoute.objects.filter(slug=slug, is_active=True).first()
        if not route:
            # Fallback for undefined route
            return "https://ranawalk.com"
            
        if route.override_url:
            target_url = route.override_url
            detected_lang = "en"
            country_code = ""
            ip_hash = ""
            ip_address = ""
        else:
            ip_address = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
            if ip_address and ',' in ip_address:
                ip_address = ip_address.split(',')[0].strip()
            
            country_code = GeoIPResolver.resolve(ip_address)
            detected_lang = LangDetector.detect(request, country_code)
            target_url = route.destination_template.replace('{lang}', detected_lang)
            
            salt = getattr(settings, 'QR_SALT', 'default-salt-value-for-hashing-ip')
            ip_hash = hashlib.sha256(f"{ip_address}{salt}".encode('utf-8')).hexdigest()[:32]
            
        try:
            QRScan.objects.create(
                route=route,
                detected_lang=detected_lang,
                country_code=country_code,
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:1000],
                ip_hash=ip_hash
            )
        except Exception:
            pass # Failsafe, don't break response if scan log fails
            
        return target_url
