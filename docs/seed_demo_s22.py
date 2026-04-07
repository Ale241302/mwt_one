"""
seed_demo_s22.py
MWT / Rana Walk — Demo Data Seed hasta Sprint 22
=================================================
Adaptado a los modelos reales del proyecto (Ale241302/mwt_one).

PROPÓSITO:
  Poblar la BD con datos simulados coherentes con la arquitectura real.
  Cubre todos los Django apps implementados hasta Sprint 22.

USO:
  # Desde la raíz del backend (donde está manage.py):
  python manage.py shell < seed_demo_s22.py

  # O como script directo:
  DJANGO_SETTINGS_MODULE=config.settings.local python seed_demo_s22.py

APPS CUBIERTAS (S1→S22):
  core (LegalEntity) · users (MWTUser) · brands (Brand/BrandSKU) ·
  clientes (Cliente) · productos (ProductMaster) · suppliers ·
  pricing (PriceList/PriceListVersion/S22 GradeItems) ·
  expedientes (Expediente/EPL/ArtifactInstance/FactoryOrder/CostLine) ·
  liquidations · transfers (Node/Transfer) · inventario ·
  commercial (RebateProgram)

CARACTERÍSTICAS:
  - Datos 100% ficticios — nombres de empresas y montos inventados
  - Idempotente: get_or_create en todo — puede correrse N veces
  - Sigue ENT_OPS_STATE_MACHINE FROZEN para estados de expediente
  - BrandType values: 'own', 'client' (lowercase, del modelo real)
  - ExpedienteStatus: REGISTRO, PRODUCCION, PREPARACION, DESPACHO,
    TRANSITO, EN_DESTINO, CERRADO, CANCELADO
  - ArtifactStatusEnum: DRAFT, COMPLETED, SUPERSEDED, VOID
  - NodeType: owned_warehouse, factory, fba, third_party, fiscal
  - TransferStatus: planned, approved, in_transit, received, reconciled

CREDENCIALES GENERADAS:
  CEO  → demo_ceo / demo1234!
  OPS  → demo_ops / demo1234!
"""

import os
import uuid
from decimal import Decimal
from datetime import datetime, timedelta

# --- Setup Django si se corre directamente ---
if not os.environ.get("DJANGO_SETTINGS_MODULE"):
    # Si no hay settings en el env, intentamos default a local (para desarrollo local)
    # Pero en el contenedor usualmente ya vendrá configurado.
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

import django
try:
    # django.setup() es necesario si se corre como script independiente,
    # pero si se corre vía 'manage.py shell < script.py', Django ya está listo.
    from django.conf import settings
    if not settings.configured:
        django.setup()
except Exception:
    django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone

NOW   = timezone.now()
TODAY = NOW.date()

print("\n" + "=" * 60)
print("MWT DEMO SEED — Sprint 22 (estructura real)")
print("=" * 60)

# ============================================================
# IMPORTS — después de django.setup()
# ============================================================
from apps.core.models import (
    LegalEntity, LegalEntityRole, LegalEntityRelationship,
    LegalEntityFrontend, LegalEntityStatus, TimestampMixin
)
from apps.users.models import MWTUser
from apps.brands.models import Brand, BrandType, BrandSKU, BrandArtifactRule, ArchProfile, DestinationChoices
from apps.clientes.models import Cliente, ClientGroup, ClientUltimateParent, ClientSubsidiary
from apps.productos.models import Producto, ProductMaster
from apps.suppliers.models import Supplier, SupplierContact
from apps.pricing.models import PriceList, PriceListItem, PriceListVersion
from apps.expedientes.models import (
    Expediente, ExpedienteProductLine, ArtifactInstance,
    FactoryOrder, CostLine, PaymentLine, EventLog
)
from apps.expedientes.enums_exp import (
    ExpedienteStatus, DispatchMode, PaymentStatus,
    CreditClockStartRule, AggregateType,
    RegisteredByType, CostLineVisibility, CostCategory, CostBehavior
)
from apps.expedientes.enums_artifacts import ArtifactStatusEnum
from apps.liquidations.models import Liquidation, LiquidationLine
from apps.transfers.models import Node, Transfer, TransferLine
from apps.transfers.enums_exp import NodeType, NodeStatus, LegalContext, TransferStatus
from apps.inventario.models import InventoryEntry
# Commercial models — opcionales si el sprint aún no está migrado
try:
    from apps.commercial.models import RebateProgram
    HAS_COMMERCIAL = True
except ImportError:
    HAS_COMMERCIAL = False
    print("⚠️  Commercial models no encontrados — skip RebateProgram")

# S22 models — opcionales si el sprint aún no está migrado
try:
    from apps.pricing.models import (
        PriceListGradeItem, ClientProductAssignment,
        EarlyPaymentPolicy, EarlyPaymentTier
    )
    HAS_S22 = True
