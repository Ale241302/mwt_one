"""
flush_demo.py - Borra los expedientes demo creados por seed_demo_data

Ejecutar dentro del contenedor Django:
    python manage.py shell < /tmp/flush_demo.py

O via:
    docker cp flush_demo.py mwt-django:/tmp/
    docker exec mwt-django python /tmp/flush_demo.py
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")
django.setup()

from apps.expedientes.models import Expediente, ArtifactInstance, CostLine, PaymentLine, EventLog
from apps.core.models import LegalEntity
from apps.transfers.models import Transfer, Node

DEMO_ENTITY_IDS = ["SONDEL-CR", "UMMIE-GT", "IMPORCOMP-CO", "MWT-CR"]

print("=" * 60)
print("FLUSH DEMO DATA")
print("=" * 60)

# 1. Expedientes demo (brand=None AND client en las entidades demo)
demo_exps = Expediente.objects.filter(
    client__entity_id__in=["SONDEL-CR", "UMMIE-GT", "IMPORCOMP-CO"],
    brand__isnull=True,
)
demo_exp_ids = list(demo_exps.values_list("pk", flat=True))
print(f"Expedientes demo encontrados: {demo_exps.count()}")

# 2. EventLogs
ev_count = EventLog.objects.filter(aggregate_id__in=demo_exp_ids).count()
EventLog.objects.filter(aggregate_id__in=demo_exp_ids).delete()
print(f"  EventLogs borrados: {ev_count}")

# 3. PaymentLines
pl_count = PaymentLine.objects.filter(expediente__in=demo_exps).count()
PaymentLine.objects.filter(expediente__in=demo_exps).delete()
print(f"  PaymentLines borradas: {pl_count}")

# 4. CostLines
cl_count = CostLine.objects.filter(expediente__in=demo_exps).count()
CostLine.objects.filter(expediente__in=demo_exps).delete()
print(f"  CostLines borradas: {cl_count}")

# 5. ArtifactInstances
ai_count = ArtifactInstance.objects.filter(expediente__in=demo_exps).count()
ArtifactInstance.objects.filter(expediente__in=demo_exps).delete()
print(f"  ArtifactInstances borradas: {ai_count}")

# 6. Expedientes
exp_count = demo_exps.count()
demo_exps.delete()
print(f"  Expedientes borrados: {exp_count}")

# 7. Transfers demo
trf_count = Transfer.objects.filter(transfer_id__startswith="TRF-DEMO").count()
Transfer.objects.filter(transfer_id__startswith="TRF-DEMO").delete()
print(f"  Transfers demo borrados: {trf_count}")

# 8. Nodes demo
node_count = Node.objects.filter(name__startswith="DEMO ").count()
Node.objects.filter(name__startswith="DEMO ").delete()
print(f"  Nodes demo borrados: {node_count}")

# 9. Liquidaciones demo (si existe el módulo)
try:
    from apps.liquidations.models import Liquidation
    liq_count = Liquidation.objects.filter(period__startswith="DEMO-").count()
    Liquidation.objects.filter(period__startswith="DEMO-").delete()
    print(f"  Liquidaciones demo borradas: {liq_count}")
except ImportError:
    print("  Liquidations module not found — skipping")

# 10. LegalEntities demo
le_count = LegalEntity.objects.filter(entity_id__in=DEMO_ENTITY_IDS).count()
LegalEntity.objects.filter(entity_id__in=DEMO_ENTITY_IDS).delete()
print(f"  LegalEntities demo borradas: {le_count}")

print("=" * 60)
print("FLUSH COMPLETADO")
print("=" * 60)
