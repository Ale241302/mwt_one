from django.test import TestCase, override_settings
from django.urls import reverse
from apps.qr.models import QRRoute, QRScan
from apps.qr.services import LangDetector, QRResolver

class QRLogicTests(TestCase):
    def setUp(self):
        self.route = QRRoute.objects.create(
            slug='gol', 
            product_slug='goliath', 
            product_name='Goliath',
            destination_template='https://ranawalk.com/{lang}/goliath'
        )

    def test_lang_detector_query_param(self):
        class MockRequest:
            GET = {'lang': 'pt'}
            META = {}
        self.assertEqual(LangDetector.detect(MockRequest()), 'pt')

    def test_lang_detector_accept_language(self):
        class MockRequest:
            GET = {}
            META = {'HTTP_ACCEPT_LANGUAGE': 'es-ES,es;q=0.9'}
        self.assertEqual(LangDetector.detect(MockRequest()), 'es')

    def test_qr_redirect_creates_scan(self):
        url = reverse('qr:qr_redirect', args=['gol'])
        response = self.client.get(url, HTTP_ACCEPT_LANGUAGE='es-ES')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, 'https://ranawalk.com/es/goliath')
        
        self.assertEqual(QRScan.objects.count(), 1)
        scan = QRScan.objects.first()
        self.assertEqual(scan.detected_lang, 'es')
        self.assertEqual(scan.route, self.route)

    def test_qr_fallback_when_not_found(self):
        url = reverse('qr:qr_redirect', args=['nonexistent'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, 'https://ranawalk.com')
        self.assertEqual(QRScan.objects.count(), 0)

    def test_qr_override_url(self):
        self.route.override_url = 'https://promo.ranawalk.com'
        self.route.save()
        url = reverse('qr:qr_redirect', args=['gol'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, 'https://promo.ranawalk.com')
        self.assertEqual(QRScan.objects.count(), 1)