except ImportError:
    HAS_S22 = False
    print("⚠️  S22 pricing models no encontrados — skip GradeItems/CPA/EPP")

User = get_user_model()

# ============================================================
# BLOQUE 1 — LEGAL ENTITIES
# ============================================================
print("\n[1/12] Legal Entities...")

le_mwt_cr, _ = LegalEntity.objects.get_or_create(
    entity_id="MWT-CR",
    defaults=dict(
        legal_name="Muito Work Limitada",
        country="CR",
        tax_id="3102123456",
        role=LegalEntityRole.OWNER,
        relationship_to_mwt=LegalEntityRelationship.SELF,
        frontend=LegalEntityFrontend.MWT_ONE,
        status=LegalEntityStatus.ACTIVE,
    )
)

le_mwt_usa, _ = LegalEntity.objects.get_or_create(
    entity_id="MWT-USA",
    defaults=dict(
        legal_name="Much Work LLC",
        country="USA",
        tax_id="87-1234567",
        role=LegalEntityRole.OWNER,
        relationship_to_mwt=LegalEntityRelationship.SELF,
        frontend=LegalEntityFrontend.MWT_ONE,
        status=LegalEntityStatus.ACTIVE,
    )
)

le_dist_cr, _ = LegalEntity.objects.get_or_create(
    entity_id="ALTAVERDE-CR",
    defaults=dict(
        legal_name="Distribuciones Altaverde S.A.",
        country="CR",
        tax_id="3101999001",
        role=LegalEntityRole.DISTRIBUTOR,
        relationship_to_mwt=LegalEntityRelationship.DISTRIBUTION,
        frontend=LegalEntityFrontend.PORTAL_MWT_ONE,
        status=LegalEntityStatus.ACTIVE,
    )
)

le_dist2_cr, _ = LegalEntity.objects.get_or_create(
    entity_id="PLENITUD-CR",
    defaults=dict(
        legal_name="Constructora Plenitud Demo S.A.",
        country="CR",
        tax_id="3101999002",
        role=LegalEntityRole.DISTRIBUTOR,
        relationship_to_mwt=LegalEntityRelationship.DISTRIBUTION,
        frontend=LegalEntityFrontend.PORTAL_MWT_ONE,
        status=LegalEntityStatus.ACTIVE,
    )
)

le_factory, _ = LegalEntity.objects.get_or_create(
    entity_id="HORIZONTE-BR",
    defaults=dict(
        legal_name="Calçados Horizonte Ltda. (demo)",
        country="BR",
        tax_id="BR99888777",
        role=LegalEntityRole.FACTORY,
        relationship_to_mwt=LegalEntityRelationship.SERVICE,
        frontend=LegalEntityFrontend.EXTERNAL,
        status=LegalEntityStatus.ACTIVE,
    )
)

print(f"   ✅ {LegalEntity.objects.count()} legal entities")

# ============================================================
# BLOQUE 2 — USERS
# ============================================================
print("\n[2/12] Users...")

ceo_user, created = User.objects.get_or_create(
    username="demo_ceo",
    defaults=dict(
        email="ceo@demo.mwt.local",
        first_name="Carlos",
        last_name="Demo",
        is_staff=True,
        is_superuser=True,
    )
)
if created:
    ceo_user.set_password("demo1234!")
    ceo_user.save()

ops_user, created = User.objects.get_or_create(
    username="demo_ops",
    defaults=dict(
        email="ops@demo.mwt.local",
        first_name="Ana",
        last_name="Ops",
    )
)
if created:
    ops_user.set_password("demo1234!")
    ops_user.save()

print(f"   ✅ {User.objects.count()} users")

# ============================================================
# BLOQUE 3 — BRANDS
# ============================================================
print("\n[3/12] Brands...")

# BrandType values son lowercase en el modelo real: 'own', 'client'
brand_marluvas, _ = Brand.objects.get_or_create(
    slug="marluvas",
    defaults=dict(
        name="Marluvas",
        brand_type=BrandType.CLIENT,   # 'client'
        is_active=True,
        min_margin_alert_pct=Decimal("12.00"),
    )
)

brand_ranawalk, _ = Brand.objects.get_or_create(
    slug="rana_walk",
    defaults=dict(
        name="Rana Walk",
        brand_type=BrandType.OWN,      # 'own'
        is_active=True,
    )
)

brand_tecmater, _ = Brand.objects.get_or_create(
    slug="tecmater",
    defaults=dict(
        name="Tecmater",
        brand_type=BrandType.CLIENT,
        is_active=True,
        min_margin_alert_pct=Decimal("10.00"),
    )
)

