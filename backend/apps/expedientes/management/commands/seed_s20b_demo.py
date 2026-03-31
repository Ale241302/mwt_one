"""
Management command: seed_s20b_demo
Crea datos de demostración con INTEGRIDAD de estados y artefactos.
Refactorizado 2026-03-31 FINAL V24 (State-Integrity-Fix): 
- Para expedientes en PRODUCCION, crea ART-04 (OC Fábrica) automáticamente.
- Evita que los botones aparezcan como BLOQUEADO al sincronizar artefactos con el estado actual.
"""

import uuid
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction


# ============================================================
# DATOS MAESTROS
# ============================================================

BRANDS = [
    {'name': 'Marluvas', 'slug': 'marluvas', 'code': 'MAR', 'type': 'represented'},
    {'name': 'Rana Walk', 'slug': 'rana_walk', 'code': 'RWK', 'type': 'own'},
    {'name': 'Tecmater', 'slug': 'tecmater', 'code': 'TEC', 'type': 'represented'},
]

CLIENTS = [
    {'name': 'SONDEL S.A.', 'code': 'SOND', 'country': 'CR'},
    {'name': 'MUITO WORK LIMITADA', 'code': 'MWLT', 'country': 'CR'},
    {'name': 'COMERCIALIZADORA UMMIE, S.A.', 'code': 'UMMI', 'country': 'GT'},
]

COUNTRIES = ['CR', 'GT', 'CO', 'PA', 'HN']
CHANNELS = ['B2B', 'GLOBAL', 'MWT-CONSOLA']

PRODUCTS_MARLUVAS = [
    {'sku': '50B22-V-E', 'name': 'Vulcabras Bota Elástico', 'category': 'calzado', 'price': Decimal('41.50')},
    {'sku': '30B22', 'name': 'Premier Bota Básica', 'category': 'calzado', 'price': Decimal('28.90')},
]

PRODUCTS_RANAWALK = [
    {'sku': 'RW-GOL-MED-S3', 'name': 'Goliath MED S3', 'category': 'plantilla', 'price': Decimal('34.50')},
]

DEMO_EXPEDIENTES = [
    {
        'brand': 'marluvas', 'client_code': 'SOND', 'status': 'REGISTRO',
        'proformas': [{'mode': 'mode_b', 'lines': ['50B22-V-E', '30B22']}],
    },
    {
        'brand': 'marluvas', 'client_code': 'UMMI', 'status': 'PRODUCCION',
        'proformas': [{'mode': 'mode_b', 'lines': ['50B22-V-E']}],
    },
]


