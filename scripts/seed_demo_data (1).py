"""
Management command: seed_demo_data
Crea datos de demostración para navegar el sistema post-Sprint 20B.

Uso:
    python manage.py seed_demo_data
    python manage.py seed_demo_data --flush  # borra datos de demo antes de recrear

Crea:
- 3 Brands (Marluvas, Rana Walk, Tecmater)
- 10 Clientes (ClientGroup + ClientSubsidiary) con client_code de 4 letras
- Productos representativos por brand (no los 565 completos — solo muestra navegable)
- Expedientes de ejemplo en varios estados con proformas, líneas y EventLog
- Nomenclatura: {BRAND}-{CLIENT_CODE}-{COUNTRY}-{SEQ}-{YEAR}
  Ejemplo: MAR-SOND-CR-001-2026

Idempotente: usa get_or_create en todo. Seguro de correr múltiples veces.
"""

import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction


# ============================================================
# DATOS MAESTROS
# ============================================================

BRANDS = [
    {'name': 'Marluvas', 'slug': 'marluvas', 'code': 'MAR', 'brand_type': 'represented'},
    {'name': 'Rana Walk', 'slug': 'rana_walk', 'code': 'RWK', 'brand_type': 'own'},
    {'name': 'Tecmater', 'slug': 'tecmater', 'code': 'TEC', 'brand_type': 'represented'},
]

CLIENTS = [
    {'name': 'SONDEL S.A.', 'code': 'SOND', 'country': 'CR', 'sap': '4000000100'},
    {'name': 'MUITO WORK LIMITADA', 'code': 'MWLT', 'country': 'CR', 'sap': '4000000145'},
    {'name': 'DISTRIBUIDORA COMTEK S.A.S.', 'code': 'COMT', 'country': 'CO', 'sap': '4000000102'},
    {'name': 'SONEPAR COLOMBIA S.A.S.', 'code': 'SNPR', 'country': 'CO', 'sap': '4000000402'},
    {'name': 'IMPORCOMP S.A.', 'code': 'IMPC', 'country': 'GT', 'sap': '4000000115'},
    {'name': 'COMERCIALIZADORA UMMIE, S.A.', 'code': 'UMMI', 'country': 'GT', 'sap': '4000000400'},
    {'name': 'GRUPO SOLUCIONES DE INGENIERIA Y AUTOMATIZACION S.A.', 'code': 'SIAS', 'country': 'GT', 'sap': '4000000484'},
    {'name': 'EQUIPOS Y GUANTES INDUSTRIALES S.A.', 'code': 'EGUI', 'country': 'GT', 'sap': '4000000501'},
    {'name': 'PRO CUSTOMER CORP.', 'code': 'PRCU', 'country': 'PA', 'sap': '4000000126'},
    {'name': 'IMPORTACIONES Y COMPRAS S. DE R.L.', 'code': 'IMYC', 'country': 'HN', 'sap': '4000000128'},
]

# Productos representativos por brand (muestra navegable, no catálogo completo)
PRODUCTS_MARLUVAS = [
    # Familia 50 — calzado industrial básico
    {'sku': '50B22-V-E', 'name': 'Vulcabras Bota Elástico', 'category': 'calzado', 'price': Decimal('41.50')},
    {'sku': '50B22-V-C', 'name': 'Vulcabras Bota Cordón', 'category': 'calzado', 'price': Decimal('41.50')},
    # Familia 30 — línea económica
    {'sku': '30B22', 'name': 'Premier Bota Básica', 'category': 'calzado', 'price': Decimal('28.90')},
    # Familia 65 — línea media
    {'sku': '65B19-E', 'name': 'Massimo Bota Elástico', 'category': 'calzado', 'price': Decimal('52.80')},
    # Familia 70 — línea premium
    {'sku': '70B29-E', 'name': 'Nexus Bota Premium', 'category': 'calzado', 'price': Decimal('68.50')},
    # Familia 75 — premium composite
    {'sku': '75BPR29-MSMC', 'name': 'Ultra Plus Composite', 'category': 'calzado', 'price': Decimal('79.00')},
    # Familia 10 — botas de caucho
    {'sku': '10VT48-N', 'name': 'Bota Caucho Vulcanizada', 'category': 'calzado', 'price': Decimal('22.30')},
    # Familia 90 — plantillas
    {'sku': '90PI22-P', 'name': 'Palmilha Confort', 'category': 'plantilla', 'price': Decimal('4.80')},
]