# BrandArtifactRules — marluvas: ART-01 obligatorio en todos destinos,
# ART-02 (proforma) obligatorio, ART-05 (embarque) solo CR
for art_type, dest in [
    ("ART-01", DestinationChoices.ALL),
    ("ART-02", DestinationChoices.ALL),
    ("ART-05", DestinationChoices.CR),
]:
    BrandArtifactRule.objects.get_or_create(
        brand=brand_marluvas,
        artifact_type=art_type,
        destination=dest,
        defaults=dict(is_required=True)
    )

# BrandSKUs — marluvas: Goliath (LOW arch) + Bison (HGH arch), tallas 35-44
TALLAS = ["35", "36", "37", "38", "39", "40", "41", "42", "43", "44"]
for size in TALLAS:
    BrandSKU.objects.get_or_create(
        brand=brand_marluvas, product_key="GOL",
        arch=ArchProfile.LOW, size=size,
        defaults=dict(sku_code=f"MAR-GOL-L-{size}")
    )
    BrandSKU.objects.get_or_create(
        brand=brand_marluvas, product_key="BIS",
        arch=ArchProfile.HGH, size=size,  # HGH no HIGH — del enum real
        defaults=dict(sku_code=f"MAR-BIS-H-{size}")
    )

print(f"   ✅ {Brand.objects.count()} brands · {BrandSKU.objects.count()} SKUs · {BrandArtifactRule.objects.count()} rules")

# ============================================================
# BLOQUE 4 — CLIENTES
# ============================================================
print("\n[4/12] Clientes...")

parent_grupo, _ = ClientUltimateParent.objects.get_or_create(
    name="Grupo Vértice (demo)", defaults=dict(country="CR")
)
group_vr, _ = ClientGroup.objects.get_or_create(
    name="Vértice Retail (demo)", defaults=dict(parent=parent_grupo)
)

CLIENTES = [
    dict(name="Ferretería Vértice Demo", email="compras@vertice.demo", country="CR", credit_approved="USD 50,000", legal_entity=le_dist_cr),
    dict(name="Industrial Norteño Demo", email="purchasing@norteno.demo", country="USA", credit_approved="USD 80,000", legal_entity=le_dist_cr),
    dict(name="Equipos Pacífico Demo", email="ops@pacifico.demo", country="CR", credit_approved="USD 20,000", legal_entity=le_dist2_cr),
    dict(name="Constructora Plenitud Demo", email="logistica@plenitud.demo", country="CR", credit_approved="USD 30,000", legal_entity=le_dist2_cr),
]
clientes = []
for data in CLIENTES:
    c, _ = Cliente.objects.get_or_create(
        email=data.pop("email"),
        defaults={**data, "is_active": True}
    )
    clientes.append(c)
    # S22: ClientSubsidiary placeholder para Altaverde
    sub_av, _ = ClientSubsidiary.objects.get_or_create(
        alias="AV-CR-01",
        defaults=dict(group=group_vr, name="Altaverde Principal (demo)", country="CR", legal_entity=le_dist_cr)
    )

print(f"   ✅ {Cliente.objects.count()} clientes · {ClientSubsidiary.objects.count()} subsidiaries")

# ============================================================
# BLOQUE 5 — PRODUCT MASTERS
# ============================================================
print("\n[5/12] ProductMasters...")

# ExpedienteProductLine apunta a ProductMaster (no Producto)
MASTERS = [
    dict(sku_base="MAR-GOL-BASE", brand=brand_marluvas, name="Marluvas Goliath (demo)",
         category="Calzado de Seguridad", hs_code="6402.99",
         weight_kg=Decimal("0.850"), moq=50, uom="PAIR",
         country_of_origin="BR", country_eligibility=["CR","USA"]),
    dict(sku_base="MAR-BIS-BASE", brand=brand_marluvas, name="Marluvas Bison (demo)",
         category="Calzado de Seguridad", hs_code="6402.99",
         weight_kg=Decimal("0.920"), moq=50, uom="PAIR",
         country_of_origin="BR", country_eligibility=["CR","USA"]),
    dict(sku_base="MAR-LEO-BASE", brand=brand_marluvas, name="Marluvas Leopard (demo)",
         category="Calzado de Seguridad", hs_code="6402.99",
         weight_kg=Decimal("0.780"), moq=50, uom="PAIR",
         country_of_origin="BR", country_eligibility=["CR","USA"]),
    dict(sku_base="RW-CLZ-BASE", brand=brand_ranawalk, name="Rana Walk Classic (demo)",
         category="Calzado", hs_code="6404.19",
         weight_kg=Decimal("0.650"), moq=24, uom="PAIR",
         country_of_origin="BR", country_eligibility=["CR"]),
]
masters = []
for data in MASTERS:
    pm, _ = ProductMaster.objects.get_or_create(
        sku_base=data["sku_base"],
        defaults=dict(
            **data,
            description=f"Demo — {data['name']}",
            channel_eligibility=["B2B"],
        )
    )
    masters.append(pm)

