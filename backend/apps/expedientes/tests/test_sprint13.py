from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.conf import settings

from apps.expedientes.models import LegalEntity, Expediente, CostLine, EventLog, ArtifactInstance
from apps.expedientes.enums_exp import (
    CostCategory, CostBehavior, AforoType, ArtifactType, AggregateType
)
from apps.expedientes.services.financial import handle_c15
from apps.expedientes.services.commands_registro import handle_c4, pre_check_viability

class Sprint13Tests(TestCase):
    def setUp(self):
        settings.DAI_RATES = {'6403.99.90': {'CR': Decimal('0.14')}}
        settings.VIABILITY_FLETE_PCT = Decimal('0.05')
        
        self.entity = LegalEntity.objects.create(entity_id="E1", legal_name="Entity 1", role='OWNER')
        self.client = LegalEntity.objects.create(entity_id="C1", legal_name="Client 1", role='ONBOARDING')
        
        self.expediente = Expediente.objects.create(
            legal_entity=self.entity,
            client=self.client,
            destination='CR'
        )
        self.expediente.partida_arancelaria = '6403.99.90'

    def test_costline_currency_usd_default(self):
        handle_c15(self.expediente, {
            'amount': '100.00',
            'currency': 'USD',
            'cost_type': 'Flete'
        })
        cost = CostLine.objects.first()
        self.assertEqual(cost.exchange_rate, Decimal('1.000000'))
        self.assertEqual(cost.amount_base_currency, Decimal('100.00'))

    def test_costline_currency_eur_convert(self):
        handle_c15(self.expediente, {
            'amount': '100.00',
            'currency': 'EUR',
            'exchange_rate': '1.100000'
        })
        cost = CostLine.objects.last()
        self.assertEqual(cost.exchange_rate, Decimal('1.100000'))
        self.assertEqual(cost.amount_base_currency, Decimal('110.00'))

    def test_handle_c4_viability_full(self):
        # First, create 5 fixed costs for avg calculation
        for i in range(5):
            CostLine.objects.create(cost_behavior=CostBehavior.FIXED_PER_OPERATION, amount=Decimal('100.0'))
            
        result = handle_c4(self.expediente, {
            'mode': 'FULL',
            'fob_mwt': '10.00',
            'fob_cliente': '12.00',
            'qty': '100'
        })
        # 100 fixed / 100 qty = 1 fixed
        # Landed Est = 10 * 1.05 * 1.14 + 1 = 11.97 + 1 = 12.97
        # 12.97 > 12.00 -> delta = 0.97
        viab = result.get('viability_check')
        self.assertIsNotNone(viab)
        self.assertTrue(viab['warning'])
        self.assertFalse(viab['degraded'])
        self.assertAlmostEqual(viab['delta_per_unit'], 0.97)

    def test_handle_c4_missing_config(self):
        del settings.DAI_RATES
        result = handle_c4(self.expediente, {'mode': 'FULL', 'fob_mwt': '10', 'fob_cliente': '12', 'qty': '1'})
        viab = result.get('viability_check')
        self.assertTrue(viab['warning'])
        self.assertTrue(viab['degraded'])
        self.assertIn('lookup_arancelario', viab['missing_inputs'])
        
    def test_handle_c4_comision_no_viability(self):
        result = handle_c4(self.expediente, {'mode': 'COMISION'})
        self.assertEqual(result, {})
        
    def test_enums_sprint13(self):
        self.assertEqual(AforoType.VERDE, 'verde')
        self.assertEqual(CostCategory.LANDED_COST, 'landed_cost')
        self.assertEqual(CostCategory.TAX_CREDIT, 'tax_credit')
        self.assertEqual(CostBehavior.FIXED_PER_OPERATION, 'fixed_per_operation')
        self.assertEqual(ArtifactType.CERTIFICATE_OF_ORIGIN, 'certificate_of_origin')
        self.assertEqual(ArtifactType.DUE_EXPORT_BR, 'due_export_br')

    def test_expediente_new_fields(self):
        self.expediente.aforo_type = AforoType.VERDE
        self.expediente.aforo_date = timezone.now().date()
        self.expediente.save()
        
        self.assertEqual(self.expediente.external_fiscal_refs, [])
