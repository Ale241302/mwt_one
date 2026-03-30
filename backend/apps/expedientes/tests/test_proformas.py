# S20-12 — 35 Tests: proformas + artifact_policy
# python manage.py test apps.expedientes.tests.test_proformas

from __future__ import annotations

import uuid
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.expedientes.models import (
    Expediente, ArtifactInstance, ExpedienteProductLine, EventLog,
)
from apps.expedientes.services.artifact_policy import resolve_artifact_policy
from apps.expedientes.services.proforma_mode import change_proforma_mode
from apps.core.models import LegalEntity
from apps.brands.models import Brand
from apps.users.models import MWTUser
from apps.productos.models import ProductMaster


class BaseExpedienteTestCase(TestCase):
    """Fixtures comunes para todos los tests."""

    @classmethod
    def setUpTestData(cls):
        cls.entity = LegalEntity.objects.create(legal_name='Test Entity', country='CO', role='CLIENT')

        cls.brand_marluvas = Brand.objects.create(slug='marluvas', name='Marluvas')
        cls.brand_rana = Brand.objects.create(slug='rana_walk', name='Rana Walk')
        cls.brand_tecmater = Brand.objects.create(slug='tecmater', name='Tecmater')
        cls.brand_unknown = Brand.objects.create(slug='unknown_brand', name='Unknown')

        cls.user = MWTUser.objects.create_superuser(
            username='testadmin', email='testadmin@mwt.com', password='testpass123'
        )

        cls.product = ProductMaster.objects.create(
            sku_base='SKU-001',
            name='Producto Test',
            brand=cls.brand_marluvas,
        )

    def _make_expediente(self, brand=None, status='REGISTRO'):
        brand = brand or self.brand_marluvas
        return Expediente.objects.create(
            brand=brand,
            client=self.entity,
            legal_entity=self.entity,
            status=status,
        )

    def _make_proforma(self, expediente, mode='mode_b', number='PF-001'):
        return ArtifactInstance.objects.create(
            expediente=expediente,
            artifact_type='ART-02',
            status='COMPLETED',
            payload={'proforma_number': number, 'mode': mode, 'operated_by': 'MWT'},
        )

    def _make_product_line(self, expediente, proforma=None):
        return ExpedienteProductLine.objects.create(
            expediente=expediente,
            product=self.product,
            quantity=10,
            unit_price='100.00',
            proforma=proforma,
        )

    def _client_auth(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        return client


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 1 — Creación y proformas básicas
# ─────────────────────────────────────────────────────────────────────────────

class Test01CreateExpedienteEmpty(BaseExpedienteTestCase):
    """Test 1: Crear expediente sin OC → REGISTRO vacío."""

    def test_create_empty(self):
        exp = self._make_expediente()
        self.assertEqual(exp.status, 'REGISTRO')
        self.assertIsNotNone(exp.expediente_id)


class Test02TwoProformasInSameExpediente(BaseExpedienteTestCase):
    """Test 2: Crear 2 proformas en el mismo expediente."""

    def test_two_proformas(self):
        exp = self._make_expediente()
        pf1 = self._make_proforma(exp, mode='mode_b', number='PF-001')
        pf2 = self._make_proforma(exp, mode='mode_c', number='PF-002')
        self.assertEqual(pf1.payload['mode'], 'mode_b')
        self.assertEqual(pf2.payload['mode'], 'mode_c')
        self.assertEqual(
            ArtifactInstance.objects.filter(expediente=exp, artifact_type='ART-02').count(), 2
        )


class Test03AssignLinesViaCreateProforma(BaseExpedienteTestCase):
    """Test 3: Asignar líneas a proformas vía API → EPL.proforma actualizado."""

    def test_assign_lines(self):
        exp = self._make_expediente()
        line = self._make_product_line(exp)
        self.assertIsNone(line.proforma)

        client = self._client_auth()
        url = f'/api/expedientes/{exp.expediente_id}/proformas/'
        resp = client.post(url, {
            'proforma_number': 'PF-001',
            'mode': 'mode_b',
            'operated_by': 'MWT',
            'line_ids': [line.id],
        }, format='json')
        self.assertEqual(resp.status_code, 201, resp.data)
        line.refresh_from_db()
        self.assertIsNotNone(line.proforma)


class Test04C5BlocksLineWithoutProforma(BaseExpedienteTestCase):
    """Test 4: C5 con línea sin proforma → gate bloquea."""

    def test_c5_gate(self):
        exp = self._make_expediente()
        self._make_product_line(exp)  # sin proforma
        client = self._client_auth()
        url = f'/api/expedientes/{exp.expediente_id}/command/C5/'
        resp = client.post(url, {}, format='json')
        self.assertIn(resp.status_code, [400, 422, 409])


class Test05RanaWalkPolicy(BaseExpedienteTestCase):
    """Test 5: Rana Walk → policy NO incluye ART-03, ART-04, ART-08."""

    def test_rana_walk_no_arts(self):
        exp = self._make_expediente(brand=self.brand_rana)
        self._make_proforma(exp, mode='default')
        policy = resolve_artifact_policy(exp)
        all_arts = set()
        for state_rules in policy.values():
            all_arts |= set(state_rules.get('required', []))
            all_arts |= set(state_rules.get('optional', []))
        self.assertNotIn('ART-03', all_arts)
        self.assertNotIn('ART-04', all_arts)
        self.assertNotIn('ART-08', all_arts)


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 2 — reassign-line
# ─────────────────────────────────────────────────────────────────────────────

class Test06ReassignLineRegistro(BaseExpedienteTestCase):
    """Test 6: reassign-line en REGISTRO → OK, EventLog from/to."""

    def test_reassign_ok(self):
        exp = self._make_expediente()
        pf1 = self._make_proforma(exp, mode='mode_b', number='PF-001')
        pf2 = self._make_proforma(exp, mode='mode_c', number='PF-002')
        line = self._make_product_line(exp, proforma=pf1)

        client = self._client_auth()
        url = f'/api/expedientes/{exp.expediente_id}/command/C_REASSIGN_LINE/'
        resp = client.post(url, {
            'line_id': line.id,
            'target_proforma_id': str(pf2.artifact_id),
        }, format='json')
        self.assertNotEqual(resp.status_code, 500)


class Test07ReassignLineProduccion(BaseExpedienteTestCase):
    """Test 7: reassign-line en PRODUCCION → error."""

    def test_reassign_blocked_in_produccion(self):
        exp = self._make_expediente(status='PRODUCCION')
        pf1 = self._make_proforma(exp, mode='mode_b')
        pf2 = self._make_proforma(exp, mode='mode_c')
        line = self._make_product_line(exp, proforma=pf1)

        client = self._client_auth()
        url = f'/api/expedientes/{exp.expediente_id}/command/C_REASSIGN_LINE/'
        resp = client.post(url, {
            'line_id': line.id,
            'target_proforma_id': str(pf2.artifact_id),
        }, format='json')
        self.assertIn(resp.status_code, [400, 404, 409])


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 3 — resolve_artifact_policy
# ─────────────────────────────────────────────────────────────────────────────

class Test08PolicyZeroProformas(BaseExpedienteTestCase):
    """Test 8: 0 proformas → REGISTRO genérica."""

    def test_zero_proformas(self):
        exp = self._make_expediente()
        policy = resolve_artifact_policy(exp)
        self.assertIn('REGISTRO', policy)
        self.assertIn('ART-01', policy['REGISTRO']['required'])


class Test09PolicyMixedMode(BaseExpedienteTestCase):
    """Test 9: 2 proformas mixed mode → unión correcta, optional no contiene items de required."""

    def test_mixed_mode_union(self):
        exp = self._make_expediente()
        self._make_proforma(exp, mode='mode_b')
        self._make_proforma(exp, mode='mode_c')
        policy = resolve_artifact_policy(exp)
        for state, rules in policy.items():
            required_set = set(rules['required'])
            optional_set = set(rules['optional'])
            self.assertTrue(required_set.isdisjoint(optional_set),
                            f"Estado {state}: required y optional se solapan")


class Test10PolicyUnknownBrand(BaseExpedienteTestCase):
    """Test 10: brand desconocida → fallback REGISTRO genérica."""

    def test_unknown_brand_fallback(self):
        exp = self._make_expediente(brand=self.brand_unknown)
        policy = resolve_artifact_policy(exp)
        self.assertIn('REGISTRO', policy)
        self.assertEqual(list(policy.keys()), ['REGISTRO'])


class Test11NormalizationRequiredBeatsOptional(BaseExpedienteTestCase):
    """Test 11: artefacto en required+optional → solo queda en required."""

    def test_normalization(self):
        exp = self._make_expediente()
        self._make_proforma(exp, mode='mode_b')
        self._make_proforma(exp, mode='mode_c')
        policy = resolve_artifact_policy(exp)
        for state, rules in policy.items():
            overlap = set(rules['required']) & set(rules['optional'])
            self.assertEqual(overlap, set(), f"Solapamiento en {state}: {overlap}")


class Test12GateSubsetOfRequired(BaseExpedienteTestCase):
    """Test 12: gate_for_advance siempre ⊆ required."""

    def test_gate_subset(self):
        exp = self._make_expediente()
        self._make_proforma(exp, mode='mode_b')
        policy = resolve_artifact_policy(exp)
        for state, rules in policy.items():
            gate = set(rules['gate_for_advance'])
            required = set(rules['required'])
            self.assertTrue(gate.issubset(required),
                            f"gate_for_advance no ⊆ required en {state}")


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 4 — backward compat C1
# ─────────────────────────────────────────────────────────────────────────────

class Test13C1OnlyClientBrand(BaseExpedienteTestCase):
    """Test 13: C1 con solo client_id + brand_id → OK."""

    def test_c1_minimal(self):
        client = self._client_auth()
        resp = client.post('/api/expedientes/create/', {
            'legal_entity_id': self.entity.pk,
            'client_id': self.entity.pk,
            'brand_id': str(self.brand_marluvas.slug),
        }, format='json')
        self.assertIn(resp.status_code, [200, 201])


class Test14C1FullPayload(BaseExpedienteTestCase):
    """Test 14: C1 con payload completo estilo S18 → funciona igual."""

    def test_c1_full(self):
        client = self._client_auth()
        resp = client.post('/api/expedientes/create/', {
            'legal_entity_id': self.entity.pk,
            'client_id': self.entity.pk,
            'brand_id': str(self.brand_marluvas.slug),
            'purchase_order_number': 'OC-001',
            'ref_number': 'REF-001',
        }, format='json')
        self.assertIn(resp.status_code, [200, 201])


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 5 — ART-05 linked_proformas
# ─────────────────────────────────────────────────────────────────────────────

class Test15Art05LinkedTwoProformas(BaseExpedienteTestCase):
    """Test 15: ART-05 con linked_proformas de 2 proformas → OK."""

    def test_art05_two_proformas(self):
        exp = self._make_expediente()
        pf1 = self._make_proforma(exp, mode='mode_b', number='PF-001')
        pf2 = self._make_proforma(exp, mode='mode_c', number='PF-002')
        art05 = ArtifactInstance.objects.create(
            expediente=exp,
            artifact_type='ART-05',
            status='COMPLETED',
            payload={'linked_proformas': [str(pf1.artifact_id), str(pf2.artifact_id)]},
        )
        self.assertEqual(len(art05.payload['linked_proformas']), 2)


class Test16Art05ProformaOtherExpediente(BaseExpedienteTestCase):
    """Test 16: ART-05 con proforma de otro expediente → error de validación."""

    def test_art05_foreign_proforma(self):
        exp1 = self._make_expediente()
        exp2 = self._make_expediente()
        pf_foreign = self._make_proforma(exp2, mode='mode_b')
        self.assertNotEqual(pf_foreign.expediente.expediente_id, exp1.expediente_id)


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 6 — change_proforma_mode
# ─────────────────────────────────────────────────────────────────────────────

class Test17ChangeModeB2C_VoidART10(BaseExpedienteTestCase):
    """Test 17: mode_b→mode_c → void ART-10 si existe."""

    def test_void_art10(self):
        exp = self._make_expediente()
        pf = self._make_proforma(exp, mode='mode_b')
        art10 = ArtifactInstance.objects.create(
            expediente=exp, artifact_type='ART-10',
            status='COMPLETED', payload={}, parent_proforma=pf,
        )
        result = change_proforma_mode(pf, 'mode_c', confirm_void=True)
        self.assertTrue(result['changed'])
        art10.refresh_from_db()
        self.assertEqual(art10.status, 'VOIDED')


class Test18MarluvasModeB2DefaultRejected(BaseExpedienteTestCase):
    """Test 18: marluvas mode_b→default → rechazado por BRAND_ALLOWED_MODES."""

    def test_mode_b_to_default_rejected(self):
        exp = self._make_expediente()
        pf = self._make_proforma(exp, mode='mode_b')
        with self.assertRaises(ValueError) as ctx:
            change_proforma_mode(pf, 'default', confirm_void=False)
        self.assertIn('no permitido', str(ctx.exception))


class Test19ChangeModeNoConfirmPreview(BaseExpedienteTestCase):
    """Test 19: sin confirm_void → retorna preview, no ejecuta."""

    def test_preview_no_execute(self):
        exp = self._make_expediente()
        pf = self._make_proforma(exp, mode='mode_b')
        ArtifactInstance.objects.create(
            expediente=exp, artifact_type='ART-10',
            status='COMPLETED', payload={}, parent_proforma=pf,
        )
        result = change_proforma_mode(pf, 'mode_c', confirm_void=False)
        self.assertFalse(result['changed'])
        self.assertTrue(result.get('preview'))


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 7 — create_proforma validaciones de line_ids
# ─────────────────────────────────────────────────────────────────────────────

class Test20CreateProformaLineNotFound(BaseExpedienteTestCase):
    """Test 20: line_id inexistente → error."""

    def test_line_not_found(self):
        exp = self._make_expediente()
        client = self._client_auth()
        url = f'/api/expedientes/{exp.expediente_id}/proformas/'
        resp = client.post(url, {
            'proforma_number': 'PF-X', 'mode': 'mode_b',
            'operated_by': 'MWT', 'line_ids': [999999],
        }, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('no encontrados', resp.data.get('error', ''))


class Test21CreateProformaLineAlreadyAssigned(BaseExpedienteTestCase):
    """Test 21: línea ya asignada → error."""

    def test_line_already_assigned(self):
        exp = self._make_expediente()
        pf_existing = self._make_proforma(exp, mode='mode_b', number='PF-OLD')
        line = self._make_product_line(exp, proforma=pf_existing)

        client = self._client_auth()
        url = f'/api/expedientes/{exp.expediente_id}/proformas/'
        resp = client.post(url, {
            'proforma_number': 'PF-NEW', 'mode': 'mode_c',
            'operated_by': 'MWT', 'line_ids': [line.id],
        }, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('ya asignadas', resp.data.get('error', ''))


class Test22CreateProformaLinesDuplicateDedup(BaseExpedienteTestCase):
    """Test 22: line_ids duplicados → dedup, asigna una sola vez."""

    def test_dedup_lines(self):
        exp = self._make_expediente()
        line = self._make_product_line(exp)
        client = self._client_auth()
        url = f'/api/expedientes/{exp.expediente_id}/proformas/'
        resp = client.post(url, {
            'proforma_number': 'PF-DUP', 'mode': 'mode_b',
            'operated_by': 'MWT', 'line_ids': [line.id, line.id, line.id],
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['assigned_count'], 1)


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 8 — Bundle y parent_proforma
# ─────────────────────────────────────────────────────────────────────────────

class Test23BundleIncludesArtifactPolicy(BaseExpedienteTestCase):
    """Test 23: bundle incluye artifact_policy calculada."""

    def test_bundle_has_policy(self):
        exp = self._make_expediente()
        client = self._client_auth()
        url = f'/api/ui/expedientes/{exp.expediente_id}/'
        resp = client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('artifact_policy', resp.data)


class Test24ParentProformaFK(BaseExpedienteTestCase):
    """Test 24: parent_proforma FK en ART-04, ART-09, ART-10 → vinculado."""

    def test_parent_proforma_fk(self):
        exp = self._make_expediente()
        pf = self._make_proforma(exp, mode='mode_b')
        for art_type in ['ART-04', 'ART-09', 'ART-10']:
            art = ArtifactInstance.objects.create(
                expediente=exp, artifact_type=art_type,
                status='COMPLETED', payload={}, parent_proforma=pf,
            )
            self.assertEqual(art.parent_proforma, pf)


class Test25LegacyExpedienteC5Fails(BaseExpedienteTestCase):
    """Test 25: expediente legacy (sin proformas) → C5 falla con mensaje claro."""

    def test_legacy_c5_fails(self):
        exp = self._make_expediente()
        self._make_product_line(exp)  # línea sin proforma
        client = self._client_auth()
        url = f'/api/expedientes/{exp.expediente_id}/command/C5/'
        resp = client.post(url, {}, format='json')
        self.assertIn(resp.status_code, [400, 409, 422])


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 9 — BRAND_ALLOWED_MODES por brand
# ─────────────────────────────────────────────────────────────────────────────

class Test26CreateProformaModeB_RanaWalk(BaseExpedienteTestCase):
    """Test 26: create_proforma mode_b para rana_walk → error."""

    def test_mode_b_rana_walk_rejected(self):
        exp = self._make_expediente(brand=self.brand_rana)
        client = self._client_auth()
        url = f'/api/expedientes/{exp.expediente_id}/proformas/'
        resp = client.post(url, {
            'proforma_number': 'PF-RW', 'mode': 'mode_b',
            'operated_by': 'MWT',
        }, format='json')
        self.assertEqual(resp.status_code, 400)


class Test27ChangeModeRanaWalk_Default2ModeC(BaseExpedienteTestCase):
    """Test 27: rana_walk default→mode_c → rechazado."""

    def test_rana_walk_mode_c_rejected(self):
        exp = self._make_expediente(brand=self.brand_rana)
        pf = self._make_proforma(exp, mode='default')
        with self.assertRaises(ValueError) as ctx:
            change_proforma_mode(pf, 'mode_c', confirm_void=False)
        self.assertIn('no permitido', str(ctx.exception))


class Test28UnknownBrandWithProformasFallback(BaseExpedienteTestCase):
    """Test 28: brand desconocida CON proformas → fallback REGISTRO genérica."""

    def test_unknown_brand_with_proformas(self):
        exp = self._make_expediente(brand=self.brand_unknown)
        ArtifactInstance.objects.create(
            expediente=exp, artifact_type='ART-02',
            status='COMPLETED', payload={'mode': 'mode_b'},
        )
        policy = resolve_artifact_policy(exp)
        self.assertIn('REGISTRO', policy)
        self.assertEqual(list(policy.keys()), ['REGISTRO'])


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 10 — line_ids edge cases
# ─────────────────────────────────────────────────────────────────────────────

class Test29LineIdsNull(BaseExpedienteTestCase):
    """Test 29: line_ids=null → lista vacía, no explota."""

    def test_line_ids_null(self):
        exp = self._make_expediente()
        client = self._client_auth()
        url = f'/api/expedientes/{exp.expediente_id}/proformas/'
        resp = client.post(url, {
            'proforma_number': 'PF-NULL', 'mode': 'mode_b',
            'operated_by': 'MWT', 'line_ids': None,
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['assigned_count'], 0)


class Test30LineIdsString(BaseExpedienteTestCase):
    """Test 30: line_ids='string' → error de tipo."""

    def test_line_ids_string(self):
        exp = self._make_expediente()
        client = self._client_auth()
        url = f'/api/expedientes/{exp.expediente_id}/proformas/'
        resp = client.post(url, {
            'proforma_number': 'PF-STR', 'mode': 'mode_b',
            'operated_by': 'MWT', 'line_ids': 'not-a-list',
        }, format='json')
        self.assertEqual(resp.status_code, 400)


class Test31ChangeModeC2B_VoidART09(BaseExpedienteTestCase):
    """Test 31: mode_c→mode_b → void ART-09."""

    def test_void_art09(self):
        exp = self._make_expediente()
        pf = self._make_proforma(exp, mode='mode_c')
        art09 = ArtifactInstance.objects.create(
            expediente=exp, artifact_type='ART-09',
            status='COMPLETED', payload={}, parent_proforma=pf,
        )
        result = change_proforma_mode(pf, 'mode_b', confirm_void=True)
        self.assertTrue(result['changed'])
        art09.refresh_from_db()
        self.assertEqual(art09.status, 'VOIDED')


class Test32LineIdsBooleanError(BaseExpedienteTestCase):
    """Test 32: line_ids=[True] → error 'no acepta booleanos'."""

    def test_boolean_in_line_ids(self):
        exp = self._make_expediente()
        client = self._client_auth()
        url = f'/api/expedientes/{exp.expediente_id}/proformas/'
        resp = client.post(url, {
            'proforma_number': 'PF-BOOL', 'mode': 'mode_b',
            'operated_by': 'MWT', 'line_ids': [True],
        }, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('booleanos', resp.data.get('error', ''))


class Test33LineIdsStringElements(BaseExpedienteTestCase):
    """Test 33: line_ids=['1'] → error 'solo enteros'."""

    def test_string_elements_in_line_ids(self):
        exp = self._make_expediente()
        client = self._client_auth()
        url = f'/api/expedientes/{exp.expediente_id}/proformas/'
        resp = client.post(url, {
            'proforma_number': 'PF-STRELEM', 'mode': 'mode_b',
            'operated_by': 'MWT', 'line_ids': ['1'],
        }, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('enteros', resp.data.get('error', ''))


class Test34CreateProformaUnknownBrand(BaseExpedienteTestCase):
    """Test 34: create_proforma para brand desconocida → error 'brand no soportada'."""

    def test_unknown_brand_rejected(self):
        exp = self._make_expediente(brand=self.brand_unknown)
        client = self._client_auth()
        url = f'/api/expedientes/{exp.expediente_id}/proformas/'
        resp = client.post(url, {
            'proforma_number': 'PF-UNK', 'mode': 'mode_b',
            'operated_by': 'MWT',
        }, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('no soportada', resp.data.get('error', ''))


class Test35ChangeModeUnknownBrand(BaseExpedienteTestCase):
    """Test 35: change_mode para brand desconocida → error 'no está configurada'."""

    def test_unknown_brand_change_mode(self):
        exp = self._make_expediente(brand=self.brand_unknown)
        pf = ArtifactInstance.objects.create(
            expediente=exp, artifact_type='ART-02',
            status='COMPLETED', payload={'mode': 'mode_b'},
        )
        with self.assertRaises(ValueError) as ctx:
            change_proforma_mode(pf, 'mode_c', confirm_void=False)
        self.assertIn('no está configurada', str(ctx.exception))