print(f"   ✅ {ProductMaster.objects.count()} product masters")

# ============================================================
# BLOQUE 6 — SUPPLIERS
# ============================================================
print("\n[6/12] Suppliers...")

SUPPLIERS = [
    dict(name="Horizonte Calçados (demo)", tax_id="BR.12.345.678/0001-99", country="BR"),
    dict(name="Safety Footwear Demo Co.", tax_id="US-EIN-99-9999991", country="USA"),
]
suppliers = []
for data in SUPPLIERS:
    s, _ = Supplier.objects.get_or_create(
        tax_id=data["tax_id"],
        defaults={**data, "is_active": True}
    )
    SupplierContact.objects.get_or_create(
        supplier=s,
        email=f"contact@{s.name[:8].lower().strip()}.demo",
        defaults=dict(name="Contacto Demo", role="Sales", is_primary=True)
    )
    suppliers.append(s)

print(f"   ✅ {Supplier.objects.count()} suppliers")

# ============================================================
# BLOQUE 7 — PRICING (S14 base + S22 extensions)
# ============================================================
print("\n[7/12] Pricing (S14 + S22)...")

pricelist_mar, _ = PriceList.objects.get_or_create(
    brand=brand_marluvas,
    name="Marluvas Demo PL 2026",
    defaults=dict(
        currency="USD",
        valid_from=NOW - timedelta(days=90),
        is_active=True,
    )
)

# S14 PriceListItems (fallback)
S14_PRICES = {
    "MAR-GOL-L-38": (Decimal("28.50"), 12),
    "MAR-GOL-L-40": (Decimal("28.50"), 12),
    "MAR-GOL-L-42": (Decimal("29.00"), 12),
    "MAR-BIS-H-38": (Decimal("34.00"), 12),
    "MAR-BIS-H-40": (Decimal("34.00"), 12),
    "MAR-BIS-H-42": (Decimal("35.00"), 12),
}
for sku, (price, moq) in S14_PRICES.items():
    PriceListItem.objects.get_or_create(
        price_list=pricelist_mar, sku=sku,
        defaults=dict(price=price, moq_per_size=moq)
    )

# S22 PriceListVersion
plv, _ = PriceListVersion.objects.get_or_create(
    brand=brand_marluvas,
    version_label="PLV-MAR-2026-Q1",
    defaults=dict(
        storage_key="pricelists/marluvas/2026-Q1-demo.csv",
        uploaded_by=ceo_user,
        is_active=True,
        activated_at=NOW - timedelta(days=30),
    )
)

if HAS_S22:
    # GradeItems con precio por grade (Marluvas usa grades por rango de tallas)
    for grade_label, price, multipliers in [
        ("35 ao 40", Decimal("27.80"), {"35":1,"36":1,"37":1,"38":1,"39":1,"40":1}),
        ("41 ao 44", Decimal("29.20"), {"41":1,"42":1,"43":1,"44":1}),
    ]:
        try:
            gi, created = PriceListGradeItem.objects.get_or_create(
                pricelist_version=plv,
                grade_label=grade_label,
                defaults=dict(unit_price_usd=price, size_multipliers=multipliers)
            )
            if not created:
                gi.unit_price_usd = price
                gi.size_multipliers = multipliers
                gi.save()
        except Exception as e:
            print(f"      ⚠️  Error en GradeItem '{grade_label}': {e}")
            # Intentamos manual update si falló el get_or_create por race condition o similar
            PriceListGradeItem.objects.filter(pricelist_version=plv, grade_label=grade_label).update(
                unit_price_usd=price,
                size_multipliers=multipliers
            )

    # ClientProductAssignment — precio cached para MAR-GOL-L-40 / Altaverde
    try:
        bsku_gol_40 = BrandSKU.objects.filter(sku_code="MAR-GOL-L-40").first()
        if bsku_gol_40:
            ClientProductAssignment.objects.update_or_create(
                brand_sku=bsku_gol_40,
                client_subsidiary=sub_av,
                defaults=dict(
                    cached_client_price=Decimal("26.50"),
                    is_active=True,
                )
            )
    except Exception as e:
        print(f"      ⚠️  Error en CPA: {e}")

    # EarlyPaymentPolicy — marluvas / Altaverde
    try:
        epp, _ = EarlyPaymentPolicy.objects.get_or_create(
            brand=brand_marluvas,
            client_subsidiary=sub_av,
            defaults=dict(base_payment_days=90, base_commission_pct=Decimal("10.00"))
        )
        for days, pct in [(8, Decimal("2.75")), (30, Decimal("1.75")), (60, Decimal("1.00"))]:
            EarlyPaymentTier.objects.get_or_create(
                policy=epp, payment_days=days, defaults=dict(discount_pct=pct)
            )
    except Exception as e:
        print(f"      ⚠️  Error en EPP: {e}")

    print(f"   ✅ S22: {PriceListGradeItem.objects.count()} grade items · {ClientProductAssignment.objects.count()} CPAs · {EarlyPaymentPolicy.objects.count()} EPPs")
