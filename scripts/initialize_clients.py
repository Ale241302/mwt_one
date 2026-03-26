import os
import django
import sys

# Setup Django environment
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from apps.core.models import LegalEntity
from apps.clientes.models import Cliente, ClientUltimateParent, ClientGroup, ClientSubsidiary
from apps.expedientes.models import Expediente

def run():
    print("Iniciando inicialización de clientes...")
    try:
        # Entidades legales de clientes que tienen expedientes
        qs_exp = Expediente.objects.all()
        client_ids = list(qs_exp.values_list('client_id', flat=True).distinct())
        print(f"IDs de clientes encontrados: {client_ids}")
        
        legal_entities = LegalEntity.objects.filter(id__in=client_ids)
        
        if not legal_entities.exists():
            print("No se encontraron LegalEntities de clientes con expedientes.")
            return

        for le in legal_entities:
            print(f"Procesando: {le.entity_id} - {le.legal_name}")
            
            # 0. Crear o obtener Cliente (v1 - requerido por la UI actual)
            cliente_v1, created_v1 = Cliente.objects.get_or_create(
                legal_entity=le,
                defaults={
                    'name': le.legal_name,
                    'country': le.country or 'CRI',
                    'is_active': True,
                }
            )
            if created_v1:
                print(f"  [+] Cliente (v1) creado: {cliente_v1.name}")

            # 1. Crear o obtener UltimateParent
            name_parts = le.legal_name.split(' ')
            base_name = name_parts[0] if name_parts else le.entity_id
            
            parent, created = ClientUltimateParent.objects.get_or_create(
                name=base_name,
                defaults={'country': le.country}
            )
            if created:
                print(f"  [+] UltimateParent creado: {parent.name}")
                
            # 2. Crear o obtener Group
            group_name = f"{base_name} Group"
            group, created = ClientGroup.objects.get_or_create(
                parent=parent,
                name=group_name
            )
            if created:
                print(f"  [+] ClientGroup creado: {group.name}")
                
            # 3. Crear o obtener Subsidiary
            alias = le.entity_id[:8]
            subsidiary, created = ClientSubsidiary.objects.get_or_create(
                legal_entity=le,
                defaults={
                    'group': group,
                    'alias': alias,
                    'name': le.legal_name,
                    'country': le.country or 'CRI',
                    'legal_name': le.legal_name,
                }
            )
            if created:
                print(f"  [+] ClientSubsidiary creado: {subsidiary.name} (Alias: {alias})")
            else:
                if not subsidiary.name:
                    subsidiary.name = le.legal_name
                    subsidiary.save()
                print(f"  [-] ClientSubsidiary ya existe: {subsidiary.name}")

    except Exception as e:
        import traceback
        print(f"ERROR: {str(e)}")
        traceback.print_exc()

    print("Inicialización de clientes completada.")

if __name__ == "__main__":
    run()