PRODUCTS_RANAWALK = [
    {'sku': 'RW-GOL-MED-S3', 'name': 'Goliath MED S3', 'category': 'plantilla', 'price': Decimal('34.50')},
    {'sku': 'RW-GOL-MED-S4', 'name': 'Goliath MED S4', 'category': 'plantilla', 'price': Decimal('34.50')},
    {'sku': 'RW-VEL-MED-S3', 'name': 'Velox MED S3', 'category': 'plantilla', 'price': Decimal('34.50')},
    {'sku': 'RW-ORB-MED-S4', 'name': 'Orbis MED S4', 'category': 'plantilla', 'price': Decimal('34.50')},
    {'sku': 'RW-LEO-LOW-S3', 'name': 'Leopard LOW S3', 'category': 'plantilla', 'price': Decimal('34.50')},
    {'sku': 'RW-LEO-MED-S4', 'name': 'Leopard MED S4', 'category': 'plantilla', 'price': Decimal('34.50')},
    {'sku': 'RW-BIS-HGH-S3', 'name': 'Bison HGH S3', 'category': 'plantilla', 'price': Decimal('34.50')},
    {'sku': 'RW-BIS-MED-S4', 'name': 'Bison MED S4', 'category': 'plantilla', 'price': Decimal('34.50')},
]

PRODUCTS_TECMATER = [
    {'sku': 'TEC-IND-001', 'name': 'Bota Industrial Tecmater', 'category': 'calzado', 'price': Decimal('45.00')},
    {'sku': 'TEC-IND-002', 'name': 'Zapato Seguridad Tecmater', 'category': 'calzado', 'price': Decimal('38.00')},
]

# Expedientes de demo — cubren varios escenarios
DEMO_EXPEDIENTES = [
    # Marluvas — expediente completo con proformas mixtas (mode_b + mode_c)
    {
        'brand': 'marluvas', 'client_code': 'SOND', 'status': 'REGISTRO',
        'proformas': [
            {'mode': 'mode_b', 'lines': ['50B22-V-E', '30B22'], 'operated_by': 'muito_work_limitada'},
            {'mode': 'mode_c', 'lines': ['70B29-E'], 'operated_by': 'muito_work_limitada'},
        ],
    },
    # Marluvas — expediente en PRODUCCION con 1 proforma
    {
        'brand': 'marluvas', 'client_code': 'UMMI', 'status': 'PRODUCCION',
        'proformas': [
            {'mode': 'mode_b', 'lines': ['65B19-E', '75BPR29-MSMC'], 'operated_by': 'muito_work_limitada'},
        ],
    },
    # Marluvas — expediente en PREPARACION
    {
        'brand': 'marluvas', 'client_code': 'COMT', 'status': 'PREPARACION',
        'proformas': [
            {'mode': 'mode_c', 'lines': ['50B22-V-C', '30B22', '90PI22-P'], 'operated_by': 'muito_work_limitada'},
        ],
    },
    # Marluvas — expediente legacy (sin proformas, pre-S20)
    {
        'brand': 'marluvas', 'client_code': 'IMPC', 'status': 'REGISTRO',
        'proformas': [],  # legacy
    },
    # Rana Walk — expediente con default mode
    {
        'brand': 'rana_walk', 'client_code': 'MWLT', 'status': 'REGISTRO',
        'proformas': [
            {'mode': 'default', 'lines': ['RW-GOL-MED-S3', 'RW-GOL-MED-S4', 'RW-VEL-MED-S3'], 'operated_by': 'muito_work_limitada'},
        ],
    },
    # Rana Walk — expediente en DESPACHO (avanzado)
    {
        'brand': 'rana_walk', 'client_code': 'MWLT', 'status': 'DESPACHO',
        'proformas': [
            {'mode': 'default', 'lines': ['RW-LEO-LOW-S3', 'RW-BIS-HGH-S3'], 'operated_by': 'muito_work_limitada'},
        ],
    },
    # Tecmater — expediente simple
    {
        'brand': 'tecmater', 'client_code': 'SNPR', 'status': 'REGISTRO',
        'proformas': [
            {'mode': 'default', 'lines': ['TEC-IND-001', 'TEC-IND-002'], 'operated_by': 'muito_work_limitada'},
        ],
    },
    # Marluvas — expediente CANCELADO
    {
        'brand': 'marluvas', 'client_code': 'PRCU', 'status': 'CANCELADO',
        'proformas': [],
    },
]

# Estado progresivo — para avanzar un expediente necesita pasar por cada estado
STATE_ORDER = ['REGISTRO', 'PRODUCCION', 'PREPARACION', 'DESPACHO', 'TRANSITO', 'EN_DESTINO', 'CERRADO']