else:
    print("   ✅ S14 pricing only")

# ============================================================
# BLOQUE 8 — EXPEDIENTES
# 3 expedientes en distintos estados del state machine real:
# REGISTRO → PRODUCCION → PREPARACION → DESPACHO → TRANSITO → EN_DESTINO → CERRADO
# ============================================================
print("\n[8/12] Expedientes...")

brand_sku_gol_40 = BrandSKU.objects.filter(brand=brand_marluvas, product_key="GOL", size="40").first()
brand_sku_gol_38 = BrandSKU.objects.filter(brand=brand_marluvas, product_key="GOL", size="38").first()
brand_sku_bis_40 = BrandSKU.objects.filter(brand=brand_marluvas, product_key="BIS", size="40").first()

# --- EXP-1: REGISTRO (recién creado, solo ART-01) ---
exp1, exp1_new = Expediente.objects.get_or_create(
    legal_entity=le_mwt_cr,
    client=le_dist_cr,
    brand=brand_marluvas,
    status=ExpedienteStatus.REGISTRO,
    defaults=dict(
        destination="CR",
        dispatch_mode=DispatchMode.MWT,
        price_basis="CIF",
        payment_status=PaymentStatus.PENDING,
        credit_clock_start_rule=CreditClockStartRule.ON_CREATION,
        credit_clock_started_at=NOW,
        incoterms="CIF",
        ref_number="REF-DEMO-2026-001",
        credit_days_client=60,
        credit_limit_client=Decimal("50000.00"),
    )
)
if exp1_new:
    # C1 gate: crea ART-01
    art01_exp1, _ = ArtifactInstance.objects.get_or_create(
        expediente=exp1,
        artifact_type="ART-01",
        defaults=dict(
            status=ArtifactStatusEnum.COMPLETED,
            payload={"client_id": le_dist_cr.pk, "brand": "marluvas", "destination": "CR"},
        )
    )
    EventLog.objects.create(
        event_type="expediente.c1_executed",
        aggregate_type=AggregateType.EXPEDIENTE,
        aggregate_id=exp1.expediente_id,
        payload={"action": "C1", "brand": "marluvas"},
        occurred_at=NOW,
        emitted_by="C1:create_expediente",
        correlation_id=uuid.uuid4(),
        expediente=exp1,
        user=ceo_user,
        action_source="C1",
        new_status=ExpedienteStatus.REGISTRO,
    )

# --- EXP-2: PRODUCCION (S20 multi-proforma — mode_b + mode_c) ---
exp2, exp2_new = Expediente.objects.get_or_create(
    legal_entity=le_mwt_cr,
    client=le_dist_cr,
    brand=brand_marluvas,
    status=ExpedienteStatus.PRODUCCION,
    defaults=dict(
        destination="CR",
        dispatch_mode=DispatchMode.MWT,
        price_basis="FOB",
        payment_status=PaymentStatus.PENDING,
        credit_clock_start_rule=CreditClockStartRule.ON_CREATION,
        credit_clock_started_at=NOW - timedelta(days=10),
        incoterms="FOB",
        ref_number="REF-DEMO-2026-002",
        credit_days_client=90,
        freight_mode="MARITIMO",
        transport_mode="CONTAINER",
        factory_order_number="FO-DEMO-001",
        proforma_client_number="PRO-CLI-001",
        fabrication_start_date=TODAY - timedelta(days=7),
        fabrication_end_date=TODAY + timedelta(days=30),
        order_value=Decimal("8340.00"),
    )
)
if exp2_new:
    art01_exp2, _ = ArtifactInstance.objects.get_or_create(
        expediente=exp2, artifact_type="ART-01",
        defaults=dict(
            status=ArtifactStatusEnum.COMPLETED,
            payload={"client_id": le_dist_cr.pk, "brand": "marluvas", "destination": "CR"},
        )
    )
    # S20: Proforma A — mode_b (marluvas solo acepta mode_b o mode_c)
    art02_a, _ = ArtifactInstance.objects.get_or_create(
        expediente=exp2, artifact_type="ART-02",
        defaults=dict(
            status=ArtifactStatusEnum.ACTIVE,
            payload={
                "mode": "mode_b",
                "operated_by": "muito_work_limitada",
                "proforma_index": 1
            },
        )
    )
    # Líneas asignadas a proforma A (S20: FK proforma → ART-02)
    for sku_obj, qty, price in [
        (brand_sku_gol_38, 24, Decimal("27.80")),
        (brand_sku_gol_40, 48, Decimal("27.80")),
    ]:
        ExpedienteProductLine.objects.get_or_create(
            expediente=exp2,
            product=masters[0],  # MAR-GOL-BASE
            brand_sku=sku_obj,
            defaults=dict(
                quantity=qty,
                unit_price=price,
                price_source="pricelist",
                base_price=Decimal("28.50"),
                pricelist_used=pricelist_mar,
                proforma=art02_a,
            )
        )
    # FactoryOrder
    FactoryOrder.objects.get_or_create(
        expediente=exp2,
        order_number="FO-DEMO-HORIZONTE-001",
        defaults=dict(
            proforma_client_number="PRO-CLI-001",
            proforma_mwt_number="PRO-MWT-001",
            purchase_number="OC-DEMO-2026-001",
        )
    )
    # CostLine (append-only: solo crear, no update)
    CostLine.objects.create(
        expediente=exp2,
        cost_type="FLETE_MARITIMO",
        amount=Decimal("850.00"),
        currency="USD",
        phase="PRODUCCION",
        visibility=CostLineVisibility.INTERNAL,
        cost_category=CostCategory.LANDED_COST,
        cost_behavior=CostBehavior.FIXED_PER_OPERATION,
        base_currency="USD",
    )

