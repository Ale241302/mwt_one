from django.test import TestCase
from .models import SizeSystem, SizeDimension, SizeEntry, SizeEntryValue, SizeEquivalence
from .services import validate_entry_completeness
from django.core.exceptions import ValidationError


class SizeSystemModelTest(TestCase):
    def setUp(self):
        self.system = SizeSystem.objects.create(
            code='TEST_SYS', category='FOOTWEAR'
        )
        self.dim_eu = SizeDimension.objects.create(
            system=self.system, code='EU', display_name='EU Size',
            unit='', display_order=1, is_primary=True
        )
        self.dim_cm = SizeDimension.objects.create(
            system=self.system, code='CM', display_name='Centimeters',
            unit='cm', display_order=2
        )

    def test_size_entry_unique_together(self):
        SizeEntry.objects.create(system=self.system, label='42', display_order=1)
        with self.assertRaises(Exception):
            SizeEntry.objects.create(system=self.system, label='42', display_order=2)

    def test_validate_entry_completeness_ok(self):
        entry = SizeEntry.objects.create(system=self.system, label='43', display_order=2)
        SizeEntryValue.objects.create(entry=entry, dimension=self.dim_eu, value='43')
        SizeEntryValue.objects.create(entry=entry, dimension=self.dim_cm, value='27.5')
        validate_entry_completeness(entry)  # no debe lanzar

    def test_validate_entry_completeness_missing(self):
        entry = SizeEntry.objects.create(system=self.system, label='44', display_order=3)
        SizeEntryValue.objects.create(entry=entry, dimension=self.dim_eu, value='44')
        # Falta dim_cm
        with self.assertRaises(ValidationError):
            validate_entry_completeness(entry)

    def test_size_entry_value_cross_system_raises(self):
        other_system = SizeSystem.objects.create(code='OTHER', category='SHIRT')
        other_dim = SizeDimension.objects.create(
            system=other_system, code='XS', display_name='XS',
            unit='', display_order=1
        )
        entry = SizeEntry.objects.create(system=self.system, label='S1', display_order=1)
        sev = SizeEntryValue(entry=entry, dimension=other_dim, value='test')
        with self.assertRaises(ValidationError):
            sev.clean()
