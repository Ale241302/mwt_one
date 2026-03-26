from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.qr.models import QRRoute, QRScan
from apps.expedientes.tests.factories import create_user

class QRE2ETests(APITestCase):

    def setUp(self):
        self.ceo = create_user(username='ceo', is_superuser=True)
        # Seed routes
        self.routes = [
            QRRoute.objects.create(slug="gol", product_slug="goliath", product_name="Goliath", destination_template="https://ranawalk.com/{lang}/goliath"),
            QRRoute.objects.create(slug="vel", product_slug="velox", product_name="Velox", destination_template="https://ranawalk.com/{lang}/velox"),
            QRRoute.objects.create(slug="orb", product_slug="orbis", product_name="Orbis", destination_template="https://ranawalk.com/{lang}/orbis"),
            QRRoute.objects.create(slug="leo", product_slug="leopard", product_name="Leopard", destination_template="https://ranawalk.com/{lang}/leopard"),
            QRRoute.objects.create(slug="bis", product_slug="bison", product_name="Bison", destination_template="https://ranawalk.com/{lang}/bison")
        ]

    def test_qr_scan_detects_language_header(self):
        url = reverse('qr:resolve_qr', kwargs={'slug': 'gol'})
        res = self.client.get(url, HTTP_ACCEPT_LANGUAGE='es-ES,es;q=0.9')
        self.assertEqual(res.status_code, status.HTTP_302_FOUND)
        self.assertEqual(res.url, "https://ranawalk.com/es/goliath")
        
        scan = QRScan.objects.filter(route__slug='gol').last()
        self.assertIsNotNone(scan)
        self.assertEqual(scan.detected_lang, 'es')

    def test_qr_scan_all_5_products_in_3_langs(self):
        langs = ['en', 'es', 'pt']
        slugs = [r.slug for r in self.routes]
        
        for lang in langs:
            for slug in slugs:
                url = reverse('qr:resolve_qr', kwargs={'slug': slug})
                res = self.client.get(url, {'lang': lang})
                self.assertEqual(res.status_code, status.HTTP_302_FOUND)
                route = QRRoute.objects.get(slug=slug)
                self.assertEqual(res.url, route.destination_template.replace('{lang}', lang))
                
        self.assertEqual(QRScan.objects.count(), 15)

    def test_qr_override(self):
        route = self.routes[0]
        route.override_url = "https://example.com/promo"
        route.save()
        
        url = reverse('qr:resolve_qr', kwargs={'slug': route.slug})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_302_FOUND)
        self.assertEqual(res.url, "https://example.com/promo")

    def test_qr_fallback(self):
        url = reverse('qr:resolve_qr', kwargs={'slug': 'invalid'})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_302_FOUND)
        self.assertEqual(res.url, "https://ranawalk.com")