# --- EXP-3: CERRADO (ciclo completo — pagado) ---
exp3, exp3_new = Expediente.objects.get_or_create(
    legal_entity=le_mwt_usa,
    client=le_dist_cr,
    brand=brand_marluvas,
    status=ExpedienteStatus.CERRADO,
    defaults=dict(
        destination="USA",
        dispatch_mode=DispatchMode.MWT,
        price_basis="EXW",
        payment_status=PaymentStatus.PAID,
        credit_clock_start_rule=CreditClockStartRule.ON_SHIPMENT,
        credit_clock_started_at=NOW - timedelta(days=45),
        payment_registered_at=NOW - timedelta(days=5),
        incoterms="FOB",
        ref_number="REF-DEMO-2025-099",
        freight_mode="MARITIMO",
        awb_bl_number="BL-DEMO-2025-099",
        shipment_date=TODAY - timedelta(days=20),
        invoice_client_number="FAC-CLI-2025-099",
        order_value=Decimal("12600.00"),
        credit_released=True,
        credit_exposure=Decimal("0.00"),
    )
)
if exp3_new:
    # Todos los artefactos del ciclo completo
    for art_type, status, payload in [
        ("ART-01", ArtifactStatusEnum.COMPLETED, {"destination": "USA"}),
        ("ART-02", ArtifactStatusEnum.COMPLETED, {"mode": "mode_c", "operated_by": "muito_work_limitada"}),
        ("ART-05", ArtifactStatusEnum.COMPLETED, {"bl_number": "BL-DEMO-2025-099"}),
    ]:
        ArtifactInstance.objects.get_or_create(
            expediente=exp3, artifact_type=art_type,
            defaults=dict(status=status, payload=payload)
        )
    # Líneas (modo histórico, sin proforma FK — pre-S20)
    for sku_obj, master, qty, price in [
        (brand_sku_bis_40, masters[1], 60, Decimal("34.00")),
        (brand_sku_gol_40, masters[0], 120, Decimal("27.80")),
    ]:
        ExpedienteProductLine.objects.get_or_create(
            expediente=exp3, product=master, brand_sku=sku_obj,
            defaults=dict(quantity=qty, unit_price=price, price_source="manual")
        )
    # PaymentLine (append-only)
    PaymentLine.objects.create(
        expediente=exp3,
        amount=Decimal("12600.00"),
        currency="USD",
        method="TRANSFERENCIA",
        reference="TRF-DEMO-2025-099",
        registered_at=NOW - timedelta(days=5),
        registered_by_type=RegisteredByType.CEO,
        registered_by_id=str(ceo_user.pk),
    )

print(f"   ✅ {Expediente.objects.count()} expedientes · "
      f"{ExpedienteProductLine.objects.count()} líneas · "
      f"{ArtifactInstance.objects.count()} artifacts · "
      f"{FactoryOrder.objects.count()} factory orders")

# ============================================================
# BLOQUE 9 — LIQUIDATIONS (comisiones marluvas)
# ============================================================
print("\n[9/12] Liquidations...")

