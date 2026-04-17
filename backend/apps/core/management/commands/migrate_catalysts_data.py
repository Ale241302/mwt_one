import logging
from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import transaction
from apps.core.models import UUIDReferenceField

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Migrates legacy ForeignKeys to UUID fields using UUIDReferenceField configuration.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Do not save changes')

    def handle(self, *args, **options):
        dry_run = options.get('dry_run')
        
        # Mapeo de modelos y campos a migrar
        # Formato: (app_label, model_name, field_name, old_data_source)
        # old_data_source puede ser el nombre de la antigua columna o una lógica de resolución.
        migration_targets = [
            ('expedientes', 'Expediente', 'brand_id', 'legacy_brand_slug'),
            ('expedientes', 'Expediente', 'nodo_destino_id', 'legacy_node_id'),
            ('transfers', 'Transfer', 'from_node_id', 'legacy_from_node_id'),
            ('transfers', 'Transfer', 'to_node_id', 'legacy_to_node_id'),
            ('inventario', 'InventoryEntry', 'node_id', 'legacy_node_id'),
            # Agregue más según sea necesario
        ]

        for app_label, model_name, field_name, source in migration_targets:
            self.stdout.write(f"Processing {app_label}.{model_name}.{field_name}...")
            try:
                model = apps.get_model(app_label, model_name)
                self.migrate_model_field(model, field_name, source, dry_run)
            except LookupError:
                self.stderr.write(f"Model {app_label}.{model_name} not found.")

    def migrate_model_field(self, model, field_name, source, dry_run):
        queryset = model.objects.all()
        count = 0
        
        with transaction.atomic():
            for obj in queryset:
                # Lógica de resolución: 
                # En un escenario real, tendríamos que leer de la tabla antes de que Django
                # elimine las columnas, o usar un backup.
                # Aquí asumo que ya tenemos los servicios para resolver por Slug/ID antiguo.
                
                # Ejemplo para Brand (usando slug):
                if field_name == 'brand_id':
                    old_slug = getattr(obj, source, None)
                    if old_slug:
                        from apps.brands.services import BrandService
                        brand = BrandService.get_brand(slug=old_slug)
                        if brand:
                            setattr(obj, field_name, brand.id)
                            count += 1

                # Ejemplo para Nodos:
                elif 'node' in field_name or 'nodo' in field_name:
                    old_id = getattr(obj, source, None)
                    if old_id:
                        from apps.nodos.services import NodeService
                        node = NodeService.get_node(id=old_id)
                        if node:
                            setattr(obj, field_name, node.id)
                            count += 1

                if not dry_run:
                    obj.save(update_fields=[field_name])

        self.stdout.write(self.style.SUCCESS(f"Successfully migrated {count} records for {model.__name__}.{field_name}"))