class Command(BaseCommand):
    help = 'Seed demo data V24 State Integrity'

    def add_arguments(self, parser):
        parser.add_argument('--flush', action='store_true')

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write('\n=== SEED DEMO DATA (V24 STATE-INTEGRITY) ===\n')

        from apps.core.models import LegalEntity
        from apps.brands.models import Brand
        from apps.clientes.models import Cliente, ClientGroup, ClientSubsidiary
        from apps.productos.models import Producto, ProductMaster
        from apps.expedientes.models import Expediente, ExpedienteProductLine, ArtifactInstance, EventLog
        from django.contrib.auth import get_user_model

        if options['flush']:
            Expediente.objects.all().delete()
            Producto.objects.all().delete()
            ProductMaster.objects.all().delete()
            Cliente.objects.all().delete()
            ClientSubsidiary.objects.all().delete()
            Brand.objects.all().delete()
            self.stdout.write(self.style.WARNING('  Flush: OK.'))

        # 1. MWT
        mw_entity, _ = LegalEntity.objects.get_or_create(
            entity_id='MWT-CR',
            defaults={'legal_name': 'MUITO WORK', 'country': 'CR', 'status': 'ACTIVE', 'role': 'OWNER', 'frontend': 'MWT'}
        )
        User = get_user_model()
        admin = User.objects.filter(username='admin').first()
        if admin and hasattr(admin, 'legal_entity_id'):
            admin.legal_entity_id = mw_entity.id
            admin.save()

        # 2. Brands
        brands_map = {}
        for b in BRANDS:
            brand, _ = Brand.objects.get_or_create(
                slug=b['slug'], 
                defaults={'name': b['name'], 'brand_type': b['type'], 'is_active': True}
            )
            brand.brand_type = b['type']
            brand.save()
            brand._demo_code = b['code']
            brands_map[b['slug']] = brand

        # 3. Clientes
        clients_map = {}
        for c in CLIENTS:
            le, _ = LegalEntity.objects.get_or_create(
                entity_id=f"{c['code']}-{c['country']}",
                defaults={'legal_name': c['name'], 'country': c['country'], 'status': 'ACTIVE', 'role': 'CLIENT'}
            )
            Cliente.objects.get_or_create(
                name=c['name'],
                defaults={'country': c['country'], 'legal_entity': le, 'is_active': True}
            )
            group, _ = ClientGroup.objects.get_or_create(name=c['name'])
            sub, _ = ClientSubsidiary.objects.get_or_create(
                alias=c['code'], group=group, 
                defaults={'name': c['name'], 'country': c['country'], 'legal_entity': le}
            )
            clients_map[c['code']] = sub

        # 4. Productos
        products_map = {}
        for brand_slug, plist in [('marluvas', PRODUCTS_MARLUVAS), ('rana_walk', PRODUCTS_RANAWALK)]:
            brand = brands_map[brand_slug]
            for p in plist:
                Producto.objects.get_or_create(
                    sku_base=p['sku'], 
                    defaults={'name': p['name'], 'brand': brand, 'category': p['category']}
                )
                pm, _ = ProductMaster.objects.get_or_create(
                    sku_base=p['sku'], brand=brand,
                    defaults={
                        'name': p['name'], 'category': p['category'],
                        'country_eligibility': COUNTRIES, 'channel_eligibility': CHANNELS
                    }
                )
                pm.country_eligibility = COUNTRIES
                pm.save()
                products_map[p['sku']] = pm

        # 5. Expedientes con integridad de artefactos
        year = timezone.now().year
        for exp_def in DEMO_EXPEDIENTES:
            brand = brands_map[exp_def['brand']]
            sub = clients_map[exp_def['client_code']]
            ref = f"{brand._demo_code}-{exp_def['client_code']}-CR-001-{year}"

            exp, created = Expediente.objects.get_or_create(
                ref_number=ref,
                defaults={
                    'legal_entity': mw_entity, 'brand': brand, 'client': sub.legal_entity, 
                    'status': exp_def['status'],
                    'mode': 'mode_b', 'freight_mode': 'FOB', 'dispatch_mode': 'MWT'
                }
            )
            
            if created:
                # ART-03 (OC Cliente) - Siempre necesaria para pasar por registro
                ArtifactInstance.objects.create(
                    expediente=exp, artifact_type='ART-03', status='completed', 
                    payload={'po_number': 'PO-DEMO-123'}
                )
                
                # INTEGRIDAD: Si el expediente ya está en PRODUCCION, debe tener ART-04 (creado por C5)
                if exp.status == 'PRODUCCION':
                    ArtifactInstance.objects.create(
                        expediente=exp, artifact_type='ART-04', status='completed', 
                        payload={'factory_po': 'FAC-DEMO-999'}
                    )
                
                for pf_def in exp_def.get('proformas', []):
                    # ART-02: Proforma
                    proforma = ArtifactInstance.objects.create(
                        expediente=exp, artifact_type='ART-02', status='completed', 
                        payload={'mode': pf_def['mode']}
                    )
                    # Relacionar lineas
                    for sku in pf_def['lines']:
                        if sku in products_map:
                            ExpedienteProductLine.objects.create(
                                expediente=exp, product=products_map[sku], 
                                proforma=proforma, unit_price=Decimal('10.00'), quantity=100
                            )
                self.stdout.write(f"  Expediente: {ref} [{exp.status}] Integrity-OK.")

        self.stdout.write(self.style.SUCCESS('\n✅ Seed completo (V24 STATE-INTEGRITY).\n'))