liq1, liq1_new = Liquidation.objects.get_or_create(
    period="2026-02",
    brand="marluvas",
    defaults=dict(
        liquidation_id="LIQ-MAR-202602-001",
        status="RECONCILED",
        total_lines=3,
        total_commission_amount=Decimal("4250.00"),
        reconciled_at=NOW - timedelta(days=15),
        reconciled_by=ceo_user,
        observations="Demo — datos ficticios, reconciliación aprobada",
    )
)
if liq1_new:
    for ref, concept, client_amt, pct, comm_amt, match in [
        ("REF-DEMO-A01", "commission", Decimal("120000.00"), Decimal("3.50"), Decimal("4200.00"), "MATCHED"),
        ("REF-DEMO-A02", "bonus_volume", Decimal("1500.00"), Decimal("3.33"), Decimal("50.00"), "MATCHED"),
        ("REF-DEMO-A03", "commission", Decimal("0.00"), Decimal("3.50"), Decimal("0.00"), "UNMATCHED"),
    ]:
        LiquidationLine.objects.get_or_create(
            liquidation=liq1,
            marluvas_reference=ref,
            defaults=dict(
                concept=concept,
                client_payment_amount=client_amt,
                commission_pct_reported=pct,
                commission_amount=comm_amt,
                currency="USD",
                match_status=match,
                matched_expediente=exp3 if match == "MATCHED" else None,
            )
        )

liq2, _ = Liquidation.objects.get_or_create(
    period="2026-03",
    brand="marluvas",
    defaults=dict(
        liquidation_id="LIQ-MAR-202603-001",
        status="PENDING_REVIEW",
        total_lines=0,
        total_commission_amount=Decimal("0.00"),
        observations="Demo — pendiente de revisión CEO",
    )
)

print(f"   ✅ {Liquidation.objects.count()} liquidations · {LiquidationLine.objects.count()} líneas")

# ============================================================
# BLOQUE 10 — NODES & TRANSFERS
# ============================================================
print("\n[10/12] Nodes & Transfers...")

node_mwt_cr, _ = Node.objects.get_or_create(
    name="Bodega MWT Costa Rica (demo)",
    defaults=dict(
        legal_entity=le_mwt_cr,
        node_type="owned_warehouse",
        location="San José, Costa Rica",
        status="active",
    )
)

node_mwt_fba, _ = Node.objects.get_or_create(
    name="MWT FBA Amazon USA (demo)",
    defaults=dict(
        legal_entity=le_mwt_usa,
        node_type="fba",
        location="Miami, Florida, USA",
        status="active",
    )
)

node_factory, _ = Node.objects.get_or_create(
    name="Horizonte Factory Brasil (demo)",
    defaults=dict(
        legal_entity=le_factory,
        node_type="factory",
        location="São Paulo, Brasil",
        status="active",
    )
)

node_dist, _ = Node.objects.get_or_create(
    name="Altaverde Distribución (demo)",
    defaults=dict(
        legal_entity=le_dist_cr,
        node_type="third_party",
        location="Cartago, Costa Rica",
        status="active",
    )
)

# Transfer: fábrica BR → bodega MWT CR (importación)
# transfer_id es auto-generado — no lo pasamos
transfer1, t1_new = Transfer.objects.get_or_create(
    from_node=node_factory,
    to_node=node_mwt_cr,
    source_expediente=exp3,
    defaults=dict(
        ownership_before=le_factory,
        ownership_after=le_mwt_cr,
        ownership_changes=True,
        legal_context="nationalization",
        customs_required=True,
        pricing_context={"incoterm": "FOB", "currency": "USD"},
        status="reconciled",
        dispatched_at=NOW - timedelta(days=22),
        received_at=NOW - timedelta(days=8),
        reconciled_at=NOW - timedelta(days=5),
    )
)
if t1_new:
    TransferLine.objects.create(
        transfer=transfer1,
        sku="MAR-BIS-H-40",
        quantity_dispatched=60,
        quantity_received=60,
    )
    TransferLine.objects.create(
        transfer=transfer1,
        sku="MAR-GOL-L-40",
        quantity_dispatched=120,
        quantity_received=118,  # 2 unidades con discrepancia
    )

# Transfer: bodega MWT CR → Altaverde (distribución interna)
transfer2, t2_new = Transfer.objects.get_or_create(
    from_node=node_mwt_cr,
    to_node=node_dist,
    source_expediente=None,
    defaults=dict(
        ownership_before=le_mwt_cr,
        ownership_after=le_dist_cr,
        ownership_changes=True,
        legal_context="distribution",
        customs_required=False,
        status="planned",
        pricing_context={"incoterm": "DDP", "currency": "USD"},
    )
)

print(f"   ✅ {Node.objects.count()} nodes · {Transfer.objects.count()} transfers")

# ============================================================
# BLOQUE 11 — INVENTARIO
# ============================================================
print("\n[11/12] Inventario...")