class Command(BaseCommand):
    help = 'Seed demo data para navegar el sistema post-Sprint 20B'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush', action='store_true',
            help='Borra expedientes de demo antes de recrear (NO borra brands/clients/products)'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write('\n=== SEED DEMO DATA ===\n')

        if options['flush']:
            self._flush_demo_expedientes()

        brands = self._create_brands()
        clients = self._create_clients()
        products = self._create_products(brands)
        self._create_expedientes(brands, clients, products)

        self.stdout.write(self.style.SUCCESS('\n✅ Seed completo.\n'))

    # ============================================================
    # BRANDS
    # ============================================================

    def _create_brands(self):
        from apps.brands.models import Brand

        result = {}
        for b in BRANDS:
            brand, created = Brand.objects.get_or_create(
                slug=b['slug'],
                defaults={
                    'name': b['name'],
                    # Agregar campos extra si existen en el modelo:
                    # 'brand_type': b['brand_type'],
                    # 'code': b['code'],
                }
            )
            # Guardar code en el objeto para referencia
            brand._demo_code = b['code']
            result[b['slug']] = brand
            status = 'CREADO' if created else 'ya existe'
            self.stdout.write(f"  Brand: {brand.name} ({brand.slug}) — {status}")

        return result

    # ============================================================
    # CLIENTS
    # ============================================================

    def _create_clients(self):
        from apps.clientes.models import ClientGroup, ClientSubsidiary

        result = {}
        for c in CLIENTS:
            # ClientGroup = agrupación de subsidiarias del mismo cliente
            group, _ = ClientGroup.objects.get_or_create(
                name=c['name'],
            )

            sub, created = ClientSubsidiary.objects.get_or_create(
                name=c['name'],
                client_group=group,
                defaults={
                    'alias': c['code'],
                    'country': c['country'],
                    # Campos opcionales (pueden no existir aún):
                    # 'legal_name': c['name'],
                    # 'external_code_marluvas': c['sap'],
                }
            )
            result[c['code']] = sub
            status = 'CREADO' if created else 'ya existe'
            self.stdout.write(f"  Cliente: {c['code']} — {c['name']} ({c['country']}) — {status}")

        return result

    # ============================================================
    # PRODUCTS
    # ============================================================

    def _create_products(self, brands):
        from apps.productos.models import ProductMaster

        result = {}
        product_map = {
            'marluvas': PRODUCTS_MARLUVAS,
            'rana_walk': PRODUCTS_RANAWALK,
            'tecmater': PRODUCTS_TECMATER,
        }

        for brand_slug, products in product_map.items():
            brand = brands[brand_slug]
            for p in products:
                pm, created = ProductMaster.objects.get_or_create(
                    sku=p['sku'],
                    brand=brand,
                    defaults={
                        'name': p['name'],
                        'category': p.get('category', 'calzado'),
                        # 'base_price': p['price'],  # depende del modelo real
                    }
                )
                result[p['sku']] = {'product': pm, 'price': p['price'], 'brand_slug': brand_slug}
                if created:
                    self.stdout.write(f"    Producto: {p['sku']} — {p['name']}")

        self.stdout.write(f"  Productos: {len(result)} totales")
        return result

    # ============================================================
    # EXPEDIENTES
    # ============================================================

    def _create_expedientes(self, brands, clients, products):
        from apps.expedientes.models import (
            Expediente, ExpedienteProductLine, ArtifactInstance, EventLog,
        )

        year = timezone.now().year
        # Consecutivos por brand
        seq_counters = {slug: 0 for slug in brands}

        for exp_def in DEMO_EXPEDIENTES:
            brand = brands[exp_def['brand']]
            client = clients[exp_def['client_code']]
            brand_code = next(b['code'] for b in BRANDS if b['slug'] == exp_def['brand'])

            # Generar expediente_number
            seq_counters[exp_def['brand']] += 1
            seq = seq_counters[exp_def['brand']]
            exp_number = f"{brand_code}-{exp_def['client_code']}-{client.country}-{seq:03d}-{year}"

            # Verificar si ya existe
            existing = Expediente.objects.filter(expediente_number=exp_number).first()
            if existing:
                self.stdout.write(f"  Expediente: {exp_number} — ya existe (skip)")
                continue

            # Crear expediente en REGISTRO
            expediente = Expediente.objects.create(
                expediente_number=exp_number,
                brand=brand,
                client_subsidiary=client,
                status='REGISTRO',
                payment_status='pending',
                is_blocked=False,
            )

            EventLog.objects.create(
                expediente=expediente,
                event_type='expediente.created',
                payload={'expediente_number': exp_number, 'brand': exp_def['brand']},
                action_source='C1',
            )

            # Crear líneas de producto (sin proforma por ahora)
            line_objects = {}
            all_skus = []
            for pf_def in exp_def.get('proformas', []):
                all_skus.extend(pf_def.get('lines', []))

            for sku in all_skus:
                if sku not in products:
                    continue
                pm = products[sku]
                line = ExpedienteProductLine.objects.create(
                    expediente=expediente,
                    product=pm['product'],
                    unit_price=pm['price'],
                    quantity=100,  # demo
                    price_source='pricelist',
                )
                line_objects[sku] = line

            # Crear proformas y asignar líneas
            pf_counter = 0
            for pf_def in exp_def.get('proformas', []):
                pf_counter += 1
                pf_number = f"PF-{expediente.id}-{pf_counter:03d}-{year}"

                proforma = ArtifactInstance.objects.create(
                    expediente=expediente,
                    artifact_type='ART-02',
                    status='COMPLETED',
                    payload={
                        'proforma_number': pf_number,
                        'mode': pf_def['mode'],
                        'operated_by': pf_def.get('operated_by', 'muito_work_limitada'),
                    },
                )

                # Asignar líneas a esta proforma
                for sku in pf_def.get('lines', []):
                    if sku in line_objects:
                        line_objects[sku].proforma = proforma
                        line_objects[sku].save(update_fields=['proforma'])

                EventLog.objects.create(
                    expediente=expediente,
                    event_type='proforma.created',
                    payload={
                        'proforma_id': proforma.id,
                        'proforma_number': pf_number,
                        'mode': pf_def['mode'],
                    },
                    proforma=proforma,
                    action_source='create_proforma',
                )

            # Avanzar estado si necesario
            target_status = exp_def['status']
            if target_status != 'REGISTRO' and target_status != 'CANCELADO':
                self._advance_to_status(expediente, target_status)
            elif target_status == 'CANCELADO':
                expediente.status = 'CANCELADO'
                expediente.save(update_fields=['status'])
                EventLog.objects.create(
                    expediente=expediente,
                    event_type='expediente.cancelled',
                    payload={'reason': 'Demo — expediente cancelado de ejemplo'},
                    action_source='C16',
                    previous_status='REGISTRO',
                    new_status='CANCELADO',
                )

            proforma_count = len(exp_def.get('proformas', []))
            line_count = len(all_skus)
            self.stdout.write(
                f"  Expediente: {exp_number} — {target_status} "
                f"({proforma_count} proformas, {line_count} líneas)"
            )

    def _advance_to_status(self, expediente, target_status):
        """
        Avanza un expediente de REGISTRO al estado objetivo
        creando EventLog por cada transición intermedia.
        No ejecuta commands reales — solo muta status + log.
        """
        from apps.expedientes.models import EventLog

        if target_status not in STATE_ORDER:
            return

        current_idx = STATE_ORDER.index('REGISTRO')
        target_idx = STATE_ORDER.index(target_status)

        # Command por transición (simplificado)
        transition_commands = {
            'PRODUCCION': 'C5',
            'PREPARACION': 'C6',
            'DESPACHO': 'C10',
            'TRANSITO': 'C11',
            'EN_DESTINO': 'C12',
            'CERRADO': 'C14',
        }

        for i in range(current_idx + 1, target_idx + 1):
            prev_status = STATE_ORDER[i - 1]
            new_status = STATE_ORDER[i]
            command = transition_commands.get(new_status, 'SYSTEM')

            expediente.status = new_status
            expediente.save(update_fields=['status'])

            EventLog.objects.create(
                expediente=expediente,
                event_type='expediente.state_changed',
                payload={
                    'from': prev_status,
                    'to': new_status,
                    'demo': True,
                },
                action_source=command,
                previous_status=prev_status,
                new_status=new_status,
            )

    def _flush_demo_expedientes(self):
        """Borra expedientes que fueron creados por este seed."""
        from apps.expedientes.models import Expediente

        year = timezone.now().year
        demo_patterns = [f'MAR-%-{year}', f'RWK-%-{year}', f'TEC-%-{year}']

        count = 0
        for pattern in demo_patterns:
            qs = Expediente.objects.filter(expediente_number__regex=pattern.replace('%', '.*'))
            c = qs.count()
            qs.delete()
            count += c

        self.stdout.write(self.style.WARNING(f'  Flush: {count} expedientes de demo borrados'))
