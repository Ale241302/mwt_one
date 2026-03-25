import pytest
from decimal import Decimal
from django.utils import timezone
from apps.core.models import LegalEntity
from apps.brands.models import Brand
from apps.agreements.models import CreditPolicy, CreditExposure, CreditOverride
from apps.users.models import MWTUser, UserRole
from apps.expedientes.models import Expediente
from apps.expedientes.services.commands.c1 import handle_c1

@pytest.mark.django_db
class TestCreditReservation:
    def setup_method(self):
        self.le = LegalEntity.objects.create(name="Test Client", entity_id="TEST-LE")
        self.brand = Brand.objects.create(name="Test Brand", slug="test-brand")
        self.ceo = MWTUser.objects.create(username="ceo", role=UserRole.CEO)
        
        # Setup Credit Policy: Max 1000 USD
        self.policy = CreditPolicy.objects.create(
            brand=self.brand,
            subject_type='subsidiary',
            subject_id=self.le.id,
            max_amount=Decimal('1000.00'),
            currency='USD',
            status='active'
        )
        self.exposure = CreditExposure.calculate(self.brand, 'subsidiary', self.le.id)

    def test_c1_success_sufficient_credit(self):
        """1. C1 successful with sufficient credit."""
        payload = {
            'entity_id': self.le.entity_id,
            'brand': self.brand.slug,
            'mode': 'IMPORT',
            'estimated_amount': 500
        }
        exp = handle_c1(self.ceo, payload)
        assert exp.credit_blocked == Decimal('500.00')
        assert exp.credit_warning == Decimal('0.00')

    def test_c1_fails_insufficient_credit(self):
        """2. C1 fails with insufficient credit."""
        payload = {
            'entity_id': self.le.entity_id,
            'brand': self.brand.slug,
            'mode': 'IMPORT',
            'estimated_amount': 1500
        }
        with pytest.raises(Exception, match="Insufficient credit"):
            handle_c1(self.ceo, payload)

    def test_c1_success_with_override(self):
        """3. C1 successful with insufficient credit BUT existing CEO Override."""
        # Pre-create Expediente (simulating partial creation if needed, or using a dry run)
        # For simplicity, we create one and then try to C1 it or just test the logic
        # In this system, C1 creates the expediente. To have an override, it must exist.
        # This implies override is for ALREADY created but blocked or re-trying.
        # But C1 is the registry. Let's assume the override is registered for the external_id or similar.
        # Actually, check_and_reserve_credit checks hasattr(expediente, 'credit_override').
        
        # Scenario: Create blocked expediente (if we allowed it) or inject override.
        exp = Expediente.objects.create(
            legal_entity=self.le,
            client=self.le,
            brand=self.brand,
            mode='IMPORT'
        )
        CreditOverride.objects.create(
            expediente=exp,
            approved_by=self.ceo,
            amount=Decimal('1500.00'),
            reason="Market expansion"
        )
        
        # We test the helper directly as handle_c1 creates NEW expediente
        from apps.expedientes.services.commands.c1 import check_and_reserve_credit
        assert check_and_reserve_credit(exp, Decimal('1500.00')) is True

    def test_credit_blocked_correctly_set(self):
        """4. C1 sets credit_blocked correctly."""
        payload = {
            'entity_id': self.le.entity_id,
            'brand': self.brand.slug,
            'mode': 'IMPORT',
            'estimated_amount': 250.50
        }
        exp = handle_c1(self.ceo, payload)
        assert exp.credit_blocked == Decimal('250.50')

    def test_c1_triggers_warning_at_80_percent(self):
        """5. C1 triggers a warning if over credit_warning (80% threshold)."""
        payload = {
            'entity_id': self.le.entity_id,
            'brand': self.brand.slug,
            'mode': 'IMPORT',
            'estimated_amount': 850 # 85% of 1000
        }
        exp = handle_c1(self.ceo, payload)
        assert exp.credit_blocked == Decimal('850.00')
        assert exp.credit_warning == Decimal('800.00') # 80% of 1000

    def test_credit_bypass_for_non_import_modes(self):
        """6. Credit reservation works for different modes (EXPORT should bypass)."""
        payload = {
            'entity_id': self.le.entity_id,
            'brand': self.brand.slug,
            'mode': 'EXPORT',
            'estimated_amount': 5000 # High amount, would fail if IMPORT
        }
        exp = handle_c1(self.ceo, payload)
        assert exp.credit_blocked == Decimal('0.00') # Not blocked in EXPORT mode

    def test_sequential_credit_consumption(self):
        """7. Concurrent (sequential) C1 requests correctly handle credit pool."""
        # Request 1: 600
        handle_c1(self.ceo, {
            'entity_id': self.le.entity_id,
            'brand': self.brand.slug,
            'mode': 'IMPORT',
            'estimated_amount': 600
        })
        
        # Request 2: 500 (Total 1100 > 1000) -> Should fail
        with pytest.raises(Exception, match="Insufficient credit"):
            handle_c1(self.ceo, {
                'entity_id': self.le.entity_id,
                'brand': self.brand.slug,
                'mode': 'IMPORT',
                'estimated_amount': 500
            })
