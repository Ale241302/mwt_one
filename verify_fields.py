import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from apps.expedientes.models import Expediente, CostLine
from apps.expedientes.enums import CostCategory, CostBehavior, AforoType

print("Checking Expediente fields...")
e = Expediente()
print(f"external_fiscal_refs exists: {hasattr(e, 'external_fiscal_refs')}")
print(f"aforo_type exists: {hasattr(e, 'aforo_type')}")
print(f"aforo_date exists: {hasattr(e, 'aforo_date')}")

print("\nChecking CostLine fields...")
c = CostLine()
print(f"category exists: {hasattr(c, 'category')}")
print(f"behavior exists: {hasattr(c, 'behavior')}")
print(f"exchange_rate exists: {hasattr(c, 'exchange_rate')}")
print(f"amount_base_currency exists: {hasattr(c, 'amount_base_currency')}")
print(f"base_currency exists: {hasattr(c, 'base_currency')}")

print("\nVerifying Enum values...")
print(f"CostCategory.LANDED_COST: {CostCategory.LANDED_COST}")
print(f"AforoType.VERDE: {AforoType.VERDE}")
