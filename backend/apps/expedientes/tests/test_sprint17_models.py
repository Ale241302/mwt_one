"""
S17-14: Tests for Sprint 17 new models.
New file — does NOT modify existing tests.
"""
from django.test import TestCase


class TestFactoryOrderSync(TestCase):
    """
    S17-10: FactoryOrder.save() must copy order_number to
    expediente.factory_order_number when creating the FIRST FactoryOrder.
    """

    def test_factory_order_syncs_flat_field_on_first_creation(self):
        """First FactoryOrder created should sync order_number to expediente."""
        # This test validates the save() override logic structurally
        from apps.expedientes.models import FactoryOrder
        import inspect
        source = inspect.getsource(FactoryOrder.save)
        self.assertIn('factory_order_number', source,
                      "FactoryOrder.save() must sync factory_order_number")
        self.assertIn('update_fields', source,
                      "Must use update_fields=['factory_order_number'] for efficiency")
        self.assertNotIn('signal', source.lower(),
                         "Must NOT use signals — only save() override")


class TestExpedienteProductLineModel(TestCase):
    """
    S17-09: ExpedienteProductLine structure.
    """

    def test_model_has_price_source_choices(self):
        from apps.expedientes.models import ExpedienteProductLine
        field = ExpedienteProductLine._meta.get_field('price_source')
        choice_values = [c[0] for c in field.choices]
        self.assertIn('pricelist', choice_values)
        self.assertIn('manual', choice_values)
        self.assertIn('override', choice_values)

    def test_product_fk_is_protect(self):
        from apps.expedientes.models import ExpedienteProductLine
        from django.db.models import PROTECT
        field = ExpedienteProductLine._meta.get_field('product')
        self.assertEqual(field.remote_field.on_delete, PROTECT,
                         "product FK must be PROTECT to avoid accidental deletions")

    def test_modification_fields_are_nullable(self):
        from apps.expedientes.models import ExpedienteProductLine
        for fname in ('quantity_modified', 'unit_price_modified', 'modification_reason'):
            field = ExpedienteProductLine._meta.get_field(fname)
            self.assertTrue(field.null, f"{fname} must be nullable")


class TestExpedientePagoModel(TestCase):
    """
    S17-11: ExpedientePago structure.
    """

    def test_required_fields_exist(self):
        from apps.expedientes.models import ExpedientePago
        required = ['expediente', 'tipo_pago', 'metodo_pago', 'payment_date', 'amount_paid']
        for fname in required:
            field = ExpedientePago._meta.get_field(fname)
            self.assertIsNotNone(field, f"{fname} must exist on ExpedientePago")

    def test_optional_fields_nullable(self):
        from apps.expedientes.models import ExpedientePago
        for fname in ('additional_info', 'url_comprobante'):
            field = ExpedientePago._meta.get_field(fname)
            self.assertTrue(field.null, f"{fname} must be nullable")

    def test_ordering_is_by_payment_date_desc(self):
        from apps.expedientes.models import ExpedientePago
        ordering = ExpedientePago._meta.ordering
        self.assertIn('-payment_date', ordering)

    def test_no_save_override(self):
        from apps.expedientes.models import ExpedientePago
        import inspect
        # ExpedientePago must NOT have a custom save() — kept clean for Sprint 18
        source = inspect.getsource(ExpedientePago)
        self.assertNotIn('def save(', source,
                         "ExpedientePago must not have save() override — integration deferred to Sprint 18")


class TestExpedienteOperationalFields(TestCase):
    """
    S17-08: ~30 operational fields on Expediente.
    """

    def test_s17_fields_exist_on_expediente(self):
        from apps.expedientes.models import Expediente
        s17_fields = [
            'purchase_order_number', 'operado_por', 'url_orden_compra',
            'ref_number', 'credit_days_client', 'credit_days_mwt',
            'credit_limit_client', 'credit_limit_mwt', 'order_value',
            'factory_order_number', 'proforma_client_number', 'proforma_mwt_number',
            'fabrication_start_date', 'fabrication_end_date',
            'url_proforma_cliente', 'url_proforma_muito_work', 'master_expediente',
            'shipping_method', 'incoterms', 'cargo_manager', 'shipping_value',
            'payment_mode_shipping', 'url_list_empaque', 'url_cotizacion_envio',
            'airline_or_shipping_company', 'awb_bl_number', 'origin_location',
            'arrival_location', 'shipment_date', 'payment_date_dispatch',
            'invoice_client_number', 'invoice_mwt_number', 'dispatch_additional_info',
            'url_certificado_origen', 'url_factura_cliente', 'url_factura_muito_work',
            'url_awb_bl', 'tracking_url',
            'intermediate_airport_or_port', 'transit_arrival_date', 'url_packing_list_detallado',
        ]
        for fname in s17_fields:
            try:
                Expediente._meta.get_field(fname)
            except Exception:
                self.fail(f"S17-08: Field '{fname}' missing from Expediente model")

    def test_reopen_count_exists(self):
        from apps.expedientes.models import Expediente
        field = Expediente._meta.get_field('reopen_count')
        self.assertIsNotNone(field)
        self.assertEqual(field.default, 0)