INV = [
    (masters[0], node_mwt_cr, 96,  48),    # GOL en CR: 96 unidades, 48 reservadas
    (masters[1], node_mwt_cr, 60,  0),     # BIS en CR: 60 disponibles
    (masters[0], node_mwt_fba, 288, 0),    # GOL en FBA USA: sin reservas
]
for master, node, qty, reserved in INV:
    try:
        # Get or create Producto first, robustly
        prod, _ = Producto.objects.get_or_create(
            sku_base=master.sku_base,
            defaults=dict(
                name=master.name,
                brand=master.brand,
                category=master.category,
                description=f"Demo {master.name}"
            )
        )
        
        # Get or create InventoryEntry
        InventoryEntry.objects.get_or_create(
            product=prod,
            node=node,
            defaults=dict(
                quantity=qty,
                reserved=reserved,
                lot_number=f"LOT-{master.sku_base[:7]}-D01",
                received_at=NOW - timedelta(days=30),
            )
        )
    except Exception as e:
        print(f"      ⚠️  Error en InventoryEntry '{master.sku_base}': {e}")

print(f"   ✅ {InventoryEntry.objects.count()} inventory entries")

# ============================================================
# BLOQUE 12 — COMMERCIAL (RebateProgram)
# ============================================================
if HAS_COMMERCIAL:
    print("\n[12/12] Commercial...")
    RebateProgram.objects.get_or_create(
        brand=brand_marluvas,
        name="Rebate Anual Marluvas 2026 (demo)",
        defaults=dict(
            period_type='annual',
            valid_from=TODAY.replace(month=1, day=1),
            valid_to=TODAY.replace(month=12, day=31),
            rebate_type='percentage',
            rebate_value=Decimal("3.50"),
            calculation_base='invoiced',
            threshold_type='amount',
            threshold_value=Decimal("100000.00"),
            is_active=True,
        )
    )
    print(f"   ✅ {RebateProgram.objects.count()} rebate programs")
else:
    print("\n[12/12] Commercial (Skipped)")

# ============================================================
# RESUMEN FINAL
# ============================================================
print("\n" + "=" * 60)
print("SEED COMPLETADO — RESUMEN")
print("=" * 60)

rows = [
    ("LegalEntities",            LegalEntity.objects.count()),
    ("Users",                    User.objects.count()),
    ("Brands",                   Brand.objects.count()),
    ("BrandSKUs",                BrandSKU.objects.count()),
    ("BrandArtifactRules",       BrandArtifactRule.objects.count()),
    ("Clientes",                 Cliente.objects.count()),
    ("ClientSubsidiaries",       ClientSubsidiary.objects.count()),
    ("ProductMasters",           ProductMaster.objects.count()),
    ("Suppliers",                Supplier.objects.count()),
    ("PriceLists",               PriceList.objects.count()),
    ("PriceListItems (S14)",     PriceListItem.objects.count()),
    ("PriceListVersions (S22)",  PriceListVersion.objects.count()),
    ("Expedientes",              Expediente.objects.count()),
    ("ExpedienteProductLines",   ExpedienteProductLine.objects.count()),
    ("ArtifactInstances",        ArtifactInstance.objects.count()),
    ("FactoryOrders",            FactoryOrder.objects.count()),
    ("CostLines",                CostLine.objects.count()),
    ("PaymentLines",             PaymentLine.objects.count()),
    ("EventLogs",                EventLog.objects.count()),
    ("Liquidations",             Liquidation.objects.count()),
    ("LiquidationLines",         LiquidationLine.objects.count()),
    ("Nodes",                    Node.objects.count()),
    ("Transfers",                Transfer.objects.count()),
    ("TransferLines",            TransferLine.objects.count()),
    ("InventoryEntries",         InventoryEntry.objects.count()),
]
if HAS_COMMERCIAL:
    rows.append(("RebatePrograms", RebateProgram.objects.count()))
if HAS_S22:
    rows += [
        ("GradeItems (S22)",         PriceListGradeItem.objects.count()),
        ("ClientAssignments (S22)",  ClientProductAssignment.objects.count()),
        ("EarlyPaymentPolicies",     EarlyPaymentPolicy.objects.count()),
    ]

for label, count in rows:
    print(f"   {label:<35} {count:>4}")

print(f"""
🔑 Credenciales demo:
   CEO  → demo_ceo / demo1234!   (is_superuser=True)
   OPS  → demo_ops / demo1234!

📊 Flujo demostrado:
   EXP-1 REGISTRO     → ART-01 creado, esperando proforma
   EXP-2 PRODUCCION   → S20 multi-proforma mode_b, líneas asignadas, factory order
   EXP-3 CERRADO      → Ciclo completo: artefactos, transfer reconciled, payment

⚠️  Todos los datos son ficticios. Ningún nombre, monto ni referencia
    corresponde a clientes, proveedores o transacciones reales.
{"=" * 60}
""")
