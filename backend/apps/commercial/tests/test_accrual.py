import threading
from decimal import Decimal
from datetime import date
from django.test import TestCase, TransactionTestCase
from django.db import IntegrityError
from apps.commercial.models import (
    RebateProgram, RebateAssignment, RebateLedger, RebateAccrualEntry
)
from apps.commercial.services.rebates import calculate_rebate_accrual
from apps.brands.models import Brand
from apps.clients.models import Client, Subsidiary
from apps.proformas.models import Proforma


class TestAccrualT5(TestCase):
    """T5: calculate_rebate_accrual()"""

    def setUp(self):
        self.brand = Brand.objects.create(name="BrandAccrual")
        self.client = Client.objects.create(name="ClientAccrual", brand=self.brand)
        self.subsidiary = Subsidiary.objects.create(name="SubAccrual", client=self.client)
        self.program = RebateProgram.objects.create(
            brand=self.brand,
            name="Accrual Program",
            period_type="quarterly",
            valid_from=date(2026, 1, 1),
            valid_to=date(2026, 3, 31),
            rebate_type="percentage",
            rebate_value=Decimal("10.00"),
            threshold_type="amount",
            threshold_amount=Decimal("5000.00"),
            calculation_base="invoiced",
        )
        self.assignment = RebateAssignment.objects.create(
            rebate_program=self.program, client=self.client
        )
        self.ledger = RebateLedger.objects.create(
            rebate_assignment=self.assignment,
            period_start=date(2026, 1, 1),
            period_end=date(2026, 3, 31),
            status="accruing",
        )
        self.proforma = Proforma.objects.create(
            client=self.client,
            total_amount=Decimal("6000.00"),
        )

    def test_t5a_basic_accrual_invoiced(self):
        result = calculate_rebate_accrual(
            ledger=self.ledger, proforma=self.proforma
        )
        self.assertGreater(result["qualifying_amount"], Decimal("0"))
        self.assertGreater(result["accrued_amount"], Decimal("0"))
        self.assertIn("threshold_met", result)

    def test_t5b_accrual_list_price(self):
        self.program.calculation_base = "list_price"
        self.program.save()
        result = calculate_rebate_accrual(
            ledger=self.ledger, proforma=self.proforma
        )
        self.assertIn("accrued_amount", result)

    def test_t5c_idempotency(self):
        calculate_rebate_accrual(ledger=self.ledger, proforma=self.proforma)
        result2 = calculate_rebate_accrual(ledger=self.ledger, proforma=self.proforma)
        self.assertTrue(result2["was_idempotent"])

    def test_t5d_calculation_base_none_raises_value_error(self):
        self.program.calculation_base = None
        self.program.save()
        with self.assertRaises(ValueError) as ctx:
            calculate_rebate_accrual(ledger=self.ledger, proforma=self.proforma)
        self.assertIn("DEC-S23-01", str(ctx.exception))

    def test_t5e_ledger_not_accruing_raises_value_error(self):
        self.ledger.status = "pending_review"
        self.ledger.save()
        with self.assertRaises(ValueError):
            calculate_rebate_accrual(ledger=self.ledger, proforma=self.proforma)


class TestAccrualConcurrentT5F(TransactionTestCase):
    """T5-f: select_for_update prevents race conditions"""

    def setUp(self):
        self.brand = Brand.objects.create(name="BrandConcurrent")
        self.client = Client.objects.create(name="ClientConcurrent", brand=self.brand)
        self.subsidiary = Subsidiary.objects.create(name="SubConcurrent", client=self.client)
        self.program = RebateProgram.objects.create(
            brand=self.brand,
            name="Concurrent Program",
            period_type="quarterly",
            valid_from=date(2026, 1, 1),
            valid_to=date(2026, 3, 31),
            rebate_type="percentage",
            rebate_value=Decimal("10.00"),
            threshold_type="none",
            calculation_base="invoiced",
        )
        self.assignment = RebateAssignment.objects.create(
            rebate_program=self.program, client=self.client
        )
        self.ledger = RebateLedger.objects.create(
            rebate_assignment=self.assignment,
            period_start=date(2026, 1, 1),
            period_end=date(2026, 3, 31),
            status="accruing",
        )

    def test_t5f_concurrent_accrual_no_race_condition(self):
        proforma1 = Proforma.objects.create(client=self.client, total_amount=Decimal("1000.00"))
        proforma2 = Proforma.objects.create(client=self.client, total_amount=Decimal("2000.00"))
        errors = []

        def run_accrual(pf):
            try:
                calculate_rebate_accrual(ledger=self.ledger, proforma=pf)
            except Exception as e:
                errors.append(e)

        t1 = threading.Thread(target=run_accrual, args=(proforma1,))
        t2 = threading.Thread(target=run_accrual, args=(proforma2,))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.assertEqual(len(errors), 0)
        entries = RebateAccrualEntry.objects.filter(ledger=self.ledger)
        self.assertEqual(entries.count(), 2)
